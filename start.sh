#!/usr/bin/env bash
# ==============================================================================
#  DUSTFALL — Mars Survival & MARS-EIS Environmental Interface
#  Full-Stack Deployment & Startup Script (Bash)
#
#  1. Clones MARS-EIS backend repository if not already present.
#  2. Installs / verifies required Python dependencies.
#  3. Starts authoritative MARS-EIS scientific engine on http://127.0.0.1:8000.
#  4. Launches DUSTFALL Pygame client with live telemetry synchronization.
#  5. Cleanly terminates background processes on exit.
#
#  Made by Lunarmist-byte
#  GitHub:   https://github.com/Lunarmist-byte
#  LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
# ==============================================================================

set -e

BACKEND_REPO="https://github.com/Lunarmist-byte/drsosospaceadventure.git"
PORT=8000
SKIP_INTRO=false

# Parse flags
for arg in "$@"; do
    case $arg in
        --skip-intro)
            SKIP_INTRO=true
            shift
            ;;
        --port=*)
            PORT="${arg#*=}"
            shift
            ;;
    esac
done

echo ""
echo "=========================================================="
echo "   DUSTFALL // FULL-STACK SIMULATION LAUNCHER (BASH)     "
echo "   Made by Lunarmist-byte                                 "
echo "   GitHub:   https://github.com/Lunarmist-byte           "
echo "   LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/"
echo "=========================================================="
echo ""

# 1. Resolve Python
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "[ERROR] Python was not found in PATH! Please install Python 3.10+."
    exit 1
fi
echo "[1/5] Using Python: $($PYTHON --version)"

# 2. Check / Clone Backend Repository
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

BACKEND_DIR="$PARENT_DIR/ssosalien"
if [ ! -d "$BACKEND_DIR" ]; then
    BACKEND_DIR="$SCRIPT_DIR/ssosalien"
fi

if [ -d "$BACKEND_DIR" ]; then
    echo "[2/5] Backend directory detected at: $BACKEND_DIR"
else
    echo "[2/5] Backend not found locally. Cloning from $BACKEND_REPO..."
    CLONE_TARGET="$PARENT_DIR/ssosalien"
    if git clone "$BACKEND_REPO" "$CLONE_TARGET" 2>/dev/null; then
        BACKEND_DIR="$CLONE_TARGET"
        echo "      Backend successfully cloned to: $BACKEND_DIR"
    else
        echo "      Parent folder clone failed, cloning inside workspace..."
        CLONE_TARGET="$SCRIPT_DIR/ssosalien"
        git clone "$BACKEND_REPO" "$CLONE_TARGET"
        BACKEND_DIR="$CLONE_TARGET"
        echo "      Backend successfully cloned to: $BACKEND_DIR"
    fi
fi

# 3. Verify Dependencies
echo "[3/5] Verifying Python dependencies..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    $PYTHON -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
fi
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    $PYTHON -m pip install -q -r "$BACKEND_DIR/requirements.txt"
fi
echo "      Dependencies verified."

# 4. Check & Start MARS-EIS Backend Server
echo "[4/5] Checking MARS-EIS simulation backend on port $PORT..."
BACKEND_PID=""

is_port_open() {
    $PYTHON -c "import sys, socket; s = socket.socket(); s.settimeout(0.4); sys.exit(0 if s.connect_ex(('127.0.0.1', $PORT)) == 0 else 1)" 2>/dev/null
}

cleanup() {
    if [ -n "$BACKEND_PID" ]; then
        echo ""
        echo "Stopping background MARS-EIS backend process (PID $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
        echo "Backend stopped cleanly."
    fi
    echo ""
    echo "Session finished. Thank you for playing DUSTFALL!"
    echo "Made by Lunarmist-byte (https://github.com/Lunarmist-byte)"
}
trap cleanup EXIT INT TERM

if is_port_open; then
    echo "      Existing MARS-EIS engine found running at http://127.0.0.1:$PORT."
else
    echo "      Starting MARS-EIS backend on http://127.0.0.1:$PORT in background..."
    (cd "$BACKEND_DIR" && $PYTHON main.py --serve-api --port "$PORT") > /dev/null 2>&1 &
    BACKEND_PID=$!

    # Wait for server ready (up to 10 seconds)
    READY=false
    for i in $(seq 1 25); do
        sleep 0.4
        if is_port_open; then
            READY=true
            break
        fi
    done

    if [ "$READY" = true ]; then
        echo "      MARS-EIS backend online and responding on port $PORT!"
    else
        echo "      [WARNING] Backend took longer than expected to bind port $PORT. Launching client anyway..."
    fi
fi

# 5. Launch DUSTFALL Pygame Client
echo "[5/5] Launching DUSTFALL Client..."
echo "----------------------------------------------------------"
cd "$SCRIPT_DIR"
GAME_ARGS=("main.py")
if [ "$SKIP_INTRO" = true ]; then
    GAME_ARGS+=("--skip-intro")
fi

$PYTHON "${GAME_ARGS[@]}"
