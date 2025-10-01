import pandas as pd
import numpy as np
import re
from datetime import datetime
import hashlib
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Global compiled patterns for better performance
LOG_PATTERN = re.compile(
    r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)'
)

# Fault classification patterns - precompiled for performance
FAULT_WORDS = {
    'critical': ['panic', 'fatal', 'crash', 'died', 'killed', 'emergency', 'oops'],
    'high': ['error', 'fail', 'failed', 'failure', 'fault', 'timeout', 'denied', 'unable', 'refused', 'exited'],
    'medium': ['warning', 'warn', 'slow', 'retry', 'delayed'],
}

TECH_PATTERNS = [
    re.compile(r'out of memory|oom|segfault', re.IGNORECASE),
    re.compile(r'kernel panic|oops:|call trace', re.IGNORECASE),
    re.compile(r'hardware error|disk.*error', re.IGNORECASE),
    re.compile(r'authentication.*fail|access.*denied', re.IGNORECASE),
    re.compile(r'shutdown failed|shutdown.*failed|failed.*shutdown', re.IGNORECASE),
    re.compile(r'stopping.*failed|failed.*stop|.*:\s*failed\s*$', re.IGNORECASE),
    re.compile(r'service.*failed|daemon.*failed|start.*failed|failed.*start', re.IGNORECASE),
    re.compile(r'exited abnormally|exited abnormally with \[\d+\]|exited with.*code\s+[1-9]\d*', re.IGNORECASE),
    re.compile(r'terminated abnormally|abnormal.*termination|process.*exit.*[1-9]\d*', re.IGNORECASE),
    re.compile(r'\[<[a-fA-F0-9]+>\]|.*\+0x[a-fA-F0-9]+'),
    re.compile(r'do_exit\+|page_fault\+|do_page_fault\+|panic\+|oops_end\+'),
    re.compile(r'handle_mm_fault\+|sysrq_handle_crash\+|error_code\+'),
]

POSITIVE_PATTERNS = [
    re.compile(r'\[\s*OK\s*\]|started successfully|completed successfully', re.IGNORECASE),
    re.compile(r'restart\.|available\.|exited normally|exited.*with.*code\s+0', re.IGNORECASE)
]

# Precompiled normalization patterns
PID_PATTERN = re.compile(r'\[\d+\]')
PROCESS_PATTERN = re.compile(r'process \d+')
PID_EQUALS_PATTERN = re.compile(r'(?i)pid\s*=\s*\d+')
TASK_PATTERN = re.compile(r'task \d+')
IP_PATTERN = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
HEX_PATTERN = re.compile(r'0x[a-fA-F0-9]+')
NUM_PATTERN = re.compile(r'\b\d+\b')

def normalize_service_name(service):
    """Remove PID numbers from service names"""
    return PID_PATTERN.sub('', service).strip()

def normalize_message(message):
    """Normalize message for pattern detection"""
    normalized = message
    normalized = PID_PATTERN.sub('[PID]', normalized)
    normalized = PROCESS_PATTERN.sub('process <PID>', normalized)
    normalized = PID_EQUALS_PATTERN.sub('pid=<PID>', normalized)
    normalized = TASK_PATTERN.sub('task <PID>', normalized)
    normalized = IP_PATTERN.sub('<IP>', normalized)
    normalized = HEX_PATTERN.sub('<HEX>', normalized)
    normalized = NUM_PATTERN.sub('<NUM>', normalized)
    return normalized

def analyze_fault_probability(message):
    """Fast fault probability analysis"""
    msg_lower = message.lower()
    
    # Quick positive pattern check
    for pattern in POSITIVE_PATTERNS:
        if pattern.search(message):
            return 0.05
    
    # High-priority explicit checks
    if re.search(r'\[<[a-fA-F0-9]+>\]', message):
        return 0.95
    if re.search(r'exited abnormally', msg_lower):
        return 0.9
    if 'shutdown failed' in msg_lower:
        return 0.95
    if msg_lower.strip().endswith('failed'):
        return 0.9
    
    # Fault word scoring
    fault_score = 0
    for severity, words in FAULT_WORDS.items():
        weight = {'critical': 1.0, 'high': 0.8, 'medium': 0.5}[severity]
        for word in words:
            if re.search(rf'\b{word}\b', msg_lower):
                fault_score += weight
    
    # Technical pattern matching
    for pattern in TECH_PATTERNS:
        if pattern.search(message):
            fault_score += 0.8
    
    return min(1.0, fault_score / 1.5)

def classify_fault_type(message, is_fault):
    """Determine specific fault type"""
    if not is_fault:
        return 'normal'
    
    msg_lower = message.lower()
    
    if re.search(r'exited abnormally|terminated abnormally|abnormal.*termination', msg_lower):
        return 'process_fault'
    elif re.search(r'\[<[a-fA-F0-9]+>\]|.*\+0x[a-fA-F0-9]+', message):
        return 'kernel_fault'
    elif any(word in msg_lower for word in ['memory', 'oom', 'vm:', 'out of memory', 'mm_fault', 'segfault']):
        return 'memory_fault'
    elif any(word in msg_lower for word in ['panic', 'crash', 'kernel', 'oops', 'do_exit', 'page_fault']):
        return 'kernel_fault'
    elif any(word in msg_lower for word in ['auth', 'login', 'failure', 'denied', 'unauthorized']):
        return 'security_fault'
    elif any(word in msg_lower for word in ['shutdown', 'stop', 'service', 'daemon']):
        return 'service_fault'
    elif any(word in msg_lower for word in ['hardware', 'disk', 'thermal', 'machine check']):
        return 'hardware_fault'
    else:
        return 'general_fault'

