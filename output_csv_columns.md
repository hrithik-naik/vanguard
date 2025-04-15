linux_kernel_logs.csv columns
---------------------------------------------------------------------------------------------------------------
Column Name         | Description
---------------------------------------------------------------------------------------------------------------
timestamp           | Parsed datetime (with year inferred), e.g., 2024-06-15 04:06:20
hostname            | Hostname of the machine that generated the log entry
service             | The service or process name (e.g., kernel, systemd) that generated the log
message             | The full log message text
is_kernel_related   | Boolean (True/False): Is the log related to the kernel or drivers?
is_failure          | Boolean (True/False): Does the log match a known kernel/driver failure pattern?
matched_patterns    | Pipe-separated list of patterns that matched this log entry
severity            | Numeric severity level (0=Unknown, 1=Info, 2=Warning, 3=Error, 4=Critical)
message_length      | Number of characters in the log message
word_count          | Number of words in the log message
fault_type          | Categorized type of fault (e.g., kernel_panic, memory, driver, storage, etc.)
has_hex_address     | Boolean: Does the message contain a hexadecimal address (e.g., 0x7fff...)?
has_memory_value    | Boolean: Does the message mention a memory size (e.g., 512MB, 4GB)?
has_process_id      | Boolean: Does the message mention a process ID or the word "process"?
---------------------------------------------------------------------------------------------------------------

linux_time_series.csv columns
--------------------------------------------------------------------------------------------------------------------------
Column Name         | Description
--------------------------------------------------------------------------------------------------------------------------
timestamp           | Start time of the time window (e.g., 2024-06-15 04:00:00)
is_kernel_related   | Count of kernel/driver-related log events in this window
is_failure          | Count of log events in this window that matched a failure pattern
severity            | Maximum severity level of any log in this window
message_length      | Mean (rounded) message length (in characters) for logs in this window
word_count          | Mean (rounded) word count for logs in this window
has_hex_address     | Count of logs in this window containing a hexadecimal address
has_memory_value    | Count of logs mentioning memory sizes in this window
has_process_id      | Count of logs mentioning process IDs or "process" in this window
fault_other         | Count of logs classified as "other" fault type in this window
fault_cpu           | Count of logs classified as "cpu" fault type in this window
fault_security      | Count of logs classified as "security" fault type in this window
fault_storage       | Count of logs classified as "storage" fault type in this window
fault_network       | Count of logs classified as "network" fault type in this window
fault_memory        | Count of logs classified as "memory" fault type in this window
fault_kernel_bug    | Count of logs classified as "kernel_bug" fault type in this window
--------------------------------------------------------------------------------------------------------------------------
