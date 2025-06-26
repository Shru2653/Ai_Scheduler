# scheduler/views.py

from django.shortcuts import render, redirect
from .scheduler import round_robin, priority_scheduling, ai_based_prioritization

def input_processes(request):
    if request.method == "POST":
        processes = []
        num_processes = int(request.POST.get('num_processes', 0))
        algorithm = request.POST.get('algorithm')

        for i in range(num_processes):
            name = request.POST.get(f'name_{i}')
            arrival = int(request.POST.get(f'arrival_{i}'))
            burst = int(request.POST.get(f'burst_{i}'))
            priority = int(request.POST.get(f'priority_{i}', 0))  # default 0 if missing

            processes.append({
                'process_name': name,
                'arrival_time': arrival,
                'burst_time': burst,
                'priority': priority,
            })

        # Save in session
        request.session['processes'] = processes
        request.session['algorithm'] = algorithm

        return redirect('visualize_schedule')

    return render(request, 'scheduler/process_input.html')

def visualize_schedule(request):
    processes = request.session.get('processes', [])
    algorithm = request.session.get('algorithm', 'round_robin')

    if not processes:
        return redirect('input_processes')

    if algorithm == 'round_robin':
        result = round_robin(processes, time_quantum=2)
    elif algorithm == 'priority_scheduling':
        result = priority_scheduling(processes)
    else:
        result = ai_based_prioritization(processes)

    # Calculate performance metrics
    total_turnaround = sum(p['turnaround_time'] for p in processes)
    total_waiting = sum(p['waiting_time'] for p in processes)
    num_processes = len(processes)
    
    # Calculate CPU utilization
    total_burst_time = sum(p['burst_time'] for p in processes)
    total_time = max(p['completion_time'] for p in processes)
    cpu_utilization = (total_burst_time / total_time) * 100 if total_time > 0 else 0

    context = {
        'result': result,
        'processes': processes,
        'avg_turnaround_time': total_turnaround / num_processes if num_processes > 0 else 0,
        'avg_waiting_time': total_waiting / num_processes if num_processes > 0 else 0,
        'cpu_utilization': cpu_utilization,
        'animation_steps': result  # Pass the animation steps directly
    }

    return render(request, 'scheduler/visualize.html', context)
