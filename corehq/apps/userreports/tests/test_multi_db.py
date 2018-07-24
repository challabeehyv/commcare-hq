from __future__ import absolute_import
from __future__ import unicode_literals
import uuid

from corehq.apps.callcenter.tests.test_utils import CallCenterDomainMockTest
from corehq.apps.userreports.models import DataSourceConfiguration, ReportConfiguration
from corehq.apps.userreports.reports.data_source import ConfigurableReportDataSource
from corehq.apps.userreports.sql.connection import get_engine_id
from corehq.apps.userreports.tests.utils import get_sample_data_source, get_sample_doc_and_indicators, \
    get_sample_report_config, doc_to_change
from corehq.apps.userreports.util import get_indicator_adapter
from corehq.pillows.case import get_ucr_es_case_pillow
from corehq.sql_db import connections
from corehq.sql_db.tests.utils import temporary_database
from six.moves import range


class UCRMultiDBTest(CallCenterDomainMockTest):

    @classmethod
    def setUpClass(cls):
        super(UCRMultiDBTest, cls).setUpClass()
        cls.db2_name = 'cchq_ucr_tests'
        db_conn_parts = connections.connection_manager.get_connection_string('default').split('/')
        db_conn_parts[-1] = cls.db2_name
        cls.db2_url = '/'.join(db_conn_parts)

        cls.context_manager = connections.override_engine('engine-2', cls.db2_url)
        cls.context_manager.__enter__()

        # setup data sources
        data_source_template = get_sample_data_source()
        cls.ds_1 = DataSourceConfiguration.wrap(data_source_template.to_json())
        cls.ds_1.engine_id = 'engine-1'
        cls.ds_1.save()
        cls.ds_2 = DataSourceConfiguration.wrap(data_source_template.to_json())
        cls.ds_2.engine_id = 'engine-2'
        cls.ds_2.save()

        cls.db_context = temporary_database(cls.db2_name)
        cls.db_context.__enter__()

        cls.ds1_adapter = get_indicator_adapter(cls.ds_1)
        cls.ds2_adapter = get_indicator_adapter(cls.ds_2)

    def setUp(self):
        # initialize the tables
        self.ds1_adapter.rebuild_table()
        self.ds2_adapter.rebuild_table()
        self.assertEqual(0, self.ds1_adapter.get_query_object().count())
        self.assertEqual(0, self.ds2_adapter.get_query_object().count())

    @classmethod
    def tearDownClass(cls):
        cls.context_manager.__exit__(None, None, None)

        # delete data sources
        cls.ds_1.delete()
        cls.ds_2.delete()

        # dispose secondary engine
        cls.ds2_adapter.session_helper.engine.dispose()

        # drop the secondary database
        cls.db_context.__exit__(None, None, None)
        super(UCRMultiDBTest, cls).tearDownClass()

    def tearDown(self):
        self.ds1_adapter.session_helper.Session.remove()
        self.ds2_adapter.session_helper.Session.remove()
        self.ds1_adapter.drop_table()
        self.ds2_adapter.drop_table()

    def test_patches_and_setup(self):
        self.assertEqual('engine-1', get_engine_id(self.ds_1))
        self.assertEqual('engine-2', get_engine_id(self.ds_2))

        self.assertEqual(connections.connection_manager.get_connection_string('default'),
                         connections.connection_manager.get_connection_string('engine-1'))
        self.assertEqual(self.db2_url,
                         connections.connection_manager.get_connection_string('engine-2'))

        self.assertNotEqual(str(self.ds1_adapter.engine.url), str(self.ds2_adapter.engine.url))
        self.assertEqual(connections.connection_manager.get_connection_string('default'),
                         str(self.ds1_adapter.engine.url))
        self.assertEqual(self.db2_url, str(self.ds2_adapter.engine.url))

    def test_pillow_save_to_multiple_databases(self):
        self.assertNotEqual(self.ds1_adapter.engine.url, self.ds2_adapter.engine.url)
        pillow = get_ucr_es_case_pillow(configs=[self.ds_1, self.ds_2])
        self.assertNotEqual(self.ds1_adapter.engine.url, self.ds2_adapter.engine.url)
        sample_doc, _ = get_sample_doc_and_indicators()
        pillow.process_change(doc_to_change(sample_doc))
        self.assertNotEqual(self.ds1_adapter.engine.url, self.ds2_adapter.engine.url)
        self.assertEqual(1, self.ds1_adapter.get_query_object().count())
        self.assertEqual(1, self.ds2_adapter.get_query_object().count())

    def test_pillow_save_to_one_database_at_a_time(self):
        pillow = get_ucr_es_case_pillow(configs=[self.ds_1])

        sample_doc, _ = get_sample_doc_and_indicators()
        pillow.process_change(doc_to_change(sample_doc))

        self.assertEqual(1, self.ds1_adapter.get_query_object().count())
        self.assertEqual(0, self.ds2_adapter.get_query_object().count())

        # save to the other
        pillow = get_ucr_es_case_pillow(configs=[self.ds_2])
        orig_id = sample_doc['_id']
        sample_doc['_id'] = uuid.uuid4().hex
        pillow.process_change(doc_to_change(sample_doc))
        self.assertEqual(1, self.ds1_adapter.get_query_object().count())
        self.assertEqual(1, self.ds2_adapter.get_query_object().count())
        self.assertEqual(1, self.ds1_adapter.get_query_object().filter_by(doc_id=orig_id).count())
        self.assertEqual(1, self.ds2_adapter.get_query_object().filter_by(doc_id=sample_doc['_id']).count())

    def test_report_data_source(self):
        # bootstrap report data sources against indicator data sources
        report_config_template = get_sample_report_config()
        report_config_1 = ReportConfiguration.wrap(report_config_template.to_json())
        report_config_1.config_id = self.ds_1._id
        report_config_2 = ReportConfiguration.wrap(report_config_template.to_json())
        report_config_2.config_id = self.ds_2._id

        # save a few docs to ds 1
        sample_doc, _ = get_sample_doc_and_indicators()
        num_docs = 3
        for i in range(num_docs):
            sample_doc['_id'] = uuid.uuid4().hex
            self.ds1_adapter.save(sample_doc)

        # ds 1 should have data, ds2 should not
        ds1_rows = ConfigurableReportDataSource.from_spec(report_config_1).get_data()
        self.assertEqual(1, len(ds1_rows))
        self.assertEqual(num_docs, ds1_rows[0]['count'])
        ds2_rows = ConfigurableReportDataSource.from_spec(report_config_2).get_data()
        self.assertEqual(0, len(ds2_rows))

        # save one doc to ds 2
        sample_doc['_id'] = uuid.uuid4().hex
        self.ds2_adapter.save(sample_doc)

        # ds 1 should still have same data, ds2 should now have one row
        ds1_rows = ConfigurableReportDataSource.from_spec(report_config_1).get_data()
        self.assertEqual(1, len(ds1_rows))
        self.assertEqual(num_docs, ds1_rows[0]['count'])
        ds2_rows = ConfigurableReportDataSource.from_spec(report_config_2).get_data()
        self.assertEqual(1, len(ds2_rows))
        self.assertEqual(1, ds2_rows[0]['count'])
