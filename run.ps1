# Start mubaiOS in a real QEMU window (not headless).
#
#   .\run.ps1                 normal boot, 1280x800 window, absolute mouse
#   .\run.ps1 -Debug          also expose a shell on the serial port
#   .\run.ps1 -MemoryMB 1024
#
# Quit the VM with the window close button, or Ctrl+Alt+Q inside the window.
param(
    [int]$MemoryMB = 2560,
    [switch]$Debug
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

$qemu = @(
    (Join-Path $root '..\tinylinux\out\toolchain\msys64\ucrt64\bin\qemu-system-x86_64.exe'),
    (Join-Path $root 'out\toolchain\msys64\ucrt64\bin\qemu-system-x86_64.exe')
) | Where-Object { Test-Path $_ } | Select-Object -First 1

$kernel = Join-Path $root 'out\nova.bzImage'
$initrd = Join-Path $root 'out\nova-initramfs.cpio.gz'

if (-not (Test-Path $qemu)) { throw "QEMU not found" }
if (-not (Test-Path $initrd)) { throw "run: python build.py" }

$cmdline = 'console=ttyS0 rdinit=/init loglevel=3 vt.global_cursor_default=0'
if ($Debug) { $cmdline += ' nova.debug=1' }

Write-Host "starting mubaiOS in a QEMU window (1280x800)..." -ForegroundColor Cyan
& $qemu -m $MemoryMB -smp 4 `
    -kernel $kernel -initrd $initrd -append $cmdline `
    -vga std -usb -device usb-tablet -netdev user,id=n0 -device virtio-net-pci,netdev=n0 -drive file=out/nova-disk.qcow2,if=none,id=d0,format=qcow2 -device virtio-blk-pci,drive=d0 -accel whpx `
    -display gtk -serial "file:$root\out\window-serial.log" `
    -no-reboot
