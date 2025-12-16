import socket
import uuid
from PySide6.QtWidgets import (
    QApplication, QDialog, QMessageBox, QProgressDialog, QTextEdit, QSystemTrayIcon,
    QMenu, QVBoxLayout, QStatusBar, QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QProgressBar, QSizePolicy,QLabel
)

from PySide6.QtGui import QIcon, QTextCursor, QAction, QCursor, QFont,QPixmap
from PySide6.QtCore import QRunnable, QThreadPool, QEvent, QSize, QThread, QTimer, Qt, QObject, Signal, QMetaObject, Slot, QLockFile, QDir, QEventLoop
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from login import Ui_Dialog
from PySide6.QtWidgets import QLineEdit

import sys
import logging
import os
import platform
import logging.handlers
import requests
from requests.exceptions import RequestException
import urllib3
import json
from urllib.parse import urlparse, parse_qs, quote
from pathlib import Path
from datetime import datetime, timedelta, timezone 
from zoneinfo import ZoneInfo
from PIL import Image, ImageSequence
import subprocess
from queue import Queue
import threading
import time
import re
import io
import hashlib
import httpx
import mimetypes
from pid import PidFile, PidFileError
import warnings
import tempfile
import psutil  # To check if Photoshop is running
from threading import Lock, Semaphore, Thread
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

if platform.system() != "Windows":
    import fcntl
import numpy as np
try:
    from psd_tools import PSDImage
except ImportError:
    PSDImage = None
try:
    import rawpy
except ImportError:
    rawpy = None
try:
    import tifffile
except ImportError:
    tifffile = None
import pytz
import shutil

try:
    import imagecodecs
except ImportError:
    logger.warning("imagecodecs not installed, LZW-compressed TIFFs may not work")
from httpx import Timeout
if platform.system() == "Windows":
    import pythoncom
    import win32com.client
    import win32gui
    import win32con
from scp import SCPClient


from ssh2.session import Session
from ssh2.sftp import LIBSSH2_FXF_CREAT, LIBSSH2_FXF_WRITE, LIBSSH2_FXF_TRUNC
from ssh2.exceptions import SFTPError

# def fast_scp_upload(ssh_transport, src_path, dest_path):
#     with SCPClient(ssh_transport, socket_timeout=30) as scp:
#         scp.put(src_path, dest_path)

def fast_scp_upload(transport, src_path, dest_path):

    # ---- MAXIMIZE UPLOAD WINDOW ----
    transport.default_window_size = 33554432     # 32MB window by Mohan
    transport.default_max_packet_size = 1048576  # 1MB packet by Mohan
    transport.packetizer.REKEY_BYTES = pow(2, 40)
    transport.packetizer.REKEY_PACKETS = pow(2, 40)

    # ---- OPTIMIZED SCP ----
    scp = SCPClient(
        transport,
        socket_timeout=30,
        buff_size=1048576   # 1 MB chunks increased by Mohan
    )

    # ---- PUT IS FASTER THAN PUTFO ON WINDOWS ----
    scp.put(src_path, dest_path)

    scp.close()
    
    transport.close()  # transport close to prevent leakage by Mohan





SUPPORTED_EXTENSIONS = [
    "jpg", "jpeg", "png", "gif", "tiff", "tif", "bmp", "webp",
    "psd", "psb", "cr2", "nef", "arw", "dng", "raf", "pef", "srw"
]
import shlex
# Global stop queue for signaling
FILE_WATCHER_STOP_QUEUE = Queue()
# Handle paramiko import
try:
    import paramiko
    NAS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"paramiko not installed: {e}. NAS functionality disabled.")
    NAS_AVAILABLE = False
    paramiko = None

try:
    import traceback
except ImportError as e:
    logging.error(f"Failed to import traceback module: {e}")
    traceback = None  # Fallback to None if import fails

# At the top of the file, ensure all imports are explicit
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"PIL not installed: {e}. Image conversion disabled.")
    PIL_AVAILABLE = False
    Image = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Constants ===
BASE_DOMAIN = "https://app-uat.vmgpremedia.com"

BASE_DIR = Path(__file__).parent.resolve()

if platform.system() == "Windows":
    # Check if D: drive exists and is writable, else fall back to C:
    d_drive = Path("D:/")
    if d_drive.exists() and d_drive.is_dir():
        BASE_TARGET_DIR = d_drive / "PremediaApp" / "Nas"
    else:
        BASE_TARGET_DIR = Path("C:/PremediaApp/Nas")
else:
    # For Linux/macOS, use home directory
    BASE_TARGET_DIR = Path.home() / "PremediaApp" / "Nas"

# Ensure the directory exists
BASE_TARGET_DIR.mkdir(parents=True, exist_ok=True)

# Cache icon paths
ICON_CACHE = {}
def load_icon(path, description):
    return QIcon(path)

def add_version_footer(window, version_text):
    """
    Adds a version label to the bottom of any QDialog or QMainWindow.
    """
    from PySide6.QtWidgets import QLabel, QVBoxLayout
    from PySide6.QtCore import Qt

    version_label = QLabel(f"Version: {version_text}")
    version_label.setAlignment(Qt.AlignRight)
    version_label.setStyleSheet("color: gray; font-size: 10px; margin-right: 10px;")

    # If the window already has a layout, append it
    layout = window.layout()
    if layout:
        layout.addWidget(version_label)
    else:
        new_layout = QVBoxLayout(window)
        new_layout.addStretch()
        new_layout.addWidget(version_label)
        window.setLayout(new_layout)


ICON_CACHE = {}
BASE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))

def get_icon_path(icon_name: str) -> str:
    """
    Returns a safe and correct path to an icon file for both source and frozen builds.
    """
    if icon_name in ICON_CACHE:
        return str(ICON_CACHE[icon_name])

    # Detect icon directory (inside _MEIPASS for frozen apps)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        icons_dir = Path(sys._MEIPASS) / "icons"
    else:
        icons_dir = BASE_DIR / "icons"

    icon_path = icons_dir / icon_name

    # Debug log to help verify path at runtime
    if not icon_path.exists():
        print(f"[Icons] ⚠️ Missing icon: {icon_path}")

    ICON_CACHE[icon_name] = icon_path
    return str(icon_path)

# OS-specific main icon
ICON_PATH = get_icon_path({
    "Windows": "premedia.ico",
    "Darwin": "premedia.icns",
    "Linux": "premedia.png"
}.get(platform.system(), "premedia.png"))

LOGGEDIN_ICON_PATH = get_icon_path({
    "Windows": "login-logo.ico",
    "Darwin": "login-logo.icns",
    "Linux": "login-logo.png"
}.get(platform.system(), "login-logo.png"))

# PHOTOSHOP_ICON_PATH = get_icon_path("photoshop.png") if (BASE_DIR / "icons" / "photoshop.png").exists() else ""
# COPY_ICON_PATH = get_icon_path("copy_icon.png") if (BASE_DIR / "icons" / "folder.png").exists() else ""
# RETRY_ICON_PATH = get_icon_path("retry.png") if (BASE_DIR / "icons" / "folder.png").exists() else ""
# FOLDER_ICON_PATH = get_icon_path("folder.png") if (BASE_DIR / "icons" / "folder.png").exists() else ""

PHOTOSHOP_ICON_PATH = get_icon_path("photoshop.png")
COPY_ICON_PATH = get_icon_path("copy_icon.png")
RETRY_ICON_PATH = get_icon_path("retry.png")
FOLDER_ICON_PATH = get_icon_path("folder.png")


def get_cache_file_path():
    # Use BASE_TARGET_DIR as the base for cache file generation
    cache_dir = Path(BASE_TARGET_DIR) / "PremediaApp"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"Ensured cache directory exists: {cache_dir}")
    except Exception as e:
        print(f"Failed to create cache directory {cache_dir}: {e}")
        app_signals.append_log.emit(f"[Cache] Failed to create cache directory {cache_dir}: {str(e)}")
        # Fallback to a default directory if creation fails
        cache_dir = Path.home() / ".cache" / "PremediaApp"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"Fell back to default cache directory: {cache_dir}")
        except Exception as e2:
            print(f"Failed to create fallback cache directory {cache_dir}: {e2}")
            app_signals.append_log.emit(f"[Cache] Failed to create fallback cache directory {cache_dir}: {str(e2)}")
    
    cache_file = cache_dir / "cache.json"
    return str(cache_file)

CACHE_FILE = get_cache_file_path()
CACHE_DAYS = 10
API_URL = f"{BASE_DOMAIN}/api/ir_production/get/projectList?business=image_retouching"
DOWNLOAD_UPLOAD_API = f"{BASE_DOMAIN}/api/get_download_upload/submission"
OAUTH_URL = f"{BASE_DOMAIN}/oauth/token"
USER_VALIDATE_URL = f"{BASE_DOMAIN}/api/user/validate"
API_URL_CREATE = f"{BASE_DOMAIN}/api/nas_create/creative"
API_URL_UPDATE_CREATE = f"{BASE_DOMAIN}/api/nas_update/creative"
API_REPLACE_QC_QA_FILE = f"{BASE_DOMAIN}/api/nas-qc-qa/update/ir-files"
API_URL_UPLOAD = f"{BASE_DOMAIN}/api/post/operator_upload"
API_URL_UPLOAD_DOWNLOAD_UPDATE = f"{BASE_DOMAIN}/api/save_download_upload/update"
API_URL_PROJECT_LIST = f"{BASE_DOMAIN}/api/get/nas/assets"
API_URL_UPDATE_NAS_ASSET = f"{BASE_DOMAIN}/api/update/nas/assets"
DRUPAL_DB_ENTRY_API = f"{BASE_DOMAIN}/api/add/files/ir/assets"
API_URL_LOGOUT = f"{BASE_DOMAIN}/premedia/logout"
IS_APP_ACTIVE_UPLOAD_DOWNLOAD = False

# NAS_IP = "192.168.3.20"
# NAS_PASSWORD = "D&*qmn012@12"
# NAS_PORT = 2022
# NAS_SHARE = ""
# NAS_PREFIX ='/mnt/nas/softwaremedia/IR_prod'
# NAS_USERNAME = "irprod"
# MOUNTED_NAS_PATH ='/mnt/nas/softwaremedia/IR_prod'


NAS_IP = "192.168.1.145"
NAS_USERNAME = "irdev"
NAS_PASSWORD = "i#0f!L&+@s%^qc"
NAS_PORT = 22
NAS_SHARE = ""
NAS_PREFIX ='/mnt/nas/softwaremedia/IR_uat'
MOUNTED_NAS_PATH ='/mnt/nas/softwaremedia/IR_uat'

APPVERSION = "1.1.3"
API_POLL_INTERVAL = 5000  # 5 seconds in milliseconds
log_window_handler = None
# === Global State ===
GLOBAL_CACHE = None
CACHE_WRITE_LOCK = threading.Lock()
HTTP_SESSION = requests.Session()
FILE_WATCHER_RUNNING = False
LOGGING_ACTIVE = True
app_signals = None
LAST_API_HIT_TIME = None
NEXT_API_HIT_TIME = None

USER_SYSTEM_INFO = {}

# ========== CONFIGURATION ==========
THROTTLE_MBPS = None       # Set to e.g. 50, 100, or None for no limit (full speed)
MIN_REQUIRED_MBPS = 50     # Optional: for warning if speed too low (in Mbps)
PRINT_INTERVAL = 0.5       # Progress update frequency in seconds
# ===================================
# === Logging Setup ===
logger = logging.getLogger("PremediaApp")
logger.setLevel(logging.INFO)  # Only INFO and higher allowed

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_dir = BASE_DIR / "log"

try:
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log", maxBytes=10485760, backupCount=5
    )
    file_handler.setLevel(logging.ERROR)  # <- Restrict handler
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    logger.error(f"Error setting up log file: {e}")
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)  # <- Restrict console handler too
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# === Signals for Safe GUI Updates ===
class AppSignals(QObject):
    update_status = Signal(str)
    append_log = Signal(str)
    update_file_list = Signal(str, str, str, int, bool)
    api_call_status = Signal(str, str, int)
    update_timer_status = Signal(str)

app_signals = AppSignals()

# === Custom Log Handler ===
class LogWindowHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_queue = []
        self.log_window = None

    def set_log_window(self, log_window):
        self.log_window = log_window
        # Flush queued logs
        for record in self.log_queue:
            self.emit(record)
        self.log_queue.clear()

    def emit(self, record):
        msg = self.format(record)
        if self.log_window and hasattr(app_signals, 'append_log'):
            try:
                app_signals.append_log.emit(msg)
            except Exception as e:
                self.log_queue.append(record)
                logging.getLogger("PremediaApp").warning(f"Failed to emit log to LogWindow: {e}")
        else:
            self.log_queue.append(record)

# === Async Logging ===
log_queue = Queue()
def async_log_worker():
    global LOGGING_ACTIVE
    while LOGGING_ACTIVE:
        record = log_queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)

log_thread = threading.Thread(target=async_log_worker, daemon=True)

# log_window_handler = None  # Global variable to store LogWindowHandler

def setup_logger(log_window=None):
    logger = logging.getLogger("PremediaApp")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    # Add StreamHandler for fallback logging
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)

    # Add LogWindowHandler
    global log_window_handler
    log_window_handler = LogWindowHandler()
    log_window_handler.setLevel(logging.INFO)
    logger.addHandler(log_window_handler)

    # Connect signals if log_window is provided
    if log_window:
        log_window_handler.set_log_window(log_window)
        app_signals.append_log.connect(log_window.append_log, Qt.QueuedConnection)
        app_signals.api_call_status.connect(log_window.append_api_status, Qt.QueuedConnection)
        app_signals.update_timer_status.connect(log_window.update_timer_status, Qt.QueuedConnection)
        logger.info("Connected logger signals to LogWindow")
    else:
        logger.info("No LogWindow provided; using StreamHandler for logging")

    return logger


def stop_logging():
    global LOGGING_ACTIVE
    LOGGING_ACTIVE = False
    log_queue.put(None)
    if log_thread.is_alive():
        log_thread.join(timeout=2.0)

def load_icon(path, context=""):
    if not path:
        logger.error(f"No icon path provided for {context}")
        app_signals.append_log.emit(f"[Init] No icon path provided for {context}")
        return QIcon()
    if path in ICON_CACHE and Path(path).exists():
        return QIcon(path)
    if not Path(path).exists():
        logger.error(f"Icon file does not exist for {context}: {path}")
        app_signals.append_log.emit(f"[Init] Icon file does not exist for {context}: {path}")
        return QIcon()
    icon = QIcon(path)
    if icon.isNull():
        logger.error(f"Failed to load icon for {context}: {path}")
        app_signals.append_log.emit(f"[Init] Failed to load icon for {context}: {path}")
    return icon
    
CACHE_DAYS = 7

