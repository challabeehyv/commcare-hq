from django.utils.translation import ugettext_lazy as _

from sqlagg.columns import SimpleColumn

from corehq.apps.reports.datatables import DataTablesColumn
from corehq.apps.reports.filters.base import BaseSingleOptionFilter
from corehq.apps.reports.filters.dates import DatespanFilter
from corehq.apps.reports.sqlreport import DatabaseColumn, SqlData
from corehq.apps.userreports.util import get_table_name
from custom.inddex.const import FOOD_CONSUMPTION


class DateRangeFilter(DatespanFilter):
    label = _('Date Range')


class AgeRangeFilter(BaseSingleOptionFilter):
    slug = 'age_range'
    label = _('Age Range')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('0-5.9 months', _('0-5.9 months')),
            ('06-59 months', _('06-59 months')),
            ('5-6 years', _('5-6 years')),
            ('7-10 years', _('7-10 years')),
            ('11-14 years', _('11-14 years')),
            ('15-49 years', _('15-49 years')),
            ('50-64 years', _('50-64 years')),
            ('65+ years', _('65+ years'))
        ]


class GenderFilter(BaseSingleOptionFilter):
    slug = 'gender'
    label = _('Gender')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('male', _('Male')),
            ('female', _('Female'))
        ]


class PregnancyFilter(BaseSingleOptionFilter):
    slug = 'pregnant'
    label = _('Pregnancy')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('yes', _('Yes')),
            ('no', _('No')),
        ]


class SettlementAreaFilter(BaseSingleOptionFilter):
    slug = 'urban_rural'
    label = _('Urban/Rural')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('per-urban', _('Peri-urban')),
            ('urban', _('Urban')),
            ('rural', _('Rural'))
        ]


class BreastFeedingFilter(BaseSingleOptionFilter):
    slug = 'breastfeeding'
    label = _('Breastfeeding')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('yes', _('Yes')),
            ('no', _('No')),
        ]


class SupplementsFilter(BaseSingleOptionFilter):
    slug = 'supplements'
    label = _('Supplement Use')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('yes', _('Yes')),
            ('no', _('Not'))
        ]


class RecallStatusFilter(BaseSingleOptionFilter):
    slug = 'recall_status'
    label = _('Recall Status')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('Open', _('Not Completed')),
            ('Completed', _('Completed'))
        ]


class GapDescriptionFilter(BaseSingleOptionFilter):
    slug = 'gap_description'
    label = _('Gap description')
    default_text = _('All')

    @property
    def options(self):
        return [
            (x, x) for x in [
                '1 - conversion factor available',
                '1 - fct data available',
                '2 - using conversion factor from base term food code',
                '2 - using fct data from base term food code',
                '3 - using fct data from reference food code',
                '7 - ingredient(s) contain fct data gaps',
                '8 - no conversion factor available',
                '8 - no fct data available',
            ]
        ]


class GapTypeFilter(BaseSingleOptionFilter):
    slug = 'gap_type'
    label = _('Gap type')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('conversion factor', 'conversion factor'),
            ('fct', 'fct'),
        ]


class FoodTypeFilter(BaseSingleOptionFilter):
    slug = 'food_type'
    label = _('Food type')
    default_text = _('All')

    @property
    def options(self):
        return [
            (x, x) for x in ['food_item', 'non_std_food_item', 'std_recipe', 'non_std_recipe']
        ]


class CaseOwnerData(SqlData):
    engine_id = 'ucr'
    filters = []
    group_by = ['owner_name']
    headers = [DataTablesColumn('Case owner')]
    columns = [DatabaseColumn('Case owner', SimpleColumn('owner_name'))]

    @property
    def table_name(self):
        return get_table_name(self.config['domain'], FOOD_CONSUMPTION)


class CaseOwnersFilter(BaseSingleOptionFilter):
    slug = 'case_owners'
    label = _('Case Owners')
    default_text = _('All')

    @property
    def options(self):
        owner_data = CaseOwnerData(config={'domain': self.domain})
        names = {
            owner['owner_name']
            for owner in owner_data.get_data()
            if owner.get('owner_name')
        }
        return [(x, x) for x in names]


class FaoWhoGiftFoodGroupDescriptionFilter(BaseSingleOptionFilter):
    slug = 'fao_who_gift_food_group_description'
    label = _('FAO/WHO GIFT Food Group Description')
    default_text = _('All')

    @property
    def options(self):
        return [
            (x, x) for x in [
                'Cereals and their products (1)', 'Roots, tubers, plantains and their products (2)',
                'Pulses, seeds and nuts and their products (3)', 'Milk and milk products (4)',
                'Eggs and their products (5)', 'Fish, shellfish and their products (6)',
                'Meat and meat products (7)', 'Insects, grubs and their products (8)',
                'Vegetables and their products( 9)', 'Fruits and their products (10)',
                'Fats and oils (11)', 'Sweets and sugars (12)', 'Spices and condiments (13)', 'Beverages (14)',
                'Foods for particular nutritional uses (15)', 'Food supplements and similar (16)',
                'Food additives (17)', 'Composite foods (18)', 'Savoury snacks (19)',
            ]
        ]
