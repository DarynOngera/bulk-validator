#!/bin/bash

# Runs the FastAPI app
uvicorn app.main:app --reload --port 8000
