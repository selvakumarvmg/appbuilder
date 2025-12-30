# updater_client.py
# import os
# import sys
# import json
# import time
# import tempfile
# import subprocess
# import hashlib
# import platform
# import requests
# import tkinter as tk
# from tkinter import messagebox

# # 🔹 Hosted version file
# VERSION_URL = "https://vmg-premedia-22112023.s3.ap-southeast-2.amazonaws.com/application/drn/latest_version.json"

# def sha256(path):
#     """Compute lowercase SHA256 checksum."""
#     h = hashlib.sha256()
#     with open(path, "rb") as f:
#         for chunk in iter(lambda: f.read(8192), b""):
#             h.update(chunk)
#     return h.hexdigest().lower()

# def ask_user_to_update(latest):
#     """Ask user if they want to update."""
#     root = tk.Tk()
#     root.withdraw()
#     res = messagebox.askyesno(
#         "Update Available",
#         f"A new version {latest} is available.\nDo you want to update now?"
#     )
#     root.destroy()
#     return res

# def check_for_update(current_version, exe_path):
#     """Check S3 JSON for update and apply if needed."""
#     try:
#         r = requests.get(f"{VERSION_URL}?t={int(time.time())}", timeout=8)
#         data = r.json()
#         latest_version = data.get("version", "").strip()
#         if not latest_version:
#             print("[Updater] ❌ Invalid version JSON.")
#             return

#         print(f"[Updater] Current: {current_version} | Latest: {latest_version}")
#         if latest_version == current_version:
#             print("[Updater] ✅ Already up to date.")
#             return

#         mandatory = bool(data.get("mandatory"))
#         if not mandatory and not ask_user_to_update(latest_version):
#             print("[Updater] Skipped by user.")
#             return

#         os_type = platform.system()

#         if os_type == "Windows":
#             platform_data = data.get("windows", {})
#         elif os_type == "Darwin":
#             platform_data = data.get("mac", {})
#         else:
#             messagebox.showerror("Update Error", f"Unsupported OS: {os_type}")
#             return

#         download_url = platform_data.get("url")
#         expected_sha = platform_data.get("sha256", "").lower()

#         if not download_url or not expected_sha:
#             messagebox.showerror(
#                 "Update Error",
#                 "Invalid update metadata for this platform."
#             )
#             return



#         # 🔹 Download new EXE
#         tmp_file = os.path.join(tempfile.gettempdir(), os.path.basename(download_url))
#         print(f"[Updater] Downloading from {download_url} ...")
#         with requests.get(download_url, stream=True, timeout=30) as resp:
#             resp.raise_for_status()
#             with open(tmp_file, "wb") as f:
#                 for chunk in resp.iter_content(chunk_size=8192):
#                     if chunk:
#                         f.write(chunk)
#         print(f"[Updater] Downloaded to: {tmp_file}")



#         # 🔹 Verify checksum
#         # expected = data.get("sha256", "").strip().lower()  ///------------->
#         expected = expected_sha
#         actual = sha256(tmp_file)
#         if expected and actual != expected:
#             messagebox.showerror("Checksum Error", "Downloaded file failed verification.")
#             os.remove(tmp_file)
#             return

#         # 🔹 Launch updater
#         if os_type == "Windows":
#             updater_path = os.path.join(os.path.dirname(exe_path), "updater.exe")
#             if not os.path.exists(updater_path):
#                 messagebox.showerror("Update Error", f"Missing updater.exe at:\n{updater_path}")
#                 return

#             print(f"[Updater] Launching updater: {updater_path}")
#             subprocess.Popen([updater_path, tmp_file, exe_path], shell=False)

#             # wait a little before exit so file lock clears
#             time.sleep(2)
#             sys.exit(0)

#         elif os_type == "Darwin":
#             updater_path = os.path.join(os.path.dirname(exe_path), "updater.sh")

#             if not os.path.exists(updater_path):
#                 messagebox.showerror("Update Error", "Missing updater.sh")
#                 return

#             subprocess.Popen(["bash", updater_path, tmp_file])
#             sys.exit(0)


#     except Exception as e:
#         print(f"[Updater] ❌ Update failed: {e}")


