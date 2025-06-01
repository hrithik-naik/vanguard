import sys
import time
import threading
import pandas as pd
from convertver1 import preprocess_linux_logs
from inference import svm, predict_batch
from concurrent.futures import ThreadPoolExecutor

log_list = []
executor = ThreadPoolExecutor(max_workers=4)  # Tune based on your CPU

def process_logs(logs):
    start_time = time.perf_counter()

    processed = preprocess_linux_logs(log_path=logs, start_year=2024)
    if processed is None or processed.empty:
        return

    df1 = processed.copy()
    df2 = processed.copy()

    # Submit both jobs to thread pool
    future_svm = executor.submit(svm, df1)
    future_pred = executor.submit(predict_batch, df2)

    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000
    print(f"Processing time: {elapsed_ms:.2f} ms")

for line in sys.stdin:
    line = line.strip()
    if line:
        log_list.append(line)
        if len(log_list) % 10 == 0:
            logs_to_process = log_list[:]
            log_list.clear()

            
            executor.submit(process_logs, logs_to_process)
