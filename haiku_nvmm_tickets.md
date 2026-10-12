# Haiku NVMM Driver Upstream Bug Reports

**Environment Across All Tickets:**
* **Host Operating System:** Haiku R1~beta6 x86_64 (`hrev59866+90`, Oct 4 2026).
* **Virtualization Mode:** Running in **nested virtualization** (outer hypervisor exposing VT-x/VMX extensions to Haiku guest, CPU: 2x Intel Core i7-8700).
* **Driver:** `/boot/system/add-ons/kernel/drivers/dev/misc/nvmm` (`/dev/misc/nvmm`).
* **QEMU Version:** `qemu-system-x86_64` 8.2+ (`qemu_x86` from HaikuPorts).

---

### Ticket 1: Linux guest (6.18) crashes in fpstate_reset without noxsave under NVMM
* **Component:** `Drivers/Misc` (or `Drivers/dev/misc/nvmm`)
* **Type:** `bug`
* **Summary:** Linux guest kernel (6.18) crashes during early boot initialization of extended FPU features unless `noxsave` is passed on the command line.
* **Reproduction Steps:**
  1. Boot Linux kernel 6.18 under QEMU accelerated with NVMM on Haiku:
     ```sh
     qemu-system-x86_64 \
       -accel nvmm \
       -smp 1 \
       -machine pc,smm=off \
       -nodefaults \
       -vga none \
       -display none \
       -m 1024M \
       -object memory-backend-ram,id=m0,size=512M \
       -object memory-backend-ram,id=m1,size=512M \
       -numa node,memdev=m0 -numa node,memdev=m1 \
       -kernel /boot/home/config/settings/docker-vm/vmlinuz-virt \
       -initrd /boot/home/config/settings/docker-vm/initramfs-virt \
       -drive file=/boot/home/config/settings/docker-vm/os.qcow2,if=virtio,id=rootdisk \
       -drive file=/boot/home/config/settings/docker-vm/data.qcow2,if=virtio,id=datadisk \
       -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2265-:22 \
       -device virtio-net-pci,netdev=net0 \
       -append "console=ttyS0 root=/dev/vda1 rw rootfstype=ext4 tsc=reliable clocksource=tsc" \
       -serial stdio
     ```
  2. Observe early kernel panic with call trace:
     ```text
     #PF: supervisor write access in kernel mode
     #PF: error_code(0x0002) - not-present page
     PGD 0 P4D 0
     Oops: Oops: 0002 [#1] SMP PTI
     CPU: 0 UID: 0 PID: 0 Comm: swapper/0 Tainted: G        W           6.18.55-0-virt #1-Alpine PREEMPT(none)
     RIP: 0010:fpstate_reset+0x15/0x90
     Code: 00 00 00 00 00 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 f3 0f 1e fa 48 8d 47 40 48 8b 35 99 5b 21 01 8b 15 ef 5b 21 01 <48> 89 47 10 8b 05 81 5b 21 01 4c 8b 05 ea 5b 21 01 f6 47 60 02 74
     RSP: 0000:ffffffff97a03e10 EFLAGS: 00010246
     Call Trace:
      <TASK>
      fpu__init_system_early_generic+0x4a/0x80
      fpu__init_system+0x1c/0x1e0
      arch_cpu_finalize_init+0x11/0x70
      start_kernel+0x3ba/0x780
      x86_64_start_reservations+0x24/0x30
      x86_64_start_kernel+0xc7/0xd0
      common_startup_64+0x13b/0x148
      </TASK>
     Kernel panic - not syncing: Attempted to kill the idle task!
     ```
  3. Note on versions: Linux kernel 6.6 reached initramfs userspace without `noxsave` (no FPU panic), whereas 6.18 reliably reproduces this panic.
  4. Appending `noxsave` to the guest kernel command line: Linux 6.18 boots cleanly to userspace.
* **Impact:** Guest runtimes requiring AVX/AVX2 instruction sets fail to run.
* **Attachments:**
  - `ticket1_kernel_panic.log` (Full guest serial console output until panic)
  - `haiku_syslog_sample.log` (Host syslog during run)

---

### Ticket 2: Abort in `nvmm_gpa_unmap` during memory setup / unmap under SMP and default machine configs
* **Component:** `Drivers/Misc`
* **Type:** `bug`
* **Summary:** QEMU aborts in `nvmm_gpa_unmap` when SMP (`-smp 2`) and default PC machine ROM/SMM regions are present.
* **Reproduction Steps:**
  1. Launch QEMU with NVMM accelerator using SMP and standard PC machine:
     ```sh
     qemu-system-x86_64 \
       -accel nvmm \
       -smp 2 \
       -machine pc \
       -m 1024M \
       -kernel /boot/home/config/settings/docker-vm/vmlinuz-virt \
       -initrd /boot/home/config/settings/docker-vm/initramfs-virt \
       -append "console=ttyS0 noxsave" \
       -serial stdio
     ```
  2. QEMU aborts with the following trace in stderr:
     ```text
     </boot/system/lib/libnvmm.so> nvmm_gpa_unmap.cold + 0
     </boot/system/bin/qemu-system-x86_64> nvmm_process_section + 0xe5
     qemu: qemu_cond_wait_impl: Operation not allowed -> Abort
     ```
* **Observed Behavior & Workaround:** Running with `-smp 1`, `-machine pc,smm=off`, `-nodefaults`, and `-vga none` avoids the ROM/SMM remapping and unmap crash. Not yet isolated which of these factors triggers the abort.
* **Attachments:**
  - `ticket2_qemu_abort_stderr.log` (QEMU standard error with stack trace)
  - `haiku_syslog_sample.log` (Host kernel syslog)

---

### Ticket 3: Physical memory descriptor leak upon abnormal QEMU termination (`kill -9`)
* **Component:** `Drivers/Misc`
* **Type:** `bug`
* **Summary:** Terminating QEMU via `SIGKILL` leaks guest physical memory mappings in the NVMM kernel driver until host reboot.
* **Reproduction Steps:**
  1. Start QEMU with NVMM:
     ```sh
     qemu-system-x86_64 \
       -accel nvmm \
       -smp 1 \
       -machine pc,smm=off \
       -nodefaults \
       -vga none \
       -display none \
       -m 1024M \
       -object memory-backend-ram,id=m0,size=512M \
       -object memory-backend-ram,id=m1,size=512M \
       -numa node,memdev=m0 -numa node,memdev=m1 \
       -kernel /boot/home/config/settings/docker-vm/vmlinuz-virt \
       -initrd /boot/home/config/settings/docker-vm/initramfs-virt \
       -append "console=ttyS0 noxsave"
     ```
  2. Kill the process abnormally: `kill -9 <qemu_pid>`.
  3. Attempt to start QEMU again: NVMM fails to allocate/map host physical memory, emitting:
     ```text
     NVMM: Failed to map HVA, HostVA:0x93f8d70000 Size:0x10000000 bytes, error=2147454976
     ```
     Subsequent allocations fail with `ENOMEM` / `0x7fff9000` until the Haiku host machine is rebooted.
  4. Compare with graceful shutdown (`poweroff` in guest or ACPI/QMP `quit`): memory is cleanly reclaimed and returned to Haiku (`sysinfo -mem`).
* **Observed Behavior & Workaround:** Clean shutdown completely avoids the leak. Suspected cause: lack of cleanup hook in `/dev/misc/nvmm` on abnormal process termination (`device_close`).
* **Attachments:**
  - `haiku_syslog_sample.log` (Syslog showing NVMM HVA mapping error)
