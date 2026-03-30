#!/bin/bash
cd "/Users/nageshei/ableton interact machine"
export $(grep -v '^#' .env | xargs)
source .venv/bin/activate
python -m aim
