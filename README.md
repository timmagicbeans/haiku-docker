# Docker on Haiku OS (Accelerated by NVMM)

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/timmagicbeans)

Native Docker engine CLI and lightweight Linux micro-VM virtualization environment for Haiku OS, accelerated by NetBSD Virtual Machine Monitor (NVMM) port and QEMU.

## Architecture Overview

```
       +-------------------------------------------------------------+
       |                         Haiku OS                            |
       |                                                             |
       |   +-------------------+              +------------------+   |
       |   |    docker (CLI)   |              |  DockerDeskbar   |   |
       |   +---------+---------+              +--------+---------+   |
       |             | (SSH execution)                 | (Tray GUI)  |
       |             v                                 v             |
       |   +-----------------------------------------------------+   |
       |   |       docker_vm controller & background bridges     |   |
       |   |    (port_daemon.py, fs_bridge.py / BPathMonitor)    |   |
       |   +--------------------------+--------------------------+   |
       |                              |                              |
       |                 QEMU with NVMM Acceleration                 |
       |                   (/dev/misc/nvmm, smm=off)                 |
       +------------------------------+------------------------------+
                                      | VirtIO
       +------------------------------v------------------------------+
       |                   Alpine Linux Micro-VM                     |
       |   +-----------------------------------------------------+   |
       |   |                   dockerd engine                    |   |
       |   |            (containers, bridge networks)            |   |
       |   +--------------------------+--------------------------+   |
       |                              |                              |
       |         sshfs /boot/home/dev (host) -> /root/dev (guest)    |
       +-------------------------------------------------------------+
```

## Features

- **Standard `docker` CLI wrapper:** Run `docker run`, `docker ps`, `docker build`, `docker compose` directly from Terminal or build scripts.
- **Hardware Acceleration:** Uses `/dev/misc/nvmm` kernel accelerator via QEMU with near-native hardware virtualization.
- **Sub-second Hot Reload Bridge:** Host-to-guest filesystem synchronization (`/boot/home/dev`) with Haiku native `BPathMonitor` event bridge into guest `inotify` (latency < 600 ms, verified with `fs.watch` in `node:20-alpine`).
- **Dynamic Port Forwarding:** Zero-config container TCP ports (`-p 3000:3000`) forwarded locally on Haiku localhost on-the-fly and cleanly terminated when containers stop.
- **Deskbar Tray Replicant (`DockerDeskbar`):** Live status monitor, start/stop controls, and workspace access in Haiku Deskbar.
- **Persistence & Integrity:** Base image SHA256 integrity verification with persistent user storage in `~/config/settings/docker-vm/os.qcow2`.

---

## Requirements & Known Limitations

1. **NVMM Kernel Driver:**
   - Requires `/dev/misc/nvmm` driver enabled on Haiku.
2. **Host Memory Limit for Micro-VM:**
   - The VM is configured with **1024 MB RAM** partitioned into two 512 MB NUMA blocks (`-object memory-backend-ram,size=512M`).
   - SMM must be disabled (`-machine pc,smm=off`) to avoid `nvmm_gpa_unmap: Cannot allocate memory` during GPA region tear-down.
3. **Linux Extended FPU State (`noxsave`):**
   - Linux kernel in the guest requires `noxsave` on the command line due to an upstream NVMM XSAVE/XRSTOR emulation limitation. AVX/AVX2 instructions are disabled inside the VM.
4. **Single vCPU (`-smp 1`):**
   - Configured with 1 vCPU for maximum stability under the current Haiku NVMM implementation.
5. **Port Forwarding Scope:**
   - Automatic dynamic port forwarding daemon handles TCP port bindings.
6. **Abnormal Termination Memory Release:**
   - Always stop the micro-VM cleanly via `docker_vm stop` or Deskbar tray. Terminating QEMU with `SIGKILL` leaks physical memory mapping in the NVMM kernel driver until host reboot.

---

## Installation via HaikuPorts / HPKG

```sh
pkgman install docker_haiku
```

Or manually copy `docker_haiku-1.0.0-1-x86_64.hpkg` to `~/config/packages/`.

---

## Building Micro-VM Image from Source

The base micro-VM image `os-1.0.0.qcow2` can be constructed using Alpine Linux tools:

```sh
./scripts/build-image.sh
```

> [!NOTE]
> Images built via `alpine-make-vm-image` are functionally identical but **not bit-for-bit reproducible** due to filesystem timestamps, ext4 volume UUIDs, and upstream security package updates. The reference SHA256 (`5d22f4c008cf2aa31e68026c8ed72c6dbfa4053f02692dd658bfd3175a5c8307`) corresponds strictly to the official binary image published in GitHub Releases. Custom builds can verify package integrity against the version manifest in `THIRD_PARTY_LICENSES.md`.

## License

MIT License. See [LICENSE](LICENSE) for details.
