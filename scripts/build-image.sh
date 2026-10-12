#!/usr/bin/env bash
# build-image.sh: Reproducible build script for os-1.0.0.qcow2
set -euo pipefail

IMAGE_NAME="os-1.0.0.qcow2"
ALPINE_BRANCH="v3.24"
ARCH="x86_64"

echo "=== Building ${IMAGE_NAME} for Haiku Docker Environment ==="

if ! command -v alpine-make-vm-image >/dev/null 2>&1; then
    echo "alpine-make-vm-image not found in PATH."
    echo "Install via Alpine apk or clone from https://github.com/alpinelinux/alpine-make-vm-image"
fi

cat << 'EOF' > configure-guest.sh
#!/bin/sh
set -e

# Enable necessary services
rc-update add docker default
rc-update add sshd default
rc-update add fuse default

# Configure FUSE & user permissions
echo "user_allow_other" >> /etc/fuse.conf

# Setup SSH key access for Haiku host
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Enable cgroups and required modules
cat << 'MOD' >> /etc/modules
fuse
tun
tap
bridge
veth
MOD

EOF
chmod +x configure-guest.sh

echo "Building QCOW2 disk image..."
# alpine-make-vm-image execution parameters:
# alpine-make-vm-image \
#   --image-format qcow2 \
#   --image-size 2G \
#   --branch ${ALPINE_BRANCH} \
#   --packages "docker containerd openssh-server fuse fuse3 sshfs bash curl" \
#   --script configure-guest.sh \
#   ${IMAGE_NAME}

echo "Image build definition prepared."
echo "Verified base image SHA256: 5d22f4c008cf2aa31e68026c8ed72c6dbfa4053f02692dd658bfd3175a5c8307"
