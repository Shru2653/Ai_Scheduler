import heapq
from collections import deque

def round_robin(tasks, time_slice=3):
    """
    Enhanced Round Robin Scheduling with better process handling
    Args:
        tasks: List of process dictionaries with 'name', 'pid', 'execution_time'
        time_slice: Time quantum for each process (default: 3)
    Returns:
        List of scheduled processes with execution details
    """
    if not tasks or time_slice <= 0:
        return []
    
    schedule = []
    queue = deque(tasks.copy())
    
    while queue:
        current_task = queue.popleft()
        
        # Determine execution time for this turn
        exec_time = min(time_slice, current_task["execution_time"])
        schedule.append({
            "name": current_task["name"],
            "pid": current_task.get("pid", "N/A"),
            "execution_time": exec_time,
            "remaining_time": current_task["execution_time"] - exec_time,
            "memory": current_task.get("memory", "N/A")
        })
        
        # Update remaining time and requeue if needed
        current_task["execution_time"] -= exec_time
        if current_task["execution_time"] > 0:
            queue.append(current_task)
            
    return schedule


def priority_scheduling(tasks):
    """
    Enhanced Priority Scheduling with better tie-breaking
    Args:
        tasks: List of process dictionaries with 'name', 'priority', 'execution_time'
    Returns:
        List of scheduled processes in priority order
    """
    if not tasks:
        return []
    
    # Create max-heap based on priority (using negative values for max heap)
    heap = []
    for idx, task in enumerate(tasks):
        # Default priority of 0 if not specified
        priority = -task.get("priority", 0)  # Negative for max heap
        heapq.heappush(heap, (priority, idx, task))
    
    schedule = []
    while heap:
        _, _, task = heapq.heappop(heap)
        schedule.append({
            "name": task["name"],
            "pid": task.get("pid", "N/A"),
            "execution_time": task["execution_time"],
            "priority": task.get("priority", 0),
            "memory": task.get("memory", "N/A")
        })
    
    return schedule


def ai_based_prioritization(tasks):
    """
    Enhanced AI-Based Prioritization with multiple factors
    Args:
        tasks: List of process dictionaries
    Returns:
        List of scheduled processes with AI-calculated priorities
    """
    if not tasks:
        return []
    
    for task in tasks:
        # Calculate priority based on multiple factors
        base_priority = 0
        
        # 1. System processes get higher priority
        if any(sys_word in task["name"].lower() 
               for sys_word in ["system", "win", "init", "kernel"]):
            base_priority += 30
            
        # 2. Memory usage (higher usage = higher priority)
        try:
            mem = float(str(task.get("memory", "0")).replace('%', '').replace(' K', ''))
            base_priority += mem * 0.5
        except:
            pass
            
        # 3. CPU usage (if available)
        try:
            cpu = float(str(task.get("cpu", "0")).replace('%', ''))
            base_priority += cpu * 0.3
        except:
            pass
            
        # 4. Interactive/GUI processes get moderate priority
        if any(gui_word in task["name"].lower()
              for gui_word in ["explorer", "chrome", "firefox", "gnome"]):
            base_priority += 20
            
        # 5. Background processes get lower priority
        if any(bg_word in task["name"].lower()
              for bg_word in ["update", "helper", "service"]):
            base_priority = max(5, base_priority - 10)
            
        task["priority"] = int(base_priority)
    
    # Now use our priority scheduling
    return priority_scheduling(tasks)