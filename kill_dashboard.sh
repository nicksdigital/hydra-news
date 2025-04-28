#!/bin/bash
# Script to kill all dashboard processes

echo "Killing all dashboard processes..."

# Find and kill all Python processes running the dashboard
pkill -f "python.*run_dashboard"
pkill -f "python.*visualizer/server.py"

echo "All dashboard processes killed"
