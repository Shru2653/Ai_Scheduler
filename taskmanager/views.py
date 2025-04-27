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
    # Get system stats
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    
    # Get process information
    processes = []
    context_switches = 0
    total_io_operations = {'disk': 0, 'network': 0, 'printer': 0}
    
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'io_counters']):
        try:
            pinfo = proc.info
            processes.append({
                'pid': pinfo['pid'],
                'name': pinfo['name'],
                'state': pinfo['status'],
                'priority': proc.nice(),
                'cpu_burst': pinfo['cpu_percent'],
                'memory': round(pinfo['memory_info'].rss / (1024 * 1024), 2),  # Convert to MB
                'io_operations': {
                    'disk': pinfo['io_counters'].read_bytes + pinfo['io_counters'].write_bytes if 'io_counters' in pinfo else 0,
                    'network': pinfo['io_counters'].read_bytes + pinfo['io_counters'].write_bytes if 'io_counters' in pinfo else 0
                },
                'waiting_time': 0  # This would need to be calculated based on scheduling
            })
            
            # Count I/O operations
            if 'io_counters' in pinfo:
                total_io_operations['disk'] += pinfo['io_counters'].read_bytes + pinfo['io_counters'].write_bytes
                total_io_operations['network'] += pinfo['io_counters'].read_bytes + pinfo['io_counters'].write_bytes
            
            # Count context switches (simplified)
            if pinfo['status'] == 'running':
                context_switches += 1
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Calculate throughput (processes per second)
    throughput = len(processes) / 60  # Assuming we're measuring over a minute
    
    context = {
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'context_switches': context_switches,
        'throughput': round(throughput, 2),
        'processes': processes,
        'io_disk': total_io_operations['disk'],
        'io_network': total_io_operations['network'],
        'io_printer': 0  # Simulated printer operations
    }
    
    return render(request, 'taskmanager/dashboard.html', context)

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

@login_required
def schedule_tasks(request):
    context = {
        'result': None,
        'avg_tat': 0,
        'avg_wt': 0,
        'algorithm': None,
        'time_quantum': 2
    }
    
    if request.method == "POST":
        algorithm = request.POST.get("algorithm")
        time_quantum = int(request.POST.get("time_quantum", 2))
        
        # Get process details from form
        process_names = request.POST.getlist("process_name[]")
        arrival_times = request.POST.getlist("arrival_time[]")
        burst_times = request.POST.getlist("burst_time[]")
        priorities = request.POST.getlist("priority[]")
        
        # Validate input
        if not all([process_names, arrival_times, burst_times, priorities]):
            context['error'] = "Please fill in all process details"
            return render(request, 'taskmanager/schedule.html', context)
        
        # Create processes list
        processes = []
        for i in range(len(process_names)):
            try:
                processes.append({
                    'name': process_names[i],
                    'arrival_time': int(arrival_times[i]),
                    'execution_time': int(burst_times[i]),
                    'priority': int(priorities[i])
                })
            except ValueError:
                context['error'] = "Invalid input values"
                return render(request, 'taskmanager/schedule.html', context)
        
        # Generate schedule based on selected algorithm
        if algorithm == "round_robin":
            result = round_robin(processes, time_quantum)
        elif algorithm == "priority":
            result = priority_scheduling(processes)
        elif algorithm == "ai":
            result = ai_based_prioritization(processes)
        else:
            result = {"gantt": [], "metrics": []}
        
        # Calculate average metrics
        if result['metrics']:
            total_wt = sum(metric['wt'] for metric in result['metrics'])
            total_tat = sum(metric['tat'] for metric in result['metrics'])
            avg_wt = total_wt / len(result['metrics'])
            avg_tat = total_tat / len(result['metrics'])
            
            context.update({
                'result': result,
                'algorithm': algorithm,
                'time_quantum': time_quantum,
                'avg_wt': round(avg_wt, 2),
                'avg_tat': round(avg_tat, 2)
            })
    
    return render(request, 'taskmanager/schedule.html', context)

