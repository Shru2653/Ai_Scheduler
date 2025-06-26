import heapq
from collections import deque
import psutil

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

    # Sort all processes by priority first (highest first), then by arrival time
    processes.sort(key=lambda x: (-x["priority"], x["arrival_time"]))

    while processes:
        # Take the highest priority process regardless of arrival time
        current_process = processes.pop(0)
        
        # If the process hasn't arrived yet, wait until it arrives
        if current_process["arrival_time"] > current_time:
            current_time = current_process["arrival_time"]

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

    # Create a copy of tasks to avoid modifying the original
    tasks_copy = tasks.copy()
    
    # Get system load information
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory_percent = psutil.virtual_memory().percent
    
    # Calculate system load factor (0.0 to 1.0)
    system_load = (cpu_percent + memory_percent) / 200.0
    
    # Print debug information
    print(f"System load: {system_load}, CPU: {cpu_percent}%, Memory: {memory_percent}%")
    
    # Use the user-provided priority directly without any adjustments
    for task in tasks_copy:
        # Just use the user-provided priority
        task["priority"] = task.get("priority", 1)
        print(f"Task {task['name']}: Priority={task['priority']} (1=lowest, 2=medium, 3=highest)")
    
    # Sort by priority first (highest first), then by arrival time
    # Note: Higher priority number (3) should be scheduled first
    # We need to use negative priority for sorting since higher numbers should be scheduled first
    tasks_copy.sort(key=lambda x: (-x["priority"], x["arrival_time"]))
    
    # Print the sorted order
    print("Sorted order (highest priority first):")
    for task in tasks_copy:
        print(f"{task['name']}: arrival={task['arrival_time']}, priority={task['priority']}")
    
    # Generate schedule using priority scheduling
    return priority_scheduling(tasks_copy)

def user_priority_scheduling(tasks):
    """
    This function respects the user's input priorities exactly without any AI adjustments.
    It simply sorts the tasks by the user-provided priority and then by arrival time.
    """
    if not tasks:
        return {"gantt": [], "metrics": []}

    # Create a copy of tasks to avoid modifying the original
    tasks_copy = tasks.copy()
    
    # Print debug information
    print("User Priority Scheduling - Using exact user-provided priorities")
    
    # Sort by user-provided priority first (highest first), then by arrival time
    tasks_copy.sort(key=lambda x: (-x.get("priority", 1), x.get("arrival_time", 0)))
    
    # Print the sorted order
    print("Sorted order:")
    for task in tasks_copy:
        print(f"{task['name']}: arrival={task.get('arrival_time', 0)}, priority={task.get('priority', 1)}")
    
    # Generate schedule using priority scheduling
    return priority_scheduling(tasks_copy)

