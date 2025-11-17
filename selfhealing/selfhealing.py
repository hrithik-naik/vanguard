import os
import socket
import asyncio
import json
from incidentmanager import process_event_batch,show_board,get_incidents_for_ai
import time

SOCKET_PATH = "/home/ubu/vanguard.sock"


if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

print(f"[Healer] Binding socket at: {os.path.abspath(SOCKET_PATH)}")

async def handle_event(data):
    
    try:
        start_time = time.perf_counter()
        event = json.loads(data.decode())
        process_event_batch(event)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print(f"Total time (Incident Board): {elapsed_ms:.2f} ms")
        # print(get_incidents_for_ai())
        
        faults = set(event.get("fault_type", []))
        # print(f"[Healer] Received event with faults={event}\n")
        # show_board()
    except Exception as e:
        print("[Healer] Bad event:", e)

async def healer_loop():
    
    loop = asyncio.get_event_loop()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.bind(SOCKET_PATH)
    sock.setblocking(False)

    print(f"[Healer] Listening on {SOCKET_PATH}")

    while True:
        data, _ = await loop.sock_recvfrom(sock, 8192)
        asyncio.create_task(handle_event(data))

if __name__ == "__main__":
    asyncio.run(healer_loop())
