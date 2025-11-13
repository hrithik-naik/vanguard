import hashlib
import json
from datetime import datetime, timedelta

INCIDENTS = {}
RESOLVE_THRESHOLD = 3
MAX_AI_ATTEMPTS = 3
INTERMITTENT_WINDOW_MINUTES = 15

def save_incidents():
    with open("/tmp/incidents.json", "w") as f:
        json.dump(INCIDENTS, f, default=str)

def load_incidents():
    try:
        with open("/tmp/incidents.json", "r") as f:
            data = json.load(f)
            for k, v in data.items():
                if isinstance(v.get("first_seen"), str):
                    v["first_seen"] = datetime.fromisoformat(v["first_seen"])
                if isinstance(v.get("last_seen"), str):
                    v["last_seen"] = datetime.fromisoformat(v["last_seen"])
                INCIDENTS[k] = v
    except FileNotFoundError:
        pass

def msg_hash(msg):
    return hashlib.md5(msg.encode()).hexdigest()

def is_intermittent(incident):
    if incident["recurrence_count"] < 2:
        return False
    
    time_since_last = (datetime.now() - incident["last_seen"]).total_seconds() / 60
    
    if incident["recurrence_count"] >= 2 and time_since_last < INTERMITTENT_WINDOW_MINUTES:
        return True
    
    return False

def process_event_batch(event):
    ts = event["timestamp"]
    msgs = event["message"]
    faults = event["is_fault"]
    types = event["fault_type"]
    pred = event["nextpredicted"]
    
    latest = datetime.fromisoformat(ts[-1]) if isinstance(ts[-1], str) else ts[-1]
    
    faulty_idx = [i for i, f in enumerate(faults) if f]
    
    for inc in INCIDENTS.values():
        if inc["status"] == "verifying":
            inc["verification_streak"] += 1
    
    if not faulty_idx:
        for inc in INCIDENTS.values():
            if inc["active"]:
                if inc["status"] == "verifying":
                    inc["verification_streak"] += 1
                    
                    if inc["verification_streak"] >= RESOLVE_THRESHOLD:
                        inc["status"] = "fixed"
                        inc["active"] = False
                        inc["fixed_at"] = latest
        return
    
    groups = {}
    for i in faulty_idx:
        m = msgs[i]
        ft = types[i]
        h = msg_hash(m)
        if h not in groups:
            groups[h] = {"fault_type": ft, "msg": m, "count": 1}
        else:
            groups[h]["count"] += 1
    
    for h, info in groups.items():
        if h not in INCIDENTS:
            INCIDENTS[h] = {
                "id": h,
                "fault_type": info["fault_type"],
                "message": info["msg"],
                "count": info["count"],
                "first_seen": latest,
                "last_seen": latest,
                "active": True,
                "status": "new",
                "verification_streak": 0,
                "ai_attempts": 0,
                "ai_max_attempts": MAX_AI_ATTEMPTS,
                "recurrence_count": 0,
                "is_intermittent": False,
                "fixed_at": None,
                "ai_action_history": [],
                "pred": pred
            }
            continue
        
        inc = INCIDENTS[h]
        
        inc["is_intermittent"] = is_intermittent(inc)
        
        if inc["status"] == "fixed":
            inc["status"] = "reoccurred"
            inc["active"] = True
            inc["verification_streak"] = 0
            inc["ai_attempts"] = 0
            inc["recurrence_count"] += 1
            inc["is_intermittent"] = is_intermittent(inc)
        
        elif inc["status"] == "verifying":
            inc["status"] = "ongoing"
            inc["verification_streak"] = 0
            inc["is_intermittent"] = is_intermittent(inc)
        
        elif inc["status"] == "failed":
            inc["status"] = "reoccurred"
            inc["active"] = True
            inc["verification_streak"] = 0
            inc["ai_attempts"] = 0
            inc["recurrence_count"] += 1
            inc["is_intermittent"] = is_intermittent(inc)
        
        else:
            if inc["ai_attempts"] > 0:
                inc["status"] = "ongoing"
            else:
                inc["status"] = "new"
        
        inc["count"] += info["count"]
        inc["last_seen"] = latest
        inc["active"] = True
        inc["pred"] = pred
        
        if inc["ai_attempts"] >= inc["ai_max_attempts"]:
            inc["status"] = "failed"
            inc["active"] = True
    
    save_incidents()

