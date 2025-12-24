import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import *
class LeaveRequestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        leave_request = await sync_to_async(leaveRequest.objects.create)(
            leave_from=data['leave_from'],
            leave_to=data['leave_to'],
            leave_type=data['leave_type'],
            Work_delegated=data['Work_delegated'],
            Comments_on_work_delegation=data['Comments_on_work_delegation'],
            status='pending',
            employeeID=Employee.objects.get(employeeID=data['employeeID'])
        )
        # print("Leave request created")

        duration = leave_request.get_duration()
        if duration <= 3:
            # Forward to level 1 approval
            asyncio.create_task(level_1_approval(leave_request.id))
        elif duration <= 15:
            # Forward to level 2 approval
            asyncio.create_task(level_2_approval(leave_request.id))
        else:
            # Forward to level 3 approval
            asyncio.create_task(level_3_approval(leave_request.id))

        # Send a response back to the client
        await self.send(json.dumps({'success': True}))