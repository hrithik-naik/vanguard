#include "../includes/syscall_mapper.hpp"
#include <iostream>
#include <sstream>
#include <fstream>
#include <unordered_map>
#include <set>
#include <cstdio>
#include <cstdlib>
#include <sys/stat.h>
#include <cstring>

std::pair<std::string, int> get_top_process() {
    FILE* pipe = popen("ps -eo pid,comm,%cpu --sort=-%cpu | awk 'NR==2 {print $1, $2}'", "r");
    if (!pipe) return {"", -1};

    char buffer[128];
    std::string result;
    if (fgets(buffer, sizeof(buffer), pipe)) {
        result = buffer;
    }
    pclose(pipe);

    std::istringstream iss(result);
    int pid;
    std::string name;
    iss >> pid >> name;

    return {name, pid};
}
std::vector<std::string> trace_process(int pid) {
    std::vector<std::string> syscalls;
    std::string cmd = "sudo strace -e trace=all -f -s 0 -p " + std::to_string(pid);
    // Remove printing the command here
    // std::cout << cmd;

    FILE* pipe = popen(cmd.c_str(), "r");
    if (!pipe) return syscalls;

    char buffer[4096];
    while (fgets(buffer, sizeof(buffer), pipe)) {
        std::istringstream iss(buffer);
        std::string pid_or_name, syscall_part;
        if (!(iss >> pid_or_name >> syscall_part)) continue;

        auto idx = syscall_part.find('(');
        if (idx != std::string::npos) {
            syscall_part = syscall_part.substr(0, idx);
            syscalls.push_back(syscall_part);
        }
    }

    pclose(pipe);
    return syscalls;
}


std::vector<std::string> extract_syscalls(const std::vector<std::string>& trace_lines) {
    std::vector<std::string> syscalls;
    for (const auto& line : trace_lines) {
        std::istringstream iss(line);
        std::string pid_or_name, syscall_part;
        if (!(iss >> pid_or_name >> syscall_part)) continue;

        auto idx = syscall_part.find('(');
        if (idx != std::string::npos) {
            syscall_part = syscall_part.substr(0, idx);
            syscalls.push_back(syscall_part);
        }
    }
    return syscalls;
}

std::unordered_map<std::string, std::string> load_syscall_table(const std::string& path) {
    std::unordered_map<std::string, std::string> map;

    // Check if the file exists
    struct stat buffer;
    if (stat(path.c_str(), &buffer) != 0) {
        std::cerr << "[ERROR] Syscall table file does not exist: " << path << std::endl;
        return map;
    }

    std::ifstream infile(path);
    if (!infile) {
        std::cerr << "[ERROR] Failed to open syscall table file: " << path << std::endl;
        return map;
    }

    std::string line;
    while (std::getline(infile, line)) {
        std::istringstream iss(line);
        std::string id, arch, abi, name;
        if (!(iss >> id >> arch >> abi >> name)) continue;
        if (name.find("sys_") == 0) name = name.substr(4);
        map[name] = id;
    }

    return map;
}

std::string format_syscall_sequence(const std::vector<std::string>& syscalls,
                                    const std::unordered_map<std::string, std::string>& tbl_map) {
    std::ostringstream oss;
    for (size_t i = 0; i < syscalls.size(); ++i) {
        oss << syscalls[i];
        if (i != syscalls.size() - 1)
            oss << "|";
    }
    return oss.str();
}
