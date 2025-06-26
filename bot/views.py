import spacy
import spacy.cli
import os
import subprocess
import platform
from django.http import JsonResponse
from django.shortcuts import render
from transformers import pipeline
from textblob import TextBlob
from taskmanager.models import Task
from django.utils import timezone
import json
# Test in Django shell



# Load models only once
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
nlp = spacy.load("en_core_web_sm")
sentiment_analyzer = pipeline("sentiment-analysis")

# Store conversation context
conversation_context = {}

# Enhanced application mappings with more applications
APP_MAPPINGS = {
    'calculator': {
        'windows': 'calc.exe',
        'linux': 'gnome-calculator',
        'mac': 'Calculator'
    },
    'notepad': {
        'windows': 'notepad.exe',
        'linux': 'gedit',
        'mac': 'TextEdit'
    },
    'chrome': {
        'windows': 'start chrome',
        'linux': 'google-chrome',
        'mac': 'open -a "Google Chrome"'
    },
    'browser': {
        'windows': 'start chrome',
        'linux': 'xdg-open https://www.google.com',
        'mac': 'open https://www.google.com'
    },
    'word': {
        'windows': 'start winword',
        'mac': 'open -a "Microsoft Word"'
    },
    'excel': {
        'windows': 'start excel',
        'mac': 'open -a "Microsoft Excel"'
    }
}

def get_os_specific_command(app_name):
    current_os = platform.system().lower()
    if 'windows' in current_os:
        return APP_MAPPINGS.get(app_name, {}).get('windows', app_name)
    elif 'linux' in current_os:
        return APP_MAPPINGS.get(app_name, {}).get('linux', app_name)
    elif 'darwin' in current_os:
        return APP_MAPPINGS.get(app_name, {}).get('mac', app_name)
    return app_name

def execute_command(command):
    try:
        if platform.system() == 'Windows':
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(command, shell=True, creationflags=CREATE_NO_WINDOW)
        else:
            subprocess.Popen(command, shell=True, start_new_session=True)
        return True
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

def analyze_sentiment(text):
    try:
        result = sentiment_analyzer(text)[0]
        return {
            'label': result['label'],
            'score': result['score']
        }
    except:
        return {'label': 'NEUTRAL', 'score': 0.5}

def get_conversation_context(user_id):
    if user_id not in conversation_context:
        conversation_context[user_id] = {
            'last_command': None,
            'last_topic': None,
            'task_context': None,
            'scheduling_context': None
        }
    return conversation_context[user_id]

def update_conversation_context(user_id, updates):
    context = get_conversation_context(user_id)
    context.update(updates)
    conversation_context[user_id] = context

