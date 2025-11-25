import json
import time
import os
from datetime import datetime
from typing import TypedDict
from langgraph.graph import StateGraph, END
from llm_provider import LLMProvider
import incidentmanager

class IncidentState(TypedDict):
    incident_id: str
    incident: dict
    analysis: str
    specialist_type: str
    action_plan: dict
    execution_result: str
    verification_passed: bool
    attempts: int
    error: str

class AIIncidentService:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.llm = LLMProvider(self.config)
        self.graph = self._build_graph()
        
        self.INCIDENTS_PATH = self.config['incident_board']['path']
        self.POLL_INTERVAL = self.config['incident_board']['poll_interval']
        self.MAX_ATTEMPTS = self.config['ai']['max_attempts']
        self.LOG_PATH = self.config['logging']['path']
        
        self.last_api_call = 0
        self.min_api_interval = 5
        
        self._ensure_log_file()
        # try:
        #     g = self.graph.get_graph()
        #     with open("workflow.png", "wb") as f:
        #         f.write(g.draw_mermaid_png())
        #     import webbrowser
        #     webbrowser.open("file://" + os.path.abspath("workflow.png"))
        #     print("📌 Workflow graph generated: workflow.png")
        # except Exception as e:
        #     print("⚠️ Graph rendering failed:", e)
        
    def _ensure_log_file(self):
        try:
            if not os.path.exists(self.LOG_PATH):
                with open(self.LOG_PATH, 'w') as f:
                    pass
            print(f"✓ Log file ready: {self.LOG_PATH}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create log file: {e}")
    
    def _rate_limit_api_call(self):
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_api_interval:
            wait_time = self.min_api_interval - time_since_last_call
            print(f"⏳ Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self.last_api_call = time.time()
    
    def _build_graph(self):
        workflow = StateGraph(IncidentState)
        
        workflow.add_node("coordinator", self.coordinator_agent)
        workflow.add_node("memory_specialist", self.memory_specialist)
        workflow.add_node("kernel_specialist", self.kernel_specialist)
        workflow.add_node("hardware_specialist", self.hardware_specialist)
        workflow.add_node("security_specialist", self.security_specialist)
        workflow.add_node("action_planner", self.action_planner)
        workflow.add_node("executor", self.executor)
        workflow.add_node("feedback_analyzer", self.feedback_analyzer)
        workflow.add_node("verifier", self.verifier)
        
        workflow.set_entry_point("coordinator")
        
        workflow.add_conditional_edges(
            "coordinator",
            self.route_to_specialist,
            {
                "memory": "memory_specialist",
                "kernel": "kernel_specialist",
                "hardware": "hardware_specialist",
                "security": "security_specialist",
            }
        )
        
        for specialist in ["memory_specialist", "kernel_specialist", 
                          "hardware_specialist", "security_specialist"]:
            workflow.add_edge(specialist, "action_planner")
        
        workflow.add_edge("action_planner", "executor")
        workflow.add_edge("executor", "feedback_analyzer")
        
        workflow.add_conditional_edges(
            "feedback_analyzer",
            self.decide_after_feedback,
            {
                "success": "verifier",
                "retry": "coordinator",
                "failed": END
            }
        )
        
        workflow.add_conditional_edges(
            "verifier",
            self.should_continue,
            {
                "success": END,
                "retry": "coordinator",
                "failed": END
            }
        )
        
        return workflow.compile()
    
    def coordinator_agent(self, state: IncidentState) -> IncidentState:
        incident = state["incident"]
        self._rate_limit_api_call()
        
        previous_feedback = ""
        if state.get("execution_result"):
            previous_feedback = f"\n\nPrevious Attempt Result:\n{state['execution_result'][:300]}"
        
        prompt = f"""You are a Linux SRE coordinator analyzing an incident.

Incident Details:
- Type: {incident['fault_type']}
- Message: {incident['message']}
- Count: {incident['count']}
- Intermittent: {incident.get('is_intermittent', False)}
- AI Attempts: {state['attempts']}/{self.MAX_ATTEMPTS}{previous_feedback}

Provide brief analysis (2-3 sentences):
1. What is happening
2. Severity
3. Resolution approach{' (considering previous failure)' if previous_feedback else ''}"""

        try:
            response = self.llm.generate(prompt)
            state["analysis"] = response
            self.log_action(incident['id'], "coordinator", {"analysis": response[:200]})
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                state["error"] = "API_RATE_LIMIT"
                print(f"⚠️  API Rate limit hit - will retry later")
            else:
                state["error"] = f"Coordinator failed: {error_msg}"
            
        return state
    
    def route_to_specialist(self, state: IncidentState) -> str:
        if state.get("error"):
            return "memory"
            
        mapping = {
            "memory_fault": "memory",
            "kernel_fault": "kernel",
            "hardware_fault": "hardware",
            "security_fault": "security",
            "general_fault": "kernel"
        }
        specialist = mapping.get(state["incident"]["fault_type"], "kernel")
        state["specialist_type"] = specialist
        return specialist
    
    def memory_specialist(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state
            
        incident = state["incident"]
        self._rate_limit_api_call()
        
        prompt = f"""Memory Specialist Analysis:

Previous: {state['analysis']}
Incident: {incident['message']}
Count: {incident['count']}

Recommend ONE action to fix OOM/memory issues. Be specific about the command."""

        try:
            response = self.llm.generate(prompt)
            state["action_plan"]["specialist_recommendation"] = response
        except Exception as e:
            state["error"] = f"Specialist failed: {str(e)}"
            
        return state
    
    def kernel_specialist(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state
            
        incident = state["incident"]
        self._rate_limit_api_call()
        
        prompt = f"""Kernel Specialist Analysis:

Previous: {state['analysis']}
Incident: {incident['message']}

Recommend ONE action to fix kernel panics/faults. Be specific."""

        try:
            response = self.llm.generate(prompt)
            state["action_plan"]["specialist_recommendation"] = response
        except Exception as e:
            state["error"] = f"Specialist failed: {str(e)}"
            
        return state
    
    def hardware_specialist(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state
            
        incident = state["incident"]
        self._rate_limit_api_call()
        
        prompt = f"""Hardware Specialist Analysis:

Previous: {state['analysis']}
Incident: {incident['message']}

Recommend ONE diagnostic/fix for hardware errors."""

        try:
            response = self.llm.generate(prompt)
            state["action_plan"]["specialist_recommendation"] = response
        except Exception as e:
            state["error"] = f"Specialist failed: {str(e)}"
            
        return state
    
    def security_specialist(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state
            
        incident = state["incident"]
        self._rate_limit_api_call()
        
        prompt = f"""Security Specialist Analysis:

Previous: {state['analysis']}
Incident: {incident['message']}
Count: {incident['count']}

Recommend ONE action to mitigate authentication/security issues."""

        try:
            response = self.llm.generate(prompt)
            state["action_plan"]["specialist_recommendation"] = response
        except Exception as e:
            state["error"] = f"Specialist failed: {str(e)}"
            
        return state
    
    def action_planner(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state
            
        recommendation = state["action_plan"].get("specialist_recommendation", "")
        
        if not recommendation:
            state["error"] = "No specialist recommendation"
            return state
        
        self._rate_limit_api_call()
        
        prompt = f"""Extract from this recommendation:

{recommendation}

Provide ONLY:
EXECUTE: <one bash command>
VERIFY: <one verification command>"""

        try:
            response = self.llm.generate(prompt)
            
            execute_cmd = ""
            verify_cmd = ""
            for line in response.strip().split('\n'):
                if line.startswith("EXECUTE:"):
                    execute_cmd = line.replace("EXECUTE:", "").strip()
                elif line.startswith("VERIFY:"):
                    verify_cmd = line.replace("VERIFY:", "").strip()
            
            state["action_plan"]["execute_command"] = execute_cmd
            state["action_plan"]["verify_command"] = verify_cmd
            
            self.log_action(state["incident_id"], "action_plan", {
                "execute": execute_cmd,
                "verify": verify_cmd
            })
        except Exception as e:
            state["error"] = f"Action planner failed: {str(e)}"
        
        return state
    
    def executor(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state

        execute_cmd = state["action_plan"].get("execute_command", "").strip()

        if not execute_cmd:
            state["execution_result"] = "ERROR: No command"
            state["error"] = "No command generated"
            return state

        SAFE_PREFIXES = [
            "systemctl restart", "systemctl status", "journalctl", "ulimit",
            "kill", "gdb", "valgrind", "echo", "dmesg", "chmod", "chown", "sysctl",
            "ps aux", "top", "free", "df", "du", "ls", "cat", "grep"
        ]

        BLOCK_PATTERNS = [
            "rm -rf", "shutdown", "reboot", "mkfs", "mount", "umount", ":(){:|:&};:",
            "wget http", "curl http", "sudo su", "passwd", "useradd", "deluser",
            "chmod 777 /", "chown -R /", "iptables", "apt remove", "apt purge",
            "dd if=", "mkfs", "truncate /", "mv /", "sed -i '/'", "pkill -9 systemd",
        ]

        def is_safe(cmd: str) -> bool:
            if any(bad in cmd for bad in BLOCK_PATTERNS):
                return False
            return any(cmd.startswith(prefix) for prefix in SAFE_PREFIXES)

        if not is_safe(execute_cmd):
            state["execution_result"] = f"BLOCKED: Unsafe command"
            state["error"] = "Command rejected by safety policy"
            self.log_action(state["incident_id"], "blocked_dangerous", {"command": execute_cmd})
            print(f"🚫 [BLOCKED] {execute_cmd}")
            return state

        self.log_action(state["incident_id"], "executing", {"command": execute_cmd})
        incidentmanager.mark_ai_attempting(state["incident_id"])

        if self.config['execution']['mode'] == "simulation":
            state["execution_result"] = f"SIMULATION_OK: {execute_cmd}"
            print(f"🎮 [SIMULATION] {execute_cmd}")
            return state

        import subprocess
        
        try:
            result = subprocess.run(
                execute_cmd,
                shell=True,
                capture_output=True,
                timeout=20,
                text=True
            )

            output = result.stdout if result.returncode == 0 else result.stderr
            state["execution_result"] = f"EXIT_CODE: {result.returncode}\nOUTPUT: {output[:500]}"

            if result.returncode == 0:
                print(f"✅ [EXECUTED] {execute_cmd}")
                print(f"   Output: {output[:100]}")
            else:
                print(f"❌ [FAILED] {execute_cmd}")
                print(f"   Error: {output[:100]}")

        except subprocess.TimeoutExpired:
            state["execution_result"] = "ERROR: Command timed out after 20s"
            state["error"] = "timeout"
            print("⏱️  [TIMEOUT]")

        except Exception as e:
            state["execution_result"] = f"ERROR: {str(e)}"
            state["error"] = str(e)
            print(f"💥 [EXCEPTION] {str(e)}")

        return state
    
    def feedback_analyzer(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state
        
        execution_result = state.get("execution_result", "")
        command = state["action_plan"].get("execute_command", "")
        
        self._rate_limit_api_call()
        
        prompt = f"""You executed this command to fix an incident:
Command: {command}

Result:
{execution_result}

Analyze if the fix was successful. Reply with ONLY one word:
- SUCCESS
- RETRY
- FAILED

Response:"""

        try:
            response = self.llm.generate(prompt).strip().upper()
            
            if "SUCCESS" in response:
                state["verification_passed"] = True
                print(f"✅ AI Analysis: Command succeeded!")
            elif "RETRY" in response:
                state["verification_passed"] = False
                print(f"🔄 AI Analysis: Command failed, will retry")
            else:
                state["verification_passed"] = False
                state["error"] = "AI determined fix failed"
                print(f"❌ AI Analysis: Cannot be fixed")
            
            self.log_action(state["incident_id"], "feedback_analysis", {
                "decision": response,
                "command": command,
                "output": execution_result[:200]
            })
            
        except Exception as e:
            print(f"⚠️  Feedback analysis failed: {e}")
            state["verification_passed"] = True
        
        return state
    
    def decide_after_feedback(self, state: IncidentState) -> str:
        if state.get("error"):
            return "failed"
        
        if state["verification_passed"]:
            return "success"
        
        if state["attempts"] < self.MAX_ATTEMPTS - 1:
            print(f"🔄 Retrying with different approach (attempt {state['attempts'] + 1}/{self.MAX_ATTEMPTS})")
            return "retry"
        
        return "failed"
    
    def verifier(self, state: IncidentState) -> IncidentState:
        if state.get("error"):
            return state
            
        if not incidentmanager.mark_ai_action_completed(
            state["incident_id"],
            state["action_plan"].get("execute_command", "")
        ):
            print(f"⚠️  Could not mark action as completed")
            state["error"] = "Failed to update incident status"
            return state
        
        self.log_action(state["incident_id"], "verification_started", {
            "status": "waiting for incident board"
        })
        
        return state
    
    def should_continue(self, state: IncidentState) -> str:
        if state.get("error") == "API_RATE_LIMIT":
            return "failed"
            
        if state.get("error"):
            if state["attempts"] >= self.MAX_ATTEMPTS - 1:
                self.escalate_incident(state["incident"])
            return "failed"
        
        return "success"
    
    def escalate_incident(self, incident: dict):
        email = self.config['escalation']['email']
        
        alert_msg = {
            "timestamp": datetime.now().isoformat(),
            "incident_id": incident['id'],
            "fault_type": incident['fault_type'],
            "message": incident['message'],
            "count": incident['count'],
            "ai_attempts": incident.get('ai_attempts', 0),
            "escalated_to": email
        }
        
        self.log_action(incident['id'], "ESCALATED", alert_msg)
        print(f"\n🚨 ESCALATED to {email}: {incident['id'][:8]}")
    
    def log_action(self, incident_id: str, action: str, details: dict):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "incident_id": incident_id,
            "action": action,
            "details": details
        }
        
        try:
            with open(self.LOG_PATH, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"⚠️  Failed to write log: {e}")
    
    def check_verification(self, incident: dict):
        print(f"\n{'='*60}")
        print(f"🔍 Verifying: {incident['id'][:8]}")
        print(f"Type: {incident['fault_type']}")
        print(f"{'='*60}\n")

        INCIDENTS = incidentmanager.load_incidents()

        if incident["id"] in INCIDENTS:
            INCIDENTS[incident["id"]]["verification_streak"] = INCIDENTS[incident["id"]].get("verification_streak", 0) + 1
            verification_streak = INCIDENTS[incident["id"]]["verification_streak"]
            incidentmanager.save_incidents(INCIDENTS)
        else:
            verification_streak = 0

        print(f"Verification Streak: {verification_streak}/3")

        if verification_streak >= 3:
            print(f"✅ FIXED! {incident['id'][:8]} - No errors for 3 cycles")

            INCIDENTS[incident["id"]]["status"] = "fixed"
            INCIDENTS[incident["id"]]["active"] = False
            INCIDENTS[incident["id"]]["fixed_at"] = datetime.now()
            incidentmanager.save_incidents(INCIDENTS)

            self.log_action(incident['id'], "verified_fixed", {
                "verification_streak": verification_streak
            })
        else:
            print(f"⏳ Waiting... {incident['id'][:8]} - Streak: {verification_streak}/3")

        return
    
    def get_incidents_to_process(self):
        try:
            eligible = incidentmanager.get_incidents_for_ai()
            max_per_cycle = self.config['incident_board']['max_per_cycle']
            return eligible[:max_per_cycle]
        except Exception as e:
            print(f"⚠️  Failed to load incidents: {e}")
            return []
    
    def process_incident(self, incident: dict):
        if incident.get("status") == "verifying":
            return self.check_verification(incident)
        
        print(f"\n{'='*60}")
        print(f"Processing: {incident['id'][:8]}")
        print(f"Type: {incident['fault_type']}")
        print(f"Message: {incident['message'][:60]}...")
        print(f"Count: {incident['count']}")
        print(f"Intermittent: {'⚠️ YES' if incident.get('is_intermittent', False) else 'NO'}")
        print(f"AI Attempts: {incident.get('ai_attempts', 0)}/{self.MAX_ATTEMPTS}")
        print(f"{'='*60}\n")
        
        initial_state = IncidentState(
            incident_id=incident['id'],
            incident=incident,
            analysis="",
            specialist_type="",
            action_plan={},
            execution_result="",
            verification_passed=False,
            attempts=incident.get('ai_attempts', 0),
            error=""
        )
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            if final_state.get("error"):
                print(f"⚠️  Partial: {incident['id'][:8]}: {final_state['error']}")
            else:
                print(f"✓ Processed: {incident['id'][:8]}")
                print(f"  Action: {final_state['action_plan'].get('execute_command', 'N/A')[:60]}")
                print(f"  Result: {final_state.get('execution_result', 'N/A')[:60]}")
        except Exception as e:
            print(f"✗ Error: {incident['id'][:8]}: {str(e)}")
            self.log_action(incident['id'], "error", {"error": str(e)})
    
    def display_dashboard(self):
        try:
            incidentmanager.show_board()
        except Exception as e:
            print(f"⚠️  Failed to display dashboard: {e}")
    
    def get_current_metrics(self):
        try:
            return incidentmanager.get_metrics()
        except Exception as e:
            print(f"⚠️  Failed to get metrics: {e}")
            return {
                "total_incidents": 0,
                "active_incidents": 0,
                "fixed_incidents": 0,
                "intermittent_issues": 0,
                "ai_success_rate": 0.0,
                "failed_incidents": 0
            }
    
    def run(self):
        print(f"🚀 AI Incident Service Started (WITH FEEDBACK LOOP)")
        print(f"Provider: {self.config['llm']['provider']}")
        print(f"Model: {self.config['llm']['model']}")
        print(f"Monitoring: {self.INCIDENTS_PATH}")
        print(f"Poll Interval: {self.POLL_INTERVAL}s")
        print(f"Max Attempts per Incident: {self.MAX_ATTEMPTS}")
        print(f"Execution Mode: {self.config['execution']['mode']}")
        print(f"Rate Limit: {self.min_api_interval}s between API calls\n")
        
        cycle_count = 0
        
        while True:
            try:
                incidents = self.get_incidents_to_process()
                
                if incidents:
                    print(f"\n{'='*80}")
                    print(f"📋 Cycle #{cycle_count} - Found {len(incidents)} incidents to process")
                    print(f"{'='*80}")
                    
                    for incident in incidents:
                        self.process_incident(incident)
                        time.sleep(1)
                    
                    print("\n")
                    self.display_dashboard()
                    
                    metrics = self.get_current_metrics()
                    print(f"\n📊 Metrics:")
                    print(f"  Active: {metrics['active_incidents']}")
                    print(f"  Fixed: {metrics['fixed_incidents']}")
                    print(f"  Intermittent: {metrics['intermittent_issues']}")
                    print(f"  AI Success Rate: {metrics['ai_success_rate']}%")
                    print(f"  Failed: {metrics['failed_incidents']}")
                    
                    cycle_count += 1
                else:
                    print(".", end="", flush=True)
                
                time.sleep(self.POLL_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\n🛑 AI Service Stopped")
                print(f"Total cycles processed: {cycle_count}")
                self.display_dashboard()
                break
            except Exception as e:
                print(f"\n⚠️  Error in main loop: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(self.POLL_INTERVAL)

if __name__ == "__main__":
    service = AIIncidentService()
    service.run()
