from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Task, SystemStats
from django.shortcuts import render, redirect
import psutil
import datetime
from django.utils.timezone import now
#import Schedulers
from .scheduler import round_robin, priority_scheduling, ai_based_prioritization, user_priority_scheduling, multilevel_feedback_queue, deadline_scheduling, shortest_job_first
from .recommender import ProcessRecommender
from django.views.decorators.csrf import csrf_exempt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import io
import base64
from django.http import HttpResponse
import tempfile, os
from matplotlib.animation import PillowWriter

# List all tasks for the current user
@login_required
def list_tasks(request):
    tasks = Task.objects.filter(user=request.user).values()
    return JsonResponse(list(tasks), safe=False)

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
        'io_printer': 0,  # Simulated printer operations
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
    return redirect('taskmanager:dashboard')

#Schedulers

# Initialize the recommender
recommender = ProcessRecommender()

@login_required
def schedule_tasks(request):
    context = {
        'result': None,
        'avg_tat': 0,
        'avg_wt': 0,
        'cpu_utilization': 0,
        'algorithm': None,
        'time_quantum': 2,
        'error': None,
        'recommendations': None
    }
    
    if request.method == "POST":
        try:
            algorithm = request.POST.get("algorithm")
            if not algorithm:
                context['error'] = "Please select a scheduling algorithm"
                return render(request, 'taskmanager/schedule.html', context)
            
            # Get time quantum only for Round Robin and MLFQ
            time_quantum = 2  # Default value
            if algorithm in ["round_robin", "mlfq"]:
                try:
                    time_quantum = int(request.POST.get("time_quantum", 2))
                    if time_quantum <= 0:
                        context['error'] = "Time quantum must be a positive integer"
                        return render(request, 'taskmanager/schedule.html', context)
                except ValueError:
                    context['error'] = "Invalid time quantum value"
                    return render(request, 'taskmanager/schedule.html', context)
            
            # Get process details from form
            process_names = request.POST.getlist("process_name[]")
            arrival_times = request.POST.getlist("arrival_time[]")
            burst_times = request.POST.getlist("burst_time[]")
            priorities = request.POST.getlist("priority[]")
            deadlines = request.POST.getlist("deadline[]")
            
            # Validate input
            if not all([process_names, arrival_times, burst_times]):
                context['error'] = "Please fill in all process details"
                return render(request, 'taskmanager/schedule.html', context)
            
            # For Priority and AI-Based Scheduling, priorities are required
            if algorithm in ["priority", "ai"] and not priorities:
                context['error'] = "Priority values are required for Priority Scheduling and AI-Based Prioritization"
                return render(request, 'taskmanager/schedule.html', context)
            
            # For Deadline Scheduling, deadlines are required
            if algorithm == "deadline" and not deadlines:
                context['error'] = "Deadline values are required for Deadline Scheduling"
                return render(request, 'taskmanager/schedule.html', context)
            
            # Create processes list
            processes = []
            recommendations = []
            
            for i in range(len(process_names)):
                try:
                    arrival_time = int(arrival_times[i])
                    burst_time = int(burst_times[i])
                    
                    if arrival_time < 0:
                        context['error'] = f"Invalid arrival time for process {process_names[i]}"
                        return render(request, 'taskmanager/schedule.html', context)
                    
                    if burst_time <= 0:
                        context['error'] = f"Invalid burst time for process {process_names[i]}"
                        return render(request, 'taskmanager/schedule.html', context)
                    
                    process_data = {
                        'name': process_names[i],
                        'arrival_time': arrival_time,
                        'execution_time': burst_time,
                    }
                    
                    # Add priority only for Priority and AI-Based Scheduling
                    if algorithm in ["priority", "ai"] and i < len(priorities):
                        try:
                            priority = int(priorities[i])
                            if priority <= 0:
                                context['error'] = f"Invalid priority for process {process_names[i]}"
                                return render(request, 'taskmanager/schedule.html', context)
                            process_data['priority'] = priority
                        except ValueError:
                            context['error'] = f"Invalid priority value for process {process_names[i]}"
                            return render(request, 'taskmanager/schedule.html', context)
                    else:
                        process_data['priority'] = 1
                    
                    # Add deadline for deadline scheduling
                    if algorithm == "deadline" and i < len(deadlines):
                        try:
                            deadline = int(deadlines[i])
                            if deadline <= 0:
                                context['error'] = f"Invalid deadline for process {process_names[i]}"
                                return render(request, 'taskmanager/schedule.html', context)
                            process_data['deadline'] = deadline
                        except ValueError:
                            context['error'] = f"Invalid deadline value for process {process_names[i]}"
                            return render(request, 'taskmanager/schedule.html', context)
                    
                    processes.append(process_data)
                    
                    # Get recommendations for each process
                    recommendation_data = {
                        'arrival_time': arrival_time,
                        'burst_time': burst_time
                    }
                    if algorithm in ["priority", "ai"]:
                        recommendation_data['priority'] = process_data['priority']
                    elif algorithm == "deadline":
                        recommendation_data['deadline'] = process_data['deadline']
                    
                    recommendations.append({
                        'process_name': process_names[i],
                        'recommendations': recommender.get_recommendations(algorithm, recommendation_data),
                        'user_values': {
                            'arrival_time': arrival_time,
                            'burst_time': burst_time,
                            'priority': process_data.get('priority', None),
                            'deadline': process_data.get('deadline', None)
                        },
                        'is_perfect_match': False
                    })
                    
                    # Check if user values match recommendations
                    rec = recommendations[-1]['recommendations']
                    user_vals = recommendations[-1]['user_values']
                    
                    if (user_vals['arrival_time'] == rec['optimal_arrival_time'] and 
                        user_vals['burst_time'] == rec['optimal_burst_time']):
                        if algorithm in ['priority', 'ai']:
                            if user_vals['priority'] == rec['optimal_priority']:
                                recommendations[-1]['is_perfect_match'] = True
                        elif algorithm == 'deadline':
                            if user_vals['deadline'] == rec['optimal_deadline']:
                                recommendations[-1]['is_perfect_match'] = True
                        else:
                            recommendations[-1]['is_perfect_match'] = True
                    
                except ValueError:
                    context['error'] = f"Invalid input values for process {process_names[i]}"
                    return render(request, 'taskmanager/schedule.html', context)
            
            # Generate schedule based on selected algorithm
            if algorithm == "round_robin":
                result = round_robin(processes, time_quantum)
                # Add time quantum recommendation for round robin
                try:
                    from taskmanager.recommender import ProcessRecommender
                    tq_recommender = ProcessRecommender().time_quantum_recommender
                    tq_recommendation = tq_recommender.get_optimal_time_quantum(
                        [{'name': p['name'], 'arrival_time': p['arrival_time'], 'execution_time': p['burst_time']} for p in processes], time_quantum
                    )
                    context['time_quantum_recommendation'] = tq_recommendation
                except Exception as tqe:
                    context['time_quantum_recommendation'] = {'error': str(tqe)}
            elif algorithm == "priority":
                result = priority_scheduling(processes)
            elif algorithm == "ai":
                result = user_priority_scheduling(processes)
            elif algorithm == "mlfq":
                time_quantums = [time_quantum, time_quantum * 2, time_quantum * 4]
                result = multilevel_feedback_queue(processes, time_quantums)
            elif algorithm == "deadline":
                result = deadline_scheduling(processes)
            elif algorithm == "sjf":
                result = shortest_job_first(processes)
            else:
                context['error'] = "Invalid scheduling algorithm selected"
                return render(request, 'taskmanager/schedule.html', context)
            
            # Calculate average metrics
            if result['metrics']:
                total_wt = sum(metric['wt'] for metric in result['metrics'])
                total_tat = sum(metric['tat'] for metric in result['metrics'])
                avg_wt = total_wt / len(result['metrics'])
                avg_tat = total_tat / len(result['metrics'])
                
                # Calculate CPU utilization
                total_time = max(item['end'] for item in result['gantt'])
                total_execution_time = sum(proc['execution_time'] for proc in processes)
                cpu_utilization = (total_execution_time / total_time) * 100 if total_time > 0 else 0
                
                context.update({
                    'result': result,
                    'avg_tat': round(avg_tat, 2),
                    'avg_wt': round(avg_wt, 2),
                    'cpu_utilization': round(cpu_utilization, 2),
                    'algorithm': algorithm,
                    'time_quantum': time_quantum,
                    'recommendations': recommendations
                })
        
        except Exception as e:
            context['error'] = f"An error occurred: {str(e)}"
            return render(request, 'taskmanager/schedule.html', context)
    
    return render(request, 'taskmanager/schedule.html', context)

