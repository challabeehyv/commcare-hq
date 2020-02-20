import logging
from contextlib import ExitStack
from functools import partial

import attr

from couchforms.models import XFormInstance
from couchforms.models import doc_types as form_doc_types
from dimagi.utils.chunked import chunked

from corehq.apps.domain.dbaccessors import get_doc_count_in_domain_by_type
from corehq.form_processor.models import XFormInstanceSQL
from corehq.sql_db.util import split_list_by_db_partition
from corehq.util.datadog.gauges import datadog_counter
from corehq.util.log import with_progress_bar
from corehq.util.pagination import ResumableFunctionIterator

from .couchsqlmigration import (
    DocCounter,
    Stopper,
    _iter_docs,
    get_main_forms_iteration_stop_date,
)
from .statedb import open_state_db

log = logging.getLogger(__name__)


def find_missing_docs(domain, state_dir, live_migrate=False, resume=True):
    """Update missing documents in state db

    Find each entity (form or case) that is in Couch but not in SQL.
    Does not verify that each entity has the same doc type in Couch and
    SQL; that is done by the diff process.

    Datadog metrics used for counting missing docs:
    - commcare.couchsqlmigration.form.has_diff
    - commcare.couchsqlmigration.case.has_diff
    """
    stopper = Stopper(live_migrate)
    dd_count = partial(datadog_counter, tags=["domain:" + domain])
    statedb = open_state_db(domain, state_dir, readonly=False)
    if live_migrate:
        log.info(f"stopping at {get_main_forms_iteration_stop_date(statedb)}")
    with statedb, stopper, ExitStack() as stop_it:
        for entity in ["form", "case"]:
            missing_ids = MissingIds(entity, statedb, stopper, resume=resume)
            stop_it.enter_context(missing_ids)
            for doc_type in missing_ids.doc_types:
                statedb.delete_missing_docs(doc_type)
                for doc_id in missing_ids(doc_type):
                    statedb.add_missing_docs(doc_type, [doc_id])
                    dd_count(f"commcare.couchsqlmigration.{entity}.has_diff")


@attr.s
class MissingIds:
    """Iterator of document ids found in Couch but not SQL"""

    @classmethod
    def forms(cls, *args, **kw):
        return cls(cls.FORM, *args, **kw)

    entity = attr.ib()
    statedb = attr.ib()
    stopper = attr.ib()
    resume = attr.ib(default=True, kw_only=True)
    tag = attr.ib(default="missing", kw_only=True)
    chunk_size = attr.ib(default=5000, kw_only=True)

    missing_docs_sql = """
        SELECT couch.{doc_id}
        FROM (SELECT unnest(%s) AS {doc_id}) AS couch
        LEFT JOIN {table} sql USING ({doc_id})
        WHERE sql.{doc_id} IS NULL
    """

    FORM = "form"
    CASE = "case"

    sql_params = {
        FORM: {"doc_id": "form_id", "table": "form_processor_xforminstancesql"},
        CASE: {"doc_id": "case_id", "table": "form_processor_commcarecasesql"},
    }

    _doc_types = {
        FORM: list(form_doc_types()) + ["HQSubmission", "XFormInstance-Deleted"],
        CASE: ['CommCareCase', 'CommCareCase-Deleted'],
    }

    def __attrs_post_init__(self):
        self.domain = self.statedb.domain
        self.counter = DocCounter(self.statedb)
        self.doc_types = self._doc_types[self.entity]
        sql_params = self.sql_params[self.entity]
        self.sql = self.missing_docs_sql.format(**sql_params)
        self._iteration_keys = set()

    def __call__(self, doc_type):
        """Create a missing ids generator for the given doc type

        Default datadog tags (varies on `self.tag`):
        - type:find_missing_forms
        - type:find_missing_cases
        """
        if self.stopper.clean_break:
            return
        assert doc_type in self.doc_types, \
            f"'{doc_type}' is not a {self.entity} doc type"
        dd_type = f"find_{self.tag}_{self.entity}s"
        count_key = f"{doc_type}.id.{self.tag}"
        resume_key = f"{self.domain}.{count_key}.{self.statedb.unique_id}"
        if not self.resume:
            self.discard_iteration_state(resume_key)
            self.counter.pop(count_key)
        couch_ids = _iter_docs(self.domain, f"{doc_type}.id", resume_key, self.stopper)
        couch_ids = self.with_progress(doc_type, couch_ids, count_key)
        with self.counter(dd_type, count_key) as add_docs:
            for batch in chunked(couch_ids, self.chunk_size, list):
                yield from self.drop_sql_ids(batch)
                add_docs(len(batch))
        self._iteration_keys.add((doc_type, count_key, resume_key))

    def drop_sql_ids(self, couch_ids):
        """Filter the given couch ids, removing ids that are in SQL"""
        for dbname, form_ids in split_list_by_db_partition(couch_ids):
            with XFormInstanceSQL.get_cursor_for_partition_db(dbname, readonly=True) as cursor:
                cursor.execute(self.sql, [form_ids])
                yield from (form_id for form_id, in cursor.fetchall())

    def with_progress(self, doc_type, iterable, count_key):
        couchdb = XFormInstance.get_db()
        return with_progress_bar(
            iterable,
            get_doc_count_in_domain_by_type(self.domain, doc_type, couchdb),
            prefix=f"Scanning {doc_type}",
            offset=self.counter.get(count_key),
            oneline="concise",
        )

    def __enter__(self):
        if self.stopper.live_migrate and not hasattr(self.stopper, "stop_date"):
            self.stopper.stop_date = get_main_forms_iteration_stop_date(self.statedb)
        self.counter.__enter__()
        return self

    def __exit__(self, *exc_info):
        if self.stopper.live_migrate and hasattr(self.stopper, "stop_date"):
            # remove stop date so main forms iteration may continue
            del self.stopper.stop_date
        if self.stopper.clean_break or exc_info[1] is not None:
            # incomplete iteration
            return
        # discard iteration state so it is possible to do again later
        for doc_type, count_key, resume_key in self._iteration_keys:
            self.discard_iteration_state(resume_key)
            self.reset_doc_count(doc_type, count_key)
        self.counter.__exit__(*exc_info)

    @staticmethod
    def discard_iteration_state(resume_key):
        ResumableFunctionIterator(resume_key, None, None, None).discard_state()

    def reset_doc_count(self, doc_type, count_key):
        count = self.counter.pop(count_key)
        if not self.stopper.live_migrate:
            couchdb = XFormInstance.get_db()
            count = get_doc_count_in_domain_by_type(self.domain, doc_type, couchdb)
        self.statedb.set_counter(doc_type, count)
