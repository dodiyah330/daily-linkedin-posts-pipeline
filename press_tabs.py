import subprocess
import time

for i in range(1, 15):
    print(f"Pressing Tab {i}...")
    subprocess.run(["agent-browser", "--session-name", "linkedin_bot", "press", "Tab"], check=True)
    time.sleep(0.5)

subprocess.run(["agent-browser", "--session-name", "linkedin_bot", "screenshot", "after_tabs.png"], check=True)
