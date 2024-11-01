import os
import subprocess

def run_quartus(command: list, working_dir: str = None) -> str:
    """
    Run a Quartus command with proper environment setup and error handling.

    Args:
        command (list): Command and arguments as list
        working_dir (str): Working directory for the command
    """
    try:

        # Method 1: Using shell=True (Windows preferred)
        cmds = command # just for debug purposes
        command = ' '.join(command)
        result = subprocess.run(
            command,
            shell=True,
            env=os.environ.copy(), # shell or env
            #check=True,
            text=True,
            capture_output=True,
            cwd= working_dir
        )

        out = result.stdout

        is_err = False if not('errors' in out and '0 errors' not in out) else True
        is_err = is_err or 'Error: ' in out

        if len(result.stderr) > 0 or is_err:
            raise RuntimeError(result.stderr)

        print("Quartus output:", out)
        return out

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("Error output:", e.stderr)
        raise
