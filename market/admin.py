from django.contrib import admin
from market.models import Instrument, TradingHoliday, Candle,HistoricalBackfillState, UpstoxToken

# Register your models here.
admin.site.register(Instrument)
admin.site.register(TradingHoliday)
admin.site.register(Candle)
admin.site.register(HistoricalBackfillState)
admin.site.register(UpstoxToken)