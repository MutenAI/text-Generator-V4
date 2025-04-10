
#!/bin/bash
cd $(dirname "$0")
echo "==== Backing up work state ===="

# Create backup directory if it doesn't exist
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

# Create timestamp for backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# Create backup archive
echo "Creating backup archive..."
tar -czf $BACKUP_FILE ./src ./config ./output .env content_generator_app.py run-streamlit.sh

echo "✅ Backup completed: $BACKUP_FILE"
echo "To restore from this backup, run: tar -xzf $BACKUP_FILE"
