import sys
import time
from convertver1 import preprocess_linux_logs
import threading
import pandas as pd
from inference import svm
#echo "Simulating a log change at $(date)" | sudo tee -a /var/log/
log_list = []


for line in sys.stdin:
    line = line.strip()
    if line:
        log_list.append(line)
        if len(log_list) %10==0:
            start_time = time.perf_counter()

            result = preprocess_linux_logs(log_path=log_list, start_year=2024)
            t1 = threading.Thread(target=svm, args=(result,))
            t1.start()
            t1.join()
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000  

            
            print(f"Processing time: {elapsed_ms:.2f} ms ")

            log_list.clear()

        
