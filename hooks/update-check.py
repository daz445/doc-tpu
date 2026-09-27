#!/usr/bin/env python3
"""Auto-update hook for doc-tpu plugin.

Checks GitHub for updates once per 24 hours.
Runs on UserPromptSubmit — only acts on the first prompt of the session.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
CHECK_INTERVAL = 86400  # 24 hours in seconds
STAMP_FILE = os.path.join(PLUGIN_ROOT, ".last-update-check")


def needs_check():
    if not os.path.exists(STAMP_FILE):
        return True
    try:
        last_check = float(Path(STAMP_FILE).read_text().strip())
        return (time.time() - last_check) > CHECK_INTERVAL
    except (ValueError, OSError):
        return True


def save_stamp():
    try:
        Path(STAMP_FILE).write_text(str(time.time()))
    except OSError:
        pass


def do_update():
    if not os.path.isdir(os.path.join(PLUGIN_ROOT, ".git")):
        return None

    try:
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=PLUGIN_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        save_stamp()

        if result.returncode == 0:
            output = result.stdout.strip()
            if "Already up to date" in output:
                return None
            return output
        else:
            return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    if not needs_check():
        sys.exit(0)

    result = do_update()

    if result:
        msg = {
            "systemMessage": f"📦 doc-tpu обновлён:\n{result}\nПерезапустите сессию для применения изменений."
        }
        print(json.dumps(msg), file=sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
