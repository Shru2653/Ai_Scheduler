from typing import List, Dict, Any
import json

class SchedulingStep:
    def __init__(self, time: int, current_process: str, ready_queue: List[str], 
                 completed: List[str], metrics: Dict[str, Any] = None):
        self.time = time
        self.current_process = current_process
        self.ready_queue = ready_queue
        self.completed = completed
        self.metrics = metrics or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time': self.time,
            'current_process': self.current_process,
            'ready_queue': self.ready_queue,
            'completed': self.completed,
            'metrics': self.metrics
        }

def create_round_robin_steps(processes: List[Dict], time_quantum: int) -> List[Dict]:
    steps = []
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    ready_queue = []
    last_checked = 0
    completed = []

    # Sort processes by arrival time
    processes = sorted(processes, key=lambda x: x['arrival_time'])
    arrival_times = [proc['arrival_time'] for proc in processes]
    remaining_burst = [proc['burst_time'] for proc in processes]

    while any(remaining_burst[i] > 0 for i in range(n)) or ready_queue:
        # Add newly arrived processes
        for i in range(last_checked, n):
            if arrival_times[i] <= current_time:
                ready_queue.append(i)
                last_checked = i + 1

        if not ready_queue:
            current_time += 1
            continue

        current_process = ready_queue.pop(0)
        process_name = processes[current_process]['process_name']

        execute_time = min(time_quantum, remaining_burst[current_process])
        current_time += execute_time
        remaining_burst[current_process] -= execute_time

        # Create step for animation
        step = SchedulingStep(
            time=current_time,
            current_process=process_name,
            ready_queue=[processes[i]['process_name'] for i in ready_queue],
            completed=[processes[i]['process_name'] for i in completed]
        )
        steps.append(step.to_dict())

        # Add any new processes that arrived during execution
        for i in range(last_checked, n):
            if arrival_times[i] <= current_time:
                ready_queue.append(i)
                last_checked = i + 1

        if remaining_burst[current_process] > 0:
            ready_queue.append(current_process)
        else:
            completion_times[current_process] = current_time
            completed.append(current_process)

    # Add final metrics step
    metrics = {}
    for i in range(n):
        turnaround_time = completion_times[i] - processes[i]['arrival_time']
        waiting_time = turnaround_time - processes[i]['burst_time']
        metrics[processes[i]['process_name']] = {
            'completion_time': completion_times[i],
            'turnaround_time': turnaround_time,
            'waiting_time': waiting_time
        }

    final_step = SchedulingStep(
        time=current_time,
        current_process="",
        ready_queue=[],
        completed=[p['process_name'] for p in processes],
        metrics=metrics
    )
    steps.append(final_step.to_dict())

    return steps

def create_priority_scheduling_steps(processes: List[Dict]) -> List[Dict]:
    steps = []
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    completed = []

    # Sort by priority and arrival time
    processes = sorted(processes, key=lambda x: (-x['priority'], x['arrival_time']))
    arrival_times = [proc['arrival_time'] for proc in processes]
    remaining_burst = [proc['burst_time'] for proc in processes]

    while any(remaining_burst[i] > 0 for i in range(n)):
        available = [(i, processes[i]['priority']) 
                    for i in range(n) 
                    if arrival_times[i] <= current_time and remaining_burst[i] > 0]
        
        if not available:
            current_time += 1
            continue

        # Select process with highest priority
        available.sort(key=lambda x: (x[1], arrival_times[x[0]]))
        selected_proc = available[0][0]
        process_name = processes[selected_proc]['process_name']

        # Execute process
        current_time += remaining_burst[selected_proc]
        remaining_burst[selected_proc] = 0
        completion_times[selected_proc] = current_time
        completed.append(selected_proc)

        # Create step for animation
        step = SchedulingStep(
            time=current_time,
            current_process=process_name,
            ready_queue=[processes[i]['process_name'] for i, _ in available[1:]],
            completed=[processes[i]['process_name'] for i in completed]
        )
        steps.append(step.to_dict())

    # Add final metrics step
    metrics = {}
    for i in range(n):
        turnaround_time = completion_times[i] - processes[i]['arrival_time']
        waiting_time = turnaround_time - processes[i]['burst_time']
        metrics[processes[i]['process_name']] = {
            'completion_time': completion_times[i],
            'turnaround_time': turnaround_time,
            'waiting_time': waiting_time
        }

    final_step = SchedulingStep(
        time=current_time,
        current_process="",
        ready_queue=[],
        completed=[p['process_name'] for p in processes],
        metrics=metrics
    )
    steps.append(final_step.to_dict())

    return steps

def create_ai_based_steps(processes: List[Dict]) -> List[Dict]:
    # AI-based scheduling uses the same steps as priority scheduling
    # but with different priority calculations
    steps = []
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    completed = []

    # Calculate AI-based priorities
    for i in range(n):
        waiting_time = max(0, current_time - arrival_times[i])
        priority_score = 1 / (processes[i]['priority'] + 1)  # lower priority number is better
        burst_score = 1 / remaining_burst[i]  # smaller burst better
        waiting_score = waiting_time / 10  # longer waiting is better

        processes[i]['ai_priority'] = (0.4 * priority_score) + (0.3 * burst_score) + (0.3 * waiting_score)

    # Sort by AI priority and arrival time
    processes = sorted(processes, key=lambda x: (-x['ai_priority'], x['arrival_time']))
    arrival_times = [proc['arrival_time'] for proc in processes]
    remaining_burst = [proc['burst_time'] for proc in processes]

    while any(remaining_burst[i] > 0 for i in range(n)):
        available = [(i, processes[i]['ai_priority']) 
                    for i in range(n) 
                    if arrival_times[i] <= current_time and remaining_burst[i] > 0]
        
        if not available:
            current_time += 1
            continue

        # Select process with highest AI priority
        available.sort(key=lambda x: (-x[1], arrival_times[x[0]]))
        selected_proc = available[0][0]
        process_name = processes[selected_proc]['process_name']

        # Execute process
        current_time += remaining_burst[selected_proc]
        remaining_burst[selected_proc] = 0
        completion_times[selected_proc] = current_time
        completed.append(selected_proc)

        # Create step for animation
        step = SchedulingStep(
            time=current_time,
            current_process=process_name,
            ready_queue=[processes[i]['process_name'] for i, _ in available[1:]],
            completed=[processes[i]['process_name'] for i in completed]
        )
        steps.append(step.to_dict())

    # Add final metrics step
    metrics = {}
    for i in range(n):
        turnaround_time = completion_times[i] - processes[i]['arrival_time']
        waiting_time = turnaround_time - processes[i]['burst_time']
        metrics[processes[i]['process_name']] = {
            'completion_time': completion_times[i],
            'turnaround_time': turnaround_time,
            'waiting_time': waiting_time
        }

    final_step = SchedulingStep(
        time=current_time,
        current_process="",
        ready_queue=[],
        completed=[p['process_name'] for p in processes],
        metrics=metrics
    )
    steps.append(final_step.to_dict())

    return steps 