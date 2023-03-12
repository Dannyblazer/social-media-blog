from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturalday
from datetime import datetime

user = get_user_model()

MSG_TYPE_MESSAGE = 0

class PublicChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = "publich_chat"
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive_json(self, content):
        command = content.get("command", None)
        try:
            if command == "send":
                if len(content['message'].lstrip()) == 0:
                    raise ClientError(422, "You can't send an empty message!")
            # Send message to room group via send_message()
                await self.send_message(content['message'])
        except ClientError as e:
            errorData = {}
            errorData['error'] = e.code
            if e.message:
                errorData['message'] = e.message
            await self.send_json(errorData)

    
    async def send_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name, 
            {
                "type": "chat_message",
                "profile_image": self.scope['user'].profile_image.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                'message': message,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        timestamp = calculate_timestamp(timezone.now())
        # Send message to WebSocket
        await self.send_json({
            'msg_type': MSG_TYPE_MESSAGE,
            "profile_image": event['profile_image'],
            "username": event['username'],
            "user_id": event['user_id'],
            "message": event['message'],
            "naturalday": timestamp
        })

class ClientError(Exception):
    """
    Custom exception class that is caught by the webscoket receive()
    handler and translated into a send back to the client
    """
    def __init__(self, code, message):
        super().__init__(code)
        self.code = code
        if message:
            self.message = message

def calculate_timestamp(timestamp):
    """
    Convert the timestamp using humanize to something nice
    """
    # Today or Yesterday
    if ((naturalday(timestamp)=="today") or (naturalday(timestamp)=="yesterday")):
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp)} at {str_time}"

    # Other day
    else:
        str_time = datetime.strftime(timestamp, "%m/%d/%Y")
        ts = f"{str_time}"
    return ts