def get_running_processes():
    def try_wmic():
        try:
            output = subprocess.check_output(
                'wmic process get name,processid,workingsetsize /format:csv',
                shell=True,
                stderr=subprocess.PIPE,
                timeout=5
            ).decode('utf-8', errors='ignore')
            
            processes = []
            for line in output.splitlines():
                if "Node," in line or not line.strip():
                    continue  # Skip header or empty lines
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    try:
                        name = parts[1].strip('"')
                        pid = parts[2].strip('"')
                        mem = int(parts[3].strip('"')) // 1024
                        processes.append({
                            'pid': pid,
                            'name': name,
                            'memory': f"{mem} K",
                            'cpu': "N/A",
                            'execution_time': 5,
                            'priority': len(processes) + 1
                        })
                    except Exception as parse_err:
                        print(f"Parse error in WMIC: {parse_err}")
                        continue
            return processes[:15]
        except Exception as e:
            print(f"[WMIC ERROR] {e}")
            return None

    def try_ps():
        try:
            output = subprocess.check_output(
                ["ps", "-eo", "pid,comm,%mem,pcpu", "--sort=-%mem", "--no-headers"],
                stderr=subprocess.PIPE,
                timeout=5
            ).decode('utf-8')

            processes = []
            for line in output.strip().split('\n')[:15]:
                parts = line.strip().split(None, 3)
                if len(parts) == 4:
                    pid, name, mem, cpu = parts
                    processes.append({
                        'pid': pid,
                        'name': name,
                        'memory': f"{mem}%",
                        'cpu': f"{cpu}%",
                        'execution_time': 5,
                        'priority': len(processes) + 1
                    })
            return processes
        except Exception as e:
            print(f"[ps ERROR] {e}")
            return None

    def try_psutil():
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    processes.append({
                        'pid': str(proc.info['pid']),
                        'name': proc.info['name'] or "Unknown",
                        'memory': f"{proc.info['memory_percent']:.1f}%",
                        'cpu': f"{proc.info['cpu_percent']:.1f}%",
                        'execution_time': 5,
                        'priority': len(processes) + 1
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    continue
            return processes[:15]
        except Exception as e:
            print(f"[psutil ERROR] {e}")
            return None

    # Execution flow
    print("[INFO] Detecting system platform...")
    processes = None
    system_platform = platform.system()

    if system_platform == 'Windows':
        print("[INFO] Attempting WMIC...")
        processes = try_wmic()
        if not processes:
            print("[INFO] WMIC failed, trying psutil...")
            processes = try_psutil()
    else:
        print("[INFO] Attempting ps...")
        processes = try_ps()
        if not processes:
            print("[INFO] ps failed, trying psutil...")
            processes = try_psutil()

    return processes or []
  # Return empty list if all methods fail
def chat(request):
    user_input = request.GET.get("msg", "").strip().lower()
    user_id = request.session.session_key or request.session.create()
    
    if not user_input:
        return JsonResponse({"reply": "Please enter a command."})

    # Analyze sentiment
    sentiment = analyze_sentiment(user_input)
    context = get_conversation_context(user_id)
    
    # Get context-aware response
    if context['last_command'] and "yes" in user_input:
        # Handle other command confirmations here
        pass
    
    # Task Management Commands
    if "list tasks" in user_input:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"reply": "You need to be logged in to view tasks. Please log in first."})
            
        tasks = Task.objects.filter(user=request.user).order_by('-start_time')[:5]  # Changed from created_at to start_time
        if not tasks:
            return JsonResponse({"reply": "No tasks found."})
        
        response = "Recent tasks:\n"
        for task in tasks:
            response += f"- {task.title} (Priority: {task.priority}, Status: {task.status})\n"
        return JsonResponse({"reply": response})
    
    elif "delete task" in user_input:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"reply": "You need to be logged in to delete tasks. Please log in first."})
            
        # Extract task title
        doc = nlp(user_input)
        task_title = None
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]:
                task_title = ent.text
                break
        
        if not task_title:
            task_title = user_input.split("delete task", 1)[1].strip()
        
        try:
            task = Task.objects.get(title=task_title, user=request.user)  # Only get tasks for the current user
            task.delete()
            return JsonResponse({"reply": f"Task '{task_title}' has been deleted."})
        except Task.DoesNotExist:
            return JsonResponse({"reply": f"Task '{task_title}' not found."})
    
    # System Monitoring Commands
    elif "system status" in user_input:
        try:
            if platform.system() == 'Windows':
                cpu = subprocess.check_output("wmic cpu get loadpercentage", shell=True).decode()
                memory = subprocess.check_output("wmic OS get FreePhysicalMemory", shell=True).decode()
                disk = subprocess.check_output("wmic logicaldisk get size,freespace,caption", shell=True).decode()
            else:
                cpu = subprocess.check_output("top -bn1 | grep 'Cpu(s)'", shell=True).decode()
                memory = subprocess.check_output("free -m", shell=True).decode()
                disk = subprocess.check_output("df -h", shell=True).decode()
            
            return JsonResponse({
                "reply": f"System Status:\nCPU: {cpu}\nMemory: {memory}\nDisk: {disk}"
            })
        except Exception as e:
            return JsonResponse({"reply": f"Failed to get system status: {str(e)}"})
    
    # Scheduling Commands
    elif "view schedule" in user_input:
        try:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse({"reply": "You need to be logged in to view schedules. Please log in first."})
                
            tasks = Task.objects.filter(user=request.user, status='Pending').order_by('priority', '-start_time')
            if not tasks:
                return JsonResponse({"reply": "No scheduled tasks found."})
            
            response = "Current Schedule:\n"
            for task in tasks:
                response += f"- {task.title} (Priority: {task.priority})\n"
            return JsonResponse({"reply": response})
        except Exception as e:
            return JsonResponse({"reply": f"Failed to view schedule: {str(e)}"})
    
    # -------- OPEN APPLICATIONS --------
    if any(word in user_input for word in ["open", "launch", "start"]):
        app_name = None
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]:
                app_name = ent.text.lower()
                break
        
        if not app_name:
            for i, token in enumerate(user_input.split()):
                if token in ["open", "launch", "start"] and i + 1 < len(user_input.split()):
                    app_name = user_input.split()[i + 1].lower()
                    break
        
        if app_name:
            command = get_os_specific_command(app_name)
            if command and execute_command(command):
                return JsonResponse({"reply": f"Opening {app_name}..."})
            else:
                return JsonResponse({"reply": f"Could not open {app_name}. Please try another application."})

    # -------- SHUTDOWN COMMANDS --------
    elif any(phrase in user_input for phrase in ["shutdown system", "shutdown computer", "shut down"]):
        return JsonResponse({"reply": "Shutdown command received (disabled for safety)."})

    # -------- DISK COMMANDS --------
    elif any(phrase in user_input for phrase in ["check disk usage", "check free space", "check memory"]):
        try:
            if platform.system() == 'Windows':
                result = subprocess.check_output(
                    "wmic logicaldisk get size,freespace,caption", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8', 'ignore')
            else:
                result = subprocess.check_output(
                    "df -h", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8')
            return JsonResponse({"reply": result})
        except Exception as e:
            return JsonResponse({"reply": f"Failed to check disk usage: {str(e)}"})

    # -------- SYSTEM INFO --------
    elif any(phrase in user_input for phrase in ["system info", "cpu usage"]):
        try:
            if platform.system() == 'Windows':
                result = subprocess.check_output(
                    "systeminfo", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8', 'ignore')
            else:
                result = subprocess.check_output(
                    "top -bn1 | head -n 5", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8')
            return JsonResponse({"reply": result})
        except Exception as e:
            return JsonResponse({"reply": f"Failed to get system info: {str(e)}"})

    # -------- NETWORK COMMANDS --------
    elif "check internet connection" in user_input:
        try:
            if platform.system() == 'Windows':
                result = subprocess.check_output(
                    "ping -n 1 google.com", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8', 'ignore')
            else:
                result = subprocess.check_output(
                    "ping -c 1 google.com", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8')
            return JsonResponse({"reply": "Internet connection is working.\n" + result})
        except:
            return JsonResponse({"reply": "No internet connection detected."})
    
    elif "ping google.com" in user_input:
        try:
            if platform.system() == 'Windows':
                result = subprocess.check_output(
                    "ping google.com", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8', 'ignore')
            else:
                result = subprocess.check_output(
                    "ping -c 4 google.com", 
                    shell=True,
                    stderr=subprocess.PIPE
                ).decode('utf-8')
            return JsonResponse({"reply": result})
        except:
            return JsonResponse({"reply": "Failed to ping google.com"})

    # -------- RESTART COMMANDS --------
    elif any(phrase in user_input for phrase in ["restart system", "reboot"]):
        return JsonResponse({"reply": "Restart command received (disabled for safety)."})

    # -------- FILE OPERATIONS --------
    elif "open file explorer" in user_input:
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(["explorer"])
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(["open", "."])
            else:  # Linux
                subprocess.Popen(["xdg-open", "."])
            return JsonResponse({"reply": "Opening file explorer..."})
        except Exception as e:
            return JsonResponse({"reply": f"Failed to open file explorer: {str(e)}"})

    
    elif "open downloads folder" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("start explorer shell:::{374DE290-123F-4565-9164-39C4925E467B}")
            else:
                os.system("xdg-open ~/Downloads")
            return JsonResponse({"reply": "Opening downloads folder..."})
        except:
            return JsonResponse({"reply": "Failed to open downloads folder"})
    
    elif "open documents folder" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("start explorer shell:::{A3A9B3A9-4632-4BB8-B4B0-B397109E5C53}")
            else:
                os.system("xdg-open ~/Documents")
            return JsonResponse({"reply": "Opening documents folder..."})
        except:
            return JsonResponse({"reply": "Failed to open documents folder"})

    # -------- TASK MANAGEMENT --------
    elif "open task manager" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("start taskmgr")
            else:
                os.system("gnome-system-monitor")
            return JsonResponse({"reply": "Opening task manager..."})
        except:
            return JsonResponse({"reply": "Failed to open task manager"})
    
    elif "close task manager" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("taskkill /im taskmgr.exe /f")
            else:
                os.system("pkill gnome-system-monitor")
            return JsonResponse({"reply": "Closing task manager..."})
        except:
            return JsonResponse({"reply": "Failed to close task manager"})
    
    elif "kill application" in user_input:
        try:
            app_name = " ".join(user_input.split()[1:])
            if platform.system() == 'Windows':
                os.system(f"taskkill /im {app_name}.exe /f")
            else:
                os.system(f"pkill {app_name}")
            return JsonResponse({"reply": f"Killing application: {app_name}"})
        except:
            return JsonResponse({"reply": f"Failed to kill application"})

    # -------- BROWSER COMMANDS --------
    elif "open browser" in user_input:
        try:
            command = get_os_specific_command('browser')
            if execute_command(command):
                return JsonResponse({"reply": "Opening browser..."})
            else:
                return JsonResponse({"reply": "Failed to open browser"})
        except:
            return JsonResponse({"reply": "Failed to open browser"})
    
    elif "open youtube" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("start chrome https://www.youtube.com")
            else:
                os.system("xdg-open https://www.youtube.com")
            return JsonResponse({"reply": "Opening YouTube..."})
        except:
            return JsonResponse({"reply": "Failed to open YouTube"})

    # -------- VOLUME CONTROL --------
    elif "mute volume" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("nircmd.exe mutesysvolume 1")
            else:
                os.system("amixer set Master mute")
            return JsonResponse({"reply": "Volume muted"})
        except:
            return JsonResponse({"reply": "Failed to mute volume"})
    
    elif "unmute volume" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("nircmd.exe mutesysvolume 0")
            else:
                os.system("amixer set Master unmute")
            return JsonResponse({"reply": "Volume unmuted"})
        except:
            return JsonResponse({"reply": "Failed to unmute volume"})
    
    elif "increase volume" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("nircmd.exe changesysvolume 5000")
            else:
                os.system("amixer set Master 5%+")
            return JsonResponse({"reply": "Volume increased"})
        except:
            return JsonResponse({"reply": "Failed to increase volume"})
    
    elif "decrease volume" in user_input:
        try:
            if platform.system() == 'Windows':
                os.system("nircmd.exe changesysvolume -5000")
            else:
                os.system("amixer set Master 5%-")
            return JsonResponse({"reply": "Volume decreased"})
        except:
            return JsonResponse({"reply": "Failed to decrease volume"})

    # -------- SCHEDULING COMMANDS --------
    elif "round robin" in user_input:
        try:
            tasks = get_running_processes()
            if not tasks:
                return JsonResponse({"reply": "Could not retrieve running processes."})
            
            from taskmanager.scheduler import round_robin
            schedule = round_robin(tasks, time_slice=2)
            
            response = "Round Robin Schedule for current processes:\n"
            for i, task in enumerate(schedule):
                response += f"{i+1}. {task['name']} (PID: {task['pid']}, Memory: {task.get('memory', 'N/A')})\n"
            
            return JsonResponse({"reply": response})
        except:
            return JsonResponse({"reply": "Failed to perform round robin scheduling"})

    elif "priority scheduling" in user_input:
        try:
            tasks = get_running_processes()
            if not tasks:
                return JsonResponse({"reply": "Could not retrieve running processes."})
            
            for task in tasks:
                try:
                    mem = float(task['memory'].replace(',', '').replace(' K', ''))
                    task['priority'] = int(mem / 10)
                except:
                    task['priority'] = 1
            
            from taskmanager.scheduler import priority_scheduling
            schedule = priority_scheduling(tasks)
            
            response = "Priority Schedule for current processes (by memory usage):\n"
            for i, task in enumerate(schedule):
                response += f"{i+1}. {task['name']} (PID: {task['pid']}, Memory: {task['memory']}, Priority: {task['priority']})\n"
            
            return JsonResponse({"reply": response})
        except:
            return JsonResponse({"reply": "Failed to perform priority scheduling"})

    elif "ai prioritize" in user_input:
        try:
            tasks = get_running_processes()
            if not tasks:
                return JsonResponse({"reply": "Could not retrieve running processes."})
            
            for task in tasks:
                task['importance'] = 0
                if 'system' in task['name'].lower() or 'win' in task['name'].lower():
                    task['importance'] += 3
                elif 'explorer' in task['name'].lower() or 'chrome' in task['name'].lower():
                    task['importance'] += 2
                try:
                    mem = float(task['memory'].replace(',', '').replace(' K', ''))
                    task['importance'] += mem / 1000
                except:
                    pass
            
            from taskmanager.scheduler import ai_based_prioritization
            prioritized_tasks = ai_based_prioritization(tasks)
            
            response = "AI Prioritized Tasks (based on process importance):\n"
            for i, task in enumerate(prioritized_tasks):
                response += f"{i+1}. {task['name']} (Importance: {task.get('importance', 0):.1f}, Memory: {task.get('memory', 'N/A')})\n"
            
            return JsonResponse({"reply": response})
        except:
            return JsonResponse({"reply": "Failed to perform AI prioritization"})

    # -------- UNKNOWN COMMANDS --------
    else:
        intents = [
            "open application", "check disk usage", "shutdown system", 
            "restart system", "open browser", "task manager", 
            "kill application", "volume control", "system info"
        ]
        try:
            result = classifier(user_input, candidate_labels=intents)
            top_intent = result["labels"][0]
            return JsonResponse({
                "reply": f"I'm not sure, but it seems like you want to: {top_intent}. Try rephrasing or using specific commands."
            })
        except:
            return JsonResponse({
                "reply": "I didn't understand that command. Try something like 'open chrome', 'check disk usage', or 'system info'."
            })

    # Update context with current command
    update_conversation_context(user_id, {'last_command': None})
    
    # Return response based on sentiment
    if sentiment['label'] == 'NEGATIVE':
        return JsonResponse({
            "reply": "I understand you might be frustrated. Let me help you with that. " + 
                    "Try using commands like 'create task', 'list tasks', or 'system status'."
        })
    
    return JsonResponse({
        "reply": "I didn't understand that command. Try something like 'create task', 'list tasks', or 'system status'."
    })

def chat_ui(request):
    return render(request, "bot/chat.html")


# Test process listing
processes = get_running_processes()
print("Found processes:", len(processes))
for p in processes[:3]:  # Print first 3 as sample
    print(p)

# Test round robin
if processes:
    from taskmanager.scheduler import round_robin
    schedule = round_robin(processes[:5], 2)  # Test with first 5 processes
    print("Round Robin Schedule:")
    for item in schedule:
        print(item)


# Test platform-specific commands
print("OS:", platform.system())
print("Browser command:", get_os_specific_command('browser'))

spacy.cli.download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")