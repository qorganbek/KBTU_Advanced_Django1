#!/bin/bash

python bot.py & uvicorn main:app --reload --host 0.0.0.0 --port 8000