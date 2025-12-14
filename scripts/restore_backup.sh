#!/bin/bash
# ResearchOS Restore Script
# Restores from backup created by create_backup.sh

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore_backup.sh <backup_dir>"
    echo ""
    echo "Available backups:"
    ls -1t backups/ 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "⚠️  WARNING: This will restore from backup:"
echo "   $BACKUP_DIR"
echo ""
cat "$BACKUP_DIR/MANIFEST.txt" 2>/dev/null || echo "   (no manifest found)"
echo ""
echo "Current code will be OVERWRITTEN!"
echo ""
read -p "Press Enter to continue, Ctrl+C to abort... " _

# Stop running services
echo "🛑 Stopping services..."
pkill -f "python.*server.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# Restore code
echo "📂 Restoring code..."
if [ -d "$BACKUP_DIR/code/research_os" ]; then
    rm -rf research_os
    cp -r "$BACKUP_DIR/code/research_os" .
fi

if [ -d "$BACKUP_DIR/code/jarvis_m4" ]; then
    rm -rf jarvis_m4
    cp -r "$BACKUP_DIR/code/jarvis_m4" .
fi

if [ -f "$BACKUP_DIR/code/start_all.sh" ]; then
    cp "$BACKUP_DIR/code/start_all.sh" .
    chmod +x start_all.sh
fi

# Restore data
echo "💾 Restoring data..."
if [ -d "$BACKUP_DIR/data/dedup" ]; then
    mkdir -p "$HOME/.jrvis/dedup"
    cp -r "$BACKUP_DIR/data/dedup/"* "$HOME/.jrvis/dedup/" 2>/dev/null || true
fi

if [ -f "$BACKUP_DIR/data/faiss/faiss_index.bin" ]; then
    mkdir -p "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2"
    cp "$BACKUP_DIR/data/faiss/faiss_index.bin" \
       "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2/"
fi

if [ -d "$BACKUP_DIR/data/research_v2.kuzu" ]; then
    rm -rf data/research_v2.kuzu
    cp -r "$BACKUP_DIR/data/research_v2.kuzu" data/
fi

if [ -f "$BACKUP_DIR/data/schema/research_schema.db" ]; then
    mkdir -p "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2"
    cp "$BACKUP_DIR/data/schema/research_schema.db" \
       "$HOME/.gemini/antigravity/brain/d8312e01-8174-4fb2-a582-ee259e6bf7f2/"
fi

echo ""
echo "✅ Restore complete from: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Verify files: ls -la research_os/ jarvis_m4/"
echo "  2. Start services: ./start_all.sh"
echo "  3. Test basic functionality"
