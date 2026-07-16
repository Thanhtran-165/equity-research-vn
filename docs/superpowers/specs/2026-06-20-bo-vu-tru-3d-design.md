# Spec thiết kế: BÒ VŨ TRỤ — Web 3D Showcase

- **Ngày:** 2026-06-20
- **Loại:** Showcase 3D nghệ thuật (single-page)
- **Ngôn ngữ UI:** Tiếng Việt
- **Trạng thái:** Đã duyệt ý tưởng, chờ review tài liệu

---

## 1. Mục đích & Đối tượng

Một trang web 3D full-screen trưng bày **con bò tót phát sáng neon** — biểu tượng
"bull market" (thị trường chứng khoán tăng giá) — đứng giữa **vũ trụ tài chính**. Mục
đích là tạo ấn tượng thị giác mạnh, nghệ thuật, tương tác, không gắn dữ liệu chứng
khoán thật (giá là giả lập để bò "sống động").

**Không phải:** dashboard giao dịch thật, landing page bán hàng, hay game có luật chơi.

---

## 2. Trải nghiệm tổng thể

Người dùng mở trang → thấy nền vũ trụ đen sâu, con bò low-poly phát sáng xanh đứng
trên một đĩa phát sáng, xoay nhẹ. Bảng giá "VN-INDEX" ở góc dao động liên tục. Khi di
chuyển chuột, đầu bò nhìn theo; khi kéo, cả bò xoay 360°; khi click, bò dậm chân húc
kèm hạt xanh bay tung và sóng lan. Khi giá tăng mạnh, bò rực sáng hơn; khi giảm, viền
chuyển đỏ và bò hơi chùng.

---

## 3. Con bò (Bull)

### 3.1 Hình dáng
- **Phong cách:** Low-poly tả thực, dựng bằng code Three.js (~25–30 mesh, không file
  GLB ngoài).
- **Tư thế:** Đứng nghiêng, dáng **húc về phía trước** — chân trước hạ thấp, đầu gục,
  sừng chĩa ra phía trước. Bướu vai nhô cao.
- **Các bộ phận:** thân to bè, bướu vai, đầu, 2 sừng cong nhọn, 4 chân vững, đuôi
  phe phẩy, 2 tai, đôi mắt.

### 3.2 Chất liệu & màu sắc (phong cách cyberpunk)
- **Thân:** tối gần đen `#0a0a18`, bề mặt hơi bóng như kim loại tối.
- **Viền neon quanh từng bộ phận:** xanh lá sáng `#00ff88` (màu tăng giá kinh điển).
- **Sừng & móng:** điểm nhấn vàng điện `#ffd700`.
- **Mắt:** đỏ rực phát sáng `#ff0044`.

### 3.3 Biến đổi theo trạng thái thị trường
| Trạng thái | Biểu hiện trên bò |
|---|---|
| Giá tăng mạnh (bull run) | Viền sáng rực hơn, toàn thân phát sáng xanh, bò đứng vững |
| Giá đi ngang | Phát sáng mức vừa, bò bình thường |
| Giá giảm (bear) | Viền chuyển đỏ `#ff3344`, bò hơi chùng xuống (nhưng vẫn đứng) |

### 3.4 Đổi màu (người dùng chủ động)
Nút "Đổi màu" cycle qua: **xanh lá → đỏ → tím → cyan** rồi quay lại xanh lá.
Chỉ đổi màu viền + mắt (sừng/móng giữ vàng).

---

## 4. Bối cảnh — Vũ trụ tài chính

Nhiều hiệu ứng (theo yêu cầu "nhiều hiệu ứng hơn"):

- **Nền:** đen sâu, gradient xanh-tím rất nhẹ ở chân.
- **Fog:** sương mù mờ xa tạo chiều sâu, làm bò nổi bật.
- **Sao:** hàng trăm điểm sáng nhỏ rải không gian xa, lấp lánh nhẹ.
- **Sao băng:** vệt sáng lao ngang xuất hiện ngẫu nhiên; xuất hiện nhiều hơn khi bò
  húc hoặc giá bùng nổ.
