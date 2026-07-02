import subprocess
import time
import sys

def run_cmd(args):
    print("Running:", " ".join(args))
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print("FAILED:", res.stderr)
        sys.exit(1)
    print("SUCCESS")

# 1. Click time
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "click", "@e252"])
time.sleep(1)

# 2. Backspace 10 times
for _ in range(10):
    run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Backspace"])
    time.sleep(0.1)

# 3. Type time
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "keyboard", "type", "3:15 AM"])
time.sleep(1)

# 4. Press Enter
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Enter"])
time.sleep(1)

print("Done setting time.")
