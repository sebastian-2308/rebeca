import subprocess
import sys


def bash(command: str, description: str = "", timeout: int = 120_000) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout / 1000,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr
        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "(command timed out)"
    except Exception as e:
        return f"(error: {e})"