def get_system_info():
    try:
        uname = platform.uname()
    except Exception:
        uname = None
        print("uname not found")

    info = {}
    
    
    # === CPU Info ===
    try:
        info["cpu"] = {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else None,
            "min_frequency_mhz": psutil.cpu_freq().min if psutil.cpu_freq() else None,
            "current_frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "per_core_usage_percent": psutil.cpu_percent(interval=1, percpu=True)
        }
    except Exception as e:
        info["cpu"] = {"error": str(e)}



    # === OS and System Info ===
    info["system"] = {
        "os": uname.system if uname else platform.system(),
        "node_name": uname.node if uname else socket.gethostname(),
        "release": uname.release if uname else "",
        "version": uname.version if uname else "",
        "machine": uname.machine if uname else platform.machine(),
        "processor": uname.processor if uname else platform.processor(),
        "architecture": platform.architecture()[0],
    }
    try:
        system = platform.system().lower()
        if system == "darwin":  # macOS
            print('darwin')
            serial = subprocess.check_output(["system_profiler", "SPHardwareDataType"], text=True)
            info["system"]["hardware_serial"] = next((line.split(":")[1].strip()
                                                    for line in serial.splitlines()
                                                    if "Serial Number" in line), None)
        elif system == "windows":
            serial = subprocess.check_output(["wmic", "bios", "get", "serialnumber"], text=True)
            lines = [line.strip() for line in serial.split("\n") if line.strip()]
            if len(lines) >= 2:
                # First line is usually "SerialNumber", second is actual value
                info["system"]["hardware_serial"] = lines[1]
            else:
                info["system"]["hardware_serial"] = 'None'
            
    except Exception:
        info["system"]["hardware_serial"] = 'None'
        
        
    # === System Identifiers ===
    try:
        if platform.system().lower() == "windows":
            info["identifiers"] = {
                "hostname": socket.gethostname(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "mac_address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                        for elements in range(0, 2 * 6, 8)][::-1]),
                "uuid": str(uuid.uuid1())
            }
        elif platform.system().lower() == "darwin":
            # safer way to get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # connect to Google DNS (no data sent)
            ip_address = s.getsockname()[0]
            s.close()

            info["identifiers"] = {
                "hostname": socket.gethostname(),
                "ip_address": ip_address,
                "mac_address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                        for elements in range(0, 2 * 6, 8)][::-1]),
                "uuid": str(uuid.uuid1())
            }
    except Exception as e:
        info["identifiers"] = {"error": str(e)}



    # === Additional macOS/Windows Specific Info ===
    try:
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        network_info = []
        for interface_name, addrs in net_if_addrs.items():
            iface = {"name": interface_name, "mac": None, "ipv4": [], "ipv6": [], "is_up": False}
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    iface["ipv4"].append({
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    })
                elif addr.family == socket.AF_INET6:
                    iface["ipv6"].append({
                        "address": addr.address.split('%')[0],
                        "netmask": addr.netmask
                    })
                elif getattr(psutil, "AF_LINK", None) and addr.family == psutil.AF_LINK:
                    iface["mac"] = addr.address
            iface["is_up"] = net_if_stats.get(interface_name, None) and net_if_stats[interface_name].isup
            network_info.append(iface)
        info["network"] = network_info
        data = {}
        data["ip_address"] = info.get("identifiers", {}).get("ip_address", "")
        data["mac_address"] = info.get("identifiers", {}).get("mac_address", "")
        
        mac_address = info.get("identifiers", {}).get("mac_address", "")
        if mac_address:
            encoded_mac = hashlib.md5(mac_address.encode()).hexdigest()
        else:
            encoded_mac = ""

        data["encoded_mac"] = encoded_mac
        
        data["details"] = info
        global USER_SYSTEM_INFO
        USER_SYSTEM_INFO = data
        print(f"USER_SYSTEM_INFO ======== {USER_SYSTEM_INFO}")
    except Exception as e:
        info["network"] = {"error": str(e)}


def get_default_cache():
    """Return a fresh cache dictionary with created_at set once."""
    return {
        "token": "",
        "user": "",
        "user_id": "",
        "user_info": {},
        "info_resp": {},
        "user_data": {},
        "data": "",
        "downloaded_files": {},
        "uploaded_files": [],
        "created_at": int(time.time())  # only when initialized
    }

def initialize_cache():
    """Create a new cache file safely."""
    cache = get_default_cache()
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except OSError as e:
        print(f"[WARN] Could not initialize cache file: {e}")
    return cache

def load_cache():
    """Load cache safely. If missing/corrupted, reinitialize."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            # Ensure required keys exist (avoid KeyError later)
            for key, default_value in get_default_cache().items():
                if key not in cache:
                    cache[key] = default_value
            return cache
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] Cache load failed ({e}), recreating...")
            return initialize_cache()
    else:
        return initialize_cache()

def save_cache(cache, significant_change=True):
    """Save cache safely without crashing app."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except OSError as e:
        print(f"[WARN] Could not save cache file: {e}")

def get_cache_age(cache):
    """Get cache age in seconds."""
    created_at = cache.get("created_at", int(time.time()))
    return int(time.time()) - created_at


def parse_custom_url():
    try:
        args = sys.argv[1:]
        logger.debug(f"Parsing custom URL from arguments: {args}")
        app_signals.append_log.emit(f"[Init] Parsing custom URL from arguments: {args}")
        if not args:
            logger.info("No custom URL provided")
            app_signals.append_log.emit("[Init] No custom URL provided")
            return ""
        url = args[0]
        parsed_url = urlparse(url)
        if parsed_url.scheme != "myapp":
            logger.warning(f"Invalid scheme in URL: {url}")
            app_signals.append_log.emit(f"[Init] Invalid scheme in URL: {url}")
            return ""
        query_params = parse_qs(parsed_url.query)
        key = query_params.get("key", [""])[0]
        logger.info(f"Parsed key: {key[:8]}..." if key else "No key found")
        app_signals.append_log.emit(f"[Init] Parsed key: {key[:8]}..." if key else "[Init] No key found")
        return key
    except Exception as e:
        logger.error(f"Error parsing custom URL: {e}")
        app_signals.append_log.emit(f"[Init] Failed to parse custom URL: {str(e)}")
        return ""

def validate_user(access_key, status_bar=None):
    """
    Validates a user's token using the API endpoint with access_key.

    Args:
        access_key (str): The access key (defaults to a hardcoded value if not provided).
        status_bar (QStatusBar, optional): Status bar to update with validation messages.

    Returns:
        dict: Contains 'status' (bool), 'message' (str), 'user' (str), 'token' (str), or full API response on success.
    """
    try:
        if not access_key:
            access_key = "e0d6aa4baffc84333faa65356d78e439"
            logger.info("No access_key provided, using default key")
            app_signals.append_log.emit("[API Scan] No access_key provided, using default key")
        
        machine_id = USER_SYSTEM_INFO.get("encoded_mac", "")
        cache = load_cache()
        validation_url = USER_VALIDATE_URL
        logger.debug(f"Validating user with access_key: {access_key[:8]}... at {validation_url}")
        app_signals.append_log.emit(f"[API Scan] Validating user with access_key: {access_key[:8]}...")
        
        resp = HTTP_SESSION.get(
            validation_url,
            params={"key": access_key, "machine_id": machine_id},
            # headers={"Authorization": f"Bearer {cache.get('token', '')}"},
            verify=False,  # Replace with verify="/path/to/server-ca.pem" in production
            timeout=30
        )
        print(f"Request URL: {resp.url}")
        app_signals.api_call_status.emit(
            validation_url,
            f"Status: {resp.status_code}, Response: {resp.text}",
            resp.status_code
        )
        app_signals.append_log.emit(f"[API Scan] User validation API response: {resp.status_code}")
        
        if status_bar:
            status_bar.showMessage(f"User validation API response: {resp.status_code}")
        
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") == 403:
            return result
        
        if not result.get("uuid"):
            raise ValueError(f"Validation failed: {result.get('message', 'No uuid in response')}")
        
        logger.info("User validation successful")
        app_signals.append_log.emit("[API Scan] User validation successful")
        return result  # Return full API response as per original function
    
    except Exception as e:
        logger.error(f"User validation error: {e}")
        app_signals.append_log.emit(f"[API Scan] Failed: User validation error - {str(e)}")
        if status_bar:
            status_bar.showMessage(f"User validation failed: {str(e)}")
        return {"status": False, "message": str(e), "user": "", "token": ""}

def create_folders_from_response(response):
    try:
        cache = load_cache()
        projects = cache.get("user_data", {}).get("projects", [])
        project_name = response.get("project_name", response.get("name", "unknown")).replace(" ", "_")
        client_name = response.get("client_name", "").replace(" ", "_")
        project_path = BASE_TARGET_DIR / client_name / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created project folder: {project_path}")
        app_signals.append_log.emit(f"[Folder] Created project folder: {project_path}")
        projects.append(response)
        cache["user_data"] = {"projects": projects}
        save_cache(cache)
    except Exception as e:
        logger.error(f"Failed to create folders: {e}")
        app_signals.append_log.emit(f"[Folder] Failed to create folders: {str(e)}")

def start_timer_api(file_path, token):
    try:
        response = HTTP_SESSION.post(
            f"{BASE_DOMAIN}/api/ir_production/timer/start",
            json={"file_path": file_path},
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=30
        )
        app_signals.api_call_status.emit(
            f"{BASE_DOMAIN}/api/ir_production/timer/start",
            "Success" if response.status_code == 200 else f"Failed: {response.status_code}",
            response.status_code
        )
        app_signals.append_log.emit(f"[API Scan] Timer start API response: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to start timer: {e}")
        app_signals.append_log.emit(f"[API Scan] Failed to start timer: {str(e)}")
        return None

def end_timer_api(file_path, timer_response, token):
    try:
        response = HTTP_SESSION.post(
            f"{BASE_DOMAIN}/api/ir_production/timer/end",
            json={"file_path": file_path, "timer_response": timer_response},
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=30
        )
        app_signals.api_call_status.emit(
            f"{BASE_DOMAIN}/api/ir_production/timer/end",
            "Success" if response.status_code == 200 else f"Failed: {response.status_code}",
            response.status_code
        )
        app_signals.append_log.emit(f"[API Scan] Timer end API response: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to end timer: {e}")
        app_signals.append_log.emit(f"[API Scan] Failed to end timer: {str(e)}")
        return None

# def connect_to_nas():
#     if not NAS_AVAILABLE:
#         raise Exception("NAS functionality disabled")
#     start = time.perf_counter()
#     try:
#         transport = paramiko.Transport((NAS_IP, 22))
#         transport.connect(username=NAS_USERNAME, password=NAS_PASSWORD)
#         sftp = paramiko.SFTPClient.from_transport(transport)
#         print(f"Connection time: {(time.perf_counter() - start)*1000:.1f}ms")
#         return (transport, sftp)
#     except (paramiko.AuthenticationException, paramiko.SSHException, Exception) as e:
#         print(f"Connection failed after {(time.perf_counter() - start)*1000:.1f}ms: {str(e)}")
#         raise Exception(f"NAS connection failed: {str(e)}")

def check_nas_write_permission(sftp, nas_path):
    """Verify and set write permission for NAS directory and file."""
    try:
        nas_parent = str(Path(nas_path).parent)
        logger.debug(f"Checking NAS directory permissions: {nas_parent}")
        app_signals.append_log.emit(f"[Transfer] Checking NAS directory permissions: {nas_parent}")
        try:
            stat = sftp.stat(nas_parent)
            mode = stat.st_mode & 0o777
            logger.debug(f"Directory {nas_parent} permissions: {oct(mode)}")
            app_signals.append_log.emit(f"[Transfer] Directory {nas_parent} permissions: {oct(mode)}")
            if mode != 0o770:
                sftp.chmod(nas_parent, 0o770)
                logger.info(f"Set permissions to 770 for {nas_parent}")
                app_signals.append_log.emit(f"[Transfer] Set permissions to 770 for {nas_parent}")
        except FileNotFoundError:
            sftp.makedirs(nas_parent, mode=0o770)
            logger.info(f"Created directory {nas_parent} with permissions 770")
            app_signals.append_log.emit(f"[Transfer] Created directory {nas_parent} with permissions 770")
        
        # Test write access
        temp_file = f"{nas_parent}/.test_write_{int(time.time())}.tmp"
        sftp.open(temp_file, 'w').close()
        sftp.remove(temp_file)
        
        # Handle existing file
        try:
            stat = sftp.stat(nas_path)
            mode = stat.st_mode & 0o777
            logger.debug(f"File {nas_path} exists with permissions: {oct(mode)}")
            app_signals.append_log.emit(f"[Transfer] File {nas_path} exists with permissions: {oct(mode)}")
            try:
                sftp.chmod(nas_path, 0o660)
                logger.info(f"Set permissions to 660 for existing file {nas_path}")
                app_signals.append_log.emit(f"[Transfer] Set permissions to 660 for existing file {nas_path}")
            except Exception:
                sftp.remove(nas_path)
                logger.info(f"Removed existing file {nas_path} due to permission issue")
                app_signals.append_log.emit(f"[Transfer] Removed existing file {nas_path} due to permission issue")
        except FileNotFoundError:
            pass  # File doesn't exist, which is fine
        
        logger.info(f"Write permission confirmed for {nas_parent}")
        app_signals.append_log.emit(f"[Transfer] Write permission confirmed for {nas_parent}")
        return True
    except Exception as e:
        logger.error(f"Write permission check failed for {nas_path}: {e}")
        app_signals.append_log.emit(f"[Transfer] Write permission check failed for {nas_path}: {e}")
        return False

MAX_RETRIES = 10
RETRY_BACKOFF = 2  # seconds
TIMEOUT = 1000  # seconds


def call_api(api_url, payload, local_file_path=None):
    logger.info("+++++++++++++++++++++++++++++++ Posting operator upload ++++++++++++++++++++++++++++++")
    attempt = 0
    while attempt < MAX_RETRIES:
        files = None
        try:
            if local_file_path:
                file_name = os.path.basename(local_file_path)
                if not os.path.exists(local_file_path):
                    logger.error(f"File not found: {local_file_path}")
                    return {"error": "File not found"}
                mime_type, _ = mimetypes.guess_type(local_file_path)
                mime_type = mime_type or 'application/octet-stream'
                files = {
                    'creative_files': (file_name, open(local_file_path, 'rb'), mime_type)
                }
                logger.debug(f"File Name: {file_name}, MIME Type: {mime_type}, File Size: {os.path.getsize(local_file_path)} bytes")
            logger.debug(f"Payload being sent: {payload}")
            logger.debug(f"Files being sent: {'Yes' if files else 'No'}")
            with httpx.Client(timeout=TIMEOUT, verify=False) as client:
                response = client.post(api_url, files=files, data=payload)
            logger.debug(f"Response Status Code: {response.status_code}")
            logger.debug(f"Response Text: {response.text[:500]}...")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as req_err:
            logger.warning(f"[Attempt {attempt+1}] Request error: {req_err}")
            attempt += 1
            if attempt < MAX_RETRIES:
                sleep_time = RETRY_BACKOFF ** attempt
                logger.debug(f"Retrying after {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            else:
                return {"error": "Request failed", "details": str(req_err)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": "Unexpected error", "details": str(e)}
        finally:
            if files:
                for _, file_obj, _ in files.values():
                    file_obj.close()

def call_api_qc_qa(api_url, payload, local_file_path=None):
    logger.info("_____________________________ Posting Qc Qa Replace _______________________")
    attempt = 0
    while attempt < MAX_RETRIES:
        files = None
        try:
            if local_file_path:
                file_name = os.path.basename(local_file_path)
                if not os.path.exists(local_file_path):
                    logger.error(f"File not found: {local_file_path}")
                    return {"error": "File not found"}
                mime_type, _ = mimetypes.guess_type(local_file_path)
                mime_type = mime_type or 'application/octet-stream'
                files = {
                    'files[]': (file_name, open(local_file_path, 'rb'), mime_type)
                }
                logger.debug(f"File Name: {file_name}, MIME Type: {mime_type}, File Size: {os.path.getsize(local_file_path)} bytes")
            logger.debug(f"Payload being sent: {payload}")
            logger.debug(f"Files being sent: {'Yes' if files else 'No'}")
            with httpx.Client(timeout=TIMEOUT, verify=False) as client:
                response = client.post(api_url, files=files, data=payload)
            logger.debug(f"Response Status Code: {response.status_code}")
            logger.debug(f"Response Text: {response.text[:500]}...")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as req_err:
            logger.warning(f"[Attempt {attempt+1}] Request error: {req_err}")
            attempt += 1
            if attempt < MAX_RETRIES:
                sleep_time = RETRY_BACKOFF ** attempt
                logger.debug(f"Retrying after {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            else:
                return {"error": "Request failed", "details": str(req_err)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": "Unexpected error", "details": str(e)}
        finally:
            if files:
                for _, file_obj, _ in files.values():
                    file_obj.close()


def post_metadata_to_api_upload(spec_id, user_id):
    logger.info("============================ Posting Metadata to Upload API ==============================")
    
    try:
        payload = {
            'business': 'image_retouching',
            'operator_uid': user_id,
            'spec_id': spec_id
        }
        response = requests.post(API_URL_UPLOAD, json=payload, verify=False)
        logger.info(response)
        if response.status_code == 200:
            logger.info(f"Successfully posted metadata to API (Upload).")
        else:
            logger.error(f"Failed to post metadata to API (Upload): {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Error posting metadata to API (Upload): {e}")


def post_api(api_url,payload):
    logger.info("-------------------------------------------------- Posting update -------------------------------")
    try:        
        response = requests.post(api_url, data=payload, verify=False)
        logger.info(response)
        if response.status_code == 200:
            logger.info(f"Successfully posted metadata to API (Upload).")
        else:
            logger.error(f"Failed to post metadata to API (Upload): {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Error posting metadata to API (Upload): {e}")


def update_download_upload_metadata(task_id, request_status, retries=3, timeout=10.0, base_retry_delay=2):
   
    payload = {"id": task_id, "request_status": request_status}
    headers = {"Content-Type": "application/json"}

    for attempt in range(1, retries + 1):
        try:
            response = httpx.post(
                API_URL_UPLOAD_DOWNLOAD_UPDATE,
                data=json.dumps(payload),
                headers=headers,
                verify=False,
                timeout=timeout,
            )
            print(f"================================================ Status Code {task_id} : {request_status}")
            if response.status_code == 200:
                return response.json()

            logger.error(
                f"Attempt {attempt}: Failed with status {response.status_code}"
            )

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Attempt {attempt}: Request error -> {e}")
        except Exception as e:
            logger.error(f"Attempt {attempt}: Unexpected error -> {e}")

        if attempt < retries:
            delay = base_retry_delay * (2 ** (attempt - 1))  # exponential backoff
            time.sleep(delay)

    return {"error": "Failed after retries"}

# ===================== image convertion logic =====================

def sanitize_filename(filename):
    return re.sub(r'[^\w\-.]', '_', filename)

def get_file_hash(file_path):
    """Calculate SHA256 hash of a file for integrity check."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}")
        return None

def check_nas_write_permission(sftp, nas_path):
    """Verify and set write permission for NAS directory and file."""
    try:
        nas_parent = str(Path(nas_path).parent)
        logger.debug(f"Checking NAS directory permissions: {nas_parent}")
        app_signals.append_log.emit(f"[Transfer] Checking NAS directory permissions: {nas_parent}")
        try:
            stat = sftp.stat(nas_parent)
            mode = stat.st_mode & 0o777
            logger.debug(f"Directory {nas_parent} permissions: {oct(mode)}")
            app_signals.append_log.emit(f"[Transfer] Directory {nas_parent} permissions: {oct(mode)}")
            if mode != 0o777:
                sftp.chmod(nas_parent, 0o777)
                logger.info(f"Set permissions to 777 for {nas_parent}")
                app_signals.append_log.emit(f"[Transfer] Set permissions to 777 for {nas_parent}")
        except FileNotFoundError:
            sftp.makedirs(nas_parent, mode=0o777)
            logger.info(f"Created directory {nas_parent} with permissions 777")
            app_signals.append_log.emit(f"[Transfer] Created directory {nas_parent} with permissions 777")
        
        # Test write access
        temp_file = f"{nas_parent}/.test_write_{int(time.time())}.tmp"
        sftp.open(temp_file, 'w').close()
        sftp.remove(temp_file)
        
        # Handle existing file
        try:
            stat = sftp.stat(nas_path)
            mode = stat.st_mode & 0o777
            logger.debug(f"File {nas_path} exists with permissions: {oct(mode)}")
            app_signals.append_log.emit(f"[Transfer] File {nas_path} exists with permissions: {oct(mode)}")
            try:
                sftp.chmod(nas_path, 0o777)
                logger.info(f"Set permissions to 777 for existing file {nas_path}")
                app_signals.append_log.emit(f"[Transfer] Set permissions to 777 for existing file {nas_path}")
            except Exception:
                sftp.remove(nas_path)
                logger.info(f"Removed existing file {nas_path} due to permission issue")
                app_signals.append_log.emit(f"[Transfer] Removed existing file {nas_path} due to permission issue")
        except FileNotFoundError:
            pass  # File doesn't exist, which is fine
        
        logger.info(f"Write permission confirmed for {nas_parent}")
        app_signals.append_log.emit(f"[Transfer] Write permission confirmed for {nas_parent}")
        return True
    except Exception as e:
        logger.error(f"Write permission check failed for {nas_path}: {e}")
        app_signals.append_log.emit(f"[Transfer-lang=python] Write permission check failed for {nas_path}: {e}")
        return False







def process_image_in_memory(image_data, ext, full_file_path):
   
    stream = io.BytesIO(image_data)
    pil_image = None
    ext = ext.lower()
    logger.info(f"Starting processing of {full_file_path} with extension {ext}")

    if ext in ['jpg', 'jpeg', 'png']:
        pil_image = Image.open(stream)
        logger.info(f"Opened {ext} file, mode: {pil_image.mode}")
    elif ext == 'gif':
        pil_image = Image.open(stream)
        pil_image = next(ImageSequence.Iterator(pil_image))
        logger.info("Processed GIF first frame, mode: {pil_image.mode}")
    elif ext in ['tif', 'tiff']:
        with tifffile.TiffFile(stream) as tif:
            page = tif.pages[0]
            arr = page.asarray()
            photometric = getattr(page.photometric, 'name', 'unknown').lower()
            if photometric in ['rgb', 'ycbcr']:
                arr = arr[:, :, :3] if arr.ndim == 3 and arr.shape[2] >= 3 else arr
                pil_image = Image.fromarray(arr.astype(np.uint8), mode='RGB')
            elif photometric == 'cmyk':
                pil_image = Image.fromarray(arr.astype(np.uint8), mode='CMYK').convert("RGB")
            elif photometric == 'minisblack' or arr.ndim == 2:
                arr = np.stack((arr,) * 3, axis=-1)
                pil_image = Image.fromarray(arr.astype(np.uint8), mode='RGB')
            else:
                logger.warning(f"Unsupported TIFF photometric: {photometric}")
                return None
            logger.info(f"Processed TIFF, mode: {pil_image.mode}, photometric: {photometric}")
    elif ext in ['psd', 'psb']:
            psd = PSDImage.open(stream)
            if psd is None or not psd.has_preview():
                logger.error(f"PSD preview not available for {full_file_path}")
                return None

            pil_image = psd.composite()
            logger.info(f"PSD composite result, mode: {pil_image.mode}, size: {pil_image.size}")

            # Apply ICC profile if available
            try:
                icc = psd.image_resources.get("icc_profile")
                if icc:
                    pil_image.info["icc_profile"] = icc.data
                    logger.info(f"Applied ICC profile to PSD: {full_file_path}")
            except Exception as e:
                logger.warning(f"Error extracting ICC profile: {e}")
    elif ext in ['cr2', 'nef', 'arw', 'dng', 'raf', 'pef', 'srw']:
        with rawpy.imread(stream) as raw:
            rgb = raw.postprocess()
            pil_image = Image.fromarray(rgb)
        logger.info(f"Processed raw image, mode: {pil_image.mode}")
    else:
        pil_image = Image.open(stream)
        logger.info(f"Opened {ext} file, mode: {pil_image.mode}")

    if pil_image is None:
        logger.error(f"Failed to create PIL image for {full_file_path}")
        return None

    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
        logger.info("Final conversion to RGB, size: {pil_image.size}")

    jpeg_buffer = io.BytesIO()
    logger.info(f"Attempting to save JPEG to buffer, initial position: {jpeg_buffer.tell()}")
    pil_image.save(jpeg_buffer, format="JPEG", quality=80, icc_profile=pil_image.info.get('icc_profile'))
    logger.info(f"JPEG save completed, buffer position: {jpeg_buffer.tell()}")
    jpeg_buffer.seek(0)
    buffer_size = jpeg_buffer.getbuffer().nbytes
    logger.info(f"Buffer byte count: {buffer_size}")
    if buffer_size == 0:
        logger.error(f"Empty JPEG buffer for {full_file_path} after save")
        return None
    jpeg_buffer.seek(0)
    return jpeg_buffer
 






def process_single_file(full_file_path):
    """Convert a single file to JPEG and move original to backup."""
    path = Path(full_file_path)
    if not path.is_file():
        logger.error(f"File does not exist: {full_file_path}")
        return None, None

    base_directory = path.parent
    original_file_name = path.name
    file_name = sanitize_filename(original_file_name)
    ext = path.suffix.lower().lstrip(".")

    if ext not in SUPPORTED_EXTENSIONS:
        logger.debug(f"Unsupported file extension: {ext}")
        error_dir = base_directory / "invalid_files"
        error_dir.mkdir(exist_ok=True)
        error_path = error_dir / original_file_name
        path.rename(error_path)
        logger.warning(f"File moved to invalid folder: {error_path}")
        return None, None

    output_file_name = ".".join(file_name.split(".")[:-1]) + ".jpg"
    local_output_path = base_directory / output_file_name

    if local_output_path.exists():
        logger.info(f"Skipping: Output JPEG exists: {local_output_path}")
        return str(local_output_path), str(path)

    if ext in ["jpg", "jpeg"]:
        sanitized_path = base_directory / file_name
        if path != sanitized_path:
            path.rename(sanitized_path)
        logger.debug(f"JPEG moved/renamed to {sanitized_path}")
        return str(sanitized_path), str(sanitized_path)

    with open(path, "rb") as f:
        image_data = f.read()

    start_time = time.time()
    jpeg_buffer = process_image_in_memory(image_data, ext, str(path))
    elapsed = time.time() - start_time
    logger.info(f"Conversion time: {elapsed:.2f} seconds")

    if jpeg_buffer is None:
        error_dir = base_directory / "invalid_files"
        error_dir.mkdir(exist_ok=True)
        error_path = error_dir / original_file_name
        path.rename(error_path)
        logger.warning(f"File moved to invalid folder: {error_path}")
        return None, None

    if local_output_path.exists():
        local_output_path.unlink()

    with open(local_output_path, "wb") as f:
        f.write(jpeg_buffer.getvalue())
    os.chmod(local_output_path, 0o777)
    logger.debug(f"Converted JPEG written to {local_output_path}")

    backup_path = base_directory / original_file_name
    path.rename(backup_path)
    logger.debug(f"Original file renamed to {backup_path}")

    return str(local_output_path), str(full_file_path)


# ===================== image covertion logic =====================


def show_alert_notification(title, message):
    
    system = platform.system()
    if system == "Windows":
        import ctypes
        # fallback: simple message box
        ctypes.windll.user32.MessageBoxW(0, message, title, 0)
    elif system == "Darwin":
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
    else:
        print(f"{title}: {message}")



class FileConversionWorker(QObject):
    finished = Signal(str, str, str)
    error = Signal(str, str)
    progress = Signal(str, int)

    def __init__(self, src_path, dest_dir):
        super().__init__()
        self.src_path = src_path
        self.dest_dir = dest_dir

    def run(self):
        if not PIL_AVAILABLE:
            self.error.emit("Pillow not installed, image conversion disabled", Path(self.src_path).name)
            return
        try:
            img = Image.open(self.src_path)
            filename = os.path.splitext(Path(self.src_path).name)[0]
            jpg_path = str(Path(self.dest_dir) / f"{filename}.jpg")
            psd_path = str(Path(self.dest_dir) / f"{filename}.psd")

            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(jpg_path, 'JPEG', quality=95)
            self.progress.emit(jpg_path, 50)
            img.save(psd_path, 'PSD')
            self.progress.emit(psd_path, 75)

            cache = load_cache()
            with open(jpg_path, 'rb') as f:
                resp = HTTP_SESSION.post(
                    f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
                    files={'file': f},
                    headers={"Authorization": f"Bearer {cache.get('token', '')}"},
                    verify=False,
                    timeout=30
                )
                app_signals.api_call_status.emit(
                    f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
                    "Success" if resp.status_code == 200 else f"Failed: {resp.status_code}",
                    resp.status_code
                )
                resp.raise_for_status()

            self.progress.emit(jpg_path, 100)
            self.finished.emit(jpg_path, psd_path, Path(self.src_path).name)
        except Exception as e:
            logger.error(f"File conversion error for {self.src_path}: {e}")
            self.error.emit(str(e), Path(self.src_path).name)


class FileWatcherWorker(QObject):
    show_dialog = Signal(str, str, str)  # Signal for title, message, dialog_type
    status_update = Signal(str)
    log_update = Signal(str)
    progress_update = Signal(str, str, int)
    request_reauth = Signal()
    task_list_update = Signal(list)
    cleanup_signal = Signal()
    user_in_other_system = Signal(str)

    _instance = None
    _instance_thread = None
    _is_running = False
    _busy = False

    @classmethod
    def get_instance(cls, parent=None):
        """Return the singleton instance of FileWatcherWorker."""
        if cls._instance is None:
            logger.debug(f"Creating new FileWatcherWorker instance with parent={parent}")
            cls._instance = cls(parent=parent)
            cls._instance_thread = QThread.currentThread()
            logger.info(f"FileWatcherWorker instance created in thread {cls._instance_thread}")
        elif parent is not None and cls._instance.parent() != parent:
            logger.warning(f"Existing instance has different parent; ignoring new parent={parent}")
            cls._instance.log_update.emit(f"[FileWatcher] Warning: Existing instance has different parent; ignoring new parent={parent}")
        return cls._instance

    def __init__(self, parent=None):
        if self._instance is not None and self._instance is not self:
            logger.warning(f"FileWatcherWorker already initialized in thread {self._instance_thread}, use get_instance()")
            self.log_update.emit(f"[FileWatcher] Warning: Already initialized in thread {self._instance_thread}, use get_instance()")
            raise RuntimeError("FileWatcherWorker is a singleton; use FileWatcherWorker.get_instance()")
        super().__init__(parent)
        FileWatcherWorker._instance = self
        FileWatcherWorker._instance_thread = QThread.currentThread()
        self.processed_tasks = set()
        self.running = True
        self._lock = Lock()  # Initialize the lock
        self.last_api_hit_time = None
        self.next_api_hit_time = None
        self.api_poll_interval = 3000
        self.config = {
            "photoshop_path": os.getenv("PHOTOSHOP_PATH", ""),
            "max_processed_tasks": 1000,
            "task_retention_hours": 24,
            "supported_image_extensions": (
                ".jpg", ".jpeg", ".png", ".gif", ".tiff", ".tif", ".bmp", ".webp",
                ".psd", ".psb", ".cr2", ".nef", ".arw", ".dng", ".raf", ".pef", ".srw"
            ),
        }
        logger.info("FileWatcherWorker initialized")
        self.log_update.emit("[FileWatcher] Initialized")
        self.log_update.emit(f"[FileWatcher] Application started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # Single-shot to prevent overlapping ticks
        self.timer.timeout.connect(self.run)
        self.cleanup_signal.connect(self.cleanup)
        if not self.timer.isActive():
            self.timer.start(self.api_poll_interval)
            logger.debug(f"FileWatcherWorker timer started with {self.api_poll_interval/1000}-second interval")
            self.log_update.emit(f"[FileWatcher] Timer started with {self.api_poll_interval/1000}-second interval")
        else:
            logger.debug("FileWatcherWorker timer already active")
            self.log_update.emit("[FileWatcher] Timer already active")


    def _prepare_download_path(self, item):
        """Prepare the local destination path for download using file_path."""
        file_path = item.get("file_path", "").lstrip("/")
        if not file_path:
            show_alert_notification("ERROR (MD2)", "Please check Nas Connection.")
            # QMessageBox.warning(None, "ERROR (MD2)", "Please check Nas Connection.")
            raise ValueError("Empty file_path in item")
        dest_path = BASE_TARGET_DIR / file_path
        logger.debug(f"Preparing download path: file_path={file_path}, dest_path={dest_path}")
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True, mode=0o777)
            os.chmod(dest_path.parent, 0o777)
            logger.debug(f"Created directory {dest_path.parent} with permissions 777")
            self.log_update.emit(f"[Transfer] Created directory {dest_path.parent} with permissions 777")
        except Exception as e:
            logger.error(f"Failed to create directory {dest_path.parent}: {str(e)}")
            self.log_update.emit(f"[Transfer] Failed to create directory {dest_path.parent}: {str(e)}")
            show_alert_notification("ERROR (MD2)", "Please check Nas Connection.")
            # QMessageBox.warning(None, "ERROR (MD2)", "Please check Nas Connection.")
            raise
        resolved_dest_path = str(dest_path.resolve())
        logger.debug(f"Prepared local path: {resolved_dest_path}")
        self.log_update.emit(f"[Transfer] Prepared local path: {resolved_dest_path}")
        return resolved_dest_path

    # def _download_from_nas(self, src_path, dest_path, item):
    #     task_id = item.get("id", '')
    #     spec_id = str(item.get("spec_id"))
    #     metadata_key = "downloaded_files_with_metadata"
    #     cache = load_cache()
    #     cache.setdefault(metadata_key, {})

    #     try:
    #         # --- FAST TRANSPORT ---
    #         conn_start = time.time()
    #         transport = paramiko.Transport((NAS_IP, NAS_PORT))

    #         # Use fastest cipher
    #         transport.get_security_options().ciphers = (
    #             'aes128-ctr', 'aes192-ctr', 'aes256-ctr'
    #         )

    #         transport.connect(username=NAS_USERNAME, password=NAS_PASSWORD)

    #         # Create high-performance SFTP client
    #         sftp = paramiko.SFTPClient.from_transport(transport)

    #         # BOOST 1: Increase Max Packet Size (default = 32 KB)
    #         sftp.MAX_PACKET_SIZE = 327680  # 320 KB

    #         # BOOST 2: Increase Max Request Size
    #         sftp.MAX_REQUEST_SIZE = 327680  # 320 KB

    #         conn_end = time.time()
    #         connection_time = (conn_end - conn_start) * 1000

    #         # Resolve NAS path
    #         nas_path = item.get("file_path", src_path)

    #         # File size
    #         file_size = sftp.stat(nas_path).st_size
    #         file_size_mb = file_size / (1024 * 1024)

    #         # --- FAST DOWNLOAD ---
    #         start_time = time.time()

    #         # Use getfo (streaming) for faster large file downloads
    #         with open(dest_path, 'wb') as out_f:
    #             sftp.getfo(nas_path, out_f)

    #         end_time = time.time()

    #         duration = end_time - start_time
    #         speed = file_size_mb / duration if duration > 0 else 0

    #         print(f"Connection: {connection_time:.1f}ms")
    #         print(f"Downloaded {file_size_mb:.2f} MB in {duration:.2f}s ({speed:.2f} MB/s)")

    #         sftp.close()
    #         transport.close()

    #     except Exception as e:
    #         print(f"❌ Download failed: {e}")
    #         update_download_upload_metadata(task_id, "failed")
    #         cache[metadata_key][spec_id]["api_response"]["request_status"] = "Download Failed"
    #         save_cache(cache, significant_change=True)
    #         raise


    def _download_from_nas(self, src_path, dest_path, item):
        task_id = item.get("id", '')
        spec_id = str(item.get("spec_id"))
        metadata_key = "downloaded_files_with_metadata"
        cache = load_cache()
        cache.setdefault(metadata_key, {})
        
        transport = None  # Initialize transport by Mohan

        try:
            # --- FAST SSH CONNECTION ---
            conn_start = time.time()
            transport = paramiko.Transport((NAS_IP, NAS_PORT))
            
            # Apply packet/window size tuning directly to the transport changes by Mohan
            transport.default_window_size = 2147483647     # 128MB window
            transport.default_max_packet_size = 65536  # 64MB packet
            transport.packetizer.REKEY_BYTES = pow(2, 40)
            transport.packetizer.REKEY_PACKETS = pow(2, 40)

            transport.get_security_options().ciphers = (
                'aes128-ctr', 'aes192-ctr', 'aes256-ctr'
            )

            transport.connect(username=NAS_USERNAME, password=NAS_PASSWORD)
            conn_end = time.time()

            print(f"Connection time: {(conn_end - conn_start) * 1000:.1f} ms")

            # Resolve NAS path
            nas_path = item.get("file_path", src_path)

            # --- SUPER FAST SCP DOWNLOAD --- buffer size increased by Mohan
            start_time = time.time()

            with SCPClient(transport, socket_timeout=30, buff_size=8388608) as scp:
                scp.get(nas_path, local_path=dest_path)

            end_time = time.time()

            # calculate file size + speed
            size_mb = Path(dest_path).stat().st_size / (1024 * 1024)
            duration = end_time - start_time
            speed = size_mb / duration if duration > 0 else 0

            print(f"📥 SCP Downloaded {size_mb:.2f} MB in {duration:.2f}s ({speed:.2f} MB/s)")

            #transport.close() commented by Mohan

        except Exception as e:
            print(f"❌ Download failed: {e}")
            cache[metadata_key][spec_id]["api_response"]["request_status"] = "Download Failed"
            save_cache(cache, significant_change=True)
            update_download_upload_metadata(task_id, "failed")
            raise
            
        # Transport close by Mohan
        finally:
            if transport:
                # Ensure the transport is closed after transfer is complete
                transport.close()



    
    # def _upload_to_nas(self, src_path, dest_path, item):
    #     task_id = item.get("id", '')
    #     spec_id = str(item.get("spec_id"))
    #     metadata_key = "uploaded_files_with_metadata"
    #     cache = load_cache()
    #     cache.setdefault(metadata_key, {})

    #     try:
    #         src_path = Path(src_path)
    #         if not src_path.exists():
    #             cache[metadata_key][spec_id]["api_response"]["request_status"] = "Upload Failed"
    #             save_cache(cache, significant_change=True)
    #             update_download_upload_metadata(task_id, "failed")
    #             show_alert_notification("Error (U1)", "Upload failed try again.")
    #             raise FileNotFoundError(f"Source file does not exist: {src_path}")

    #         # --- FAST PARAMIKO CONNECTION ---
    #         conn_start = time.time()
    #         transport = paramiko.Transport((NAS_IP, NAS_PORT))   # IMPORTANT: Use SFTPGo port

    #         transport.get_security_options().ciphers = (
    #             'aes128-ctr', 'aes192-ctr', 'aes256-ctr'
    #         )

    #         transport.connect(username=NAS_USERNAME, password=NAS_PASSWORD)
    #         sftp = paramiko.SFTPClient.from_transport(transport)

    #         sftp.MAX_PACKET_SIZE = 327680
    #         sftp.MAX_REQUEST_SIZE = 327680

    #         conn_end = time.time()
    #         print(f"Connection time: {(conn_end - conn_start) * 1000:.1f} ms")

    #         # Destination path
    #         dest_path = item.get("file_path", dest_path)

    #         # Ensure directory exists
    #         dest_dir = os.path.dirname(dest_path)
    #         try:
    #             sftp.stat(dest_dir)
    #         except FileNotFoundError:
    #             parts = dest_dir.strip("/").split("/")
    #             current = ""
    #             for part in parts:
    #                 current += f"/{part}"
    #                 try:
    #                     sftp.stat(current)
    #                 except FileNotFoundError:
    #                     sftp.mkdir(current, mode=0o777)

    #         file_size = src_path.stat().st_size
    #         file_size_mb = file_size / (1024 * 1024)

    #         # --- SUPER-FAST CHUNKED UPLOAD ---
    #         print("Uploading...")

    #         start_time = time.time()

    #         with open(src_path, "rb") as local_file:
    #             with sftp.open(dest_path, 'wb') as remote_file:
    #                 while True:
    #                     chunk = local_file.read(1024 * 1024)  # 1 MB chunks
    #                     if not chunk:
    #                         break
    #                     remote_file.write(chunk)

    #                 remote_file.flush()

    #         sftp.chmod(dest_path, 0o777)

    #         end_time = time.time()

    #         duration = end_time - start_time
    #         speed = file_size_mb / duration

    #         print(f"⚡ Uploaded {file_size_mb:.2f} MB in {duration:.2f}s ({speed:.2f} MB/s)")

    #         sftp.close()
    #         transport.close()

    #     except Exception as e:
    #         print(f"❌ Upload failed: {e}")
    #         cache[metadata_key][spec_id]["api_response"]["request_status"] = "Upload Failed"
    #         save_cache(cache, significant_change=True)
    #         show_alert_notification("Error (U3)", "Upload failed try again.")
    #         raise


#     def _upload_to_nas(self, src_path, dest_path, item):
#         task_id = item.get("id", '')
#         spec_id = str(item.get("spec_id"))
#         metadata_key = "uploaded_files_with_metadata"
#         cache = load_cache()
#         cache.setdefault(metadata_key, {})
#         transport = None  # initialize transport by Mohan
#         try:
#             src_path = Path(src_path)
#             if not src_path.exists():
#                 cache[metadata_key][spec_id]["api_response"]["request_status"] = "Upload Failed"
#                 save_cache(cache, significant_change=True)
#                 update_download_upload_metadata(task_id, "failed")
#                 show_alert_notification("Error (U1)", "Upload failed try again.")
#                 raise FileNotFoundError(f"Source file does not exist: {src_path}")

#             # --- FAST SSH (same as before) ---
#             conn_start = time.time()
#             transport = paramiko.Transport((NAS_IP, NAS_PORT))
#             transport.set_keepalive(15) # Send KeepAlive every 15 seconds by Mohan
#             # Apply packet/window size tuning directly to the transport by Mohan
#             transport.default_window_size = 3554432     # 32MB window by Mohan
#             transport.default_max_packet_size = 1048576   # 1MB packet by Mohan
#             transport.get_security_options().ciphers = (
# 'aes128-ctr', 'aes192-ctr', 'aes256-ctr'
#             )
#             transport.connect(username=NAS_USERNAME, password=NAS_PASSWORD)
#             conn_end = time.time()

#             print(f"Connection time: {(conn_end - conn_start) * 1000:.1f} ms")

#             # Destination: use item’s file_path if provided
#             dest_path = item.get("file_path", dest_path)
            
#             # --- OPTIMIZATION BY MOHAN: ONE-SHOT DIRECTORY CREATION (FIXES THE 70S BOTTLENECK) ---
#             # Replaced the slow recursive check with a single fast SSH command:
#             dest_dir = os.path.dirname(dest_path)
#             chan = transport.open_session()
#             chan.exec_command(f'mkdir -p "{dest_dir}"') 
#             chan.close()
#             # --------------------------------------------------------------------------

#             # --- SUPER FAST SCP UPLOAD ---
#             start = time.time()
#             fast_scp_upload(transport, str(src_path), dest_path)
#             end = time.time()

#             duration = end - start
#             size_mb = src_path.stat().st_size / (1024 * 1024)
#             speed = size_mb / duration

#             print(f"⚡ Uploaded {size_mb:.2f} MB in {duration:.2f}s ({speed:.2f} MB/s)")
            
#             # --- FIX: SET PERMISSIONS AFTER UPLOAD ---
#             try:
#                 sftp = paramiko.SFTPClient.from_transport(transport)
#                 sftp.chmod(dest_path, 0o777)
#                 sftp.close()
#                 logger.info(f"Set permissions to 777 for uploaded file {dest_path}")
#             except Exception as perm_e:
#                 logger.warning(f"Failed to set file permissions (chmod) after SCP: {perm_e}")
#                 # Continue if chmod fails, as the file is already uploaded by SCP

#             # transport.close() commented by Mohan

#         except Exception as e:
#         # Check if the error is due to Channel Closed or connection loss
#             if "Channel closed" in str(e) or "Timeout" in str(e) or "EOF" in str(e):
#                 logger.error(f"Upload failed due to connection issue (Channel closed/Timeout/EOF): {e}")
#                 show_alert_notification("Upload Error", "Connection lost during upload. This may be fixed by the KeepAlive setting. Please retry.")
                
#             if 'transport' in locals() and transport and transport.is_active():       # transport close by Mohan
#                 transport.close()
                
#             print(f"❌ Upload failed: {e}")
#             cache[metadata_key][spec_id]["api_response"]["request_status"] = "Upload Failed"
#             save_cache(cache, significant_change=True)
#             show_alert_notification("Error (U3)", "Upload failed try again.")
#             raise


    def _upload_to_nas(self, src_path, dest_path, item):
        task_id = item.get("id", '')
        spec_id = str(item.get("spec_id"))
        metadata_key = "uploaded_files_with_metadata"
        cache = load_cache()
        cache.setdefault(metadata_key, {})
        
        src_path = Path(src_path)
        if not src_path.exists():
            cache[metadata_key][spec_id]["api_response"]["request_status"] = "Upload Failed"
            save_cache(cache, significant_change=True)
            update_download_upload_metadata(task_id, "failed")
            show_alert_notification("Error (U1)", "Upload failed try again.")
            raise FileNotFoundError(f"Source file does not exist: {src_path}")

        dest_path = item.get("file_path", dest_path)
        dest_dir = os.path.dirname(dest_path)
        
        sock = None
        session = None
        sftp = None
        try:
            # ---------- CONNECTION ----------
            start_conn = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((NAS_IP, NAS_PORT))
            
            session = Session()
            session.handshake(sock)
            
            session.userauth_password(NAS_USERNAME, NAS_PASSWORD)
            
            if not session.userauth_authenticated():
                raise Exception("SSH authentication failed")
            
            end_conn = time.time()
            print(f"Connection established in {(end_conn - start_conn) * 1000:.1f} ms")

            # ---------- SFTP INIT ----------
            sftp = session.sftp_init()

            # ---------- NO DIRECTORY CREATION ----------
            print(f"Directory creation skipped (as requested).")
            print(f"Assuming destination directory already exists: {dest_dir}")
            print(f"If upload fails with 'No such file or directory', create the folder manually on the NAS.\n")

            # ---------- UPLOAD WITH LIVELY PROGRESS ----------
            upload_start = time.time()
            
            flags = LIBSSH2_FXF_CREAT | LIBSSH2_FXF_WRITE | LIBSSH2_FXF_TRUNC
            chunk_size = 4 * 1024 * 1024  # 4 MB chunks
            
            file_size = src_path.stat().st_size
            total_mb = file_size / (1024 * 1024)
            
            # Throttling setup
            bytes_per_second = None
            if THROTTLE_MBPS is not None:
                bytes_per_second = THROTTLE_MBPS * 1024 * 1024 / 8
            
            transferred = 0
            last_print_time = time.time()
            chunk_start_time = time.time()
            
            print(f"Uploading: {src_path.name} ({total_mb:.2f} MB)")
            print(f"Destination: {dest_path}")
            print("Progress: 0.0% | Speed: 0.00 MB/s | Transferred: 0.00 / {:.2f} MB".format(total_mb))
            
            with open(src_path, "rb") as local_file, \
                sftp.open(dest_path, flags, 0o644) as remote_file:
                
                while True:
                    data = local_file.read(chunk_size)
                    if not data:
                        break
                    
                    remote_file.write(data)
                    transferred += len(data)
                    
                    # Throttling
                    if bytes_per_second:
                        chunk_end_time = time.time()
                        elapsed = chunk_end_time - chunk_start_time
                        expected = len(data) / bytes_per_second
                        if elapsed < expected:
                            time.sleep(expected - elapsed)
                        chunk_start_time = time.time()
                    
                    # Real-time progress
                    current_time = time.time()
                    if current_time - last_print_time >= PRINT_INTERVAL:
                        elapsed_total = current_time - upload_start
                        transferred_mb = transferred / (1024 * 1024)
                        percentage = (transferred / file_size) * 100 if file_size > 0 else 100
                        speed = transferred_mb / elapsed_total if elapsed_total > 0 else 0
                        
                        print(f"Progress: {percentage:6.1f}% | Speed: {speed:6.2f} MB/s | "
                            f"Transferred: {transferred_mb:8.2f} / {total_mb:.2f} MB", end="\r")
                        
                        last_print_time = current_time
            
            # Final results
            upload_end = time.time()
            duration = upload_end - upload_start
            final_mb = file_size / (1024 * 1024)
            final_speed = final_mb / duration if duration > 0 else 0
            
            print(f"\n\nUpload completed: {final_mb:.2f} MB in {duration:.2f}s ({final_speed:.2f} MB/s)")
            
            if MIN_REQUIRED_MBPS:
                actual_mbps = final_speed * 8
                if actual_mbps < MIN_REQUIRED_MBPS:
                    print(f"WARNING: Upload speed {actual_mbps:.1f} Mbps is below required {MIN_REQUIRED_MBPS} Mbps!")
                else:
                    print(f"Speed {actual_mbps:.1f} Mbps meets minimum requirement ✓")

        except Exception as e:
            print("\nUpload failed!")
            error_details = str(e)
            
            if sftp:
                sftp_err = sftp.last_error()
                if sftp_err != 0:
                    error_details += f" | SFTP error code: {sftp_err}"
                    if sftp_err == 2:
                        error_details += " (No such file or directory – destination folder missing)"
                    elif sftp_err == 3:
                        error_details += " (Permission denied)"
            
            if session:
                sess_err = session.last_errno()
                if sess_err != 0:
                    error_details += f" | Session error code: {sess_err}"
            
            print(f"Error: {error_details or 'Unknown error'}")
            print("Tip: If 'No such file or directory', create the full destination folder manually on the NAS once.")
            traceback.print_exc()
            
            cache[metadata_key][spec_id]["api_response"]["request_status"] = "Upload Failed"
            save_cache(cache, significant_change=True)
            show_alert_notification("Error (U3)", "Upload failed – check if destination folder exists.")
            raise
        finally:
            if session:
                session.disconnect()
            if sock:
                sock.close()


        
    def _update_cache_and_signals(self, action_type, src_path, dest_path, item, task_id, is_nas, file_type="original"):
        cache = load_cache()
        cache.setdefault("downloaded_files", {})
        cache.setdefault("downloaded_files_with_metadata", {})
        cache.setdefault("uploaded_files", [])
        cache.setdefault("uploaded_files_with_metadata", {})
        cache.setdefault("timer_responses", {})
        local_path = src_path if action_type.lower() == "upload" else dest_path
        try:
            if action_type.lower() == "download":
                cache["downloaded_files"][task_id] = local_path
                cache["downloaded_files_with_metadata"][task_id] = {"local_path": local_path, "api_response": item}
                # timer_response = start_timer_api(src_path, cache.get('token', ''))
                # if timer_response:
                #     cache["timer_responses"][local_path] = timer_response
                app_signals.update_file_list.emit(local_path, f"{action_type} Completed", action_type.lower(), 100, is_nas)
                logger.debug(f"Emitted update_file_list signal: dest_path={local_path}, status={action_type} Completed, is_nas={is_nas}")
                self.log_update.emit(f"[Signal] Emitted update_file_list: dest_path={local_path}, status={action_type} Completed, is_nas={is_nas}")
            elif action_type.lower() in ("upload", "replace"):
                cache["uploaded_files"].append(dest_path)
                cache["uploaded_files_with_metadata"][task_id] = {"local_path": local_path, "api_response": item}
                # timer_response = cache.get("timer_responses", {}).get(local_path)
                # if timer_response:
                #     end_timer_api(src_path, timer_response, cache.get('token', ''))
                # app_signals.update_file_list.emit(local_path, f"{action_type} Completed ({file_type.capitalize()})", action_type.lower(), 100, is_nas)
                app_signals.update_file_list.emit(local_path, f"{action_type} Completed", action_type.lower(), 100, is_nas)
                logger.debug(f"Emitted update_file_list signal: dest_path={local_path}, status={action_type} Completed, is_nas={is_nas}")
                self.log_update.emit(f"[Signal] Emitted update_file_list: dest_path={local_path}, status={action_type} Completed, is_nas={is_nas}")
            save_cache(cache)
            app_signals.append_log.emit(f"[Transfer] {action_type} completed: {src_path} to {dest_path}")
        except Exception as e:
            logger.error(f"Failed to update cache and signals for {action_type} ({file_type}, Task {task_id}): {str(e)}")
            self.log_update.emit(f"[Transfer] Failed to update cache and signals for {action_type} ({file_type}, Task {task_id}): {str(e)}")
            raise

    def open_with_photoshop(self, file_path, key_val):
        """Open a file in Adobe Photoshop across platforms and bring it to the front if minimized."""
        try:
            import platform
            import subprocess
            import time
            import logging
            import os
            from pathlib import Path

            logger = logging.getLogger(__name__)
            system = platform.system()
            file_path = str(Path(file_path).resolve())
            try:
                key_val_int = int(key_val)
            except (TypeError, ValueError):
                key_val_int = 0  # fallback if conversion fails

            if key_val_int >= 1:
                self.log_update.emit("[Photoshop] Skipping photoshop file open")
                logger.info("Skipping photoshop file open")
                return True
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")

            logger.debug(f"System: {system}, File path: {file_path}")
            photoshop_path = None

            if system == "Windows":
                try:
                    import win32gui
                    import win32con
                    import win32com.client
                    import win32api
                    import win32process
                    import ctypes
                except ImportError as e:
                    raise ImportError("Required pywin32 modules not found. Run: pip install pywin32") from e

                # Check environment variable for Photoshop path
                photoshop_path = os.getenv("PHOTOSHOP_PATH")
                if photoshop_path and Path(photoshop_path).exists():
                    logger.debug(f"Using Photoshop path from PHOTOSHOP_PATH: {photoshop_path}")
                else:
                    search_dirs = [
                        Path("C:/Program Files/Adobe"),
                        Path("C:/Program Files (x86)/Adobe")
                    ]
                    for base_dir in search_dirs:
                        if not base_dir.exists():
                            logger.debug(f"Search directory does not exist: {base_dir}")
                            continue
                        photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                        if photoshop_exes:
                            photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                            photoshop_path = str(photoshop_exes[0])
                            logger.debug(f"Found Photoshop at: {photoshop_path}")
                            break
                    if not photoshop_path:
                        raise FileNotFoundError("Adobe Photoshop executable not found in Program Files")

                # Verify Photoshop executable accessibility
                if not os.access(photoshop_path, os.X_OK):
                    raise PermissionError(f"Photoshop executable is not accessible: {photoshop_path}")

                # Try opening via COM first
                try:
                    logger.debug("Attempting to open via COM")
                    ps_app = win32com.client.Dispatch("Photoshop.Application")
                    ps_app.Visible = True
                    ps_app.Open(file_path)

                    # Wait for Photoshop window and bring to front
                    def wait_for_window(title_contains="Adobe Photoshop", max_wait=10, interval=0.5):
                        start_time = time.time()
                        while time.time() - start_time < max_wait:
                            windows = []
                            def enum_handler(hwnd, lst):
                                if win32gui.IsWindowVisible(hwnd):
                                    title = win32gui.GetWindowText(hwnd)
                                    if title_contains.lower() in title.lower():
                                        lst.append(hwnd)
                            win32gui.EnumWindows(enum_handler, windows)
                            if windows:
                                logger.debug(f"Found Photoshop window: {win32gui.GetWindowText(windows[0])}")
                                return windows[0]
                            time.sleep(interval)
                        logger.warning("Photoshop window not found")
                        return None

                    hwnd = wait_for_window()
                    if hwnd:
                        try:
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                            logger.debug(f"Activated Photoshop window: {win32gui.GetWindowText(hwnd)}")
                        except Exception as e:
                            logger.debug(f"Window activation failed: {e}")
                    else:
                        logger.warning("Failed to activate Photoshop window: not found")
                    logger.info(f"Opened {Path(file_path).name} via COM")
                    self.log_update.emit(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                    return  # Exit after successful COM opening
                except Exception as e:
                    logger.debug(f"COM attempt failed: {e}. Falling back to subprocess.")

                # Try subprocess only if COM fails
                cmd = [photoshop_path, file_path]
                logger.debug(f"Executing subprocess command: {cmd}")
                try:
                    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
                    # Wait for Photoshop window and bring to front
                    def wait_for_window(title_contains="Adobe Photoshop", max_wait=10, interval=0.5):
                        start_time = time.time()
                        while time.time() - start_time < max_wait:
                            windows = []
                            def enum_handler(hwnd, lst):
                                if win32gui.IsWindowVisible(hwnd):
                                    title = win32gui.GetWindowText(hwnd)
                                    if title_contains.lower() in title.lower():
                                        lst.append(hwnd)
                            win32gui.EnumWindows(enum_handler, windows)
                            if windows:
                                logger.debug(f"Found Photoshop window: {win32gui.GetWindowText(windows[0])}")
                                return windows[0]
                            time.sleep(interval)
                        logger.warning("Photoshop window not found")
                        return None

                    hwnd = wait_for_window()
                    if hwnd:
                        try:
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                            logger.debug(f"Activated Photoshop window: {win32gui.GetWindowText(hwnd)}")
                        except Exception as e:
                            logger.debug(f"Subprocess window activation failed: {e}")
                    else:
                        logger.warning("Failed to activate Photoshop window: not found")
                    logger.info(f"Opened {Path(file_path).name} via subprocess")
                    self.log_update.emit(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                except subprocess.CalledProcessError as e:
                    logger.debug(f"Subprocess failed: {e}, stderr: {e.stderr}")
                    raise RuntimeError(f"Failed to open file: {e}")

            elif system == "Darwin":
                # Check environment variable for custom Photoshop path
                custom_path = os.getenv("PHOTOSHOP_PATH")
                if custom_path and Path(custom_path).exists():
                    photoshop_path = str(Path(custom_path).resolve())
                    logger.debug(f"Found Photoshop via environment variable: {photoshop_path}")

                # Try Spotlight search with broader query
                if not photoshop_path:
                    try:
                        result = subprocess.run(
                            ["mdfind", "kMDItemKind == 'Application' && (kMDItemFSName == 'Adobe Photoshop*.app' || kMDItemFSName == 'Photoshop*.app' || kMDItemFSName == 'Adobe*Photoshop*.app')"],
                            capture_output=True, text=True, check=True
                        )
                        if result.stdout.strip():
                            photoshop_path = result.stdout.strip().split("\n")[0]
                            logger.debug(f"Found Photoshop via mdfind: {photoshop_path}")
                    except subprocess.CalledProcessError as e:
                        logger.debug(f"mdfind failed with error: {e}, stderr: {e.stderr}")

                # Expanded search locations with deeper glob patterns
                if not photoshop_path:
                    search_locations = [
                        Path("/Applications"),
                        Path("~/Applications").expanduser(),
                        Path("/Applications/Adobe Creative Cloud"),
                        Path("~/Applications/Adobe Creative Cloud").expanduser(),
                        Path("/Applications/Adobe"),
                        Path("~/Applications/Adobe").expanduser(),
                        Path("/Applications/Adobe Photoshop*"),
                        Path("~/Applications/Adobe Photoshop*").expanduser(),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop*"),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop*").expanduser(),
                    ]
                    for search_dir in search_locations:
                        if not search_dir.exists():
                            logger.debug(f"Search directory does not exist: {search_dir}")
                            continue
                        logger.debug(f"Searching for Photoshop in: {search_dir}")
                        photoshop_apps = (
                            list(search_dir.glob("Adobe*Photoshop*.app")) +
                            list(search_dir.glob("Photoshop*.app")) +
                            list(search_dir.glob("*/Adobe*Photoshop*.app"))
                        )
                        if photoshop_apps:
                            logger.debug(f"Found potential Photoshop apps: {[str(app) for app in photoshop_apps]}")
                            photoshop_apps.sort(key=lambda x: x.name, reverse=True)
                            photoshop_path = str(photoshop_apps[0])
                            logger.debug(f"Selected Photoshop via glob in {search_dir}: {photoshop_path}")
                            break

                # Check versioned paths, including exact match for 2025
                if not photoshop_path:
                    versioned_paths = [
                        Path("/Applications/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("~/Applications/Adobe Photoshop 2025/Adobe Photoshop 2025.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2025/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2024/Adobe Photoshop 2024.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2024/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2023/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop 2025.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop 2024.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop 2023.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop.app").expanduser(),
                    ]
                    for path in versioned_paths:
                        if path.exists():
                            photoshop_path = str(path)
                            logger.debug(f"Found Photoshop in versioned path: {photoshop_path}")
                            break

                # Fallback to user selection via file dialog (if GUI is available)
                if not photoshop_path and hasattr(self, 'window'):
                    from PySide6.QtWidgets import QFileDialog
                    logger.debug("Prompting user to select Photoshop application")
                    photoshop_path, _ = QFileDialog.getOpenFileName(
                        self.window(), "Locate Adobe Photoshop", "/Applications", "Applications (*.app)"
                    )
                    if photoshop_path:
                        logger.debug(f"User-selected Photoshop path: {photoshop_path}")
                    else:
                        logger.debug("User cancelled Photoshop path selection")

                if not photoshop_path:
                    error_msg = (
                        "Adobe Photoshop application not found in /Applications, ~/Applications, "
                        "Adobe Creative Cloud, or Adobe directories. Please set PHOTOSHOP_PATH environment variable."
                    )
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

                # Open file and bring Photoshop to front
                for attempt in range(3):
                    try:
                        subprocess.run(["open", "-a", photoshop_path, file_path], check=True)
                        app_name = Path(photoshop_path).name.replace('.app', '')
                        applescript = f'''
                            tell application "{app_name}"
                                activate
                            end tell
                            delay 0.5
                            tell application "System Events"
                                set frontmost of process "{app_name}" to true
                            end tell
                        '''
                        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, check=True)
                        logger.debug(f"AppleScript output: {result.stdout}")
                        logger.info(f"Opened {Path(file_path).name} via open -a at {photoshop_path}")
                        self.log_update.emit(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                        break
                    except subprocess.CalledProcessError as e:
                        if attempt < 2:
                            logger.debug(f"Attempt {attempt+1} failed: {e}. Retrying...")
                            time.sleep(2)
                        else:
                            raise RuntimeError(f"Failed to open file after 3 attempts: {e}")

            elif system == "Linux":
                try:
                    subprocess.run(["wine", "--version"], capture_output=True, check=True)
                    wine_dirs = [
                        Path.home() / ".wine/drive_c/Program Files/Adobe",
                        Path.home() / ".wine/drive_c/Program Files (x86)/Adobe"
                    ]
                    for base_dir in wine_dirs:
                        if not base_dir.exists():
                            continue
                        photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                        if photoshop_exes:
                            photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                            photoshop_path = str(photoshop_exes[0])
                            break
                    if not photoshop_path:
                        raise FileNotFoundError("Photoshop.exe not found in Wine directories")

                    for attempt in range(3):
                        try:
                            subprocess.run(["wine", photoshop_path, file_path], check=True)
                            time.sleep(1)  # Initial wait for process to start
                            # Try multiple window title patterns
                            title_patterns = ["Adobe Photoshop", "Photoshop"]
                            for pattern in title_patterns:
                                try:
                                    result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, check=True)
                                    for line in result.stdout.splitlines():
                                        if pattern in line:
                                            window_id = line.split()[0]
                                            subprocess.run(["wmctrl", "-i", "-a", window_id], check=True)
                                            logger.debug(f"Activated window with ID {window_id}: {line}")
                                            break
                                except Exception as e:
                                    logger.debug(f"Failed to activate window with pattern {pattern}: {e}")
                            logger.info(f"Opened {Path(file_path).name} via wine")
                            self.log_update.emit(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                            break
                        except subprocess.CalledProcessError as e:
                            if attempt < 2:
                                logger.debug(f"Attempt {attempt+1} failed: {e}. Retrying...")
                                time.sleep(2)
                            else:
                                raise RuntimeError(f"Failed to open file after 3 attempts: {e}")
                except subprocess.CalledProcessError:
                    raise FileNotFoundError("Wine is not installed or not functioning")

            else:
                error_message = f"Unsupported platform for Photoshop: {system}"
                logger.warning(error_message)
                self.log_update.emit(f"[Photoshop] {error_message}")
                raise ValueError(error_message)

        except Exception as e:
            error_message = f"Failed to open {Path(file_path).name} in Photoshop: {str(e)}"
            logger.error(error_message)
            self.log_update.emit(f"[Photoshop] {error_message}")
            raise

    def perform_file_transfer(self, src_path, dest_path, action_type, item, is_nas_src, is_nas_dest):
        """Perform file transfer (download/upload/replace) and update cache metadata reliably."""
        task_id = str(item.get('id'))
        spec_id = str(item.get("spec_id"))
        print("===================================")
        print(item.get("file_path"))
        print("===================================")
        
        if not task_id:
            raise ValueError("Task ID is missing or invalid in item dictionary")
        
        global IS_APP_ACTIVE_UPLOAD_DOWNLOAD
        IS_APP_ACTIVE_UPLOAD_DOWNLOAD = True

        status_prefix = "Download" if action_type.lower() == "download" else "Upload"
        metadata_key = "downloaded_files_with_metadata" if action_type.lower() == "download" else "uploaded_files_with_metadata"

        try:
            logger.debug(f"Starting file transfer for task {task_id}, action_type: {action_type}")

            # Load cache once
            cache = load_cache()
            cache.setdefault(metadata_key, {})

            # Initialize task entry if missing
            if task_id not in cache[metadata_key]:
                cache[metadata_key][spec_id] = {
                    "local_path": dest_path if action_type.lower() == "download" else src_path,
                    "api_response": {
                        "id": task_id,
                        "file_path": item.get("file_path"),
                        "file_name": item.get("file_name", Path(src_path).name),
                        "request_type": action_type.lower(),
                        "job_id": item.get("job_id"),
                        "job_name": item.get("job_name"),
                        "project_id": item.get("project_id"),
                        "project_name": item.get("project_name"),
                        "client_name": item.get("client_name"),
                        "spec_id": item.get("spec_id"),
                        "user_id": item.get("user_id"),
                        "user_type": item.get("user_type"),
                        "creative_id": item.get("creative_id"),
                        "inventory_id": item.get("inventory_id"),
                        "nas_path": item.get("nas_path"),
                        "thumbnail": item.get("thumbnail"),
                        "created_on": item.get("created_on"),
                        "updated_date": item.get("updated_date"),
                        "request_status": f"{status_prefix} Started"
                    },
                    
                }

            # Save initial "In Progress" state
            save_cache(cache, significant_change=True)
            update_download_upload_metadata(task_id, "In Progress")
            logger.info(f"[{status_prefix} In Progress] Task {task_id}")
            self.progress_update.emit(f"{action_type} (Task {task_id}): {Path(src_path).name}", dest_path, 10)

            # ------------------------------
            # Handle Download
            # ------------------------------
            if action_type.lower() == "download":
                dest_path = self._prepare_download_path(item)

                if is_nas_src:
                    self._download_from_nas(src_path, dest_path, item)
                else:
                    self._download_from_http(src_path, dest_path)

                if not os.path.exists(dest_path):
                    cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} Failed"
                    save_cache(cache, significant_change=True)
                    raise FileNotFoundError(f"{status_prefix} file not found: {dest_path}")

                cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} Completed"
                cache[metadata_key][spec_id]["local_path"] = dest_path
                save_cache(cache, significant_change=True)
                update_download_upload_metadata(task_id, "completed")

                # Optional: Open with Photoshop
                try:
                    key_val = item.get("key_val")
                    self.open_with_photoshop(dest_path, key_val)
                except Exception as e:
                    cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} Failed Photoshop"
                    save_cache(cache, significant_change=True)
                    logger.warning(f"Failed to open {dest_path} with Photoshop: {str(e)}")
                    self.log_update.emit(f"[Transfer] Warning: Failed to open {dest_path} with Photoshop: {str(e)}")

                # Optional: Conversion to JPG
                # cache[metadata_key][task_id]["api_response"]["request_status"] = f"{status_prefix} Conversion Started"
                # save_cache(cache, significant_change=True)
                # local_jpg, _ = process_single_file(dest_path)
                # if local_jpg:
                #     cache[metadata_key][task_id]["api_response"]["request_status"] = f"{status_prefix} Conversion Completed"
                #     save_cache(cache, significant_change=True)
                #     app_signals.update_file_list.emit(local_jpg, "Conversion Completed", "download", 100, False)
                # else:
                #     cache[metadata_key][task_id]["api_response"]["request_status"] = f"{status_prefix} Conversion Failed"
                #     save_cache(cache, significant_change=True)
                #     self.log_update.emit(f"[Transfer] Failed: JPG conversion failed for {dest_path}")

                # self.progress_update.emit(f"{action_type} Completed (Task {task_id}): {Path(src_path).name}", dest_path, 100)
                # app_signals.update_file_list.emit(dest_path, f"{action_type} Completed", "download", 100, is_nas_src)

            # ------------------------------
            # Handle Upload / Replace
            # ------------------------------
            elif action_type.lower() in ("upload", "replace"):
                if not os.path.exists(src_path):
                    cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} Source Missing"
                    save_cache(cache, significant_change=True)
                    raise FileNotFoundError(f"Source file does not exist: {src_path}")

                # Check if file is accessible
                try:
                    with open(src_path, 'rb') as f:
                        f.read(1)
                except (PermissionError, IOError):
                    cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} File In Use"
                    save_cache(cache, significant_change=True)
                    raise RuntimeError(f"File {src_path} is currently in use by another application.")

                # Upload to NAS or HTTP
                if is_nas_dest:
                    self._upload_to_nas(src_path, dest_path, item)
                    cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} Completed"
                else:
                    cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} HTTP Not Implemented"
                    save_cache(cache, significant_change=True)
                    raise NotImplementedError("HTTP upload not implemented")

                save_cache(cache, significant_change=True)
                update_download_upload_metadata(task_id, "completed")
                self.progress_update.emit(f"{action_type} Completed (Task {task_id}): {Path(src_path).name}", dest_path, 100)

                try:
                    request_data = {
                        'job_id': item.get('job_id'),
                        'project_id': item.get("project_id"),
                        'file_name': item.get("user_id"),
                        'user_id': item.get("user_id"),
                        'user_type': item.get("user_type"),
                        'spec_id': item.get("spec_id"),
                        'creative_id': item.get("creative_id"),
                        'inventory_id': item.get("inventory_id"),
                        'nas_path': "softwaremedia/IR_uat/" + dest_path,
                    }

                    response = requests.post(
                        DRUPAL_DB_ENTRY_API,
                        data=request_data,
                        headers={},
                        verify=False
                    )

                    cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} completed"
                    save_cache(cache, significant_change=True)
                    update_download_upload_metadata(task_id, "Conversion Started")
                    logging.info(f"DRUPAL_DB_ENTRY_API data success: {response.text}")

                except Exception as e:
                    cache[metadata_key][spec_id]["status"] = f"{status_prefix} API Call Failed"
                    save_cache(cache, significant_change=True)
                    logging.error(f"DRUPAL_DB_ENTRY_API call error: {str(e)}")
                
            else:
                raise ValueError(f"Invalid action_type: {action_type}")
            IS_APP_ACTIVE_UPLOAD_DOWNLOAD = False

        except Exception as e:
            # Update cache with failure
            cache.setdefault(metadata_key, {})
            if spec_id not in cache[metadata_key]:
                cache[metadata_key][spec_id] = {"local_path": dest_path, "status": f"{status_prefix} Failed"}
            else:
                cache[metadata_key][spec_id]["api_response"]["request_status"] = f"{status_prefix} Failed"

            save_cache(cache, significant_change=True)
            update_download_upload_metadata(task_id, "failed")
            IS_APP_ACTIVE_UPLOAD_DOWNLOAD = False
            logger.error(f"{status_prefix} error (Task {task_id}): {str(e)}")
            self.log_update.emit(f"[Transfer] Failed (Task {task_id}): {str(e)}")
            self.progress_update.emit(f"{action_type} Failed (Task {task_id}): {Path(src_path).name}", dest_path, 0)
            raise



    def run(self):
        with self._lock:
            if self._busy:
                logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] File watcher already running, skipping this cycle, instance: {id(self)}")
                self.log_update.emit("[FileWatcher] Skipped: Already running")
                return
            current_time = datetime.now(timezone.utc)
            if hasattr(self, 'next_api_hit_time') and self.next_api_hit_time and current_time < self.next_api_hit_time:
                logger.debug(f"[{current_time.isoformat()}] API call skipped: Too soon since last call, instance: {id(self)}")
                self.log_update.emit("[FileWatcher] Skipped: Too soon since last API call")
                return
            self._busy = True
            self._is_running = True
        try:
            # Initialize executor and semaphore if not already set
            if not hasattr(self, 'executor'):
                self.executor = ThreadPoolExecutor(max_workers=2)  # Set max_workers to 2 for parallel processing
                logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Initialized ThreadPoolExecutor with max_workers=2, instance: {id(self)}")
                self.log_update.emit("[FileWatcher] Initialized ThreadPoolExecutor with max_workers=2")
            if not hasattr(self, 'sftp_semaphore'):
                self.sftp_semaphore = Semaphore(2)  # Limit concurrent SFTP connections
                logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Initialized SFTP semaphore with limit=2, instance: {id(self)}")
                self.log_update.emit("[FileWatcher] Initialized SFTP semaphore with limit=2")
            if not self.running:
                logger.info(f"[{current_time.isoformat()}] File watcher stopped, instance: {id(self)}")
                self.log_update.emit("[FileWatcher] Stopped: Worker is not running")
                return
            logger.debug(f"[{current_time.isoformat()}] Starting file watcher run, instance: {id(self)}")
            self.log_update.emit("[API Scan] Starting file watcher run")

            if not self.check_connectivity():
                logger.warning(f"[{current_time.isoformat()}] Connectivity check failed, will retry on next run, instance: {id(self)}")
                self.status_update.emit("Connectivity check failed, will retry")
                self.log_update.emit("[API Scan] Connectivity check failed")
                return

            cache = load_cache()
            user_id = cache.get('user_id', '')
            token = cache.get('token', '')
            cache.setdefault('user_type', 'operator')
            save_cache(cache)
            if not user_id or not token:
                logger.error(f"[{current_time.isoformat()}] No user_id or token found in cache, instance: {id(self)}")
                self.status_update.emit("No user_id or token found in cache")
                self.log_update.emit("[API Scan] Failed: No user_id or token found in cache")
                self.request_reauth.emit()
                logger.debug(f"[{current_time.isoformat()}] Timer remains active for retry after re-authentication, instance: {id(self)}")
                self.log_update.emit("[FileWatcher] Timer remains active for retry after re-authentication")
                return

            self.status_update.emit("Checking for file tasks...")
            self.log_update.emit("[API Scan] Starting file task check")
            app_signals.append_log.emit("[API Scan] Initiating file task check")
            self.last_api_hit_time = current_time
            self.next_api_hit_time = self.last_api_hit_time + timedelta(milliseconds=self.api_poll_interval)
            app_signals.update_timer_status.emit(
                f"Last API hit: {self.last_api_hit_time.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
                f"Next API hit: {self.next_api_hit_time.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
                f"Interval: {self.api_poll_interval/1000:.1f}s"
            )
            headers = {"Authorization": f"Bearer {token}"}
            max_retries = 3
            tasks = []
            print(f"USER_SYSTEM_INFO.get(÷,).get(mac)-----{USER_SYSTEM_INFO.get('encoded_mac', '')}")
            # api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}&machine_id={USER_SYSTEM_INFO.get("identifiers", {}).get("encoded_mac", "")}"
            # machine_id = USER_SYSTEM_INFO.get("encoded_mac", "")
            # api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}&machine_id={USER_SYSTEM_INFO.get('encoded_mac', '')}"
            if isinstance(USER_SYSTEM_INFO, dict):
                machine_id = USER_SYSTEM_INFO.get("encoded_mac", "")
            elif isinstance(USER_SYSTEM_INFO, list) and USER_SYSTEM_INFO:
                # if it's a list, use the first element that contains encoded_mac
                first_entry = USER_SYSTEM_INFO[0]
                machine_id = first_entry.get("encoded_mac", "") if isinstance(first_entry, dict) else ""
            else:
                machine_id = ""

            print(f"[DEBUG] USER_SYSTEM_INFO type={type(USER_SYSTEM_INFO)}, machine_id={machine_id}")
            api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}&machine_id={machine_id}"
            # machine_id = USER_SYSTEM_INFO.get("encoded_mac", "") if isinstance(USER_SYSTEM_INFO, dict) else ""
            # api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}&machine_id={machine_id}"

            for attempt in range(max_retries):
                try:
                    logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Hitting API: {api_url}, instance: {id(self)}")
                    app_signals.append_log.emit(f"[API Scan] Hitting API: {api_url}")
                    response = HTTP_SESSION.get(api_url, headers=headers, verify=False, timeout=60)
                    
                    
                    response_data = response.json()

                    
                    
                    logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] API response: Status={response.status_code}, Content={response.text[:500]}..., instance: {id(self)}")
                    app_signals.append_log.emit(f"[API Scan] API response: Status={response.status_code}, Content={response.text[:500]}...")
                    app_signals.api_call_status.emit(api_url, "Success" if response.status_code == 200 else f"Failed: {response.status_code}", response.status_code)

                    if response.status_code == 401:
                        logger.warning(f"[{datetime.now(timezone.utc).isoformat()}] Unauthorized: Token may be invalid, instance: {id(self)}")
                        self.log_update.emit("[API Scan] Unauthorized: Token invalid")
                        self.status_update.emit("Unauthorized: Token invalid")
                        self.request_reauth.emit()
                        logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Timer remains active for retry after re-authentication, instance: {id(self)}")
                        self.log_update.emit("[FileWatcher] Timer remains active for retry after re-authentication")
                        return

                    response.raise_for_status()
                    response_data = response.json()
                    # ✅ Handle both list and dict response formats safely
                    if isinstance(response_data, dict):
                        if response_data.get("status") == 403:
                            self.user_in_other_system.emit("user_already_logged_in")
                            return
                        tasks = response_data.get("data", [])
                    elif isinstance(response_data, list):
                        tasks = response_data  # API directly returns a list of tasks
                    else:
                        logger.error(f"Unexpected API response type: {type(response_data)} - {response_data}")
                        self.log_update.emit(f"[API Scan] Unexpected API response type: {type(response_data)}")
                        tasks = []


                    
                    tasks = response_data if isinstance(response_data, list) else response_data.get('data', [])
                    if not isinstance(tasks, list):
                        logger.error(f"[{datetime.now(timezone.utc).isoformat()}] API returned non-list tasks: {type(tasks)}, data: {tasks}, instance: {id(self)}")
                        self.log_update.emit(f"[API Scan] Failed: API returned non-list tasks: {type(tasks)}")
                        return
                    logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Retrieved {len(tasks)} tasks: {tasks}, instance: {id(self)}")
                    app_signals.append_log.emit(f"[API Scan] Retrieved {len(tasks)} tasks from API")
                    break
                except RequestException as e:
                    logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Attempt {attempt + 1} failed fetching tasks from {api_url}: {e}, instance: {id(self)}")
                    self.log_update.emit(f"[API Scan] Failed to fetch tasks (attempt {attempt + 1}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    logger.warning(f"[{datetime.now(timezone.utc).isoformat()}] Max retries reached for task fetch, will retry on next run, instance: {id(self)}")
                    self.status_update.emit(f"Error fetching tasks after retries: {str(e)}")
                    self.log_update.emit(f"[API Scan] Failed to fetch tasks after retries: {str(e)}")
                    app_signals.append_log.emit(f"[API Scan] Failed: Task fetch error after retries - {str(e)}")
                    return

            unprocessed_tasks = [task for task in tasks if f"{task.get('id', '')}:{task.get('request_type', '').lower()}" not in self.processed_tasks]

            # ✅ FIXED: Properly build download and upload task lists
            download_tasks = []
            upload_tasks = []

            for item in unprocessed_tasks:
                if not isinstance(item, dict):
                    continue

                req_type = item.get('request_type', '').lower()
                task_data = {
                    "task_id": str(item.get('id', '')),
                    "action_type": req_type,
                    "file_name": item.get('file_name', Path(item.get('file_path') or '').name if item.get('file_path') else 'unknown_file'),
                    "file_path": item.get('file_path', ''),
                    "status": "Queued",
                    "thumbnail": item.get('thumbnail', ''),
                    "job_id": item.get('job_id', ''),
                    "job_name": item.get('job_name', ''),
                    "project_id": item.get('project_id', ''),
                    "project_name": item.get('project_name', ''),
                    "created_at": datetime.now().strftime("%d-%b-%Y %I:%M %p")
                }

                if req_type == "download":
                    logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Download task: {item}, instance: {id(self)}")
                    task_data["task_type"] = "download"
                    download_tasks.append(task_data)

                elif req_type in ("upload", "replace"):
                    logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Upload task: {item}, instance: {id(self)}")
                    task_data["task_type"] = "upload"
                    upload_tasks.append(task_data)

            self.task_list_update.emit(download_tasks + upload_tasks)
            self.log_update.emit(f"[API Scan] Task list emitted to GUI: {len(download_tasks)} download tasks, {len(upload_tasks)} upload tasks")

            self._clean_processed_tasks()
            futures = []
            for item in unprocessed_tasks:
                if not isinstance(item, dict):
                    logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Invalid task item type: {type(item)}, item: {item}, instance: {id(self)}")
                    self.log_update.emit(f"[API Scan] Failed: Invalid task item type: {type(item)}")
                    app_signals.update_file_list.emit("", f"Invalid task: {type(item)}", "unknown", 0, False)
                    continue

                task_id = str(item.get('id', ''))
                file_path = item.get('file_path', '')
                if not file_path:
                    logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Invalid task {task_id}: Missing file_path, item: {item}, instance: {id(self)}")
                    self.log_update.emit(f"[API Scan] Failed: Invalid task {task_id} - Missing file_path")
                    app_signals.update_file_list.emit("", f"Invalid task {task_id}: Missing file_path", "unknown", 0, False)
                    continue

                file_name = item.get('file_name', Path(file_path).name)
                action_type = item.get('request_type', '').lower()
                task_key = f"{task_id}:{action_type}"
                is_online = 'http' in file_path.lower()
                local_path = str(BASE_TARGET_DIR / file_path.lstrip("/"))

                    # ✅ Prevent duplicate submissions
                with self._lock:
                    if task_key in self.processed_tasks:
                        logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Skipping duplicate task: {task_key}, instance: {id(self)}")
                        self.log_update.emit(f"[API Scan] Skipped duplicate task: {task_key}")
                        continue
                    self.processed_tasks.add(task_key)  # Mark immediately as in-progress
                    update_download_upload_metadata(task_id, "in progress")

                logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Submitting task: task_key={task_key}, task_id={task_id}, action_type={action_type}, file_path={file_path}, instance: {id(self)}")
                self.log_update.emit(f"[API Scan] Submitting task: task_key={task_key}, task_id={task_id}, action_type={action_type}, file_path={file_path}")

                futures.append(
                    self.executor.submit(
                        self._process_task,
                        task_id, file_name, file_path, action_type, local_path, is_online, item, 3, self.sftp_semaphore
                    )
                )

            # Start a background thread to handle task results
            def handle_task_results(futures):
                completed_tasks = 0
                failed_tasks = 0
                updates = []
                for future in futures:
                    try:
                        result = future.result()  # Wait for each task to complete
                        updates.append(result['update'])
                        if result['success']:
                            completed_tasks += 1
                            with self._lock:
                                self.processed_tasks.add(result['task_key'])
                        else:
                            failed_tasks += 1
                    except Exception as e:
                        logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Task processing error: {str(e)}, instance: {id(self)}")
                        self.log_update.emit(f"[API Scan] Task processing error: {str(e)}")
                        failed_tasks += 1
                if updates:
                    for update in updates:
                        app_signals.update_file_list.emit(*update)
                logger.info(f"[{datetime.now(timezone.utc).isoformat()}] Background task summary: {completed_tasks} completed, {failed_tasks} failed, instance: {id(self)}")
                self.log_update.emit(f"[FileWatcher] Background task summary: {completed_tasks} completed, {failed_tasks} failed")

            # Launch background thread to process results
            Thread(target=handle_task_results, args=(futures,), daemon=True).start()
            self.status_update.emit("File tasks check completed")
            self.log_update.emit(f"[API Scan] File tasks check completed, submitted {len(futures)} tasks")
            app_signals.append_log.emit(f"[API Scan] Completed: Submitted {len(futures)} tasks")

        except Exception as e:
            logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Error in file watcher run: {e}, instance: {id(self)}")
            self.status_update.emit(f"Error processing tasks: {str(e)}")
            self.log_update.emit(f"[API Scan] Failed: Error processing tasks - {str(e)}")
            app_signals.append_log.emit(f"[API Scan] Failed: Task processing error - {str(e)}")
        finally:
            self._busy = False
            self._is_running = False
            logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] File watcher cycle completed, instance: {id(self)}")
            self.log_update.emit("[FileWatcher] Cycle completed, awaiting next timer tick")
            # if self.running:
            #     self.timer.start(self.api_poll_interval)

    def _process_task(self, task_id, file_name, file_path, action_type, local_path, is_online, item, max_download_retries, sftp_semaphore):
        """Process a single task (download/upload) with retry logic and SFTP semaphore."""
        # update_download_upload_metadata(task_id, "in progress")
        task_key = f"{task_id}:{action_type}"
        update = (local_path, f"{action_type} Queued", action_type, 0, not is_online)
        try:
            if action_type == "download":
                self.status_update.emit(f"Downloading {file_name}")
                self.log_update.emit(f"[API Scan] Starting download: {file_path} to {local_path}, task_id: {task_id}")
                app_signals.append_log.emit(f"[API Scan] Initiating download: {file_name}")
                app_signals.update_file_list.emit(local_path, f"{action_type} Queued", action_type, 0, not is_online)
                for attempt in range(max_download_retries):
                    try:
                        if not is_online:
                            with sftp_semaphore:  # Limit concurrent SFTP connections
                                self.show_progress(f"Downloading {file_name}", file_path, local_path, action_type, item, not is_online, False)
                        else:
                            self.show_progress(f"Downloading {file_name}", file_path, local_path, action_type, item, not is_online, False)
                        if os.path.exists(local_path):
                            self.log_update.emit(f"[API Scan] Download successful: {local_path}, task_id: {task_id}")
                            return {
                                'update': (local_path, f"Download Completed", action_type, 100, not is_online),
                                'task_key': task_key,
                                'success': True
                            }
                        else:
                            logger.warning(f"[{datetime.now(timezone.utc).isoformat()}] Download failed for {local_path}; attempt {attempt + 1} of {max_download_retries}, instance: {id(self)}")
                            self.log_update.emit(f"[API Scan] Download failed for {local_path}; attempt {attempt + 1} of {max_download_retries}")
                            update = (local_path, f"Download Failed: File not found", action_type, 0, not is_online)
                            if attempt == max_download_retries - 1:
                                raise FileNotFoundError(f"Downloaded file not found: {local_path}")
                    except Exception as e:
                        logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Download failed for {local_path} (Task {task_id}): {str(e)}, attempt {attempt + 1}, instance: {id(self)}")
                        self.log_update.emit(f"[API Scan] Download failed for {local_path} (Task {task_id}): {str(e)}")
                        update = (local_path, f"Download Failed: {str(e)}", action_type, 0, not is_online)
                        if attempt < max_download_retries - 1:
                            delay = 2 ** attempt
                            logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Retrying download after {delay}s, instance: {id(self)}")
                            self.log_update.emit(f"[API Scan] Retrying download after {delay}s")
                            time.sleep(delay)
                        else:
                            raise
            elif action_type.lower() in ("upload", "replace"):
                self.status_update.emit(f"Uploading {file_name}")
                self.log_update.emit(f"[API Scan] Starting upload: {local_path} to {file_path}, task_id: {task_id}")
                app_signals.append_log.emit(f"[API Scan] Initiating upload: {file_name}")
                app_signals.update_file_list.emit(local_path, f"{action_type} Queued", action_type, 0, not is_online)
                for attempt in range(max_download_retries):
                    try:
                        if not is_online:
                            with sftp_semaphore:  # Limit concurrent SFTP connections
                                client_name = item.get("client_name", "").strip().replace(" ", "_") or None
                                project_name = item.get("project_name", item.get("name", "")).strip().replace(" ", "_") or None
                                if not client_name or not project_name:
                                    try:
                                        parts = Path(file_path).parts
                                        if len(parts) >= 3:
                                            client_name = client_name or parts[1]
                                            project_name = project_name or parts[2]
                                        else:
                                            client_name = client_name or "default_client"
                                            project_name = project_name or "default_project"
                                    except Exception as e:
                                        self.log_update.emit(f"[Upload] Fallback parsing failed: {e}")
                                        client_name = client_name or "default_client"
                                        project_name = project_name or "default_project"
                                original_nas_path = item.get('file_path', file_path)
                                self.show_progress(f"Uploading {file_name}", local_path, original_nas_path, action_type, item, False, not is_online)
                                self.log_update.emit(f"[API Scan] Upload successful: {local_path} to {original_nas_path}, task_id: {task_id}")
                                return {
                                    'update': (local_path, "Upload Completed (Original)", action_type, 100, not is_online),
                                    'task_key': task_key,
                                    'success': True
                                }
                        else:
                            self.show_progress(f"Uploading {file_name}", local_path, file_path, action_type, item, False, not is_online)
                            self.log_update.emit(f"[API Scan] Upload successful: {local_path} to {file_path}, task_id: {task_id}")
                            return {
                                'update': (local_path, "Upload Completed (Original)", action_type, 100, not is_online),
                                'task_key': task_key,
                                'success': True
                            }
                    except Exception as e:
                        logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Upload failed for {local_path} (Task {task_id}): {str(e)}, attempt {attempt + 1}, instance: {id(self)}")
                        self.log_update.emit(f"[API Scan] Upload failed for {local_path} (Task {task_id}): {str(e)}")
                        update = (local_path, f"Upload Failed: {str(e)}", action_type, 0, not is_online)
                        if attempt < max_download_retries - 1:
                            delay = 2 ** attempt
                            logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] Retrying upload after {delay}s, instance: {id(self)}")
                            self.log_update.emit(f"[API Scan] Retrying upload after {delay}s")
                            time.sleep(delay)
                        else:
                            raise
        except Exception as e:
            logger.error(f"[{datetime.now(timezone.utc).isoformat()}] Error processing task {task_id}: {str(e)}, instance: {id(self)}")
            self.log_update.emit(f"[API Scan] Error processing task {task_id}: {str(e)}")
            return {
                'update': (local_path, f"{action_type} Failed: {str(e)}", action_type, 0, not is_online),
                'task_key': task_key,
                'success': False
            }

    def check_connectivity(self):
        try:
            logger.debug(f"Checking API connectivity (attempt 1): {DOWNLOAD_UPLOAD_API}")
            self.log_update.emit(f"[API Scan] Checking API connectivity (attempt 1): {DOWNLOAD_UPLOAD_API}")
            response = HTTP_SESSION.get(f"{DOWNLOAD_UPLOAD_API}?user_id=200", verify=False, timeout=10)
            app_signals.api_call_status.emit(DOWNLOAD_UPLOAD_API, f"Status: {response.status_code}, Response: {response.text[:500]}...", response.status_code)
            self.log_update.emit(f"[API Scan] API Call: {DOWNLOAD_UPLOAD_API} | Status: Status: {response.status_code}, Response: {response.text[:500]}...")
            response.raise_for_status()
            self.log_update.emit("[API Scan] API connectivity check passed")
            return True
        except RequestException as e:
            logger.error(f"API connectivity check failed: {str(e)}")
            self.log_update.emit(f"[API Scan] API connectivity check failed: {str(e)}")
            return False

    def show_progress(self, message, src_path, dest_path, action_type, item, is_nas_src, is_nas_dest):
        task_id = str(item.get('id', ''))
        original_filename = Path(src_path).name
        try:
            self.perform_file_transfer(src_path, dest_path, action_type, item, is_nas_src, is_nas_dest)
            self.progress_update.emit(f"{action_type} Completed (Task {task_id}): {original_filename}", dest_path, 100)
        except Exception as e:
            logger.error(f"Progress error for {action_type} (Task {task_id}): {str(e)}")
            self.log_update.emit(f"[App] Progress update: {action_type} Failed (Task {task_id}): {original_filename}")
            raise

    def _download_from_http(self, src_path, dest_path):
        raise NotImplementedError("HTTP download not implemented")

    def _upload_to_http(self, src_path):
        raise NotImplementedError("HTTP upload not implemented")

    def _clean_processed_tasks(self):
        current_time = time.time()
        retention_seconds = self.config["task_retention_hours"] * 3600
        self.processed_tasks = {task for task in self.processed_tasks if (current_time - float(task.split(":")[0])) < retention_seconds}
        if len(self.processed_tasks) > self.config["max_processed_tasks"]:
            self.processed_tasks = set(list(self.processed_tasks)[-self.config["max_processed_tasks"]:])

    def cleanup(self):
        self.running = False
        logger.info("FileWatcherWorker cleaned up")
        self.log_update.emit("[FileWatcher] Cleaned up")

    def stop(self):
        """Stop the timer and worker gracefully."""
        self.running = False
        if self.timer.isActive():
            self.timer.stop()
        logger.debug(f"[{datetime.now(timezone.utc).isoformat()}] FileWatcherWorker stopped")






class LogWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PremediaApp Log")
        self.setWindowIcon(load_icon(ICON_PATH, "log window"))
        self.setMinimumSize(700, 400)
        self.resize(700, 400)

        # Initialize UI components
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.status_bar = QStatusBar(self)

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.status_bar)
        self.setLayout(layout)

        # Track signal-slot pairs with metadata
        self._connected_signals = {}  # Format: {name: (signal, slot, signal_signature)}

        # Load logs and connect signals
        self.load_logs()
        self.connect_signals()

        logger.info("LogWindow initialized")
        app_signals.append_log.emit("[Log] LogWindow initialized")

    def connect_signals(self):
        """Connect all signals, ensuring no duplicates."""
        if self._connected_signals:
            logger.debug("Signals already connected, skipping reconnection.")
            return

        # Define signal-slot pairs with expected signatures
        signal_pairs = [
            (app_signals.append_log, self.append_log, "append_log", str),
            (app_signals.api_call_status, self.append_api_status, "api_call_status", (str, str, int)),
            (app_signals.update_status, self.handle_update_status, "update_status", str),
            (app_signals.update_timer_status, self.update_timer_status, "update_timer_status", str),
        ]

        for signal, slot, name, expected_signature in signal_pairs:
            self.safe_connect(signal, slot, name, expected_signature)

    def safe_connect(self, signal, slot, name, expected_signature):
        """Connect a signal to a slot with signature verification and tracking."""
        try:
            # Verify signal signature
            signal_signature = getattr(signal, "signature", None)
            if signal_signature:
                logger.debug(f"Signal '{name}' signature: {signal_signature}")
            else:
                logger.warning(f"No signature available for signal '{name}'")

            # Basic signature check (PyQt doesn't expose signature directly, so we rely on expected)
            signal.connect(slot)
            self._connected_signals[name] = (signal, slot, expected_signature)
            logger.debug(f"✅ Connected '{name}' to '{slot.__name__}' with expected signature {expected_signature}")
        except Exception as e:
            logger.error(f"❌ Failed to connect '{name}' to '{slot.__name__}': {e}")
            app_signals.append_log.emit(f"[Log] Failed to connect signal '{name}': {str(e)}")


    def safe_disconnect(self, name):
        """Disconnect a signal safely with detailed logging."""
        signal_slot = self._connected_signals.pop(name, None)
        if signal_slot:
            signal, slot, signature = signal_slot
            try:
                if signal is not None and slot is not None:
                    with warnings.catch_warnings(record=True) as caught_warnings:
                        warnings.simplefilter("always")
                        signal.disconnect(slot)

                        if caught_warnings:
                            for w in caught_warnings:
                                logger.warning(f"⚠️ Disconnect warning for '{name}': {w.message}")
                        else:
                            logger.debug(f"✅ Disconnected '{name}' from '{slot.__name__}' (signature: {signature})")
                else:
                    logger.warning(f"⚠️ '{name}' has invalid signal or slot object.")
            except Exception as e:
                logger.warning(f"⚠️ Could not disconnect '{name}' from '{getattr(slot, '__name__', repr(slot))}': {e}")
        else:
            logger.debug(f"⚠️ '{name}' was never connected or already disconnected.")

    def disconnect_signals(self):
        """Disconnect all tracked signals."""
        for name in list(self._connected_signals.keys()):
            self.safe_disconnect(name)
        logger.debug("All signals disconnected.")

    def handle_update_status(self, message):
        """Update status bar with a message."""
        try:
            self.status_bar.showMessage(message)
            logger.debug(f"Status bar updated: {message}")
        except Exception as e:
            logger.error(f"Failed to update status bar: {e}")
            app_signals.append_log.emit(f"[Log] Failed to update status bar: {str(e)}")

    def update_timer_status(self, message):
        """Update timer status in status bar and log."""
        try:
            self.status_bar.showMessage(message)
            app_signals.append_log.emit(f"[Timer] {message}")
            logger.debug(f"Timer status updated: {message}")
        except Exception as e:
            logger.error(f"Failed to update timer status: {e}")
            app_signals.append_log.emit(f"[Timer] Failed to update timer status: {str(e)}")

    def load_logs(self):
        """Load recent logs from file."""
        try:
            log_file = log_dir / "app.log"
            if log_file.exists():
                with log_file.open("r", encoding='utf-8') as f:
                    lines = f.readlines()[-200:]
                self.text_edit.setPlainText("".join(lines))
                self.text_edit.moveCursor(QTextCursor.End)
                self.status_bar.showMessage("Logs loaded")
                app_signals.append_log.emit("[Log] Loaded existing logs from app.log")
                logger.debug(f"Loaded {len(lines)} log lines from {log_file}")
            else:
                self.status_bar.showMessage("No log file found")
                app_signals.append_log.emit("[Log] No log file found, starting fresh")
                logger.warning("No log file found at {log_file}")
        except Exception as e:
            logger.error(f"Failed to load logs: {e}")
            self.text_edit.setPlainText(f"Failed to load logs: {e}")
            self.status_bar.showMessage(f"Failed to load logs: {str(e)}")
            app_signals.append_log.emit(f"[Log] Failed to load logs: {str(e)}")

    def append_log(self, message):
        """Append a log message to the text edit."""
        try:
            # Format API scan messages in bold
            if "[API Scan]" in message:
                self.text_edit.append(f"<b>{message}</b>")
            else:
                self.text_edit.append(message)

            # Keep only the last 200 lines
            lines = self.text_edit.toPlainText().splitlines()
            if len(lines) > 200:
                self.text_edit.setPlainText("\n".join(lines[-200:]))

            self.text_edit.moveCursor(QTextCursor.End)
            self.text_edit.ensureCursorVisible()
            QApplication.processEvents()
            logger.debug(f"Appended log: {message}")
        except Exception as e:
            logger.error(f"Failed to append log: {e}")
            app_signals.append_log.emit(f"[Log] Failed to append log: {str(e)}")

    def append_api_status(self, endpoint, status, status_code):
        """Append API status to the log."""
        try:
            log_msg = f"[API Scan] API Call: {endpoint} | Status: {status} | Code: {status_code}"
            self.text_edit.append(f"<b>{log_msg}</b>")

            # Keep only the last 200 lines
            lines = self.text_edit.toPlainText().splitlines()
            if len(lines) > 200:
                self.text_edit.setPlainText("\n".join(lines[-200:]))

            self.text_edit.moveCursor(QTextCursor.End)
            self.text_edit.ensureCursorVisible()
            QApplication.processEvents()
            app_signals.append_log.emit(log_msg)
            logger.debug(f"Appended API status: {log_msg}")
        except Exception as e:
            logger.error(f"Failed to append API status: {e}")
            app_signals.append_log.emit(f"[Log] Failed to append API status: {str(e)}")

    def closeEvent(self, event):
        logger.debug("LogWindow is closing. Disconnecting signals.")
        self.disconnect_signals()
        self._connected_signals.clear()  # Allow reconnection
        super().closeEvent(event)

# ---------------------- NEW: Async Thumbnail Loader ----------------------

class ThumbnailLoaderSignals(QObject):
    """Signals for ThumbnailLoader to communicate with the main thread."""
    loaded = Signal(QPixmap)  # Signal to send the loaded pixmap

class ThumbnailLoader(QRunnable):
    """Load a thumbnail in the background."""
    def __init__(self, label: QLabel, url: str):
        super().__init__()
        self.label = label
        self.url = url
        self.signals = ThumbnailLoaderSignals()

        # Connect the signal to update the QLabel in the main thread
        self.signals.loaded.connect(self.label.setPixmap)

    @Slot()
    def run(self):
        pixmap = QPixmap()
        try:
            # Local file
            if Path(self.url).exists():
                pixmap.load(self.url)
            # Remote URL
            elif self.url.startswith("http"):
                response = requests.get(self.url, timeout=3)
                if response.status_code == 200:
                    pixmap.loadFromData(response.content)
        except Exception:
            pass
        if pixmap.isNull():
            pixmap.load("default_thumbnail.png")
        # Emit the signal to update the GUI in the main thread
        self.signals.loaded.emit(pixmap)
# -------------------------------------------------------------------------



class FileDownloadListWindow(QDialog):
    def __init__(self, file_type, parent=None):
        super().__init__(parent)
        self.file_type = file_type.lower()
        self.setWindowTitle(f"{file_type.capitalize()} Files")
        self.setWindowIcon(load_icon(ICON_PATH, f"{file_type} files window"))
        self.setMinimumSize(800, 400)
        self.resize(800, 400)
        logger.debug(f"Initializing FileListWindow for file_type: {self.file_type}")
        app_signals.append_log.emit(f"[Files] Initializing FileListWindow for {self.file_type}")

        # Initialize search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search by Project Name, Job Name, or File Name")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1.5px solid #ccc;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
                color: #333;
                selection-background-color: #0078d7;
            }

            QLineEdit:hover {
                border: 1.5px solid #999;
                background-color: #f9f9f9;
            }

            QLineEdit:focus {
                border: 1.5px solid #0078d7;
                background-color: #ffffff;
            }

            QLineEdit::placeholder {
                color: #888;
                font-style: italic;
            }
        """)

        # Initialize search button
        self.search_button = QPushButton("Search", self)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 20px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #004b82;
            }
        """)
        self.search_button.clicked.connect(lambda: self.filter_table(self.search_bar.text()))

        # Initialize clear button
        self.clear_button = QPushButton("Clear", self)
        # --- QPushButton (Clear) Style ---
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #333;
                border: 1.2px solid #ccc;
                border-radius: 8px;
                padding: 6px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #eaeaea;
                border-color: #999;
            }
            QPushButton:pressed {
                background-color: #dcdcdc;
            }
        """)
        self.clear_button.clicked.connect(self.clear_search)

        # Initialize table
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        headers = ["Thumbnail", "Project Name", "Job Name", "File Name", "Date", "Open Folder", "Open in Photoshop", "Status"]
        if platform.system() == "Windows":
            headers.append("Copy")
        self.table.setHorizontalHeaderLabels(headers)
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Layout
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_button)

        layout = QVBoxLayout()
        layout.addLayout(search_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        add_version_footer(self, APPVERSION)

        # Store original rows for filtering
        self.original_rows = []

        # Load files initially
        self._load_files_with_logging()

        # Connect signals
        self.app_signals_connection = app_signals.update_file_list.connect(self.refresh_files, Qt.QueuedConnection)
        self.file_watcher = FileWatcherWorker.get_instance(parent=self)
        self.progress_connection = self.file_watcher.progress_update.connect(self.update_progress, Qt.QueuedConnection)

    def keyPressEvent(self, event):
        """Handle Enter key press in the search bar."""
        super().keyPressEvent(event)
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.search_bar.hasFocus():
            self.filter_table(self.search_bar.text())

    def showEvent(self, event):
        """Reload files when the window is shown."""
        super().showEvent(event)
        logger.debug(f"Window shown, reloading files for {self.file_type}")
        self._load_files_with_logging()
        app_signals.append_log.emit(f"[Files] Reloaded {self.file_type} files on window show")

    def closeEvent(self, event):
        """Disconnect signals when the window is closed."""
        try:
            app_signals.update_file_list.disconnect(self.app_signals_connection)
            self.file_watcher.progress_update.disconnect(self.progress_connection)
            logger.debug(f"Disconnected signals for {self.file_type} FileListWindow")
        except Exception as e:
            logger.debug(f"Error disconnecting signals: {e}")
        super().closeEvent(event)

    def _load_files_with_logging(self):
        """Wrapper for load_files with additional logging for debugging."""
        try:
            self.load_files()
        except Exception as e:
            logger.error(f"Error loading files in FileListWindow: {e}")
            app_signals.append_log.emit(f"[Files] Failed to load files for {self.file_type}: {str(e)}")

    def load_files(self):
        """Load files into the table based on file_type."""
        try:
            cache = load_cache()
            logger.debug(f"Cache contents: {cache}")
            metadata_key = f"{self.file_type}_files_with_metadata"
            logger.debug(f"Metadata for {metadata_key}: {cache.get(metadata_key, {})}")

            metadata = cache.get(metadata_key, {})
            files = {task_id: data.get("local_path", "") for task_id, data in metadata.items() if data.get("local_path")}
            logger.debug(f"Files for {self.file_type}: {files}")

            # Clear table
            self.table.clearContents()
            self.table.setRowCount(0)

            # Set headers
            headers = [
                "Thumbnail",
                "Project Name",
                "Job Name",
                "File Name",
                "Date",
                "Open Folder",
                "Open in Photoshop",
                "Status",
            ]
            if platform.system() == "Windows":
                headers.append("Copy")

            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)

            # Collect rows
            self.original_rows = []
            file_list = files.items()
            logger.debug(f"File list: {list(file_list)}")

            for task_id, file_path in file_list:
                logger.debug(f"Processing task_id: {task_id}, file_path: {file_path}")
                if not file_path:
                    logger.warning(f"Skipping task_id {task_id} due to empty file_path")
                    continue

                filename = Path(file_path).name
                normalized_file_path = str(Path(file_path)).replace('\\', '/')
                relative_file_path = normalized_file_path.split('premedia.irtest/')[-1] if 'premedia.irtest/' in normalized_file_path else normalized_file_path

                meta = metadata.get(str(task_id), {})
                if not meta:
                    logger.warning(f"No metadata found for task_id: {task_id}, file_path: {file_path}")
                    continue
                thumbnail = meta.get("api_response", {}).get("thumbnail", "Unknown") or "Unknown"
                project_name = meta.get("api_response", {}).get("project_name", "Unknown") or "Unknown"
                job_name = meta.get("api_response", {}).get("job_name", "Unknown") or "Unknown"

                if project_name == "Unknown" or job_name == "Unknown":
                    logger.debug(f"Skipping file {filename} due to project_name: {project_name}, job_name: {job_name}, meta: {meta}")
                    continue

                created_at_raw = meta.get("api_response", {}).get("created_on", "") or meta.get("created_at") or meta.get("date", "")

                dt = None
                display_date = ""
                if created_at_raw:
                    try:
                        ts = int(created_at_raw)
                        if 0 < ts < 4102444800:
                            dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
                            display_date = dt.strftime("%d-%b-%Y %I:%M %p")
                    except Exception:
                        pass

                    if not dt and isinstance(created_at_raw, str):
                        s = created_at_raw.strip()
                        try:
                            dt = datetime.fromisoformat(s)
                            display_date = dt.strftime("%d-%b-%Y %I:%M %p")
                        except Exception:
                            fmts = [
                                "%d-%b-%Y %I:%M %p",
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%dT%H:%M:%S%z",
                                "%Y-%m-%dT%H:%M:%S",
                            ]
                            for f in fmts:
                                try:
                                    dt = datetime.strptime(s, f)
                                    display_date = dt.strftime("%d-%b-%Y %I:%M %p")
                                    break
                                except Exception:
                                    continue

                status = meta.get("api_response", {}).get("request_status", "Unknown")
                if status == "Unknown" and file_path:
                    status = "Completed" if Path(file_path).exists() else "Failed"

                meta_data_response = meta.get("api_response", {})

                self.original_rows.append({
                    "thumbnail": thumbnail,
                    "project_name": project_name,
                    "job_name": job_name,
                    "file_name": filename,
                    "created_at": display_date or created_at_raw,
                    "folder_path": file_path,
                    "photoshop_path": file_path,
                    "Copy_path": file_path,
                    "status": status,
                    "dt": dt,
                    "meta_data_response": meta_data_response
                })

            # Sort rows by date (latest first)
            self.original_rows.sort(key=lambda r: (1 if r["dt"] is None else 0, -r["dt"].timestamp() if r["dt"] else 0))

            # Populate table with all rows initially
            self._populate_table(self.original_rows)

            app_signals.append_log.emit(f"[Files] Loaded {len(self.original_rows)} {self.file_type} files")

        except Exception as e:
            logger.error(f"Error in load_files for {self.file_type}: {str(e)}")
            app_signals.append_log.emit(f"[Files] Failed to load {self.file_type} files: {str(e)}")
            raise

    def _populate_table(self, rows):
        """Populate the table with the given rows."""
        self.table.clearContents()
        self.table.setRowCount(0)

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            logger.debug(f"Inserting row {row} with data: {row_data}")

            thumb_label = QLabel()
            thumb_label.setFixedSize(24, 24)
            thumb_label.setScaledContents(True)
            thumb_label.setPixmap(QPixmap("default_thumbnail.png"))
            self.table.setCellWidget(row, 0, thumb_label)

            loader = ThumbnailLoader(thumb_label, row_data["thumbnail"])
            pool = QThreadPool.globalInstance()
            pool.start(loader)

            self.table.setItem(row, 1, QTableWidgetItem(row_data["project_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(row_data["job_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(row_data["file_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(row_data["created_at"]))

            folder_btn = QPushButton()
            folder_btn.setIcon(load_icon(FOLDER_ICON_PATH, "folder"))
            folder_btn.setIconSize(QSize(24, 24))
            folder_btn.clicked.connect(lambda _, p=row_data["folder_path"]: self.open_folder(p))
            self.table.setCellWidget(row, 5, folder_btn)

            photoshop_btn = QPushButton()
            photoshop_btn.setIcon(load_icon(PHOTOSHOP_ICON_PATH, "photoshop"))
            photoshop_btn.setIconSize(QSize(24, 24))
            photoshop_btn.clicked.connect(lambda _, p=row_data["photoshop_path"]: self.open_with_photoshop(p))
            self.table.setCellWidget(row, 6, photoshop_btn)

            if row_data["status"] == 'Failed' or row_data["status"] == 'Download Failed':
                status_btn = QPushButton(row_data["status"])
                status_btn.setIcon(load_icon(RETRY_ICON_PATH, "status"))
                status_btn.setIconSize(QSize(24, 24))
                status_btn.clicked.connect(lambda _, p=row_data["meta_data_response"]: self.retry_file_process(p))
                self.table.setCellWidget(row, 7, status_btn)
            else:
                self.table.setItem(row, 7, QTableWidgetItem(row_data["status"]))

            if platform.system() == "Windows":
                copy_btn = QPushButton()
                copy_btn.setIcon(load_icon(COPY_ICON_PATH, "copy"))
                copy_btn.setIconSize(QSize(24, 24))
                copy_btn.clicked.connect(lambda _, p=row_data["Copy_path"]: self.copy_file_to_clipboard(p))
                self.table.setCellWidget(row, 8, copy_btn)

        self.table.resizeColumnsToContents()

    def filter_table(self, search_text):
        """Filter table rows based on search text."""
        search_text = search_text.lower().strip()
        filtered_rows = []

        for row_data in self.original_rows:
            if (search_text in row_data["project_name"].lower() or
                search_text in row_data["job_name"].lower() or
                search_text in row_data["file_name"].lower()):
                filtered_rows.append(row_data)

        if not filtered_rows:
            # Clear table and show "Content not available" message
            self.table.clearContents()
            self.table.setRowCount(1)
            label = QLabel("Content not available")
            label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(0, 0, label)
            self.table.setSpan(0, 0, 1, self.table.columnCount())
            logger.debug("No matching rows found, displaying 'Content not available'")
            app_signals.append_log.emit(f"[Files] No {self.file_type} files match the search: {search_text}")
        else:
            self._populate_table(filtered_rows)
            logger.debug(f"Filtered table to {len(filtered_rows)} rows with search: {search_text}")
            app_signals.append_log.emit(f"[Files] Filtered {self.file_type} files to {len(filtered_rows)} rows")

    def clear_search(self):
        """Clear the search bar and repopulate the table with all rows."""
        self.search_bar.clear()
        self._populate_table(self.original_rows)
        logger.debug(f"Cleared search and restored {len(self.original_rows)} rows")
        app_signals.append_log.emit(f"[Files] Cleared search and restored {len(self.original_rows)} {self.file_type} files")

    def refresh_files(self, file_path, status, action_type, progress, is_nas_src):
        """Refresh the file list if the action_type matches file_type."""
        try:
            if action_type == self.file_type:
                logger.debug(f"Refreshing files for {self.file_type} due to update: {file_path}, status: {status}, progress: {progress}")
                self._load_files_with_logging()
                # Reapply filter after refresh
                self.filter_table(self.search_bar.text())
                app_signals.append_log.emit(f"[Files] Refreshed {self.file_type} file list")
        except Exception as e:
            logger.error(f"Error refreshing file list: {e}")
            app_signals.append_log.emit(f"[Files] Failed to refresh {self.file_type} file list: {str(e)}")

    def update_file_list(self, file_path, status, action_type, progress, is_nas_src):
        """Update the table with file transfer status."""
        if action_type != self.file_type or not file_path:
            return
        try:
            logger.debug(f"Updating file list for {self.file_type}: {file_path}, status: {status}, progress: {progress}")
            for row in range(self.table.rowCount()):
                if self.table.item(row, 3) and self.table.item(row, 3).text() == Path(file_path).name:
                    status_col = 7
                    progress_col = 4
                    self.table.setItem(row, status_col, QTableWidgetItem(status))
                    progress_bar = self.table.cellWidget(row, progress_col)
                    if not isinstance(progress_bar, QProgressBar):
                        progress_bar = QProgressBar(self)
                        progress_bar.setMinimum(0)
                        progress_bar.setMaximum(100)
                        progress_bar.setFixedHeight(20)
                        self.table.setCellWidget(row, progress_col, progress_bar)
                    progress_bar.setValue(progress)
                    self.table.resizeColumnsToContents()
                    app_signals.append_log.emit(f"[Files] Updated {self.file_type} file list: {Path(file_path).name}")
                    return

            # If file not found, reload the entire table
            logger.debug(f"File {file_path} not found in table, reloading full list")
            self._load_files_with_logging()
            self.filter_table(self.search_bar.text())
            app_signals.append_log.emit(f"[Files] Added {Path(file_path).name} to {self.file_type} list by refreshing")
        except Exception as e:
            logger.error(f"Error updating file list: {e}")
            app_signals.append_log.emit(f"[Files] Failed to update {self.file_type} file list: {str(e)}")

    def update_progress(self, file_path, progress):
        """Update progress for a file in the table."""
        try:
            logger.debug(f"Updating progress for {self.file_type}: {file_path}, progress: {progress}")
            for row in range(self.table.rowCount()):
                if self.table.item(row, 3) and self.table.item(row, 3).text() == Path(file_path).name:
                    progress_col = 4
                    progress_bar = self.table.cellWidget(row, progress_col)
                    if not isinstance(progress_bar, QProgressBar):
                        progress_bar = QProgressBar(self)
                        progress_bar.setMinimum(0)
                        progress_bar.setMaximum(100)
                        progress_bar.setFixedHeight(20)
                        self.table.setCellWidget(row, progress_col, progress_bar)
                    progress_bar.setValue(progress)
                    app_signals.append_log.emit(f"[Files] Progress updated for {Path(file_path).name}: {progress}%")
                    return
            logger.debug(f"File {file_path} not found for progress update, reloading table")
            self._load_files_with_logging()
            self.filter_table(self.search_bar.text())
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            app_signals.append_log.emit(f"[Files] Failed to update progress: {str(e)}")

    def open_with_photoshop(self, file_path):
        """Dynamically find Adobe Photoshop path and open the specified file."""
        try:
            import platform
            import subprocess
            import time
            import logging
            import os
            from pathlib import Path

            logger = logging.getLogger(__name__)
            system = platform.system()
            file_path = str(Path(file_path).resolve())

            if not Path(file_path).exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")

            logger.debug(f"System: {system}, File path: {file_path}")
            photoshop_path = None

            if system == "Windows":
                try:
                    import win32gui
                    import win32con
                    import win32com.client
                    import win32api
                    import win32process
                    import ctypes
                except ImportError as e:
                    raise ImportError("Required pywin32 modules not found. Run: pip install pywin32") from e

                photoshop_path = os.getenv("PHOTOSHOP_PATH")
                if photoshop_path and Path(photoshop_path).exists():
                    logger.debug(f"Using Photoshop path from PHOTOSHOP_PATH: {photoshop_path}")
                else:
                    search_dirs = [
                        Path("C:/Program Files/Adobe"),
                        Path("C:/Program Files (x86)/Adobe")
                    ]
                    for base_dir in search_dirs:
                        if not base_dir.exists():
                            logger.debug(f"Search directory does not exist: {base_dir}")
                            continue
                        photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                        if photoshop_exes:
                            photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                            photoshop_path = str(photoshop_exes[0])
                            logger.debug(f"Found Photoshop at: {photoshop_path}")
                            break
                    if not photoshop_path:
                        raise FileNotFoundError("Adobe Photoshop executable not found in Program Files")

                if not os.access(photoshop_path, os.X_OK):
                    raise PermissionError(f"Photoshop executable is not accessible: {photoshop_path}")

                com_success = False
                try:
                    logger.debug("Attempting to open via COM")
                    ps_app = win32com.client.Dispatch("Photoshop.Application")
                    ps_app.Visible = True
                    ps_app.Open(file_path)

                    def bring_to_front(title_contains="Adobe Photoshop"):
                        def enum_handler(hwnd, _):
                            if win32gui.IsWindowVisible(hwnd):
                                title = win32gui.GetWindowText(hwnd)
                                if title_contains.lower() in title.lower():
                                    try:
                                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                        fg_thread = win32process.GetWindowThreadProcessId(
                                            win32gui.GetForegroundWindow())[0]
                                        target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
                                        this_thread = win32api.GetCurrentThreadId()
                                        if ctypes.windll.user32.AttachThreadInput(this_thread, target_thread, True):
                                            win32gui.SetForegroundWindow(hwnd)
                                            ctypes.windll.user32.AttachThreadInput(this_thread, target_thread, False)
                                    except Exception as e:
                                        logger.debug(f"Window activation failed: {e}")
                        win32gui.EnumWindows(enum_handler, None)

                    time.sleep(1.5)
                    bring_to_front()
                    logger.info(f"Opened {Path(file_path).name} via COM")
                    print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                    com_success = True
                except Exception as e:
                    logger.debug(f"COM attempt failed: {e}. Falling back to subprocess.")

                if not com_success:
                    for attempt in range(3):
                        try:
                            cmd = [photoshop_path, file_path]
                            logger.debug(f"Executing subprocess command: {cmd}")
                            result = subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
                            time.sleep(2)
                            def enum_windows_callback(hwnd, hwnds):
                                if win32gui.IsWindowVisible(hwnd) and 'Adobe Photoshop' in win32gui.GetWindowText(hwnd):
                                    hwnds.append(hwnd)
                            hwnds = []
                            win32gui.EnumWindows(enum_windows_callback, hwnds)
                            if hwnds:
                                win32gui.ShowWindow(hwnds[0], win32con.SW_RESTORE)
                                win32gui.SetForegroundWindow(hwnds[0])
                            logger.info(f"Opened {Path(file_path).name} via subprocess")
                            print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                            break
                        except subprocess.CalledProcessError as e:
                            if attempt < 2:
                                logger.debug(f"Subprocess attempt {attempt+1} failed: {e}, stderr: {e.stderr}. Retrying...")
                                time.sleep(2)
                            else:
                                logger.debug(f"Subprocess failed after retries: {e}, stderr: {e.stderr}")
                                try:
                                    process = subprocess.Popen([photoshop_path, file_path], stderr=subprocess.PIPE, text=True)
                                    time.sleep(2)
                                    def enum_windows_callback(hwnd, hwnds):
                                        if win32gui.IsWindowVisible(hwnd) and 'Adobe Photoshop' in win32gui.GetWindowText(hwnd):
                                            hwnds.append(hwnd)
                                    hwnds = []
                                    win32gui.EnumWindows(enum_windows_callback, hwnds)
                                    if hwnds:
                                        win32gui.ShowWindow(hwnds[0], win32con.SW_RESTORE)
                                        win32gui.SetForegroundWindow(hwnds[0])
                                    logger.info(f"Opened {Path(file_path).name} via Popen fallback")
                                    print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                                except Exception as e2:
                                    raise RuntimeError(f"Failed to open file after 3 attempts: {e}, Popen fallback failed: {e2}")

            elif system == "Darwin":
                custom_path = os.getenv("PHOTOSHOP_PATH")
                if custom_path and Path(custom_path).exists():
                    photoshop_path = str(Path(custom_path).resolve())
                    logger.debug(f"Found Photoshop via environment variable: {photoshop_path}")

                if not photoshop_path:
                    try:
                        result = subprocess.run(
                            ["mdfind", "kMDItemKind == 'Application' && (kMDItemFSName == 'Adobe Photoshop*.app' || kMDItemFSName == 'Photoshop*.app' || kMDItemFSName == 'Adobe*Photoshop*.app')"],
                            capture_output=True, text=True, check=True
                        )
                        if result.stdout.strip():
                            photoshop_path = result.stdout.strip().split("\n")[0]
                            logger.debug(f"Found Photoshop via mdfind: {photoshop_path}")
                    except subprocess.CalledProcessError as e:
                        logger.debug(f"mdfind failed with error: {e}, stderr: {e.stderr}")

                if not photoshop_path:
                    search_locations = [
                        Path("/Applications"),
                        Path("~/Applications").expanduser(),
                        Path("/Applications/Adobe Creative Cloud"),
                        Path("~/Applications/Adobe Creative Cloud").expanduser(),
                        Path("/Applications/Adobe"),
                        Path("~/Applications/Adobe").expanduser(),
                        Path("/Applications/Adobe Photoshop*"),
                        Path("~/Applications/Adobe Photoshop*").expanduser(),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop*"),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop*").expanduser(),
                    ]
                    for search_dir in search_locations:
                        if not search_dir.exists():
                            logger.debug(f"Search directory does not exist: {search_dir}")
                            continue
                        logger.debug(f"Searching for Photoshop in: {search_dir}")
                        photoshop_apps = (
                            list(search_dir.glob("Adobe*Photoshop*.app")) +
                            list(search_dir.glob("Photoshop*.app")) +
                            list(search_dir.glob("*/Adobe*Photoshop*.app"))
                        )
                        if photoshop_apps:
                            logger.debug(f"Found potential Photoshop apps: {[str(app) for app in photoshop_apps]}")
                            photoshop_apps.sort(key=lambda x: x.name, reverse=True)
                            photoshop_path = str(photoshop_apps[0])
                            logger.debug(f"Selected Photoshop via glob in {search_dir}: {photoshop_path}")
                            break

                if not photoshop_path:
                    versioned_paths = [
                        Path("/Applications/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("~/Applications/Adobe Photoshop 2025/Adobe Photoshop 2025.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2025/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2024/Adobe Photoshop 2024.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2024/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2023/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop 2025.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop 2024.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop 2023.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop.app").expanduser(),
                    ]
                    for path in versioned_paths:
                        if path.exists():
                            photoshop_path = str(path)
                            logger.debug(f"Found Photoshop in versioned path: {photoshop_path}")
                            break

                if not photoshop_path and hasattr(self, 'window'):
                    from PySide6.QtWidgets import QFileDialog
                    logger.debug("Prompting user to select Photoshop application")
                    photoshop_path, _ = QFileDialog.getOpenFileName(
                        self.window(), "Locate Adobe Photoshop", "/Applications", "Applications (*.app)"
                    )
                    if photoshop_path:
                        logger.debug(f"User-selected Photoshop path: {photoshop_path}")
                    else:
                        logger.debug("User cancelled Photoshop path selection")

                if not photoshop_path:
                    error_msg = (
                        "Adobe Photoshop application not found in /Applications, ~/Applications, "
                        "Adobe Creative Cloud, or Adobe directories. Please set PHOTOSHOP_PATH environment variable."
                    )
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

                for attempt in range(3):
                    try:
                        subprocess.run(["open", "-a", photoshop_path, file_path], check=True)
                        applescript = f'tell application "{Path(photoshop_path).name}" to activate'
                        subprocess.run(["osascript", "-e", applescript], check=True)
                        logger.info(f"Opened {Path(file_path).name} via open -a at {photoshop_path}")
                        print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                        break
                    except subprocess.CalledProcessError as e:
                        if attempt < 2:
                            logger.debug(f"Attempt {attempt+1} failed: {e}. Retrying...")
                            time.sleep(2)
                        else:
                            raise RuntimeError(f"Failed to open file after 3 attempts: {e}")

            elif system == "Linux":
                try:
                    subprocess.run(["wine", "--version"], capture_output=True, check=True)
                    wine_dirs = [
                        Path.home() / ".wine/drive_c/Program Files/Adobe",
                        Path.home() / ".wine/drive_c/Program Files (x86)/Adobe"
                    ]
                    for base_dir in wine_dirs:
                        if not base_dir.exists():
                            continue
                        photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                        if photoshop_exes:
                            photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                            photoshop_path = str(photoshop_exes[0])
                            break
                    if not photoshop_path:
                        raise FileNotFoundError("Photoshop.exe not found in Wine directories")

                    for attempt in range(3):
                        try:
                            subprocess.run(["wine", photoshop_path, file_path], check=True)
                            try:
                                subprocess.run(["wmctrl", "-a", "Adobe Photoshop"], check=False)
                            except Exception as e:
                                logger.debug(f"Could not raise Photoshop window: {e}")
                            logger.info(f"Opened {Path(file_path).name} via wine")
                            print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                            break
                        except subprocess.CalledProcessError as e:
                            if attempt < 2:
                                logger.debug(f"Attempt {attempt+1} failed: {e}. Retrying...")
                                time.sleep(2)
                            else:
                                raise RuntimeError(f"Failed to open file after 3 attempts: {e}")
                except subprocess.CalledProcessError:
                    raise FileNotFoundError("Wine is not installed or not functioning")

            else:
                error_message = f"Unsupported platform for Photoshop: {system}"
                logger.warning(error_message)
                print(f"[Photoshop] {error_message}")
                raise ValueError(error_message)

        except Exception as e:
            error_message = f"Failed to open {Path(file_path).name} in Photoshop: {str(e)}"
            logger.error(error_message)
            print(f"[Photoshop] {error_message}")
            raise

    def open_folder(self, file_path):
        """Open the folder containing the file."""
        try:
            folder_path = str(Path(file_path).parent)
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", folder_path], check=True)
            elif system == "Darwin":
                subprocess.run(["open", folder_path], check=True)
            elif system == "Linux":
                subprocess.run(["xdg-open", folder_path], check=True)
            else:
                logger.warning(f"Unsupported platform for opening folder: {system}")
                app_signals.append_log.emit(f"[Folder] Unsupported platform for opening folder: {system}")
                app_signals.update_status.emit(f"Unsupported platform for opening folder: {system}")
                return
            app_signals.update_status.emit(f"Opened folder for {Path(file_path).name}")
            app_signals.append_log.emit(f"[Folder] Opened folder for {Path(file_path).name}")
        except Exception as e:
            logger.error(f"Failed to open folder {file_path}: {e}")
            app_signals.append_log.emit(f"[Folder] Failed to open folder: {str(e)}")
            app_signals.update_status.emit(f"Failed to open folder for {Path(file_path).name}: {str(e)}")

    def copy_file_to_clipboard(self, file_path):
        """Copy the file path to the clipboard."""
        try:
            file_path = os.path.join(BASE_TARGET_DIR, file_path)
            if not os.path.exists(file_path):
                raise FileNotFoundError(file_path)

            system = platform.system()
            if system == "Windows":
                import pyautogui
                import ctypes
                import pygetwindow as gw

            folder, filename = os.path.split(os.path.abspath(file_path))
            if system == "Windows":
                SW_SHOWNOACTIVATE = 4
                ctypes.windll.shell32.ShellExecuteW(None, "open", folder, None, None, SW_SHOWNOACTIVATE)
            elif system == "Darwin":
                subprocess.run(["open", folder])
            else:
                raise NotImplementedError(f"Unsupported OS: {system}")

            time.sleep(0.1)
            pyautogui.typewrite(filename)
            time.sleep(0.1)

            if system == "Windows":
                pyautogui.hotkey('ctrl', 'c')
                pyautogui.hotkey('alt', 'f4')
            elif system == "Darwin":
                pyautogui.hotkey('command', 'c')
                pyautogui.hotkey('command', 'w')
            else:
                raise NotImplementedError(f"Copy not supported on {system}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Cleanup or final steps executed.")

    def retry_file_process(self, meta_data_response):
        """Retry a failed file process."""
        print(f"meta_data_response===={meta_data_response}")
        action_type = meta_data_response.get("request_type", "Unknown")
        if action_type == 'download':
            src_path = meta_data_response.get("file_path", "")
            dest_path = os.path.join(BASE_TARGET_DIR, meta_data_response.get("nas_path", ""))
            is_nas_src = True
            is_nas_dest = False
            print(f"===={src_path}==={dest_path}===={action_type}========{is_nas_src}=========={is_nas_dest}=======")
        if action_type == 'upload':
            dest_path = meta_data_response.get("file_path", "")
            src_path = os.path.join(BASE_TARGET_DIR, meta_data_response.get("nas_path", ""))
            is_nas_src = False
            is_nas_dest = True
        file_worker = FileWatcherWorker.get_instance()

        file_worker.perform_file_transfer(
            src_path,
            dest_path,
            action_type,
            meta_data_response,
            is_nas_src,
            is_nas_dest
        )
        

class FileUploadListWindow(QDialog):
    def __init__(self, file_type, parent=None):
        super().__init__(parent)
        self.file_type = file_type.lower()
        self.setWindowTitle(f"{file_type.capitalize()} Files")
        self.setWindowIcon(load_icon(ICON_PATH, f"{file_type} files window"))
        self.setMinimumSize(800, 400)
        self.resize(800, 400)
        logger.debug(f"Initializing FileListWindow for file_type: {self.file_type}")
        app_signals.append_log.emit(f"[Files] Initializing FileListWindow for {self.file_type}")

        # Initialize search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search by Project Name, Job Name, or File Name")
        # --- QLineEdit Style ---
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1.5px solid #ccc;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
                color: #333;
                selection-background-color: #0078d7;
            }

            QLineEdit:hover {
                border: 1.5px solid #999;
                background-color: #f9f9f9;
            }

            QLineEdit:focus {
                border: 1.5px solid #0078d7;
                background-color: #ffffff;
            }

            QLineEdit::placeholder {
                color: #888;
                font-style: italic;
            }
        """)


        # Initialize search button
        self.search_button = QPushButton("Search", self)
        # --- QPushButton (Search) Style ---
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 20px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #004b82;
            }
        """)
        self.search_button.clicked.connect(lambda: self.filter_table(self.search_bar.text()))

        # Initialize clear button
        self.clear_button = QPushButton("Clear", self)
        # --- QPushButton (Clear) Style ---
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #333;
                border: 1.2px solid #ccc;
                border-radius: 8px;
                padding: 6px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #eaeaea;
                border-color: #999;
            }
            QPushButton:pressed {
                background-color: #dcdcdc;
            }
        """)
        self.clear_button.clicked.connect(self.clear_search)

        # Initialize table
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        headers = ["Thumbnail", "Project Name", "Job Name", "File Name", "Date", "Open Folder", "Open in Photoshop", "Status"]
        if platform.system() == "Windows":
            headers.append("Copy")
        self.table.setHorizontalHeaderLabels(headers)
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Layout
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_button)

        layout = QVBoxLayout()
        layout.addLayout(search_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        add_version_footer(self, APPVERSION)

        # Store original rows for filtering
        self.original_rows = []

        # Load files initially
        self._load_files_with_logging()

        # Connect signals
        self.app_signals_connection = app_signals.update_file_list.connect(self.refresh_files, Qt.QueuedConnection)
        self.file_watcher = FileWatcherWorker.get_instance(parent=self)
        self.progress_connection = self.file_watcher.progress_update.connect(self.update_progress, Qt.QueuedConnection)

    def keyPressEvent(self, event):
        """Handle Enter key press in the search bar."""
        super().keyPressEvent(event)
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.search_bar.hasFocus():
            self.filter_table(self.search_bar.text())

    def showEvent(self, event):
        """Reload files when the window is shown."""
        super().showEvent(event)
        logger.debug(f"Window shown, reloading files for {self.file_type}")
        self._load_files_with_logging()
        app_signals.append_log.emit(f"[Files] Reloaded {self.file_type} files on window show")

    def closeEvent(self, event):
        """Disconnect signals when the window is closed."""
        try:
            app_signals.update_file_list.disconnect(self.app_signals_connection)
            self.file_watcher.progress_update.disconnect(self.progress_connection)
            logger.debug(f"Disconnected signals for {self.file_type} FileListWindow")
        except Exception as e:
            logger.debug(f"Error disconnecting signals: {e}")
        super().closeEvent(event)

    def _load_files_with_logging(self):
        """Wrapper for load_files with additional logging for debugging."""
        try:
            self.load_files()
        except Exception as e:
            logger.error(f"Error loading files in FileListWindow: {e}")
            app_signals.append_log.emit(f"[Files] Failed to load files for {self.file_type}: {str(e)}")

    def load_files(self):
        """Load files into the table based on file_type."""
        try:
            cache = load_cache()
            logger.debug(f"Cache contents: {cache}")
            metadata_key = f"{self.file_type}_files_with_metadata"
            logger.debug(f"Metadata for {metadata_key}: {cache.get(metadata_key, {})}")

            metadata = cache.get(metadata_key, {})
            files = {task_id: data.get("local_path", "") for task_id, data in metadata.items() if data.get("local_path")}
            logger.debug(f"Files for {self.file_type}: {files}")

            # Clear table
            self.table.clearContents()
            self.table.setRowCount(0)

            # Set headers
            headers = [
                "Thumbnail",
                "Project Name",
                "Job Name",
                "File Name",
                "Date",
                "Open Folder",
                "Open in Photoshop",
                "Status",
            ]
            if platform.system() == "Windows":
                headers.append("Copy")

            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)

            # Collect rows
            self.original_rows = []
            file_list = files.items()
            logger.debug(f"File list: {list(file_list)}")

            for task_id, file_path in file_list:
                logger.debug(f"Processing task_id: {task_id}, file_path: {file_path}")
                if not file_path:
                    logger.warning(f"Skipping task_id {task_id} due to empty file_path")
                    continue

                filename = Path(file_path).name
                normalized_file_path = str(Path(file_path)).replace('\\', '/')
                relative_file_path = normalized_file_path.split('premedia.irtest/')[-1] if 'premedia.irtest/' in normalized_file_path else normalized_file_path

                meta = metadata.get(str(task_id), {})
                if not meta:
                    logger.warning(f"No metadata found for task_id: {task_id}, file_path: {file_path}")
                    continue
                thumbnail = meta.get("api_response", {}).get("thumbnail", "Unknown") or "Unknown"
                project_name = meta.get("api_response", {}).get("project_name", "Unknown") or "Unknown"
                job_name = meta.get("api_response", {}).get("job_name", "Unknown") or "Unknown"

                if project_name == "Unknown" or job_name == "Unknown":
                    logger.debug(f"Skipping file {filename} due to project_name: {project_name}, job_name: {job_name}, meta: {meta}")
                    continue

                created_at_raw = meta.get("api_response", {}).get("created_on", "") or meta.get("created_at") or meta.get("date", "")

                dt = None
                display_date = ""
                if created_at_raw:
                    try:
                        ts = int(created_at_raw)
                        if 0 < ts < 4102444800:
                            dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
                            display_date = dt.strftime("%d-%b-%Y %I:%M %p")
                    except Exception:
                        pass

                    if not dt and isinstance(created_at_raw, str):
                        s = created_at_raw.strip()
                        try:
                            dt = datetime.fromisoformat(s)
                            display_date = dt.strftime("%d-%b-%Y %I:%M %p")
                        except Exception:
                            fmts = [
                                "%d-%b-%Y %I:%M %p",
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%dT%H:%M:%S%z",
                                "%Y-%m-%dT%H:%M:%S",
                            ]
                            for f in fmts:
                                try:
                                    dt = datetime.strptime(s, f)
                                    display_date = dt.strftime("%d-%b-%Y %I:%M %p")
                                    break
                                except Exception:
                                    continue

                status = meta.get("api_response", {}).get("request_status", "Unknown")
                if status == "Unknown" and file_path:
                    status = "Completed" if Path(file_path).exists() else "Failed"

                meta_data_response = meta.get("api_response", {})

                row_data = {
                    "thumbnail": thumbnail,
                    "project_name": project_name,
                    "job_name": job_name,
                    "file_name": filename,
                    "created_at": display_date or created_at_raw,
                    "folder_path": file_path,
                    "photoshop_path": file_path,
                    "Copy_path": file_path,
                    "status": status,
                    "dt": dt,
                    "meta_data_response": meta_data_response
                }
                self.original_rows.append(row_data)

            # Sort rows by date (latest first)
            self.original_rows.sort(key=lambda r: (1 if r["dt"] is None else 0, -r["dt"].timestamp() if r["dt"] else 0))

            # Populate table with all rows initially
            self._populate_table(self.original_rows)

            app_signals.append_log.emit(f"[Files] Loaded {len(self.original_rows)} {self.file_type} files")

        except Exception as e:
            logger.error(f"Error in load_files for {self.file_type}: {str(e)}")
            app_signals.append_log.emit(f"[Files] Failed to load {self.file_type} files: {str(e)}")
            raise

    def _populate_table(self, rows):
        """Populate the table with the given rows."""
        self.table.clearContents()
        self.table.setRowCount(0)

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            logger.debug(f"Inserting row {row} with data: {row_data}")

            thumb_label = QLabel()
            thumb_label.setFixedSize(24, 24)
            thumb_label.setScaledContents(True)
            thumb_label.setPixmap(QPixmap("default_thumbnail.png"))
            self.table.setCellWidget(row, 0, thumb_label)

            loader = ThumbnailLoader(thumb_label, row_data["thumbnail"])
            pool = QThreadPool.globalInstance()
            pool.start(loader)

            self.table.setItem(row, 1, QTableWidgetItem(row_data["project_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(row_data["job_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(row_data["file_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(row_data["created_at"]))

            folder_btn = QPushButton()
            folder_btn.setIcon(load_icon(FOLDER_ICON_PATH, "folder"))
            folder_btn.setIconSize(QSize(24, 24))
            folder_btn.clicked.connect(lambda _, p=row_data["folder_path"]: self.open_folder(p))
            self.table.setCellWidget(row, 5, folder_btn)

            photoshop_btn = QPushButton()
            photoshop_btn.setIcon(load_icon(PHOTOSHOP_ICON_PATH, "photoshop"))
            photoshop_btn.setIconSize(QSize(24, 24))
            photoshop_btn.clicked.connect(lambda _, p=row_data["photoshop_path"]: self.open_with_photoshop(p))
            self.table.setCellWidget(row, 6, photoshop_btn)

            if row_data["status"] == 'Failed' or row_data["status"] == 'Upload Failed':
                status_btn = QPushButton("Failed")
                status_btn.setIcon(load_icon(RETRY_ICON_PATH, "status"))
                status_btn.setIconSize(QSize(24, 24))
                status_btn.clicked.connect(lambda _, p=row_data["meta_data_response"]: self.retry_file_process(p))
                self.table.setCellWidget(row, 7, status_btn)
            else:
                self.table.setItem(row, 7, QTableWidgetItem(row_data["status"]))

            if platform.system() == "Windows":
                copy_btn = QPushButton()
                copy_btn.setIcon(load_icon(COPY_ICON_PATH, "copy"))
                copy_btn.setIconSize(QSize(24, 24))
                copy_btn.clicked.connect(lambda _, p=row_data["Copy_path"]: self.copy_file_to_clipboard(p))
                self.table.setCellWidget(row, 8, copy_btn)

        self.table.resizeColumnsToContents()

    def filter_table(self, search_text):
        """Filter table rows based on search text."""
        search_text = search_text.lower().strip()
        filtered_rows = []

        for row_data in self.original_rows:
            if (search_text in row_data["project_name"].lower() or
                search_text in row_data["job_name"].lower() or
                search_text in row_data["file_name"].lower()):
                filtered_rows.append(row_data)

        if not filtered_rows:
            # Clear table and show "Content not available" message
            self.table.clearContents()
            self.table.setRowCount(1)
            label = QLabel("Content not available")
            label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(0, 0, label)
            self.table.setSpan(0, 0, 1, self.table.columnCount())
            logger.debug("No matching rows found, displaying 'Content not available'")
            app_signals.append_log.emit(f"[Files] No {self.file_type} files match the search: {search_text}")
        else:
            self._populate_table(filtered_rows)
            logger.debug(f"Filtered table to {len(filtered_rows)} rows with search: {search_text}")
            app_signals.append_log.emit(f"[Files] Filtered {self.file_type} files to {len(filtered_rows)} rows")

    def clear_search(self):
        """Clear the search bar and repopulate the table with all rows."""
        self.search_bar.clear()
        self._populate_table(self.original_rows)
        logger.debug(f"Cleared search and restored {len(self.original_rows)} rows")
        app_signals.append_log.emit(f"[Files] Cleared search and restored {len(self.original_rows)} {self.file_type} files")

    def refresh_files(self, file_path, status, action_type, progress, is_nas_src):
        """Refresh the file list if the action_type matches file_type."""
        try:
            if action_type == self.file_type:
                logger.debug(f"Refreshing files for {self.file_type} due to update: {file_path}, status: {status}, progress: {progress}")
                self._load_files_with_logging()
                # Reapply filter after refresh
                self.filter_table(self.search_bar.text())
                app_signals.append_log.emit(f"[Files] Refreshed {self.file_type} file list")
        except Exception as e:
            logger.error(f"Error refreshing file list: {e}")
            app_signals.append_log.emit(f"[Files] Failed to refresh {self.file_type} file list: {str(e)}")

    def update_file_list(self, file_path, status, action_type, progress, is_nas_src):
        """Update the table with file transfer status."""
        if action_type != self.file_type or not file_path:
            return
        try:
            logger.debug(f"Updating file list for {self.file_type}: {file_path}, status: {status}, progress: {progress}")
            for row in range(self.table.rowCount()):
                if self.table.item(row, 3) and self.table.item(row, 3).text() == Path(file_path).name:
                    status_col = 7
                    progress_col = 4
                    self.table.setItem(row, status_col, QTableWidgetItem(status))
                    progress_bar = self.table.cellWidget(row, progress_col)
                    if not isinstance(progress_bar, QProgressBar):
                        progress_bar = QProgressBar(self)
                        progress_bar.setMinimum(0)
                        progress_bar.setMaximum(100)
                        progress_bar.setFixedHeight(20)
                        self.table.setCellWidget(row, progress_col, progress_bar)
                    progress_bar.setValue(progress)
                    self.table.resizeColumnsToContents()
                    app_signals.append_log.emit(f"[Files] Updated {self.file_type} file list: {Path(file_path).name}")
                    return

            # If file not found, reload the entire table
            logger.debug(f"File {file_path} not found in table, reloading full list")
            self._load_files_with_logging()
            self.filter_table(self.search_bar.text())
            app_signals.append_log.emit(f"[Files] Added {Path(file_path).name} to {self.file_type} list by refreshing")
        except Exception as e:
            logger.error(f"Error updating file list: {e}")
            app_signals.append_log.emit(f"[Files] Failed to update {self.file_type} file list: {str(e)}")

    def update_progress(self, file_path, progress):
        """Update progress for a file in the table."""
        try:
            logger.debug(f"Updating progress for {self.file_type}: {file_path}, progress: {progress}")
            for row in range(self.table.rowCount()):
                if self.table.item(row, 3) and self.table.item(row, 3).text() == Path(file_path).name:
                    progress_col = 4
                    progress_bar = self.table.cellWidget(row, progress_col)
                    if not isinstance(progress_bar, QProgressBar):
                        progress_bar = QProgressBar(self)
                        progress_bar.setMinimum(0)
                        progress_bar.setMaximum(100)
                        progress_bar.setFixedHeight(20)
                        self.table.setCellWidget(row, progress_col, progress_bar)
                    progress_bar.setValue(progress)
                    app_signals.append_log.emit(f"[Files] Progress updated for {Path(file_path).name}: {progress}%")
                    return
            logger.debug(f"File {file_path} not found for progress update, reloading table")
            self._load_files_with_logging()
            self.filter_table(self.search_bar.text())
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            app_signals.append_log.emit(f"[Files] Failed to update progress: {str(e)}")

    def open_with_photoshop(self, file_path):
        """Dynamically find Adobe Photoshop path and open the specified file."""
        try:
            import platform
            import subprocess
            import time
            import logging
            import os
            from pathlib import Path

            logger = logging.getLogger(__name__)
            system = platform.system()
            file_path = str(Path(file_path).resolve())

            if not Path(file_path).exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")

            logger.debug(f"System: {system}, File path: {file_path}")
            photoshop_path = None

            if system == "Windows":
                try:
                    import win32gui
                    import win32con
                    import win32com.client
                    import win32api
                    import win32process
                    import ctypes
                except ImportError as e:
                    raise ImportError("Required pywin32 modules not found. Run: pip install pywin32") from e

                photoshop_path = os.getenv("PHOTOSHOP_PATH")
                if photoshop_path and Path(photoshop_path).exists():
                    logger.debug(f"Using Photoshop path from PHOTOSHOP_PATH: {photoshop_path}")
                else:
                    search_dirs = [
                        Path("C:/Program Files/Adobe"),
                        Path("C:/Program Files (x86)/Adobe")
                    ]
                    for base_dir in search_dirs:
                        if not base_dir.exists():
                            logger.debug(f"Search directory does not exist: {base_dir}")
                            continue
                        photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                        if photoshop_exes:
                            photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                            photoshop_path = str(photoshop_exes[0])
                            logger.debug(f"Found Photoshop at: {photoshop_path}")
                            break
                    if not photoshop_path:
                        raise FileNotFoundError("Adobe Photoshop executable not found in Program Files")

                if not os.access(photoshop_path, os.X_OK):
                    raise PermissionError(f"Photoshop executable is not accessible: {photoshop_path}")

                com_success = False
                try:
                    logger.debug("Attempting to open via COM")
                    ps_app = win32com.client.Dispatch("Photoshop.Application")
                    ps_app.Visible = True
                    ps_app.Open(file_path)

                    def bring_to_front(title_contains="Adobe Photoshop"):
                        def enum_handler(hwnd, _):
                            if win32gui.IsWindowVisible(hwnd):
                                title = win32gui.GetWindowText(hwnd)
                                if title_contains.lower() in title.lower():
                                    try:
                                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                        fg_thread = win32process.GetWindowThreadProcessId(
                                            win32gui.GetForegroundWindow())[0]
                                        target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
                                        this_thread = win32api.GetCurrentThreadId()
                                        if ctypes.windll.user32.AttachThreadInput(this_thread, target_thread, True):
                                            win32gui.SetForegroundWindow(hwnd)
                                            ctypes.windll.user32.AttachThreadInput(this_thread, target_thread, False)
                                    except Exception as e:
                                        logger.debug(f"Window activation failed: {e}")
                        win32gui.EnumWindows(enum_handler, None)

                    time.sleep(1.5)
                    bring_to_front()
                    logger.info(f"Opened {Path(file_path).name} via COM")
                    print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                    com_success = True
                except Exception as e:
                    logger.debug(f"COM attempt failed: {e}. Falling back to subprocess.")

                if not com_success:
                    for attempt in range(3):
                        try:
                            cmd = [photoshop_path, file_path]
                            logger.debug(f"Executing subprocess command: {cmd}")
                            result = subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
                            time.sleep(2)
                            def enum_windows_callback(hwnd, hwnds):
                                if win32gui.IsWindowVisible(hwnd) and 'Adobe Photoshop' in win32gui.GetWindowText(hwnd):
                                    hwnds.append(hwnd)
                            hwnds = []
                            win32gui.EnumWindows(enum_windows_callback, hwnds)
                            if hwnds:
                                win32gui.ShowWindow(hwnds[0], win32con.SW_RESTORE)
                                win32gui.SetForegroundWindow(hwnds[0])
                            logger.info(f"Opened {Path(file_path).name} via subprocess")
                            print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                            break
                        except subprocess.CalledProcessError as e:
                            if attempt < 2:
                                logger.debug(f"Subprocess attempt {attempt+1} failed: {e}, stderr: {e.stderr}. Retrying...")
                                time.sleep(2)
                            else:
                                logger.debug(f"Subprocess failed after retries: {e}, stderr: {e.stderr}")
                                try:
                                    process = subprocess.Popen([photoshop_path, file_path], stderr=subprocess.PIPE, text=True)
                                    time.sleep(2)
                                    def enum_windows_callback(hwnd, hwnds):
                                        if win32gui.IsWindowVisible(hwnd) and 'Adobe Photoshop' in win32gui.GetWindowText(hwnd):
                                            hwnds.append(hwnd)
                                    hwnds = []
                                    win32gui.EnumWindows(enum_windows_callback, hwnds)
                                    if hwnds:
                                        win32gui.ShowWindow(hwnds[0], win32con.SW_RESTORE)
                                        win32gui.SetForegroundWindow(hwnds[0])
                                    logger.info(f"Opened {Path(file_path).name} via Popen fallback")
                                    print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                                except Exception as e2:
                                    raise RuntimeError(f"Failed to open file after 3 attempts: {e}, Popen fallback failed: {e2}")

            elif system == "Darwin":
                custom_path = os.getenv("PHOTOSHOP_PATH")
                if custom_path and Path(custom_path).exists():
                    photoshop_path = str(Path(custom_path).resolve())
                    logger.debug(f"Found Photoshop via environment variable: {photoshop_path}")

                if not photoshop_path:
                    try:
                        result = subprocess.run(
                            ["mdfind", "kMDItemKind == 'Application' && (kMDItemFSName == 'Adobe Photoshop*.app' || kMDItemFSName == 'Photoshop*.app' || kMDItemFSName == 'Adobe*Photoshop*.app')"],
                            capture_output=True, text=True, check=True
                        )
                        if result.stdout.strip():
                            photoshop_path = result.stdout.strip().split("\n")[0]
                            logger.debug(f"Found Photoshop via mdfind: {photoshop_path}")
                    except subprocess.CalledProcessError as e:
                        logger.debug(f"mdfind failed with error: {e}, stderr: {e.stderr}")

                if not photoshop_path:
                    search_locations = [
                        Path("/Applications"),
                        Path("~/Applications").expanduser(),
                        Path("/Applications/Adobe Creative Cloud"),
                        Path("~/Applications/Adobe Creative Cloud").expanduser(),
                        Path("/Applications/Adobe"),
                        Path("~/Applications/Adobe").expanduser(),
                        Path("/Applications/Adobe Photoshop*"),
                        Path("~/Applications/Adobe Photoshop*").expanduser(),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop*"),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop*").expanduser(),
                    ]
                    for search_dir in search_locations:
                        if not search_dir.exists():
                            logger.debug(f"Search directory does not exist: {search_dir}")
                            continue
                        logger.debug(f"Searching for Photoshop in: {search_dir}")
                        photoshop_apps = (
                            list(search_dir.glob("Adobe*Photoshop*.app")) +
                            list(search_dir.glob("Photoshop*.app")) +
                            list(search_dir.glob("*/Adobe*Photoshop*.app"))
                        )
                        if photoshop_apps:
                            logger.debug(f"Found potential Photoshop apps: {[str(app) for app in photoshop_apps]}")
                            photoshop_apps.sort(key=lambda x: x.name, reverse=True)
                            photoshop_path = str(photoshop_apps[0])
                            logger.debug(f"Selected Photoshop via glob in {search_dir}: {photoshop_path}")
                            break

                if not photoshop_path:
                    versioned_paths = [
                        Path("/Applications/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2025/Adobe Photoshop 2025.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2025/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2024/Adobe Photoshop 2024.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2024/Adobe Photoshop.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2023/Adobe Photoshop 2023.app"),
                        Path("/Applications/Adobe/Adobe Photoshop 2023/Adobe Photoshop.app"),
                        Path("~/Applications/Adobe Photoshop 2025/Adobe Photoshop 2025.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2025/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2024/Adobe Photoshop 2024.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2024/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app").expanduser(),
                        Path("~/Applications/Adobe Photoshop 2023/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop 2025.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2025/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop 2024.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2024/Adobe Photoshop.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop 2023.app").expanduser(),
                        Path("~/Applications/Adobe Creative Cloud/Adobe Photoshop 2023/Adobe Photoshop.app").expanduser(),
                    ]
                    for path in versioned_paths:
                        if path.exists():
                            photoshop_path = str(path)
                            logger.debug(f"Found Photoshop in versioned path: {photoshop_path}")
                            break

                if not photoshop_path and hasattr(self, 'window'):
                    from PySide6.QtWidgets import QFileDialog
                    logger.debug("Prompting user to select Photoshop application")
                    photoshop_path, _ = QFileDialog.getOpenFileName(
                        self.window(), "Locate Adobe Photoshop", "/Applications", "Applications (*.app)"
                    )
                    if photoshop_path:
                        logger.debug(f"User-selected Photoshop path: {photoshop_path}")
                    else:
                        logger.debug("User cancelled Photoshop path selection")

                if not photoshop_path:
                    error_msg = (
                        "Adobe Photoshop application not found in /Applications, ~/Applications, "
                        "Adobe Creative Cloud, or Adobe directories. Please set PHOTOSHOP_PATH environment variable."
                    )
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

                for attempt in range(3):
                    try:
                        subprocess.run(["open", "-a", photoshop_path, file_path], check=True)
                        applescript = f'tell application "{Path(photoshop_path).name}" to activate'
                        subprocess.run(["osascript", "-e", applescript], check=True)
                        logger.info(f"Opened {Path(file_path).name} via open -a at {photoshop_path}")
                        print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                        break
                    except subprocess.CalledProcessError as e:
                        if attempt < 2:
                            logger.debug(f"Attempt {attempt+1} failed: {e}. Retrying...")
                            time.sleep(2)
                        else:
                            raise RuntimeError(f"Failed to open file after 3 attempts: {e}")

            elif system == "Linux":
                try:
                    subprocess.run(["wine", "--version"], capture_output=True, check=True)
                    wine_dirs = [
                        Path.home() / ".wine/drive_c/Program Files/Adobe",
                        Path.home() / ".wine/drive_c/Program Files (x86)/Adobe"
                    ]
                    for base_dir in wine_dirs:
                        if not base_dir.exists():
                            continue
                        photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                        if photoshop_exes:
                            photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                            photoshop_path = str(photoshop_exes[0])
                            break
                    if not photoshop_path:
                        raise FileNotFoundError("Photoshop.exe not found in Wine directories")

                    for attempt in range(3):
                        try:
                            subprocess.run(["wine", photoshop_path, file_path], check=True)
                            try:
                                subprocess.run(["wmctrl", "-a", "Adobe Photoshop"], check=False)
                            except Exception as e:
                                logger.debug(f"Could not raise Photoshop window: {e}")
                            logger.info(f"Opened {Path(file_path).name} via wine")
                            print(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
                            break
                        except subprocess.CalledProcessError as e:
                            if attempt < 2:
                                logger.debug(f"Attempt {attempt+1} failed: {e}. Retrying...")
                                time.sleep(2)
                            else:
                                raise RuntimeError(f"Failed to open file after 3 attempts: {e}")
                except subprocess.CalledProcessError:
                    raise FileNotFoundError("Wine is not installed or not functioning")

            else:
                error_message = f"Unsupported platform for Photoshop: {system}"
                logger.warning(error_message)
                print(f"[Photoshop] {error_message}")
                raise ValueError(error_message)

        except Exception as e:
            error_message = f"Failed to open {Path(file_path).name} in Photoshop: {str(e)}"
            logger.error(error_message)
            print(f"[Photoshop] {error_message}")
            raise

    def open_folder(self, file_path):
        """Open the folder containing the file."""
        try:
            folder_path = str(Path(file_path).parent)
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", folder_path], check=True)
            elif system == "Darwin":
                subprocess.run(["open", folder_path], check=True)
            elif system == "Linux":
                subprocess.run(["xdg-open", folder_path], check=True)
            else:
                logger.warning(f"Unsupported platform for opening folder: {system}")
                app_signals.append_log.emit(f"[Folder] Unsupported platform for opening folder: {system}")
                app_signals.update_status.emit(f"Unsupported platform for opening folder: {system}")
                return
            app_signals.update_status.emit(f"Opened folder for {Path(file_path).name}")
            app_signals.append_log.emit(f"[Folder] Opened folder for {Path(file_path).name}")
        except Exception as e:
            logger.error(f"Failed to open folder {file_path}: {e}")
            app_signals.append_log.emit(f"[Folder] Failed to open folder: {str(e)}")
            app_signals.update_status.emit(f"Failed to open folder for {Path(file_path).name}: {str(e)}")

    def copy_file_to_clipboard(self, file_path):
        """Copy the file path to the clipboard."""
        try:
            file_path = os.path.join(BASE_TARGET_DIR, file_path)
            if not os.path.exists(file_path):
                raise FileNotFoundError(file_path)

            system = platform.system()
            if system == "Windows":
                import pyautogui
                import ctypes
                import pygetwindow as gw

            folder, filename = os.path.split(os.path.abspath(file_path))
            if system == "Windows":
                SW_SHOWNOACTIVATE = 4
                ctypes.windll.shell32.ShellExecuteW(None, "open", folder, None, None, SW_SHOWNOACTIVATE)
            elif system == "Darwin":
                subprocess.run(["open", folder])
            else:
                raise NotImplementedError(f"Unsupported OS: {system}")

            time.sleep(0.1)
            pyautogui.typewrite(filename)
            time.sleep(0.1)

            if system == "Windows":
                pyautogui.hotkey('ctrl', 'c')
                pyautogui.hotkey('alt', 'f4')
            elif system == "Darwin":
                pyautogui.hotkey('command', 'c')
                pyautogui.hotkey('command', 'w')
            else:
                raise NotImplementedError(f"Copy not supported on {system}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Cleanup or final steps executed.")

    def retry_file_process(self, meta_data_response):
        """Retry a failed file process."""
        print(f"meta_data_response===={meta_data_response}")
        action_type = meta_data_response.get("request_type", "Unknown")
        if action_type == 'download':
            src_path = meta_data_response.get("file_path", "")
            dest_path = os.path.join(BASE_TARGET_DIR, meta_data_response.get("nas_path", ""))
            is_nas_src = True
            is_nas_dest = False
            print(f"===={src_path}==={dest_path}===={action_type}========{is_nas_src}=========={is_nas_dest}=======")
        if action_type == 'upload':
            dest_path = meta_data_response.get("file_path", "")
            src_path = os.path.join(BASE_TARGET_DIR, meta_data_response.get("nas_path", ""))
            is_nas_src = False
            is_nas_dest = True
        file_worker = FileWatcherWorker.get_instance()

        file_worker.perform_file_transfer(
            src_path,
            dest_path,
            action_type,
            meta_data_response,
            is_nas_src,
            is_nas_dest
        )
    
    

# LoginWorker (provided, with fixes)
class LoginWorker(QObject):
    success = Signal(dict, str) 
    failure = Signal(str)
    user_in_use = Signal(str)
    proceed = None
    switch_login = False
    def __init__(self, username, password, remember_me, tray_icon, status_bar, switch_login):
        super().__init__()
        self.username = username
        self.password = password
        self.rememberme = remember_me
        self.tray_icon = tray_icon
        self.status_bar = status_bar
        self.switch_login = switch_login
        
    def run(self):
        try:
            print("inside_logworker")
            logger.debug("Starting LoginWorker.run")
            app_signals.append_log.emit("[Login] Starting LoginWorker.run")
            logger.debug(f"OAuth request data: {{\n"
                        f"  grant_type: password,\n"
                        f"  username: {self.username},\n"
                        f"  password: {'*' * len(self.password)},\n"
                        f"  client_id: hZBc4VyhUSQgZobyjdVH7ZPk4WRey2BIjqws_UxF5cM,\n"
                        f"  client_secret: crazy-cloud,\n"
                        f"  scope: pm_client\n}}")
            
            if self.status_bar is None:
                logger.warning("Status bar is None, cannot update message")
            else:
                self.status_bar.showMessage("Requesting access token...")
            
            # Create a new session for thread safety
            session = requests.Session()
            payload = {
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "client_id": "hZBc4VyhUSQgZobyjdVH7ZPk4WRey2BIjqws_UxF5cM",
                    "client_secret": "crazy-cloud",
                    "scope": "pm_client",
                    "details": USER_SYSTEM_INFO.get("details", {}),
                    "machine_id": USER_SYSTEM_INFO.get("encoded_mac", ""),
                    "mac_address": USER_SYSTEM_INFO.get("mac_address", ""),
                    "add_mac": 1 if self.switch_login else 0

                }
            print(f"payload of login {payload}")
            token_resp = session.post(
                OAUTH_URL,
                data = payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=False,  # Enable SSL verification
                timeout=60
            )
            self.switch_login = False
            
            logger.debug(f"Token response raw: {token_resp.text}")
            app_signals.api_call_status.emit(
                OAUTH_URL,
                f"Status: {token_resp.status_code}, Response: {token_resp.text}",
                token_resp.status_code
            )
            app_signals.append_log.emit(f"[Login] Token API response: {token_resp.status_code}, {token_resp.text}")
            print(f"token_resp.status_code ======== {token_resp.text}")
            if token_resp.status_code == 403:
                self.user_in_use.emit("user_already_logged_in")
                QThread.currentThread().quit()
                return
            if self.status_bar:
                self.status_bar.showMessage(f"Token API response: {token_resp.status_code}")
            if token_resp.status_code in (400, 401):
                try:
                    error_details = token_resp.json()
                    error_msg = f"Bad request: {error_details.get('error_description', token_resp.text)}"
                except ValueError:
                    error_msg = f"Bad request: {token_resp.text}"
                logger.error(f"Token API error: {error_msg}")
                raise Exception(error_msg)
            
            token_resp.raise_for_status()
            token_data = token_resp.json()
            logger.debug(f"Token response JSON: {token_data}")
            access_token = token_data.get("access_token")
            if not access_token:
                raise Exception("No access token received in response")

            if self.status_bar:
                self.status_bar.showMessage("Fetching user info...")
            info_resp = session.get(
                f"{BASE_DOMAIN}/api/user/getinfo?emailid={self.username}",
                headers={"Authorization": f"Bearer {access_token}"},
                verify=False,
                timeout=60
            )
            logger.debug(f"User info response raw: {info_resp.text}")
            app_signals.api_call_status.emit(
                f"{BASE_DOMAIN}/api/user/getinfo?emailid={self.username}",
                f"Status: {info_resp.status_code}, Response: {info_resp.text}",
                info_resp.status_code
            )
            app_signals.append_log.emit(f"[Login] User info API response: {info_resp.status_code}, {info_resp.text}")
            if self.status_bar:
                self.status_bar.showMessage(f"User info API response: {info_resp.status_code}")
            info_resp.raise_for_status()
            user_info = info_resp.json()

            if self.status_bar:
                self.status_bar.showMessage("Fetching user data...")
            user_resp = session.get(
                f"{BASE_DOMAIN}/jsonapi/user/user?filter[name]={self.username}",
                headers={"Authorization": f"Bearer {access_token}"},
                verify=False,
                timeout=60
            )
            logger.debug(f"User data response raw: {user_resp.text}")
            app_signals.api_call_status.emit(
                f"{BASE_DOMAIN}/jsonapi/user/user?filter[name]={self.username}",
                f"Status: {user_resp.status_code}, Response: {user_resp.text}",
                user_resp.status_code
            )
            app_signals.append_log.emit(f"[Login] User data API response: {user_resp.status_code}, {user_resp.text}")
            if self.status_bar:
                self.status_bar.showMessage(f"User data API response: {user_resp.status_code}")
            user_resp.raise_for_status()
            user_data = user_resp.json()

            cache = load_cache() or {}  # Handle case where load_cache returns None
            logger.debug(f"Loaded cache: {cache}")
            print(f"Loaded cacheaaa: {cache}")
            cached_user = cache.get("user")
            cached_token = cache.get("token")

            # if not load_cache() or self.username != load_cache().get("user"):

            # If new user or cache empty → save cache
            if not cached_user or self.username != cached_user:
                logger.debug("New user login or cache empty. Saving full cache data.")
       
                cache_data = {
                    "token": access_token,
                    "user": self.username,
                    "user_id": user_info.get('uid', ''),
                    "user_info": dict(user_info),
                    "info_resp": dict(user_info),
                    "user_data": dict(user_data),
                    "data": self.username,
                    "downloaded_files": cache.get("downloaded_files", []),
                    "uploaded_files": cache.get("uploaded_files", []),
                    "timer_responses": cache.get("timer_responses", {}),
                    "saved_username": self.username if self.rememberme else cache.get("saved_username", ""),
                    "saved_password": self.password if self.rememberme else cache.get("saved_password", ""),
                    "cached_at": datetime.now(ZoneInfo("UTC")).isoformat()
                }
                save_cache(cache_data)
                logger.debug(f"Cache saved: {cache_data}")
                app_signals.append_log.emit(f"[Login] Cache saved for user: {self.username}")

            elif self.username == cached_user and not cached_token:
                # Same user but token empty → only update token
                logger.debug("Same user re-login detected. Updating token only.")
                cache["token"] = access_token
                cache["cached_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
                save_cache(cache)
                logger.debug(f"[Login] Token updated for user: {self.username}")

            
            logger.debug("Emitting success signal")
            self.success.emit(user_info, access_token)
            app_signals.append_log.emit(f"[Login] Successful login for user: {self.username}")
            if self.status_bar:
                self.status_bar.showMessage(f"Successful login for {self.username}")
        
        except requests.exceptions.SSLError as e:
            error_msg = f"SSL error: {str(e)}"
            logger.error(error_msg)
            self.failure.emit(error_msg)
            app_signals.append_log.emit(f"[Login] Failed: {error_msg}")
            if self.status_bar:
                self.status_bar.showMessage(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            self.failure.emit(error_msg)
            app_signals.append_log.emit(f"[Login] Failed: {error_msg}")
            if self.status_bar:
                self.status_bar.showMessage(error_msg)
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timed out: {str(e)}"
            logger.error(error_msg)
            self.failure.emit(error_msg)
            app_signals.append_log.emit(f"[Login] Failed: {error_msg}")
            if self.status_bar:
                self.status_bar.showMessage(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            self.failure.emit(error_msg)
            app_signals.append_log.emit(f"[Login] Failed: {error_msg}")
            if self.status_bar:
                self.status_bar.showMessage(error_msg)
        except Exception as e:
            error_msg = f"Login error: {str(e)}"
            logger.error(error_msg)
            self.failure.emit(error_msg)
            app_signals.append_log.emit(f"[Login] Failed: {error_msg}")
            if self.status_bar:
                self.status_bar.showMessage(error_msg)
        
        
    
    def switch_user_here(self):
        try:
            session = requests.Session()
            token_resp_validation = session.post(
                OAUTH_URL,
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "client_id": "hZBc4VyhUSQgZobyjdVH7ZPk4WRey2BIjqws_UxF5cM",
                    "client_secret": "crazy-cloud",
                    "scope": "pm_client",
                    "details": USER_SYSTEM_INFO.get("details", {}),
                    "machine_id": USER_SYSTEM_INFO.get("encoded_mac", ""),
                    "mac_address": USER_SYSTEM_INFO.get("mac_address", ""),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=False,  # Enable SSL verification
                timeout=60
            )
            logger.debug(f"Token response raw: {token_resp_validation.text}")
            app_signals.api_call_status.emit(
                OAUTH_URL,
                f"Status: {token_resp_validation.status_code}, Response: {token_resp_validation.text}",
                token_resp_validation.status_code
            )
            app_signals.append_log.emit(f"[Login] Token API response: {token_resp_validation.status_code}, {token_resp_validation.text}")    
            if self.status_bar:
                self.status_bar.showMessage(f"Token API response: {token_resp_validation.status_code}")
            if token_resp_validation.status_code in (400, 401):
                try:
                    error_details = token_resp_validation.json()
                    error_msg = f"Bad request: {error_details.get('error_description', token_resp_validation.text)}"
                except ValueError:
                    error_msg = f"Bad request: {token_resp_validation.text}"
                logger.error(f"Token API error: {error_msg}")
                return False
            return token_resp_validation
        except:
            return False

class LoginDialog(QDialog):
    login_success = Signal(dict, str)
    login_failure = Signal(str)
    login_clicked = Signal(str, str)
    user_in_other_system = Signal(str)
    switch_login = False
    LoginDialog_USERNAME = ''
    LoginDialog_PASSWORD = ''
    def __init__(self, parent=None, app=None):
        try:
            from PySide6.QtWidgets import QWidget
            if parent is not None and not isinstance(parent, QWidget):
                logger.warning(f"Invalid parent type {type(parent).__name__}, setting parent to None")
                app_signals.append_log.emit(f"[Login] Warning: Invalid parent type {type(parent).__name__}, setting parent to None")
                parent = None

            self.app = app
            logger.debug(f"Initializing LoginDialog with parent={parent}, app={app}")
            super().__init__(parent)
            self.is_logged_in = False

            if traceback:
                logger.debug(f"Call stack:\n{''.join(traceback.format_stack()[:-1])}")
            else:
                logger.warning("traceback module not available, skipping stack trace")
                app_signals.append_log.emit("[Login] Warning: traceback module not available, skipping stack trace")

            self.setWindowIcon(load_icon(ICON_PATH, "login dialog"))
            self.setWindowTitle("PremediaApp Login")
            self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

            self.ui = Ui_Dialog()
            self.ui.setupUi(self)

            self.status_bar = QStatusBar()
            self.status_bar.setSizeGripEnabled(False)
            self.status_bar.setFixedHeight(20)
            self.status_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

            main_layout = QVBoxLayout()
            main_layout.addStretch(1)
            main_layout.addWidget(self.status_bar, stretch=0)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(5)
            self.setLayout(main_layout)
            add_version_footer(self, APPVERSION)

            cache = load_cache()
            token = cache.get("token")
            user_id = cache.get("user_id")
            name = cache.get("user_data", {}).get("data", [{}])[0].get("attributes", {}).get("name", cache.get("user_info", {}).get("mail", "user"))
            user_info = {
                "uid": user_id,
                "name": name,
                "mail": cache.get("user_info", {}).get("mail", "user"),  
                "access_key": cache.get("user_info", {}).get("access_key")
            }
            # if token and user_id:
            #     logger.info(f"Auto-login from cache for user: {user_id}")
            #     app_signals.append_log.emit(f"[Login] Auto-login from cache for user: {user_id}")
            #     QTimer.singleShot(100, lambda: self.on_login_success(user_info, token))
            # else:
            #     app_signals.append_log.emit("[Login] No valid cache for auto-login")


            if token and user_id:
                logger.info(f"Attempting auto-login from cache for user: {user_id}")
                app_signals.append_log.emit(f"[Login] Attempting auto-login from cache for user: {user_id}")

                # Get access_key from cached user_info
                access_key = user_info.get("access_key")

                # Validate cached token/access_key
                validation_result = validate_user(access_key, status_bar=self.status_bar)
                
                if validation_result.get("status") == 403:
                    
                    self.user_in_other_system.emit("user_already_logged_in")
                    # QThread.currentThread().quit()
                    return

                if validation_result.get("uuid"):
                    # Token valid, schedule login success
                    QTimer.singleShot(300, lambda: self.on_login_success(user_info, token))
                    # print('-------------------------------------------------')
                    # print(f"Auto-login scheduled for user: {user_id}")
                    app_signals.append_log.emit(f"[Login] Auto-login scheduled for user: {user_id}")
                else:
                    # Token invalid, call existing on_login_failed
                    error_msg = "Cached login expired, please log in manually"
                    # print("=================================================")
                    # print(f"{error_msg} for user: {user_id}")
                    app_signals.append_log.emit(f"[Login] Cached token invalid for user: {user_id}")
                    self.status_bar.showMessage(error_msg)

                    # Call your existing on_login_failed (dialog remains open)
                    QTimer.singleShot(100, lambda: self.on_login_failed(error_msg))

            if cache.get("saved_username") and cache.get("saved_password"):
                self.ui.usernametxt.setText(cache["saved_username"])
                self.ui.passwordtxt.setText(cache["saved_password"])
                self.ui.rememberme.setChecked(True)
                app_signals.append_log.emit("[Login] Loaded saved credentials from cache")
                self.status_bar.showMessage("Loaded saved credentials")
            else:
                app_signals.append_log.emit("[Login] No saved credentials found in cache")
                self.status_bar.showMessage("No saved credentials found")

            app_signals.update_status.connect(self.status_bar.showMessage, Qt.QueuedConnection)
            self.ui.buttonBox.accepted.connect(self.handle_login)
            print(f"---------handle")
            self.progress = None
            self.thread = None
            logger.debug("[Login] LoginDialog initialized")
            app_signals.append_log.emit("[Login] Initializing LoginDialog")
            self.status_bar.showMessage("Login dialog initialized")

            self.resize(764, 669)
        except Exception as e:
            logger.error(f"Failed to initialize LoginDialog: {e}")
            app_signals.append_log.emit(f"[Login] Failed to initialize LoginDialog: {str(e)}")
            QMessageBox.critical(None, "Initialization Error", f"Failed to initialize login dialog: {str(e)}")
            raise

    def show_progress(self, message):
        try:
            if self.progress and self.progress.isVisible():
                logger.debug(f"Progress dialog already visible, updating message to: {message}")
                self.progress.setLabelText(message)
                QApplication.processEvents()
                return

            self.progress = QProgressDialog(message, None, 0, 0, self)
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.setCancelButton(None)
            self.progress.setMinimumDuration(0)
            self.progress.setWindowTitle("Please wait")
            self.progress.setWindowIcon(load_icon(ICON_PATH, "progress dialog"))
            self.progress.show()
            QApplication.processEvents()
            logger.debug(f"Progress dialog shown: {message}, visible={self.progress.isVisible()}")
            app_signals.append_log.emit(f"[Login] Showing progress: {message}")
            self.status_bar.showMessage(message)
        except Exception as e:
            logger.error(f"Progress dialog error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Progress dialog error - {str(e)}")
            self.status_bar.showMessage(f"Progress error: {str(e)}")
            QMessageBox.critical(self, "Progress Error", f"Progress dialog error: {str(e)}")

    def handle_login(self):
        try:
            logger.debug("handle_login called")
            username = self.ui.usernametxt.text().strip()
            password = self.ui.passwordtxt.text().strip()
            logger.debug(f"Login attempt with username: {username}, rememberme: {self.ui.rememberme.isChecked()}")
            app_signals.append_log.emit(f"[Login] Attempting login with username: {username}")
            self.status_bar.showMessage(f"Attempting login for {username}")
            if not username or not password:
                QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
                app_signals.append_log.emit("[Login] Failed: Missing username or password")
                self.status_bar.showMessage("Missing username or password")
                return
            self.show_progress("Validating credentials...")
            self.perform_login(username, password)
        except Exception as e:
            logger.error(f"Error in handle_login: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Handle login error - {str(e)}")
            self.status_bar.showMessage(f"Login error: {str(e)}")
            if self.progress:
                self.progress.close()
            QMessageBox.critical(self, "Login Error", f"Login error: {str(e)}")

    def perform_login(self, username, password):
        try:
            self.LoginDialog_USERNAME = username
            self.LoginDialog_PASSWORD = password
            logger.debug("Starting login thread")
            self.thread = QThread()
            tray_icon = getattr(self.parent(), 'tray_icon', None)
            self.worker = LoginWorker(username, password, self.ui.rememberme.isChecked(), tray_icon=tray_icon, status_bar=self.status_bar, switch_login=self.switch_login)
            self.switch_login = False
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.success.connect(self.on_login_success)
            # self.worker.user_in_use.connect(lambda: self.validate_account_already_inuse(username, password), Qt.QueuedConnection)
            self.worker.user_in_use.connect(self.validate_account_already_inuse)
            self.worker.failure.connect(self.on_login_failed)
            self.worker.success.connect(self.thread.quit)
            self.worker.failure.connect(self.thread.quit)
            self.worker.success.connect(self.worker.deleteLater)
            self.worker.failure.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(lambda: self.cleanup_progress())  # Clean up progress dialog
            self.thread.start()
            app_signals.append_log.emit(f"[Login] Starting login thread for user: {username}")
            self.status_bar.showMessage(f"Starting login for {username}")
        except Exception as e:
            logger.error(f"Login thread error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Login thread error - {str(e)}")
            self.status_bar.showMessage(f"Login thread error: {str(e)}")
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()
                logger.debug("Progress dialog closed in perform_login error handler")
                app_signals.append_log.emit("[Login] Progress dialog closed in error handler")
            QMessageBox.critical(self, "Login Error", f"Login thread error: {str(e)}")

    def cleanup_progress(self):
        try:
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()
                logger.debug("Progress dialog closed in cleanup_progress")
                app_signals.append_log.emit("[Login] Progress dialog closed in cleanup_progress")
        except Exception as e:
            logger.error(f"Error in cleanup_progress: {str(e)}")
            app_signals.append_log.emit(f"[Login] Failed: Error in cleanup_progress - {str(e)}")

    def validate_account_already_inuse(self):
        print("in validate_account_already_inuse")

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Account In Use")
        msg_box.setText("You are already logged in on another device.\nDo you want to switch this session here?")
        msg_box.setIcon(QMessageBox.Warning)
        switch_btn = msg_box.addButton("Switch Here", QMessageBox.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        # Apply red color only to Cancel button
        switch_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;   /* Red background */
                color: white;
                border-radius: 4px;
                padding: 2px;
            }
        """)


        # --- Block here until user clicks ---
        msg_box.exec()

        if msg_box.clickedButton() == switch_btn:
            print("User chose to switch session.")
            self.switch_login = True
        else:
            print("User cancelled.")
            self.switch_login = False
        print(f"self.LoginDialog_USERNAME={self.LoginDialog_USERNAME}===self.LoginDialog_PASSWORD{self.LoginDialog_PASSWORD}")
        if self.switch_login:
            self.perform_login(self.LoginDialog_USERNAME, self.LoginDialog_PASSWORD)
 
    def on_login_success(self, user_info: dict, token: str):
        try:
            logger.info(f"Login successful for user_id: {user_info['uid']}")
            app_signals.append_log.emit(f"[App] Login successful for user_id: {user_info['uid']}")
            self.is_logged_in = True
            user_name = user_info.get('name', user_info.get('mail', 'user'))
            # Update parent (PremediaApp) state
            if hasattr(self, 'app') and self.app:
                self.app.set_logged_in_state()
                self.app.start_file_watcher()
                logger.debug("Updated PremediaApp state")
                app_signals.append_log.emit("[Login] Updated PremediaApp state")
            
            # Close progress dialog
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()  # Ensure close is processed
                logger.debug("Progress dialog closed in on_login_success")
                app_signals.append_log.emit("[Login] Progress dialog closed")
            
            # Show success message
            QMessageBox.information(self, "Login Success", f"Successfully logged in as {user_name}")
            
            self.accept()
            app_signals.update_status.emit("Logged in successfully")
            logger.debug("on_login_success completed successfully")
            app_signals.append_log.emit("[Login] on_login_success completed successfully")
        except Exception as e:
            logger.error(f"Error in on_login_success: {str(e)}")
            app_signals.append_log.emit(f"[Login] Failed: Error in on_login_success - {str(e)}")
            app_signals.update_status.emit(f"Login success handling error: {str(e)}")
            # Ensure progress dialog is closed on error
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()
                logger.debug("Progress dialog closed in on_login_success error handler")
                app_signals.append_log.emit("[Login] Progress dialog closed in error handler")
            QMessageBox.critical(self, "Login Error", f"Error handling login success: {str(e)}")



    def on_login_failed(self, error):
        try:
            # Log the failure
            logger.error(f"Login failed: {error}")
            app_signals.append_log.emit(f"[App] Login failed: {error}")
            app_signals.update_status.emit(f"Login failed: {error}")

            # Close progress dialog if open
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()
                logger.debug("Progress dialog closed in on_login_failed")
                app_signals.append_log.emit("[Login] Progress dialog closed")

            # Show error popup
            QMessageBox.critical(self, "Login Error", str(error))

            # Update parent (PremediaApp) to logged-out state and refresh tray menu
            if hasattr(self, 'app') and self.app:
                # Ensure logged_in = False and clear cached user info
                self.app.set_logged_out_state()  # Updates tray menu to logged-out state

                # Open login dialog again after a short delay to ensure tray updates
                QTimer.singleShot(100, lambda: self.app.show_login())

        except Exception as e:
            logger.error(f"Error in on_login_failed: {str(e)}")
            app_signals.append_log.emit(f"[Login] Failed: Error in on_login_failed - {str(e)}")
            app_signals.update_status.emit(f"Error in on_login_failed: {str(e)}")

            # Ensure progress dialog is closed on error
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()
                logger.debug("Progress dialog closed in on_login_failed error handler")
                app_signals.append_log.emit("[Login] Progress dialog closed in error handler")



    def on_login_failed(self, error):
        try:
            logger.error(f"Login failed: {error}")
            app_signals.append_log.emit(f"[App] Login failed: {error}")
            app_signals.update_status.emit(f"Login failed: {error}")

            # Close progress dialog
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()
                logger.debug("Progress dialog closed in on_login_failed")
                app_signals.append_log.emit("[Login] Progress dialog closed")

            # Show error popup
            QMessageBox.critical(self, "Login Error", str(error))

            # Update parent (PremediaApp) to logged-out state and show login form
            if hasattr(self, 'app') and self.app:
                self.app.set_logged_out_state()  # Set tray menu/logged-out state
                QTimer.singleShot(100, lambda: self.app.show_login())  # Open login dialog again

        except Exception as e:
            logger.error(f"Error in on_login_failed: {str(e)}")
            app_signals.append_log.emit(f"[Login] Failed: Error in on_login_failed - {str(e)}")
            app_signals.update_status.emit(f"Error in on_login_failed: {str(e)}")
            if self.progress and self.progress.isVisible():
                self.progress.close()
                QApplication.processEvents()
                logger.debug("Progress dialog closed in on_login_failed error handler")
                app_signals.append_log.emit("[Login] Progress dialog closed in error handler")


    def closeEvent(self, event):
        try:
            if app_signals.update_status.isSignalConnected(self.status_bar.showMessage):
                app_signals.update_status.disconnect(self.status_bar.showMessage)
        except Exception as e:
            logger.debug(f"Failed to disconnect update_status signal: {e}")
            app_signals.append_log.emit(f"[Login] Failed to disconnect update_status signal: {str(e)}")
        super().closeEvent(event)
  
  

def check_single_instance():
    pid_dir = tempfile.gettempdir()
    try:
        with PidFile(piddir=pid_dir, pidname='premedia_app.pid'):
            logger.info(f"Acquired lock for PID {os.getpid()}")
            return True
    except PidFileError:
        logger.error(f"Another instance of PremediaApp is running (PID file exists)")
        print("Another instance of PremediaApp is already running")
        sys.exit(1)


class PremediaApp(QApplication):
    
    def __init__(self, key="e0d6aa4baffc84333faa65356d78e439"):
        try:
            super().__init__(sys.argv)
            self.setQuitOnLastWindowClosed(False)
            self.setWindowIcon(load_icon(ICON_PATH, "application"))
            self.CACHE_FILE = CACHE_FILE
            # Prevent multiple instances using a lock file
            self.lock_file = os.path.join(tempfile.gettempdir(), "premedia_app.lock")
            try:
                self.lock_fd = open(self.lock_file, 'w')
            except IOError:
                logger.error("Another instance of PremediaApp is already running")
                app_signals.append_log.emit("[Init] Failed: Another instance of PremediaApp is already running")
                sys.exit(1)

            # Initialize system tray icon
            self.tray_icon = None
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(load_icon(ICON_PATH, "system tray"))
                self.tray_icon.setToolTip("PremediaApp")
                self.tray_icon.activated.connect(self.handle_tray_icon_activated)
                self.tray_icon.show()
                QApplication.processEvents()
                logger.info(f"System tray icon initialized, visible: {self.tray_icon.isVisible()}")
                app_signals.append_log.emit(f"[Init] System tray icon initialized, visible: {self.tray_icon.isVisible()}")
            else:
                logger.warning("System tray not available")
                app_signals.append_log.emit("[Init] System tray not available")

            self.logged_in = False
            load_cache()

            # Set up tray menu
            self.tray_menu = QMenu()
            self.login_action = QAction("Login")
            self.logout_action = QAction("Logout")
            self.quit_action = QAction("Quit")
            self.log_action = QAction("View Log Window")
            self.downloaded_files_action = QAction("Downloaded Files")
            self.uploaded_files_action = QAction("Uploaded Files")
            self.clear_cache_action = QAction("Clear Cache")
            self.open_cache_action = QAction("Open Cache File")
            self.tray_menu.addAction(self.log_action)
            self.tray_menu.addAction(self.downloaded_files_action)
            self.tray_menu.addAction(self.uploaded_files_action)
            self.tray_menu.addAction(self.open_cache_action)
            self.tray_menu.addAction(self.login_action)
            self.tray_menu.addAction(self.logout_action)
            self.tray_menu.addAction(self.clear_cache_action)
            self.tray_menu.addAction(self.quit_action)
            if self.tray_icon:
                self.tray_icon.setContextMenu(self.tray_menu)
                # Remove redundant show() call
                QApplication.processEvents()

            # Connect actions to slots
            self.login_action.triggered.connect(self.show_login)
            self.logout_action.triggered.connect(self.logout)
            self.quit_action.triggered.connect(self.cleanup_and_quit)
            self.log_action.triggered.connect(self.show_logs)
            self.downloaded_files_action.triggered.connect(self.show_downloaded_files)
            self.uploaded_files_action.triggered.connect(self.show_uploaded_files)
            self.clear_cache_action.triggered.connect(self.clear_cache)
            self.open_cache_action.triggered.connect(self.open_cache_file)

            self.log_window = LogWindow()
            self.downloaded_files_window = None
            self.uploaded_files_window = None
            try:
                self.login_dialog = LoginDialog(parent=None, app=self)   
                self.login_dialog.user_in_other_system.connect(self.show_login_page)
                             
            except Exception as e:
                logger.error(f"Failed to initialize LoginDialog: {e}")
                app_signals.append_log.emit(f"[Init] Failed to initialize LoginDialog: {str(e)}")
                self.login_dialog = None
                QMessageBox.critical(None, "Initialization Error", f"Failed to initialize login dialog: {str(e)}")
                self.cleanup_and_quit()
                return

            # Connect signals to log window
            try:
                app_signals.update_status.disconnect(self.log_window.handle_update_status)
            except Exception:
                logger.debug("No existing update_status connection to disconnect")
            app_signals.update_status.connect(self.log_window.status_bar.showMessage, Qt.QueuedConnection)
            setup_logger(self.log_window)

            if not log_thread.is_alive():
                log_thread.start()

            logger.debug(f"Initializing with key: {key[:8]}...")
            app_signals.append_log.emit(f"[Init] Initializing with key: {key[:8]}...")
            cache = load_cache()
            logger.debug(f"Cache contents: {json.dumps(cache, indent=2)}")
            app_signals.append_log.emit(f"[Init] Cache contents: {json.dumps(cache, indent=2)}")
            #cache validation
            
            cache_created_ts = cache.get("created_at")  # Unix timestamp
            logger.debug(f"[TEST] Cache created_at: {cache_created_ts}")
            app_signals.append_log.emit(f"[TEST] Cache created_at: {cache_created_ts}")

            print(f"cache_created_ts:{cache_created_ts}")

            if cache_created_ts:
                try:
                    print('working fine')
                    cache_created = datetime.fromtimestamp(cache_created_ts, tz=timezone.utc)
                    now = datetime.now(timezone.utc)
                    age_days = (now - cache_created).days
                    logger.debug(f"[TEST] Cache created_at: {cache_created_ts}")
                    app_signals.append_log.emit(f"[TEST] Cache created_at: {cache_created_ts}")
                    print('now:', now)
                    print('cache_created:', cache_created)
                    print('timedelta(days=7):', timedelta(days=7))
                    if now - cache_created > timedelta(days=7):
                    # if now - cache_created > timedelta(minutes=1):
                        logger.info("Cache is older than 7 days. Clearing cache...")
                        app_signals.append_log.emit("[Init] Cache is older than 7 days. Clearing cache...")
                        self.clear_cache()  # Make sure your clear_cache() resets CACHE_FILE too
                        cache = {}  # Reset cache variable
                    else:
                        logger.debug(f"Cache is valid. Age: {(now - cache_created).days} days")
                        print("Cache is valid. Age:", (now - cache_created).days, "days")
                        app_signals.append_log.emit(f"[Init] Cache is valid. Age: {(now - cache_created).days} days")
                except Exception as e:
                    logger.error(f"Failed to validate cache date: {e}")
                    app_signals.append_log.emit(f"[Init] Failed to validate cache date: {str(e)}")
                    self.clear_cache()
                    cache = {}
            else:
                logger.debug("No cache creation timestamp found, skipping validation")
                app_signals.append_log.emit("[Init] No cache creation timestamp found, skipping validation")
                



            # Auto-login logic
            if cache.get("token") and cache.get("user") and cache.get("user_id") and not self.logged_in:
                logger.debug("Attempting auto-login with cached credentials")
                app_signals.append_log.emit("[Init] Attempting auto-login with cached credentials")
                user_info = cache.get("user_info", {})
                access_key = user_info.get("access_key", "")
                validation_result = validate_user(access_key, self.log_window.status_bar)
                print(f"Validation result: {validation_result}")
                print("==================================================================")
                if validation_result.get("status") == 403:
                #   
                    self.logout()
                    # self.set_logged_out_state()
                    # self.show_login()
                    # raise
                elif validation_result.get("uuid"):
                    try:
                        info_resp = HTTP_SESSION.get(
                            f"{BASE_DOMAIN}/api/user/getinfo?emailid={cache.get('user')}",
                            headers={"Authorization": f"Bearer {cache.get('token')}"},
                            verify=False,
                            timeout=30
                        )
                        app_signals.api_call_status.emit(
                            f"{BASE_DOMAIN}/api/user/getinfo?emailid={cache.get('user')}",
                            f"Status: {info_resp.status_code}, Response: {info_resp.text}",
                            info_resp.status_code
                        )
                        app_signals.append_log.emit(f"[Init] User info API response: {info_resp.status_code}")
                        info_resp.raise_for_status()
                        user_info = info_resp.json()
                        cache_data = {
                            "token": cache.get("token", ""),
                            "user": cache.get("user", ""),
                            "user_id": user_info.get("uid", cache.get("user_id", "")),
                            "user_info": user_info,
                            "info_resp": validation_result,
                            "user_data": cache.get("user_data", {}),
                            "data": key,
                            "downloaded_files": cache.get("downloaded_files", []),
                            "downloaded_files_with_metadata": cache.get("downloaded_files_with_metadata", {}),
                            "uploaded_files_with_metadata": cache.get("uploaded_files_with_metadata", {}),
                            "uploaded_files": cache.get("uploaded_files", []),
                            "timer_responses": cache.get("timer_responses", {}),
                            "saved_username": cache.get("saved_username", ""),
                            "saved_password": cache.get("saved_password", ""),
                            "cached_at": datetime.now(ZoneInfo("UTC")).isoformat()
                        }
                        save_cache(cache_data)
                        self.set_logged_in_state()
                        logger.debug("Calling start_file_watcher after auto-login")
                        app_signals.append_log.emit("[Init] Calling start_file_watcher after auto-login")
                        self.start_file_watcher()
                        self.log_window.status_bar.showMessage(f"Auto-login successful for {cache.get('user')}")
                        self.post_login_processes()
                        app_signals.append_log.emit("[Init] Auto-login successful with cached credentials")
                    except Exception as e:
                        logger.error(f"Auto-login failed during user info fetch: {e}")
                        app_signals.append_log.emit(f"[Init] Auto-login failed during user info fetch: {str(e)}")
                        self.logout()
                        # self.set_logged_out_state()
                        # self.show_login()
                else:
                    logger.warning(f"Auto-login failed: {validation_result.get('message', 'Unknown error')}")
                    app_signals.append_log.emit(f"[Init] Auto-login failed: {validation_result.get('message', 'Unknown error')}")
                    self.logout()
                    # self.set_logged_out_state()
                    # self.show_login()
            elif cache.get("saved_username") and cache.get("saved_password"):
                logger.debug("Attempting auto-login with saved credentials")
                app_signals.append_log.emit("[Init] Attempting auto-login with saved credentials")
                self.login_dialog.perform_login(cache["saved_username"], cache["saved_password"])
            else:
                logger.debug("No valid cached credentials, showing login dialog")
                app_signals.append_log.emit("[Init] No valid cached credentials, showing login dialog")
                self.set_logged_out_state()
                self.show_login()

            logger.info("PremediaApp initialized")
            app_signals.append_log.emit("[Init] PremediaApp initialized")
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            app_signals.append_log.emit(f"[Init] Failed: Initialization error - {str(e)}")
            if self.login_dialog:
                app_signals.update_status.emit(f"Initialization error: {str(e)}")
                self.show_login()
            else:
                QMessageBox.critical(None, "Initialization Error", f"Failed to initialize application: {str(e)}")
            self.cleanup_and_quit()

    def event(self, event):
        try:
            if event.type() == QEvent.ApplicationActivate:
                logger.debug("Application activated via taskbar/dock")
                app_signals.append_log.emit("[App] Application activated via taskbar/dock")
                for window in [self.log_window, self.downloaded_files_window, self.uploaded_files_window, self.login_dialog]:
                    if window and window.isVisible():
                        window.raise_()
                        window.activateWindow()
                        logger.debug(f"Restored window: {window.windowTitle()}")
                        app_signals.append_log.emit(f"[App] Restored window: {window.windowTitle()}")
            return super().event(event)
        except Exception as e:
            logger.error(f"Error in event handler: {e}")
            app_signals.append_log.emit(f"[App] Failed: Error in event handler - {str(e)}")
            return super().event(event)

    def show_login_page(self):
        self.logout()
        


    def handle_tray_icon_activated(self, reason):
        try:
            system = platform.system().lower()  # "windows", "darwin", "linux"

            if reason == QSystemTrayIcon.Trigger:
                # Left-click: only show menu manually on Windows/Linux
                if system != "darwin":  # Skip on macOS
                    if self.tray_icon.contextMenu():
                        self.tray_icon.contextMenu().popup(QCursor.pos())
                        logger.debug("Tray icon left-click: Showing context menu")
                        app_signals.append_log.emit("[Tray] Left-click: Showing context menu")
                else:
                    logger.debug("Tray icon clicked (macOS auto-handles menu display)")
                    app_signals.append_log.emit("[Tray] macOS: Skipped manual popup")

            elif reason == QSystemTrayIcon.DoubleClick:
                pass  # No action
            elif reason == QSystemTrayIcon.Context:
                pass  # macOS auto-shows menu
            elif reason == QSystemTrayIcon.MiddleClick:
                pass

            app_signals.update_status.emit("Tray icon activated")

        except Exception as e:
            logger.error(f"Error in handle_tray_icon_activated: {e}")
            app_signals.append_log.emit(f"[Tray] Failed: Error handling tray icon activation - {str(e)}")
            app_signals.update_status.emit(f"Error handling tray icon activation: {str(e)}")
            QMessageBox.critical(None, "Tray Icon Error", f"Error handling tray icon activation: {str(e)}")



    def update_tray_menu(self):
        try:
            # Check if system tray is available and tray_icon is initialized
            if not self.tray_icon or not QSystemTrayIcon.isSystemTrayAvailable():
                logger.warning("System tray not available or tray_icon not initialized")
                return

            # Clear the existing tray menu to rebuild it
            self.tray_menu.clear()
            user_fullname = "Unknown"  # Default value

            # Load user full name (with fallback) from cache if logged in
            if self.logged_in:
                try:
                    cache_file = Path(self.CACHE_FILE).resolve()
                    if cache_file.exists() and cache_file.is_file():
                        with cache_file.open('r', encoding='utf-8') as f:
                            cache_data = json.load(f)

                        user_data = cache_data.get('user_data', {}).get('data', [])
                        if user_data and isinstance(user_data, list):
                            attributes = user_data[0].get('attributes', {})

                            # Fallback order: field_fullname → name → mail → "Unknown"
                            user_fullname = (
                                attributes.get('field_fullname')
                                or attributes.get('name')
                                or attributes.get('mail')
                                or "Unknown"
                            )

                            user_fullname = str(user_fullname).strip()
                            if not user_fullname:
                                user_fullname = "Unknown"

                            logger.debug(f"Resolved tray user name: {user_fullname}")
                            app_signals.append_log.emit(f"[Tray] User name resolved: {user_fullname}")
                        else:
                            logger.warning("Cache user_data missing or not a list")
                            user_fullname = "Unknown"
                    else:
                        logger.warning(f"Cache file missing or invalid: {cache_file}")
                        app_signals.append_log.emit(f"[Tray] Cache file missing: {cache_file}")
                        user_fullname = "Unknown"
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Failed to read fullname from cache: {e}")
                    app_signals.append_log.emit(f"[Tray] Failed to read cache: {str(e)}")
                    user_fullname = "Unknown"

            # Clear icon cache to ensure fresh icons are loaded
            ICON_CACHE.clear()
            logger.debug(f"update_tray_menu: self.logged_in = {self.logged_in}")

            # Select platform-specific tray icon based on login status
            tray_icon_name = {
                "Windows": "login-logo.ico" if self.logged_in else "logout-logo.ico",
                "Darwin": "login-logo.icns" if self.logged_in else "logout-logo.icns",
                "Linux": "login-logo.png" if self.logged_in else "logout-logo.png"
            }.get(platform.system(), "logout-logo.png")

            icon_path = get_icon_path(tray_icon_name)

            # Windows-specific workaround to refresh tray icon
            if platform.system() == "Windows":
                dummy_icon_path = get_icon_path("login-logo.png")
                self.tray_icon.setIcon(QIcon(dummy_icon_path))  # Set temporary icon
                QApplication.processEvents()

            # Set the actual tray icon, falling back to default if invalid
            if not Path(icon_path).exists() or QIcon(icon_path).isNull():
                icon_path = get_icon_path("login-logo.png")
            self.tray_icon.setIcon(QIcon(icon_path))
            self.tray_icon.setToolTip(
                f"PremediaApp - {'Logged in as ' + user_fullname if self.logged_in else 'Not logged in'}"
            )
            QApplication.processEvents()

            logger.debug(f"Tray icon updated: {icon_path}, logged_in={self.logged_in}")

            # Helper function to set up action icons with fallback
            def setup_action(action, icon_name, visible=True, enabled=True):
                path = get_icon_path(icon_name)
                if not Path(path).exists() or QIcon(path).isNull():
                    path = get_icon_path("premedia.png")  # Fallback icon
                action.setIcon(QIcon(path))
                action.setVisible(visible)
                action.setEnabled(enabled)

            # Create user info action (always shown when logged in)
            user_icon_name = {
                "Windows": "user_icon.ico",
                "Darwin": "user_icon.icns",
                "Linux": "user_icon.png"
            }.get(platform.system(), "user_icon.png")

            user_action = QAction(f"{user_fullname}", self.tray_menu)
            user_action.setEnabled(False)  # Non-interactive user info
            font = QFont()
            font.setBold(True)
            user_action.setFont(font)
            setup_action(user_action, user_icon_name)

            if self.logged_in:
                self.tray_menu.addAction(user_action)
                self.tray_menu.addSeparator()

            # Set up main actions with platform-specific icons
            setup_action(self.login_action, {
                "Windows": "login_icon.ico",
                "Darwin": "login_icon.icns",
                "Linux": "login_icon.png"
            }.get(platform.system(), "login_icon.png"), visible=not self.logged_in, enabled=not self.logged_in)

            setup_action(self.logout_action, {
                "Windows": "logout_icon.ico",
                "Darwin": "logout_icon.icns",
                "Linux": "logout_icon.png"
            }.get(platform.system(), "logout_icon.png"), visible=self.logged_in, enabled=self.logged_in)

            setup_action(self.downloaded_files_action, {
                "Windows": "download_icon.ico",
                "Darwin": "download_icon.icns",
                "Linux": "download_icon.png"
            }.get(platform.system(), "download_icon.png"), visible=True, enabled=self.logged_in)

            setup_action(self.uploaded_files_action, {
                "Windows": "upload_icon.ico",
                "Darwin": "upload_icon.icns",
                "Linux": "upload_icon.png"
            }.get(platform.system(), "upload_icon.png"), visible=True, enabled=self.logged_in)

            setup_action(self.clear_cache_action, {
                "Windows": "clear_cache_icon.ico",
                "Darwin": "clear_cache_icon.icns",
                "Linux": "clear_cache_icon.png"
            }.get(platform.system(), "clear_cache_icon.png"), visible=True, enabled=self.logged_in)

            setup_action(self.quit_action, {
                "Windows": "quit_icon.ico",
                "Darwin": "quit_icon.icns",
                "Linux": "quit_icon.png"
            }.get(platform.system(), "quit_icon.png"), visible=True, enabled=True)

            # Add actions to tray menu in order
            self.tray_menu.addSeparator()
            self.tray_menu.addAction(self.downloaded_files_action)
            self.tray_menu.addAction(self.uploaded_files_action)
            self.tray_menu.addSeparator()
            self.tray_menu.addAction(self.clear_cache_action)
            self.tray_menu.addSeparator()
            self.tray_menu.addAction(self.login_action)
            self.tray_menu.addAction(self.logout_action)
            self.tray_menu.addSeparator()
            self.tray_menu.addAction(self.quit_action)

            # Add version display at the bottom with icon
            try:
                version_text = f"Version: {APPVERSION}"
            except NameError:
                version_text = "Version: Unknown"
                logger.warning("APPVERSION global variable not defined")
                app_signals.append_log.emit("[Tray] APPVERSION global variable not defined")
            version_action = QAction(version_text, self.tray_menu)
            version_action.setEnabled(False)  # Non-interactive
            font = QFont()
            font.setBold(True)
            version_action.setFont(font)
            # Set platform-specific version icon
            version_icon_name = {
                "Windows": "version_icon.ico",
                "Darwin": "version_icon.icns",
                "Linux": "version_icon.png"
            }.get(platform.system(), "version_icon.png")
            setup_action(version_action, version_icon_name)
            self.tray_menu.addSeparator()
            self.tray_menu.addAction(version_action)

            # Set the context menu for the tray icon
            self.tray_icon.setContextMenu(self.tray_menu)

            logger.debug(f"Tray menu updated: logged_in={self.logged_in}, user={user_fullname}, version={version_text}")
            app_signals.append_log.emit(f"[Tray] Menu updated: User={user_fullname}, Version={version_text}")

        except Exception as e:
            logger.error(f"Error updating tray menu: {e}\n{traceback.format_exc()}")
            app_signals.append_log.emit(f"[Tray] Failed to update tray menu: {str(e)}")
            app_signals.update_status.emit(f"Failed to update tray menu: {str(e)}")
            QMessageBox.critical(None, "Tray Menu Error", f"Failed to update tray menu: {str(e)}")

    def is_file_watcher_running(self):
        """Safely check if the file watcher thread is running."""
        thread = getattr(self, 'file_watcher_thread', None)
        if thread is None:
            return False
        try:
            return thread.isRunning()
        except RuntimeError:
            # Thread was already deleted
            self.file_watcher_thread = None
            return False


    def stop_file_watcher_thread(self):
        """Safely stop the file watcher thread and worker."""
        thread = getattr(self, 'file_watcher_thread', None)
        if thread is not None:
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(5000)
            except RuntimeError:
                logger.warning("FileWatcherThread already deleted")
            finally:
                self.file_watcher_thread = None

        worker = getattr(self, 'file_watcher', None)
        if worker is not None:
            self.file_watcher = None  # Let Python GC handle it

        timer = getattr(self, 'poll_timer', None)
        if timer is not None and timer.isActive():
            timer.stop()
            self.poll_timer = None


    def start_file_watcher(self):
        global FILE_WATCHER_RUNNING
        try:
            logger.info("Attempting to start FileWatcherWorker")
            app_signals.append_log.emit("[App] Attempting to start FileWatcherWorker")

            # Validate log window
            if self.log_window is None or self.log_window.status_bar is None:
                self.handle_error("FileWatcher", "Log window or status bar not initialized")
                return

            # Load cache safely
            try:
                cache = load_cache()
                logger.debug(f"Cache keys: {list(cache.keys())}")
                app_signals.append_log.emit(f"[App] Cache keys: {list(cache.keys())}")
            except Exception:
                cache = {}

            # Stop old thread
            self.stop_file_watcher_thread()

            FILE_WATCHER_RUNNING = True

            # ---- FIX: Create thread FIRST ----
            self.file_watcher_thread = QThread()

            # ---- FIX: Create worker INSIDE thread ----
            def create_worker():
                FileWatcherWorker._instance = None
                self.file_watcher = FileWatcherWorker.get_instance(parent=None)
                print("Worker created in thread:", QThread.currentThread())

                # connect worker signals
                self.file_watcher.status_update.connect(self.log_window.status_bar.showMessage)
                self.file_watcher.log_update.connect(app_signals.append_log)
                self.file_watcher.progress_update.connect(self.update_progress)

            self.file_watcher_thread.started.connect(create_worker)
            self.file_watcher_thread.start()

            logger.info("FileWatcherWorker thread started successfully")
            app_signals.append_log.emit("[App] FileWatcherWorker thread started successfully")

            # ---- FIX: Ensure poll_timer never becomes None ----
            if getattr(self, "poll_timer", None):
                self.poll_timer.stop()

            self.poll_timer = QTimer(self)
            self.poll_timer.timeout.connect(
                lambda: QMetaObject.invokeMethod(self.file_watcher, "run", Qt.QueuedConnection)
            )
            self.poll_timer.start(3000)  # 3 sec

            # Watchdog
            self.watchdog_timer = QTimer(self)
            self.watchdog_timer.timeout.connect(self.check_memory_usage)
            self.watchdog_timer.start(60000)

            self.schedule_daily_restart(3, 0)

        except Exception as e:
            self.handle_error("FileWatcher", f"Failed to start FileWatcherWorker: {str(e)}")



    def restart_file_watcher(self):
        """Restart FileWatcherWorker safely, with backoff."""
        try:
            if not hasattr(self, "restart_count"):
                self.restart_count = 0
            self.restart_count += 1

            backoff_delay = min(self.restart_count * 30, 300)
            if self.restart_count > 10:
                logger.error("[Watchdog] Too many restarts (>10). Stopping FileWatcherWorker permanently.")
                app_signals.append_log.emit("[Watchdog] Too many restarts (>10). Stopping FileWatcherWorker permanently.")
                return

            logger.info(f"[Watchdog] Restart attempt {self.restart_count}, backoff {backoff_delay}s")
            app_signals.append_log.emit(f"[Watchdog] Restart attempt {self.restart_count}, backoff {backoff_delay}s")

            # Stop old thread safely
            self.stop_file_watcher_thread()

            # Restart after backoff
            QTimer.singleShot(backoff_delay * 1000, self.start_file_watcher)

        except Exception as e:
            self.handle_error("FileWatcher", f"Failed to restart FileWatcherWorker: {str(e)}")

    def check_memory_usage(self, threshold_mb: int = 500, cpu_threshold: int = 80):
        """Watchdog check: restart file watcher if memory/CPU exceeds thresholds."""
        try:
            import psutil
            process = psutil.Process()

            mem_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=1)  # lightweight per-process CPU %

            logger.info(f"[Watchdog] Memory: {mem_mb:.2f} MB | CPU: {cpu_percent:.1f}%")
            app_signals.append_log.emit(f"[Watchdog] Memory: {mem_mb:.2f} MB | CPU: {cpu_percent:.1f}%")

            if mem_mb > threshold_mb or cpu_percent > cpu_threshold:
                reason = "Memory" if mem_mb > threshold_mb else "CPU"
                logger.warning(f"[Watchdog] {reason} exceeded limit. Restarting FileWatcherWorker...")
                app_signals.append_log.emit(f"[Watchdog] {reason} exceeded limit. Restarting FileWatcherWorker...")
                self.restart_file_watcher()

        except Exception as e:
            logger.error(f"[Watchdog] Failed to check system usage: {str(e)}")
            app_signals.append_log.emit(f"[Watchdog] Failed to check system usage: {str(e)}")


    def daily_restart_file_watcher(self):
        """Restart FileWatcher once every 24h for preventive cleanup."""
        logger.info("[DailyRestart] Performing scheduled daily restart of FileWatcherWorker...")
        app_signals.append_log.emit("[DailyRestart] Performing scheduled daily restart of FileWatcherWorker...")

        self.restart_count = 0  # reset watchdog counter
        self.restart_file_watcher()


    def schedule_daily_restart(self, hour: int = 3, minute: int = 0):
        """Schedule daily restart at fixed time (default 03:00 AM)."""
        from datetime import datetime, timedelta

        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)  # schedule for next day if already past

        delay_ms = int((target - now).total_seconds() * 1000)

        logger.info(f"[DailyRestart] Scheduled first daily restart at {target}")
        app_signals.append_log.emit(f"[DailyRestart] Scheduled first daily restart at {target}")

        QTimer.singleShot(delay_ms, self._start_daily_restart_cycle)


    def _start_daily_restart_cycle(self):
        """First trigger, then repeat daily."""
        self.daily_restart_file_watcher()
        self.daily_restart_timer = QTimer(self)
        self.daily_restart_timer.timeout.connect(self.daily_restart_file_watcher)
        self.daily_restart_timer.start(24 * 60 * 60 * 1000)  # 24h




    def handle_error(self, context, error, show_dialog=True):
        import traceback
        logger.error(f"{context}: {str(error)}\n{traceback.format_exc()}")
        app_signals.append_log.emit(f"[{context}] Failed: {str(error)}")
        app_signals.update_status.emit(f"{context} error: {str(error)}")
        if show_dialog:
            QMessageBox.critical(None, f"{context} Error", f"{context} error: {str(error)}")


    def cleanup_and_quit(self):
        if IS_APP_ACTIVE_UPLOAD_DOWNLOAD:
            print(f"Skip log out: {IS_APP_ACTIVE_UPLOAD_DOWNLOAD}")
            # Show success message
            QMessageBox.information(None, "Action blocked", "An upload/download is currently in progress. Try again once it is complete.")
            return

        try:
            logger.debug("Cleanup initiated")
            app_signals.append_log.emit("[App] Cleanup initiated")

            global FILE_WATCHER_RUNNING
            FILE_WATCHER_RUNNING = False
            FILE_WATCHER_STOP_QUEUE.put(True)

            # Stop poll timer if exists
            if hasattr(self, 'poll_timer') and self.poll_timer.isActive():
                self.poll_timer.stop()
                logger.debug("Stopped poll_timer")
                app_signals.append_log.emit("[App] Stopped poll_timer")

            # Stop file watcher thread if exists
            if hasattr(self, 'file_watcher_thread') and self.file_watcher_thread.isRunning():
                self.file_watcher_thread.quit()
                self.file_watcher_thread.wait(10000)
                if self.file_watcher_thread.isRunning():
                    logger.warning("File watcher thread did not stop gracefully, terminating")
                    app_signals.append_log.emit("[App] File watcher thread did not stop gracefully, terminating")
                    self.file_watcher_thread.terminate()
                    self.file_watcher_thread.wait(1000)

            # Close all top-level widgets
            for w in QApplication.topLevelWidgets():
                logger.debug(f"Closing widget: {w}")
                app_signals.append_log.emit(f"[App] Closing widget: {w}")
                w.close()

            # Hide tray icon if exists
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()

            # Close HTTP session
            logger.debug("Closing HTTP_SESSION")
            app_signals.append_log.emit("[App] Closing HTTP_SESSION")
            HTTP_SESSION.close()

            # Stop logging
            stop_logging()

            # Update status
            app_signals.update_status.emit("Application quitting")
            app_signals.append_log.emit("[App] Application quitting")
            logger.info("Application quitting")

            # Quit application safely
            QApplication.quit()

        except Exception as e:
            # Don’t crash — just log the error
            self.handle_error("Cleanup", f"Error in cleanup_and_quit: {str(e)}")
            try:
                QApplication.quit()
            except Exception:
                sys.exit(1)

    def logout_apicall(self, user_id):
        machine_id = USER_SYSTEM_INFO.get('encoded_mac', '')
        try:
            payload = {
                'user_id': user_id,
                'machine_id': machine_id,
            }
            response = requests.post(API_URL_LOGOUT, data=payload, verify=False)
            logger.info(response)
            if response.status_code == 200:
                logger.info(f"Successfully posted metadata to API (Logout).")
            else:
                logger.error(f"Failed to post metadata to API (Logout): {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error posting metadata to API (Logout): {e}")


    def logout(self):
        if IS_APP_ACTIVE_UPLOAD_DOWNLOAD:
            QMessageBox.information(None, "Action blocked",
                                    "An upload/download is currently in progress. Try again once it is complete.")
            print(f"Skip log out: {IS_APP_ACTIVE_UPLOAD_DOWNLOAD}")
            return

        try:
            self.logged_in = False
            cache = load_cache()
            # print(cache.get("user_id", ""), 'cacacasc')
            user_id = cache.get("user_id", "")
            print(f"logout --------------------------------user_id: {user_id}")
            self.logout_apicall(user_id)
            cache["token"] = ""
            if not self.login_dialog.ui.rememberme.isChecked():
                cache["saved_username"] = ""
                cache["saved_password"] = ""
            save_cache(cache)
            self.update_tray_menu()
            logger.info("Logged out successfully")
            app_signals.append_log.emit("[Login] Logged out successfully")
            app_signals.update_status.emit("Logged out successfully")

            # 🧩 FIX: Create a fresh login dialog before showing
            try:
                self.login_dialog.close()
            except Exception:
                pass

            self.login_dialog = LoginDialog(parent=None, app=self)
            self.login_dialog.show()
            self.login_dialog.raise_()
            self.login_dialog.activateWindow()
            self.login_dialog.setWindowState(Qt.WindowActive)
            self.login_dialog.showNormal()

            logger.info("Login dialog opened successfully")
            app_signals.append_log.emit("[Login] Login dialog opened successfully")

        except Exception as e:
            logger.error(f"Logout error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Logout error - {str(e)}")
            app_signals.update_status.emit(f"Logout error: {str(e)}")
            # QMessageBox.critical(self, "Logout Error", f"Failed to log out: {str(e)}")


    def set_logged_in_state(self):
        try:
            self.logged_in = True
            logger.debug(f"Setting logged_in state to: {self.logged_in}")
            app_signals.append_log.emit(f"[State] Setting logged_in state to: {self.logged_in}")
            self.update_tray_menu()
            if self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon.setIcon(load_icon(LOGGEDIN_ICON_PATH, "logged in"))
                self.tray_icon.show()
                logger.debug(f"Tray icon set to 'logged in', visible: {self.tray_icon.isVisible()}")
                app_signals.append_log.emit(f"[Tray] Tray icon set to 'logged in', visible: {self.tray_icon.isVisible()}")
            else:
                logger.warning("Tray icon or system tray not available")
                app_signals.append_log.emit("[Tray] Tray icon or system tray not available")
            if hasattr(self, 'login_dialog'):
                self.login_dialog.is_logged_in = True
                logger.debug(f"LoginDialog is_logged_in set to: {self.login_dialog.is_logged_in}")
            logger.info("Set logged in state")
            app_signals.append_log.emit("[State] Set to logged-in state")
            app_signals.update_status.emit("Logged in state set")
        except Exception as e:
            self.handle_error("SetLoggedIn", f"Error setting logged-in state: {str(e)}")


    def set_logged_out_state(self):
        try:
            self.logged_in = False
            if hasattr(self, 'login_dialog'):
                self.login_dialog.is_logged_in = False
            logger.info("Set logged out state")
            app_signals.append_log.emit("[State] Set to logged-out state")
            app_signals.update_status.emit("Logged out state set")

            # Force tray menu update
            self.update_tray_menu()
            QApplication.processEvents()  # Make sure UI updates immediately

            # Optionally force reset the tray icon tooltip
            if self.tray_icon:
                self.tray_icon.setToolTip("PremediaApp - Not logged in")

        except Exception as e:
            logger.error(f"Error in set_logged_out_state: {e}")
            app_signals.append_log.emit(f"[State] Failed: Error setting logged-out state - {str(e)}")
            app_signals.update_status.emit(f"Error setting logged-out state: {str(e)}")


    def open_cache_file(self):
        try:
            cache_file = Path(self.CACHE_FILE).resolve()
            logger.debug(f"Attempting to open cache file: {cache_file}")
            app_signals.append_log.emit(f"[Cache] Attempting to open: {cache_file}")

            # Check if file exists
            if not cache_file.exists():
                logger.warning(f"Cache file does not exist: {cache_file}")
                app_signals.append_log.emit(f"[Cache] Cache file does not exist: {cache_file}")
                app_signals.update_status.emit("Cache file does not exist")
                QMessageBox.warning(None, "Cache Error", f"Cache file does not exist:\n{cache_file}")
                return

            # Verify file is readable
            if not cache_file.is_file():
                logger.warning(f"Cache file is not a valid file: {cache_file}")
                app_signals.append_log.emit(f"[Cache] Invalid file: {cache_file}")
                app_signals.update_status.emit("Invalid cache file")
                QMessageBox.warning(None, "Cache Error", f"Invalid cache file:\n{cache_file}")
                return

            # Read and beautify file content
            try:
                with cache_file.open('r', encoding='utf-8') as f:
                    raw_content = f.read()
                # Try to parse and beautify JSON
                try:
                    json_data = json.loads(raw_content)
                    content = json.dumps(json_data, indent=4, sort_keys=True)
                    logger.debug("Successfully parsed and formatted JSON content")
                    app_signals.append_log.emit("[Cache] Successfully formatted JSON content")
                except json.JSONDecodeError as json_err:
                    logger.warning(f"Cache file is not valid JSON: {json_err}")
                    app_signals.append_log.emit(f"[Cache] Not valid JSON, displaying raw content: {str(json_err)}")
                    content = raw_content  # Fall back to raw content
            except UnicodeDecodeError:
                logger.warning(f"Cache file is not UTF-8 encoded: {cache_file}")
                app_signals.append_log.emit(f"[Cache] Non-UTF-8 file detected: {cache_file}")
                with cache_file.open('r', encoding='latin-1') as f:
                    content = f.read()  # Display raw content without JSON formatting

            # Create and show dialog
            dialog = QDialog(None)  # Use None as parent since PremediaApp is not a widget
            dialog.setWindowTitle("Cache File Content")
            dialog.setMinimumSize(600, 400)

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(content)

            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.close)

            layout = QVBoxLayout()
            layout.addWidget(text_edit)
            layout.addWidget(close_button)
            dialog.setLayout(layout)

            app_signals.update_status.emit("Opened cache file")
            app_signals.append_log.emit(f"[Cache] Opened cache file: {cache_file}")
            dialog.exec_()  # Modal dialog for better visibility

        except (IOError, OSError) as e:
            logger.error(f"IO error opening cache file: {e}\n{traceback.format_exc()}")
            app_signals.append_log.emit(f"[Cache] Failed: IO error - {str(e)}")
            app_signals.update_status.emit(f"Error opening cache file: {str(e)}")
            QMessageBox.critical(None, "Cache Error", f"Failed to open cache file:\n{str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error opening cache file: {e}\n{traceback.format_exc()}")
            app_signals.append_log.emit(f"[Cache] Failed: Unexpected error - {str(e)}")
            app_signals.update_status.emit("Unexpected error")
            QMessageBox.critical(None, "Cache Error", f"Unexpected error opening cache file:\n{str(e)}")

    def clear_cache(self):
        global IS_APP_ACTIVE_UPLOAD_DOWNLOAD
        IS_APP_ACTIVE_UPLOAD_DOWNLOAD = False
        global GLOBAL_CACHE

        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirm Clear Cache")
        msg_box.setText(
            "Are you sure you want to clear the cache and delete all files and folders in the premedia application directory? "
            "This action cannot be undone, and all data will be permanently deleted."
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.info(f"[Cache] Clearing cache from BASE_DIR: {BASE_TARGET_DIR}")
                app_signals.append_log.emit(f"[Cache] Clearing cache from BASE_DIR: {BASE_TARGET_DIR}")

                initialize_cache()
                GLOBAL_CACHE = None
                self.logged_in = False
                self.update_tray_menu()

                # Delete everything inside BASE_TARGET_DIR
                if os.path.exists(BASE_TARGET_DIR):
                    try:
                        shutil.rmtree(BASE_TARGET_DIR)   # remove the whole folder
                        logger.info(f"Deleted BASE_TARGET_DIR: {BASE_TARGET_DIR}")
                        app_signals.append_log.emit(f"[Cache] Deleted BASE_TARGET_DIR: {BASE_TARGET_DIR}")
                    except Exception as e:
                        logger.error(f"Failed to delete BASE_TARGET_DIR: {e}")
                        app_signals.append_log.emit(f"[Cache] Failed to delete BASE_TARGET_DIR: {e}")

                    # Recreate empty BASE_TARGET_DIR
                    os.makedirs(BASE_TARGET_DIR, exist_ok=True)
                    logger.info(f"Recreated empty {BASE_TARGET_DIR}")
                    app_signals.append_log.emit(f"[Cache] Recreated empty {BASE_TARGET_DIR}")

                logger.info("Cache cleared manually")
                app_signals.append_log.emit("[Cache] Cache cleared manually")
                app_signals.update_status.emit("Cache cleared successfully")

                # ✅ Show success dialog
                QMessageBox.information(None, "Cache Cleared", "Cache cleared successfully!")

                self.show_login()
            except Exception as e:
                print(f"Error clearing cache: {e}")
                app_signals.append_log.emit(f"[Cache] Failed: Error clearing cache - {str(e)}")
                app_signals.update_status.emit(f"Error clearing cache: {str(e)}")
                QMessageBox.critical(None, "Cache Error", f"Failed to clear cache: {str(e)}")
        else:
            app_signals.append_log.emit("[Cache] Cache clear cancelled by user")
            logger.info("Cache clear cancelled by user")
            app_signals.update_status.emit("Cache clear cancelled")

    def quit(self):
        global HTTP_SESSION, FILE_WATCHER_RUNNING
        try:
            logger.debug("Quit initiated")
            if hasattr(self, 'poll_timer') and self.poll_timer.isActive():
                logger.debug("Stopping poll_timer")
                self.poll_timer.stop()
                FILE_WATCHER_RUNNING = False

            if hasattr(self, 'file_watcher_thread') and self.file_watcher_thread.isRunning():
                logger.debug("Quitting file_watcher_thread")
                self.file_watcher_thread.quit()
                self.file_watcher_thread.wait(2000)

            if hasattr(self, 'login_dialog') and self.login_dialog.isVisible():
                logger.debug("Closing login_dialog")
                self.login_dialog.close()

            if self.tray_icon:
                logger.debug("Hiding tray_icon")
                self.tray_icon.hide()

            logger.debug("Closing HTTP_SESSION")
            HTTP_SESSION.close()

            stop_logging()
            app_signals.update_status.emit("Application quitting")
            app_signals.append_log.emit("[App] Application quitting")
            logger.info("Application quitting")
            self.app.quit()
        except Exception as e:
            logger.error(f"Error in quit: {e}")
            app_signals.append_log.emit(f"[App] Failed: Quit error - {str(e)}")
            app_signals.update_status.emit(f"Quit error: {str(e)}")
            stop_logging()
            self.app.quit()

    def show_login(self):
        try:
            if not self.logged_in:
                # If the old dialog was closed or deleted, recreate it safely
                if self.login_dialog is None or not isinstance(self.login_dialog, LoginDialog):
                    logger.warning("Recreating login dialog (previous instance lost or invalid)")
                    self.login_dialog = LoginDialog(parent=None, app=self)
                    self.login_dialog.user_in_other_system.connect(self.show_login_page)

                # If signals were lost after logout, rebind them
                try:
                    if hasattr(self.login_dialog.ui, "login_button") and \
                    not self.login_dialog.ui.login_button.receivers(self.login_dialog.ui.login_button.clicked):
                        self.login_dialog.ui.login_button.clicked.connect(self.login_dialog.handle_login)
                        logger.debug("Reconnected login button signal")

                    if hasattr(self.login_dialog.ui, "cancel_button") and \
                    not self.login_dialog.ui.cancel_button.receivers(self.login_dialog.ui.cancel_button.clicked):
                        self.login_dialog.ui.cancel_button.clicked.connect(self.login_dialog.reject)
                        logger.debug("Reconnected cancel button signal")
                except Exception as signal_error:
                    logger.warning(f"Could not verify/reconnect signals: {signal_error}")

                # Make absolutely sure the dialog is visible and interactive
                self.login_dialog.showNormal()
                self.login_dialog.raise_()
                self.login_dialog.activateWindow()
                self.login_dialog.setWindowState(Qt.WindowActive)
                QApplication.processEvents()

                app_signals.update_status.emit("Login dialog opened")
                app_signals.append_log.emit("[Login] Login dialog opened")
                logger.info("Login dialog opened successfully")
            else:
                app_signals.update_status.emit("Already logged in")
                app_signals.append_log.emit("[Login] Already logged in")
                logger.info("User is already logged in")
        except Exception as e:
            logger.error(f"Error in show_login: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Error opening login dialog - {str(e)}")
            app_signals.update_status.emit(f"Error opening login dialog: {str(e)}")
            QMessageBox.critical(None, "Login Error", f"Failed to open login dialog: {str(e)}")


    def show_logs(self):
        try:
            self.log_window.load_logs()
            setup_logger(self.log_window)  # Reconnect logger signals
            self.log_window.connect_signals()  # Reconnect LogWindow signals
            self.log_window.show()
            self.log_window.raise_()
            self.log_window.activateWindow()
            self.log_window.setWindowState(Qt.WindowActive)
            self.log_window.showNormal()
            app_signals.update_status.emit("Log window opened")
            app_signals.append_log.emit("[Log] Log window opened")
        except Exception as e:
            logger.error(f"Error in show_logs: {e}")
            app_signals.append_log.emit(f"[Log] Failed: Error opening log window - {str(e)}")
            app_signals.update_status.emit(f"Error opening log window: {str(e)}")
            QMessageBox.critical(self, "Log Error", f"Failed to open log window: {str(e)}")

    def show_downloaded_files(self):
        try:
            if not self.downloaded_files_window or not self.downloaded_files_window.isVisible():
                self.downloaded_files_window = FileDownloadListWindow("downloaded")
                self.downloaded_files_window.show()
                self.downloaded_files_window.raise_()
                self.downloaded_files_window.activateWindow()
                # Ensure the window is visible and brought to front
                self.downloaded_files_window.setWindowState(Qt.WindowActive)
                self.downloaded_files_window.showNormal()  # Restore to normal state if minimized
                app_signals.update_status.emit("Downloaded files window opened")
                app_signals.append_log.emit("[Files] Downloaded files window opened")
        except Exception as e:
            logger.error(f"Error in show_downloaded_files: {e}")
            app_signals.append_log.emit(f"[Files] Failed: Error showing downloaded files - {str(e)}")
            app_signals.update_status.emit(f"Error showing downloaded files: {str(e)}")
            QMessageBox.critical(self, "Files Error", f"Failed to show downloaded files: {str(e)}")

    def show_uploaded_files(self):
        try:
            if not self.uploaded_files_window or not self.uploaded_files_window.isVisible():
                self.uploaded_files_window = FileUploadListWindow("uploaded")
                self.uploaded_files_window.show()
                self.uploaded_files_window.raise_()
                self.uploaded_files_window.activateWindow()
                # Ensure the window is visible and brought to front
                self.uploaded_files_window.setWindowState(Qt.WindowActive)
                self.uploaded_files_window.showNormal()  # Restore to normal state if minimized
                app_signals.update_status.emit("Uploaded files window opened")
                app_signals.append_log.emit("[Files] Uploaded files window opened")
        except Exception as e:
            logger.error(f"Error in show_uploaded_files: {e}")
            app_signals.append_log.emit(f"[Files] Failed: Error showing uploaded files - {str(e)}")
            app_signals.update_status.emit(f"Error showing uploaded files: {str(e)}")
            QMessageBox.critical(self, "Files Error", f"Failed to show uploaded files: {str(e)}")

    def convert_to_jpg_and_psd(self, src_path, dest_dir):
        try:
            self.thread = QThread()
            self.worker = FileConversionWorker(src_path, dest_dir)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_conversion_finished)
            self.worker.error.connect(self.on_conversion_error)
            self.worker.progress.connect(lambda file_path, progress: app_signals.update_file_list.emit(file_path, f"Converting: {progress}%", "download", progress, False))
            self.worker.finished.connect(self.thread.quit)
            self.worker.error.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.error.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
            app_signals.append_log.emit(f"[Conversion] Starting conversion for {src_path}")
        except Exception as e:
            logger.error(f"File conversion thread error: {e}")
            app_signals.append_log.emit(f"[Conversion] Failed: File conversion thread error - {str(e)}")
            app_signals.update_status.emit(f"File conversion thread error: {str(e)}")
            QMessageBox.critical(self, "Conversion Error", f"File conversion thread error: {str(e)}")

    def on_conversion_finished(self, jpg_path, psd_path, basename):
        try:
            cache = load_cache()
            if cache:
                cache["downloaded_files"].extend([jpg_path, psd_path])
                save_cache(cache)
            app_signals.update_status.emit(f"Uploaded JPG: {basename}")
            app_signals.update_file_list.emit(jpg_path, "Conversion Completed", "download", 100, False)
            app_signals.update_file_list.emit(psd_path, "Conversion Completed", "download", 100, False)
            app_signals.append_log.emit(f"[Conversion] Completed conversion for {basename}")
        except Exception as e:
            logger.error(f"Error in on_conversion_finished: {e}")
            app_signals.append_log.emit(f"[Conversion] Failed: Conversion error - {str(e)}")
            app_signals.update_status.emit(f"Conversion error: {str(e)}")
            QMessageBox.critical(self, "Conversion Error", f"Conversion error: {str(e)}")

    def on_conversion_error(self, error, basename):
        try:
            app_signals.update_status.emit(f"Conversion failed for {basename}: {error}")
            app_signals.update_file_list.emit("", f"Conversion Failed: {error}", "download", 0, False)
            app_signals.append_log.emit(f"[Conversion] Failed: Conversion error for {basename} - {error}")
        except Exception as e:
            logger.error(f"Error in on_conversion_error: {e}")
            app_signals.append_log.emit(f"[Conversion] Failed: Error handling conversion error - {str(e)}")
            app_signals.update_status.emit(f"Error handling conversion error: {str(e)}")
            QMessageBox.critical(self, "Conversion Error", f"Error handling conversion error: {str(e)}")

    def open_with_photoshop(self, file_path):
        try:
            system = platform.system()
            photoshop_path = None
            if system == "Windows":
                search_dirs = [
                    Path("C:/Program Files/Adobe"),
                    Path("C:/Program Files (x86)/Adobe")
                ]
                for base_dir in search_dirs:
                    if not base_dir.exists():
                        continue
                    photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                    if photoshop_exes:
                        photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                        photoshop_path = str(photoshop_exes[0])
                        break
                if not photoshop_path:
                    raise FileNotFoundError("Adobe Photoshop executable not found in Program Files")
            elif system == "Darwin":
                try:
                    result = subprocess.run(
                        ["mdfind", "kMDItemKind == 'Application' && kMDItemFSName == 'Adobe Photoshop.app'"],
                        capture_output=True, text=True, check=True
                    )
                    if result.stdout.strip():
                        photoshop_path = result.stdout.strip().split("\n")[0]
                except subprocess.CalledProcessError:
                    photoshop_apps = list(Path("/Applications").glob("Adobe Photoshop*.app"))
                    if photoshop_apps:
                        photoshop_apps.sort(key=lambda x: x.name, reverse=True)
                        photoshop_path = str(photoshop_apps[0])
                if not photoshop_path:
                    raise FileNotFoundError("Adobe Photoshop application not found in /Applications")
            elif system == "Linux":
                try:
                    subprocess.run(["wine", "--version"], capture_output=True, check=True)
                    wine_dirs = [
                        Path.home() / ".wine/drive_c/Program Files/Adobe",
                        Path.home() / ".wine/drive_c/Program Files (x86)/Adobe"
                    ]
                    for base_dir in wine_dirs:
                        if not base_dir.exists():
                            continue
                        photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                        if photoshop_exes:
                            photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                            photoshop_path = str(photoshop_exes[0])
                            break
                    if not photoshop_path:
                        raise FileNotFoundError("Photoshop.exe not found in Wine directories")
                except subprocess.CalledProcessError:
                    raise FileNotFoundError("Wine is not installed or not functioning")
            else:
                error_msg = f"Unsupported platform for Photoshop: {system}"
                logger.warning(error_msg)
                app_signals.append_log.emit(f"[Photoshop] {error_msg}")
                app_signals.update_status.emit(error_msg)
                QMessageBox.critical(self, "Photoshop Error", error_msg)
                return
            if not Path(file_path).is_file():
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                app_signals.append_log.emit(f"[Photoshop] {error_msg}")
                app_signals.update_status.emit(error_msg)
                QMessageBox.critical(self, "Photoshop Error", error_msg)
                return
            if system == "Darwin":
                subprocess.run(["open", "-a", photoshop_path, file_path], check=True)
            else:
                subprocess.run([photoshop_path, file_path], check=True)
            logger.info(f"Opened {Path(file_path).name} in Photoshop at {photoshop_path}")
            app_signals.append_log.emit(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
            app_signals.update_status.emit(f"Opened {Path(file_path).name} in Photoshop")
        except Exception as e:
            error_msg = f"Failed to open {Path(file_path).name} in Photoshop: {str(e)}"
            logger.error(error_msg)
            app_signals.append_log.emit(f"[Photoshop] {error_msg}")
            app_signals.update_status.emit(error_msg)
            QMessageBox.critical(self, "Photoshop Error", error_msg)

    def update_progress(self, value: int):
        try:
            logger.debug(f"Progress update received: {value}%")
            app_signals.append_log.emit(f"[App] Progress update: {value}%")
            if hasattr(self, 'log_window') and self.log_window:
                self.log_window.status_bar.showMessage(f"File operation progress: {value}%")
                logger.debug(f"Updated LogWindow status bar with progress: {value}%")
                app_signals.update_status.emit(f"File operation progress: {value}%")
        except Exception as e:
            logger.error(f"Error in update_progress: {e}")
            app_signals.append_log.emit(f"[App] Error in update_progress: {str(e)}")

    def post_login_processes(self):
        global FILE_WATCHER_RUNNING
        try:
            cache = load_cache()
            token = cache.get("token", "")
            user_id = cache.get("user_id", "")
            if not token or not user_id:
                self.handle_error("Post-Login", "No token or user_id for post-login processes")
                self.set_logged_out_state()
                self.show_login()
                return

            # Stop existing resources
            if hasattr(self, 'poll_timer') and self.poll_timer.isActive():
                self.poll_timer.stop()
                logger.debug("Stopped existing poll timer")
                app_signals.append_log.emit("[Login] Stopped existing poll timer")

            if hasattr(self, 'file_watcher_thread') and self.file_watcher_thread.isRunning():
                self.file_watcher_thread.quit()
                self.file_watcher_thread.wait(10000)
                logger.debug("Stopped existing file watcher thread")
                app_signals.append_log.emit("[Login] Stopped existing file watcher thread")

            FileWatcherWorker._instance = None
            FILE_WATCHER_RUNNING = True

            # Start file watcher
            self.start_file_watcher()

            # Update tray menu
            self.update_tray_menu()
            if self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon.show()
                logger.debug(f"Tray icon visible after post-login: {self.tray_icon.isVisible()}")
                app_signals.append_log.emit(f"[Login] Tray icon visible after post-login: {self.tray_icon.isVisible()}")
            else:
                logger.warning("Tray icon or system tray not available")
                app_signals.append_log.emit("[Tray] Tray icon or system tray not available")

            # Close progress dialog if visible
            if hasattr(self, 'login_dialog') and self.login_dialog.progress and self.login_dialog.progress.isVisible():
                self.login_dialog.progress.close()
                logger.debug("Progress dialog closed")
                app_signals.append_log.emit("[Login] Progress dialog closed")

            # Reconnect status signals
            try:
                app_signals.update_status.disconnect(self.log_window.status_bar.showMessage)
            except Exception:
                logger.debug("No existing update_status connection to disconnect")
            app_signals.update_status.connect(self.log_window.status_bar.showMessage, Qt.QueuedConnection)

            logger.info("Post-login processes completed successfully")
            app_signals.append_log.emit("[Login] Post-login processes completed successfully")
            app_signals.update_status.emit("File watcher started")
        except Exception as e:
            self.handle_error("Post-Login", f"Post-login error: {str(e)}")
            if hasattr(self, 'login_dialog') and self.login_dialog.progress and self.login_dialog.progress.isVisible():
                self.login_dialog.progress.close()
                logger.debug("Progress dialog closed in error handler")
                app_signals.append_log.emit("[Login] Progress dialog closed in error handler")
            self.set_logged_out_state()
            self.show_login()

    def show_dialog(self, title, message, dialog_type):
        try:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            if dialog_type.lower() == "error":
                msg_box.setIcon(QMessageBox.Critical)
            else:
                msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
            logger.debug(f"Displayed dialog: {title} - {message} ({dialog_type})")
            app_signals.append_log.emit(f"[Dialog] Displayed: {title} - {message} ({dialog_type})")
            app_signals.update_status.emit(f"Displayed dialog: {title}")
        except Exception as e:
            logger.error(f"Error in show_dialog: {str(e)}")
            app_signals.append_log.emit(f"[Dialog] Failed: Error displaying dialog - {str(e)}")
            app_signals.update_status.emit(f"Error displaying dialog: {str(e)}")

get_system_info()

if __name__ == "__main__":
    try:
        key = parse_custom_url()
        app = PremediaApp(key)
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application crashed: {e}")
        import traceback
        traceback.print_exc()