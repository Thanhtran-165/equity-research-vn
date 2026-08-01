# LỆNH V6: HPG DỌN SẠCH RESIDUAL CTD (MỤC TIÊU ≥ 68/74)

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-01

---

## 1. Bối cảnh (đọc trước — 3 phút)

V5 đạt **63/74** (+9 nhờ copy CTD template) nhưng **89% fail còn lại là CTD residuals** —
số liệu CTD (PE 7.9, ROE 8.3, CAGR -18.2%, upside 35%) còn sót trong HTML HPG. Chính
bạn kết luận: *"mỗi lần em replace một con số, nó xuất hiện ở context khác (CSS,
narrative, chart label)"*.

**Kết luận của ZCode sau review V5:**
- REQ-025/036/060/061 bạn ghi "lỗi skill" — **KHÔNG phải** (bạn tự thừa nhận REQ-036 là
  "lỗi narrative (copy sai), KHÔNG phải verifier"). Verifier bắt ĐÚNG số 7.9/8.3 — vấn đề
  là các số đó KHÔNG ĐƯỢC tồn tại trong báo cáo HPG. **Sạch residual → các REQ này tự PASS.**
- Skill đã bổ sung quy tắc cấm copy báo cáo mã khác (phase6-dashboard.md Lesson #17) —
  từ giờ build từ template trắng.

**Nhiệm vụ lệnh này:** dọn SẠCH residual CTD trong báo cáo HPG hiện có → verify lại.

## 2. NHIỆM VỤ

1. **Grep toàn bộ residual CTD** trong `/tmp/cohort_v3_HPG/HPG_Complete_Report.html`:
2. Thay mỗi số bằng GIÁ TRỊ HPG TÍNH LẠI từ data files của HPG (KHÔNG đoán — tính từ
   financials.json / verified-dashboard-data.json / technical_active.json)
3. Verify → sửa → verify. Tối thiểu 2 vòng, tối đa 4. Mục tiêu **≥ 68/74**.

## 3. DANH SÁCH RESIDUAL CTD CẦN GREP (bắt buộc quét từng từ)

**Số đặc trưng CTD (thay bằng số HPG tương ứng):**

| Số CTD | Ý nghĩa | Số HPG thay thế |
|---|---|---|
| `7.9` / `7,9` | P/E CTD | P/E HPG = 11.0 (giá ÷ EPS 2025) |
| `8.3` / `8,3` | ROE CTD | ROE HPG ≈ 11.8% (tính từ financials) |
| `-18.2` / `-18,2` | CAGR CTD | CAGR HPG recompute (giá trị THẬT từ data — đừng viết bừa) |
| `35` (upside) | upside CTD | upside HPG tính lại từ median target |
| `61,000` | giá CTD | 21,700 (giá HPG) |
| `92,750` | đỉnh 52 tuần CTD | tech52wLow/đỉnh HPG từ technical_active.json |
| `114M` / `114` (triệu cp) | số CP CTD | số CP HPG (issue_share) |
| `6,954` | vốn hóa CTD | vốn hóa HPG |
| `7,736` / `3,729` / `2,267` | EPS CTD | EPS HPG: 1,973 (2025) |
| `82,328` | BVPS CTD | BVPS HPG |
| `-831` | CFO CTD | CFO HPG (2025) |
| `2.55%` | biên LNST CTD | biên LNST HPG |
| `-40.6` | drawdown CTD | -22.3 (HPG) |
| `3,396` | nợ ròng CTD | nợ ròng HPG |
| `526` (tỷ tranh chấp) | Ngôi Sao Việt | XÓA (không thuộc HPG) |

**Từ khóa CTD (kiểm tra context — peers hợp lệ thì giữ, narrative thì xóa):**
`Coteccons`, `Ngôi Sao Việt`, `nhà thầu`, `xây dựng`, `backlog`, `CTD`, `đầu tư công`,
`Tranh chấp` (nếu gắn NSV), `Dung Quất` (⚠️ ĐÂY LÀ HPG THẬT — GIỮ NGUYÊN).

## 4. QUY TRÌNH BẮT BUỘC

1. Grep danh sách mục 3 → ghi số lượng residual từng loại (báo cáo)
2. Thay bằng giá trị HPG TÍNH LẠI — ghi nguồn từng số (financials/technical/peers.json)
3. **Sau MỖI lần thay → grep LẠI toàn bộ danh sách** (residual di chuyển context —
   bài học V5: thay chỗ này, hiện chỗ kia)
4. Verify → ghi vòng log → sửa tiếp
5. Dừng khi ≥ 68/74 hoặc hết 4 vòng → báo cáo trung thực

## 5. RÀNG BUỘC

- ✗ Sửa source skill gốc
- ✗ Copy thêm HTML mã khác (báo cáo HPG hiện tại là nền — chỉ THAY SỐ, không copy mới)
- ✗ Bịa số khi không chắc — tính lại từ data, không thì ghi `null`
- ✗ Commit/push
- REQ-074 phải giữ PASS (P/E chuẩn hóa 12,39× + P/E raw 11,0× — không được phá)

## 6. BÁO CÁO (tạo `/tmp/COHORT-REPORT-GLM-V6.md` — NGẮN GỌN)

| Hạng mục | Nội dung |
|---|---|
| Recall cuối | x/74 + tiến trình vòng |
| Residual | Bảng: số CTD \| còn mấy chỗ \| đã thay thành gì (nguồn) |
| REQ fail cuối | id + lý do 1 dòng + phân loại |
| REQ-074 | PASS/FAIL |
| Maturity | ≥65/74 = đủ bằng chứng PRODUCTION_READY? |

## 7. TIÊU CHÍ THÀNH CÔNG

- **HPG ≥ 68/74**, residual CTD = 0 (grep không còn từ khóa mục 3)
- REQ-074 PASS
- Mọi fail còn lại phân loại rõ — nghi verifier phải kèm bằng chứng
