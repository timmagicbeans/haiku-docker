# Haiku NVMM Driver Upstream Bug Reports

### Ticket 1: Linux guest crash during FPU extended state probing (`fpstate_reset`) without `noxsave`
* **Component:** `drivers/dev/misc/nvmm` (x86 VMX/SVM emulation)
* **Summary:** Linux guest kernel crashes or hangs during early boot initialization of extended FPU features unless `noxsave` is passed on the kernel command line.
* **Reproduction Steps:**
  1. Boot any modern Linux kernel (tested with 6.6 and 6.18) under QEMU accelerated with NVMM on Haiku:
     ```sh
     qemu-system-x86_64 -accel nvmm -smp 1 -machine pc,smm=off -nodefaults -vga none -display none ...
     ```
  2. Observe early kernel crash during `fpu__init_system()` -> `fpstate_reset()`.
  3. Append `noxsave` to the kernel arguments: guest boots cleanly to userspace.
* **Impact:** Workloads and runtimes requiring AVX/AVX2 instructions cannot execute (e.g., MongoDB 5+, precompiled binary extensions requiring AVX).
* **Observed Behavior & Workaround:** Adding `noxsave` bypasses probing of extended XSAVE/XRSTOR processor states, allowing the system to run stably.

---

### Ticket 2: Failure in `nvmm_gpa_unmap` when address space includes SMM / ROM regions
* **Component:** `drivers/dev/misc/nvmm` / `libnvmm`
* **Summary:** QEMU encounters `nvmm_gpa_unmap: Cannot allocate memory` (error `0x7fff9000` / `-ENOMEM`) during guest memory space setup or teardown when default PC machine ROM/SMM regions are present.
* **Reproduction Steps:**
  1. Run QEMU with default machine parameters:
     ```sh
     qemu-system-x86_64 -accel nvmm -machine pc -m 1024M ...
     ```
  2. QEMU aborts with an unmap error during address space initialization or device setup.
* **Observed Behavior & Workaround:** Adding `smm=off`, `-nodefaults`, and `-vga none` eliminates the ROM regions and address space reorganizations where `nvmm_gpa_unmap` fails.

---

### Ticket 3: Physical memory descriptor leak upon abnormal QEMU termination (`kill -9`)
* **Component:** `drivers/dev/misc/nvmm`
* **Summary:** Killing the QEMU process with `SIGKILL` causes physical memory allocated to the guest to remain unmapped and leaked in the Haiku kernel until host reboot.
* **Reproduction Steps:**
  1. Run QEMU with NVMM (e.g. allocating 1024 MB RAM).
  2. Terminate the process cleanly (`poweroff` or QMP `quit`): observe `sysinfo -mem` returns fully to free memory (~1.7 GB).
  3. Start QEMU again and issue `kill -9 <qemu_pid>`: observe that memory allocated to the guest is NOT returned to the system. Subsequent attempts to allocate guest RAM quickly fail with `ENOMEM`.
* **Observed Behavior & Workaround:** Clean termination via ACPI powerdown or QMP quit completely prevents the leak. Suspected cause: abnormal termination lacks a kernel-side cleanup hook in `/dev/misc/nvmm` on `device_close`.
