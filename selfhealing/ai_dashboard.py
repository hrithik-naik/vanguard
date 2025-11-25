from flask import Flask, render_template_string
import json
import os

LOG_FILE = "logs/ai_actions.log"

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Incident Actions Log</title>
    <meta http-equiv="refresh" content="5"> <!-- Auto refresh -->
    <style>
        body { font-family: Arial, sans-serif; background: #111; color: #eee; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; border: 1px solid #444; }
        th { background: #333; }
        tr:nth-child(even) { background: #1b1b1b; }
        .success { color: #4caf50; }
        .failed { color: #ff5252; }
        .blocked { color: #ff9800; }
    </style>
</head>
<body>
    <h2>🤖 AI Action Log</h2>
    <p>Source: <code>{{ log_file }}</code></p>

    {% if entries %}
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Incident ID</th>
            <th>Action</th>
            <th>Details</th>
        </tr>
        {% for entry in entries %}
        <tr>
            <td>{{ entry.timestamp }}</td>
            <td>{{ entry.incident_id[:8] }}</td>
            <td>
                {% if "failed" in entry.action.lower() %}
                    <span class="failed">{{ entry.action }}</span>
                {% elif "blocked" in entry.action.lower() %}
                    <span class="blocked">{{ entry.action }}</span>
                {% elif "verified" in entry.action.lower() or "success" in entry.action.lower() %}
                    <span class="success">{{ entry.action }}</span>
                {% else %}
                    {{ entry.action }}
                {% endif %}
            </td>
            <td><pre>{{ entry.details|tojson(indent=2) }}</pre></td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
        <p>No logs available yet.</p>
    {% endif %}
</body>
</html>
"""

def read_logs():
    if not os.path.exists(LOG_FILE):
        return []
    
    entries = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(data)
            except ValueError:
                continue

    # Sort newest first
    entries.reverse()
    return entries

@app.route("/")
def dashboard():
    logs = read_logs()
    return render_template_string(HTML_TEMPLATE, entries=logs, log_file=LOG_FILE)

if __name__ == "__main__":
    print("🚀 AI Log Dashboard running at http://127.0.0.1:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