def multilevel_feedback_queue(tasks, time_quantums=[2, 4, 8]):
    """
    Multilevel Feedback Queue (MLFQ) scheduling algorithm with proper preemption and aging
    Args:
        tasks: List of tasks with name, arrival_time, execution_time
        time_quantums: List of time quantums for each queue level (decreasing priority)
    Returns:
        Dictionary containing Gantt chart and metrics
    """
    if not tasks:
        return {"gantt": [], "metrics": []}

    # Initialize processes
    processes = []
    for task in tasks:
        processes.append({
            "name": task["name"],
            "arrival_time": task.get("arrival_time", 0),
            "execution_time": task["execution_time"],
            "remaining_time": task["execution_time"],
            "queue_level": 0,  # Start in highest priority queue
            "start_times": [],
            "completion_time": 0,
            "waiting_time": 0,
            "last_executed": 0,
            "waiting_since": 0,
            "quantum_used": 0
        })

    # Sort by arrival time
    processes.sort(key=lambda x: x["arrival_time"])

    # Initialize queues (highest priority to lowest)
    queues = [[] for _ in range(len(time_quantums))]
    current_time = 0
    gantt = []
    completed = []
    aging_threshold = 3

    def print_queues():
        """Debug function to print queue contents"""
        print(f"\nTime: {current_time}")
        for i, queue in enumerate(queues):
            print(f"Queue {i}: {[p['name'] for p in queue]}")
        print(f"Completed: {[p['name'] for p in completed]}\n")

    def check_aging(queues, current_time):
        """Promote processes waiting longer than aging_threshold in lower queues"""
        for q_idx in range(1, len(queues)):
            promoted = []
            for process in queues[q_idx]:
                if (current_time - process["waiting_since"]) >= aging_threshold:
                    print(f"Aging: {process['name']} promoted to queue {q_idx-1}")
                    queues[q_idx-1].append(process)
                    process["queue_level"] = q_idx - 1
                    process["waiting_since"] = current_time
                    process["quantum_used"] = 0
                    promoted.append(process)
            # Remove promoted processes from current queue
            queues[q_idx] = [p for p in queues[q_idx] if p not in promoted]

    def update_waiting_times(queues, current_time, running_process):
        """Update waiting time for all processes not running"""
        for q in queues:
            for p in q:
                if p != running_process:
                    p["waiting_time"] += 1

    def check_preemption(current_process, current_queue, queues, current_time):
        """Check if current process should be preempted by a higher priority process"""
        for q_idx in range(current_queue):
            if queues[q_idx]:
                print(f"Preempting {current_process['name']} for higher priority process")
                # Save state and re-queue current process
                queues[current_queue].insert(0, current_process)
                return True
        return False

    def demote_process(process, current_queue, queues):
        """Move process to appropriate queue based on quantum usage"""
        if current_queue < len(queues) - 1:
            process["queue_level"] = current_queue + 1
            process["waiting_since"] = current_time
            process["quantum_used"] = 0
            queues[current_queue + 1].append(process)
            print(f"Process {process['name']} demoted to queue {current_queue + 1}")
        else:
            # In lowest queue, use FCFS
            process["waiting_since"] = current_time
            process["quantum_used"] = 0
            queues[current_queue].append(process)

    while processes or any(queues):
        # Check for aging in all queues
        check_aging(queues, current_time)
        
        # Add newly arrived processes
        while processes and processes[0]["arrival_time"] <= current_time:
            new_process = processes.pop(0)
            new_process["waiting_since"] = current_time
            new_process["quantum_used"] = 0
            queues[0].append(new_process)
            print(f"Process {new_process['name']} arrived at time {current_time}")

        # Find highest priority non-empty queue
        current_queue = next((i for i, q in enumerate(queues) if q), None)
        
        if current_queue is None:
            if processes:
                current_time = processes[0]["arrival_time"]
                continue
            else:
                break

        current_process = queues[current_queue].pop(0)
        
        # Record start time if first execution
        if not current_process["start_times"]:
            current_process["start_times"].append(current_time)
            print(f"Process {current_process['name']} started execution at time {current_time}")

        # Determine execution time
        if current_queue == len(queues) - 1:
            # Lowest queue: FCFS (run to completion)
            exec_time = current_process["remaining_time"]
        else:
            exec_time = min(time_quantums[current_queue] - current_process["quantum_used"], 
                          current_process["remaining_time"])

        # Execute incrementally with preemption checks
        for _ in range(exec_time):
            # Update Gantt chart and process state
            gantt.append({
                "process": current_process["name"],
                "start": current_time,
                "end": current_time + 1,
                "queue_level": current_queue
            })
            
            current_time += 1
            current_process["remaining_time"] -= 1
            current_process["quantum_used"] += 1
            
            # Update waiting times for other processes
            update_waiting_times(queues, current_time, current_process)
            
            # Check for new arrivals and preemption
            if check_preemption(current_process, current_queue, queues, current_time):
                break

        if current_process["remaining_time"] == 0:
            # Process completed
            current_process["completion_time"] = current_time
            completed.append(current_process)
            print(f"Process {current_process['name']} completed at time {current_time}")
        else:
            # Process not completed, handle queue transition
            demote_process(current_process, current_queue, queues)

        print_queues()

    # Calculate metrics
    metrics = []
    for process in completed:
        turnaround_time = process["completion_time"] - process["arrival_time"]
        waiting_time = process["waiting_time"]
        metrics.append({
            "process": process["name"],
            "ct": process["completion_time"],
            "tat": turnaround_time,
            "wt": waiting_time
        })

    metrics.sort(key=lambda x: x["process"])
    return {"gantt": gantt, "metrics": metrics}

