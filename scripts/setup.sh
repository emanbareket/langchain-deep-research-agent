#!/bin/bash
# Compatibility wrapper: start.sh now handles setup and launch in one step.
set -e
cd "$(dirname "$0")"
exec ./start.sh
