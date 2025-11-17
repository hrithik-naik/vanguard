#!/bin/bash

set -e  # Exit on error

echo "🚀 Starting Self-Healing System"
echo "================================"

# Fix permissions first
echo ""
echo "🔧 Fixing file permissions..."

# Function to fix file permissions
fix_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo "  Found: $file"
        # Try without sudo first
        if [ -w "$file" ]; then
            echo "  ✓ Already writable"
        else
            # Need sudo
            if sudo -n chown $USER:$USER "$file" 2>/dev/null; then
                chmod 666 "$file"
                echo "  ✓ Fixed with sudo"
            else
                echo "  ⚠️  Need sudo password to fix permissions"
                sudo chown $USER:$USER "$file"
                chmod 666 "$file"
                echo "  ✓ Fixed"
            fi
        fi
    else
        echo "  Creating: $file"
        if [ "$file" = "/tmp/incidents.json" ]; then
            echo "{}" > "$file"
        else
            touch "$file"
        fi
        chmod 666 "$file"
        echo "  ✓ Created"
    fi
}

# Fix both files
fix_file "/tmp/incidents.json"
fix_file "/tmp/ai_actions.log"

echo ""
echo "📊 File permissions:"
ls -lh /tmp/incidents.json /tmp/ai_actions.log

# Activate virtual environment
echo ""
echo "🐍 Activating virtual environment..."
if [ -f "build/.venv/bin/activate" ]; then
    source build/.venv/bin/activate
    echo "  ✓ Virtual environment activated"
else
    echo "  ✗ Virtual environment not found at build/.venv"
    echo "  Please create it first with: python3 -m venv build/.venv"
    exit 1
fi

# Check if required packages are installed
echo ""
echo "📦 Checking dependencies..."
python3 -c "import langgraph, google.generativeai" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✓ Required packages found"
else
    echo "  ⚠️  Some packages may be missing"
    echo "  Install with: pip install langgraph google-generativeai"
fi

# Start AI service
echo ""
echo "🤖 Starting AI Incident Service..."
echo "================================"
echo ""

# Run the service
python3 selfhealing/ai_service.py

# Cleanup on exit
trap "echo ''; echo '🛑 Shutdown complete'" EXIT