class DeadlineIOScheduler:
    """
    Deadline I/O Scheduler implementation
    Handles read and write requests with deadlines
    """
    def __init__(self, read_expire=500, write_expire=5000, writes_starved=2, fifo_batch=16, front_merges=True):
        self.read_expire = read_expire  # milliseconds
        self.write_expire = write_expire  # milliseconds
        self.writes_starved = writes_starved
        self.fifo_batch = fifo_batch
        self.front_merges = front_merges
        
        # Priority queues for read and write requests
        self.read_queue = []  # Higher priority
        self.write_queue = []
        
        # Track number of read batches processed
        self.read_batches_processed = 0
        
        # Current time in milliseconds
        self.current_time = 0

    def add_request(self, request):
        """
        Add a new I/O request to the appropriate queue
        Args:
            request: Dictionary containing:
                - type: 'read' or 'write'
                - sector: sector number
                - size: request size
                - arrival_time: time when request arrived
        """
        # Calculate deadline based on request type
        if request['type'] == 'read':
            deadline = request['arrival_time'] + self.read_expire
            queue = self.read_queue
        else:
            deadline = request['arrival_time'] + self.write_expire
            queue = self.write_queue
        
        # Add deadline to request
        request['deadline'] = deadline
        
        # Add to appropriate queue
        queue.append(request)
        
        # Sort queue by deadline
        queue.sort(key=lambda x: x['deadline'])
        
        # Try to merge with existing requests if front_merges is enabled
        if self.front_merges:
            self._try_merge(request, queue)

    def _try_merge(self, request, queue):
        """
        Try to merge the new request with existing ones
        """
        if not queue:
            return
            
        # Find requests that can be merged
        for i, existing_request in enumerate(queue):
            if existing_request['sector'] == request['sector']:
                # Merge requests
                existing_request['size'] += request['size']
                queue.pop(i)  # Remove the new request
                break

    def get_next_request(self):
        """
        Get the next request to process based on deadline scheduling rules
        Returns:
            Next request to process or None if no requests
        """
        # Check if any requests have expired
        self._check_expired_requests()
        
        # Process read requests if available and not starved
        if self.read_queue and self.read_batches_processed < self.writes_starved:
            self.read_batches_processed += 1
            return self._get_batch(self.read_queue)
        
        # Process write requests if available
        if self.write_queue:
            self.read_batches_processed = 0  # Reset read batch counter
            return self._get_batch(self.write_queue)
        
        # Process remaining read requests if any
        if self.read_queue:
            return self._get_batch(self.read_queue)
        
        return None

    def _check_expired_requests(self):
        """
        Check for expired requests in both queues
        """
        current_time = self.current_time
        
        # Check read queue
        expired_reads = [r for r in self.read_queue if r['deadline'] < current_time]
        if expired_reads:
            print(f"Expired read requests: {[r['sector'] for r in expired_reads]}")
        
        # Check write queue
        expired_writes = [r for r in self.write_queue if r['deadline'] < current_time]
        if expired_writes:
            print(f"Expired write requests: {[r['sector'] for r in expired_writes]}")

    def _get_batch(self, queue):
        """
        Get a batch of requests from the queue
        Args:
            queue: Queue to get requests from
        Returns:
            List of requests in the batch
        """
        if not queue:
            return None
            
        # Get requests up to fifo_batch size
        batch = []
        while queue and len(batch) < self.fifo_batch:
            batch.append(queue.pop(0))
            
        return batch

    def process_requests(self, requests):
        """
        Process a list of I/O requests
        Args:
            requests: List of I/O requests to process
        Returns:
            List of processed requests in order
        """
        processed_requests = []
        
        # Add all requests to appropriate queues
        for request in requests:
            self.add_request(request)
        
        # Process requests until all queues are empty
        while self.read_queue or self.write_queue:
            batch = self.get_next_request()
            if batch:
                processed_requests.extend(batch)
                # Update current time based on processing the batch
                self.current_time += len(batch) * 10  # Assuming 10ms per request
            
        return processed_requests

def deadline_io_scheduling(requests):
    """
    Wrapper function to use the Deadline I/O Scheduler
    Args:
        requests: List of I/O requests to process
    Returns:
        Dictionary containing processed requests and metrics
    """
    scheduler = DeadlineIOScheduler()
    processed_requests = scheduler.process_requests(requests)
    
    # Calculate metrics
    metrics = []
    for request in processed_requests:
        metrics.append({
            "type": request["type"],
            "sector": request["sector"],
            "size": request["size"],
            "arrival_time": request["arrival_time"],
            "completion_time": request["deadline"],
            "turnaround_time": request["deadline"] - request["arrival_time"]
        })
    
    return {
        "processed_requests": processed_requests,
        "metrics": metrics
    }

