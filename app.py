from PySide6.QtWidgets import (
    QApplication, QDialog, QMessageBox, QProgressDialog, QTextEdit, QSystemTrayIcon,
    QMenu, QVBoxLayout, QStatusBar, QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QProgressBar, QSizePolicy
)
from PySide6.QtCore import QEvent, QSize, QThread, QTimer, Qt, QObject, Signal
from PySide6.QtGui import QIcon, QTextCursor, QAction, QCursor
from login import Ui_Dialog
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
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import subprocess
from queue import Queue
import threading
import time
from psd_tools import PSDImage
from PIL import Image
import numpy as np
import shutil
from pathlib import Path

# Handle paramiko import
try:
    import paramiko
    NAS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"paramiko not installed: {e}. NAS functionality disabled.")
    NAS_AVAILABLE = False
    paramiko = None

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
def get_icon_path(icon_name):
    if icon_name in ICON_CACHE:
        return str(ICON_CACHE[icon_name])
    icons_dir = BASE_DIR / "icons"
    try:
        icons_dir.mkdir(exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create icons directory {icons_dir}: {e}")
        app_signals.append_log.emit(f"[Init] Failed to create icons directory {icons_dir}: {str(e)}")
    icon_path = str(icons_dir / icon_name)
    ICON_CACHE[icon_name] = icon_path
    return icon_path

ICON_PATH = get_icon_path({
    "Windows": "premedia.ico",
    "Darwin": "premedia.icns",
    "Linux": "premedia.png"
}.get(platform.system(), "premedia.png"))
PHOTOSHOP_ICON_PATH = get_icon_path("photoshop.png") if (BASE_DIR / "icons" / "photoshop.png").exists() else ""
FOLDER_ICON_PATH = get_icon_path("folder.png") if (BASE_DIR / "icons" / "folder.png").exists() else ""
def get_cache_file_path():
    if platform.system() == "Windows":
        cache_dir = Path(os.getenv("APPDATA")) / "PremediaApp"
    elif platform.system() == "Darwin":
        cache_dir = Path.home() / "Library" / "Caches" / "PremediaApp"
    else:
        cache_dir = Path.home() / ".cache" / "PremediaApp"
    try:
        cache_dir.mkdir(exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create cache directory {cache_dir}: {e}")
        app_signals.append_log.emit(f"[Cache] Failed to create cache directory {cache_dir}: {str(e)}")
    return str(cache_dir / "cache.json")

CACHE_FILE = get_cache_file_path()
CACHE_DAYS = 10
API_URL = f"{BASE_DOMAIN}/api/ir_production/get/projectList?business=image_retouching"
DOWNLOAD_UPLOAD_API = f"{BASE_DOMAIN}/api/get_download_upload/submission"
OAUTH_URL = f"{BASE_DOMAIN}/oauth/token"
USER_VALIDATE_URL = f"{BASE_DOMAIN}/api/user/validate"
NAS_IP = "192.168.3.20"
NAS_USERNAME = "irdev"
NAS_PASSWORD = "i#0f!L&+@s%^qc"
NAS_SHARE = ""
API_POLL_INTERVAL = 5000  # 5 seconds in milliseconds

# === Global State ===
GLOBAL_CACHE = None
CACHE_WRITE_LOCK = threading.Lock()
HTTP_SESSION = requests.Session()
FILE_WATCHER_RUNNING = False
LOGGING_ACTIVE = True
app_signals = None
LAST_API_HIT_TIME = None
NEXT_API_HIT_TIME = None

# === Logging Setup ===
logger = logging.getLogger("PremediaApp")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_dir = BASE_DIR / "log"
try:
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log", maxBytes=10485760, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    logger.error(f"Error setting up log file: {e}")
    console_handler = logging.StreamHandler()
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
class LogWindowHandler(logging.Handler, QObject):
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setLevel(logging.INFO)
        self.setFormatter(formatter)

    def emit(self, record):
        global LOGGING_ACTIVE
        if not LOGGING_ACTIVE:
            return
        try:
            msg = self.format(record)
            app_signals.append_log.emit(msg)
        except Exception as e:
            logger.error(f"Log signal emission error: {e}")
            app_signals.append_log.emit(f"[Log] Log signal emission error: {str(e)}")

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

def setup_logger(log_window=None):
    logger.handlers.clear()
    async_handler = LogWindowHandler()
    logger.addHandler(async_handler)
    if log_window:
        app_signals.append_log.connect(log_window.append_log, Qt.QueuedConnection)
        app_signals.api_call_status.connect(log_window.append_api_status, Qt.QueuedConnection)
        app_signals.update_timer_status.connect(log_window.update_timer_status, Qt.QueuedConnection)
    try:
        log_file = log_dir / "app.log"
        if log_file.exists():
            with log_file.open('r') as f:
                lines = f.readlines()
            if len(lines) > 200:
                with log_file.open('w') as f:
                    f.writelines(lines[-200:])
    except Exception as e:
        logger.error(f"Error managing log file: {e}")
        app_signals.append_log.emit(f"[Log] Error managing log file: {str(e)}")
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

# Cache functions
def get_default_cache():
    return {
        "token": "",
        "user": "",
        "user_id": "",
        "user_info": {},
        "info_resp": {},
        "user_data": {},
        "data": "",
        "downloaded_files": [],
        "uploaded_files": [],
        "timer_responses": {},
        "saved_username": "",
        "saved_password": "",
        "cached_at": datetime.now(ZoneInfo("UTC")).isoformat()
    }

def initialize_cache():
    global GLOBAL_CACHE
    default_cache = get_default_cache()
    cache_dir = Path(CACHE_FILE).parent
    try:
        cache_dir.mkdir(exist_ok=True)
        with CACHE_WRITE_LOCK:
            with open(CACHE_FILE, "w") as f:
                json.dump(default_cache, f, indent=2)
            if platform.system() in ["Linux", "Darwin"]:
                os.chmod(CACHE_FILE, 0o600)
        GLOBAL_CACHE = default_cache
        logger.info("Initialized empty cache file")
        app_signals.append_log.emit("[Cache] Initialized empty cache file")
        return True
    except Exception as e:
        logger.error(f"Error initializing cache: {e}")
        app_signals.append_log.emit(f"[Cache] Error initializing cache: {str(e)}")
        GLOBAL_CACHE = default_cache
        return False

def save_cache(data):
    global GLOBAL_CACHE
    data_copy = data.copy()
    data_copy['cached_at'] = datetime.now(ZoneInfo("UTC")).isoformat()
    cache_dir = Path(CACHE_FILE).parent
    try:
        cache_dir.mkdir(exist_ok=True)
        if Path(CACHE_FILE).exists():
            backup_file = str(cache_dir / f"cache_backup_{datetime.now(ZoneInfo('UTC')).strftime('%Y%m%d_%H%M%S')}.json")
            with open(CACHE_FILE, "r") as f, open(backup_file, "w") as bf:
                bf.write(f.read())
        with CACHE_WRITE_LOCK:
            with open(CACHE_FILE, "w") as f:
                json.dump(data_copy, f, indent=2)
            if platform.system() in ["Linux", "Darwin"]:
                os.chmod(CACHE_FILE, 0o600)
        GLOBAL_CACHE = data_copy
        logger.info("Cache saved successfully")
        app_signals.append_log.emit("[Cache] Cache saved successfully")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")
        app_signals.append_log.emit(f"[Cache] Failed to save cache: {str(e)}")

def load_cache():
    global GLOBAL_CACHE
    default_cache = get_default_cache()
    if GLOBAL_CACHE is not None:
        return GLOBAL_CACHE
    cache_file = Path(CACHE_FILE)
    if not cache_file.exists():
        logger.warning("Cache file does not exist, initializing new cache")
        app_signals.append_log.emit("[Cache] Cache file does not exist, initializing new cache")
        initialize_cache()
        return GLOBAL_CACHE
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        required_keys = default_cache.keys()
        if not all(key in data for key in required_keys):
            logger.warning("Cache is missing required keys, reinitializing")
            app_signals.append_log.emit("[Cache] Cache is missing required keys, reinitializing")
            initialize_cache()
            return GLOBAL_CACHE
        cached_time_str = data.get("cached_at", "2000-01-01T00:00:00+00:00")
        try:
            cached_time = datetime.fromisoformat(cached_time_str)
            if datetime.now(ZoneInfo("UTC")) - cached_time >= timedelta(days=CACHE_DAYS):
                logger.warning("Cache is expired, reinitializing")
                app_signals.append_log.emit("[Cache] Cache is expired, reinitializing")
                initialize_cache()
                return GLOBAL_CACHE
        except ValueError as e:
            logger.error(f"Invalid cached_at format: {e}, reinitializing cache")
            app_signals.append_log.emit(f"[Cache] Invalid cached_at format: {str(e)}, reinitializing cache")
            initialize_cache()
            return GLOBAL_CACHE
        token = data.get("token", "")
        if token:
            try:
                resp = HTTP_SESSION.get(
                    USER_VALIDATE_URL,
                    headers={"Authorization": f"Bearer {token}"},
                    verify=False,
                    timeout=10
                )
                if resp.status_code != 200 or not resp.json().get("status"):
                    logger.warning(f"Cached token invalid (status: {resp.status_code}), reinitializing cache")
                    app_signals.append_log.emit(f"[Cache] Cached token invalid (status: {resp.status_code}), reinitializing cache")
                    initialize_cache()
                    return GLOBAL_CACHE
            except RequestException as e:
                logger.error(f"Token validation failed: {e}, keeping cache but marking token as invalid")
                app_signals.append_log.emit(f"[Cache] Token validation failed: {str(e)}, keeping cache but marking token as invalid")
                data["token"] = ""
                GLOBAL_CACHE = data
                save_cache(GLOBAL_CACHE)
                return GLOBAL_CACHE
        GLOBAL_CACHE = data
        logger.info("Cache loaded successfully")
        app_signals.append_log.emit("[Cache] Cache loaded successfully")
        return GLOBAL_CACHE
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted cache file: {e}, reinitializing cache")
        app_signals.append_log.emit(f"[Cache] Corrupted cache file: {str(e)}, reinitializing cache")
        initialize_cache()
        return GLOBAL_CACHE
    except Exception as e:
        logger.error(f"Error loading cache: {e}, reinitializing cache")
        app_signals.append_log.emit(f"[Cache] Failed to load cache: {str(e)}, reinitializing cache")
        initialize_cache()
        return GLOBAL_CACHE

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
        
        cache = load_cache()
        validation_url = "https://app-uat.vmgpremedia.com/api/user/validate"
        logger.debug(f"Validating user with access_key: {access_key[:8]}... at {validation_url}")
        app_signals.append_log.emit(f"[API Scan] Validating user with access_key: {access_key[:8]}...")
        
        resp = HTTP_SESSION.get(
            validation_url,
            params={"key": access_key},
            headers={"Authorization": f"Bearer {cache.get('token', '')}"},
            verify=False,  # Replace with verify="/path/to/server-ca.pem" in production
            timeout=30
        )
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

def connect_to_nas():
    if not NAS_AVAILABLE:
        logger.warning("NAS functionality disabled")
        app_signals.append_log.emit("[API Scan] NAS functionality disabled")
        return None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            transport = paramiko.Transport((NAS_IP, 22))
            transport.connect(username=NAS_USERNAME, password=NAS_PASSWORD)
            sftp = paramiko.SFTPClient.from_transport(transport)
            # sftp.stat(NAS_SHARE)
            logger.info(f"Connected to NAS at {NAS_IP}/{NAS_SHARE}")
            app_signals.append_log.emit(f"[API Scan] Connected to NAS at {NAS_IP}/{NAS_SHARE}")
            return (transport, sftp)
        except paramiko.AuthenticationException as e:
            logger.error(f"NAS authentication failed: {e}")
            app_signals.append_log.emit(f"[API Scan] Failed: NAS authentication error - {str(e)}")
            return None
        except paramiko.SSHException as e:
            logger.error(f"NAS SSH error (attempt {attempt + 1}): {e}")
            app_signals.append_log.emit(f"[API Scan] Failed: NAS SSH error (attempt {attempt + 1}) - {str(e)}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2)  # Wait before retrying
        except Exception as e:
            logger.error(f"Failed to connect to NAS (attempt {attempt + 1}): {e}")
            app_signals.append_log.emit(f"[API Scan] Failed: NAS connection error (attempt {attempt + 1}) - {str(e)}")
            return None
    return None

class FileConversionWorker(QObject):
    finished = Signal(str, str, str)
    error = Signal(str, str)
    progress = Signal(str, int)

    def __init__(self, src_path, dest_dir):
        super().__init__()
        self.src_path = src_path
        self.dest_dir = dest_dir

    # def run(self):
    #     try:
    #         img = Image.open(self.src_path)
    #         filename = os.path.splitext(Path(self.src_path).name)[0]
    #         jpg_path = str(Path(self.dest_dir) / f"{filename}.jpg")
    #         psd_path = str(Path(self.dest_dir) / f"{filename}.psd")

    #         if img.mode != 'RGB':
    #             img = img.convert('RGB')
    #         img.save(jpg_path, 'JPEG', quality=95)
    #         self.progress.emit(jpg_path, 50)
    #         img.save(psd_path, 'PSD')
    #         self.progress.emit(psd_path, 75)

    #         with open(jpg_path, 'rb') as f:
    #             resp = HTTP_SESSION.post(
    #                 f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
    #                 files={'file': f},
    #                 headers={"Authorization": f"Bearer {load_cache().get('token', '')}"},
    #                 verify=False,
    #                 timeout=30
    #             )
    #             app_signals.api_call_status.emit(
    #                 f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
    #                 "Success" if resp.status_code == 200 else f"Failed: {resp.status_code}",
    #                 resp.status_code
    #             )
    #             resp.raise_for_status()

    #         self.progress.emit(jpg_path, 100)
    #         self.finished.emit(jpg_path, psd_path, Path(self.src_path).name)
    #     except Exception as e:
    #         logger.error(f"File conversion error for {self.src_path}: {e}")
    #         self.error.emit(str(e), Path(self.src_path).name)

    # def run(self):
    #     try:
    #         psd = PSDImage.open(self.src_path)
    #         composite = psd.composite()

    #         filename = os.path.splitext(Path(self.src_path).name)[0]
    #         jpg_path = str(Path(self.dest_dir) / f"{filename}.jpg")
    #         psd_path = str(Path(self.dest_dir) / f"{filename}.psd")

    #         if composite.mode != 'RGB':
    #             composite = composite.convert('RGB')
    #         os.makedirs(self.dest_dir, exist_ok=True)
    #         composite.save(jpg_path, format='JPEG', quality=95)
    #         self.progress.emit(jpg_path, 50)

    #         shutil.copy(self.src_path, psd_path)
    #         self.progress.emit(psd_path, 75)

    #         with open(jpg_path, 'rb') as f:
    #             resp = HTTP_SESSION.post(
    #                 f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
    #                 files={'file': f},
    #                 headers={"Authorization": f"Bearer {load_cache().get('token', '')}"},
    #                 verify=False,
    #                 timeout=30
    #             )
    #             app_signals.api_call_status.emit(
    #                 f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
    #                 "Success" if resp.status_code == 200 else f"Failed: {resp.status_code}",
    #                 resp.status_code
    #             )
    #             resp.raise_for_status()

    #         self.progress.emit(jpg_path, 100)
    #         self.finished.emit(jpg_path, psd_path, Path(self.src_path).name)

    #     except Exception as e:
    #         logger.error(f"File conversion error for {self.src_path}: {e}")
    #         self.error.emit(str(e), Path(self.src_path).name)

    def run(self):
        try:
            psd = PSDImage.open(self.src_path)

            # Composite image
            composite = psd.composite()

            # Convert to numpy array and back to PIL Image for real JPEG saving
            composite_array = np.array(composite)
            composite_image = Image.fromarray(composite_array.astype('uint8')).convert('RGB')

            # File names
            filename = os.path.splitext(Path(self.src_path).name)[0]
            jpg_path = str(Path(self.dest_dir) / f"{filename}.jpg")
            psd_path = str(Path(self.dest_dir) / f"{filename}.psd")

            # Ensure output directory exists
            os.makedirs(self.dest_dir, exist_ok=True)

            # Save real JPEG
            composite_image.save(jpg_path, format='JPEG', quality=95)
            self.progress.emit(jpg_path, 50)

            # Copy original PSD
            shutil.copy(self.src_path, psd_path)
            self.progress.emit(psd_path, 75)

            # Upload JPEG to API
            with open(jpg_path, 'rb') as f:
                resp = HTTP_SESSION.post(
                    f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
                    files={'file': f},
                    headers={"Authorization": f"Bearer {load_cache().get('token', '')}"},
                    verify=False,
                    timeout=30
                )
                app_signals.api_call_status.emit(
                    f"{BASE_DOMAIN}/api/ir_production/upload/jpg",
                    "Success" if resp.status_code == 200 else f"Failed: {resp.status_code}",
                    resp.status_code
                )
                resp.raise_for_status()

            # Emit final status
            self.progress.emit(jpg_path, 100)
            self.finished.emit(jpg_path, psd_path, Path(self.src_path).name)

        except Exception as e:
            logger.error(f"File conversion error for {self.src_path}: {e}")
            self.error.emit(str(e), Path(self.src_path).name)


from PySide6.QtWidgets import QProgressDialog
# class FileWatcherWorker(QObject):
#     status_update = Signal(str)
#     log_update = Signal(str)
#     progress_update = Signal(str, str, int)

#     _instance = None

#     def __init__(self, parent=None):
#         if FileWatcherWorker._instance is not None:
#             logger.warning("FileWatcherWorker already instantiated, skipping new instance")
#             return
#         super().__init__(parent)
#         FileWatcherWorker._instance = self
#         self.processed_tasks = set()
#         self.progress_dialog = None

#     @staticmethod
#     def get_instance(parent=None):
#         """Return the singleton instance of FileWatcherWorker."""
#         if FileWatcherWorker._instance is None:
#             FileWatcherWorker._instance = FileWatcherWorker(parent)
#         return FileWatcherWorker._instance

#     def check_connectivity(self):
#         cache = load_cache()
#         user_id = cache.get('user_id', '')
#         token = cache.get('token', '')
#         if not user_id or not token:
#             logger.error("No user_id or token found in cache for connectivity check")
#             self.log_update.emit("[API Scan] Failed: No user_id or token found in cache for connectivity check")
#             return False

#         api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}"
#         headers = {"Authorization": f"Bearer {token}"}
#         try:
#             logger.debug(f"Checking API connectivity: {api_url}")
#             self.log_update.emit(f"[API Scan] Checking API connectivity: {api_url}")
#             response = HTTP_SESSION.get(api_url, headers=headers, verify=False, timeout=10)
#             app_signals.api_call_status.emit(api_url, "Success" if response.status_code == 200 else f"Failed: {response.status_code}", response.status_code)
#             if response.status_code != 200:
#                 logger.warning(f"API connectivity check failed: {response.status_code} - {response.text}")
#                 self.log_update.emit(f"[API Scan] API connectivity check failed: {response.status_code} - {response.text}")
#                 return False
#             self.log_update.emit("[API Scan] API connectivity check passed")
#         except Exception as e:
#             logger.warning(f"API connectivity check failed: {str(e)}")
#             self.log_update.emit(f"[API Scan] API connectivity check failed: {str(e)}")
#             return False

#         if NAS_AVAILABLE:
#             nas_connection = connect_to_nas()
#             if not nas_connection:
#                 logger.warning("NAS connectivity check failed, continuing without NAS")
#                 self.log_update.emit("[API Scan] NAS connectivity check failed, continuing without NAS")
#                 return True
#             transport, sftp = nas_connection
#             try:
#                 sftp.stat("/irdev")  # Verify share exists
#                 self.log_update.emit("[API Scan] NAS share /irdev accessible")
#             except Exception as e:
#                 logger.warning(f"NAS share check failed: {str(e)}")
#                 self.log_update.emit(f"[API Scan] NAS share check failed: {str(e)}")
#                 transport.close()
#                 return True
#             transport.close()
#         return True

#     def show_progress(self, title, src_path, dest_path, action_type, item, is_nas_src, is_nas_dest):
#         try:
#             self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 0)
#             self.perform_file_transfer(src_path, dest_path, action_type, item, is_nas_src, is_nas_dest)
#         except Exception as e:
#             logger.error(f"Progress dialog error for {action_type}: {e}")
#             self.log_update.emit(f"[Progress] Failed: {action_type} progress error - {str(e)}")

#     def perform_file_transfer(self, src_path, dest_path, action_type, item, is_nas_src, is_nas_dest):
#         try:
#             self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 10)
#             if action_type.lower() == "download":
#                 if is_nas_src:
#                     nas_connection = connect_to_nas()
#                     if not nas_connection:
#                         raise Exception(f"NAS connection failed to {NAS_IP}")
#                     transport, sftp = nas_connection
#                     try:
#                         # Use NAS_SHARE for path
#                         nas_base_path = "/irdev"
#                         if not src_path.startswith("/"):
#                             src_path = f"{nas_base_path}/{src_path}"
#                         logger.debug(f"Attempting NAS download: {src_path} to {dest_path}")
#                         self.log_update.emit(f"[Transfer] Attempting NAS download: {src_path} to {dest_path}")
#                         sftp.stat(src_path)  # Check if file exists
#                         sftp.get(src_path, dest_path)
#                         transport.close()
#                     except Exception as e:
#                         transport.close()
#                         raise Exception(f"NAS download failed for {src_path}: {str(e)}")
#                 else:
#                     response = HTTP_SESSION.get(src_path, verify=False, timeout=30)
#                     response.raise_for_status()
#                     with open(dest_path, 'wb') as f:
#                         f.write(response.content)
#                 self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 50)
#                 app_signals.append_log.emit(f"[Transfer] {action_type} completed: {src_path} to {dest_path}")
#                 self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 100)
#                 app_signals.update_file_list.emit(dest_path, f"{action_type} Completed", action_type.lower(), 100, is_nas_src)
#             elif action_type.lower() == "upload":
#                 if is_nas_dest:
#                     nas_connection = connect_to_nas()
#                     if not nas_connection:
#                         raise Exception(f"NAS connection failed to {NAS_IP}")
#                     transport, sftp = nas_connection
#                     try:
#                         nas_base_path = "/irdev"
#                         if not dest_path.startswith("/"):
#                             dest_path = f"{nas_base_path}/{dest_path}"
#                         sftp.put(src_path, dest_path)
#                         transport.close()
#                     except Exception as e:
#                         transport.close()
#                         raise Exception(f"NAS upload failed for {dest_path}: {str(e)}")
#                 else:
#                     with open(src_path, 'rb') as f:
#                         response = HTTP_SESSION.post(
#                             f"{BASE_DOMAIN}/api/ir_production/upload",
#                             files={'file': f},
#                             headers={"Authorization": f"Bearer {load_cache().get('token', '')}"},
#                             verify=False,
#                             timeout=30
#                         )
#                         response.raise_for_status()
#                 self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 50)
#                 app_signals.append_log.emit(f"[Transfer] {action_type} completed: {src_path} to {dest_path}")
#                 self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 100)
#                 app_signals.update_file_list.emit(dest_path, f"{action_type} Completed", action_type.lower(), 100, is_nas_dest)
#         except Exception as e:
#             logger.error(f"File {action_type} error: {e}")
#             self.log_update.emit(f"[Transfer] Failed: {action_type} error - {str(e)}")
#             app_signals.update_file_list.emit(dest_path, f"{action_type} Failed: {str(e)}", action_type.lower(), 0, is_nas_src)
#             self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 0)

#     def run(self):
#         global FILE_WATCHER_RUNNING, LAST_API_HIT_TIME, NEXT_API_HIT_TIME
#         if not FILE_WATCHER_RUNNING:
#             logger.info("File watcher stopped due to FILE_WATCHER_RUNNING being False")
#             self.status_update.emit("File watcher stopped")
#             self.log_update.emit("[API Scan] File watcher stopped due to FILE_WATCHER_RUNNING being False")
#             return
#         try:
#             logger.debug("Starting file watcher run")
#             self.log_update.emit("[API Scan] Starting file watcher run")
#             if not self.check_connectivity():
#                 logger.warning("Connectivity check failed, will retry on next run")
#                 self.status_update.emit("Connectivity check failed, will retry")
#                 self.log_update.emit("[API Scan] Connectivity check failed")
#                 return

#             self.status_update.emit("Checking for file tasks...")
#             self.log_update.emit("[API Scan] Starting file task check")
#             app_signals.append_log.emit("[API Scan] Initiating file task check")
#             LAST_API_HIT_TIME = datetime.now(ZoneInfo("UTC"))
#             NEXT_API_HIT_TIME = LAST_API_HIT_TIME + timedelta(milliseconds=API_POLL_INTERVAL)
#             app_signals.update_timer_status.emit(
#                 f"Last API hit: {LAST_API_HIT_TIME.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
#                 f"Next API hit: {NEXT_API_HIT_TIME.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
#                 f"Interval: {API_POLL_INTERVAL/1000:.1f}s"
#             )
#             cache = load_cache()
#             logger.debug(f"Cache contents before processing: {json.dumps(cache, indent=2)}")
#             self.log_update.emit(f"[API Scan] Cache contents: {json.dumps(cache, indent=2)}")

#             user_id = cache.get('user_id', '')
#             token = cache.get('token', '')
#             if not user_id or not token:
#                 logger.error("No user_id or token found in cache, stopping file watcher")
#                 self.status_update.emit("No user_id or token found in cache")
#                 self.log_update.emit("[API Scan] Failed: No user_id or token found in cache")
#                 FILE_WATCHER_RUNNING = False
#                 return
#             headers = {"Authorization": f"Bearer {token}"}
#             max_retries = 3
#             tasks = []
#             for attempt in range(max_retries):
#                 try:
#                     api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}"
#                     logger.debug(f"Hitting API: {api_url}")
#                     app_signals.append_log.emit(f"[API Scan] Hitting API: {api_url}")
#                     response = HTTP_SESSION.get(api_url, headers=headers, verify=False, timeout=60)
#                     logger.debug(f"API response: Status={response.status_code}, Content={response.text[:500]}...")
#                     app_signals.append_log.emit(f"[API Scan] API response: Status={response.status_code}, Content={response.text[:500]}...")
#                     app_signals.api_call_status.emit(api_url, "Success" if response.status_code == 200 else f"Failed: {response.status_code}", response.status_code)
#                     if response.status_code == 401:
#                         logger.warning("Unauthorized: Token may be invalid, stopping file watcher")
#                         self.log_update.emit("[API Scan] Unauthorized: Token may be invalid")
#                         FILE_WATCHER_RUNNING = False
#                         return
#                     response.raise_for_status()
#                     response_data = response.json()
#                     logger.debug(f"Raw API response: {json.dumps(response_data, indent=2)}")
#                     self.log_update.emit(f"[API Scan] Raw API response: {json.dumps(response_data[:5], indent=2)}")
#                     tasks = response_data if isinstance(response_data, list) else response_data.get('data', [])
#                     if not isinstance(tasks, list):
#                         logger.error(f"API returned non-list tasks: {type(tasks)}, data: {tasks}")
#                         self.log_update.emit(f"[API Scan] Failed: API returned non-list tasks: {type(tasks)}")
#                         return
#                     for i, task in enumerate(tasks):
#                         if not isinstance(task, dict):
#                             logger.error(f"Invalid task at index {i}: {type(task)}, data: {task}")
#                             self.log_update.emit(f"[API Scan] Failed: Invalid task at index {i}: {type(task)}")
#                             continue
#                         if not task.get('id') or not task.get('file_path'):
#                             logger.error(f"Invalid task at index {i}: Missing id or file_path, task: {task}")
#                             self.log_update.emit(f"[API Scan] Failed: Invalid task at index {i}: Missing id or file_path")
#                             continue
#                     logger.debug(f"Tasks retrieved: {json.dumps(tasks, indent=2)}")
#                     self.log_update.emit(f"[API Scan] Tasks retrieved: {json.dumps(tasks[:5], indent=2)}")
#                     self.log_update.emit(f"[API Scan] Retrieved {len(tasks)} tasks")
#                     app_signals.append_log.emit(f"[API Scan] Retrieved {len(tasks)} tasks from API")
#                     break
#                 except RequestException as e:
#                     logger.error(f"Attempt {attempt + 1} failed fetching tasks from {api_url}: {e}")
#                     self.log_update.emit(f"[API Scan] Failed to fetch tasks (attempt {attempt + 1}): {str(e)}")
#                     if attempt == max_retries - 1:
#                         logger.warning("Max retries reached for task fetch, will retry on next run")
#                         self.status_update.emit(f"Error fetching tasks after retries: {str(e)}")
#                         self.log_update.emit(f"[API Scan] Failed to fetch tasks after retries: {str(e)}")
#                         app_signals.append_log.emit(f"[API Scan] Failed: Task fetch error after retries - {str(e)}")
#                         return

#             # Validate cache
#             cache = load_cache()
#             if not isinstance(cache.get("downloaded_files", {}), dict):
#                 logger.warning("Invalid downloaded_files in cache, resetting to dict")
#                 self.log_update.emit("[API Scan] Invalid downloaded_files in cache, resetting to dict")
#                 cache["downloaded_files"] = {}
#                 save_cache(cache)
#             if not isinstance(cache.get("downloaded_files_with_metadata", {}), dict):
#                 logger.warning("Invalid downloaded_files_with_metadata in cache, resetting to dict")
#                 self.log_update.emit("[API Scan] Invalid downloaded_files_with_metadata in cache, resetting to dict")
#                 cache["downloaded_files_with_metadata"] = {}
#                 save_cache(cache)
#             if not isinstance(cache.get("uploaded_files", []), list):
#                 logger.warning("Invalid uploaded_files in cache, resetting to list")
#                 self.log_update.emit("[API Scan] Invalid uploaded_files in cache, resetting to list")
#                 cache["uploaded_files"] = []
#                 save_cache(cache)

#             for item in tasks[:5]:
#                 if not isinstance(item, dict):
#                     logger.error(f"Invalid task item type: {type(item)}, item: {item}")
#                     self.log_update.emit(f"[API Scan] Failed: Invalid task item type: {type(item)}")
#                     continue
#                 task_key = f"{item.get('file_path', '')}:{item.get('request_type', '')}"
#                 task_id = str(item.get('id', ''))  # Ensure task_id is string
#                 logger.debug(f"Processing task: task_key={task_key}, task_id={task_id}")
#                 self.log_update.emit(f"[API Scan] Processing task: task_key={task_key}, task_id={task_id}")
#                 if task_key in self.processed_tasks or (task_id and task_id in cache.get('downloaded_files_with_metadata', {})):
#                     logger.debug(f"Skipping already processed task: {task_key} (id: {task_id})")
#                     self.log_update.emit(f"[API Scan] Skipping already processed task: {task_key} (id: {task_id})")
#                     continue
#                 file_path = item.get('file_path', '')
#                 file_name = item.get('file_name', Path(file_path).name)
#                 action_type = item.get('request_type', '').lower()
#                 is_online = 'http' in file_path.lower()
#                 local_path = str(BASE_TARGET_DIR / file_name)

#                 if action_type == "download":
#                     self.status_update.emit(f"Downloading {file_name}")
#                     self.log_update.emit(f"[API Scan] Starting download: {file_path} to {local_path}")
#                     app_signals.append_log.emit(f"[API Scan] Initiating download: {file_name}")
#                     self.show_progress(f"Downloading {file_name}", file_path, local_path, action_type, item, not is_online, False)
#                     cache = load_cache()
#                     if "downloaded_files_with_metadata" not in cache:
#                         cache["downloaded_files_with_metadata"] = {}
#                     if "downloaded_files" not in cache:
#                         cache["downloaded_files"] = {}
#                     if task_id:
#                         cache["downloaded_files_with_metadata"][task_id] = {"local_path": local_path, "api_response": item}
#                         cache["downloaded_files"][task_id] = local_path
#                     timer_response = start_timer_api(file_path, cache["token"])
#                     if timer_response:
#                         cache["timer_responses"][local_path] = timer_response
#                     save_cache(cache)
#                     self.processed_tasks.add(task_key)
                    
#                 elif action_type == "upload" and Path(local_path).exists():
#                     self.status_update.emit(f"Uploading {file_name}")
#                     self.log_update.emit(f"[API Scan] Starting upload: {local_path} to {file_path}")
#                     app_signals.append_log.emit(f"[API Scan] Initiating upload: {file_name}")
#                     self.show_progress(f"Uploading {file_name}", local_path, file_path, action_type, item, False, not is_online)
#                     cache = load_cache()
#                     cache["uploaded_files"].append(file_path)
#                     timer_response = cache.get("timer_responses", {}).get(local_path)
#                     if timer_response:
#                         end_timer_api(file_path, timer_response, cache["token"])
#                     save_cache(cache)
#                     self.processed_tasks.add(task_key)
#                 self.status_update.emit("File tasks check completed")
#                 self.log_update.emit(f"[API Scan] File tasks check completed, processed {len(tasks[:5])} tasks")
#                 app_signals.append_log.emit(f"[API Scan] Completed: Processed {len(tasks[:5])} tasks")
                
#                     if not is_online and self.parent():
#                         self.parent().convert_to_jpg_and_psd(local_path, str(Path(local_path).parent))

#         except Exception as e:
#             logger.error(f"Error processing tasks: {e}")
#             self.status_update.emit(f"Error processing tasks: {str(e)}")
#             self.log_update.emit(f"[API Scan] Failed: Error processing tasks - {str(e)}")
#             app_signals.append_log.emit(f"[API Scan] Failed: Task processing error - {str(e)}")


class FileWatcherWorker(QObject):
    status_update = Signal(str)
    log_update = Signal(str)
    progress_update = Signal(str, str, int)

    _instance = None

    def __init__(self, parent=None):
        if FileWatcherWorker._instance is not None:
            logger.warning("FileWatcherWorker already instantiated, skipping new instance")
            return
        super().__init__(parent)
        FileWatcherWorker._instance = self
        self.processed_tasks = set()
        self.progress_dialog = None

    @staticmethod
    def get_instance(parent=None):
        """Return the singleton instance of FileWatcherWorker."""
        if FileWatcherWorker._instance is None:
            FileWatcherWorker._instance = FileWatcherWorker(parent)
        return FileWatcherWorker._instance

    def check_connectivity(self):
        cache = load_cache()
        user_id = cache.get('user_id', '')
        token = cache.get('token', '')
        if not user_id or not token:
            logger.error("No user_id or token found in cache for connectivity check")
            self.log_update.emit("[API Scan] Failed: No user_id or token found in cache for connectivity check")
            return False

        api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            logger.debug(f"Checking API connectivity: {api_url}")
            self.log_update.emit(f"[API Scan] Checking API connectivity: {api_url}")
            response = HTTP_SESSION.get(api_url, headers=headers, verify=False, timeout=10)
            app_signals.api_call_status.emit(api_url, "Success" if response.status_code == 200 else f"Failed: {response.status_code}", response.status_code)
            if response.status_code != 200:
                logger.warning(f"API connectivity check failed: {response.status_code} - {response.text}")
                self.log_update.emit(f"[API Scan] API connectivity check failed: {response.status_code} - {response.text}")
                return False
            self.log_update.emit("[API Scan] API connectivity check passed")
        except Exception as e:
            logger.warning(f"API connectivity check failed: {str(e)}")
            self.log_update.emit(f"[API Scan] API connectivity check failed: {str(e)}")
            return False

        if NAS_AVAILABLE:
            nas_connection = connect_to_nas()
            if not nas_connection:
                logger.warning("NAS connectivity check failed, continuing without NAS")
                self.log_update.emit("[API Scan] NAS connectivity check failed, continuing without NAS")
                return True
            transport, sftp = nas_connection
            try:
                sftp.stat("/irdev")  # Verify share exists
                self.log_update.emit("[API Scan] NAS share /irdev accessible")
            except Exception as e:
                logger.warning(f"NAS share check failed: {str(e)}")
                self.log_update.emit(f"[API Scan] NAS share check failed: {str(e)}")
                transport.close()
                return True
            transport.close()
        return True

    def show_progress(self, title, src_path, dest_path, action_type, item, is_nas_src, is_nas_dest):
        try:
            self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 0)
            self.perform_file_transfer(src_path, dest_path, action_type, item, is_nas_src, is_nas_dest)
        except Exception as e:
            logger.error(f"Progress dialog error for {action_type}: {e}")
            self.log_update.emit(f"[Progress] Failed: {action_type} progress error - {str(e)}")

    def perform_file_transfer(self, src_path, dest_path, action_type, item, is_nas_src, is_nas_dest):
        try:
            self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 10)
            if action_type.lower() == "download":
                if is_nas_src:
                    nas_connection = connect_to_nas()
                    if not nas_connection:
                        raise Exception(f"NAS connection failed to {NAS_IP}")
                    transport, sftp = nas_connection
                    try:
                        # ✅ Convert mount path back to NAS SFTP path
                        mount_prefix = "/mnt/nas/softwaremedia/IR_uat"
                        nas_base_path = ""
                        if src_path.startswith(mount_prefix):
                            src_path = src_path.replace(mount_prefix, nas_base_path)
                        logger.debug(f"Attempting NAS download: {src_path} to {dest_path}")
                        self.log_update.emit(f"[Transfer] Attempting NAS download: {src_path} to {dest_path}")
                        sftp.stat(src_path)  # Check if file exists
                        sftp.get(src_path, dest_path)
                        transport.close()
                    except Exception as e:
                        transport.close()
                        raise Exception(f"NAS download failed for {src_path}: {str(e)}")
                else:
                    # response = HTTP_SESSION.get(src_path, verify=False, timeout=30)
                    # response.raise_for_status()
                    # with open(dest_path, 'wb') as f:
                    #     f.write(response.content)
                    start_time = time.time()
                    with HTTP_SESSION.get(src_path, stream=True, verify=False, timeout=60) as r:
                        r.raise_for_status()
                        with open(dest_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                                if chunk:
                                    f.write(chunk)
                    end_time = time.time()
                    print(f"Downloaded {Path(src_path).name} in {end_time - start_time:.2f} seconds")

                self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 50)
                app_signals.append_log.emit(f"[Transfer] {action_type} completed: {src_path} to {dest_path}")
                self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 100)
                app_signals.update_file_list.emit(dest_path, f"{action_type} Completed", action_type.lower(), 100, is_nas_src)
            elif action_type.lower() == "upload":
                if is_nas_dest:
                    nas_connection = connect_to_nas()
                    if not nas_connection:
                        raise Exception(f"NAS connection failed to {NAS_IP}")
                    transport, sftp = nas_connection
                    try:
                        nas_base_path = "/irdev"
                        if not dest_path.startswith("/"):
                            dest_path = f"{nas_base_path}/{dest_path}"
                        sftp.put(src_path, dest_path)
                        transport.close()
                    except Exception as e:
                        transport.close()
                        raise Exception(f"NAS upload failed for {dest_path}: {str(e)}")
                else:
                    with open(src_path, 'rb') as f:
                        response = HTTP_SESSION.post(
                            f"{BASE_DOMAIN}/api/ir_production/upload",
                            files={'file': f},
                            headers={"Authorization": f"Bearer {load_cache().get('token', '')}"},
                            verify=False,
                            timeout=30
                        )
                        response.raise_for_status()
                self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 50)
                app_signals.append_log.emit(f"[Transfer] {action_type} completed: {src_path} to {dest_path}")
                self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 100)
                app_signals.update_file_list.emit(dest_path, f"{action_type} Completed", action_type.lower(), 100, is_nas_dest)
        except Exception as e:
            logger.error(f"File {action_type} error: {e}")
            self.log_update.emit(f"[Transfer] Failed: {action_type} error - {str(e)}")
            app_signals.update_file_list.emit(dest_path, f"{action_type} Failed: {str(e)}", action_type.lower(), 0, is_nas_src)
            self.progress_update.emit(f"{action_type}: {Path(src_path).name}", dest_path, 0)

    def run(self):
        global FILE_WATCHER_RUNNING, LAST_API_HIT_TIME, NEXT_API_HIT_TIME
        if not FILE_WATCHER_RUNNING:
            logger.info("File watcher stopped due to FILE_WATCHER_RUNNING being False")
            self.status_update.emit("File watcher stopped")
            self.log_update.emit("[API Scan] File watcher stopped due to FILE_WATCHER_RUNNING being False")
            return
        try:
            logger.debug("Starting file watcher run")
            self.log_update.emit("[API Scan] Starting file watcher run")
            if not self.check_connectivity():
                logger.warning("Connectivity check failed, will retry on next run")
                self.status_update.emit("Connectivity check failed, will retry")
                self.log_update.emit("[API Scan] Connectivity check failed")
                return

            self.status_update.emit("Checking for file tasks...")
            self.log_update.emit("[API Scan] Starting file task check")
            app_signals.append_log.emit("[API Scan] Initiating file task check")
            LAST_API_HIT_TIME = datetime.now(ZoneInfo("UTC"))
            NEXT_API_HIT_TIME = LAST_API_HIT_TIME + timedelta(milliseconds=API_POLL_INTERVAL)
            app_signals.update_timer_status.emit(
                f"Last API hit: {LAST_API_HIT_TIME.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
                f"Next API hit: {NEXT_API_HIT_TIME.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
                f"Interval: {API_POLL_INTERVAL/1000:.1f}s"
            )
            cache = load_cache()
            logger.debug(f"Cache contents before processing: {json.dumps(cache, indent=2)}")
            self.log_update.emit(f"[API Scan] Cache contents: {json.dumps(cache, indent=2)}")

            user_id = cache.get('user_id', '')
            token = cache.get('token', '')
            if not user_id or not token:
                logger.error("No user_id or token found in cache, stopping file watcher")
                self.status_update.emit("No user_id or token found in cache")
                self.log_update.emit("[API Scan] Failed: No user_id or token found in cache")
                FILE_WATCHER_RUNNING = False
                return
            headers = {"Authorization": f"Bearer {token}"}
            max_retries = 3
            tasks = []
            for attempt in range(max_retries):
                try:
                    api_url = f"{DOWNLOAD_UPLOAD_API}?user_id={quote(user_id)}"
                    logger.debug(f"Hitting API: {api_url}")
                    app_signals.append_log.emit(f"[API Scan] Hitting API: {api_url}")
                    response = HTTP_SESSION.get(api_url, headers=headers, verify=False, timeout=60)
                    logger.debug(f"API response: Status={response.status_code}, Content={response.text[:500]}...")
                    app_signals.append_log.emit(f"[API Scan] API response: Status={response.status_code}, Content={response.text[:500]}...")
                    app_signals.api_call_status.emit(api_url, "Success" if response.status_code == 200 else f"Failed: {response.status_code}", response.status_code)
                    if response.status_code == 401:
                        logger.warning("Unauthorized: Token may be invalid, stopping file watcher")
                        self.log_update.emit("[API Scan] Unauthorized: Token may be invalid")
                        FILE_WATCHER_RUNNING = False
                        return
                    response.raise_for_status()
                    response_data = response.json()
                    logger.debug(f"Raw API response: {json.dumps(response_data, indent=2)}")
                    self.log_update.emit(f"[API Scan] Raw API response: {json.dumps(response_data[:5], indent=2)}")
                    tasks = response_data if isinstance(response_data, list) else response_data.get('data', [])
                    if not isinstance(tasks, list):
                        logger.error(f"API returned non-list tasks: {type(tasks)}, data: {tasks}")
                        self.log_update.emit(f"[API Scan] Failed: API returned non-list tasks: {type(tasks)}")
                        return
                    for i, task in enumerate(tasks):
                        if not isinstance(task, dict):
                            logger.error(f"Invalid task at index {i}: {type(task)}, data: {task}")
                            self.log_update.emit(f"[API Scan] Failed: Invalid task at index {i}: {type(task)}")
                            continue
                        if not task.get('id') or not task.get('file_path'):
                            logger.error(f"Invalid task at index {i}: Missing id or file_path, task: {task}")
                            self.log_update.emit(f"[API Scan] Failed: Invalid task at index {i}: Missing id or file_path")
                            continue
                    logger.debug(f"Tasks retrieved: {json.dumps(tasks, indent=2)}")
                    self.log_update.emit(f"[API Scan] Tasks retrieved: {json.dumps(tasks[:5], indent=2)}")
                    self.log_update.emit(f"[API Scan] Retrieved {len(tasks)} tasks")
                    app_signals.append_log.emit(f"[API Scan] Retrieved {len(tasks)} tasks from API")
                    break
                except RequestException as e:
                    logger.error(f"Attempt {attempt + 1} failed fetching tasks from {api_url}: {e}")
                    self.log_update.emit(f"[API Scan] Failed to fetch tasks (attempt {attempt + 1}): {str(e)}")
                    if attempt == max_retries - 1:
                        logger.warning("Max retries reached for task fetch, will retry on next run")
                        self.status_update.emit(f"Error fetching tasks after retries: {str(e)}")
                        self.log_update.emit(f"[API Scan] Failed to fetch tasks after retries: {str(e)}")
                        app_signals.append_log.emit(f"[API Scan] Failed: Task fetch error after retries - {str(e)}")
                        return

            # Validate cache
            cache = load_cache()
            if not isinstance(cache.get("downloaded_files", {}), dict):
                logger.warning("Invalid downloaded_files in cache, resetting to dict")
                self.log_update.emit("[API Scan] Invalid downloaded_files in cache, resetting to dict")
                cache["downloaded_files"] = {}
                save_cache(cache)
            if not isinstance(cache.get("downloaded_files_with_metadata", {}), dict):
                logger.warning("Invalid downloaded_files_with_metadata in cache, resetting to dict")
                self.log_update.emit("[API Scan] Invalid downloaded_files_with_metadata in cache, resetting to dict")
                cache["downloaded_files_with_metadata"] = {}
                save_cache(cache)
            if not isinstance(cache.get("uploaded_files", []), list):
                logger.warning("Invalid uploaded_files in cache, resetting to list")
                self.log_update.emit("[API Scan] Invalid uploaded_files in cache, resetting to list")
                cache["uploaded_files"] = []
                save_cache(cache)
            if not isinstance(cache.get("uploaded_files_with_metadata", {}), dict):
                logger.warning("Invalid uploaded_files_with_metadata in cache, resetting to dict")
                self.log_update.emit("[API Scan] Invalid uploaded_files_with_metadata in cache, resetting to dict")
                cache["uploaded_files_with_metadata"] = {}
                save_cache(cache)

            for item in tasks:  # Process all tasks
                if not isinstance(item, dict):
                    logger.error(f"Invalid task item type: {type(item)}, item: {item}")
                    self.log_update.emit(f"[API Scan] Failed: Invalid task item type: {type(item)}")
                    continue
                task_id = str(item.get('id', ''))  # Ensure task_id is string
                file_path = item.get('file_path', '')
                # 🔁 Path conversion from SFTP-style path to actual NAS mount path
                SFTP_PREFIX = "/image.test"
                NAS_MOUNT_PREFIX = "/mnt/nas/softwaremedia/IR_uat/image.test"
                if file_path.startswith(SFTP_PREFIX):
                    file_path = file_path.replace(SFTP_PREFIX, NAS_MOUNT_PREFIX)

                # file_name = item.get('file_name', Path(file_path).name)
                file_name = Path(file_path).name
                action_type = item.get('request_type', '').lower()
                task_key = f"{task_id}:{action_type}"  # Use task_id to avoid conflicts
                logger.debug(f"Processing task: task_key={task_key}, task_id={task_id}")
                self.log_update.emit(f"[API Scan] Processing task: task_key={task_key}, task_id={task_id}")
                if task_key in self.processed_tasks:
                    logger.debug(f"Skipping already processed task: {task_key} (id: {task_id})")
                    self.log_update.emit(f"[API Scan] Skipping already processed task: {task_key} (id: {task_id})")
                    continue
                is_online = 'http' in file_path.lower()
                local_path = str(BASE_TARGET_DIR / file_name)
                
                # ✅ Skip if file already exists
                # if Path(local_path).exists():
                #     logger.info(f"Skipping download: {local_path} already exists")
                #     self.log_update.emit(f"[API Scan] Skipping download: {local_path} already exists")
                #     self.processed_tasks.add(task_key)  # Optional to avoid rechecking next time
                #     continue

                if action_type == "download":
                    self.status_update.emit(f"Downloading {file_name}")
                    self.log_update.emit(f"[API Scan] Starting download: {file_path} to {local_path}")
                    app_signals.append_log.emit(f"[API Scan] Initiating download: {file_name}")
                    self.perform_file_transfer(file_path, local_path, action_type, item, not is_online, False)
                    cache = load_cache()
                    if "downloaded_files_with_metadata" not in cache:
                        cache["downloaded_files_with_metadata"] = {}
                    if "downloaded_files" not in cache:
                        cache["downloaded_files"] = {}
                    if task_id:
                        cache["downloaded_files_with_metadata"][task_id] = {"local_path": local_path, "api_response": item}
                        cache["downloaded_files"][task_id] = local_path
                    timer_response = start_timer_api(file_path, cache["token"])
                    if timer_response:
                        cache["timer_responses"][local_path] = timer_response
                    save_cache(cache)
                    self.processed_tasks.add(task_key)
                    # if not is_online and self.parent():
                    #     self.parent().convert_to_jpg_and_psd(local_path, str(Path(local_path).parent))
                    self.log_update.emit(f"[API Scan] Download completed for {file_name} without conversion")
                    app_signals.append_log.emit(f"[API Scan] Download completed for {file_name} without conversion")
                elif action_type == "upload":
                    self.status_update.emit(f"Uploading {file_name}")
                    self.log_update.emit(f"[API Scan] Starting upload: {local_path} to {file_path}")
                    app_signals.append_log.emit(f"[API Scan] Initiating upload: {file_name}")
                    cache = load_cache()
                    if "uploaded_files" not in cache:
                        cache["uploaded_files"] = []
                    if "uploaded_files_with_metadata" not in cache:
                        cache["uploaded_files_with_metadata"] = {}
                    cache["uploaded_files"].append(local_path)
                    if task_id:
                        cache["uploaded_files_with_metadata"][task_id] = {"local_path": local_path, "api_response": item}
                    save_cache(cache)
                    if Path(local_path).exists():
                        self.show_progress(f"Uploading {file_name}", local_path, file_path, action_type, item, False, not is_online)
                        timer_response = cache.get("timer_responses", {}).get(local_path)
                        if timer_response:
                            end_timer_api(file_path, timer_response, cache["token"])
                    else:
                        self.log_update.emit(f"[API Scan] Upload skipped: {local_path} does not exist")
                        app_signals.update_file_list.emit(local_path, "Upload Failed: File not found", action_type, 0, not is_online)
                    self.processed_tasks.add(task_key)
                self.status_update.emit("File tasks check completed")
                self.log_update.emit(f"[API Scan] File tasks check completed, processed {len(tasks)} tasks")
                app_signals.append_log.emit(f"[API Scan] Completed: Processed {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"Error processing tasks: {e}")
            self.status_update.emit(f"Error processing tasks: {str(e)}")
            self.log_update.emit(f"[API Scan] Failed: Error processing tasks - {str(e)}")
            app_signals.append_log.emit(f"[API Scan] Failed: Task processing error - {str(e)}")


class LogWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PremediaApp Log")
        self.setWindowIcon(load_icon(ICON_PATH, "log window"))
        self.setMinimumSize(700, 400)
        self.resize(700, 400)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.status_bar = QStatusBar(self)
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.status_bar)
        self.setLayout(layout)
        self.load_logs()
        app_signals.append_log.connect(self.append_log, Qt.QueuedConnection)
        app_signals.api_call_status.connect(self.append_api_status, Qt.QueuedConnection)
        app_signals.update_status.connect(self.status_bar.showMessage, Qt.QueuedConnection)
        app_signals.update_timer_status.connect(self.update_timer_status, Qt.QueuedConnection)
        logger.info("LogWindow initialized")
        app_signals.append_log.emit("[Log] LogWindow initialized")

    def load_logs(self):
        try:
            log_file = log_dir / "app.log"
            if log_file.exists():
                with log_file.open("r") as f:
                    lines = f.readlines()
                self.text_edit.setPlainText("".join(lines[-200:]))
                self.text_edit.moveCursor(QTextCursor.End)
                self.status_bar.showMessage("Logs loaded")
                app_signals.append_log.emit("[Log] Loaded existing logs from app.log")
            else:
                self.status_bar.showMessage("No log file found")
                app_signals.append_log.emit("[Log] No log file found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load logs: {e}")
            self.text_edit.setPlainText(f"Failed to load logs: {e}")
            self.status_bar.showMessage(f"Failed to load logs: {str(e)}")
            app_signals.append_log.emit(f"[Log] Failed to load logs: {str(e)}")

    def append_log(self, message):
        try:
            if "[API Scan]" in message:
                self.text_edit.append(f"<b>{message}</b>")
            else:
                self.text_edit.append(message)
            lines = self.text_edit.toPlainText().splitlines()
            if len(lines) > 200:
                self.text_edit.setPlainText("\n".join(lines[-200:]))
            self.text_edit.moveCursor(QTextCursor.End)
            self.text_edit.ensureCursorVisible()
            QApplication.processEvents()
        except Exception as e:
            logger.error(f"Failed to append log: {e}")
            app_signals.append_log.emit(f"[Log] Failed to append log: {str(e)}")

    def append_api_status(self, endpoint, status, status_code):
        try:
            log_msg = f"[API Scan] API Call: {endpoint} | Status: {status} | Code: {status_code}"
            self.text_edit.append(f"<b>{log_msg}</b>")
            lines = self.text_edit.toPlainText().splitlines()
            if len(lines) > 200:
                self.text_edit.setPlainText("\n".join(lines[-200:]))
            self.text_edit.moveCursor(QTextCursor.End)
            self.text_edit.ensureCursorVisible()
            QApplication.processEvents()
            app_signals.append_log.emit(log_msg)
        except Exception as e:
            logger.error(f"Failed to append API status: {e}")
            app_signals.append_log.emit(f"[Log] Failed to append API status: {str(e)}")

    def update_timer_status(self, message):
        try:
            self.status_bar.showMessage(message)
            app_signals.append_log.emit(f"[Timer] {message}")
        except Exception as e:
            logger.error(f"Failed to update timer status: {e}")
            app_signals.append_log.emit(f"[Timer] Failed to update timer status: {str(e)}")

    def closeEvent(self, event):
        try:
            app_signals.append_log.disconnect(self.append_log)
            app_signals.api_call_status.disconnect(self.append_api_status)
            app_signals.update_status.disconnect(self.status_bar.showMessage)
            app_signals.update_timer_status.disconnect(self.update_timer_status)
        except Exception:
            pass
        super().closeEvent(event)

