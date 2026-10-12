# Docker on Haiku OS (Hardware-Accelerated via NVMM)

Hi everyone,

I'm excited to share **Haiku Docker v1.0.0**, bringing native Docker CLI capabilities and container workflows to Haiku OS with hardware acceleration!

* **GitHub Repository:** https://github.com/timmagicbeans/haiku-docker
* **Release v1.0.0:** https://github.com/timmagicbeans/haiku-docker/releases/tag/v1.0.0

### Architecture & Features
1. **Hardware Acceleration via NVMM:**
   Under the hood, Haiku runs an ultra-lean Alpine Linux micro-VM via QEMU with `-accel nvmm`. CPU execution is near-native without TCG overhead.
2. **Transparent CLI & Drop-in Integration:**
   Standard `docker` and `docker compose` commands work seamlessly out of the box in Terminal.
3. **Deskbar Replicant:**
   `DockerDeskbar` sits in the Deskbar tray with live status indicators and right-click Start / Stop controls.
4. **Bi-directional Dev Sharing & Hot Reloading:**
   Haiku's `/boot/home/dev` is shared into the guest via SSHFS. File modifications trigger instantaneous inotify events via a custom `BPathMonitor` bridge (tested Next.js live hot-reload latency: **552 ms** without polling!).
5. **Dynamic Port Forwarding:**
   Containers exposing ports (e.g. `docker run -p 3000:3000`) are automatically tunneled to Haiku host `localhost:3000` via a background daemon.
6. **Persistent User Overlay:**
   Uses a clean qcow2 backing-file overlay architecture (`~/config/settings/docker-vm/os.qcow2`) so guest containers and settings persist across restarts, while preserving base image integrity.

### Recipe & Upstream Bug Reports
* A HaikuPorts recipe (`docker_haiku-1.0.0.recipe`) is prepared in the repository.
* Detailed NVMM driver bug reports and workarounds (`noxsave`, `smm=off`, physical memory leak on SIGKILL) have been documented for Haiku Trac developers in `haiku_nvmm_tickets.md`.

Feedback, testing, and contributions are warmly welcome!
