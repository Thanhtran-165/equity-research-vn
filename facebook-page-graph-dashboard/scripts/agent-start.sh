#!/bin/bash
# (Re)start 2 LaunchAgents.
# Usage: ./scripts/agent-start.sh

set -e

PLIST_SERVER="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.server.plist"
PLIST_SYNC="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.sync.plist"
PLIST_REFRESH="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.token-refresh.plist"

echo "→ Đảm bảo đã build production..."
cd /Users/bobo/ZCodeProject/facebook-page-graph-dashboard
if [ ! -f .next/BUILD_ID ]; then
  echo "  Chưa có build → chạy npm run build..."
  npm run build
fi

echo "→ Unload cũ (nếu đang chạy)..."
launchctl unload "$PLIST_SERVER" 2>/dev/null || true
launchctl unload "$PLIST_SYNC" 2>/dev/null || true
sleep 1

echo "→ Load server agent..."
launchctl load -w "$PLIST_SERVER" && echo "  ✓ loaded"

echo "→ Load sync agent..."
launchctl load -w "$PLIST_SYNC" && echo "  ✓ loaded"

echo "→ Load token-refresh agent (optional — chỉ load nếu có user token)..."
if grep -qE "^FB_USER_ACCESS_TOKEN=\S" "$PROJECT_DIR/.env.local" 2>/dev/null; then
  launchctl load -w "$PLIST_REFRESH" && echo "  ✓ loaded (chạy mỗi 50 phút)"
else
  echo "  (skip — chưa có FB_USER_ACCESS_TOKEN trong .env.local)"
fi

echo
echo "→ Đợi server khởi động (5s)..."
sleep 5

# Verify
echo
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Đã khởi động"
echo "═══════════════════════════════════════════════════════════"
echo
echo "Server: http://localhost:3123"
echo "Sync:   mỗi 2 giờ tự động (lần đầu lúc 00:00/02:00/...)"
echo
echo "Trạng thái chi tiết: ./scripts/agent-status.sh"