class FileListWindow(QDialog):
    def __init__(self, file_type, parent=None):
        super().__init__(parent)
        self.file_type = file_type.lower()
        self.setWindowTitle(f"{file_type.capitalize()} Files")
        self.setWindowIcon(load_icon(ICON_PATH, f"{file_type} files window"))
        self.setMinimumSize(800, 400)
        self.resize(800, 400)
        logger.debug(f"Initializing FileListWindow for file_type: {self.file_type}")
        app_signals.append_log.emit(f"[Files] Initializing FileListWindow for {self.file_type}")

        self.table = QTableWidget(self)
        self.table.setColumnCount(6 if self.file_type == "downloaded" else 5)
        headers = ["File Path", "Open Folder", "Open in Photoshop", "Status", "Progress"]
        if self.file_type == "downloaded":
            headers.insert(3, "Source")
        self.table.setHorizontalHeaderLabels(headers)
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

        try:
            self.load_files()
        except Exception as e:
            logger.error(f"Error loading files in FileListWindow: {e}")
            app_signals.append_log.emit(f"[Files] Failed to load files for {self.file_type}: {str(e)}")

        app_signals.update_file_list.connect(self.update_file_list, Qt.QueuedConnection)
        self.file_watcher = FileWatcherWorker.get_instance(parent=self)  # Use singleton
        self.file_watcher.progress_update.connect(self.update_progress, Qt.QueuedConnection)

    # def load_files(self):
    #     """Load files into the table based on file_type."""
    #     try:
    #         cache = load_cache()
    #         logger.debug(f"Loading files for {self.file_type}, cache: {json.dumps(cache, indent=2)}")
    #         app_signals.append_log.emit(f"[Files] Loading files for {self.file_type}")
    #         files = cache.get(f"{self.file_type}_files", {}) if self.file_type == "downloaded" else cache.get(f"{self.file_type}_files", [])
    #         logger.debug(f"Files retrieved: {files}")
    #         self.table.setRowCount(0)

    #         file_list = files.items() if isinstance(files, dict) else enumerate(files)
    #         for task_id, file_path in file_list:
    #             row = self.table.rowCount()
    #             self.table.insertRow(row)
    #             filename = Path(file_path).name
    #             path_item = QTableWidgetItem(filename)
    #             self.table.setItem(row, 0, path_item)

    #             folder_btn = QPushButton()
    #             folder_btn.setIcon(load_icon(FOLDER_ICON_PATH, "folder"))
    #             folder_btn.setIconSize(QSize(24, 24))
    #             folder_btn.clicked.connect(lambda _, p=file_path: self.open_folder(p))
    #             self.table.setCellWidget(row, 1, folder_btn)

    #             photoshop_btn = QPushButton()
    #             photoshop_btn.setIcon(load_icon(PHOTOSHOP_ICON_PATH, "photoshop"))
    #             photoshop_btn.setIconSize(QSize(24, 24))
    #             photoshop_btn.clicked.connect(lambda _, p=file_path: self.open_with_photoshop(p))
    #             self.table.setCellWidget(row, 2, photoshop_btn)

    #             if self.file_type == "downloaded":
    #                 source = cache.get("downloaded_files_with_metadata", {}).get(task_id, {}).get("api_response", {}).get("file_path", "Unknown")
    #                 source_item = QTableWidgetItem(source)
    #                 self.table.setItem(row, 3, source_item)
    #                 status_col = 4
    #                 progress_col = 5
    #             else:
    #                 status_col = 3
    #                 progress_col = 4

    #             status_item = QTableWidgetItem("Completed")
    #             self.table.setItem(row, status_col, status_item)
    #             progress_bar = QProgressBar(self)
    #             progress_bar.setMinimum(0)
    #             progress_bar.setMaximum(100)
    #             progress_bar.setValue(100)
    #             progress_bar.setFixedHeight(20)
    #             self.table.setCellWidget(row, progress_col, progress_bar)

    #         self.table.resizeColumnsToContents()
    #         app_signals.append_log.emit(f"[Files] Loaded {len(files)} {self.file_type} files")
    #     except Exception as e:
    #         logger.error(f"Error in load_files for {self.file_type}: {e}")
    #         app_signals.append_log.emit(f"[Files] Failed to load {self.file_type} files: {str(e)}")
    #         raise

    def load_files(self):
        """Load files into the table based on file_type."""
        try:
            cache = load_cache()
            logger.debug(f"Loading files for {self.file_type}, cache: {json.dumps(cache, indent=2)}")
            app_signals.append_log.emit(f"[Files] Loading files for {self.file_type}")
            files = cache.get(f"{self.file_type}_files", {}) if self.file_type == "downloaded" else cache.get(f"{self.file_type}_files", [])
            logger.debug(f"Files retrieved: {files}")
            self.table.setRowCount(0)

            file_list = files.items() if isinstance(files, dict) else enumerate(files)
            for task_id, file_path in file_list:
                row = self.table.rowCount()
                self.table.insertRow(row)
                filename = Path(file_path).name
                path_item = QTableWidgetItem(filename)
                self.table.setItem(row, 0, path_item)

                folder_btn = QPushButton()
                folder_btn.setIcon(load_icon(FOLDER_ICON_PATH, "folder"))
                folder_btn.setIconSize(QSize(24, 24))
                folder_btn.clicked.connect(lambda _, p=file_path: self.open_folder(p))
                self.table.setCellWidget(row, 1, folder_btn)

                photoshop_btn = QPushButton()
                photoshop_btn.setIcon(load_icon(PHOTOSHOP_ICON_PATH, "photoshop"))
                photoshop_btn.setIconSize(QSize(24, 24))
                photoshop_btn.clicked.connect(lambda _, p=file_path: self.open_with_photoshop(p))
                self.table.setCellWidget(row, 2, photoshop_btn)

                if self.file_type == "downloaded":
                    source = cache.get("downloaded_files_with_metadata", {}).get(task_id, {}).get("api_response", {}).get("file_path", "Unknown")
                    source_item = QTableWidgetItem(source)
                    self.table.setItem(row, 3, source_item)
                    status_col = 4
                    progress_col = 5
                else:  # For uploaded files
                    source = cache.get("uploaded_files_with_metadata", {}).get(task_id, {}).get("api_response", {}).get("file_path", file_path)
                    source_item = QTableWidgetItem(source)
                    self.table.setItem(row, 3, source_item)
                    status_col = 4
                    progress_col = 5

                status_item = QTableWidgetItem("Completed" if Path(file_path).exists() else "Failed")
                self.table.setItem(row, status_col, status_item)
                progress_bar = QProgressBar(self)
                progress_bar.setMinimum(0)
                progress_bar.setMaximum(100)
                progress_bar.setValue(100 if Path(file_path).exists() else 0)
                progress_bar.setFixedHeight(20)
                self.table.setCellWidget(row, progress_col, progress_bar)

            self.table.resizeColumnsToContents()
            app_signals.append_log.emit(f"[Files] Loaded {len(files)} {self.file_type} files")
        except Exception as e:
            logger.error(f"Error in load_files for {self.file_type}: {e}")
            app_signals.append_log.emit(f"[Files] Failed to load {self.file_type} files: {str(e)}")
            raise

    def open_with_photoshop(self, file_path):
        """Dynamically find Adobe Photoshop path and open the specified file."""
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
                logger.warning(f"Unsupported platform for Photoshop: {system}")
                app_signals.append_log.emit(f"[Photoshop] Unsupported platform: {system}")
                app_signals.update_status.emit(f"Unsupported platform: {system}")
                return

            if system == "Darwin":
                subprocess.run(["open", "-a", photoshop_path, file_path], check=True)
            else:
                subprocess.run([photoshop_path, file_path], check=True)

            logger.info(f"Opened {Path(file_path).name} in Photoshop at {photoshop_path}")
            app_signals.append_log.emit(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
            app_signals.update_status.emit(f"Opened {Path(file_path).name} in Photoshop")

        except Exception as e:
            logger.error(f"Failed to open {file_path} in Photoshop: {e}")
            app_signals.append_log.emit(f"[Photoshop] Failed: Error opening {Path(file_path).name} - {str(e)}")
            app_signals.update_status.emit(f"Failed to open {Path(file_path).name} in Photoshop: {str(e)}")

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

    def update_file_list(self, file_path, status, action_type, progress, is_nas_src):
        """Update the table with file transfer status."""
        if action_type != self.file_type:
            return
        try:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0) and self.table.item(row, 0).text() == Path(file_path).name:
                    status_col = 4 if self.file_type == "downloaded" else 3
                    progress_col = 5 if self.file_type == "downloaded" else 4
                    self.table.item(row, status_col).setText(status)
                    progress_bar = self.table.cellWidget(row, progress_col)
                    if progress == 100:
                        progress_bar = QProgressBar(self)
                        progress_bar.setMinimum(0)
                        progress_bar.setMaximum(100)
                        progress_bar.setValue(100)
                        progress_bar.setFixedHeight(20)
                        self.table.setCellWidget(row, progress_col, progress_bar)
                    else:
                        if not progress_bar or isinstance(progress_bar, QWidget):
                            progress_bar = QProgressBar(self)
                            progress_bar.setMinimum(0)
                            progress_bar.setMaximum(100)
                            progress_bar.setFixedHeight(20)
                            self.table.setCellWidget(row, progress_col, progress_bar)
                        progress_bar.setValue(progress)
                    if self.file_type == "downloaded":
                        self.table.item(row, 3).setText("NAS" if is_nas_src else "DOMAIN")
                    self.table.resizeColumnsToContents()
                    app_signals.append_log.emit(f"[Files] Updated {self.file_type} file list: {Path(file_path).name}")
                    return

            row = self.table.rowCount()
            self.table.insertRow(row)
            path_item = QTableWidgetItem(Path(file_path).name)
            self.table.setItem(row, 0, path_item)

            folder_btn = QPushButton()
            folder_btn.setIcon(load_icon(FOLDER_ICON_PATH, "folder"))
            folder_btn.setIconSize(QSize(24, 24))
            folder_btn.clicked.connect(lambda _, p=file_path: self.open_folder(p))
            self.table.setCellWidget(row, 1, folder_btn)

            photoshop_btn = QPushButton()
            photoshop_btn.setIcon(load_icon(PHOTOSHOP_ICON_PATH, "photoshop"))
            photoshop_btn.setIconSize(QSize(24, 24))
            photoshop_btn.clicked.connect(lambda _, p=file_path: self.open_with_photoshop(p))
            self.table.setCellWidget(row, 2, photoshop_btn)

            if self.file_type == "downloaded":
                source_item = QTableWidgetItem("NAS" if is_nas_src else "DOMAIN")
                self.table.setItem(row, 3, source_item)
                status_col = 4
                progress_col = 5
            else:
                status_col = 3
                progress_col = 4

            status_item = QTableWidgetItem(status)
            self.table.setItem(row, status_col, status_item)

            progress_bar = QProgressBar(self)
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(progress)
            progress_bar.setFixedHeight(20)
            self.table.setCellWidget(row, progress_col, progress_bar)

            self.table.resizeColumnsToContents()
            app_signals.append_log.emit(f"[Files] Added {Path(file_path).name} to {self.file_type} list")
        except Exception as e:
            logger.error(f"Error updating file list: {e}")
            app_signals.append_log.emit(f"[Files] Failed to update {self.file_type} file list: {str(e)}")

    def update_progress(self, title, file_path, progress):
        """Update progress for a file in the table."""
        try:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0) and self.table.item(row, 0).text() == Path(file_path).name:
                    progress_col = 5 if self.file_type == "downloaded" else 4
                    progress_bar = self.table.cellWidget(row, progress_col)
                    if not progress_bar or isinstance(progress_bar, QWidget):
                        progress_bar = QProgressBar(self)
                        progress_bar.setMinimum(0)
                        progress_bar.setMaximum(100)
                        progress_bar.setFixedHeight(20)
                        self.table.setCellWidget(row, progress_col, progress_bar)
                    progress_bar.setValue(progress)
                    app_signals.append_log.emit(f"[Files] Progress updated for {Path(file_path).name}: {progress}%")
                    return
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            app_signals.append_log.emit(f"[Files] Failed to update progress: {str(e)}")


