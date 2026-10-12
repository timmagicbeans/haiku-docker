# Docker on Haiku OS (Hardware-Accelerated via NVMM)

Hi everyone,

I'm excited to share **Haiku Docker v1.0.0**, bringing native Docker CLI capabilities and container workflows to Haiku OS with hardware acceleration!

* **GitHub Repository:** https://github.com/timmagicbeans/haiku-docker
* **Release v1.0.0:** https://github.com/timmagicbeans/haiku-docker/releases/tag/v1.0.0

### Architecture & Features
1. **Hardware Acceleration via NVMM:**
   Under the hood, Haiku runs a lightweight Alpine Linux micro-VM via QEMU with NVMM hardware acceleration (`-accel nvmm -smp 1 -m 1024M` partitioned across two 512M NUMA nodes).
2. **Transparent CLI & Drop-in Integration:**
   Standard `docker` and `docker compose` commands work seamlessly out of the box in Haiku Terminal.
3. **Deskbar Replicant:**
   `DockerDeskbar` sits in the Deskbar tray with live status indicators and right-click Start / Stop controls.
4. **Host-to-Guest Workspace Sharing & Hot Reloading:**
   Haiku's `/boot/home/dev` is shared into the guest via SSHFS. File modifications trigger instantaneous inotify events via a custom `BPathMonitor` bridge (verified with `fs.watch` in `node:20-alpine`, latency **~550 ms** without polling).
5. **Dynamic Port Forwarding:**
   Containers exposing ports (e.g. `docker run -p 3000:3000`) are automatically tunneled to Haiku host `localhost:3000` via a background daemon.
6. **Persistent User Storage:**
   Guest containers, volumes, and configurations are preserved directly in `~/config/settings/docker-vm/os.qcow2`.

### Requirements & Known Limitations
* **NVMM Driver:** Requires `/dev/misc/nvmm` enabled on Haiku host.
* **Kernel Argument `noxsave` (No AVX):** The guest Linux kernel boots with `noxsave` due to an upstream NVMM XSAVE/XRSTOR emulation bug. AVX/AVX2 instruction sets are disabled.
* **Single vCPU (`-smp 1`):** Micro-VM runs with 1 vCPU for stability.
* **Port Tunneling:** Dynamic forwarding is currently implemented for TCP ports.
* **Graceful Shutdown:** Always stop the VM cleanly via `docker_vm stop` or Deskbar to avoid physical memory leaks in the kernel driver caused by abrupt process termination (`kill -9`).

### Recipe & Upstream Bug Reports
* A HaikuPorts recipe (`docker_haiku-1.0.0.recipe`) is prepared in the repository.
* Detailed NVMM driver bug reports and workarounds (`noxsave`, `smm=off`, physical memory leak on SIGKILL) have been documented for Haiku Trac developers in `haiku_nvmm_tickets.md`.

Feedback, testing, and contributions are warmly welcome!
