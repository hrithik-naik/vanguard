import sys, os, time, json, socket, pandas as pd
from concurrent.futures import ThreadPoolExecutor
from preprocessortedbeta import process_realtime_logs
from inferencelstm import run_inference

SOCKET_PATH = "/tmp/vanguard.sock"
executor = ThreadPoolExecutor(max_workers=4)
log_list = []

def send_event(event):
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(event).encode("utf-8"), SOCKET_PATH)
        sock.close()
    except Exception as e:
        print(f"[Warn] send_event failed: {e}")

def process_logs(logs):
    t0 = time.perf_counter()
    df = process_realtime_logs(logs)
    if df is None or df.empty:
        return

    df[["timestamp","is_fault","fault_type","cluster_id"]].to_csv(
        "processed_logs.tsv", sep="\t", index=False, mode="a", header=not os.path.exists("processed_logs.tsv")
    )

    pred = run_inference(df["normalized_message"].astype(str).tolist())
    faults = df[df["is_fault"] == True]
    if faults.empty:
        return

    event = {
        "timestamp": str(df.iloc[-1]["timestamp"]),
        "faults": faults[["timestamp","message","fault_type"]].to_dict(orient="records"),
        "predicted_count": float(pred.get("predicted_count", 0)),
        "k_next": int(pred.get("k_next", 10)),
        "context_m": int(pred.get("context_m", 10))
    }
    executor.submit(send_event, event)
    print(f"[Detector] Sent {len(faults)} faults | pred={event['predicted_count']:.3f} | took {(time.perf_counter()-t0)*1000:.2f} ms")

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    log_list.append(line)
    if len(log_list) % 10 == 0:
        executor.submit(process_logs, log_list[:])
        log_list.clear()
