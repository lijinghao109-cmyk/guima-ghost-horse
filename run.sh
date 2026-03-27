#!/bin/bash
cd "/Users/nageshei/ableton interact machine"
export $(grep -v '^#' .env | xargs)
python3 aim.py
