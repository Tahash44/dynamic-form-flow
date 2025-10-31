import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.forms.models import Form
from apps.reports.serializers import FormReportSerializer
from channels.db import database_sync_to_async

class FormReportConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.form_id = self.scope['url_route']['kwargs']['form_id']
        self.group_name = f'form_{self.form_id}_report'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_report(self, event):
        report_data = event['report']
        await self.send(text_data=json.dumps(report_data))

    @database_sync_to_async
    def get_report_data(self):
        form = Form.objects.get(id=self.form_id)
        serializer = FormReportSerializer(form)
        return serializer.data