# updater_client.py
import os
import sys
import time
import tempfile
import subprocess
import hashlib
import platform
import requests
import tkinter as tk
from tkinter import messagebox

# 🔹 Hosted version file
VERSION_URL = "https://vmg-premedia-22112023.s3.ap-southeast-2.amazonaws.com/application/drn/latest_version.json"


# =========================
# Utility helpers
# =========================

def sha256(path):
    """Compute lowercase SHA256 checksum."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def show_error(title, msg):
    """Safe Tk error dialog (macOS friendly)."""
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, msg)
    root.destroy()


def ask_user_to_update(latest):
    """Ask user if they want to update."""
    root = tk.Tk()
    root.withdraw()
    res = messagebox.askyesno(
        "Update Available",
        f"A new version {latest} is available.\nDo you want to update now?"
    )
    root.destroy()
    return res


# =========================
# Main update logic
# =========================

def check_for_update(current_version, exe_path):
    """Check S3 JSON for update and apply if needed."""
    try:
        # 🔹 Force no-cache (IMPORTANT for macOS)
        r = requests.get(
            f"{VERSION_URL}?t={int(time.time())}",
            timeout=8,
            headers={
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
        )
        r.raise_for_status()

        try:
            data = r.json()
        except Exception as e:
            show_error("Update Error", f"Invalid update metadata:\n{e}")
            return

        latest_version = str(data.get("version", "")).strip()
        if not latest_version:
            show_error("Update Error", "Version information missing from server.")
            return

        print(f"[Updater] Current: {current_version} | Latest: {latest_version}")

        if latest_version == current_version:
            print("[Updater] ✅ Already up to date.")
            return

        mandatory = bool(data.get("mandatory"))
        if not mandatory and not ask_user_to_update(latest_version):
            print("[Updater] Skipped by user.")
            return

        # 🔹 Platform detection
        os_type = platform.system()

        if os_type == "Windows":
            platform_data = data.get("windows", {})
        elif os_type == "Darwin":
            platform_data = data.get("mac", {})
        else:
            show_error("Update Error", f"Unsupported OS: {os_type}")
            return

        download_url = platform_data.get("url", "").strip()
        expected_sha = platform_data.get("sha256", "").strip().lower()

        if not download_url or not expected_sha:
            show_error(
                "Update Error",
                "Invalid update metadata for this platform.\n"
                "Please contact support."
            )
            return

        print("[Updater] Download URL:", download_url)

        # 🔹 Download update to unique temp file
        tmp_file = tempfile.NamedTemporaryFile(delete=False).name
        print(f"[Updater] Downloading update...")

        with requests.get(download_url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with open(tmp_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        print(f"[Updater] Downloaded to: {tmp_file}")

        # 🔹 Verify checksum
        actual_sha = sha256(tmp_file)
        print(f"[Updater] Expected SHA: {expected_sha}")
        print(f"[Updater] Actual SHA:   {actual_sha}")

        if actual_sha != expected_sha:
            os.remove(tmp_file)
            show_error("Checksum Error", "Downloaded file failed verification.")
            return

        # 🔹 Ensure executable permission on macOS
        if os_type == "Darwin":
            os.chmod(tmp_file, 0o755)

        # 🔹 Launch updater
        if os_type == "Windows":
            updater_path = os.path.join(os.path.dirname(exe_path), "updater.exe")
            if not os.path.exists(updater_path):
                show_error("Update Error", f"Missing updater.exe at:\n{updater_path}")
                return

            print(f"[Updater] Launching updater.exe")
            subprocess.Popen(
                [updater_path, tmp_file, exe_path],
                close_fds=True,
                shell=False
            )

            time.sleep(2)
            sys.exit(0)

        elif os_type == "Darwin":
            updater_path = os.path.join(os.path.dirname(exe_path), "updater.sh")
            if not os.path.exists(updater_path):
                show_error("Update Error", "Missing updater.sh")
                return

            print(f"[Updater] Launching updater.sh")
            subprocess.Popen(["bash", updater_path, tmp_file, exe_path])
            sys.exit(0)

    except Exception as e:
        show_error("Update Failed", str(e))
