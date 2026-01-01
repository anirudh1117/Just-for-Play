import json
from channels.generic.websocket import AsyncWebsocketConsumer


class JobLogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope["url_route"]["kwargs"]["job_id"]
        self.group_name = f"job_{self.job_id}"

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connected for job {self.job_id}")

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for job {self.job_id}")

    async def receive(self, text_data):
        # We don't need incoming messages for now
        pass

    async def send_job_log(self, event):
        """
        Called when a new log is added to this job.
        """
        await self.send(text_data=json.dumps({
            "timestamp": event["timestamp"],
            "message": event["message"]
        }))