def learning_module(request):
    """
    View function for the learning module that teaches scheduling algorithms.
    """
    return render(request, 'taskmanager/learn.html')

@login_required
def disk_schedule(request):
    context = {}
    if request.method == "POST":
        algorithm = request.POST.get("disk_algorithm")
        requests_str = request.POST.get("requests", "")
        head = request.POST.get("head")
        try:
            requests = [int(x.strip()) for x in requests_str.split(",") if x.strip()]
            head = int(head)
        except Exception:
            context['disk_result'] = {'visualization': '<div class="text-red-400">Invalid input.</div>', 'total_movement': 0}
            return render(request, 'taskmanager/schedule.html', context)

        # Create figure for static visualization
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Track Number')
        ax.set_title(f'Disk Scheduling - {algorithm.upper()}')

        # Initialize variables for different algorithms
        total_movement = 0
        current_head = head
        sequence = [head]  # Track the sequence of head movements

        if algorithm == 'fcfs':
            sequence.extend(requests)
            for i in range(len(sequence) - 1):
                total_movement += abs(sequence[i+1] - sequence[i])
        elif algorithm == 'sstf':
            remaining = requests.copy()
            while remaining:
                closest = min(remaining, key=lambda x: abs(x - current_head))
                sequence.append(closest)
                total_movement += abs(closest - current_head)
                current_head = closest
                remaining.remove(closest)
        elif algorithm == 'scan':
            direction = 1
            remaining = sorted(requests)
            while remaining:
                if direction == 1:
                    next_track = min((x for x in remaining if x >= current_head), default=None)
                    if next_track is None:
                        direction = -1
                        continue
                else:
                    next_track = max((x for x in remaining if x <= current_head), default=None)
                    if next_track is None:
                        direction = 1
                        continue
                sequence.append(next_track)
                total_movement += abs(next_track - current_head)
                current_head = next_track
                remaining.remove(next_track)
        elif algorithm == 'cscan':
            remaining = sorted(requests)
            while remaining:
                next_track = min((x for x in remaining if x >= current_head), default=None)
                if next_track is None:
                    total_movement += abs(current_head - min(requests))
                    current_head = min(requests)
                    next_track = min(remaining)
                sequence.append(next_track)
                total_movement += abs(next_track - current_head)
                current_head = next_track
                remaining.remove(next_track)

        # Plot the head movement
        time_steps = range(len(sequence))
        ax.plot(time_steps, sequence, 'b-', linewidth=2, label='Head Movement')
        ax.scatter(time_steps, sequence, color='red', s=60, label='Track Access')

        # Autoscale y-axis to data
        ymin = min(sequence) - 5
        ymax = max(sequence) + 5
        ax.set_ylim(ymin, ymax)

        # Annotate only the actual access points, spaced out for clarity
        for i, track in enumerate(sequence):
            if i == 0 or i == len(sequence)-1 or abs(sequence[i] - sequence[i-1]) > 0:
                ax.annotate(str(track), (i, track), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=9)

        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()

        # Save the plot to a temporary file
        tmpfile = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmpfile.close()
        plt.savefig(tmpfile.name, bbox_inches='tight', dpi=100)
        plt.close(fig)

        # Convert the plot to base64 for embedding in HTML
        with open(tmpfile.name, 'rb') as f:
            plot_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmpfile.name)

        context['disk_result'] = {
            'visualization': f'<img src="data:image/png;base64,{plot_data}" class="w-full max-w-3xl mx-auto" alt="Disk Scheduling Visualization">',
            'total_movement': total_movement,
            'sequence': sequence
        }

    return render(request, 'taskmanager/schedule.html', context)

