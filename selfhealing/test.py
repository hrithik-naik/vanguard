#!/usr/bin/env python3
"""
Test script to verify incidentmanager updates work correctly
"""

import sys
import time
from datetime import datetime

# Add your project path if needed
# sys.path.insert(0, '/path/to/your/project')

import incidentmanager

def test_file_operations():
    """Test that file read/write works"""
    print("🧪 Testing file operations...")
    
    # Test load
    incidents = incidentmanager.load_incidents()
    print(f"✓ Loaded {len(incidents)} incidents")
    
    # Test save
    test_incident = {
        "test_id_123": {
            "id": "test_id_123",
            "fault_type": "test_fault",
            "message": "Test incident",
            "count": 1,
            "first_seen": datetime.now(),
            "last_seen": datetime.now(),
            "active": True,
            "status": "new",
            "verification_streak": 0,
            "ai_attempts": 0,
            "ai_max_attempts": 3,
            "recurrence_count": 0,
            "is_intermittent": False,
            "fixed_at": None,
            "ai_action_history": [],
            "pred": None
        }
    }
    
    try:
        incidentmanager.save_incidents(test_incident)
        print("✓ Save successful")
    except Exception as e:
        print(f"✗ Save failed: {e}")
        return False
    
    # Verify it was saved
    incidents = incidentmanager.load_incidents()
    if "test_id_123" in incidents:
        print("✓ Incident persisted correctly")
    else:
        print("✗ Incident not found after save")
        return False
    
    return True

def test_ai_workflow():
    """Test the AI workflow functions"""
    print("\n🧪 Testing AI workflow...")
    
    # Get incidents
    eligible = incidentmanager.get_incidents_for_ai()
    print(f"✓ Found {len(eligible)} eligible incidents")
    
    if eligible:
        incident = eligible[0]
        incident_id = incident['id']
        
        # Test mark_ai_attempting
        print(f"  Testing mark_ai_attempting for {incident_id[:8]}...")
        success = incidentmanager.mark_ai_attempting(incident_id)
        if success:
            print(f"  ✓ Marked as attempting")
        else:
            print(f"  ✗ Failed to mark as attempting")
            return False
        
        # Verify status changed
        incidents = incidentmanager.load_incidents()
        if incidents[incident_id]['status'] == 'ongoing':
            print(f"  ✓ Status changed to 'ongoing'")
        else:
            print(f"  ✗ Status not updated (still {incidents[incident_id]['status']})")
            return False
        
        # Test mark_ai_action_completed
        print(f"  Testing mark_ai_action_completed for {incident_id[:8]}...")
        success = incidentmanager.mark_ai_action_completed(incident_id, "test command")
        if success:
            print(f"  ✓ Marked as completed")
        else:
            print(f"  ✗ Failed to mark as completed")
            return False
        
        # Verify status changed
        incidents = incidentmanager.load_incidents()
        if incidents[incident_id]['status'] == 'verifying':
            print(f"  ✓ Status changed to 'verifying'")
        else:
            print(f"  ✗ Status not updated (still {incidents[incident_id]['status']})")
            return False
    
    return True

def show_current_state():
    """Display current incident board"""
    print("\n📊 Current Incident Board State:")
    incidentmanager.show_board()
    
    print("\n📈 Metrics:")
    metrics = incidentmanager.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    print("="*60)
    print("Testing incidentmanager functionality")
    print("="*60)
    
    # Test 1: File operations
    if not test_file_operations():
        print("\n❌ File operations test FAILED")
        sys.exit(1)
    
    # Test 2: AI workflow
    if not test_ai_workflow():
        print("\n❌ AI workflow test FAILED")
        sys.exit(1)
    
    # Show current state
    show_current_state()
    
    print("\n" + "="*60)
    print("✅ All tests PASSED")
    print("="*60)