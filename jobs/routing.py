from django.urls import re_path
from .consumers import JobLogConsumer

websocket_urlpatterns = [
    re_path(r"ws/job/(?P<job_id>\d+)/$", JobLogConsumer.as_asgi()),
]
