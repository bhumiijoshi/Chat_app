import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from chat_app.models import Room, Message


class ChatConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None  
        
    # When user connects to websocket
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name'] # Getting room name from url
        self.room_group_name = f'chat_{self.room_name}' # Creating group name 
        self.room = Room.objects.get(name=self.room_name) # Getting room object's instance
        self.user = self.scope['user'] # Getting User from scope
        self.user_inbox = f'inbox_{self.user.username}' # Creating inbox name 
    
        # Accepting the connection 
        self.accept()

        # Join the room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        # Send the user list to the newly joined user
        self.send(json.dumps({
            'type': 'user_list',
            'users': [user.username for user in self.room.online.all()],
        }))

        if self.user.is_authenticated:
          
            # Create a user inbox for private messages
            async_to_sync(self.channel_layer.group_add)(
                self.user_inbox,
                self.channel_name,
            )
          
            # Send the join event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'user': self.user.username,
                }
            )
            # Adding current user into online user
            self.room.online.add(self.user)

    # When user disconnect from websocket
    def disconnect(self, close_code):
        
        # Remove from the room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

        if self.user.is_authenticated:
            # Delete the user inbox for private messages
            async_to_sync(self.channel_layer.group_add)(
                self.user_inbox,
                self.channel_name,
            )
          
            # Send the leave event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user': self.user.username,
                }
            )
            
            # Remove user from online user
            self.room.online.remove(self.user)

    # When socket receives message from client
    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if not self.user.is_authenticated:
            return

        if message.startswith('/pm '):
            split = message.split(' ', 2)
            target = split[1]
            target_msg = split[2]

            # Send private message to the target
            async_to_sync(self.channel_layer.group_send)(
                f'inbox_{target}',
                {
                    'type': 'private_message',
                    'user': self.user.username,
                    'message': target_msg,
                }
            )
            # Send private message delivered to the user
            self.send(json.dumps({
                'type': 'private_message_delivered',
                'target': target,
                'message': target_msg,
            }))
            
            # Creating private message 
            Message.objects.create(user=self.user, room=self.room, content=target_msg)
            return
        

        # Send chat message event to the room
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user': self.user.username,
                'message': message,
            }
        )
        # Creating message
        Message.objects.create(user=self.user, room=self.room, content=message)

    # Events as per their type
    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))

    def private_message(self, event):
        self.send(text_data=json.dumps(event))

    def private_message_delivered(self, event):
        self.send(text_data=json.dumps(event))
 