import pandas as pd
import numpy as np
import re
import os
from datetime import datetime


def preprocess_linux_logs(log_path, start_year=2024):
    """
    Preprocess Linux logs for kernel and driver fault detection with proper year handling.
    
    Args:
        log_path (str): Path to the Linux log file
        output_dir (str): Directory to save processed data
        start_year (int): Year when the logs start (June)
    """
    
    
   
    
    # Step 2: Define regex patterns for Linux log format
    # Month Day Time Hostname Service: Message
    log_pattern = r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+):\s+(.*)'
    
    # Refined patterns to identify kernel and driver failures
    kernel_driver_failure_patterns = [
        r'kernel panic',
        r'not syncing',
        r'Oops:',
        r'Call Trace:',
        r'BUG:',
        r'Out of memory',
        r'oom-killer',
        r'hung task',
        r'blocked for more than',
        r'segfault at',
        r'general protection fault',
        r'Unable to handle kernel',
        r'Machine check events?',
        r'driver.*(fail|error|fault|crash|timeout|reset)',
        r'module.*(fail|error|fault|crash|timeout|reset)'
    ]
    
    # For broader kernel and driver related log detection
    kernel_patterns = [
        r'kernel',
        r'driver',
        r'module',
        r'firmware',
        r'hardware',
        r'device',
        r'cpu',
        r'memory',
        r'disk',
        r'error',
        r'warning',
        r'fail',
        r'critical',
        r'panic'
    ]
    
    # Step 3: Parse log lines into structured format with proper year handling
    structured_logs = []
    current_year = start_year
    last_month = None
    
    for line in log_path:
        line = line.strip()
        if not line:
            continue
        
        match = re.search(log_pattern, line)
        if match:
            timestamp_str, hostname, service, message = match.groups()
            
            # Extract month to handle year transitions
            month_match = re.match(r'(\w{3})\s+', timestamp_str)
            if month_match:
                current_month = month_match.group(1)
                # Handle year transition (Dec to Jan)
                if last_month == 'Dec' and current_month == 'Jan':
                    current_year += 1
                last_month = current_month
            
            # Try to parse the timestamp with the correct year
            try:
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            except:
                timestamp = None
            
            # Check if this is kernel or driver related
            is_kernel_related = False
            matched_patterns = []
            
            for pattern in kernel_patterns:
                if re.search(pattern, message, re.IGNORECASE) or re.search(pattern, service, re.IGNORECASE):
                    is_kernel_related = True
                    matched_patterns.append(pattern)
            
            # Check for specific failure patterns
            is_failure = False
            for pattern in kernel_driver_failure_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    is_failure = True
                    break
            
            # Create log entry
            log_entry = {
                'timestamp': timestamp,
                'hostname': hostname,
                'service': service,
                'message': message,
                'is_kernel_related': is_kernel_related,
                'is_failure': is_failure,
                'matched_patterns': "|".join(matched_patterns) if matched_patterns else ""
            }
            
            structured_logs.append(log_entry)
    
    # Convert to DataFrame
    df = pd.DataFrame(structured_logs)
    
    # Step 4: Filter to keep only kernel and driver related logs
    kernel_logs = df[df['is_kernel_related']].copy()
    # print(f"Found {len(kernel_logs)} kernel and driver related logs out of {len(df)} total logs")
    # print(f"Of which {kernel_logs['is_failure'].sum()} are identified as failures")
    
    # Step 5: Extract additional features from the logs
    def extract_features(df):
        """Extract additional features from log messages for fault detection"""
        # Severity classification
        def classify_severity(message):
            if re.search(r'emergency|critical|alert|panic|fault', message, re.IGNORECASE):
                return 4  # Critical
            elif re.search(r'error|fail', message, re.IGNORECASE):
                return 3  # Error
            elif re.search(r'warning|warn', message, re.IGNORECASE):
                return 2  # Warning
            elif re.search(r'notice|info', message, re.IGNORECASE):
                return 1  # Info
            else:
                return 0  # Unknown
        
        df['severity'] = df['message'].apply(classify_severity)
        
        # Message length features
        df['message_length'] = df['message'].str.len()
        df['word_count'] = df['message'].str.split().str.len()
        
        # Improved fault type detection
        def detect_fault_type(message):
            import re
            message_lower = message.lower()

    # Kernel panic is highest priority
            if re.search(r'kernel[\s-]*panic|not[\s-]*syncing|panic[\s-]*kernel|fatal[\s-]*exception|panic[\s-]*in[\s-]*kernel|kernel[\s-]*trap|kernel[\s-]*oops|bsod|blue[\s-]*screen|system[\s-]*halt|critical[\s-]*failure|system[\s-]*crash', message_lower):
                return 'kernel_panic'

    # Memory-related issues
            if re.search(r'out of memory|oom-killer|oom|memory allocation|malloc|swap|heap|ram|memory[\s-]*leak|memory[\s-]*exhaustion|memory[\s-]*corruption|segmentation[\s-]*fault|page[\s-]*fault|memory[\s-]*pressure|swap[\s-]*thrashing|low[\s-]*memory|memory[\s-]*fragmentation|memory[\s-]*error|bad[\s-]*alloc|memory[\s-]*full|cannot[\s-]*allocate[\s-]*memory', message_lower):
                return 'memory'

    # Storage-related issues
            if re.search(r'disk|storage|i/o error|block|fs|filesystem|sata|raid|filesystem error|read error|hard drive failure|disk failure|smart error|bad sector|i/o timeout|disk full|corrupt|write error|unmounted|raid failure|disk read-write failure|block corruption|disk overheated|journal|inode|superblock|ext[2-4]|xfs|btrfs|ntfs|fat|exfat|mount[\s-]*failure|i/o[\s-]*wait|nfs|san|nas|storage[\s-]*array|lun|scsi|partition|data[\s-]*corruption', message_lower):
                return 'storage'

    # Driver/module issues
            if re.search(r'driver.*(fail|error|fault|crash|timeout|reset|unresponsive|hang|corruption|malfunction|deadlock|segfault|crash dump)|module.*(fail|error|fault|crash|timeout|reset|unresponsive|hang|corruption|malfunction|deadlock|segfault|crash dump)|firmware[\s-]*error|bios[\s-]*error|missing[\s-]*driver|incompatible[\s-]*driver|module[\s-]*load[\s-]*failed|insmod[\s-]*failed|modprobe[\s-]*error|unsigned[\s-]*module|tainted[\s-]*kernel|driver[\s-]*version[\s-]*mismatch', message_lower):
                return 'driver'

    # CPU/Processing issues
            if re.search(r'cpu|processor|core|hung task|blocked for more than|overclock|thermal shutdown|cpu usage|overheating|underclock|crash|core dump|load|throttle|interrupts|context switch|system hang|soft lockup|hard lockup|watchdog|high[\s-]*load[\s-]*average|scheduler|process[\s-]*starvation|realtime[\s-]*priority|nice[\s-]*value|affinity|clocksource|time[\s-]*jump|cpufreq|cpu[\s-]*governor|mce[\s-]*error|instruction[\s-]*error|illegal[\s-]*instruction', message_lower):
                return 'cpu'

    # Network-related issues
            if re.search(r'network|ethernet|wifi|connection|interface|tcp|udp|dns|packet loss|latency|connectivity|link[\s-]*down|ethernet[\s-]*error|nic|mac[\s-]*address|dhcp|ip[\s-]*address|route|gateway|subnet|vlan|bridge|bonding|teaming|mtu|socket|ping|traceroute|packet[\s-]*drop|network[\s-]*unreachable|host[\s-]*unreachable|link[\s-]*flapping|network[\s-]*congestion|buffer[\s-]*overflow|arp|rarp|icmp|network[\s-]*timeout', message_lower):
                return 'network'

    # Security issues
            if re.search(r'security|auth|permission|access|unauthorized|auth failure|hack|compromise|intrusion|malware|exploit|phishing|breach|ransomware|privilege escalation|spyware|trojan|denial of service|port scan|firewall bypass|keylogger|rootkit|authentication[\s-]*failure|failed[\s-]*login|brute[\s-]*force|suspicious[\s-]*activity|cve|vulnerability|zero[\s-]*day|backdoor|credential[\s-]*theft|session[\s-]*hijacking|ssh[\s-]*attack|ssl|tls|mitm|man[\s-]*in[\s-]*the[\s-]*middle', message_lower):
                return 'security'

    # Kernel bugs and exceptions
            if re.search(r'oops:|bug:|call trace:|segfault at|general protection fault|unable to handle kernel|kernel error|kernel[\s-]*bug|kernel[\s-]*null[\s-]*pointer|kernel[\s-]*page[\s-]*fault|kernel[\s-]*stack[\s-]*overflow|kernel[\s-]*protection|kernel[\s-]*exception|rip:|tip:|eip:|bad[\s-]*rip|invalid[\s-]*opcode|divide[\s-]*error|kernel[\s-]*warning|kernel[\s-]*mode[\s-]*exception|kernel[\s-]*fault', message_lower):
                return 'kernel_bug'

    # Hardware-related issues
            if re.search(r'machine check events?|hardware error|hardware failure|faulty|overheated|device error|pci[\s-]*error|hardware[\s-]*event|hardware[\s-]*interrupt|acpi[\s-]*error|usb[\s-]*error|device[\s-]*disconnect|device[\s-]*failure|fan[\s-]*failure|temperature[\s-]*critical|thermal[\s-]*event|sensor[\s-]*error|hardware[\s-]*monitoring|bios[\s-]*error|firmware[\s-]*error|ecc[\s-]*error|uncorrectable[\s-]*error|correctable[\s-]*error|gpu[\s-]*error', message_lower):
                return 'hardware'

    # Power-related issues
            if re.search(r'power failure|voltage|battery|power off|shutdown|acpi|battery error|ups|power[\s-]*supply|power[\s-]*management|power[\s-]*state|suspend|hibernate|resume|standby|power[\s-]*saving|low[\s-]*battery|critical[\s-]*battery|power[\s-]*event|undervoltage|overvoltage|power[\s-]*surge|brown[\s-]*out|clean[\s-]*shutdown|dirty[\s-]*shutdown|emergency[\s-]*shutdown|power[\s-]*button', message_lower):
                return 'power'

    # Software-related issues
            if re.search(r'software failure|exception|stack trace|segmentation fault|bug report|core dump|segfault|assertion failed|crash|fault|abort|illegal instruction|unhandled exception|stack overflow|bus error|application[\s-]*crash|service[\s-]*failure|daemon[\s-]*crash|unexpected[\s-]*termination|exit[\s-]*code|signal[\s-]*[0-9]+|killed|terminated|coredump|backtrace|null[\s-]*pointer|dangling[\s-]*pointer|double[\s-]*free|use[\s-]*after[\s-]*free|memory[\s-]*leak', message_lower):
                return 'software'

    # Performance issues
            if re.search(r'latency|timeout|response time|slowness|performance degradation|lag|delay|slow|lagginess|freeze|throughput|bottleneck|overload|unresponsive|high[\s-]*utilization|resource[\s-]*contention|i/o[\s-]*wait|load[\s-]*average|queuing|congestion|thrashing|spikes|jitter|stutter|backlog|resource[\s-]*exhaustion|load[\s-]*balancing|scaling[\s-]*issue|performance[\s-]*regression', message_lower):
                return 'performance'

    # Default case for unclassified faults
            return 'other'
        
        df['fault_type'] = df['message'].apply(detect_fault_type)
        
        # Technical value extraction
        df['has_hex_address'] = df['message'].str.contains(r'0x[0-9a-fA-F]+', regex=True)
        df['has_memory_value'] = df['message'].str.contains(r'\d+\s*[kKmMgG][bB]', regex=True)
        df['has_process_id'] = df['message'].str.contains(r'pid|process', regex=True)
        
        return df
    
    # Apply feature extraction
    kernel_logs = extract_features(kernel_logs)
    
    
    
    # Step 8: Save processed data to CSV files
    if not kernel_logs.empty:
        # Save to CSV (convert timestamp to string for CSV storage)
        kernel_logs_for_csv = kernel_logs.copy()
        if 'timestamp' in kernel_logs_for_csv.columns:
            kernel_logs_for_csv['timestamp'] = kernel_logs_for_csv['timestamp'].astype(str)
        
        return kernel_logs
    return pd.DataFrame(columns=[
    'timestamp', 'hostname', 'service', 'message',
    'is_kernel_related', 'is_failure', 'matched_patterns',
    'severity', 'message_length', 'word_count', 'fault_type',
    'has_hex_address', 'has_memory_value', 'has_process_id'
])
        
    
    
    
    
    
    return {
        'kernel_logs': kernel_logs,
    }

# Example usage