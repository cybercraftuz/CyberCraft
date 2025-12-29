import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.server_id = self.scope["url_route"]["kwargs"]["server_id"]
        self.group = f"progress_{self.server_id}"

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def send_log(self, event):
        await self.send(text_data=json.dumps({"log": event["log"]}))
