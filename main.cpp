#include "includes/monitor.hpp"
#include <iostream>
#include <thread>
#include <chrono>
#include <cstdio>

int main() {
    std::cout << "Starting Linux Kernel Monitor...\n";

    std::string run = setup();
    std::cout << run;

    FILE* pipe = popen(".venv/bin/python ../preprocessing/logparser.py", "w");
   
    if (!pipe) {
        std::cerr << "Failed to open pipe to Python script.\n";
        return 1;
    }

    std::string lastLogs;
    auto lastLogChange = std::chrono::steady_clock::now();
    int duration;

    while (true) {
        std::string currentLogs = getKernalLogs();
        

        if (currentLogs != lastLogs) {
            duration = 0;
            lastLogChange = std::chrono::steady_clock::now();

            fwrite(currentLogs.c_str(), 1, currentLogs.size(), pipe);
            fflush(pipe);
            lastLogs = currentLogs;
        }

        auto now = std::chrono::steady_clock::now();
        duration = std::chrono::duration_cast<std::chrono::seconds>(now - lastLogChange).count();
        std::cout << "Seconds since last log change: " << duration << std::endl;

        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    pclose(pipe);
    return 0;
}
