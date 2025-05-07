import sys


#echo "Simulating a log change at $(date)" | sudo tee -a /var/log/kern.log

for line in sys.stdin:
    line = line.strip()
    if line:
        print(f"Processed: {line}")  # This is where you'd do your actual preprocessing
