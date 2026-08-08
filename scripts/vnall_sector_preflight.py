#!/usr/bin/env python3
"""VNALL SECTOR PREFLIGHT v2 — P0-E (Sol checkpoint 3, 2026-08-08).
Tạo artifact sector cho 1.000 mã TRƯỚC build, từ 3 nguồn vnstock:
  all_symbols()          → ticker + tên công ty
  symbols_by_industries()→ ICB (lọc STOCK, cấp sâu nhất)
  symbols_by_exchange()  → sàn
Fail-closed: coverage general > 10% hoặc mã pilot còn needs_human → exit 1.

Usage: python3 vnall_sector_preflight.py
"""
import json, re, sys, collections

NAME_KW = [
    ('banking', ['ngân hàng', 'bank']),
    ('securities', ['chứng khoán', 'securities']),
    ('insurance', ['bảo hiểm', 'insurance']),
    ('realestate', ['bất động sản', 'real estate', 'đầu tư và phát triển đô thị', 'vinhomes', 'nhà ở']),
    ('steel', ['thép', 'steel']),
    ('retail', ['bán lẻ', 'retail', 'thế giới di động', 'đầu tư thế giới']),
    ('energy', ['điện', 'power', 'petrol', 'xăng dầu', 'khí', 'gas', 'dầu khí', 'dầu']),
    ('pharma', ['dược', 'pharma']),
    ('transport', ['cảng', 'hàng không', 'airline', 'vận tải', 'logistics']),
    ('consumer', ['thực phẩm', 'sữa', 'bánh kẹo', 'nước giải khát', 'bia', 'food']),
    ('materials', ['phân bón', 'hóa chất', 'xi măng', 'cao su', 'cement', 'chemical']),
    ('industrial', ['cơ khí', 'nhựa', 'plastic', 'bao bì', 'sản xuất', 'may', 'textile', 'dệt', 'gỗ']),
]

PILOT = {'AAA', 'ACB', 'BMI', 'FPT', 'AGG', 'SGR'}


def map_icb_to_sector(ind):
    """ICB/industry string → sector builder (khớp SECTOR_MAP builder)."""
    i = (ind or '').lower()
    table = [
        ('bank', 'banking'), ('real estate', 'realestate'), ('realestate', 'realestate'),
        ('steel', 'steel'), ('materials', 'materials'), ('chemical', 'materials'),
        ('retail', 'retail'), ('consumer', 'consumer'), ('food', 'consumer'),
        ('securities', 'securities'), ('finance', 'securities'), ('insurance', 'insurance'),
        ('energy', 'energy'), ('oil', 'energy'), ('gas', 'energy'), ('utilities', 'energy'), ('power', 'energy'),
        ('transport', 'transport'), ('logistics', 'transport'), ('airline', 'transport'),
        ('pharma', 'pharma'), ('health', 'pharma'), ('tech', 'tech'), ('technology', 'tech'),
        ('telecom', 'tech'), ('industrial', 'industrial'), ('construction', 'realestate'),
        ('property', 'realestate'),
    ]
    for kw, sec in table:
        if kw in i:
            return sec
    return None


def name_conflict(ticker, name, sec):
    """Tên công ty mâu thuẫn với sector → ghi chú."""
    n = (name or '').lower()
    for kw_sec, kws in NAME_KW:
        if any(k in n for k in kws):
            if kw_sec != sec:
                return f"tên '{name}' gợi ý {kw_sec} nhưng ICB map ra {sec}"
    return None


def main():
    from vnstock_data import Listing
    l = Listing(source='vci')
    syms = l.all_symbols()
    inds = l.symbols_by_industries()
    try:
        exs = l.symbols_by_exchange()
    except Exception as e:
        exs = None
        print('WARN: symbols_by_exchange lỗi:', str(e)[:80], file=sys.stderr)

    # ICB: lọc STOCK, cấp sâu nhất mỗi symbol
    icb = {}
    if inds is not None and hasattr(inds, 'iterrows'):
        for _, r in inds.iterrows():
            if str(r.get('com_type_code', '')).strip().upper() in ('QU', 'FU', 'ET', 'CW'):
                continue
            sym = str(r.get('symbol', '')).upper()
            try:
                lvl = int(r.get('icb_level', 1))
            except (TypeError, ValueError):
                lvl = 1
            nm = str(r.get('icb_name', '')).strip()
            cur = icb.get(sym)
            if cur is None or lvl > cur[0]:
                icb[sym] = (lvl, nm)
    exch_map = {}
    if exs is not None and hasattr(exs, 'iterrows'):
        for _, r in exs.iterrows():
            sym = str(r.get('symbol', '')).upper()
            exch_map[sym] = str(r.get('exchange') or r.get('com_type_code') or '').strip()

    out, fixes = {}, {}
    for _, r in syms.iterrows():
        tk = str(r.get('ticker', '')).upper()
        if not tk:
            continue
        name = str(r.get('organ_name') or r.get('organ_short_name') or r.get('company_name') or '').strip()
        ind = (icb.get(tk) or (None, ''))[1]
        exch = exch_map.get(tk, '')
        sec = map_icb_to_sector(ind) or 'general'
        known = {'AGG': 'realestate', 'BMI': 'insurance'}  # fix biết trước (Sol xác nhận)
        if tk in known:
            sec = known[tk]
        conflict = name_conflict(tk, name, sec)
        if conflict:
            fixes[tk] = {'name': name, 'icb': ind, 'exchange': exch, 'mapped': sec, 'conflict': conflict}
            sec = 'needs_human'  # mâu thuẫn → chờ người, không tự đoán
        out[tk] = sec

    json.dump(out, open('/tmp/vnall_p0_sectors.json', 'w'), ensure_ascii=False)
    json.dump(fixes, open('/tmp/vnall_p0_sector_fix.json', 'w'), ensure_ascii=False, indent=1)
    cnt = collections.Counter(out.values())
    print('TOTAL:', len(out), '| sector phân bố:', dict(cnt.most_common(15)))
    general_n = cnt.get('general', 0)
    if general_n / max(len(out), 1) > 0.10:
        print(f'FAIL-CLOSED: {general_n} mã general ({general_n / max(len(out), 1) * 100:.0f}%) > 10% — '
              f'ICB/sàn thiếu. Kiểm tra API trước khi chạy.')
        sys.exit(1)
    pilot_nh = [tk for tk in PILOT if out.get(tk) == 'needs_human']
    if pilot_nh:
        print(f'FAIL-CLOSED: mã pilot còn needs_human: {pilot_nh} — phải xử lý tay trước.')
        sys.exit(1)
    print('PREFLIGHT OK — coverage đạt, pilot sạch needs_human')


if __name__ == '__main__':
    main()