# LoginWorker (provided, with fixes)

class LoginWorker(QObject):
    success = Signal(dict)
    failure = Signal(str)
    
    def __init__(self, username, password, remember_me, tray_icon, status_bar):
        super().__init__()
        self.username = username
        self.password = password
        self.rememberme = remember_me
        self.tray_icon = tray_icon
        self.status_bar = status_bar
    
    def run(self):
        try:
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
            token_resp = session.post(
                OAUTH_URL,
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "client_id": "hZBc4VyhUSQgZobyjdVH7ZPk4WRey2BIjqws_UxF5cM",
                    "client_secret": "crazy-cloud",
                    "scope": "pm_client"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=False,  # Enable SSL verification
                timeout=60
            )
            logger.debug(f"Token response raw: {token_resp.text}")
            app_signals.api_call_status.emit(
                OAUTH_URL,
                f"Status: {token_resp.status_code}, Response: {token_resp.text}",
                token_resp.status_code
            )
            app_signals.append_log.emit(f"[Login] Token API response: {token_resp.status_code}, {token_resp.text}")
            
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
            
            logger.debug("Emitting success signal")
            self.success.emit(user_info)
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

class LoginDialog(QDialog):
    def __init__(self, tray_icon, on_success_callback=None):
        super().__init__()
        self.is_logged_in = False
        self.setWindowIcon(load_icon(ICON_PATH, "login dialog"))
        self.setWindowTitle("PremediaApp Login")
        self.tray_icon = tray_icon
        self.on_success_callback = on_success_callback
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        # Load UI
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Create status bar
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setFixedHeight(20)
        self.status_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Add status bar to layout
        main_layout = QVBoxLayout()
        main_layout.addStretch(1)
        main_layout.addWidget(self.status_bar, stretch=0)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        self.setLayout(main_layout)

        # Initialize tray menu
        self.tray_menu = QMenu()
        self.login_action = QAction("Login", self)
        self.logout_action = QAction("Logout", self)
        self.exit_action = QAction("Exit", self)
        self.login_action.triggered.connect(self.show)
        self.logout_action.triggered.connect(self.logout)
        self.exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(self.login_action)
        self.tray_menu.addAction(self.logout_action)
        self.tray_menu.addAction(self.exit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.update_tray_menu()

        # Check cache for valid token
        cache = load_cache()
        if cache.get("token") and cache.get("user"):
            self.is_logged_in = True
            self.update_tray_menu()
            logger.info(f"Auto-login from cache for user: {cache['user']}")
            app_signals.append_log.emit(f"[Login] Auto-login from cache for user: {cache['user']}")

        # Load saved credentials
        if cache.get("saved_username") and cache.get("saved_password"):
            self.ui.usernametxt.setText(cache["saved_username"])
            self.ui.passwordtxt.setText(cache["saved_password"])
            self.ui.rememberme.setChecked(True)
            app_signals.append_log.emit("[Login] Loaded saved credentials from cache")
            self.status_bar.showMessage("Loaded saved credentials")
        else:
            app_signals.append_log.emit("[Login] No saved credentials found in cache")
            self.status_bar.showMessage("No saved credentials found")

        # Connect signals
        app_signals.update_status.connect(self.status_bar.showMessage, Qt.QueuedConnection)
        self.ui.buttonBox.accepted.connect(self.handle_login)

        self.progress = None
        logger.debug("[Login] LoginDialog initialized")
        app_signals.append_log.emit("[Login] Initializing LoginDialog")
        self.status_bar.showMessage("Login dialog initialized")

        self.resize(764, 669)

    def update_tray_menu(self):
        self.login_action.setVisible(not self.is_logged_in)
        self.logout_action.setVisible(self.is_logged_in)
        logger.debug(f"Updated tray menu: logged_in={self.is_logged_in}, actions=[{', '.join([action.text() for action in self.tray_menu.actions()])}]")
        app_signals.append_log.emit(f"[Tray] Updated menu: Login={not self.is_logged_in}, Logout={self.is_logged_in}")
        self.tray_icon.setContextMenu(self.tray_menu)  # Refresh menu
        self.tray_icon.show()  # Ensure tray icon is visible

    def logout(self):
        try:
            self.is_logged_in = False
            self.update_tray_menu()
            cache = load_cache()
            cache["token"] = ""
            cache["saved_username"] = "" if not self.ui.rememberme.isChecked() else cache["saved_username"]
            cache["saved_password"] = "" if not self.ui.rememberme.isChecked() else cache["saved_password"]
            save_cache(cache)
            logger.info("Logged out successfully")
            app_signals.append_log.emit("[Login] Logged out successfully")
            self.status_bar.showMessage("Logged out successfully")
            self.show()
        except Exception as e:
            logger.error(f"Logout error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Logout error - {str(e)}")
            self.status_bar.showMessage(f"Logout error: {str(e)}")

    def show_progress(self, message):
        try:
            self.progress = QProgressDialog(message, None, 0, 0, self)
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.setCancelButton(None)
            self.progress.setMinimumDuration(0)
            self.progress.setWindowTitle("Please wait")
            try:
                self.progress.setWindowIcon(load_icon(ICON_PATH, "progress dialog"))
            except Exception as e:
                logger.warning(f"Failed to load progress dialog icon: {e}")
            self.progress.show()
            QApplication.processEvents()
            logger.debug(f"Progress dialog shown: {message}, visible={self.progress.isVisible()}")
            app_signals.append_log.emit(f"[Login] Showing progress: {message}")
            self.status_bar.showMessage(message)
        except Exception as e:
            logger.error(f"Progress dialog error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Progress dialog error - {str(e)}")
            self.status_bar.showMessage(f"Progress error: {str(e)}")

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
            logger.info("Login process started")
            app_signals.append_log.emit("[Login] Login process started")
            self.status_bar.showMessage("Login process started")
        except Exception as e:
            logger.error(f"Error in handle_login: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Handle login error - {str(e)}")
            self.status_bar.showMessage(f"Login error: {str(e)}")
            if self.progress:
                self.progress.close()

    def perform_login(self, username, password):
        try:
            logger.debug("Starting login thread")
            self.thread = QThread()
            self.worker = LoginWorker(username, password, self.ui.rememberme.isChecked(), tray_icon=self.tray_icon, status_bar=self.status_bar)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.success.connect(self.on_login_success)
            self.worker.failure.connect(self.on_login_failure)
            self.worker.success.connect(self.thread.quit)
            self.worker.failure.connect(self.thread.quit)
            self.worker.success.connect(self.worker.deleteLater)
            self.worker.failure.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
            app_signals.append_log.emit(f"[Login] Starting login thread for user: {username}")
            self.status_bar.showMessage(f"Starting login for {username}")
        except Exception as e:
            logger.error(f"Login thread error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Login thread error - {str(e)}")
            self.status_bar.showMessage(f"Login thread error: {str(e)}")
            if self.progress:
                self.progress.close()

    def on_login_success(self, user_info):
        try:
            if self.progress:
                self.progress.close()
            self.is_logged_in = True
            self.update_tray_menu()
            if self.tray_icon:
                self.tray_icon.show()
            logger.debug(f"Login success: {user_info}")
            logger.debug("Showing success QMessageBox")
            QMessageBox.information(self, "Login Success", f"Welcome: {user_info.get('uid', 'Unknown')}")
            app_signals.append_log.emit(f"[Login] Login successful for user: {user_info.get('uid', 'Unknown')}")
            self.status_bar.showMessage(f"Login successful for user: {user_info.get('uid', 'Unknown')}")
            if self.on_success_callback:
                self.on_success_callback()
            self.accept()
        except Exception as e:
            logger.error(f"Error in on_login_success: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Login success handling error - {str(e)}")
            self.status_bar.showMessage(f"Login success error: {str(e)}")

    def on_login_failure(self, error_msg):
        try:
            if self.progress:
                self.progress.close()
            logger.debug(f"Login failure: {error_msg}")
            QMessageBox.critical(self, "Login Failed", error_msg)
            app_signals.append_log.emit(f"[Login] Failed: Login error - {error_msg}")
            self.status_bar.showMessage(f"Login failed: {error_msg}")
        except Exception as e:
            logger.error(f"Error in on_login_failure: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Login failure handling error - {str(e)}")
            self.status_bar.showMessage(f"Login failure error: {str(e)}")

    def closeEvent(self, event):
        try:
            app_signals.update_status.disconnect(self.status_bar.showMessage)
        except Exception:
            pass
        super().closeEvent(event)
    def __init__(self, tray_icon, on_success_callback=None):
        super().__init__()

        self.setWindowIcon(load_icon(ICON_PATH, "login dialog"))
        self.setWindowTitle("PremediaApp Login")
        self.tray_icon = tray_icon
        self.on_success_callback = on_success_callback
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        # Load UI
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Create status bar
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setFixedHeight(20)
        self.status_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Add status bar to layout
        main_layout = QVBoxLayout()
        main_layout.addStretch(1)
        main_layout.addWidget(self.status_bar, stretch=0)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        self.setLayout(main_layout)

        # Set size policy
        try:
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        except Exception as e:
            logger.warning(f"QSizePolicy not available: {e}")
            app_signals.append_log.emit(f"[Init] QSizePolicy not available: {str(e)}")

        # Load saved credentials
        cache = load_cache()
        if cache.get("saved_username") and cache.get("saved_password"):
            self.ui.usernametxt.setText(cache["saved_username"])
            self.ui.passwordtxt.setText(cache["saved_password"])
            self.ui.rememberme.setChecked(True)
            app_signals.append_log.emit("[Login] Loaded saved credentials from cache")
            self.status_bar.showMessage("Loaded saved credentials")
        else:
            app_signals.append_log.emit("[Login] No saved credentials found in cache")
            self.status_bar.showMessage("No saved credentials found")

        # Connect signals
        app_signals.update_status.connect(self.status_bar.showMessage, Qt.QueuedConnection)
        self.ui.buttonBox.accepted.connect(self.handle_login)

        self.progress = None
        logger.debug("[Login] LoginDialog initialized")
        app_signals.append_log.emit("[Login] Initializing LoginDialog")
        self.status_bar.showMessage("Login dialog initialized")

        self.resize(764, 669)

    def show_progress(self, message):
        try:
            self.progress = QProgressDialog(message, None, 0, 0, self)
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.setCancelButton(None)
            self.progress.setMinimumDuration(0)
            self.progress.setWindowTitle("Please wait")
            try:
                self.progress.setWindowIcon(load_icon(ICON_PATH, "progress dialog"))
            except Exception as e:
                logger.warning(f"Failed to load progress dialog icon: {e}")
            self.progress.show()
            QApplication.processEvents()
            logger.debug(f"Progress dialog shown: {message}")
            app_signals.append_log.emit(f"[Login] Showing progress: {message}")
            self.status_bar.showMessage(message)
        except Exception as e:
            logger.error(f"Progress dialog error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Progress dialog error - {str(e)}")
            self.status_bar.showMessage(f"Progress error: {str(e)}")

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
            logger.info("Login process started")
            app_signals.append_log.emit("[Login] Login process started")
            self.status_bar.showMessage("Login process started")
        except Exception as e:
            logger.error(f"Error in handle_login: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Handle login error - {str(e)}")
            self.status_bar.showMessage(f"Login error: {str(e)}")
            if self.progress:
                self.progress.close()

    def perform_login(self, username, password):
        try:
            logger.debug("Starting login thread")
            self.thread = QThread()
            self.worker = LoginWorker(username, password, self.ui.rememberme.isChecked(), tray_icon=self.tray_icon, status_bar=self.status_bar)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.success.connect(self.on_login_success)
            self.worker.failure.connect(self.on_login_failure)
            self.worker.success.connect(self.thread.quit)
            self.worker.failure.connect(self.thread.quit)
            self.worker.success.connect(self.worker.deleteLater)
            self.worker.failure.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
            app_signals.append_log.emit(f"[Login] Starting login thread for user: {username}")
            self.status_bar.showMessage(f"Starting login for {username}")
        except Exception as e:
            logger.error(f"Login thread error: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Login thread error - {str(e)}")
            self.status_bar.showMessage(f"Login thread error: {str(e)}")
            if self.progress:
                self.progress.close()

    def on_login_success(self, user_info):
        try:
            if self.progress:
                self.progress.close()
            if self.tray_icon:
                self.tray_icon.show()
            logger.debug(f"Login success: {user_info}")
            QMessageBox.information(self, "Login Success", f"Welcome: {user_info.get('uid', 'Unknown')}")
            app_signals.append_log.emit(f"[Login] Login successful for user: {user_info.get('uid', 'Unknown')}")
            self.status_bar.showMessage(f"Login successful for user: {user_info.get('uid', 'Unknown')}")
            if self.on_success_callback:
                self.on_success_callback()
            self.accept()
        except Exception as e:
            logger.error(f"Error in on_login_success: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Login success handling error - {str(e)}")
            self.status_bar.showMessage(f"Login success error: {str(e)}")

    def on_login_failure(self, error_msg):
        try:
            if self.progress:
                self.progress.close()
            logger.debug(f"Login failure: {error_msg}")
            QMessageBox.critical(self, "Login Failed", error_msg)
            app_signals.append_log.emit(f"[Login] Failed: Login error - {error_msg}")
            self.status_bar.showMessage(f"Login failed: {error_msg}")
        except Exception as e:
            logger.error(f"Error in on_login_failure: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Login failure handling error - {str(e)}")
            self.status_bar.showMessage(f"Login failure error: {str(e)}")

    def closeEvent(self, event):
        try:
            app_signals.update_status.disconnect(self.status_bar.showMessage)
        except Exception:
            pass
        super().closeEvent(event)

class PremediaApp:
    def __init__(self, key="e0d6aa4baffc84333faa65356d78e439"):
        try:
            self.app = QApplication.instance() or QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
            self.app.setWindowIcon(load_icon(ICON_PATH, "application"))
            self.tray_icon = QSystemTrayIcon(load_icon(ICON_PATH, "system tray")) if QSystemTrayIcon.isSystemTrayAvailable() else None
            if self.tray_icon:
                self.tray_icon.setToolTip("PremediaApp")
                self.tray_icon.show()
                logger.info(f"System tray icon initialized, available: {QSystemTrayIcon.isSystemTrayAvailable()}")
                app_signals.append_log.emit(f"[Init] System tray icon initialized, available: {QSystemTrayIcon.isSystemTrayAvailable()}")

            self.logged_in = False
            load_cache()  # Initialize GLOBAL_CACHE

            # Set up tray menu
            tray_menu = QMenu()
            self.login_action = QAction("Login")
            self.logout_action = QAction("Logout")
            self.quit_action = QAction("Quit")
            self.log_action = QAction("View Log Window")
            self.downloaded_files_action = QAction("Downloaded Files")
            self.uploaded_files_action = QAction("Uploaded Files")
            self.clear_cache_action = QAction("Clear Cache")
            self.open_cache_action = QAction("Open Cache File")
            tray_menu.addAction(self.log_action)
            tray_menu.addAction(self.downloaded_files_action)
            tray_menu.addAction(self.uploaded_files_action)
            tray_menu.addAction(self.open_cache_action)
            tray_menu.addAction(self.login_action)
            tray_menu.addAction(self.clear_cache_action)
            tray_menu.addAction(self.quit_action)
            if self.tray_icon:
                self.tray_icon.setContextMenu(tray_menu)

            self.login_action.triggered.connect(self.show_login)
            self.logout_action.triggered.connect(self.logout)
            self.quit_action.triggered.connect(self.quit)
            self.log_action.triggered.connect(self.show_logs)
            self.downloaded_files_action.triggered.connect(self.show_downloaded_files)
            self.uploaded_files_action.triggered.connect(self.show_uploaded_files)
            self.clear_cache_action.triggered.connect(self.clear_cache)
            self.open_cache_action.triggered.connect(self.open_cache_file)

            self.log_window = LogWindow()
            self.downloaded_files_window = None
            self.uploaded_files_window = None
            try:
                self.login_dialog = LoginDialog(self.tray_icon, self.post_login_processes)
            except Exception as e:
                logger.error(f"Failed to initialize LoginDialog: {e}")
                app_signals.append_log.emit(f"[Init] Failed to initialize LoginDialog: {str(e)}")
                self.login_dialog = None
                QMessageBox.critical(None, "Initialization Error", f"Failed to initialize login dialog: {str(e)}")
                return

            try:
                app_signals.update_status.disconnect(self.log_window.status_bar.showMessage)
            except Exception:
                pass

            app_signals.update_status.connect(self.log_window.status_bar.showMessage, Qt.QueuedConnection)
            setup_logger(self.log_window)

            if not log_thread.is_alive():
                log_thread.start()

            logger.debug(f"Initializing with key: {key[:8]}...")
            app_signals.append_log.emit(f"[Init] Initializing with key: {key[:8]}...")
            # Inside PremediaApp.__init__
            # Inside PremediaApp.__init__
            load_cache()  # Initialize GLOBAL_CACHE
            cache = load_cache()
            logger.debug(f"Cache contents: {json.dumps(cache, indent=2)}")
            app_signals.append_log.emit(f"[Init] Cache contents: {json.dumps(cache, indent=2)}")

            # Auto-login logic
            if cache.get("token") and cache.get("user") and cache.get("user_id") and not self.logged_in:
                logger.debug("Attempting auto-login with cached credentials")
                app_signals.append_log.emit("[Init] Attempting auto-login with cached credentials")
                validation_result = validate_user(key, self.log_window.status_bar)
                if validation_result.get("uuid"):  # Check for uuid to indicate successful validation
                    try:
                        info_resp = HTTP_SESSION.get(
                            f"{BASE_DOMAIN}/api/user/getinfo?emailid={cache.get('user')}",
                            headers={"Authorization": f"Bearer {cache.get('token')}"},
                            verify=False,  # Replace with verify="/path/to/server-ca.pem" in production
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
                            "downloaded_files_with_metadata": cache.get("downloaded_files_with_metadata", []),
                            "uploaded_files": cache.get("uploaded_files", []),
                            "timer_responses": cache.get("timer_responses", {}),
                            "saved_username": cache.get("saved_username", ""),
                            "saved_password": cache.get("saved_password", ""),
                            "cached_at": datetime.now(ZoneInfo("UTC")).isoformat()
                        }
                        save_cache(cache_data)
                        self.set_logged_in_state()
                        self.tray_icon.setIcon(load_icon(ICON_PATH, "logged in"))  # Update tray icon
                        self.log_window.status_bar.showMessage(f"Auto-login successful for {cache.get('user')}")
                        self.post_login_processes()
                        self.show_logs()  # Show log window after auto-login
                        app_signals.append_log.emit("[Init] Auto-login successful with cached credentials")
                    except Exception as e:
                        logger.error(f"Auto-login failed during user info fetch: {e}")
                        app_signals.append_log.emit(f"[Init] Auto-login failed during user info fetch: {str(e)}")
                        self.set_logged_out_state()
                        self.login_dialog.show()
                else:
                    logger.warning(f"Auto-login failed: {validation_result.get('message', 'Unknown error')}")
                    app_signals.append_log.emit(f"[Init] Auto-login failed: {validation_result.get('message', 'Unknown error')}")
                    self.set_logged_out_state()
                    self.login_dialog.show()
            elif cache.get("saved_username") and cache.get("saved_password"):
                logger.debug("Attempting auto-login with saved credentials")
                app_signals.append_log.emit("[Init] Attempting auto-login with saved credentials")
                self.login_dialog.perform_login(cache["saved_username"], cache["saved_password"])
            else:
                logger.debug("No valid cached credentials, showing login dialog")
                app_signals.append_log.emit("[Init] No valid cached credentials, showing login dialog")
                self.set_logged_out_state()
                self.login_dialog.show()

        #############################################################
            logger.info("PremediaApp initialized")
            app_signals.append_log.emit("[Init] PremediaApp initialized")
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            app_signals.append_log.emit(f"[Init] Failed: Initialization error - {str(e)}")
            if self.login_dialog:
                app_signals.update_status.emit(f"Initialization error: {str(e)}")
                self.login_dialog.show()
            else:
                QMessageBox.critical(None, "Initialization Error", f"Failed to initialize application: {str(e)}")
            self.set_logged_out_state()

    def open_cache_file(self):
        try:
            cache_file = Path(CACHE_FILE)
            if not cache_file.exists():
                logger.warning("Cache file does not exist")
                app_signals.append_log.emit("[Cache] Cache file does not exist")
                QMessageBox.warning(None, "Cache Error", "Cache file does not exist.")
                return

            # Read the cache file content
            with cache_file.open('r', encoding='utf-8') as f:
                content = f.read()

            # Create a dialog to display the file content
            dialog = QDialog()
            dialog.setWindowTitle("Cache File Content")
            dialog.setMinimumSize(600, 400)  # Set a reasonable size for the dialog

            # Create a QTextEdit to display the content
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)  # Make it read-only to prevent editing
            text_edit.setPlainText(content)  # Set the file content

            # Set up the layout
            layout = QVBoxLayout()
            layout.addWidget(text_edit)
            dialog.setLayout(layout)

            # Show the dialog
            dialog.exec_()

            app_signals.update_status.emit("Opened cache file")
            app_signals.append_log.emit(f"[Cache] Opened cache file: {cache_file}")

        except Exception as e:
            logger.error(f"Error opening cache file: {e}")
            app_signals.append_log.emit(f"[Cache] Failed: Error opening cache file - {str(e)}")
            QMessageBox.critical(None, "Cache Error", f"Failed to open cache file: {str(e)}")

    def clear_cache(self):
        global GLOBAL_CACHE
        try:
            initialize_cache()
            GLOBAL_CACHE = None
            app_signals.append_log.emit("[Cache] Cache cleared manually")
            logger.info("Cache cleared manually")
            self.login_dialog.show()
            self.set_logged_out_state()
            app_signals.append_log.emit("[Cache] Showing login dialog after cache clear")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            app_signals.append_log.emit(f"[Cache] Failed: Error clearing cache - {str(e)}")

    def set_logged_in_state(self):
        try:
            self.logged_in = True
            if self.tray_icon:
                self.tray_icon.contextMenu().removeAction(self.login_action)
                self.tray_icon.contextMenu().insertAction(self.quit_action, self.logout_action)
            logger.info("Set logged in state")
            app_signals.append_log.emit("[State] Set to logged-in state")
        except Exception as e:
            logger.error(f"Error in set_logged_in_state: {e}")
            app_signals.append_log.emit(f"[State] Failed: Error setting logged-in state - {str(e)}")

    def set_logged_out_state(self):
        try:
            self.logged_in = False
            if self.tray_icon:
                self.tray_icon.contextMenu().removeAction(self.logout_action)
                self.tray_icon.contextMenu().insertAction(self.quit_action, self.login_action)
            logger.info("Set logged out state")
            app_signals.append_log.emit("[State] Set to logged-out state")
        except Exception as e:
            logger.error(f"Error in set_logged_out_state: {e}")
            app_signals.append_log.emit(f"[State] Failed: Error setting logged-out state - {str(e)}")

    def show_login(self):
        try:
            if not self.logged_in:
                self.login_dialog.show()
                app_signals.update_status.emit("Login dialog opened")
                app_signals.append_log.emit("[Login] Login dialog opened")
            else:
                app_signals.update_status.emit("Already logged in")
                app_signals.append_log.emit("[Login] Already logged in")
        except Exception as e:
            logger.error(f"Error in show_login: {e}")
            app_signals.update_status.emit(f"Error opening login dialog: {str(e)}")
            app_signals.append_log.emit(f"[Login] Failed: Error opening login dialog - {str(e)}")

    def logout(self):
        global GLOBAL_CACHE, FILE_WATCHER_RUNNING
        try:
            if hasattr(self, 'poll_timer') and self.poll_timer.isActive():
                self.poll_timer.stop()
                FILE_WATCHER_RUNNING = False
            if hasattr(self, 'file_watcher_thread') and self.file_watcher_thread.isRunning():
                self.file_watcher_thread.quit()
                self.file_watcher_thread.wait()
            initialize_cache()
            GLOBAL_CACHE = None
            self.set_logged_out_state()
            self.login_dialog.show()
            QMessageBox.information(None, "Logged Out", "You have been logged out.")
            app_signals.update_status.emit("Logged out")
            app_signals.append_log.emit("[Login] Logged out successfully")
        except Exception as e:
            logger.error(f"Error in logout: {e}")
            app_signals.update_status.emit(f"Logout error: {str(e)}")
            app_signals.append_log.emit(f"[Login] Failed: Logout error - {str(e)}")

    def quit(self):
        global HTTP_SESSION, FILE_WATCHER_RUNNING
        try:
            if hasattr(self, 'poll_timer') and self.poll_timer.isActive():
                self.poll_timer.stop()
                FILE_WATCHER_RUNNING = False
            if hasattr(self, 'file_watcher_thread') and self.file_watcher_thread.isRunning():
                self.file_watcher_thread.quit()
                self.file_watcher_thread.wait(2000)  # Wait up to 2 seconds
            if self.tray_icon:
                self.tray_icon.hide()
            HTTP_SESSION.close()
            stop_logging()
            app_signals.update_status.emit("Application quitting")
            app_signals.append_log.emit("[App] Application quitting")
            logger.info("Application quitting")
            self.app.quit()
        except Exception as e:
            logger.error(f"Error in quit: {e}")
            app_signals.update_status.emit(f"Quit error: {str(e)}")
            app_signals.append_log.emit(f"[App] Failed: Quit error - {str(e)}")
            stop_logging()
            self.app.quit()

    def show_logs(self):
        try:
            self.log_window.load_logs()
            self.log_window.show()
            app_signals.update_status.emit("Log window opened")
            app_signals.append_log.emit("[Log] Log window opened")
        except Exception as e:
            logger.error(f"Error in show_logs: {e}")
            app_signals.update_status.emit(f"Error opening log window: {str(e)}")
            app_signals.append_log.emit(f"[Log] Failed: Error opening log window - {str(e)}")

    def show_downloaded_files(self):
        try:
            if not self.downloaded_files_window or not self.downloaded_files_window.isVisible():
                self.downloaded_files_window = FileListWindow("downloaded")
                self.downloaded_files_window.show()
                app_signals.update_status.emit("Downloaded files window opened")
                app_signals.append_log.emit("[Files] Downloaded files window opened")
        except Exception as e:
            logger.error(f"Error in show_downloaded_files: {e}")
            app_signals.update_status.emit(f"Error showing downloaded files: {str(e)}")
            app_signals.append_log.emit(f"[Files] Failed: Error showing downloaded files - {str(e)}")

    def show_uploaded_files(self):
        try:
            if not self.uploaded_files_window or not self.uploaded_files_window.isVisible():
                self.uploaded_files_window = FileListWindow("uploaded")
                self.uploaded_files_window.show()
                app_signals.update_status.emit("Uploaded files window opened")
                app_signals.append_log.emit("[Files] Uploaded files window opened")
        except Exception as e:
            logger.error(f"Error in show_uploaded_files: {e}")
            app_signals.update_status.emit(f"Error showing uploaded files: {str(e)}")
            app_signals.append_log.emit(f"[Files] Failed: Error showing uploaded files - {str(e)}")

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
            app_signals.update_status.emit(f"File conversion thread error: {str(e)}")
            app_signals.append_log.emit(f"[Conversion] Failed: File conversion thread error - {str(e)}")

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
            app_signals.update_status.emit(f"Conversion error: {str(e)}")
            app_signals.append_log.emit(f"[Conversion] Failed: Conversion error - {str(e)}")

    def on_conversion_error(self, error, basename):
        try:
            app_signals.update_status.emit(f"Conversion failed for {basename}: {error}")
            app_signals.update_file_list.emit("", f"Conversion Failed: {error}", "download", 0, False)
            app_signals.append_log.emit(f"[Conversion] Failed: Conversion error for {basename} - {error}")
        except Exception as e:
            logger.error(f"Error in on_conversion_error: {e}")
            app_signals.append_log.emit(f"[Conversion] Failed: Error handling conversion error - {str(e)}")

    def open_with_photoshop(self, file_path):
        """Dynamically find Adobe Photoshop path and open the specified file."""
        try:
            system = platform.system()
            photoshop_path = None

            if system == "Windows":
                # Search Program Files and Program Files (x86) for Photoshop
                search_dirs = [
                    Path("C:/Program Files/Adobe"),
                    Path("C:/Program Files (x86)/Adobe")
                ]
                for base_dir in search_dirs:
                    if not base_dir.exists():
                        continue
                    # Find all Photoshop executables, sort by version (descending)
                    photoshop_exes = list(base_dir.glob("Adobe Photoshop */Photoshop.exe"))
                    if photoshop_exes:
                        # Pick the latest version based on directory name (e.g., "Adobe Photoshop 2023")
                        photoshop_exes.sort(key=lambda x: x.parent.name, reverse=True)
                        photoshop_path = str(photoshop_exes[0])
                        break
                if not photoshop_path:
                    raise FileNotFoundError("Adobe Photoshop executable not found in Program Files")

            elif system == "Darwin":
                # Use mdfind to locate Photoshop or check common paths
                try:
                    result = subprocess.run(
                        ["mdfind", "kMDItemKind == 'Application' && kMDItemFSName == 'Adobe Photoshop.app'"],
                        capture_output=True, text=True, check=True
                    )
                    if result.stdout.strip():
                        photoshop_path = result.stdout.strip().split("\n")[0]
                except subprocess.CalledProcessError:
                    # Fallback to common paths
                    photoshop_apps = list(Path("/Applications").glob("Adobe Photoshop*.app"))
                    if photoshop_apps:
                        photoshop_apps.sort(key=lambda x: x.name, reverse=True)
                        photoshop_path = str(photoshop_apps[0])
                if not photoshop_path:
                    raise FileNotFoundError("Adobe Photoshop application not found in /Applications")

            elif system == "Linux":
                # Check for wine and Photoshop in common Wine directories
                try:
                    subprocess.run(["wine", "--version"], capture_output=True, check=True)
                    # Check common Wine program files
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
                logger.warning(f"Unsupported platform for Photoshop: {system}")
                app_signals.append_log.emit(f"[Photoshop] Unsupported platform: {system}")
                app_signals.update_status.emit(f"Unsupported platform: {system}")
                return

            # Open the file with Photoshop
            if system == "Darwin":
                subprocess.run(["open", "-a", photoshop_path, file_path], check=True)
            else:
                subprocess.run([photoshop_path, file_path], check=True)

            logger.info(f"Opened {Path(file_path).name} in Photoshop at {photoshop_path}")
            app_signals.append_log.emit(f"[Photoshop] Opened {Path(file_path).name} at {photoshop_path}")
            app_signals.update_status.emit(f"Opened {Path(file_path).name} in Photoshop")

        except Exception as e:
            logger.error(f"Failed to open {file_path} in Photoshop: {e}")
            app_signals.append_log.emit(f"[Photoshop] Failed: Error opening {Path(file_path).name} - {str(e)}")
            app_signals.update_status.emit(f"Failed to open {Path(file_path).name} in Photoshop: {str(e)}")

    def post_login_processes(self):
        global FILE_WATCHER_RUNNING
        try:
            cache = load_cache()
            token = cache.get("token", "")
            user_id = cache.get("user_id", "")
            if not token or not user_id:
                logger.error("No token or user_id for post-login processes")
                app_signals.append_log.emit("[Login] Failed: No token or user_id for post-login processes")
                self.set_logged_out_state()
                self.login_dialog.show()
                return

            if hasattr(self, 'poll_timer') and self.poll_timer.isActive():
                logger.debug("Poll timer already active, skipping initialization")
                app_signals.append_log.emit("[Login] Poll timer already active, skipping initialization")
                return

            FILE_WATCHER_RUNNING = True
            self.file_watcher_thread = QThread()
            self.file_watcher = FileWatcherWorker()  # Initialize without parent
            self.file_watcher.moveToThread(self.file_watcher_thread)
            self.file_watcher_thread.started.connect(self.file_watcher.run)
            self.file_watcher.status_update.connect(self.log_window.status_bar.showMessage)
            self.file_watcher.log_update.connect(app_signals.append_log.emit)
            self.poll_timer = QTimer()
            self.poll_timer.timeout.connect(self.file_watcher.run)
            self.poll_timer.start(API_POLL_INTERVAL)

            self.file_watcher_thread.start()
            app_signals.append_log.emit("[Login] Post-login processes started")
            app_signals.update_status.emit("File watcher started")
        except Exception as e:
            logger.error(f"Error in post_login_processes: {e}")
            app_signals.append_log.emit(f"[Login] Failed: Post-login processes error - {str(e)}")
            app_signals.update_status.emit(f"Post-login error: {str(e)}")

if __name__ == "__main__":
    key = parse_custom_url()
    app = PremediaApp(key)
    sys.exit(app.app.exec())