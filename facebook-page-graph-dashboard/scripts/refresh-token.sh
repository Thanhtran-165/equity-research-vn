#!/bin/bash
# Refresh PAGE Access Token từ USER Access Token.
#
# Logic:
# 1. Đọc FB_USER_ACCESS_TOKEN từ .env.local.
# 2. Gọi POST /api/fb/exchange-token { userToken, longLived: true }.
# 3. Endpoint tự:
#    - Exchange short-lived → long-lived user token (60 ngày) qua oauth/access_token.
#    - Exchange user token → page token qua /me/accounts.
#    - Ghi page token + page ID vào .env.local + .env.
# 4. Restart LaunchAgent server để nhận token mới.
#
# Yêu cầu:
#   - FB_USER_ACCESS_TOKEN trong .env.local (lấy từ Graph API Explorer)
#   - FB_APP_ID + FB_APP_SECRET trong .env.local (để exchange sang long-lived)
#   - Server dashboard phải đang chạy port 3123.
#
# Usage:
#   ./scripts/refresh-token.sh            # mặc định update env + restart server
#   ./scripts/refresh-token.sh --no-restart  # chỉ exchange, không restart
#   ./scripts/refresh-token.sh --no-long-lived  # skip bước 1 (short → long), dùng user token hiện tại

set -e

PROJECT_DIR="/Users/bobo/ZCodeProject/facebook-page-graph-dashboard"
LOG_FILE="${PROJECT_DIR}/logs/token-refresh.log"
PORT="${PORT:-3123}"

mkdir -p "${PROJECT_DIR}/logs"

RESTART=1
LONG_LIVED=1
for arg in "$@"; do
  case "$arg" in
    --no-restart) RESTART=0 ;;
    --no-long-lived) LONG_LIVED=0 ;;
  esac
done

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

cd "${PROJECT_DIR}"

# 1. Đọc user token
USER_TOKEN=$(grep -E "^FB_USER_ACCESS_TOKEN=" .env.local | head -1 | sed 's/^FB_USER_ACCESS_TOKEN=//' | tr -d '\r\n"')
if [ -z "${USER_TOKEN}" ]; then
  log "✗ Thiếu FB_USER_ACCESS_TOKEN trong .env.local"
  log "  Hãy mở .env.local và dán user token (lấy từ Graph API Explorer) vào dòng FB_USER_ACCESS_TOKEN=..."
  exit 1
fi
log "→ User token tìm thấy trong .env.local (length: ${#USER_TOKEN})"

# 2. Check server đang chạy
if ! curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/api/env" | grep -q "200"; then
  log "✗ Server không chạy ở port ${PORT}. Hãy chạy ./scripts/agent-start.sh trước."
  exit 1
fi

# 3. Build JSON payload
PAYMENT_EXTRA=""
if [ "${LONG_LIVED}" = "1" ]; then
  PAYMENT_EXTRA=',"longLived":true'
fi
PAYLOAD="{\"userToken\":\"${USER_TOKEN}\"${PAYMENT_EXTRA}}"

# 4. Gọi exchange
log "→ Gọi POST /api/fb/exchange-token (longLived=${LONG_LIVED})..."
RESPONSE=$(curl -sS -X POST \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" \
  "http://localhost:${PORT}/api/fb/exchange-token")

# 5. Parse response
OK=$(echo "${RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "False")
if [ "${OK}" != "True" ]; then
  log "✗ Exchange failed:"
  echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  code:', d.get('error',{}).get('code','?')); print('  msg:', d.get('error',{}).get('message','?')[:200])" 2>/dev/null || echo "  ${RESPONSE}" | tee -a "${LOG_FILE}"
  exit 1
fi

log "✓ Exchange thành công:"
echo "${RESPONSE}" | python3 -c "
import sys, json, datetime as dt
d = json.load(sys.stdin)['data']
print(f'  Page: {d[\"pageName\"]} (id={d[\"pageId\"]})')
print(f'  Page token: {d[\"pageAccessTokenMasked\"]} (length: {d[\"pageAccessTokenLength\"]})')
if d.get('longLivedExpiresAt'):
  exp = dt.datetime.fromtimestamp(d['longLivedExpiresAt'])
  days = (exp - dt.datetime.now()).days
  print(f'  Long-lived expires: {exp.isoformat()} (còn {days} ngày)')
print(f'  envUpdated: {d[\"envUpdated\"]}')
if d.get('warning'):
  print(f'  warning: {d[\"warning\"]}')
" | tee -a "${LOG_FILE}"

# 6. Restart server
if [ "${RESTART}" = "1" ]; then
  log "→ Restart LaunchAgent server..."
  ./scripts/agent-start.sh 2>&1 | tail -3 | tee -a "${LOG_FILE}"
  sleep 5
  log "→ Verify server up..."
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/api/env")
  if [ "${HTTP}" = "200" ]; then
    log "✓ Server up (HTTP 200)"
  else
    log "✗ Server fail (HTTP ${HTTP})"
  fi
fi

log "✅ Refresh xong."
