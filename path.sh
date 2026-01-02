#!/bin/bash
# path.sh - Setup Python path for the project
# Usage: source path.sh (for local dev) or run in Docker entrypoint

set -e

# Detect project root
if [ -n "$1" ]; then
    PROJECT_ROOT="$1"
else
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

PROJECT_NAME=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]')

echo "🔧 Setting up Python path for: $PROJECT_NAME"
echo "   Project root: $PROJECT_ROOT"

# Check if running in Docker (site-packages location differs)
if [ -d "/usr/local/lib" ]; then
    # Docker/Linux environment
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || echo "/usr/local/lib/python3.13/site-packages")
elif [ -d "$PROJECT_ROOT/venv" ]; then
    # Virtual environment
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    SITE_PACKAGES="$PROJECT_ROOT/venv/lib/python$PYTHON_VERSION/site-packages"
else
    # System Python
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
fi

# Create .pth file
PTH_FILE="$SITE_PACKAGES/${PROJECT_NAME}.pth"
echo "$PROJECT_ROOT" > "$PTH_FILE"

echo "✅ Created: $PTH_FILE"
echo "   Path added: $PROJECT_ROOT"

# Also export PYTHONPATH for current session
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo "✅ PYTHONPATH updated for current session"

# Verify
echo ""
echo "🔍 Verification:"
python -c "import sys; print('   ' + '\n   '.join([p for p in sys.path if p]))" | head -5
