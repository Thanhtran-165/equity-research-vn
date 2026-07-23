# ⚠️ DISCLAIMER — Quan trọng

## Không phải lời khuyên đầu tư

Bộ skill `equity-research-vn` này là **công cụ giáo dục và tham khảo** để phân tích cổ phiếu Việt Nam. Nó KHÔNG phải là:

- ❌ Lời khuyên đầu tư cá nhân (financial advice)
- ❌ Khuyến nghị mua/bán cổ phiếu cụ thể
- ❌ Cam kết tính chính xác tuyệt đối của số liệu
- ❌ Thay thế tư vấn từ chuyên gia tài chính có giấy phép

## Rủi ro khi sử dụng

1. **Số liệu có thể sai hoặc chậm** — Dữ liệu từ vnstock API, CafeF, Vietstock có thể:
   - Bị trễ (delayed) so với real-time
   - Chứa lỗi (data quality issues)
   - Bị thay đổi sau khi kiểm toán (restated)

2. **Phân tích có thể sai** — Các phương pháp định giá (DCF, PE/PB, Graham) dựa trên giả định có thể không xảy ra. Kết luận "OVERVALUED/UNDERVALUED" là **ý kiến dựa trên data**, không phải sự thật.

3. **Cổ phiếu chu kỳ** — Nhiều cổ phiếu VN (thép, dầu khí, BĐS) là chu kỳ — biến động mạnh. Phân tích "hợp lý" hôm nay có thể sai trong 3-6 tháng.

4. **AI có thể hallucinate** — Agent chạy skill này (GLM, GPT, Claude) có thể hiểu sai context hoặc tạo số liệu không có. **Luôn verify số liệu quan trọng** từ BCTC kiểm toán chính thức.

## Cách sử dụng an toàn

✅ Dùng như **điểm khởi đầu** để hiểu doanh nghiệp — không phải kết luận cuối cùng

✅ **Cross-check số liệu** từ ít nhất 2 nguồn trước khi ra quyết định đầu tư

✅ Đọc **BCTC kiểm toán chính thức** từ trang QHCD doanh nghiệp (bsr.com.vn, hpg.com.vn...)

✅ Tham khảo **nhiều báo cáo CTCK** (VCBS, MBS, BSC, VIX...) — không tin 1 nguồn

✅ Hiểu **ngành đặc thù** trước khi định giá (crack spread cho lọc dầu, NIM cho ngân hàng...)

❌ KHÔNG mua/bán cổ phiếu chỉ dựa trên output của skill này

❌ KHÔNG dùng cho day-trading — data có thể delayed

❌ KHÔNG tin target price từ skill — đây chỉ là ước tính dựa trên giả định

## Trách nhiệm

Người dùng chịu hoàn toàn trách nhiệm về quyết định đầu tư của mình. Tác giả skill không chịu trách nhiệm cho bất kỳ khoản lỗ nào phát sinh từ việc sử dụng skill này.

**Đầu tư cổ phiếu có rủi ro mất vốn. Chỉ đầu tư số tiền bạn có thể chấp nhận mất.**

---

## Data sources attribution

Skill này sử dụng dữ liệu từ các nguồn công khai:

- **vnstock** (https://vnstocks.com) — open-source Python library lấy data HOSE/HNX/UPCoM
- **CafeF** (https://cafef.vn) — tin tức và số liệu tài chính
- **Vietstock** (https://vietstock.vn) — báo cáo tài chính và tỷ số
- **BSR Portal** (https://bsr.com.vn) — BCTC chính thức Bình Sơn
- **yfinance** — giá dầu Brent/WTI từ Yahoo Finance

Mọi trademark thuộc về chủ sở hữu tương ứng.
