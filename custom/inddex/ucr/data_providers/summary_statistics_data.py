from memoized import memoized

from custom.inddex.ucr.data_providers.mixins import SummaryStatisticsDataMixin


class SummaryStatsNutrientDataProvider(SummaryStatisticsDataMixin):
    total_row = None
    title = 'Group-level Summary Statistics by Nutrient Intake'
    slug = 'group_level_summary_statistics_by_nutrient_intake'
    headers_in_order = [
        'nutrient', 'mean', 'median', 'std.Dev', '5_percent', '25_percent',
        '50_percent', '75_percent', '95_percent'
    ]

    def __init__(self, config, filters_config):
        self.config = config
        self.filters_config = filters_config

    @property
    def filter_values(self):
        return self.filters_config

    @property
    @memoized
    def rows(self):
        return [
            ['energy_kcal', '125.8', '4.3', '177.0', '0.0', '0.0', '4.3', '190.7', '430.5'],
            ['water_g', '82.6', '26.3', '128.1', '0.0', '0.0', '26.3', '98.7', '312.1'],
            ['protein_g', '44.6', '31.6', '57.8', '0.0', '0.0', '31.6', '51.1', '145.5'],
            ['all_other_nutrients', '', '', '', '', '', '', '', ''],
        ]
