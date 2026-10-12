#!/usr/bin/env python3
"""
Dynamic Port Forwarding Daemon for Docker on Haiku OS.
Queries running docker containers periodically.
When a container maps host ports (e.g. -p 3000:3000 or -p 8080:80),
it opens local TCP forwarding tunnels from Haiku localhost to the guest.
When containers stop, forwarders are cleanly terminated.
Resilient against idle periods and transient disconnects.
"""
import subprocess
import time
import os
import sys

CONFIG_DIR = "/boot/home/config/settings/docker-vm"
KEY = os.path.join(CONFIG_DIR, "id_docker_vm")
PORT = 2265

active_forwards = {}

def get_mapped_ports():
    if not os.path.exists(KEY):
        return []
    try:
        res = subprocess.run(
            ["ssh", "-q",
             "-o", "ConnectTimeout=3",
             "-o", "BatchMode=yes",
             "-o", "ServerAliveInterval=15",
             "-o", "ServerAliveCountMax=3",
             "-o", "StrictHostKeyChecking=no",
             "-i", KEY, "-p", str(PORT),
             "root@127.0.0.1", "docker ps --format '{{.Ports}}'"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5
        )
        if res.returncode != 0:
            return []
        
        ports = set()
        for line in res.stdout.strip().splitlines():
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
        return sorted(list(ports))
    except Exception:
        return []

def start_forward(port):
    print(f"[Port Daemon] Opening tunnel for host port {port} -> guest {port}...", flush=True)
    cmd = [
        "ssh", "-N",
        "-L", f"127.0.0.1:{port}:127.0.0.1:{port}",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "StrictHostKeyChecking=no",
        "-i", KEY, "-p", str(PORT),
        "root@127.0.0.1"
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    active_forwards[port] = p

def stop_forward(port):
    print(f"[Port Daemon] Closing tunnel for host port {port}...", flush=True)
    p = active_forwards.pop(port, None)
    if p:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

def main():
    print("[Port Daemon] Dynamic Docker port forwarder running (persistent polling)...", flush=True)
    consecutive_failures = 0
    while True:
        try:
            ports = get_mapped_ports()
            needed = set(ports)
            current = set(active_forwards.keys())

            # Stop no longer mapped ports
            for p in current - needed:
                stop_forward(p)

            # Start newly mapped ports
            for p in needed - current:
                start_forward(p)

            # Health check on active tunnel processes
            for p in list(active_forwards.keys()):
                proc = active_forwards[p]
                if proc.poll() is not None:
                    print(f"[Port Daemon] Tunnel on {p} exited (code {proc.poll()}). Re-evaluating...", flush=True)
                    if p in needed:
                        start_forward(p)
                    else:
                        del active_forwards[p]

            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            # Sleep slightly longer during successive transient failures
            time.sleep(min(consecutive_failures, 5))

        time.sleep(2)

if __name__ == "__main__":
    main()
