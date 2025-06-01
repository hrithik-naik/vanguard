#ifndef SYSCALL_MAPPER_HPP
#define SYSCALL_MAPPER_HPP

#include <string>
#include <vector>
#include <unordered_map>

std::pair<std::string, int> get_top_process();
std::vector<std::string> trace_process(int pid);
std::vector<std::string> extract_syscalls(const std::vector<std::string>& trace_lines);
std::unordered_map<std::string, std::string> load_syscall_table(const std::string& path);
std::string format_syscall_sequence(const std::vector<std::string>& syscalls,
                                    const std::unordered_map<std::string, std::string>& tbl_map);

#endif // SYSCALL_MAPPER_HPP
