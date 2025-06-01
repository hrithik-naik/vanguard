#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <sys/types.h>
#include <time.h>
#include <fcntl.h>
#include <errno.h>

volatile int keep_running = 1;

void signal_handler(int sig) {
    printf("\nReceived signal %d, stopping log generation...\n", sig);
    keep_running = 0;
}

int write_to_kmsg(const char* message) {
    int fd;
    char full_message[512];
    int ret;
    
    // Open /dev/kmsg (kernel message buffer)
    fd = open("/dev/kmsg", O_WRONLY);
    if (fd == -1) {
        perror("Failed to open /dev/kmsg (try running as root)");
        return -1;
    }
    
    // Format message with priority (kernel warning level)
    snprintf(full_message, sizeof(full_message), "<4>oom_simulator: %s\n", message);
    
    // Write to kernel message buffer
    ret = write(fd, full_message, strlen(full_message));
    close(fd);
    
    return ret;
}

void generate_kernel_failure_logs() {
    pid_t pid = getpid();
    int log_count = 0;
    
    // Realistic kernel failure messages that indicate system crashes/failures
    const char* failure_messages[] = {
        "Out of Memory: Killed process 22608 (httpd).",
        "Out of Memory: Killed process 22747 (httpd).",
        "Out of Memory: Killed process 22759 (httpd).",
        "Out of Memory: Killed process 22613 (httpd).",
        "Out of Memory: Killed process 22766 (httpd).",
        "Out of memory: Kill process simulation - memory exhausted",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=211.46.241.200  user=guest"
    };
    
    int num_messages = sizeof(failure_messages) / sizeof(failure_messages[0]);
    
    printf("Writing kernel failure simulation messages to kernel log...\n");
    printf("These simulate serious kernel failures and memory errors\n");
    printf("Visible in: journalctl -k\n\n");
    
    while (keep_running) {
        const char* message = failure_messages[log_count % num_messages];
        
        // Write to kernel message buffer
        if (write_to_kmsg(message) > 0) {
            printf("[%d] Kernel log: %s\n", log_count + 1, message);
        } else {
            printf("[%d] Failed to write kernel log (need root privileges)\n", log_count + 1);
            printf("    Fallback: %s\n", message);
        }
        
        log_count++;
        sleep(2);
        
        // Add critical system failure indicators
        if (log_count % 5 == 0) {
            char critical_msg[256];
            snprintf(critical_msg, sizeof(critical_msg), 
                    "CRITICAL: System stability compromised - error count: %d", 
                    log_count);
            write_to_kmsg(critical_msg);
            printf("[%d] Critical: %s\n", log_count, critical_msg);
        }
        
        // Simulate hardware error reports
        if (log_count % 7 == 0) {
            char hw_error[256];
            snprintf(hw_error, sizeof(hw_error), 
                    "Hardware error detected: CPU %d, Bank %d, Status 0x%x", 
                    log_count % 4, log_count % 8, 0x8c00 + log_count);
            write_to_kmsg(hw_error);
            printf("[%d] Hardware error: %s\n", log_count, hw_error);
        }
    }
}

int main() {
    printf("Kernel Failure Log Generator\n");
    printf("Process ID: %d\n", getpid());
    printf("NOTE: Requires root privileges to write to /dev/kmsg\n");
    printf("Run as: sudo ./kernel_failure_logs\n");
    printf("Monitor with: journalctl -k -f\n");
    printf("Press Ctrl+C to stop\n\n");
    
    // Check if running as root
    if (geteuid() != 0) {
        printf("WARNING: Not running as root. Logs may not appear in journalctl -k\n");
        printf("For kernel logs, run: sudo ./kernel_failure_logs\n\n");
    }
    
    // Set up signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // Generate the logs
    generate_kernel_failure_logs();
    
    printf("\nKernel failure log generation stopped.\n");
    return 0;
}
