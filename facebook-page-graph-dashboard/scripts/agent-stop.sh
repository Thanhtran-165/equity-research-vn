#!/bin/bash
# Dừng 2 LaunchAgents (không xoá plist — vẫn tự chạy lại sau khi reboot).
# Usage: ./scripts/agent-stop.sh

set -e

PLIST_SERVER="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.server.plist"
PLIST_SYNC="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.sync.plist"
PLIST_REFRESH="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.token-refresh.plist"

echo "→ Dừng server agent..."
launchctl unload "$PLIST_SERVER" 2>/dev/null && echo "  ✓ unloaded" || echo "  (chưa load)"

echo "→ Dừng sync agent..."
launchctl unload "$PLIST_SYNC" 2>/dev/null && echo "  ✓ unloaded" || echo "  (chưa load)"

echo "→ Dừng token-refresh agent..."
launchctl unload "$PLIST_REFRESH" 2>/dev/null && echo "  ✓ unloaded" || echo "  (chưa load)"

echo
echo "✅ Đã dừng. Chạy ./scripts/agent-start.sh để chạy lại."
echo "⚠️  Sau khi reboot máy, 2 agents sẽ tự chạy lại (vẫn còn plist)."
