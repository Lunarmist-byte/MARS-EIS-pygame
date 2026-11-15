#!/usr/bin/env bash
# Forward to start.sh
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$DIR/start.sh" "$@"
