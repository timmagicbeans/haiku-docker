# Third Party Licenses and Open Source Disclosures

The `os-1.0.0.qcow2` micro-VM image distributed alongside Haiku Docker Project contains software components licensed under various open source licenses, including the GNU General Public License (GPLv2, GPLv3), LGPL, BSD, MIT, and Apache licenses.

## Source Code Availability

In compliance with the GNU General Public License and other reciprocal open source licenses, complete source code for all packages and components included in the micro-VM image is available upstream through Alpine Linux package repositories:

- **Alpine Linux Source Git (aports):** https://gitlab.alpinelinux.org/alpine/aports
- **Linux Kernel Source:** https://kernel.org (Linux 6.18.55-r0 `linux-virt`)

## Included Packages and Exact Versions

The base Alpine Linux system inside `os-1.0.0.qcow2` contains the following installed packages (`apk info -v`):

```text
alpine-base-3.24.2-r0
alpine-baselayout-3.7.2-r1
alpine-baselayout-data-3.7.2-r1
alpine-conf-3.22.0-r0
alpine-keys-2.6-r0
alpine-release-3.24.2-r0
apk-tools-3.0.8-r0
bash-5.3.9-r1
blkid-2.42.3-r1
bridge-1.5-r5
brotli-libs-1.2.0-r1
busybox-1.37.0-r31
busybox-binsh-1.37.0-r31
busybox-mdev-openrc-1.37.0-r31
busybox-openrc-1.37.0-r31
busybox-suid-1.37.0-r31
c-ares-1.34.8-r0
ca-certificates-20260909-r0
ca-certificates-bundle-20260909-r0
chrony-4.8-r7
chrony-common-4.8-r7
chrony-openrc-4.8-r7
containerd-2.3.6-r0
containerd-openrc-2.3.6-r0
cryptsetup-libs-2.8.6-r0
curl-8.22.0-r0
device-mapper-libs-2.03.35-r3
docker-29.8.2-r0
docker-cli-29.8.2-r0
docker-cli-buildx-0.34.1-r1
docker-engine-29.8.2-r0
docker-openrc-29.8.2-r0
e2fsprogs-1.47.4-r0
e2fsprogs-libs-1.47.4-r0
fuse-2.9.9-r7
fuse-common-3.18.3-r0
fuse-openrc-3.18.3-r0
fuse3-3.18.3-r0
fuse3-libs-3.18.3-r0
glib-2.88.1-r1
ifupdown-ng-0.13.0-r0
iptables-1.8.13-r0
iptables-openrc-1.8.13-r0
json-c-0.18-r1
kmod-34.2-r1
kmod-libs-34.2-r1
lddtree-1.27-r0
libapk-3.0.8-r0
libblkid-2.42.3-r1
libcap2-2.78-r0
libcom_err-1.47.4-r0
libcrypto3-3.5.9-r0
libcurl-8.22.0-r0
libeconf-0.8.3-r0
libedit-20260508.3.1-r1
libffi-3.5.2-r1
libidn2-2.3.8-r0
libintl-1.0-r0
libmnl-1.0.5-r2
libmount-2.42.3-r1
libncursesw-6.6_p20260516-r0
libnftnl-1.3.1-r0
libpsl-0.21.5-r3
libseccomp-2.6.1-r0
libssl3-3.5.9-r0
libunistring-1.4.2-r0
libuuid-2.42.3-r1
libxtables-1.8.13-r0
linux-virt-6.18.55-r0
log_proxy-0.7.4-r0
mdev-conf-4.10-r0
mkinitfs-3.14.1-r0
mtools-4.0.49-r0
musl-1.2.6-r2
musl-utils-1.2.6-r2
ncurses-terminfo-base-6.6_p20260516-r0
nghttp2-libs-1.70.0-r0
openrc-0.63.2-r0
openrc-user-0.63.2-r0
openssh-10.3_p1-r1
openssh-client-common-10.3_p1-r1
openssh-client-default-10.3_p1-r1
openssh-keygen-10.3_p1-r1
openssh-server-10.3_p1-r1
openssh-server-common-10.3_p1-r1
openssh-server-common-openrc-10.3_p1-r1
openssh-sftp-server-10.3_p1-r1
pcre2-10.49-r0
readline-8.3.3-r1
runc-1.4.3-r1
scanelf-1.3.9-r1
sshfs-3.7.6-r0
ssl_client-1.37.0-r31
syslinux-6.04_pre1-r19
tini-static-0.19.0-r3
xz-libs-5.8.4-r0
zlib-1.3.2-r1
zstd-libs-1.5.7-r2
```