def parse_log_entry(log_line, current_year=2025):
    """Parse single log entry"""
    log_line = log_line.strip()
    if not log_line:
        return None
    
    match = LOG_PATTERN.match(log_line)
    
    if not match:
        return {
            'timestamp': None,
            'service': 'unknown',
            'message': log_line
        }
    
    timestamp_str, hostname, service, message = match.groups()
    
    try:
        timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
    except ValueError:
        timestamp = None
    
    return {
        'timestamp': timestamp,
        'service': normalize_service_name(service.strip()),
        'message': message.strip()
    }

def hash_based_clustering(normalized_messages):
    """Ultra-fast hash-based clustering for small batches"""
    if len(normalized_messages) < 2:
        return [0] * len(normalized_messages)
    
    clusters = defaultdict(list)
    
    for i, msg in enumerate(normalized_messages):
        # Extract key terms for similarity grouping
        msg_lower = msg.lower()
        words = msg_lower.split()
        
        # Create signature from:
        # 1. First 3 significant words (skip common words)
        # 2. Service/process related terms
        # 3. Error patterns
        
        skip_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        significant_words = [w for w in words[:5] if w not in skip_words and len(w) > 2]
        
        # Build signature components
        signature_parts = []
        
        # Add first few significant words
        if significant_words:
            signature_parts.extend(significant_words[:3])
        
        # Add error/fault indicators
        error_indicators = []
        for word in ['error', 'fail', 'panic', 'crash', 'fault', 'warning', 'denied', 'timeout']:
            if word in msg_lower:
                error_indicators.append(word)
        signature_parts.extend(error_indicators[:2])
        
        # Add service patterns (kernel, ssh, http, etc.)
        service_patterns = []
        for word in words:
            if any(pattern in word for pattern in ['kernel', 'ssh', 'http', 'mysql', 'nginx', 'apache']):
                service_patterns.append(word)
        signature_parts.extend(service_patterns[:1])
        
        # Create hash from signature
        if signature_parts:
            signature = ' '.join(sorted(signature_parts))
            hash_key = hashlib.md5(signature.encode()).hexdigest()[:8]
        else:
            # Fallback: use first few characters
            hash_key = hashlib.md5(msg_lower[:20].encode()).hexdigest()[:8]
        
        clusters[hash_key].append(i)
    
    # Assign cluster IDs
    cluster_mapping = {}
    cluster_id = 0
    
    # Sort clusters by size (largest first) for consistent numbering
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
    
    for hash_key, indices in sorted_clusters:
        for idx in indices:
            cluster_mapping[idx] = cluster_id
        cluster_id += 1
    
    return [cluster_mapping.get(i, 0) for i in range(len(normalized_messages))]

def process_realtime_logs(realtime_logs, current_year=2025):
    """
    Process batch of real-time logs and return results as DataFrame
    Input: List of log strings
    Output: DataFrame with classification results
    """
    if not realtime_logs:
        return pd.DataFrame()
    
    # Parse all logs
    parsed_logs = []
    for log_line in realtime_logs:
        parsed_entry = parse_log_entry(log_line, current_year)
        if parsed_entry:
            parsed_logs.append(parsed_entry)
    
    if not parsed_logs:
        return pd.DataFrame()
    
    # Get normalized messages for clustering
    messages = [log['message'] for log in parsed_logs]
    normalized_messages = [normalize_message(msg) for msg in messages]
    
    # Use ultra-fast hash-based clustering
    cluster_ids = hash_based_clustering(normalized_messages)
    
    # Process each log
    results = []
    for i, parsed_log in enumerate(parsed_logs):
        fault_prob = analyze_fault_probability(parsed_log['message'])
        is_fault = fault_prob > 0.5
        fault_type = classify_fault_type(parsed_log['message'], is_fault)
        normalized_msg = normalize_message(parsed_log['message'])
        # Mark audit logs so they are not treated as kernel
# After fault probability check
        service_lc = (parsed_log['service'] or '').lower()
        message_lc = (parsed_log['message'] or '').lstrip().lower()
        if service_lc.startswith('audit') or message_lc.startswith('audit:'):
            is_fault = False
            fault_type="normal"# force audit logs to be treated as non-fault
 # per your requirement (keep the spelling as requested)

        
        result = {
            'timestamp': parsed_log['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if parsed_log['timestamp'] else 'Unknown',
            'service': parsed_log['service'],
            'message': parsed_log['message'],
            'normalized_message': normalized_msg,
            'is_fault': is_fault,
            'fault_type': fault_type,
            'cluster_id': cluster_ids[i] if i < len(cluster_ids) else 0
        }
        results.append(result)
    
    # Return as DataFrame
    return pd.DataFrame(results)

# Example usage
