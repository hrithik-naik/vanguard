#include "includes/monitor.hpp"
#include <iostream>
#include <thread>
#include <chrono>
#include <cstdio>
#include <atomic>

std::atomic<bool> keep_running(true);
void monitor_kernel_logs() {
    FILE* pipe = popen(".venv/bin/python ../preprocessing/logparser.py", "w");
    if (!pipe) {
        std::cerr << "Failed to open pipe to Python script.\n";
        return;
    }

    std::string lastLogs;

    while (keep_running) {
        std::string currentLogs = getKernalLogs();  

        if (currentLogs != lastLogs) {
            fwrite(currentLogs.c_str(), 1, currentLogs.size(), pipe);
            fflush(pipe);
            lastLogs = currentLogs;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(100)); 
    }

    pclose(pipe);
}


void monitor_syscalls() {
    while (keep_running) {
        return ;
    }
}

int main() {
    std::cout << "Starting Linux Kernel Monitor...\n";
    std::string run = setup();
    std::cout << run;

    std::thread log_thread(monitor_kernel_logs);
    //std::thread syscall_thread(monitor_syscalls);

    std::cout << "Press ENTER to stop...\n";
    std::cin.get();

    keep_running = false;

    log_thread.join();
    //syscall_thread.join();

    std::cout << "Monitoring stopped.\n";
    return 0;
}