@login_required
def paging(request):
    print('Paging view called')
    context = {}
    if request.method == "POST":
        print('POST data:', request.POST)
        algorithm = request.POST.get("paging_algorithm")
        ref_str = request.POST.get("reference_string", "")
        frames = request.POST.get("frames")
        print('AJAX:', request.headers.get('x-requested-with'))
        try:
            reference = [int(x.strip()) for x in ref_str.split(",") if x.strip()]
            frames = int(frames)
            if frames < 1 or frames > 10:
                raise ValueError("Number of frames must be between 1 and 10")
        except Exception as e:
            print('Error:', e)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)
            context['error'] = str(e)
            return render(request, 'taskmanager/schedule.html', context)
        context['paging_data'] = {
            'reference_string': reference,
            'frames': frames,
            'algorithm': algorithm
        }
        gif_data = None
        total_faults = 0
        total_hits = 0
        if reference:
            print('Generating GIF for reference:', reference)
            # Simulate the algorithm to count faults and hits
            frames_list = []
            ref_bits = []  # For Second Chance
            pointer = 0
            for i, page in enumerate(reference):
                if algorithm == 'second_chance':
                    if page in frames_list:
                        total_hits += 1
                        idx = frames_list.index(page)
                        ref_bits[idx] = 1
                    else:
                        total_faults += 1
                        if len(frames_list) < frames:
                            frames_list.append(page)
                            ref_bits.append(1)
                        else:
                            # Defensive: ensure pointer is always valid
                            if pointer >= len(frames_list):
                                pointer = 0
                            attempts = 0
                            while attempts < len(frames_list):
                                if ref_bits[pointer] == 0:
                                    frames_list[pointer] = page
                                    ref_bits[pointer] = 1
                                    pointer = (pointer + 1) % frames
                                    break
                                else:
                                    ref_bits[pointer] = 0
                                    pointer = (pointer + 1) % frames
                                attempts += 1
                            else:
                                # Fallback: replace at pointer if all bits are 1 (shouldn't happen)
                                frames_list[pointer] = page
                                ref_bits[pointer] = 1
                                pointer = (pointer + 1) % frames
                else:
                    if page not in frames_list:
                        total_faults += 1
                        if len(frames_list) < frames:
                            frames_list.append(page)
                        else:
                            if algorithm == 'fifo':
                                frames_list.pop(0)
                            elif algorithm == 'lru':
                                lru_page = min(frames_list, key=lambda p: reference[:i].count(p))
                                idx = frames_list.index(lru_page)
                                frames_list.pop(idx)
                            elif algorithm == 'optimal':
                                farthest = -1
                                farthest_page = None
                                for p in frames_list:
                                    try:
                                        next_use = reference[i+1:].index(p)
                                        if next_use > farthest:
                                            farthest = next_use
                                            farthest_page = p
                                    except ValueError:
                                        farthest_page = p
                                        break
                                if farthest_page:
                                    idx = frames_list.index(farthest_page)
                                    frames_list.pop(idx)
                            frames_list.append(page)
                    else:
                        total_hits += 1
            try:
                if not reference or not frames_list:
                    raise ValueError('No data to plot.')
                fig, ax = plt.subplots(figsize=(8, 6))
                n = len(reference)
                ax.set_ylim(-1, n)
                ax.set_xlim(min(reference) - 1, max(reference) + 1)
                ax.set_yticks(range(n))
                ax.set_yticklabels([str(i) for i in range(n)])
                ax.set_xlabel("Page Reference")
                ax.set_ylabel("Step")
                ax.set_title("Page Replacement Reference String Traversal")
                ax.invert_yaxis()
                line, = ax.plot([], [], 'b-', lw=2)
                point, = ax.plot([], [], 'ro', markersize=8)
                def init():
                    line.set_data([], [])
                    point.set_data([], [])
                    return line, point
                def animate(i):
                    x = reference[:i + 1]
                    y = list(range(i + 1))
                    line.set_data(x, y)
                    point.set_data(x[-1:], y[-1:])
                    return line, point
                ani = animation.FuncAnimation(
                    fig, animate, frames=n, init_func=init, blit=True, interval=700, repeat=False
                )
                tmpfile = tempfile.NamedTemporaryFile(suffix='.gif', delete=False)
                tmpfile.close()
                pillow_writer = PillowWriter(fps=2, metadata={'loop': 0})  # loop:0 means no repeat
                ani.save(tmpfile.name, writer=pillow_writer)
                plt.close(fig)
                with open(tmpfile.name, 'rb') as f:
                    gif_data = base64.b64encode(f.read()).decode('utf-8')
                os.unlink(tmpfile.name)
                print('GIF generated:', bool(gif_data))
            except Exception as e:
                print('Plotting error:', e)
                gif_data = None
                context['error'] = f'Error generating graph: {e}'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            print('Returning JSON with GIF')
            return JsonResponse({'gif_data': gif_data, 'total_faults': total_faults, 'total_hits': total_hits, 'error': context.get('error', None)})
        if gif_data:
            context['paging_gif_data'] = gif_data
            context['total_faults'] = total_faults
            context['total_hits'] = total_hits
    return render(request, 'taskmanager/schedule.html', context)

