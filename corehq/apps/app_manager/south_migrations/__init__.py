import logging
from couchdbkit import ResourceNotFound
from dimagi.utils.couch import sync_docs
from dimagi.utils.couch.database import iter_docs
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from corehq.apps.app_manager.const import APP_V1
from corehq.apps.app_manager.detail_screen import get_column_xpath_generator
from corehq.apps.app_manager.models import Application
from corehq.apps.app_manager.xpath import dot_interpolate
import corehq.apps.app_manager.models as app_models
import sys


logger = logging.getLogger(__name__)


class AppMigrationMixin(object):
    """Subclass this on a south-migration model to run data-migration on apps
    """

    @classmethod
    def migrate_app(cls, app_doc):
        """Modify app_doc and return True if app should be saved
        """
        raise NotImplementedError()

    def get_app_ids(self):
        """List of app_ids of apps that need to be migrated
        """
        raise NotImplementedError()

    @staticmethod
    def _check_or_create_couch_view():
        # if the view doesn't exist manually create it.
        # typically for initial load or tests.
        try:
            Application.get_db().view(
                'app_manager/applications',
                limit=1,
            ).all()
        except ResourceNotFound:
            sync_docs.sync(app_models, verbosity=2)

    def forwards(self, orm):
        self._check_or_create_couch_view()

        errors = []

        def _migrate_app_ids(app_ids):
            to_save = []
            count = len(app_ids)
            logger.info('migrating {} apps'.format(count))
            for i, app_doc in enumerate(iter_docs(Application.get_db(), app_ids)):
                try:
                    if app_doc["doc_type"] in ["Application", "Application-Deleted"]:
                        application = Application.wrap(app_doc)
                        should_save = self.migrate_app(application)
                        if should_save:
                            to_save.append(application)
                            if len(to_save) > 25:
                                self.bulk_save(to_save)
                                logger.info('completed {}/{} apps'.format(i, count))
                                to_save = []
                except Exception:
                    errors.append("App {id} not properly migrated because {error}".format(id=app_doc['_id'],
                                                                                          error=sys.exc_info()[0]))
            if to_save:
                self.bulk_save(to_save)

        logger.info('migrating applications')
        _migrate_app_ids(self.get_app_ids())

        if errors:
            logger.info('\n'.join(errors))

    @classmethod
    def bulk_save(cls, apps):
        Application.get_db().bulk_save(apps)
        for app in apps:
            logger.info("Filter migration on app {id} complete.".format(id=app.id))

    def backwards(self, orm):
        pass

    models = {}
    complete_apps = ['app_manager']


class AppFilterMigrationMixIn(AppMigrationMixin):
    """
    This is the main data migration code for the filter changes.
    """

    def get_app_ids(self):
        # this is the only method that migration subclasses should override
        raise NotImplementedError()

    def _get_main_app_ids(self):
        return self._get_app_ids([None, None])

    def _get_released_app_ids(self):
        return self._get_app_ids(['^ReleasedApplications'])

    def _get_all_app_ids(self):
        return self._get_app_ids([None])

    def _get_app_ids(self, startkey):
        return {r['id'] for r in Application.get_db().view(
            'app_manager/applications',
            startkey=startkey,
            endkey=startkey + [{}],
            reduce=False,
        ).all()}

    @classmethod
    def migrate_app(cls, app):
        filter_combination_func = cls.combine_and_interpolate_V2_filters
        if app.application_version == APP_V1:
            filter_combination_func = \
                cls.combine_and_interpolate_V1_filters

        needs_save = False
        for module in app.get_modules():
            for detail_type in ["case_details", "task_details", "goal_details", "product_details"]:
                details = getattr(module, detail_type, None)
                if details is None:
                    # This module does not have the given detail_type
                    continue
                detail = details.short
                # already migrated - don't bother saving again
                if detail.filter:
                    return False
                combined_filter_string = filter_combination_func(
                    detail.get_columns(), app, module, detail
                )
                if combined_filter_string and detail.filter != combined_filter_string:
                    detail.filter = combined_filter_string
                    needs_save = True
        return needs_save

    @classmethod
    def combine_and_interpolate_V1_filters(cls, columns, app, module, detail):
        """
        Return a single filter xpath generated by ANDing together the given
        componenets. Also replaces "."s with the corresponding xpath. The
        interpolation here is specific to v1 apps! use
        combine_and_interpolate_V2_filters for V2 apps.
        :param column_filters: A list of columns
        :param app:
        :param module:
        :param detail:
        :return:
        """
        filters = []
        for i, column in enumerate(columns):
            if column.format == 'filter':
                value = dot_interpolate(
                    column.filter_xpath,
                    '%s_%s_%s' % (column.model, column.field, i + 1)
                )
                filters.append("(%s)" % value)
        xpath = ' and '.join(filters)
        return cls.partial_escape(xpath)

    @classmethod
    def partial_escape(cls, xpath):
        """
        Copied from http://stackoverflow.com/questions/275174/how-do-i-perform-html-decoding-encoding-using-python-django
        but without replacing the single quote
        """
        return mark_safe(
            force_unicode(xpath).replace(
                '&', '&amp;'
            ).replace(
                '<', '&lt;'
            ).replace(
                '>', '&gt;'
            ).replace(
                '"', '&quot;'
            )
        )

    @classmethod
    def combine_and_interpolate_V2_filters(cls, columns, app, module, detail):
        """
        Return a single filter xpath generated by ANDing together the given
        componenets. Also replaces "."s with the corresponding xpath.
        The interpolation here is specific to v2 apps! use
        combine_and_interpolate_V1_filters for V1 apps.
        :param column_filters: A list of columns
        :param app:
        :param module:
        :param detail:
        :return:
        """
        interpolated_filters = []
        for column in columns:
            if column.format == "filter":
                # filters might have a "." in them like: . = "VT"
                # We need to replace these dots with the names of the
                # properties that they refer to.
                #
                # So, if we had a case property called "state", the filter
                # xpath would be converted to: state = "VT"

                # The string that will replace "."s
                replacer_xpath = get_column_xpath_generator(
                    app, module, detail, column
                ).xpath

                # The filter with "."s replaced
                interpolated_xpath = dot_interpolate(
                    column.filter_xpath, replacer_xpath
                )

                interpolated_filters.append(interpolated_xpath)

        combined_filter = ' and '.join(
            '(%s)' % f for f in interpolated_filters
        )

        return combined_filter
