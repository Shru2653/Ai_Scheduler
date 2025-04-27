# scheduler/scheduler.py

def round_robin(processes, time_quantum):
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    result = []
    ready_queue = []
    last_checked = 0

    # Sort processes by arrival time initially
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

        execute_time = min(time_quantum, remaining_burst[current_process])
        current_time += execute_time
        remaining_burst[current_process] -= execute_time

        # Add any new processes that arrived during execution
        for i in range(last_checked, n):
            if arrival_times[i] <= current_time:
                ready_queue.append(i)
                last_checked = i + 1

        if remaining_burst[current_process] > 0:
            ready_queue.append(current_process)
        else:
            completion_times[current_process] = current_time
            result.append((processes[current_process]['process_name'], current_time))

    # Calculate metrics
    for i in range(n):
        processes[i]['completion_time'] = completion_times[i]
        processes[i]['turnaround_time'] = completion_times[i] - processes[i]['arrival_time']
        processes[i]['waiting_time'] = processes[i]['turnaround_time'] - processes[i]['burst_time']

    return result




def priority_scheduling(processes):
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    completed = 0
    result = []

    while completed < n:
        available = [(i, processes[i]['priority']) for i in range(n) if arrival_times[i] <= current_time and remaining_burst[i] > 0]
        if not available:
            current_time += 1
            continue

        # Select process with highest priority (smallest number)
        available.sort(key=lambda x: (x[1], arrival_times[x[0]]))
        selected_proc = available[0][0]

        current_time += remaining_burst[selected_proc]
        remaining_burst[selected_proc] = 0
        completion_times[selected_proc] = current_time
        completed += 1
        result.append((processes[selected_proc]['process_name'], current_time))

    # Calculate metrics
    for i in range(n):
        processes[i]['completion_time'] = completion_times[i]
        processes[i]['turnaround_time'] = processes[i]['completion_time'] - arrival_times[i]
        processes[i]['waiting_time'] = processes[i]['turnaround_time'] - processes[i]['burst_time']

    return result


def ai_based_prioritization(processes):
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    completed = 0
    result = []

    while completed < n:
        available = []
        for i in range(n):
            if arrival_times[i] <= current_time and remaining_burst[i] > 0:
                waiting_time = current_time - arrival_times[i]
                priority_score = 1 / (processes[i]['priority'] + 1)  # lower priority number is better
                burst_score = 1 / remaining_burst[i]  # smaller burst better
                waiting_score = waiting_time / 10  # longer waiting is better

                score = (0.4 * priority_score) + (0.3 * burst_score) + (0.3 * waiting_score)
                available.append((i, score))

        if not available:
            current_time += 1
            continue

        # Select process with highest AI score
        available.sort(key=lambda x: (-x[1], arrival_times[x[0]]))
        selected_proc = available[0][0]

        current_time += remaining_burst[selected_proc]
        remaining_burst[selected_proc] = 0
        completion_times[selected_proc] = current_time
        completed += 1
        result.append((processes[selected_proc]['process_name'], current_time))

    # Calculate metrics
    for i in range(n):
        processes[i]['completion_time'] = completion_times[i]
        processes[i]['turnaround_time'] = processes[i]['completion_time'] - arrival_times[i]
        processes[i]['waiting_time'] = processes[i]['turnaround_time'] - processes[i]['burst_time']

    return result
