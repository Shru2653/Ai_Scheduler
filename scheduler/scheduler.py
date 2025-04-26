# scheduler/scheduler.py

def round_robin(processes, time_quantum):
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    result = []
    ready_queue = []

    while any(remaining_burst[i] > 0 for i in range(n)) or ready_queue:
        # Add newly arrived processes to ready queue
        for i in range(n):
            if arrival_times[i] <= current_time and remaining_burst[i] > 0 and i not in ready_queue:
                ready_queue.append(i)

        if not ready_queue:
            current_time += 1
            continue

        current_process = ready_queue.pop(0)
        
        if remaining_burst[current_process] > time_quantum:
            current_time += time_quantum
            remaining_burst[current_process] -= time_quantum
            result.append((processes[current_process]['process_name'], current_time))
            
            # Check for new arrivals during this time quantum
            for i in range(n):
                if arrival_times[i] <= current_time and remaining_burst[i] > 0 and i not in ready_queue and i != current_process:
                    ready_queue.append(i)
            
            if remaining_burst[current_process] > 0:
                ready_queue.append(current_process)
        else:
            current_time += remaining_burst[current_process]
            remaining_burst[current_process] = 0
            completion_times[current_process] = current_time
            result.append((processes[current_process]['process_name'], current_time))

    # Calculate additional metrics
    for i in range(n):
        processes[i]['completion_time'] = completion_times[i]
        processes[i]['turnaround_time'] = completion_times[i] - arrival_times[i]
        processes[i]['waiting_time'] = processes[i]['turnaround_time'] - processes[i]['burst_time']

    return result

def priority_scheduling(processes):
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    result = []
    completed = 0

    while completed < n:
        highest_priority = float('inf')
        selected_proc = -1

        # Find highest priority process that has arrived
        for i in range(n):
            if arrival_times[i] <= current_time and remaining_burst[i] > 0:
                if processes[i]['priority'] < highest_priority:
                    highest_priority = processes[i]['priority']
                    selected_proc = i

        if selected_proc == -1:
            current_time += 1
            continue

        # Execute the selected process
        current_time += remaining_burst[selected_proc]
        completion_times[selected_proc] = current_time
        remaining_burst[selected_proc] = 0
        completed += 1
        result.append((processes[selected_proc]['process_name'], current_time))

    # Calculate additional metrics
    for i in range(n):
        processes[i]['completion_time'] = completion_times[i]
        processes[i]['turnaround_time'] = completion_times[i] - arrival_times[i]
        processes[i]['waiting_time'] = processes[i]['turnaround_time'] - processes[i]['burst_time']

    return result

def ai_based_prioritization(processes):
    n = len(processes)
    remaining_burst = [proc['burst_time'] for proc in processes]
    arrival_times = [proc['arrival_time'] for proc in processes]
    completion_times = [-1] * n
    current_time = 0
    result = []
    completed = 0

    while completed < n:
        best_score = float('-inf')
        selected_proc = -1

        # AI-based scoring for process selection
        for i in range(n):
            if arrival_times[i] <= current_time and remaining_burst[i] > 0:
                # Calculate a score based on multiple factors
                waiting_time = current_time - arrival_times[i]
                priority_score = 1 / (processes[i]['priority'] + 1)  # Lower priority number is better
                burst_score = 1 / remaining_burst[i]  # Shorter burst time is better
                waiting_score = waiting_time / 10  # Longer waiting time increases priority
                
                # Combined score with weights
                score = (0.4 * priority_score + 
                        0.3 * burst_score + 
                        0.3 * waiting_score)

                if score > best_score:
                    best_score = score
                    selected_proc = i

        if selected_proc == -1:
            current_time += 1
            continue

        # Execute the selected process
        current_time += remaining_burst[selected_proc]
        completion_times[selected_proc] = current_time
        remaining_burst[selected_proc] = 0
        completed += 1
        result.append((processes[selected_proc]['process_name'], current_time))

    # Calculate additional metrics
    for i in range(n):
        processes[i]['completion_time'] = completion_times[i]
        processes[i]['turnaround_time'] = completion_times[i] - arrival_times[i]
        processes[i]['waiting_time'] = processes[i]['turnaround_time'] - processes[i]['burst_time']

    return result
