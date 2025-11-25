import json, time, requests
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
RUNTIME_DIR = APP_DIR / "runtime"
UPDATE_URL = "https://yourserver.com/runtime/"   # CHANGE THIS

def runtime_update_loop():
    """Background update loop to auto-update runtime modules."""
    while True:
        try:
            local = json.loads((RUNTIME_DIR / "version.json").read_text())
            server = requests.get(UPDATE_URL + "version.json").json()

            if local["version"] != server["version"]:
                print("[UPDATE] New runtime version found!")

                # Download every module
                for f in server["files"]:
                    content = requests.get(UPDATE_URL + f).text
                    (RUNTIME_DIR / f).write_text(content)

                # Update version file
                (RUNTIME_DIR / "version.json").write_text(
                    json.dumps(server, indent=2)
                )

                print("[UPDATE] Runtime updated successfully!")

        except Exception as e:
            print("[UPDATE ERROR]", e)

        time.sleep(300)   # every 5 minutes
