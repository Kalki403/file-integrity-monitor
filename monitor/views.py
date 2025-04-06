import os
import hashlib
import threading
import time
from django.shortcuts import render
from django.http import JsonResponse, FileResponse

# Global variables
MONITOR_DIR = None  # Directory to monitor
LOG_DIR = None  # Directory to save logs
old_state = {}  # Dictionary to store file hashes
monitoring = False  # Flag to indicate if monitoring is active
log_messages = []  # List to store log messages
LOG_FILE_PATH = None  # Path to the log file (dynamic)

# Function to calculate the hash of a file
def calculate_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):  # Read in chunks to handle large files
            hasher.update(chunk)
    return hasher.hexdigest()

# Function to scan the directory and calculate hashes
def scan_directory(directory):
    excluded_dirs = {"__pycache__", "venv", ".git", "node_modules"}  # Directories to exclude
    excluded_extensions = {".pyc", ".log", ".tmp", ".db"}  # File extensions to exclude

    file_hashes = {}
    for root, dirs, files in os.walk(directory):
        # Exclude unwanted directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Exclude files with unwanted extensions
                if not any(file.endswith(ext) for ext in excluded_extensions):
                    file_hashes[file_path] = calculate_file_hash(file_path)
            except Exception as e:
                log_message = f"Error reading file {file_path}: {e}"
                log_messages.append(log_message)
                save_log_to_file(log_message)
    return file_hashes

# Function to detect changes
def detect_changes(old_state, new_state):
    changes = {
        "added": [],
        "deleted": [],
        "modified": []
    }

    # Find added files
    for file in new_state:
        if file not in old_state:
            changes["added"].append(file)

    # Find deleted files
    for file in old_state:
        if file not in new_state:
            changes["deleted"].append(file)

    # Find modified files
    for file in new_state:
        if file in old_state and old_state[file] != new_state[file]:
            changes["modified"].append(file)

    return changes

# Function to monitor files periodically
def monitor_files():
    global old_state
    while monitoring:
        time.sleep(10)  # Scan interval (10 seconds)
        new_state = scan_directory(MONITOR_DIR)
        changes = detect_changes(old_state, new_state)
        if any(changes.values()):
            log_message = f"Changes detected: {changes}"
            log_messages.append(log_message)
            save_log_to_file(log_message)
        old_state = new_state

# Views
def dashboard(request):
    context = {
        "monitor_dir": MONITOR_DIR,
        "log_dir": LOG_DIR,
        "log_messages": log_messages,  # Pass log messages to the template
        "monitoring_status": monitoring,
    }
    return render(request, "monitor/dashboard.html", context)

def start_monitoring(request):
    global monitoring, MONITOR_DIR
    if not monitoring and MONITOR_DIR:
        monitoring = True
        threading.Thread(target=monitor_files).start()
        log_message = "Monitoring started."
        log_messages.append(log_message)
        save_log_to_file(log_message)  # Save log to file
        return JsonResponse({"status": "started"})
    return JsonResponse({"status": "error", "message": "Monitoring already started or no directory selected."})

def stop_monitoring(request):
    global monitoring
    monitoring = False
    log_message = "Monitoring stopped."
    log_messages.append(log_message)
    save_log_to_file(log_message)  # Save log to file
    return JsonResponse({"status": "stopped"})

def select_directory(request):
    global MONITOR_DIR, LOG_FILE_PATH
    directory = request.POST.get("directory")
    if directory and os.path.isdir(directory):
        MONITOR_DIR = directory
        # Update log file name based on the monitored directory
        if LOG_DIR:
            dir_name = os.path.basename(os.path.normpath(MONITOR_DIR))  # Extract directory name
            LOG_FILE_PATH = os.path.join(LOG_DIR, f"{dir_name}.txt")  # Set log file name
        log_message = f"Directory selected: {MONITOR_DIR}"
        log_messages.append(log_message)
        save_log_to_file(log_message)  # Save log to file
        return JsonResponse({"status": "success", "directory": MONITOR_DIR})
    return JsonResponse({"status": "error", "message": "Invalid directory."})

def select_log_directory(request):
    global LOG_DIR, LOG_FILE_PATH
    log_directory = request.POST.get("log_directory")
    if log_directory and os.path.isdir(log_directory):
        LOG_DIR = log_directory
        # Update log file name based on the monitored directory
        if MONITOR_DIR:
            dir_name = os.path.basename(os.path.normpath(MONITOR_DIR))  # Extract directory name
            LOG_FILE_PATH = os.path.join(LOG_DIR, f"{dir_name}.txt")  # Set log file name
        log_message = f"Log directory selected: {LOG_DIR}"
        log_messages.append(log_message)
        save_log_to_file(log_message)  # Save log to file
        return JsonResponse({"status": "success", "log_directory": LOG_DIR})
    return JsonResponse({"status": "error", "message": "Invalid log directory."})

def get_logs(request):
    return JsonResponse({"logs": log_messages})  # Return logs as JSON

def download_logs(request):
    if LOG_FILE_PATH and os.path.exists(LOG_FILE_PATH):
        log_file = open(LOG_FILE_PATH, "rb")
        return FileResponse(log_file, as_attachment=True, filename=os.path.basename(LOG_FILE_PATH))
    return JsonResponse({"status": "error", "message": "No log file available."})

# Function to save logs to a file
def save_log_to_file(log_message):
    if LOG_FILE_PATH:
        with open(LOG_FILE_PATH, "a") as log_file:  # Append mode ('a')
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Add a timestamp
            log_file.write(f"[{timestamp}] {log_message}\n")