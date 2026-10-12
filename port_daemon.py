#!/usr/bin/env python3
"""
Dynamic Port Forwarding Daemon for Docker on Haiku OS.
Utilizes SSH multiplexing (ControlMaster) to avoid connection churn.
Listens to continuous 'docker events' stream for instant port reaction.
Performs periodic reconciliation (every 60s) to keep state consistent.
Dynamically adds/removes forwards via OpenSSH control commands:
  ssh -O forward -L 127.0.0.1:<port>:127.0.0.1:<port> -S <sock> root@127.0.0.1
  ssh -O cancel  -L 127.0.0.1:<port>:127.0.0.1:<port> -S <sock> root@127.0.0.1
"""
import subprocess
import time
import os
import sys
import select

CONFIG_DIR = "/boot/home/config/settings/docker-vm"
KEY = os.path.join(CONFIG_DIR, "id_docker_vm")
SOCK = os.path.join(CONFIG_DIR, "docker-vm.sock")
PID_FILE = os.path.join(CONFIG_DIR, "port_daemon.pid")
PORT = 2265

active_ports = set()

def write_pid():
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"[Port Daemon] Warning writing pid: {e}", flush=True)

def is_master_alive():
    if not os.path.exists(SOCK):
        return False
    res = subprocess.run(
        ["ssh", "-O", "check", "-S", SOCK, "root@127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return (res.returncode == 0)

def ensure_master():
    if is_master_alive():
        return True
    if not os.path.exists(KEY):
        return False

    try:
        if os.path.exists(SOCK):
            os.remove(SOCK)
    except OSError:
        pass

    print("[Port Daemon] Starting SSH ControlMaster...", flush=True)
    subprocess.run(
        [
            "ssh", "-N", "-f", "-M",
            "-S", SOCK,
            "-i", KEY,
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ControlPersist=yes",
            "-o", "ServerAliveInterval=15",
            "-o", "ServerAliveCountMax=3",
            "-p", str(PORT),
            "root@127.0.0.1"
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    for _ in range(10):
        time.sleep(0.5)
        if is_master_alive():
            return True
    return False

def run_ssh_cmd(cmd_str, timeout=10):
    if not ensure_master():
        return None
    try:
        res = subprocess.run(
            ["ssh", "-S", SOCK, "root@127.0.0.1", cmd_str],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=timeout
        )
        if res.returncode == 0:
            return res.stdout
    except Exception as e:
        print(f"[Port Daemon] Command error ({cmd_str}): {e}", flush=True)
    return None

def query_mapped_ports():
    out = run_ssh_cmd("docker ps --format '{{.Ports}}'", timeout=10)
    if out is None:
        return None

    ports = set()
    for line in out.strip().splitlines():
        for part in line.split(","):
            part = part.strip()
            if "->" in part:
                left = part.split("->")[0]
                if ":" in left:
                    host_port_str = left.split(":")[-1]
                    try:
                        p = int(host_port_str)
                        if 1 <= p <= 65535:
                            ports.add(p)
                    except ValueError:
                        pass
    return ports

def add_forward(port):
    if not ensure_master():
        return False
    print(f"[Port Daemon] Opening tunnel for host port {port} -> guest {port} via ControlMaster...", flush=True)
    res = subprocess.run(
        ["ssh", "-O", "forward", "-L", f"127.0.0.1:{port}:127.0.0.1:{port}", "-S", SOCK, "root@127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return (res.returncode == 0)

def cancel_forward(port):
    if not is_master_alive():
        return
    print(f"[Port Daemon] Closing tunnel for host port {port} via ControlMaster...", flush=True)
    subprocess.run(
        ["ssh", "-O", "cancel", "-L", f"127.0.0.1:{port}:127.0.0.1:{port}", "-S", SOCK, "root@127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def sync_ports():
    global active_ports
    target = query_mapped_ports()
    if target is None:
        return

    # Cancel ports no longer present
    for p in list(active_ports - target):
        cancel_forward(p)
        active_ports.discard(p)

    # Add newly mapped ports
    for p in list(target - active_ports):
        if add_forward(p):
            active_ports.add(p)

def start_events_stream():
    if not ensure_master():
        return None
    try:
        proc = subprocess.Popen(
            [
                "ssh", "-S", SOCK, "root@127.0.0.1",
                "docker events --filter type=container --format '{{.Action}}'"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        return proc
    except Exception as e:
        print(f"[Port Daemon] Failed to start events stream: {e}", flush=True)
        return None

def main():
    write_pid()
    print("[Port Daemon] Dynamic Docker port forwarder running (ControlMaster + events stream)...", flush=True)

    # Allow guest environment and Master to fully settle
    for _ in range(10):
        if is_master_alive():
            break
        time.sleep(0.5)

    ensure_master()
    sync_ports()

    events_proc = start_events_stream()
    last_reconcile = time.time()
    RECONCILE_INTERVAL = 60.0

    while True:
        try:
            now = time.time()

            # 1. Periodic reconciliation (every 60s)
            if now - last_reconcile >= RECONCILE_INTERVAL:
                sync_ports()
                last_reconcile = now

            # 2. Check if events stream process is healthy
            if events_proc is None or events_proc.poll() is not None:
                if events_proc and events_proc.poll() is not None:
                    print(f"[Port Daemon] Events stream exited ({events_proc.poll()}). Re-establishing...", flush=True)
                ensure_master()
                sync_ports()
                events_proc = start_events_stream()
                time.sleep(1)
                continue

            # 3. Read events with 1s timeout
            r, _, _ = select.select([events_proc.stdout], [], [], 1.0)
            if r:
                line = events_proc.stdout.readline()
                if not line:
                    # Stream closed EOF
                    print("[Port Daemon] Events stream EOF received.", flush=True)
                    events_proc.terminate()
                    events_proc = None
                    continue
                action = line.strip().lower()
                # If container lifecycle changes ports, synchronize
                if any(k in action for k in ("start", "stop", "die", "destroy", "kill", "pause", "unpause", "restart")):
                    print(f"[Port Daemon] Container event detected: {action}. Syncing ports...", flush=True)
                    sync_ports()

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Port Daemon] Unexpected error: {e}", flush=True)
            time.sleep(2)

    # Cleanup forwards on exit
    for p in list(active_ports):
        cancel_forward(p)
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

if __name__ == "__main__":
    main()
