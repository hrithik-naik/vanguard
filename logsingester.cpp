#include <iostream>
#include <fstream>
#include <sstream>
#include <thread>
#include <chrono>
#include <cstdio>
#include <array>
using namespace std;

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

std::string getDmesgLogs() {
    return runCommand("journalctl -k -n 10");
}
string setup(){
   string c=runCommand("bash ../setup.sh");
   return c;
}

std::string getCPUUsage() {
    std::ifstream file("/proc/stat");
    std::string line;
    getline(file, line); // Read the first line
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

int main() {
    std::cout << "Starting Linux Kernel Monitor...\n";
    string run=setup();
    cout<<run;

    FILE* pipe = popen(".venv/bin/python ../logparser.py", "w");
    if (!pipe) {
        std::cerr << "Failed to open pipe to Python script.\n";
        return 1;
    }
    std::string logs;
    string lastLogs;
    auto lastLogChange = std::chrono::steady_clock::now();
    int duration;
    while (true) {
        logs += getDmesgLogs();
        cout<<"got logs";
        
        

        std::string currentLogs = getDmesgLogs();
        if (currentLogs != lastLogs) {
        duration=0;
        lastLogChange = std::chrono::steady_clock::now();
        // Only send if logs are different
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
