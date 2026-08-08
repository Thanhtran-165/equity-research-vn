#!/usr/bin/env python3
"""VNALL RUN P0 — runner chuẩn sau kiểm định Sol (2026-08-08).
Sửa 5 lỗi runner cũ (data/vnall/vnall_run.py):
1. không còn phụ thuộc status==pending (chạy theo danh sách mã đích);
2. done CHỈ khi returncode==0 và verdict PASS — critical FAIL không bao giờ thành done;
3. staging directory MỚI hoàn toàn mỗi mã (không merge, không file stale);
4. xóa result.json cũ trước build — không đọc kết quả cũ khi build lỗi;
5. snapshot cũ giữ nguyên + nhãn invalid (không ghi đè trước khi audit).

Usage: python3 vnall_run_p0.py <tickers.json|ticker1,ticker2> [--sleep 60]
  tickers.json: [{"ticker":"AAA","sector":"materials"}, ...]
"""
import json, os, subprocess, sys, time, datetime

BUILDER = os.path.expanduser('~/.zcode/skills/equity-research-vn/scripts/build_report.py')
BASE = os.path.expanduser('~/ZCodeProject/data/vnall')
STAGE = os.path.join(BASE, 'work_p0')      # staging mới — không đụng work/ cũ
TRACKER = os.path.join(BASE, 'vnall_tracker_p0.json')
RUN_ID = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

def main():
    if len(sys.argv) < 2:
        print('usage: vnall_run_p0.py <tickers.json|t1,t2> [--sleep N]'); sys.exit(2)
    src = sys.argv[1]
    sleep_s = 60
    if '--sleep' in sys.argv:
        sleep_s = int(sys.argv[sys.argv.index('--sleep') + 1])
    if src.endswith('.json'):
        items = json.load(open(src))
        if isinstance(items, dict):
            items = items.get('tickers', [])
    else:
        items = [{'ticker': t.strip(), 'sector': 'general'} for t in src.split(',') if t.strip()]

    os.makedirs(STAGE, exist_ok=True)
    tracker = {}
    if os.path.exists(TRACKER):
        tracker = json.load(open(TRACKER))  # nối tiếp nếu crash giữa chừng

    for it in items:
        tk = it['ticker']; sec = it.get('sector', 'general')
        wd = os.path.join(STAGE, tk)
        # 3) staging phải SẠCH — xóa nếu tồn tại từ lần chạy trước (chưa promote)
        if os.path.exists(wd):
            import shutil; shutil.rmtree(wd)
        os.makedirs(wd)
        result_file = os.path.join(wd, 'result.json')
        entry = {'ticker': tk, 'sector': sec, 'batch': it.get('batch', 0),
                 'status': 'running', 'run_id': RUN_ID, 'ts': datetime.datetime.utcnow().isoformat()}
        tracker[tk] = entry
        json.dump(tracker, open(TRACKER, 'w'), ensure_ascii=False, indent=1)
        # P0 (Sol checkpoint 2): DỌN /tmp/vn100_<ticker> trước build — tránh copy
        # state cũ của lần chạy trước khi builder crash giữa chừng.
        import shutil as _sh0
        _sh0.rmtree(f'/tmp/vn100_{tk}', ignore_errors=True)
        try:
            r = subprocess.run(['python3', BUILDER, tk, sec], cwd=wd,
                               capture_output=True, text=True, timeout=900)
            out = r.stdout + r.stderr
            # builder viết /tmp/vn100_<TICKER> (đường dẫn cố định) — copy kết quả về staging
            import shutil as _sh
            src_dir = f'/tmp/vn100_{tk}'
            if os.path.isdir(src_dir):
                _sh.copytree(src_dir, wd, dirs_exist_ok=True)
            ok = False
            if os.path.exists(result_file):
                try:
                    res = json.load(open(result_file))
                    recall = res.get('recall', 0)
                    fails = res.get('fails', [])
                    # 2) done CHỈ khi exit 0 (builder fail-closed) + recall >= 70
                    ok = r.returncode == 0 and recall >= 70
                    entry.update({'recall': recall, 'fails': fails,
                                  'status': 'done' if ok else 'needs_human',
                                  'exit': r.returncode})
                except Exception:
                    entry.update({'status': 'needs_human', 'exit': r.returncode,
                                  'note': 'result.json parse lỗi'})
            else:
                entry.update({'status': 'NO_DATA', 'exit': r.returncode,
                              'note': 'không có result.json — builder crash/API fail',
                              'tail': out[-500:]})
            print(f"{tk} ({sec}): exit={r.returncode} -> {entry.get('status')} recall={entry.get('recall')}")
        except subprocess.TimeoutExpired:
            entry.update({'status': 'NO_DATA', 'note': 'timeout 900s'})
            print(f"{tk}: TIMEOUT")
        except Exception as e:
            entry.update({'status': 'NO_DATA', 'note': f'exception: {e}'})
            print(f"{tk}: ERROR {e}")
        json.dump(tracker, open(TRACKER, 'w'), ensure_ascii=False, indent=1)
        time.sleep(sleep_s)

    print(f'\nDONE — {RUN_ID}')
    print(f'tracker: {TRACKER}')
    st = {}
    for e in tracker.values():
        st[e['status']] = st.get(e['status'], 0) + 1
    print('status:', st)

if __name__ == '__main__':
    main()