- **Đĩa phát sáng dưới bò:** đĩa tròn phẳng, phát sáng xanh nhạt, có đường vòng tròn
  đồng tâm (như radar/đồ thị) nhấp nháy, xoay chậm.
- **Candlestick xa:** vài dải thanh nến xanh/đỏ mờ trôi nhẹ ở xa, nhỏ, làm điểm nhấn
  bối cảnh (không gây rối).

---

## 5. Tương tác

### 5.1 Bò phản ứng theo con trỏ (luôn)
- **Di chuyển chuột (hover, không nhấn):** đầu bò xoay nhẹ nhìn theo con trỏ, mắt đỏ
  dõi theo.
- **Kéo chuột (nhấn + kéo):** xoay cả con bò 360° (OrbitControls, mượt, có quán tính).
  Trong lúc đang kéo, hiệu ứng "đầu nhìn theo con trỏ" tạm dừng để tránh xung đột;
  khi thả chuột, đầu lại nhìn theo.
- **Cuộn (scroll):** zoom vào/ra, có giới hạn (không xuyên bò, không đi quá xa).

### 5.2 Click = "cú húc bull"
- Click vào bò → bò **dậm chân trước + gục đầu húc**, kèm:
  - **vệt sóng xanh** lan ra từ chân trước,
  - **hạt xanh bay tung** (như giá bùng nổ),
  - một vài **sao băng** xuất hiện,
  - giá giả lập **nhảy lên**.

### 5.3 Thị trường tự dao động
- Dòng giá VN-INDEX chạy liên tục, dao động lên xuống ngẫu nhiên theo thuật toán
  "random walk" có xu hướng nhẹ lên (vì là *bull* market).
- Khi giá tăng mạnh: bò rực sáng + hạt xanh nhiều + sao băng.
- Khi giá giảm: viền bò đỏ + bò chùng.

### 5.4 Mobile (touch)
Mọi thao tác hoạt động bằng ngón tay: vuốt để xoay, chụm để zoom, tap để húc.

### 5.5 Âm thanh
**Không có** — tập trung hoàn toàn vào hình ảnh.

---

## 6. Giao diện chữ (UI overlay)

### 6.1 Bố cục
```
┌─────────────────────────────────────────────┐
│  🐂 BÒ VŨ TRỤ                    [BULL ▲]   │  header mờ
│                                              │
│              (con bò 3D ở giữa)              │
│                                              │
│  VN-INDEX  1,247.5  ▲ +2.3%   [🎨 Đổi màu]  │  footer glass
│  Kéo để xoay · Click để húc                   │
└─────────────────────────────────────────────┘
```

### 6.2 Các thành phần
| Vị trí | Nội dung |
|---|---|
| Trên trái | Tên "BÒ VŨ TRỤ" + logo bò nhỏ, viền phát sáng xanh |
| Trên phải | Chỉ báo trạng thái `BULL ▲` (xanh) / `BEAR ▬` (đỏ), nhấp nháy theo giá |
| Dưới trái | Bảng giá `VN-INDEX` + % tăng/giảm, đổi màu xanh/đỏ |
| Dưới phải | Nút "Đổi màu" (cycle xanh→đỏ→tím→cyan) |
| Giữa dưới | Hướng dẫn "Kéo để xoay · Click để húc", tự ẩn sau 5 giây |

### 6.3 Phong cách
- **Glassmorphism:** nền mờ kính, viền mỏng, blur nền.
- **Font tiêu đề (tên, trạng thái):** tech góc cạnh — Rajdhani hoặc Orbitron.
- **Font nội dung (giá, hướng dẫn):** sans-serif sạch — Be Vietnam Pro.
- Mọi chữ tiếng Việt (có dấu).

---

## 7. Kiến trúc kỹ thuật

### 7.1 Tech stack
- **Three.js** (thuần, không R3F) + **Vite**.
- Three.js addons: OrbitControls, UnrealBloomPass (EffectComposer) cho glow neon.

