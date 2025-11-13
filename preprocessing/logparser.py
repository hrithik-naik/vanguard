import sys
import os
import time
import threading
import pandas as pd
import sys, os, time, json, socket
import asyncio
from preprocessortedbeta import process_realtime_logs
from concurrent.futures import ThreadPoolExecutor
import tensorflow as tf
from inferencelstm import run_inference

SOCKET_PATH = "/home/ubu/vanguard.sock"
log_list = []
executor = ThreadPoolExecutor(max_workers=4)

async def send_event(event: dict):
   
    if not os.path.exists(SOCKET_PATH):
        print("[Warn] Healer socket missing — skipping send.")
        return
    try:
        data = json.dumps(event).encode("utf-8")
        print(f"[Sender] Sending to socket path: {os.path.abspath(SOCKET_PATH)}")
        
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.setblocking(False)
        
        loop = asyncio.get_running_loop()
        await loop.sock_sendto(sock, data, SOCKET_PATH)
        sock.close()
        
        print("[Sender] Event sent successfully")
        
    except Exception as e:
        print("[Error] Failed to send event:", e)

def process_logs(logs):
    start_time = time.perf_counter()
    processed = process_realtime_logs(logs)
    print(processed)
    print(type(processed))
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    print(f"Total time (preprocess + inference): {elapsed_ms:.2f} ms")
    
    FILE = "processed_logs.tsv"
    write_header = not os.path.exists(FILE)
    with open(FILE, "a", encoding="utf-8") as f:
        processed[["timestamp","is_fault","fault_type","cluster_id"]].to_csv(f, index=False, sep="\t", header=write_header)
    
    if processed is None or processed.empty:
        return
    
    future_lstm = executor.submit(
        run_inference,
        processed["normalized_message"].astype(str).tolist()
    )
    result = future_lstm.result()
    
    if processed["is_fault"].any():
        event = {
            "timestamp": processed["timestamp"].astype(str).tolist(),
            "message": processed["message"].astype(str).tolist(),
            "is_fault": processed["is_fault"].astype(bool).tolist(),
            "fault_type": processed["fault_type"].astype(str).tolist(),
            "nextpredicted": result,
        }
        
        
        
        asyncio.run(send_event(event))
        print("[Debug] Send event completed")
    else:
        print("[Skip] No faults in this batch.")

for line in sys.stdin:
    line = line.strip()
    if line:
        log_list.append(line)
        if len(log_list) % 10 == 0:
            logs_to_process = log_list[:]
            log_list.clear()
            executor.submit(process_logs, logs_to_process)