def get_incidents_for_ai():
    eligible = [
        inc for inc in INCIDENTS.values()
        if inc["active"]
        and inc["status"] in ["new", "ongoing", "reoccurred"]
        and inc["ai_attempts"] < MAX_AI_ATTEMPTS
    ]
    
    eligible.sort(key=lambda x: (not x["is_intermittent"], -x["count"]))
    
    return eligible

def mark_ai_attempting(incident_id):
    inc = INCIDENTS[incident_id]
    inc["status"] = "ongoing"
    inc["ai_attempts"] += 1
    inc["ai_action_history"].append({
        "attempt": inc["ai_attempts"],
        "started_at": datetime.now().isoformat()
    })

def mark_ai_action_completed(incident_id, action_taken):
    inc = INCIDENTS[incident_id]
    inc["status"] = "verifying"
    inc["verification_streak"] = 0
    
    if inc["ai_action_history"]:
        inc["ai_action_history"][-1]["action"] = action_taken
        inc["ai_action_history"][-1]["completed_at"] = datetime.now().isoformat()
    
    if inc["ai_attempts"] >= MAX_AI_ATTEMPTS:
        inc["status"] = "failed"
        inc["active"] = True

def show_board():
    active = [inc for inc in INCIDENTS.values() if inc["active"]]
    resolved = [inc for inc in INCIDENTS.values() if inc["status"] == "fixed"]
    
    print(f"\n{'='*140}")
    print(f"=== Vanguard Incident Dashboard ===")
    print(f"Active: {len(active)} | Fixed: {len(resolved)} | Total: {len(INCIDENTS)}")
    print(f"{'='*140}")
    print(f"{'ID':<32} {'TYPE':<15} {'STATUS':<12} {'CNT':<5} {'AI':<3} {'INT':<4} {'LAST_SEEN':<19} {'MESSAGE':<45}")
    print(f"{'-'*140}")
    
    all_incidents = sorted(INCIDENTS.values(), key=lambda x: (
        not x["active"],
        not x.get("is_intermittent", False),
        -x["count"]
    ))
    
    for inc in all_incidents:
        intermittent_flag = "⚠️" if inc.get("is_intermittent", False) else "  "
        last_seen_str = inc["last_seen"].strftime('%Y-%m-%d %H:%M:%S') if isinstance(inc["last_seen"], datetime) else str(inc["last_seen"])
        
        print(f"{inc['id']:<32} {inc['fault_type']:<15} {inc['status']:<12} "
              f"{inc['count']:<5} {inc['ai_attempts']:<3} {intermittent_flag:<4} "
              f"{last_seen_str:<19} {inc['message'][:45]:<45}")
    
    print(f"{'='*140}")
    print(f"Legend: INT = Intermittent issue (⚠️)")
    print(f"Status: new -> ongoing -> verifying -> fixed | failed | reoccurred")

def get_metrics():
    active = [inc for inc in INCIDENTS.values() if inc["active"]]
    fixed = [inc for inc in INCIDENTS.values() if inc["status"] == "fixed"]
    intermittent = [inc for inc in active if inc.get("is_intermittent", False)]
    
    ai_attempted = [i for i in INCIDENTS.values() if i["ai_attempts"] > 0]
    ai_success = len(fixed)
    ai_rate = (ai_success / len(ai_attempted) * 100) if ai_attempted else 0
    
    return {
        "total_incidents": len(INCIDENTS),
        "active_incidents": len(active),
        "fixed_incidents": len(fixed),
        "intermittent_issues": len(intermittent),
        "ai_success_rate": round(ai_rate, 2),
        "failed_incidents": len([i for i in active if i["status"] == "failed"])
    }