import heapq
from collections import deque

def round_robin(tasks, time_slice=3):
    if not tasks or time_slice <= 0:
        return {"gantt": [], "metrics": []}

    # Initialize processes
    processes = []
    for task in tasks:
        processes.append({
            "name": task["name"],
            "arrival_time": task.get("arrival_time", 0),
            "execution_time": task["execution_time"],
            "remaining_time": task["execution_time"],
            "start_times": [],  # to track Gantt chart
            "completion_time": 0
        })
    
    # Sort by arrival time
    processes.sort(key=lambda x: x["arrival_time"])

    current_time = 0
    ready_queue = deque()
    gantt = []
    completed = []

    # Move initial processes
    while processes and processes[0]["arrival_time"] <= current_time:
        ready_queue.append(processes.pop(0))

    while processes or ready_queue:
        if not ready_queue:
            current_time = processes[0]["arrival_time"]
            ready_queue.append(processes.pop(0))

        current_process = ready_queue.popleft()

        start_time = current_time
        exec_time = min(time_slice, current_process["remaining_time"])
        current_time += exec_time
        end_time = current_time

        # Add to Gantt chart
        gantt.append({
            "process": current_process["name"],
            "start": start_time,
            "end": end_time
        })

        current_process["remaining_time"] -= exec_time

        # Add newly arrived processes
        while processes and processes[0]["arrival_time"] <= current_time:
            ready_queue.append(processes.pop(0))

        if current_process["remaining_time"] == 0:
            current_process["completion_time"] = current_time
            completed.append(current_process)
        else:
            ready_queue.append(current_process)

    # Now calculate metrics
    metrics = []
    for process in completed:
        turnaround_time = process["completion_time"] - process["arrival_time"]
        waiting_time = turnaround_time - process["execution_time"]

        metrics.append({
            "process": process["name"],
            "ct": process["completion_time"],
            "tat": turnaround_time,
            "wt": waiting_time
        })

    # Sort by process name
    metrics.sort(key=lambda x: x["process"])
    return {"gantt": gantt, "metrics": metrics}


def priority_scheduling(tasks):
    if not tasks:
        return {"gantt": [], "metrics": []}

    processes = []
    for task in tasks:
        processes.append({
            "name": task["name"],
            "arrival_time": task.get("arrival_time", 0),
            "execution_time": task["execution_time"],
            "priority": task.get("priority", 0),
        })

    current_time = 0
    completed = []
    gantt = []

    while processes:
        available = [p for p in processes if p["arrival_time"] <= current_time]
        if not available:
            current_time = min(p["arrival_time"] for p in processes)
            continue

        # Select highest priority; if tie, shortest execution_time
        available.sort(key=lambda x: (-x["priority"], x["execution_time"]))
        current_process = available[0]

        processes.remove(current_process)

        start_time = current_time
        end_time = current_time + current_process["execution_time"]

        gantt.append({
            "process": current_process["name"],
            "start": start_time,
            "end": end_time
        })

        current_time = end_time

        turnaround_time = current_time - current_process["arrival_time"]
        waiting_time = turnaround_time - current_process["execution_time"]

        completed.append({
            "process": current_process["name"],
            "ct": current_time,
            "tat": turnaround_time,
            "wt": waiting_time
        })

    completed.sort(key=lambda x: x["process"])
    return {"gantt": gantt, "metrics": completed}


def ai_based_prioritization(tasks):
    if not tasks:
        return {"gantt": [], "metrics": []}

    for task in tasks:
        base_priority = 0

        # System processes
        if any(sys_word in task["name"].lower() for sys_word in ["system", "win", "init", "kernel"]):
            base_priority += 30

        # Memory usage
        try:
            mem = float(str(task.get("memory", "0")).replace('%', '').replace(' K', ''))
            base_priority += mem * 0.5
        except:
            pass

        # CPU usage
        try:
            cpu = float(str(task.get("cpu", "0")).replace('%', ''))
            base_priority += cpu * 0.3
        except:
            pass

        # GUI processes
        if any(gui_word in task["name"].lower() for gui_word in ["explorer", "chrome", "firefox", "gnome"]):
            base_priority += 20

        # Background processes
        if any(bg_word in task["name"].lower() for bg_word in ["update", "helper", "service"]):
            base_priority = max(5, base_priority - 10)

        task["priority"] = int(base_priority)

    return priority_scheduling(tasks)
