from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Task, SystemStats
from django.shortcuts import render, redirect
import psutil
import datetime
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
# import psutil
# import datetime

#import Schedulers
from .scheduler import round_robin, priority_scheduling, ai_based_prioritization

# List all tasks for the current user
@login_required
def list_tasks(request):
    tasks = Task.objects.filter(user=request.user).values()
    return JsonResponse(list(tasks), safe=False)

# Create a new task (basic version)
@login_required
def create_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        category = request.POST.get('category')
        priority = int(request.POST.get('priority'))
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        Task.objects.create(
            user=request.user,
            title=title,
            description=description,
            category=category,
            priority=priority,
            start_time=start_time,
            end_time=end_time
        )
        return redirect('dashboard')

    return render(request, 'taskmanager/create_task.html')

# Monitor system stats in real time
@login_required
def get_system_stats(request):
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    # Save it to DB
    SystemStats.objects.create(cpu_usage=cpu, memory_usage=memory, disk_usage=disk)

    return JsonResponse({
        'cpu': cpu,
        'memory': memory,
        'disk': disk,
    })

@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user)
    return render(request, 'taskmanager/dashboard.html', {'tasks': tasks})

def system_monitor(request):
    import platform
    import psutil
    from datetime import timedelta

    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    uptime_seconds = psutil.boot_time()
    uptime = timedelta(seconds=(psutil.time.time() - uptime_seconds))

    context = {
        'cpu': cpu,
        'memory': memory,
        'disk': disk,
        'system_info': {
            'platform': platform.system(),
            'processor': platform.processor(),
            'uptime': uptime
        }
    }
    return render(request, 'taskmanager/system_monitor.html', context)

def current_task(request):
    # Get the currently executing task (status = Running)
    current = Task.objects.filter(status='Running').order_by('-start_time').first()

    context = {
        'current_task': current
    }
    return render(request, 'taskmanager/current_task.html', context)


def executing_task_info(request):
    processes = []
    total_wt = 0
    total_tat = 0
    now = datetime.datetime.now()

    for proc in psutil.process_iter(['pid', 'name', 'create_time', 'memory_info', 'cpu_percent']):
        try:
            pinfo = proc.info
            arrival_time = datetime.datetime.fromtimestamp(pinfo['create_time'])
            waiting_time = (now - arrival_time).total_seconds()
            tat = waiting_time  # In real systems, tat = end_time - arrival_time

            memory_used = pinfo['memory_info'].rss / (1024 ** 2)  # MB
            cpu_usage = pinfo['cpu_percent']  # %

            processes.append({
                'pid': pinfo['pid'],
                'name': pinfo['name'],
                'arrival_time': arrival_time.strftime('%Y-%m-%d %H:%M:%S'),
                'waiting_time': round(waiting_time, 2),
                'tat': round(tat, 2),
                'memory_used': round(memory_used, 2),
                'cpu_usage': cpu_usage,
            })

            total_wt += waiting_time
            total_tat += tat
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    context = {
        'processes': processes,
        'avg_wt': round(total_wt / len(processes), 2) if processes else 0,
        'avg_tat': round(total_tat / len(processes), 2) if processes else 0,
    }

    return render(request, 'taskmanager/executing_task_info.html', context)

from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'home.html')

#Schedulers

def schedule_tasks(request):
    # Example tasks for testing; replace this with dynamic user input or database tasks
    tasks = [
        {"name": "Task1", "execution_time": 10, "priority": 2},
        {"name": "Task2", "execution_time": 5, "priority": 1},
        {"name": "Task3", "execution_time": 8, "priority": 3},
    ]
    
    schedule = []  # Default empty schedule
    if request.method == "POST":
        algorithm = request.POST.get("algorithm")  # Get selected algorithm
        time_slice = int(request.POST.get("time_slice", 3))  # Default time slice = 3

        if algorithm == "round_robin":
            schedule = round_robin(tasks, time_slice)
        elif algorithm == "priority":
            schedule = priority_scheduling(tasks)
        elif algorithm == "ai":
            schedule = ai_based_prioritization(tasks)
        else:
            schedule = [{"task": "Unsupported Algorithm", "execution_time": 0}]

        # Debugging output
        print("Generated Schedule:", schedule)

        # Return the schedule to the template
        return render(request, "taskmanager/schedule.html", {"schedule": schedule, "tasks": tasks})

    # Render the page with the default task list
    return render(request, "taskmanager/schedule.html", {"tasks": tasks})

