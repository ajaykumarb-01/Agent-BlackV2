import sys
import os
import subprocess
import time
import signal
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(ROOT, "logs")
PYTHON = sys.executable

os.makedirs(LOGS, exist_ok=True)

AGENTS = [
    {"name": "research-agent", "port": 8001, "dir": os.path.join("agents", "research-agent")},
    {"name": "solution-agent", "port": 8002, "dir": os.path.join("agents", "solution-agent")},
    {"name": "experiment-agent", "port": 8003, "dir": os.path.join("agents", "experiment-agent")},
    # host-agent is not started as a separate process here because the
    # control panel (port 8000) imports and cd runs the orchestrator in-process.
]

processes = []

def start_agent(name, port, dir):
    log_out = open(os.path.join(LOGS, f"{name}.log"), "w")
    log_err = open(os.path.join(LOGS, f"{name}-err.log"), "w")
    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port)],
        cwd=os.path.join(ROOT, dir),
        stdout=log_out,
        stderr=log_err,
    )
    return proc

def _stream_to_file_and_console(proc, log_out_path, log_err_path, label):
    """Read subprocess stdout/stderr, print to console with label, and write to log files."""
    out_file = open(log_out_path, "w", buffering=1)
    err_file = open(log_err_path, "w", buffering=1)

    def _reader(stream, file, prefix):
        for line in iter(stream.readline, b""):
            decoded = line.decode("utf-8", errors="replace")
            file.write(decoded)
            sys.stdout.write(f"{prefix}{decoded}")
            sys.stdout.flush()
        stream.close()
        file.close()

    t_out = threading.Thread(target=_reader, args=(proc.stdout, out_file, f"[{label}] "), daemon=True)
    t_err = threading.Thread(target=_reader, args=(proc.stderr, err_file, f"[{label}:err] "), daemon=True)
    t_out.start()
    t_err.start()
    return t_out, t_err

def start_control_panel():
    log_out_path = os.path.join(LOGS, "control-panel.log")
    log_err_path = os.path.join(LOGS, "control-panel-err.log")
    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _stream_to_file_and_console(proc, log_out_path, log_err_path, "control-panel")
    return proc

def stop_all():
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
    for proc in processes:
        proc.wait()

if __name__ == "__main__":
    print("Starting Agent Black...")
    print(f"Logs directory: {LOGS}")
    print()

    for agent in AGENTS:
        proc = start_agent(**agent)
        processes.append(proc)
        print(f"  [{proc.pid}] {agent['name']} -> http://localhost:{agent['port']}")

    # Start the control panel API server on port 8000
    cp_proc = start_control_panel()
    processes.append(cp_proc)
    print(f"  [{cp_proc.pid}] control-panel  -> http://localhost:8000")

    print()
    print("All agents started. Logs written to logs/")
    print("Press Ctrl+C to stop all agents.")

    try:
        while True:
            time.sleep(1)
            for proc in processes:
                if proc.poll() is not None:
                    print(f"WARNING: {proc.args} exited with code {proc.returncode}")
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_all()
        print("All agents stopped.")
