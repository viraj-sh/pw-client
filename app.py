import subprocess
import sys
import time
import socket
import requests
import os
import argparse
from app.core.utils import RESET, BOLD, FG_RED, FG_WHITE, FG_GREEN, FG_YELLOW

app_dir = os.path.join(os.path.dirname(__file__), "app")
sys.path.insert(0, app_dir)


def parse_args():
    parser = argparse.ArgumentParser(description="Launch FastAPI server")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logs for uvicorn",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Optional port to run the server on (overrides auto-selection)",
    )
    return parser.parse_args()


def find_free_port(start=8000, end=8100):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available")


def wait_for_server(port, timeout=10):
    url = f"http://127.0.0.1:{port}/docs"
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.head(url, timeout=0.5)
            if r.status_code >= 200:
                return True
        except requests.RequestException:
            try:
                r = requests.get(url, timeout=0.5)
                if r.status_code in (200, 404):
                    return True
            except requests.RequestException:
                time.sleep(0.1)
                continue
        time.sleep(0.1)
    return False


def open_browser(url):
    try:
        import webbrowser

        webbrowser.open(url, new=2)
    except Exception:
        pass


if __name__ == "__main__":
    args = parse_args()
    env_port = os.environ.get("PORT")
    port = args.port or (
        int(env_port) if env_port and env_port.isdigit() else find_free_port()
    )

    if args.debug:
        print(
            f"""{BOLD}{FG_RED}🚀 Starting application{RESET}
{FG_WHITE}• URL:{RESET} {BOLD}http://127.0.0.1:{port}{RESET}
{FG_WHITE}• Host:{RESET} 127.0.0.1
{FG_WHITE}• Port:{RESET} {BOLD}{port}{RESET}
{FG_WHITE}• Mode:{RESET} {BOLD}DEBUG{RESET}
{FG_WHITE}• Reload:{RESET} enabled
{FG_WHITE}• Log level:{RESET} info
{FG_WHITE}• Access log:{RESET} enabled"""
        )

    else:
        print(
            f"""{BOLD}{FG_RED}🚀 Starting application{RESET}
{FG_WHITE}• Mode:{RESET} {BOLD}QUIET{RESET}"""
        )

    env = os.environ.copy()
    env["PYTHONPATH"] = app_dir + os.pathsep + env.get("PYTHONPATH", "")

    if args.debug:
        stdout_setting = None
        stderr_setting = None
        log_level = "info"
        access_log_flag = []
    else:
        stdout_setting = subprocess.DEVNULL
        stderr_setting = subprocess.DEVNULL
        log_level = "critical"
        access_log_flag = ["--no-access-log"]
    uvicorn_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--reload",
            "--log-level",
            log_level,
            *access_log_flag,
        ],
        stdout=stdout_setting,
        stderr=stderr_setting,
        env=env,
        start_new_session=True,
    )

    if not args.debug and wait_for_server(port):
        url = f"http://127.0.0.1:{port}"
        print(
            f"""
{BOLD}{FG_GREEN}✅ Application is ready{RESET}
{FG_WHITE}• URL:{RESET} {BOLD}{url}{RESET}
{FG_WHITE}• Browser:{RESET} opening a new tab

{FG_YELLOW}Tip:{RESET} use --debug for full logs and manual control
{FG_YELLOW}GitHub:{RESET} https://github.com/viraj-sh/pw-client
{FG_YELLOW}Docs:{RESET}   https://github.com/viraj-sh/pw-client/wiki

{FG_RED}Note:{RESET} Keep this terminal open; closing it will stop the server."""
        )
        open_browser(url)
    elif not args.debug:
        print(
            f"""{BOLD}{FG_RED}❌ Application failed to start{RESET}
{FG_WHITE}• Port attempted:{RESET} {BOLD}{port}{RESET}
{FG_WHITE}• Mode:{RESET} {BOLD}QUIET{RESET} (logs suppressed)

{FG_YELLOW}Troubleshooting:{RESET}
• Try: python app.py --debug
• Check: port availability, app/main.py, Uvicorn errors

{FG_YELLOW}GitHub:{RESET} https://github.com/viraj-sh/pw-client
{FG_YELLOW}Docs:{RESET}   https://github.com/viraj-sh/pw-client/wiki"""
        )
        uvicorn_proc.terminate()
        sys.exit(1)

    try:
        uvicorn_proc.wait()
    except KeyboardInterrupt:
        uvicorn_proc.terminate()
        uvicorn_proc.wait()
