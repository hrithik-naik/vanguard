import hashlib
import json
import fcntl
import os
from datetime import datetime, timedelta

INCIDENTS_PATH = os.path.join(os.getcwd(), "data", "incidents.json")
RESOLVE_THRESHOLD = 3
MAX_AI_ATTEMPTS = 3
INTERMITTENT_WINDOW_MINUTES = 15

def _lock_file(f):
    """Acquire an exclusive lock on the file"""
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)

def _unlock_file(f):
    """Release the lock on the file"""
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def save_incidents(incidents):
    """Save incidents to file with file locking"""
    # Ensure /tmp directory is writable
    os.makedirs(os.path.dirname(INCIDENTS_PATH), exist_ok=True)
    
    # Try to create file with proper permissions if it doesn't exist
    if not os.path.exists(INCIDENTS_PATH):
        try:
            with open(INCIDENTS_PATH, 'w') as f:
                json.dump({}, f)
            # Make file writable by everyone (for multi-user scenarios)
            os.chmod(INCIDENTS_PATH, 0o666)
        except PermissionError:
            print(f"⚠️  Cannot create {INCIDENTS_PATH} - permission denied")
            print(f"   Run: sudo chown $USER:$USER {INCIDENTS_PATH}")
            raise
    
    try:
        with open(INCIDENTS_PATH, 'w') as f:
            _lock_file(f)
            try:
                json.dump(incidents, f, default=str, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                _unlock_file(f)
    except PermissionError as e:
        print(f"⚠️  Permission denied writing to {INCIDENTS_PATH}")
        print(f"   Fix with: sudo chown $USER:$USER {INCIDENTS_PATH} && chmod 666 {INCIDENTS_PATH}")
        raise
    except Exception as e:
        print(f"⚠️  Error saving incidents: {e}")
        raise

def load_incidents():
    """Load incidents from file with file locking"""
    if not os.path.exists(INCIDENTS_PATH):
        return {}
    
    try:
        with open(INCIDENTS_PATH, 'r') as f:
            _lock_file(f)
            try:
                data = json.load(f)
                # Convert ISO timestamp strings back to datetime objects
                for k, v in data.items():
                    if isinstance(v.get("first_seen"), str):
                        try:
                            v["first_seen"] = datetime.fromisoformat(v["first_seen"])
                        except:
                            v["first_seen"] = datetime.now()
                    if isinstance(v.get("last_seen"), str):
                        try:
                            v["last_seen"] = datetime.fromisoformat(v["last_seen"])
                        except:
                            v["last_seen"] = datetime.now()
                return data
            finally:
                _unlock_file(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception as e:
        print(f"⚠️  Error loading incidents: {e}")
        return {}

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
    """Process event batch and update incidents (called by log processor)"""
    # Load current state
    INCIDENTS = load_incidents()
    
    ts = event["timestamp"]
    msgs = event["message"]
    faults = event["is_fault"]
    types = event["fault_type"]
    pred = event["nextpredicted"]
    
    latest = datetime.fromisoformat(ts[-1]) if isinstance(ts[-1], str) else ts[-1]
    
    faulty_idx = [i for i, f in enumerate(faults) if f]
    
    # Update verification streaks
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
        save_incidents(INCIDENTS)
        return
    
    # Group faults by message hash
    groups = {}
    for i in faulty_idx:
        m = msgs[i]
        ft = types[i]
        h = msg_hash(m)
        if h not in groups:
            groups[h] = {"fault_type": ft, "msg": m, "count": 1}
        else:
            groups[h]["count"] += 1
    
    # Update or create incidents
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
    
    save_incidents(INCIDENTS)

def get_incidents_for_ai():
    """Get incidents eligible for AI processing"""
    INCIDENTS = load_incidents()
    
    eligible = [
        inc for inc in INCIDENTS.values()
        if inc["active"]
        and inc["status"] in ["new", "ongoing", "reoccurred", "verifying"]  # Include verifying!
        and inc["ai_attempts"] < MAX_AI_ATTEMPTS
    ]
    
    # Sort: prioritize non-verifying, then intermittent, then by count
    eligible.sort(key=lambda x: (
        x["status"] == "verifying",  # Process new/ongoing first
        not x.get("is_intermittent", False),
        -x.get("count", 0)
    ))
    
    return eligible

def mark_ai_attempting(incident_id):
    """Mark incident as being processed by AI"""
    INCIDENTS = load_incidents()
    
    if incident_id not in INCIDENTS:
        print(f"⚠️  Incident {incident_id} not found")
        return False
    
    inc = INCIDENTS[incident_id]
    inc["status"] = "ongoing"
    inc["ai_attempts"] += 1
    inc["ai_action_history"].append({
        "attempt": inc["ai_attempts"],
        "started_at": datetime.now().isoformat()
    })
    
    save_incidents(INCIDENTS)
    return True

def mark_ai_action_completed(incident_id, action_taken):
    """Mark AI action as completed and set to verifying"""
    INCIDENTS = load_incidents()
    
    if incident_id not in INCIDENTS:
        print(f"⚠️  Incident {incident_id} not found")
        return False
    
    inc = INCIDENTS[incident_id]
    inc["status"] = "verifying"
    inc["verification_streak"] = 0
    
    if inc["ai_action_history"]:
        inc["ai_action_history"][-1]["action"] = action_taken
        inc["ai_action_history"][-1]["completed_at"] = datetime.now().isoformat()
    
    if inc["ai_attempts"] >= MAX_AI_ATTEMPTS:
        inc["status"] = "failed"
        inc["active"] = True
    
    save_incidents(INCIDENTS)
    return True

def show_board():
    """Display incident dashboard"""
    INCIDENTS = load_incidents()
    
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
    """Get incident metrics"""
    INCIDENTS = load_incidents()
    
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

# Backward compatibility for scripts that use the old API
INCIDENTS = {}

def save_incidents_old():
    """Legacy function - use save_incidents(INCIDENTS) instead"""
    save_incidents(INCIDENTS)

def load_incidents_old():
    """Legacy function - use INCIDENTS = load_incidents() instead"""
    global INCIDENTS
    INCIDENTS = load_incidents()

def reset_incidents(backup=True):
    """Reset incident board to empty state"""
    if backup and os.path.exists(INCIDENTS_PATH):
        # Create backup
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = INCIDENTS_PATH.replace(".json", f"_backup_{timestamp}.json")
        
        try:
            import shutil
            shutil.copy2(INCIDENTS_PATH, backup_path)
            print(f"✓ Backed up to: {backup_path}")
        except Exception as e:
            print(f"⚠️  Could not create backup: {e}")
    
    # Create fresh empty incidents file
    try:
        save_incidents({})
        print(f"✓ Reset {INCIDENTS_PATH}")
        return True
    except Exception as e:
        print(f"✗ Failed to reset: {e}")
        return False

def clear_fixed_incidents():
    """Remove only fixed/resolved incidents, keep active ones"""
    INCIDENTS = load_incidents()
    
    active_incidents = {
        k: v for k, v in INCIDENTS.items() 
        if v.get("active", False) or v.get("status") != "fixed"
    }
    
    removed = len(INCIDENTS) - len(active_incidents)
    save_incidents(active_incidents)
    
    print(f"✓ Removed {removed} fixed incidents")
    print(f"✓ Kept {len(active_incidents)} active incidents")
    return removed