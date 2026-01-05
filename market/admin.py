from django.contrib import admin
from market.models import Instrument, TradingHoliday, Candle,HistoricalBackfillState, UpstoxToken

# Register your models here.
admin.site.register(Instrument)
admin.site.register(TradingHoliday)
admin.site.register(Candle)
admin.site.register(UpstoxToken)

from django.contrib import admin
from market.models import HistoricalBackfillState


@admin.register(HistoricalBackfillState)
class HistoricalBackfillStateAdmin(admin.ModelAdmin):
    list_display = (
        "instrument",
        "interval",
        "last_fetched_date",
        "retry_count",
        "failed_until",
        "last_error_short",
        "started_at",
        "last_progress_at",
        "updated_at",
    )

    list_filter = (
        "interval",
        "failed_until",
    )

    search_fields = (
        "instrument__symbol",
        "instrument__instrument_key",
    )

    readonly_fields = (
        "started_at",
        "last_progress_at",
        "updated_at",
    )

    ordering = ("-updated_at",)

    def last_error_short(self, obj):
        if not obj.last_error:
            return "-"
        return obj.last_error[:80]

    last_error_short.short_description = "Last Error"