@login_required
def page_replacement_visualizer(request):
    if request.method == "POST":
        algorithm = request.POST.get("paging_algorithm")
        ref_str = request.POST.get("reference_string", "")
        frames = request.POST.get("frames")
        try:
            reference = [int(x.strip()) for x in ref_str.split(",") if x.strip()]
            frames = int(frames)
            if frames < 1 or frames > 10:
                raise ValueError("Number of frames must be between 1 and 10")
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Initialize page frames
        page_frames = []
        page_faults = 0
        history = []
        
        # Process each page reference
        for i, page in enumerate(reference):
            step = {
                'page': page,
                'frames': page_frames.copy(),
                'fault': False,
                'replaced': None
            }
            
            if page not in page_frames:
                page_faults += 1
                step['fault'] = True
                
                if len(page_frames) < frames:
                    page_frames.append(page)
                else:
                    if algorithm == 'fifo':
                        # FIFO: Replace the oldest page
                        replaced = page_frames.pop(0)
                        page_frames.append(page)
                        step['replaced'] = replaced
                    elif algorithm == 'lru':
                        # LRU: Replace the least recently used page
                        # Find the least recently used page
                        lru_page = min(page_frames, key=lambda p: reference[:i].count(p))
                        idx = page_frames.index(lru_page)
                        replaced = page_frames.pop(idx)
                        page_frames.append(page)
                        step['replaced'] = replaced
                    elif algorithm == 'optimal':
                        # Optimal: Replace the page that won't be used for the longest time
                        # Find the page that won't be used for the longest time
                        farthest = -1
                        farthest_page = None
                        for p in page_frames:
                            try:
                                next_use = reference[i+1:].index(p)
                                if next_use > farthest:
                                    farthest = next_use
                                    farthest_page = p
                            except ValueError:
                                # Page won't be used again
                                farthest_page = p
                                break
                        
                        if farthest_page:
                            idx = page_frames.index(farthest_page)
                            replaced = page_frames.pop(idx)
                            page_frames.append(page)
                            step['replaced'] = replaced
            
            history.append(step)
        
        return JsonResponse({
            'history': history,
            'total_faults': page_faults
        })
    
    return render(request, 'taskmanager/page_replacement.html')