def deadline_scheduling(tasks):
    """
    Deadline Scheduling Algorithm
    Args:
        tasks: List of tasks with name, arrival_time, execution_time, and deadline
    Returns:
        Dictionary containing Gantt chart and metrics
    """
    if not tasks:
        return {"gantt": [], "metrics": []}

    # Initialize processes
    processes = []
    for task in tasks:
        processes.append({
            "name": task["name"],
            "arrival_time": task.get("arrival_time", 0),
            "execution_time": task["execution_time"],
            "deadline": task.get("deadline", 0),
            "remaining_time": task["execution_time"],
            "start_time": -1,
            "completion_time": -1,
            "missed_deadline": False
        })

    # Sort by arrival time
    processes.sort(key=lambda x: x["arrival_time"])

    current_time = 0
    ready_queue = []
    gantt = []
    completed = []

    while processes or ready_queue:
        # Add newly arrived processes to ready queue
        while processes and processes[0]["arrival_time"] <= current_time:
            ready_queue.append(processes.pop(0))

        if not ready_queue:
            if processes:
                current_time = processes[0]["arrival_time"]
                continue
            else:
                break

        # Sort ready queue by deadline (earliest deadline first)
        ready_queue.sort(key=lambda x: (x["deadline"], x["arrival_time"]))

        # Get the process with earliest deadline
        current_process = ready_queue.pop(0)

        # Check if process will miss its deadline
        if current_time + current_process["remaining_time"] > current_process["deadline"]:
            current_process["missed_deadline"] = True
            print(f"Warning: Process {current_process['name']} will miss its deadline!")

        # Record start time if first execution
        if current_process["start_time"] == -1:
            current_process["start_time"] = current_time
            print(f"Process {current_process['name']} started execution at time {current_time}")

        # Execute the process
        start_time = current_time
        current_time += current_process["remaining_time"]
        current_process["remaining_time"] = 0
        current_process["completion_time"] = current_time

        # Add to Gantt chart
        gantt.append({
            "process": current_process["name"],
            "start": start_time,
            "end": current_time
        })

        # Add to completed list
        completed.append(current_process)
        print(f"Process {current_process['name']} completed at time {current_time}")

    # Calculate metrics
    metrics = []
    for process in completed:
        turnaround_time = process["completion_time"] - process["arrival_time"]
        waiting_time = turnaround_time - process["execution_time"]
        metrics.append({
            "process": process["name"],
            "ct": process["completion_time"],
            "tat": turnaround_time,
            "wt": waiting_time,
            "missed_deadline": process["missed_deadline"]
        })

    # Sort metrics by process name to maintain consistent order
    metrics.sort(key=lambda x: x["process"])
    return {"gantt": gantt, "metrics": metrics}

def shortest_job_first(tasks):
    """
    Shortest Job First (SJF) Scheduling Algorithm
    Args:
        tasks: List of tasks with name, arrival_time, and execution_time
    Returns:
        Dictionary containing Gantt chart and metrics
    """
    if not tasks:
        return {"gantt": [], "metrics": []}

    # Initialize processes
    processes = []
    for task in tasks:
        processes.append({
            "name": task["name"],
            "arrival_time": task.get("arrival_time", 0),
            "execution_time": task["execution_time"],
            "remaining_time": task["execution_time"],
            "start_time": -1,
            "completion_time": -1
        })

    # Sort by arrival time
    processes.sort(key=lambda x: x["arrival_time"])

    current_time = 0
    ready_queue = []
    gantt = []
    completed = []

    while processes or ready_queue:
        # Add newly arrived processes to ready queue
        while processes and processes[0]["arrival_time"] <= current_time:
            ready_queue.append(processes.pop(0))

        if not ready_queue:
            if processes:
                current_time = processes[0]["arrival_time"]
                continue
            else:
                break

        # Sort ready queue by execution time (shortest first)
        ready_queue.sort(key=lambda x: x["remaining_time"])

        # Get the process with shortest remaining time
        current_process = ready_queue.pop(0)

        # Record start time if first execution
        if current_process["start_time"] == -1:
            current_process["start_time"] = current_time
            print(f"Process {current_process['name']} started execution at time {current_time}")

        # Execute the process
        start_time = current_time
        current_time += current_process["remaining_time"]
        current_process["remaining_time"] = 0
        current_process["completion_time"] = current_time

        # Add to Gantt chart
        gantt.append({
            "process": current_process["name"],
            "start": start_time,
            "end": current_time
        })

        # Add to completed list
        completed.append(current_process)
        print(f"Process {current_process['name']} completed at time {current_time}")

    # Calculate metrics
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

    # Sort metrics by process name to maintain consistent order
    metrics.sort(key=lambda x: x["process"])
    return {"gantt": gantt, "metrics": metrics} 