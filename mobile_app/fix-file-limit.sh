#!/bin/bash
# Fix "too many open files" error for React Native/Expo

# Increase file descriptor limit for current session
ulimit -n 4096

# Check current limit
echo "Current file descriptor limit: $(ulimit -n)"

# Start Expo with increased limit
echo "Starting Expo with increased file limit..."
npm start

