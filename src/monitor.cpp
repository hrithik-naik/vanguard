#include "../includes/monitor.hpp"
#include <fstream>
#include <sstream>
#include <array>
#include <cstdio>

std::string runCommand(const std::string& cmd) {
    std::array<char, 128> buffer;
    std::string result;
    FILE* pipe = popen(cmd.c_str(), "r");
    if (!pipe) return "Error executing command.";
    while (fgets(buffer.data(), buffer.size(), pipe)) {
        result += buffer.data();
    }
    pclose(pipe);
    return result;
}

std::string getKernalLogs() {
    return runCommand("journalctl -k -n 10");
}

std::string setup() {
    return runCommand("bash ../setup.sh");
}

std::string getCPUUsage() {
    std::ifstream file("/proc/stat");
    std::string line;
    getline(file, line);
    return "CPU Stats: " + line;
}

std::string getMemoryUsage() {
    std::ifstream file("/proc/meminfo");
    std::stringstream buffer;
    std::string line;
    int count = 0;
    while (getline(file, line) && count++ < 5) {
        buffer << line << "\n";
    }
    return buffer.str();
}
