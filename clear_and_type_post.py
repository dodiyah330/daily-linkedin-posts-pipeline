import subprocess
import time
import sys

text = """Five AI updates you should know about this week

Five updates in the world of artificial intelligence that happened this week. Curation is a service so here is the summary of what matters.

1. Anthropic filed for a confidential initial public offering. The creator of the Claude models is preparing to go public, signaling a massive consolidation phase in the consumer AI sector.

2. IBM partnered with Google Cloud to scale enterprise agent platforms. Large companies will now be able to deploy automated systems across both clouds, making multi-platform integration faster.

3. S&P Global launched Credit Memo Builder. The agentic system helps financial analysts generate complex credit research memos in minutes instead of days.

4. NVIDIA announced RTX Spark PC chips. These new computer processors will handle large voice and video tasks locally on your device without sending data to external servers.

5. DARPA and the NSF started the AI Forge program. The initiative provides funding and computing resources to help small software companies build secure systems.

The trend this week is clear: AI is moving from a chatbot helper to automated systems running on local devices and corporate platforms.

Which of these updates will have the biggest impact on your team's workflow this quarter?

Follow @founderswing for daily data drops"""

def run_cmd(args):
    print("Running:", " ".join(args))
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print("FAILED:", res.stderr)
        sys.exit(1)
    print("SUCCESS")

# 1. Click text box
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "click", "@e250"])
time.sleep(1)

# 2. Select all using Meta+a
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Meta+a"])
time.sleep(0.5)

# 3. Select all using Control+a (just in case)
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Control+a"])
time.sleep(0.5)

# 4. Backspace
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "press", "Backspace"])
time.sleep(1)

# 5. Type text
run_cmd(["agent-browser", "--session-name", "linkedin_bot", "type", "@e250", text])
time.sleep(2)

print("Done clearing and typing.")
