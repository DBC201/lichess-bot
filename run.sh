#!/bin/bash

source ./venv/bin/activate

nohup python3 lichess-bot.py > output &
