#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../milestone-handler-function"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
functions-framework --target=handle_milestone_completion --debug --port=8084
