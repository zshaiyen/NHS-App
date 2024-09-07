#!/bin/bash

# Function to display usage instructions
usage() {
    echo "Usage: $0 source_file backup_directory restart_file"
    exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    usage
fi

# Define the source file and backup directory
SOURCE_FILE=$1
BACKUP_DIR=$2
RESTART_FILE=$3

# Check if the source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: Source file does not exist."
    exit 1
fi

# Check if the backup directory exists, create it if not
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory does not exist. Creating directory..."
    mkdir -p "$BACKUP_DIR"
fi

# Get the base name of the file (without the directory path)
FILE_NAME=$(basename "$SOURCE_FILE")

# Add a timestamp to the backup file name
TIMESTAMP=$(date +'%Y%m%d%H%M%S')
BACKUP_FILE="$BACKUP_DIR/${FILE_NAME}_backup_$TIMESTAMP"

# Copy the source file to the backup location
cp "$SOURCE_FILE" "$BACKUP_FILE"

# Confirm success
if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
else
    echo "Error: Backup failed."
    exit 1
fi

# Delete old backups
echo "Deleting old backups..."
find "$BACKUP_DIR" -name "${FILE_NAME}_backup_*" -type f -mtime +7 -print -exec rm -f {} \;

if [ $? -ne 0 ]; then
    echo "Error: Failed to delete old backups."
    exit 1
fi

# Restart app
touch $RESTART_FILE
