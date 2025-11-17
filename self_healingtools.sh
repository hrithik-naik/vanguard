#!/usr/bin/env bash

set -e

echo "🔧 Updating package list..."
sudo apt update -y

echo "📦 Installing debugging and analysis tools..."
sudo apt install -y \
    gdb \
    valgrind \
    strace \
    ltrace \
    binutils \
    elfutils \
    systemd-coredump

echo "🧰 Installing development toolchain..."
sudo apt install -y \
    build-essential \
    clang \
    clang-tools \
    cmake \
    pkg-config

echo "🧪 Installing sanitizer libraries..."
sudo apt install -y \
    libasan6 \
    libtsan2 \
    libubsan1 \
    liblsan0 || true

echo "📊 Installing monitoring utilities..."
sudo apt install -y \
    sysstat \
    procps \
    iproute2 \
    net-tools

echo "🛡 Installing optional security utilities..."
sudo apt install -y \
    auditd \
    fail2ban \
    nmap

echo "📝 Enabling core dumps..."
sudo bash -c 'echo "* soft core unlimited" >> /etc/security/limits.conf'
sudo bash -c 'echo "* hard core unlimited" >> /etc/security/limits.conf'
sudo bash -c 'sysctl -w kernel.core_pattern=/var/crash/core.%e.%p'

echo "✅ Installation complete."
echo "⚠️ Restart the terminal or run: source /etc/profile"
