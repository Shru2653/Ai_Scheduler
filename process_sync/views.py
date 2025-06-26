from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import uuid
from .models import MutexLock, ProcessQueue, QueueItem

# Create your views here.

def index(request):
    return render(request, 'process_sync/index.html')

@require_http_methods(["POST"])
def acquire_lock(request):
    resource_name = request.POST.get('resource_name')
    timeout = int(request.POST.get('timeout', 30))
    process_id = str(uuid.uuid4())

    if not resource_name:
        return JsonResponse({'error': 'Resource name is required'}, status=400)

    mutex, created = MutexLock.objects.get_or_create(resource_name=resource_name)
    
    if mutex.acquire(process_id, timeout):
        return JsonResponse({
            'success': True,
            'process_id': process_id,
            'locked_at': mutex.locked_at.isoformat(),
            'expires_at': mutex.expires_at.isoformat()
        })
    return JsonResponse({
        'success': False,
        'message': 'Resource is already locked'
    }, status=409)

@require_http_methods(["POST"])
def release_lock(request):
    resource_name = request.POST.get('resource_name')
    process_id = request.POST.get('process_id')

    if not all([resource_name, process_id]):
        return JsonResponse({'error': 'Resource name and process ID are required'}, status=400)

    try:
        mutex = MutexLock.objects.get(resource_name=resource_name)
        if mutex.release(process_id):
            return JsonResponse({'success': True})
        return JsonResponse({
            'success': False,
            'message': 'Lock is held by another process'
        }, status=403)
    except MutexLock.DoesNotExist:
        return JsonResponse({'error': 'Resource not found'}, status=404)

@require_http_methods(["POST"])
def create_queue(request):
    queue_name = request.POST.get('queue_name')
    if not queue_name:
        return JsonResponse({'error': 'Queue name is required'}, status=400)

    queue, created = ProcessQueue.objects.get_or_create(name=queue_name)
    return JsonResponse({
        'success': True,
        'queue_id': queue.id,
        'name': queue.name
    })

@require_http_methods(["POST"])
def add_to_queue(request):
    queue_name = request.POST.get('queue_name')
    priority = int(request.POST.get('priority', 0))
    process_id = str(uuid.uuid4())

    if not queue_name:
        return JsonResponse({'error': 'Queue name is required'}, status=400)

    try:
        queue = ProcessQueue.objects.get(name=queue_name)
        item = QueueItem.objects.create(
            queue=queue,
            process_id=process_id,
            priority=priority
        )
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'process_id': process_id,
            'status': item.status
        })
    except ProcessQueue.DoesNotExist:
        return JsonResponse({'error': 'Queue not found'}, status=404)

@require_http_methods(["GET"])
def get_queue_status(request):
    queue_name = request.GET.get('queue_name')
    if not queue_name:
        return JsonResponse({'error': 'Queue name is required'}, status=400)

    try:
        queue = ProcessQueue.objects.get(name=queue_name)
        items = queue.items.all()
        return JsonResponse({
            'success': True,
            'queue_name': queue.name,
            'items': [{
                'process_id': item.process_id,
                'priority': item.priority,
                'status': item.status,
                'created_at': item.created_at.isoformat(),
                'started_at': item.started_at.isoformat() if item.started_at else None,
                'completed_at': item.completed_at.isoformat() if item.completed_at else None
            } for item in items]
        })
    except ProcessQueue.DoesNotExist:
        return JsonResponse({'error': 'Queue not found'}, status=404)