def page_replacement_line_graph(request):
    if request.method == "POST":
        ref_str = request.POST.get("reference_string", "")
        reference = [int(x.strip()) for x in ref_str.split(",") if x.strip()]
        n = len(reference)
        if n == 0:
            return render(request, 'taskmanager/page_replacement_line_graph.html', {'error': 'Please enter a valid reference string.'})

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_ylim(-1, n)
        ax.set_xlim(min(reference) - 1, max(reference) + 1)
        ax.set_yticks(range(n))
        ax.set_yticklabels([str(i) for i in range(n)])
        ax.set_xlabel("Page Reference")
        ax.set_ylabel("Step")
        ax.set_title("Page Replacement Reference String Traversal")
        ax.invert_yaxis()  # Step 0 at the top

        line, = ax.plot([], [], 'b-', lw=2)
        point, = ax.plot([], [], 'ro', markersize=8)

        def init():
            line.set_data([], [])
            point.set_data([], [])
            return line, point

        def animate(i):
            x = reference[:i + 1]  # Page references (horizontal)
            y = list(range(i + 1))  # Steps (vertical)
            line.set_data(x, y)
            point.set_data(x[-1:], y[-1:])
            return line, point

        ani = animation.FuncAnimation(
            fig, animate, frames=n, init_func=init, blit=True, interval=700, repeat=False
        )

        tmpfile = tempfile.NamedTemporaryFile(suffix='.gif', delete=False)
        tmpfile.close()  # Close the file so Pillow can write to it
        ani.save(tmpfile.name, writer='pillow')
        plt.close(fig)
        with open(tmpfile.name, 'rb') as f:
            gif_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmpfile.name)  # Delete the temp file manually
        return render(request, 'taskmanager/page_replacement_line_graph.html', {
            'gif_data': gif_data,
            'reference': reference
        })

    return render(request, 'taskmanager/page_replacement_line_graph.html')

