import os
import subprocess

# Map friendly names to actual Windows commands or exe paths
APP_COMMANDS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    # Example for Spotify—update path if yours differs:
    "spotify": r"C:\Users\You\AppData\Roaming\Spotify\Spotify.exe",
    # Add more mappings as you like
}

def open_application(app_name: str) -> str:
    """
    Try to open the given app_name.
    Returns a status message.
    """
    key = app_name.lower().strip()
    print(f"🔍 Looking for app: '{key}'")  # Debug line
    cmd = APP_COMMANDS.get(key)
    if not cmd:
        return f"❌ I don't know how to open '{app_name}'."

    try:
        print(f"🚀 Attempting to run: {cmd}")  # Debug line
        # For executables or file paths:
        if os.path.isfile(cmd) or cmd.lower().endswith(".exe"):
            os.startfile(cmd)
        else:
            # Fallback: try via subprocess (for system commands)
            subprocess.Popen(cmd, shell=True)
        return f"✅ Opening {app_name}."
    except Exception as e:
        return f"❌ Failed to open {app_name}: {e}"
