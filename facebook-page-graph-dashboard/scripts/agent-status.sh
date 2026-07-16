#!/bin/bash
# Hiển thị trạng thái 2 LaunchAgents + log gần đây.
# Usage: ./scripts/agent-status.sh

set -e

PLIST_SERVER="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.server.plist"
PLIST_SYNC="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.sync.plist"
PLIST_REFRESH="$HOME/Library/LaunchAgents/com.bobo.fb-dashboard.token-refresh.plist"
LOG_DIR="/Users/bobo/ZCodeProject/facebook-page-graph-dashboard/logs"

echo "═══════════════════════════════════════════════════════════"
echo "  Facebook Page Dashboard — LaunchAgent Status"
echo "═══════════════════════════════════════════════════════════"
echo

# Server status
echo "▶ SERVER  (com.bobo.fb-dashboard.server)"
PID=$(launchctl list 2>/dev/null | grep "com.bobo.fb-dashboard.server" | awk '{print $1}')
if [ "$PID" != "-" ] && [ -n "$PID" ]; then
  echo "  Trạng thái:  ✅ đang chạy (PID $PID)"
else
  echo "  Trạng thái:  ❌ chưa chạy"
fi
echo "  Endpoint:    http://localhost:3123"
echo "  RunAtLoad:   ✅ tự khởi động khi đăng nhập"
echo "  KeepAlive:   ✅ tự restart nếu crash (sau 10s)"
echo

# Sync status
echo "▶ SYNC    (com.bobo.fb-dashboard.sync)"
SPID=$(launchctl list 2>/dev/null | grep "com.bobo.fb-dashboard.sync" | awk '{print $1}')
if [ "$SPID" != "-" ] && [ -n "$SPID" ]; then
  echo "  Trạng thái:  ✅ đang chạy lần này (PID $SPID)"
else
  echo "  Trạng thái:  ⏰ chờ đến lịch tiếp theo"
fi
echo "  Lịch:        mỗi 2 giờ (00:00, 02:00, 04:00 ... 22:00)"
echo

# Token refresh status
echo "▶ REFRESH (com.bobo.fb-dashboard.token-refresh)"
RSTATUS=$(launchctl list 2>/dev/null | grep "com.bobo.fb-dashboard.token-refresh" | awk '{print $1}')
if [ -n "$RSTATUS" ]; then
  echo "  Trạng thái:  ✅ đã load (chạy mỗi 50 phút)"
else
  echo "  Trạng thái:  ❌ chưa load"
fi
echo "  Script:      scripts/refresh-token.sh"
echo "  Yêu cầu:     FB_USER_ACCESS_TOKEN + FB_APP_ID + FB_APP_SECRET trong .env.local"
echo

# Server log tail
echo "── Server log (5 dòng cuối) ──"
tail -5 "$LOG_DIR/server.out.log" 2>/dev/null | sed 's/^/  /'
echo

# Sync log tail
echo "── Sync log (5 dòng cuối) ──"
if [ -f "$LOG_DIR/sync.out.log" ]; then
  tail -5 "$LOG_DIR/sync.out.log" 2>/dev/null | sed 's/^/  /'
else
  echo "  (chưa có log — sync chưa chạy lần nào)"
fi
echo

echo "── Lệnh tiện ích ──"
echo "  Trạng thái:    $0"
echo "  Stop:          ./scripts/agent-stop.sh"
echo "  Start/Restart: ./scripts/agent-start.sh"
echo "  Xem log server:tail -f $LOG_DIR/server.out.log"
echo "  Xem log sync:  tail -f $LOG_DIR/sync.out.log"
