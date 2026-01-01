from django.urls import path
from market.views import upstox_login, upstox_callback

urlpatterns = [
    path("upstox/login/", upstox_login, name="upstox_login"),
    path("upstox/callback/", upstox_callback, name="upstox_callback"),
]
