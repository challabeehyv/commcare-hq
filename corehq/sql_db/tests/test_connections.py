from collections import Counter

import mock
from django.db import DEFAULT_DB_ALIAS
from django.test import override_settings
from django.test.testcases import SimpleTestCase

from corehq.sql_db.connections import ConnectionManager
from corehq.sql_db.util import get_databases_for_read_query


def _get_db_config(db_name, master=None, delay=None):
    config = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': db_name,
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
    if master:
        config['STANDBY'] = {
            'MASTER': master
        }
        if delay:
            config['STANDBY']['ACCEPTABLE_REPLICATION_DELAY'] = delay
    return config


DATABASES = {
    DEFAULT_DB_ALIAS: _get_db_config('default'),
    'ucr': _get_db_config('ucr', 'default', 5),
    'other': _get_db_config('other', 'default')
}
REPORTING_DATABASES = {
    'default': DEFAULT_DB_ALIAS,
    'ucr': DEFAULT_DB_ALIAS
}


@override_settings(DATABASES=DATABASES, REPORTING_DATABASES=REPORTING_DATABASES)
class ConnectionManagerTests(SimpleTestCase):
    @override_settings(REPORTING_DATABASES={})
    def test_new_settings_empty(self):
        manager = ConnectionManager()
        self.assertEqual(manager.engine_id_django_db_map, {
            'default': 'default',
            'ucr': 'default'
        })

    @override_settings(REPORTING_DATABASES={'default': DEFAULT_DB_ALIAS, 'ucr': 'ucr', 'other': 'other'})
    def test_new_settings(self):
        manager = ConnectionManager()
        self.assertEqual(manager.engine_id_django_db_map, {
            'default': 'default',
            'ucr': 'ucr',
            'other': 'other'
        })

    @mock.patch('corehq.sql_db.util.get_replication_delay_for_standby', return_value=0)
    @mock.patch('corehq.sql_db.util.get_standby_databases', return_value={'ucr', 'other'})
    def test_read_load_balancing(self, *args):
        reporting_dbs = {
            'ucr': {
                'WRITE': 'ucr',
                'READ': [('ucr', 8), ('other', 1), ('default', 1)]
            },
        }
        with override_settings(REPORTING_DATABASES=reporting_dbs):
            manager = ConnectionManager()
            self.assertEqual(manager.engine_id_django_db_map, {
                'default': 'default',
                'ucr': 'ucr',
            })

            # test that load balancing works with a 10% margin for randomness
            total_requests = 10000
            randomness_margin = total_requests * 0.1
            total_weighting = sum(db[1] for db in reporting_dbs['ucr']['READ'])
            expected = {
                alias: weight * total_requests // total_weighting
                for alias, weight in reporting_dbs['ucr']['READ']
            }
            balanced = Counter(manager.get_load_balanced_read_db_alias('ucr') for i in range(total_requests))
            for db, requests in balanced.items():
                self.assertAlmostEqual(requests, expected[db], delta=randomness_margin)

        with override_settings(REPORTING_DATABASES={'default': DEFAULT_DB_ALIAS}):
            manager = ConnectionManager()
            self.assertEqual(
                [DEFAULT_DB_ALIAS] * 3,
                [manager.get_load_balanced_read_db_alias(DEFAULT_DB_ALIAS) for i in range(3)]
            )

    @mock.patch('corehq.sql_db.util.get_replication_delay_for_standby', lambda x: {'other': 4}[x])
    @mock.patch('corehq.sql_db.util.get_standby_databases', return_value={'other'})
    def test_standby_filtering(self, *args):
        reporting_dbs = {
            'ucr_engine': {
                'WRITE': 'ucr',
                'READ': [('ucr', 8), ('other', 1)]
            },
        }
        with override_settings(REPORTING_DATABASES=reporting_dbs):
            # should always return the `ucr` db since `other` has bad replication delay
            manager = ConnectionManager()
            self.assertEqual(
                ['ucr', 'ucr', 'ucr'],
                [manager.get_load_balanced_read_db_alias('ucr_engine') for i in range(3)]
            )

    @mock.patch('corehq.sql_db.util.get_replication_delay_for_standby', lambda x: {'ucr': 6, 'other': 4}[x])
    @mock.patch('corehq.sql_db.util.get_standby_databases', return_value={'ucr', 'other'})
    def test_get_databases_for_read_query_filter(self, *args):
        self.assertEqual(
            get_databases_for_read_query({'ucr', 'other'}),
            set()
        )

    @mock.patch('corehq.sql_db.util.get_replication_delay_for_standby', lambda x: {'ucr': 5, 'other': 3}[x])
    @mock.patch('corehq.sql_db.util.get_standby_databases', return_value={'ucr', 'other'})
    def test_get_databases_for_read_query_pass(self, *args):
        self.assertEqual(
            get_databases_for_read_query({'ucr', 'other'}),
            {'ucr', 'other'}
        )
