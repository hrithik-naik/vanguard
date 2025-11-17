from flask import Flask, render_template_string, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
PATH = "data/incidents.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vanguard Incident Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0e27;
            color: #00ff41;
            padding: 20px;
        }
        .header {
            background: #1a1e3a;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 2px solid #00ff41;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 10px;
            text-shadow: 0 0 10px #00ff41;
        }
        .stats {
            font-size: 16px;
            color: #00d4ff;
        }
        .legend {
            margin-top: 10px;
            font-size: 14px;
            color: #888;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #1a1e3a;
            border-radius: 8px;
            overflow: hidden;
        }
        th {
            background: #2a2e4a;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #00ff41;
            font-size: 14px;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #2a2e4a;
            font-size: 13px;
        }
        tr:hover {
            background: #252943;
        }
        .status-new { color: #ffd700; }
        .status-ongoing { color: #ff8c00; }
        .status-verifying { color: #00bfff; }
        .status-fixed { color: #00ff41; }
        .status-failed { color: #ff4444; }
        .status-reoccurred { color: #ff66ff; }
        .intermittent { color: #ff4444; font-size: 16px; }
        .id-cell { 
            font-size: 11px; 
            color: #666;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .refresh-time {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #1a1e3a;
            padding: 10px 15px;
            border-radius: 5px;
            border: 1px solid #00ff41;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="refresh-time">Auto-refresh: <span id="countdown">5</span>s</div>
    
    <div class="header">
        <h1>⚡ Vanguard Incident Dashboard</h1>
        <div class="stats">
            Active: <span id="active">0</span> | 
            Fixed: <span id="fixed">0</span> | 
            Total: <span id="total">0</span>
        </div>
        <div class="legend">
            Status: <span class="status-new">new</span> → 
            <span class="status-ongoing">ongoing</span> → 
            <span class="status-verifying">verifying</span> → 
            <span class="status-fixed">fixed</span> | 
            <span class="status-failed">failed</span> | 
            <span class="status-reoccurred">reoccurred</span>
        </div>
    </div>

    <table id="incidents-table">
        <thead>
            <tr>
                <th>Type</th>
                <th>Status</th>
                <th>Count</th>
                <th>AI</th>
                <th>INT</th>
                <th>Last Seen</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody id="incidents-body">
            <tr><td colspan="7" style="text-align:center; padding:30px;">Loading...</td></tr>
        </tbody>
    </table>

    <script>
        let countdown = 5;
        
        function updateDashboard() {
            fetch('/api/incidents')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('active').textContent = data.active;
                    document.getElementById('fixed').textContent = data.fixed;
                    document.getElementById('total').textContent = data.total;
                    
                    const tbody = document.getElementById('incidents-body');
                    if (data.incidents.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px;">No incidents yet...</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = data.incidents.map(inc => `
                        <tr>
                            <td>${inc.fault_type}</td>
                            <td class="status-${inc.status}">${inc.status}</td>
                            <td>${inc.count}</td>
                            <td>${inc.ai_attempts}</td>
                            <td class="intermittent">${inc.is_intermittent ? '⚠️' : ''}</td>
                            <td>${inc.last_seen}</td>
                            <td>${inc.message}</td>
                        </tr>
                    `).join('');
                });
        }
        
        function startCountdown() {
            countdown = 5;
            const interval = setInterval(() => {
                countdown--;
                document.getElementById('countdown').textContent = countdown;
                if (countdown <= 0) {
                    clearInterval(interval);
                    updateDashboard();
                    startCountdown();
                }
            }, 1000);
        }
        
        updateDashboard();
        startCountdown();
    </script>
</body>
</html>
"""

def parse_timestamp(ts):
    try:
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return str(ts)[:19]
    except:
        return str(ts)[:19]

def shorten(s, n=60):
    return (s[:n] + "...") if len(s) > n else s

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/incidents')
def get_incidents():
    if not os.path.exists(PATH):
        return jsonify({
            'active': 0,
            'fixed': 0,
            'total': 0,
            'incidents': []
        })
    
    try:
        with open(PATH, 'r') as f:
            incidents = json.load(f)
    except:
        return jsonify({
            'active': 0,
            'fixed': 0,
            'total': 0,
            'incidents': []
        })
    
    active = sum(1 for x in incidents.values() if x.get("active"))
    fixed = sum(1 for x in incidents.values() if x.get("status") == "fixed")
    total = len(incidents)
    
    incident_list = sorted(incidents.values(), key=lambda x: (
        not x.get("active", False),
        not x.get("is_intermittent", False),
        -x.get("count", 0)
    ))
    
    formatted_incidents = []
    for inc in incident_list:
        formatted_incidents.append({
            'id': inc['id'][:8],
            'fault_type': inc['fault_type'],
            'status': inc['status'],
            'count': inc['count'],
            'ai_attempts': inc['ai_attempts'],
            'is_intermittent': inc.get('is_intermittent', False),
            'last_seen': parse_timestamp(inc.get('last_seen', '')),
            'message': shorten(inc['message'])
        })
    
    return jsonify({
        'active': active,
        'fixed': fixed,
        'total': total,
        'incidents': formatted_incidents
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)