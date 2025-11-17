#!/bin/bash

echo "📊 Monitoring Vanguard processes... (Ctrl+C to exit)"
echo

while true; do
    clear
    date +"⏱  %Y-%m-%d %H:%M:%S"
    echo "---------------------------------------------------------"

    ps -eo pid,comm,%cpu,%mem,rss,etime --sort=-%cpu \
        | grep -E "selfhealing|logparser|dashboard|ai_service|vanguard|python" \
        | grep -v grep \
        | awk '{printf "PID: %-6s CPU: %-5s%% MEM: %-5s%% RSS: %-8s Time: %-10s CMD: %s\n", $1, $3, $4, $5"KB", $6, $2}'

    echo "---------------------------------------------------------"

    # Optional sampling mode
    sleep 1
done
