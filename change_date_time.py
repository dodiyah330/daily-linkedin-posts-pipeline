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

# 1. Click date
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "click", "@e254"])
time.sleep(1)

# 2. Select all
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Meta+a"])
time.sleep(0.5)

# 3. Backspace
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Backspace"])
time.sleep(0.5)

# 4. Type date
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "keyboard", "type", "06/11/2026"])
time.sleep(1)

# 5. Click time
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "click", "@e251"])
time.sleep(1)

# 6. Select all
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Meta+a"])
time.sleep(0.5)

# 7. Backspace
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Backspace"])
time.sleep(0.5)

# 8. Type time
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "keyboard", "type", "3:15 AM"])
time.sleep(1)

# 9. Press Enter
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Enter"])
time.sleep(1)

print("Done setting date/time.")
