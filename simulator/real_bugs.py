#!/usr/bin/env python3
"""
Create REAL bugs that AI can actually fix
These are safe but real system issues
"""

import subprocess
import time
import os
import signal

class RealBugCreator:
    
    def create_broken_service(self):
        """
        Create a systemd service that crashes
        AI can detect it and restart it
        """
        print("🔴 Creating broken service...")
        
        # Create a service that crashes
        service_content = """[Unit]
Description=Test Broken Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -c "import sys; print('Starting...'); sys.exit(1)"
Restart=no

[Install]
WantedBy=multi-user.target
"""
        
        service_path = "/tmp/broken-test.service"
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        print(f"✓ Created service file: {service_path}")
        print("To install: sudo cp /tmp/broken-test.service /etc/systemd/system/")
        print("Then: sudo systemctl start broken-test")
        print("\nAI can detect this is failed and restart it!")
    
    def create_memory_leak_process(self):
        """
        Start a real process that leaks memory
        AI can detect high memory and kill it
        """
        print("💾 Creating real memory leak process...")
        
        code = """
import time
leaked = []
while True:
    leaked.append(' ' * 1024 * 1024)  # 1MB per second
    time.sleep(1)
"""
        
        proc = subprocess.Popen(
            ['python3', '-c', code],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"✓ Memory leak started (PID: {proc.pid})")
        print(f"  This process will consume RAM")
        print(f"  AI can detect it with 'ps aux' and kill PID {proc.pid}")
        print(f"\nManual fix: kill {proc.pid}")
        
        return proc.pid
    
    def create_disk_full_scenario(self):
        """
        Fill up disk space in /tmp
        AI can detect and clean it up
        """
        print("💿 Creating disk space issue...")
        
        # Create large files in /tmp
        for i in range(10):
            filename = f"/tmp/large_file_{i}.tmp"
            subprocess.run(['dd', 'if=/dev/zero', f'of={filename}', 'bs=1M', 'count=100'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✓ Created 1GB of files in /tmp")
        print("  Files: /tmp/large_file_*.tmp")
        print("  AI can detect with 'df -h' and remove with 'rm /tmp/large_file_*.tmp'")
        print("\nManual fix: rm /tmp/large_file_*.tmp")
    
    def create_zombie_process(self):
        """
        Create a zombie (defunct) process
        AI can detect and clean it
        """
        print("🧟 Creating zombie process...")
        
        code = """
import os
import time
pid = os.fork()
if pid > 0:
    time.sleep(60)
else:
    exit(0)
"""
        
        proc = subprocess.Popen(['python3', '-c', code])
        
        print(f"✓ Zombie process creator started (PID: {proc.pid})")
        print("  Check with: ps aux | grep defunct")
        print("  AI can detect zombies and kill parent process")
    
    def create_high_cpu_process(self):
        """
        Create process using 100% CPU
        AI can detect and nice/kill it
        """
        print("🔥 Creating high CPU process...")
        
        code = """
while True:
    pass
"""
        
        proc = subprocess.Popen(['python3', '-c', code])
        
        print(f"✓ CPU hog started (PID: {proc.pid})")
        print("  Check with: top")
        print(f"  AI can detect high CPU and kill PID {proc.pid}")
        print(f"\nManual fix: kill {proc.pid}")
        
        return proc.pid
    
    def create_port_conflict(self):
        """
        Start service on port already in use
        AI can detect and kill conflicting process
        """
        print("🔌 Creating port conflict...")
        
        # Start two processes on same port
        code1 = """
import socket
s = socket.socket()
s.bind(('0.0.0.0', 8888))
s.listen(1)
print("Listening on 8888")
input()
"""
        
        proc1 = subprocess.Popen(['python3', '-c', code1], stdin=subprocess.PIPE)
        time.sleep(1)
        
        # Try to start another on same port (will fail)
        proc2 = subprocess.Popen(['python3', '-c', code1], 
                                stderr=subprocess.PIPE)
        
        print(f"✓ Port 8888 is now blocked by PID {proc1.pid}")
        print("  AI can detect with 'netstat' or 'lsof' and kill the blocker")
        print(f"\nManual fix: kill {proc1.pid}")
        
        return proc1.pid
    
    def create_permission_issue(self):
        """
        Create file with wrong permissions
        AI can detect and fix with chmod
        """
        print("🔒 Creating permission issue...")
        
        testfile = "/tmp/permission_test.txt"
        
        with open(testfile, 'w') as f:
            f.write("test data")
        
        os.chmod(testfile, 0o000)  # No permissions
        
        print(f"✓ Created file with no permissions: {testfile}")
        print("  Try: cat /tmp/permission_test.txt (will fail)")
        print("  AI can fix with: chmod 644 /tmp/permission_test.txt")
        print("\nManual fix: chmod 644 /tmp/permission_test.txt")
    
    def create_log_rotation_issue(self):
        """
        Create huge log file
        AI can detect and truncate/rotate it
        """
        print("📝 Creating log file issue...")
        
        logfile = "/tmp/huge_app.log"
        
        # Create 100MB log file
        with open(logfile, 'w') as f:
            for i in range(100000):
                f.write(f"[ERROR] This is log line {i}\n" * 10)
        
        size = os.path.getsize(logfile) / (1024*1024)
        print(f"✓ Created {size:.1f}MB log file: {logfile}")
        print("  AI can detect with 'du -sh' and fix with: truncate -s 0 /tmp/huge_app.log")
        print("\nManual fix: truncate -s 0 /tmp/huge_app.log")

def main():
    creator = RealBugCreator()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║           CREATE REAL BUGS FOR AI TO FIX                  ║
╚════════════════════════════════════════════════════════════╝

These create REAL system issues that AI can actually detect and fix.

Choose:
1. Memory Leak Process (AI kills it)
2. High CPU Process (AI kills it)
3. Disk Full (AI cleans files)
4. Permission Issue (AI fixes chmod)
5. Huge Log File (AI truncates)
6. Port Conflict (AI kills blocker)
7. Zombie Process (AI cleans)

0. Exit
""")
    
    choice = input("Enter choice: ").strip()
    
    pids = []
    
    try:
        if choice == "1":
            pid = creator.create_memory_leak_process()
            pids.append(pid)
            print("\n✓ Bug created! Your detection system should pick this up.")
            print("  Watch: ps aux | grep python")
            input("\nPress ENTER when done to cleanup...")
        
        elif choice == "2":
            pid = creator.create_high_cpu_process()
            pids.append(pid)
            print("\n✓ Bug created! Check with 'top'")
            input("\nPress ENTER when done to cleanup...")
        
        elif choice == "3":
            creator.create_disk_full_scenario()
            print("\n✓ Bug created! Check with 'df -h /tmp'")
            input("\nPress ENTER when done to cleanup...")
            subprocess.run(['rm', '-f'] + [f'/tmp/large_file_{i}.tmp' for i in range(10)])
            print("✓ Cleaned up")
        
        elif choice == "4":
            creator.create_permission_issue()
            print("\n✓ Bug created!")
            input("\nPress ENTER when done to cleanup...")
            os.chmod("/tmp/permission_test.txt", 0o644)
            os.remove("/tmp/permission_test.txt")
            print("✓ Cleaned up")
        
        elif choice == "5":
            creator.create_log_rotation_issue()
            print("\n✓ Bug created! Check with 'ls -lh /tmp/huge_app.log'")
            input("\nPress ENTER when done to cleanup...")
            os.remove("/tmp/huge_app.log")
            print("✓ Cleaned up")
        
        elif choice == "6":
            pid = creator.create_port_conflict()
            pids.append(pid)
            print("\n✓ Bug created! Check with 'netstat -tulpn | grep 8888'")
            input("\nPress ENTER when done to cleanup...")
        
        elif choice == "7":
            creator.create_zombie_process()
            print("\n✓ Bug created! Check with 'ps aux | grep defunct'")
            input("\nPress ENTER when done to cleanup...")
        
        elif choice == "0":
            return
        
        else:
            print("Invalid choice")
            return
        
    finally:
        # Cleanup processes
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"✓ Killed process {pid}")
            except:
                pass

if __name__ == "__main__":
    main()