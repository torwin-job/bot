from applications.models import Application
from asgiref.sync import sync_to_async

async def create_application(name, phone, service):
    return await sync_to_async(Application.objects.create)(
        name=name,
        phone=phone,
        service=service
    ) 