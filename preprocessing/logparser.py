import sys
import time
import threading
import pandas as pd
from convertver1 import preprocess_linux_logs
from inference import svm, predict_batch
from preprocessortedbeta import process_realtime_logs
from concurrent.futures import ThreadPoolExecutor
import tensorflow as tf
from inferencelstm import run_inference

log_list = []
executor = ThreadPoolExecutor(max_workers=4)  # Tune based on your CPU

def process_logs(logs):
    start_time = time.perf_counter()

    processed = process_realtime_logs(logs)

    print(processed)
    print(type(processed))
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    print(f"Total time (preprocess + inference): {elapsed_ms:.2f} ms")

    if processed is None or processed.empty:
        return

    # Submit inference job and wait for result
    future_lstm = executor.submit(
        run_inference,
        processed["normalized_message"].astype(str).tolist()
    )
    #result = future_lstm.result()   # blocks until inference done

    

  


    

for line in sys.stdin:
    line = line.strip()
    if line:
        log_list.append(line)
        if len(log_list) % 10 == 0:
            logs_to_process = log_list[:]
            log_list.clear()

            
            executor.submit(process_logs, logs_to_process)