### 7.2 Cấu trúc thư mục
```
bull-universe/
├── index.html              # Entry: canvas + UI overlay
├── package.json            # vite + three
├── vite.config.js
├── src/
│   ├── main.js             # Bootstrap: khởi tạo scene + loop
│   ├── scene/
│   │   ├── SceneManager.js # scene, camera, renderer, resize
│   │   ├── Lighting.js     # ánh sáng + fog vũ trụ
│   │   └── PostFX.js       # bloom (UnrealBloomPass)
│   ├── entities/
│   │   ├── Bull.js         # dựng bò low-poly + material neon
│   │   ├── Universe.js     # nền sao, sao băng, đĩa, candlestick
│   │   └── Particles.js    # hạt khi giá tăng / húc
│   ├── controls/
│   │   ├── CameraControls.js  # OrbitControls giới hạn góc
│   │   └── PointerReactor.js  # bò nhìn theo chuột + click húc
│   ├── state/
│   │   └── MarketState.js     # giá VN-INDEX giả lập (random walk)
│   └── ui/
│       ├── overlay.js      # DOM overlay: giá, nút, trạng thái
│       └── style.css       # typography + glassmorphism
└── public/
    └── favicon.svg
```

### 7.3 Luồng dữ liệu & render loop
```
MarketState (giá dao động)
   ├─→ Bull: đổi cường độ/màu phát sáng theo giá
   ├─→ Particles: sinh hạt khi giá tăng mạnh
   └─→ UI overlay: hiện giá + % + trạng thái BULL/BEAR

PointerReactor (chuột/touch)
   ├─→ Bull: đầu nhìn theo con trỏ
   └─→ (click) → Bull.huc() + Particles.burst() + MarketState.boost()

Render loop (requestAnimationFrame):
   MarketState.tick() → PointerReactor.update() → Bull.update()
   → Particles.update() → Universe.update() → renderer.render() [qua PostFX bloom]
```

### 7.4 Giao diện giữa các module
- `MarketState`: `{ value, delta, trend }`, phương thức `tick()`, `boost(amount)`,
  sự kiện `change`.
- `Bull`: `update(marketState)`, `lookAt(pointerNDC)`, `huc()`, `setColor(palette)`.
- `Particles`: `burst(count, color)`, `update()`.
- `Universe`: `spawnShootingStar(count)`, `update(marketState)`.
- `PointerReactor`: nhận renderer DOM element + camera, gọi callback của Bull.

---

## 8. Hiệu năng & Tương thích

- **Mục tiêu:** 60fps trên laptop tầm trung, 30fps+ trên điện thoại phổ thông.
- **Giảm tải:** giới hạn số hạt, số sao; tắt bloom tự động trên thiết bị yếu (qua
  `devicePixelRatio` + `navigator.hardwareConcurrency`).
- **Resize:** camera aspect + renderer cập nhật khi đổi kích thước cửa sổ.
- **Touch:** pointer events (gộp chuột + touch), pinch-to-zoom qua OrbitControls.

---

## 9. Phạm vi (Scope) — có/không

**Có:**
- Bò 3D low-poly neon tự dựng, biến đổi màu theo giá.
- Vũ trụ nhiều hiệu ứng (sao, sao băng, đĩa, candlestick mờ).
- Tương tác chuột/touch đầy đủ, click húc + hạt.
- Bảng giá VN-INDEX giả lập, nút đổi màu, UI glassmorphism 2 font.
- Mobile-friendly, giảm tải hiệu năng.

**Không (YAGNI):**
- Không dữ liệu chứng khoán thật (không gọi API).
- Không âm thanh.
- Không đăng nhập/ưu thích/lưu trạng thái người dùng.
- Không nhiều trang/routing (single-page).
- Không i18n tự động (chỉ tiếng Việt, có dấu).

---

## 10. Tiêu chí hoàn thành

1. Mở trang → thấy bò phát sáng giữa vũ trụ, xoay nhẹ, bảng giá chạy.
2. Kéo chuột xoay bò 360°, cuộn zoom, di chuyển chuột → đầu bò nhìn theo.
3. Click bò → húc + sóng + hạt + sao băng + giá nhảy.
4. Giá tăng mạnh → bò rực sáng + hạt nhiều; giá giảm → viền đỏ + bò chùng.
5. Nút đổi màu cycle đúng 4 màu; chỉ báo BULL/BEAR đổi theo giá.
6. Chạy mượt ≥30fps trên điện thoại; UI tiếng Việt có dấu, glassmorphism, 2 font.