def recommend_algorithm(processes):
    """
    Recommends the best scheduling algorithm based on process characteristics.
    Returns a tuple of (recommended_algorithm, explanation)
    """
    if not processes:
        return None, "No processes to analyze"
    
    # Calculate average burst time and variance
    burst_times = [p['execution_time'] for p in processes]
    avg_burst = sum(burst_times) / len(burst_times)
    burst_variance = sum((x - avg_burst) ** 2 for x in burst_times) / len(burst_times)
    
    # Check if arrival times are all 0 (FCFS is good for this)
    arrival_times = [p['arrival_time'] for p in processes]
    all_arrival_zero = all(t == 0 for t in arrival_times)
    
    # Check if burst times are very similar (SJF is good for this)
    burst_similar = burst_variance < (avg_burst * 0.2)  # If variance is less than 20% of average
    
    # Check if there are many short processes (Round Robin is good for this)
    short_processes = sum(1 for bt in burst_times if bt <= avg_burst * 0.5)
    many_short_processes = short_processes > len(processes) * 0.3  # If more than 30% are short
    
    if all_arrival_zero:
        return "fcfs", "All processes arrive at time 0, making FCFS a good choice for fairness"
    elif burst_similar:
        return "sjf", "Process burst times are similar, making SJF efficient"
    elif many_short_processes:
        return "round_robin", "Many short processes present, making Round Robin suitable for fair execution"
    else:
        return "round_robin", "Round Robin is recommended as a balanced choice for mixed process characteristics"

@login_required
def get_algorithm_recommendation(request):
    if request.method == "POST":
        try:
            process_names = request.POST.getlist("process_name[]")
            arrival_times = request.POST.getlist("arrival_time[]")
            burst_times = request.POST.getlist("burst_time[]")
            
            if not all([process_names, arrival_times, burst_times]):
                return JsonResponse({
                    'error': "Please fill in all process details"
                })
            
            processes = []
            for i in range(len(process_names)):
                try:
                    arrival_time = int(arrival_times[i])
                    burst_time = int(burst_times[i])
                    
                    if arrival_time < 0 or burst_time <= 0:
                        return JsonResponse({
                            'error': f"Invalid time values for process {process_names[i]}"
                        })
                    
                    processes.append({
                        'name': process_names[i],
                        'arrival_time': arrival_time,
                        'execution_time': burst_time
                    })
                except ValueError:
                    return JsonResponse({
                        'error': f"Invalid numeric values for process {process_names[i]}"
                    })
            
            recommended_algorithm, explanation = recommend_algorithm(processes)
            
            return JsonResponse({
                'algorithm': recommended_algorithm,
                'explanation': explanation
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            })
    
    return JsonResponse({
        'error': "Invalid request method"
    })

