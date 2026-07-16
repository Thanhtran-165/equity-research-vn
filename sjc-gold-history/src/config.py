"""Constants and metadata for gold price types and branches.

These IDs are the `goldPriceId` values used by sjc.com.vn's PriceService.ashx
`GetGoldPriceHistory` method. They were reverse-engineered from the
`<select id="select-province">` on https://sjc.com.vn/bieu-do-gia-vang.

Each ID maps a (branch, gold type) pair. ID 1 = the canonical "Hồ Chí Minh —
Vàng SJC 1L, 10L, 1KG" used as the headline SJC price.
"""
# (id, branch, type_name) — order matches the site's <select>.
GOLD_PRICE_IDS = [
    (1,   "Hồ Chí Minh", "Vàng SJC 1L, 10L, 1KG"),
    (17,  "Hồ Chí Minh", "Vàng SJC 5 chỉ"),
    (33,  "Hồ Chí Minh", "Vàng SJC 0.5 chỉ, 1 chỉ, 2 chỉ"),
    (49,  "Hồ Chí Minh", "Vàng nhẫn SJC 99,99% 1 chỉ, 2 chỉ, 5 chỉ"),
    (65,  "Hồ Chí Minh", "Vàng nhẫn SJC 99,99% 0.5 chỉ, 0.3 chỉ"),
    (81,  "Hồ Chí Minh", "Nữ trang 99,99%"),
    (97,  "Hồ Chí Minh", "Nữ trang 99%"),
    (113, "Hồ Chí Minh", "Nữ trang 75%"),
    (129, "Hồ Chí Minh", "Nữ trang 68%"),
    (210, "Hồ Chí Minh", "Nữ trang 61%"),
    (145, "Hồ Chí Minh", "Nữ trang 58,3%"),
    (161, "Hồ Chí Minh", "Nữ trang 41,7%"),
    (2,   "Miền Bắc",    "Vàng SJC 1L, 10L, 1KG"),
    (13,  "Hạ Long",     "Vàng SJC 1L, 10L, 1KG"),
    (177, "Hải Phòng",   "Vàng SJC 1L, 10L, 1KG"),
    (188, "Miền Trung",  "Vàng SJC 1L, 10L, 1KG"),
    (7,   "Huế",         "Vàng SJC 1L, 10L, 1KG"),
    (10,  "Quảng Ngãi",  "Vàng SJC 1L, 10L, 1KG"),
    (4,   "Nha Trang",   "Vàng SJC 1L, 10L, 1KG"),
    (8,   "Biên Hòa",    "Vàng SJC 1L, 10L, 1KG"),
    (9,   "Miền Tây",    "Vàng SJC 1L, 10L, 1KG"),
    (16,  "Bạc Liêu",    "Vàng SJC 1L, 10L, 1KG"),
    (5,   "Cà Mau",      "Vàng SJC 1L, 10L, 1KG"),
]

# Canonical headline SJC price (1L in HCM) — the default.
DEFAULT_GOLD_PRICE_ID = 1

# sjc.com.vn API rejects windows >= 90 days ("Chỉ được xem Giá trong khoảng
# dưới 90 ngày"). Use 89 to stay safely under the limit (90 itself is rejected).
MAX_WINDOW_DAYS = 89

# Earliest date with data on sjc.com.vn (verified by probing the API).
EARLIEST_DATE = "2009-07-22"

# Endpoints
SJC_URL = "https://sjc.com.vn/bieu-do-gia-vang"
PRICE_SERVICE_URL = "https://sjc.com.vn/GoldPrice/Services/PriceService.ashx"
