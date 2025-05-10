import sys
from preprocessing.convertver1 import preprocess_linux_logs
import pandas as pd


#echo "Simulating a log change at $(date)" | sudo tee -a /var/log/kern.log
list=[]
for line in sys.stdin:
    line = line.strip()
    if line:
        list.append(line)
        if(len(list)==10):
            a=preprocess_linux_logs(log_path=list,start_year=2024)
            print(a)
            list.clear()
            
        
