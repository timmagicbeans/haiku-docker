# Haiku NVMM Driver Upstream Bug Reports

**Environment Across All Tickets:**
* **Host Operating System:** Haiku R1~beta6 x86_64 (`hrev59866+90`, Oct 4 2026).
* **Virtualization Mode:** Running in **nested virtualization** (outer hypervisor exposing VT-x/VMX extensions to Haiku guest, CPU: 2x Intel Core i7-8700).
* **Driver:** `/boot/system/add-ons/kernel/drivers/dev/misc/nvmm` (`/dev/misc/nvmm`).
* **QEMU Version:** `qemu-system-x86_64` 8.2+ (`qemu_x86` from HaikuPorts).

---

### Ticket 1: Linux guest (6.18) crashes in fpstate_reset without noxsave under NVMM
* **Component:** `Drivers/Misc` (or `System/Kernel`)
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
  3. **Version comparison:** Linux kernel 6.6 reached initramfs userspace without `noxsave` (no FPU panic), whereas 6.18 reliably reproduces this panic.
  4. **Root-cause hint for developers:**
     The faulting instruction opcode `48 89 47 10` is `mov %rax,0x10(%rdi)`. The page fault occurs with `RDI=0` (`CR2=0x10`), indicating that a pointer to `fpstate` is `NULL`. In Linux 6.18, `fpu__init_system_early_generic` calculates the buffer size and state offsets based on XSAVE CPUID leaf `0xD`. NVMM likely reports an unexpected or unhandled CPUID leaf `0xD` feature mask or size value, leading the kernel to skip allocation or miscalculate the initial fpstate buffer.
  5. **Workaround:** Appending `noxsave` to the guest kernel command line bypasses XSAVE initialization and boots Linux 6.18 cleanly to userspace.
* **Impact:** Guest runtimes requiring AVX/AVX2 instruction sets cannot function.
* **Attachments:**
  - `ticket1_kernel_panic.log` (Full guest serial console output until panic)
  - `haiku_syslog_sample.log` (Host syslog during run)

---

### Ticket 2: Abort in `nvmm_gpa_unmap` during memory setup / unmap under SMP and default machine configs
* **Component:** `Drivers/Misc` (or `System/Kernel`)
* **Type:** `bug`
* **Summary:** QEMU aborts in `nvmm_gpa_unmap` during flatview topology commit when SMP (`-smp 2`) and default PC machine configuration are used.
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
       -serial stdio -display none
     ```
  2. QEMU immediately aborts with the following stack trace in Haiku syslog / stderr:
     ```text
     KERN: debug_server: Thread 66137 entered the debugger: Debugger call: `abort() called'
     KERN: stack trace, current PC 0xb031593269 </boot/system/lib/libroot.so> _kern_debugger + 0x9:
     KERN:   (0x7fc59fcdabe0)  0x1d1ef84e0d5  </boot/system/lib/libnvmm.so> nvmm_gpa_unmap.cold + 0
     KERN:   (0x7fc59fcdac60)  0x39284ea035   </boot/system/bin/qemu-system-x86_64> nvmm_process_section + 0xe5
     KERN:   (0x7fc59fcdacb0)  0x392859dc62   </boot/system/bin/qemu-system-x86_64> address_space_update_topology_pass + 0x2e2
     KERN:   (0x7fc59fcdad60)  0x392859e04f   </boot/system/bin/qemu-system-x86_64> address_space_set_flatview + 0xbf
     KERN:   (0x7fc59fcdadd0)  0x39285a1d00   </boot/system/bin/qemu-system-x86_64> memory_region_transaction_commit + 0x130
     KERN:   (0x7fc59fcdadf0)  0x3928513ea7   </boot/system/bin/qemu-system-x86_64> pc_memory_init + 0x187
     KERN:   (0x7fc59fcdae70)  0x39284fbb01   </boot/system/bin/qemu-system-x86_64> pc_init1.constprop.0 + 0x1c1
     KERN:   (0x7fc59fcdaf30)  0x392830d4a4   </boot/system/bin/qemu-system-x86_64> machine_run_board_init + 0x254
     KERN:   (0x7fc59fcdb040)  0x3928480665   </boot/system/bin/qemu-system-x86_64> qmp_x_exit_preconfig + 0x55
     KERN:   (0x7fc59fcdb090)  0x39284846b7   </boot/system/bin/qemu-system-x86_64> qemu_init + 0x3c87
     KERN:   (0x7fc59fcdb1e0)  0x392829e6e9   </boot/system/bin/qemu-system-x86_64> main + 0x9
     ```
* **Observed Behavior & Workaround:** Running with `-smp 1`, `-machine pc,smm=off`, `-nodefaults`, and `-vga none` avoids the abort during flatview topology commit. Not yet isolated which of these factors triggers the abort.
* **Attachments:**
  - `ticket2_qemu_abort_stderr.log` (QEMU standard error with stack trace)
  - `ticket2_syslog_abort.log` (Host kernel syslog showing thread abort and stack trace)

---

### Ticket 3: Physical memory descriptor leak upon abnormal QEMU termination (`kill -9`)
* **Component:** `Drivers/Misc` (or `System/Kernel`)
* **Type:** `bug`
* **Summary:** Terminating QEMU via `SIGKILL` leaks guest physical memory mappings in the NVMM kernel driver until host reboot.
* **Reproduction Steps:**
  1. Fresh boot of Haiku host.
  2. Start QEMU with `-accel nvmm`:
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
  3. Abruptly kill the process: `kill -9 <qemu_pid>`.
  4. Start the same command again $\to$ QEMU fails immediately with:
     ```text
     NVMM: Failed to map HVA, HostVA:0x93f8d70000 Size:0x10000000 bytes, error=2147454976
     ```
     Subsequent allocations fail with `ENOMEM` / `0x7fff9000` until host reboot.
  5. Reboot Haiku host $\to$ launch works normally again.
* **Observed Behavior & Workaround:** Clean shutdown (`poweroff` in guest, ACPI/QMP `quit`, or SIGTERM) cleanly releases memory mappings back to Haiku (`sysinfo -mem`). Suspected cause: lack of cleanup handler in `/dev/misc/nvmm` when a process fd is forcibly closed on `SIGKILL`.
* **Attachments:**
  - `haiku_syslog_sample.log` (Syslog showing NVMM HVA mapping error)
