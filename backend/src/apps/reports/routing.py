from django.urls import re_path
from reports import consumers

websocket_urlpatterns = [
    re_path(r'ws/forms/(?P<form_id>\d+)/report/$', consumers.FormReportConsumer.as_asgi()),
]
