#!/bin/bash

# Get the PIDs of Python processes related to lichess-bot
python_pids=$(ps aux | grep lichess-bot | grep -v grep | awk '{print $2}')

# Kill each Python process
for pid in $python_pids; do
    kill -9 $pid
done

