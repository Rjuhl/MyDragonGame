#!/bin/bash

# Define the target directory
TARGET_DIR="/Users/rainjuhl/Documents/MyDragonGame/data/chunks"

# Check if the directory exists
if [ -d "$TARGET_DIR" ]; then
  echo "Deleting all files and directories under $TARGET_DIR"
  rm -rf "$TARGET_DIR"/*
  echo "Cleanup complete."
else
  echo "Directory $TARGET_DIR does not exist."
  exit 1
fi
