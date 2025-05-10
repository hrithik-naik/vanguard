#ifndef MONITOR_HPP
#define MONITOR_HPP

#include <string>

std::string runCommand(const std::string& cmd);
std::string getKernalLogs();
std::string setup();
std::string getCPUUsage();
std::string getMemoryUsage();

#endif // MONITOR_HPP
