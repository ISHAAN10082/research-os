#!/bin/bash
# ResearchOS Backup Script
# Creates timestamped backup of critical code and data

set -e

BACKUP_ROOT="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

echo "📦 Creating backup at $BACKUP_DIR..."

# Create backup directory structure
mkdir -p "$BACKUP_DIR"/{code,data,config}

# Backup code
echo "  → Backing up code..."
cp -r research_os "$BACKUP_DIR/code/" 2>/dev/null || true
cp -r jarvis_m4 "$BACKUP_DIR/code/" 2>/dev/null || true
cp start_all.sh "$BACKUP_DIR/code/" 2>/dev/null || true
cp run.sh "$BACKUP_DIR/code/" 2>/dev/null || true

# Backup data indices (not raw papers - too large)
echo "  → Backing up indices..."
if [ -d "$HOME/.jrvis/dedup" ]; then
    cp -r "$HOME/.jrvis/dedup" "$BACKUP_DIR/data/" 2>/dev/null || true
fi

if [ -f "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2/faiss_index.bin" ]; then
    mkdir -p "$BACKUP_DIR/data/faiss"
    cp "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2/faiss_index.bin" \
       "$BACKUP_DIR/data/faiss/" 2>/dev/null || true
fi

# Backup database
echo "  → Backing up database..."
if [ -d "data/research_v2.kuzu" ]; then
    cp -r data/research_v2.kuzu "$BACKUP_DIR/data/" 2>/dev/null || true
fi

# Backup schema database
if [ -f "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2/research_schema.db" ]; then
    mkdir -p "$BACKUP_DIR/data/schema"
    cp "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2/research_schema.db" \
       "$BACKUP_DIR/data/schema/" 2>/dev/null || true
fi

# Create manifest
echo "  → Creating manifest..."
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
ResearchOS Backup
Created: $TIMESTAMP
Host: $(hostname)
User: $(whoami)

Contents:
- Code: research_os/, jarvis_m4/, start_all.sh
- Data: Deduplication indices, FAISS index, KuzuDB, Schema
- Config: Environment settings

To restore:
  ./scripts/restore_backup.sh $BACKUP_DIR

Notes:
- Raw PDF files are NOT backed up (too large)
- Only indices and metadata are preserved
- Papers can be re-ingested from originals if needed
EOF

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo "✅ Backup complete!"
echo "   Location: $BACKUP_DIR"
echo "   Size: $BACKUP_SIZE"
echo ""
echo "To restore: ./scripts/restore_backup.sh $BACKUP_DIR"

# Keep only last 10 backups
echo "  → Cleaning old backups (keeping last 10)..."
ls -t "$BACKUP_ROOT" | tail -n +11 | xargs -I {} rm -rf "$BACKUP_ROOT/{}" 2>/dev/null || true

echo "✅ Done"
