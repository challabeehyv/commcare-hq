from django.db import models, transaction, connections

from corehq.warehouse.const import (
    APP_STATUS_FACT_SLUG,
    FORM_FACT_SLUG,
    USER_DIM_SLUG,
    DOMAIN_DIM_SLUG,
    FORM_STAGING_SLUG,
    SYNCLOG_STAGING_SLUG,
)

from .dimensions import UserDim, DomainDim
from corehq.form_processor.models import XFormInstanceSQL
from corehq.sql_db.routers import db_for_read_write
from corehq.util.test_utils import unit_testing_only
from corehq.warehouse.etl import CustomSQLETLMixin
from corehq.warehouse.models.shared import WarehouseTableMixin


class BaseFact(models.Model, WarehouseTableMixin):

    @classmethod
    @transaction.atomic
    def commit(cls, start_datetime, end_datetime):
        cls.load(start_datetime, end_datetime)

    class Meta:
        abstract = True

    @classmethod
    @unit_testing_only
    def clear_records(cls):
        database = db_for_read_write(cls)
        with connections[database].cursor() as cursor:
            cursor.execute("TRUNCATE {}".format(cls._meta.db_table))


class FormFact(BaseFact, CustomSQLETLMixin):
    '''
    Represents the staging table to dump data before loading into the FormFact

    Grain: form_id
    '''
    slug = FORM_FACT_SLUG

    form_id = models.CharField(max_length=255, unique=True)

    domain = models.CharField(max_length=255, default=None)
    app_id = models.CharField(max_length=255, null=True)
    xmlns = models.CharField(max_length=255, default=None)
    user_id = models.CharField(max_length=255, null=True)

    user_dim = models.ForeignKey(UserDim, on_delete=models.PROTECT)
    domain_dim = models.ForeignKey(DomainDim, on_delete=models.PROTECT)

    # The time at which the server has received the form
    received_on = models.DateTimeField(db_index=True)
    deleted_on = models.DateTimeField(null=True)
    edited_on = models.DateTimeField(null=True)
    last_modified = models.DateTimeField(null=True)

    build_id = models.CharField(max_length=255, null=True)
    state = models.PositiveSmallIntegerField(
        choices=XFormInstanceSQL.STATES,
        default=XFormInstanceSQL.NORMAL
    )

    @classmethod
    def dependencies(cls):
        return [
            USER_DIM_SLUG,
            DOMAIN_DIM_SLUG,
            FORM_STAGING_SLUG,
        ]


class ApplicationStatusFact(BaseFact, CustomSQLETLMixin):
    '''
    Application Status Report Fact Table

    Grain: app_id, user_id
    '''
    slug = APP_STATUS_FACT_SLUG

    # TODO: Add app dimension
    # app_dim = models.CharField(max_length=255)

    user_dim = models.ForeignKey(UserDim, on_delete=models.PROTECT)

    last_form_submission_date = models.DateTimeField(null=True)
    last_sync_log_date = models.DateTimeField(null=True)

    last_form_app_build_version = models.CharField(max_length=255)
    last_form_app_commcare_version = models.CharField(max_length=255)
    last_form_app_source = models.CharField(max_length=255)

    last_sync_log_app_build_version = models.CharField(max_length=255)
    last_sync_log_app_commcare_version = models.CharField(max_length=255)
    last_sync_log_app_source = models.CharField(max_length=255)

    @classmethod
    def dependencies(cls):
        return [
            USER_DIM_SLUG,
            FORM_STAGING_SLUG,
            FORM_FACT_SLUG,
            SYNCLOG_STAGING_SLUG,
        ]
