import heapq
from collections import deque


def round_robin(tasks, time_slice=3):
    if not tasks or time_slice <= 0:
        return {"gantt": [], "metrics": []}

    schedule = []
    queue = deque(tasks.copy())
    time = 0
    gantt = []
    metrics = []
    completed = {}

    while queue:
        current_task = queue.popleft()

        exec_time = min(time_slice, current_task["execution_time"])
        start_time = time
        end_time = time + exec_time

        gantt.append({
            "process": current_task["name"],
            "start": start_time,
            "end": end_time
        })

        current_task["execution_time"] -= exec_time
        time += exec_time

        if current_task["execution_time"] > 0:
            queue.append(current_task)
        else:
            ct = end_time
            tat = ct - current_task.get("arrival_time", 0)
            wt = tat - current_task["execution_time"]
            metrics.append({
                "process": current_task["name"],
                "ct": ct,
                "tat": tat,
                "wt": wt
            })

    return {"gantt": gantt, "metrics": metrics}


def priority_scheduling(tasks):
    if not tasks:
        return {"gantt": [], "metrics": []}

    heap = []
    for idx, task in enumerate(tasks):
        priority = -task.get("priority", 0)
        heapq.heappush(heap, (priority, idx, task))

    time = 0
    gantt = []
    metrics = []

    while heap:
        _, _, task = heapq.heappop(heap)
        start_time = time
        end_time = time + task["execution_time"]

        gantt.append({
            "process": task["name"],
            "start": start_time,
            "end": end_time
        })

        ct = end_time
        tat = ct - task.get("arrival_time", 0)
        wt = tat - task["burst_time"]

        metrics.append({
            "process": task["name"],
            "ct": ct,
            "tat": tat,
            "wt": wt
        })

        time = end_time

    return {"gantt": gantt, "metrics": metrics}


def ai_based_prioritization(tasks):
    if not tasks:
        return {"gantt": [], "metrics": []}

    for task in tasks:
        base_priority = 0

        if any(sys_word in task["name"].lower() for sys_word in ["system", "win", "init", "kernel"]):
            base_priority += 30

        try:
            mem = float(str(task.get("memory", "0")).replace('%', '').replace(' K', ''))
            base_priority += mem * 0.5
        except:
            pass

        try:
            cpu = float(str(task.get("cpu", "0")).replace('%', ''))
            base_priority += cpu * 0.3
        except:
            pass

        if any(gui_word in task["name"].lower() for gui_word in ["explorer", "chrome", "firefox", "gnome"]):
            base_priority += 20

        if any(bg_word in task["name"].lower() for bg_word in ["update", "helper", "service"]):
            base_priority = max(5, base_priority - 10)

        task["priority"] = int(base_priority)

    return priority_scheduling(tasks)
