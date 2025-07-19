from services.models import Service
from asgiref.sync import sync_to_async

def format_description(description: str) -> str:
    lines = [line.strip() for line in description.replace('–', '\n–').split('\n') if line.strip()]
    formatted = '\n'.join(f'• {line.lstrip("– ")}' for line in lines)
    return formatted

async def get_all_services():
    return await sync_to_async(list)(Service.objects.all())

async def get_service_by_id(service_id):
    return await sync_to_async(Service.objects.get)(id=service_id) 