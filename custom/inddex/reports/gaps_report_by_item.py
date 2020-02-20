from custom.inddex.filters import GapTypeFilter, GapDescriptionFilter, FoodTypeFilter, FoodCodeFilter, \
    RecallStatusFilter
from custom.inddex.ucr.data_providers.gaps_report_by_item_data import GapsReportByItemDetailsData, \
    GapsReportByItemSummaryData
from custom.inddex.utils import MultiTabularReport


class GapsReportByItem(MultiTabularReport):
    title = '1b: Gaps Report By Item'
    name = title
    slug = 'gaps_report_by_item'

    @property
    def fields(self):
        fields = super().fields
        fields += [
            GapTypeFilter,
            GapDescriptionFilter,
            FoodTypeFilter,
            FoodCodeFilter,
            RecallStatusFilter
        ]

        return fields

    @property
    def report_config(self):
        report_config = super().report_config
        report_config.update(
            gap_type=self.gap_type,
            gap_description=self.gap_description,
            food_code=self.food_code,
            food_type=self.food_type,
            recall_status=self.recall_status
        )

        return report_config

    @property
    def gap_type(self):
        return self.request.GET.get('gap_type') or ''

    @property
    def gap_description(self):
        return self.request.GET.get('gap_description') or ''

    @property
    def food_code(self):
        return self.request.GET.get('food_code') or ''

    @property
    def food_type(self):
        return self.request.GET.get('food_type') or ''

    @property
    def recall_status(self):
        return self.request.GET.get('recall_status') or ''

    @property
    def data_providers(self):
        return [
            GapsReportByItemSummaryData(config=self.report_config),
            GapsReportByItemDetailsData(config=self.report_config)
        ]
