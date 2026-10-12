# Haiku NVMM Driver Upstream Bug Reports

**Environment Across All Tickets:**
* **Host Operating System:** Haiku R1~beta6 x86_64 (`hrev59866+90`, Oct 4 2026).
* **Virtualization Mode:** Running in **nested virtualization** (outer hypervisor exposing VT-x/VMX extensions to Haiku guest, CPU: 2x Intel Core i7-8700).
* **Driver:** `/boot/system/add-ons/kernel/drivers/dev/misc/nvmm` (`/dev/misc/nvmm`).
* **QEMU Version:** `qemu-system-x86_64` 8.2+ (`qemu_x86` from HaikuPorts).

---

### Ticket 1: Linux guest crash during FPU extended state probing (`fpstate_reset`) without `noxsave`
* **Component:** `Drivers/Misc` (or `Drivers/dev/misc/nvmm`)
* **Type:** `bug`
* **Summary:** Linux guest kernel (6.18) crashes during early boot initialization of extended FPU features unless `noxsave` is passed on the command line.
* **Reproduction Steps:**
  1. Boot Linux kernel 6.18 under QEMU accelerated with NVMM on Haiku:
     ```sh
     qemu-system-x86_64 -accel nvmm -smp 1 -machine pc,smm=off -nodefaults -vga none -display none ...
     ```
  2. Observe early kernel panic with call trace:
     ```text
     RIP: 0010:fpstate_reset+0x15/0x90
     #PF: supervisor write access in kernel mode (error_code 0x0002)
     Kernel panic - not syncing: Attempted to kill the idle task!
     ```
  3. Note on versions: Linux kernel 6.6 boots to userspace **without** `noxsave`, whereas 6.18 reliably reproduces this panic.
  4. Append `noxsave` to the guest kernel command line: Linux 6.18 boots cleanly to userspace.
* **Impact:** Guest runtimes requiring AVX/AVX2 instruction sets fail to run.
* **Observed Behavior & Workaround:** Adding `noxsave` disables XSAVE/XRSTOR processor state probing, avoiding the panic.
* **Reference & Context:** https://github.com/timmagicbeans/haiku-docker

---

### Ticket 2: Abort in `nvmm_gpa_unmap` during memory setup / unmap under SMP and default machine configs
* **Component:** `Drivers/Misc`
* **Type:** `bug`
* **Summary:** QEMU aborts in `nvmm_gpa_unmap` when SMP (`-smp 2`) and default PC machine ROM/SMM regions are present.
* **Reproduction Steps:**
  1. Launch QEMU with NVMM accelerator using SMP:
     ```sh
     qemu-system-x86_64 -accel nvmm -smp 2 -machine pc ...
     ```
  2. QEMU aborts with the following trace:
     ```text
     </boot/system/lib/libnvmm.so> nvmm_gpa_unmap.cold + 0
     </boot/system/bin/qemu-system-x86_64> nvmm_process_section + 0xe5
     qemu: qemu_cond_wait_impl: Operation not allowed -> Abort
     ```
* **Observed Behavior & Workaround:** Running with `-smp 1`, `-machine pc,smm=off`, `-nodefaults`, and `-vga none` avoids the ROM/SMM remapping and unmap crash.
* **Reference & Context:** https://github.com/timmagicbeans/haiku-docker

---

### Ticket 3: Physical memory descriptor leak upon abnormal QEMU termination (`kill -9`)
* **Component:** `Drivers/Misc`
* **Type:** `bug`
* **Summary:** Terminating QEMU via `SIGKILL` leaks guest physical memory mappings in the NVMM kernel driver until host reboot.
* **Reproduction Steps:**
  1. Start QEMU with NVMM (e.g. allocating guest memory).
  2. Kill the process abnormally: `kill -9 <qemu_pid>`.
  3. Attempt to start QEMU again: NVMM fails to allocate/map host physical memory, emitting:
     ```text
     NVMM: Failed to map HVA, HostVA:0x93f8d70000 Size:0x10000000 bytes, error=2147454976
     ```
     Subsequent allocations fail with `ENOMEM` / `0x7fff9000` until the Haiku host machine is rebooted.
  4. Compare with graceful shutdown (`poweroff` in guest or ACPI/QMP `quit`): memory is cleanly reclaimed and returned to Haiku (`sysinfo -mem`).
* **Observed Behavior & Workaround:** Clean shutdown completely avoids the leak. Suspected cause: lack of cleanup hook in `/dev/misc/nvmm` on abnormal process termination (`device_close`).
* **Reference & Context:** https://github.com/timmagicbeans/haiku-docker
