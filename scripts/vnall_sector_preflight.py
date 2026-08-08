#!/usr/bin/env python3
"""VNALL SECTOR PREFLIGHT — P0-E (Sol checkpoint 2, 2026-08-08).
Tạo artifact sector cho 1.000 mã TRƯỚC build:
1. Listing().all_symbols() → ticker + tên công ty + sàn + ICB
2. Map ICB/industry → sector builder (đối chiếu MAP trong references/sector_pack.md)
3. Đối chiếu TÊN CÔNG TY với từ khóa ngành — mâu thuẫn → ghi fix list
4. Xuất /tmp/vnall_p0_sectors.json: {TICKER: sector} + /tmp/vnall_p0_sector_fix.json

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
    syms = Listing(source='vci').all_symbols()
    out, fixes, notes = {}, {}, []
    for _, r in syms.iterrows():
        tk = str(r.get('ticker', '')).upper()
        if not tk:
            continue
        name = str(r.get('organ_name') or r.get('organ_short_name') or r.get('company_name') or '').strip()
        ind = str(r.get('industry') or r.get('industry_en') or r.get('icb_name') or r.get('sector') or '').strip()
        exch = str(r.get('exchange') or r.get('com_type_code') or '')
        sec = map_icb_to_sector(ind) or 'general'
        # fix biết trước (Sol xác nhận): AGG=BĐS, BMI=bảo hiểm, SGR không phải ngân hàng
        known = {'AGG': 'realestate', 'BMI': 'insurance'}
        if tk in known:
            sec = known[tk]
        conflict = name_conflict(tk, name, sec)
        if conflict:
            fixes[tk] = {'name': name, 'icb': ind, 'mapped': sec, 'conflict': conflict}
            sec = 'needs_human'  # mâu thuẫn → chờ người, không tự đoán
        out[tk] = sec
        if exch and 'HNX' in exch.upper() and sec != 'needs_human':
            notes.append(f"HNX identity case: {tk} '{name}' -> {sec}")
            if len(notes) >= 3:
                notes = notes[:3]
    json.dump(out, open('/tmp/vnall_p0_sectors.json', 'w'), ensure_ascii=False)
    json.dump(fixes, open('/tmp/vnall_p0_sector_fix.json', 'w'), ensure_ascii=False, indent=1)
    cnt = collections.Counter(out.values())
    print('TOTAL:', len(out), '| sector phân bố:', dict(cnt.most_common(15)))
    print('MÂU THUẪN TÊN (needs_human):', len(fixes))
    for tk, f in list(fixes.items())[:10]:
        print(' -', tk, f['name'], '|', f['conflict'])
    print('HNX/UPCOM identity mẫu:', notes)

if __name__ == '__main__':
    main()
