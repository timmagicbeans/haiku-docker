#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import select

WATCH_DIR = "/boot/home/dev"
CONFIG_DIR = "/boot/home/config/settings/docker-vm"
SOCK = os.path.join(CONFIG_DIR, "docker-vm.sock")
KEY = os.path.join(CONFIG_DIR, "id_docker_vm")
PID_FILE = os.path.join(CONFIG_DIR, "fs_bridge.pid")
SUPPRESS_SECONDS = 2.0
DEBOUNCE_SECONDS = 0.080 # 80ms

try:
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
except Exception as e:
    pass

print(f"[FS Bridge] Starting with BPathMonitor on {WATCH_DIR}...", flush=True)

recently_touched = {}

path_monitor_bin = "/boot/home/config/bin/path_monitor"
if not os.path.exists(path_monitor_bin):
    path_monitor_bin = "/boot/system/bin/path_monitor"
if not os.path.exists(path_monitor_bin):
    path_monitor_bin = "/boot/home/docker-poc/path_monitor"

proc = subprocess.Popen(
    [path_monitor_bin, WATCH_DIR],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

pending_events = set()
last_event_time = 0

def forward_batch(paths):
    now = time.time()
    valid_paths = []
    for p in paths:
        if "/.git" in p or "/node_modules" in p or ".next" in p:
            continue
        last_t = recently_touched.get(p, 0)
        if now - last_t < SUPPRESS_SECONDS:
            continue
        valid_paths.append(p)

    if not valid_paths:
        return

    for p in valid_paths:
        recently_touched[p] = now

    for k in list(recently_touched.keys()):
        if now - recently_touched[k] > 10.0:
            del recently_touched[k]

    cmd_paths = " ".join([f'"{p}"' for p in valid_paths])
    print(f"[FS Bridge] Propagating change for {len(valid_paths)} files: {valid_paths}", flush=True)
    try:
        if os.path.exists(SOCK):
            subprocess.run(
                ["ssh", "-q", "-S", SOCK, "root@127.0.0.1", f"touch -c {cmd_paths}"],
                timeout=3
            )
        else:
            subprocess.run(
                ["ssh", "-q", "-o", "ConnectTimeout=2", "-i", KEY,
                 "-p", "2265", "root@127.0.0.1", f"touch -c {cmd_paths}"],
                timeout=3
            )
    except Exception as e:
        print(f"[FS Bridge] Error touching files: {e}", flush=True)

try:
    while True:
        rlist, _, _ = select.select([proc.stdout], [], [], 0.05)
        now = time.time()
        if rlist:
            line = proc.stdout.readline()
            if not line:
                break
            path = line.strip()
            if path:
                pending_events.add(path)
                last_event_time = now

        if pending_events and (now - last_event_time >= DEBOUNCE_SECONDS):
            to_send = list(pending_events)
            pending_events.clear()
            forward_batch(to_send)
finally:
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass
