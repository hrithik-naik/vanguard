cmake_minimum_required(VERSION 3.5)

project("vanguard")
include_directories(includes)

add_executable("vanguard" 
main.cpp
src/monitor.cpp
)
