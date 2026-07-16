// src/data/timeline.mjs — bilingual parallel timeline
export const TIMELINE = {
  layers: [
    {
      id: "geopolitics",
      label: { vi: "Địa chính trị", en: "Geopolitics" },
      color: "var(--chart-line-4)",
      historical: [
        { date: "1967-06", text: { vi: "Chiến tranh 6 ngày; bộ trưởng dầu Ả Rập bắt đầu phối hợp.", en: "Six-Day War; Arab oil ministers begin coordinating." } },
        { date: "1973-10", text: { vi: "Chiến tranh Yom Kippur; cấm vận dầu OAPEC chống Mỹ/Hà Lan.", en: "Yom Kippur War; OAPEC oil embargo against US/Netherlands." } },
        { date: "1979-01", text: { vi: "Cách mạng Iran; xuất khẩu dầu Iran sụp.", en: "Iranian Revolution; Iranian oil exports collapse." } },
        { date: "1979-11", text: { vi: "Mỹ bị bắt con tin tại Tehran.", en: "US embassy hostages taken in Tehran." } },
        { date: "1980-09", text: { vi: "Chiến tranh Iran–Iraq bắt đầu; sản lượng dầu cả hai giảm.", en: "Iran–Iraq War begins; oil production in both drops." } },
        { date: "1983-09", text: { vi: "Bắn rơi Korean Air 007; căng thẳng Chiến tranh lạnh đỉnh.", en: "Korean Air 007 shootdown; Cold War tensions peak." } },
      ],
      current: [
        { date: "2020-01", text: { vi: "COVID-19 tuyên bố khẩn cấp y tế (WHO).", en: "COVID-19 declared public health emergency (WHO)." } },
        { date: "2022-02", text: { vi: "Nga xâm lược Ukraine; trừng phạt dầu/tài chính Nga.", en: "Russia invades Ukraine; sanctions on Russian oil/finance." } },
        { date: "2023-10", text: { vi: "Chiến tranh Hamas–Israel; rủi ro leo thang khu vực.", en: "Hamas–Israel war; risk of regional escalation." } },
        { date: "2024-04", text: { vi: "Trao đổi tên lửa trực tiếp Iran–Israel; repricing rủi ro Hormuz.", en: "Direct Iran–Israel missile exchanges; Hormuz risk repriced." } },
        { date: "2024-07", text: { vi: "Vụ ám sát; biến động bầu cử Mỹ.", en: "Assassination attempts; US election volatility." } },
      ],
    },
    {
      id: "energy",
      label: { vi: "Năng lượng", en: "Energy" },
      color: "var(--chart-line)",
      historical: [
        { date: "1973-10", text: { vi: "Cấm vận dầu; giá tăng gấp bốn lên ~$12/bbl.", en: "Oil embargo; price quadruples to ~$12/bbl." } },
        { date: "1979", text: { vi: "Cú sốc dầu thứ hai; crude đạt ~$40/bbl vào 1980.", en: "Second oil shock; crude hits ~$40/bbl by 1980." } },
        { date: "1981", text: { vi: "Giải kiểm soát giá dầu Mỹ hoàn tất; bùng nổ khoan bắt đầu.", en: "US oil price decontrol completed; drilling boom begins." } },
        { date: "1983", text: { vi: "Futures WTI ra mắt NYMEX.", en: "WTI crude futures launch on NYMEX." } },
      ],
      current: [
        { date: "2020-04", text: { vi: "WTI briefly âm; cầu sụp từ lockdown.", en: "WTI briefly negative; demand collapses from lockdowns." } },
        { date: "2021-10", text: { vi: "Khủng hoảng khí châu Âu; TTF spike >€150/MWh.", en: "European gas crisis; TTF spikes >€150/MWh." } },
        { date: "2022-02", text: { vi: "Chiến tranh Nga-Ukraine; Brent >$130/bbl tháng 3.", en: "Russia–Ukraine war; Brent >$130/bbl in March." } },
        { date: "2023", text: { vi: "Cắt sản xuất OPEC+; Saudi cắt đơn phương.", en: "OPEC+ production cuts; Saudi unilateral cut." } },
        { date: "2024-06", text: { vi: "OPEC+ kéo dài cắt tự nguyện; công suất dự phòng mỏng.", en: "OPEC+ extends voluntary cuts; spare capacity thin." } },
      ],
    },
    {
      id: "commodities",
      label: { vi: "Hàng hóa", en: "Commodities" },
      color: "var(--chart-line-3)",
      historical: [
        { date: "1971-08", text: { vi: "Nixon kết thúc convertibility vàng; vàng bắt đầu chạy từ $35.", en: "Nixon ends gold convertibility; gold begins its run from $35." } },
        { date: "1973-74", text: { vi: "Lúa mì/ngô tăng; deal grain Soviet + mùa vụ kém.", en: "Wheat/corn surge; Soviet grain deals + poor harvests." } },
        { date: "1979-80", text: { vi: "Vàng đỉnh $850 (1/1980); bạc bị corner (Hunt brothers).", en: "Gold peaks at $850 (Jan 1980); silver cornered (Hunt brothers)." } },
        { date: "1982", text: { vi: "Giá hàng hóa sụp khi suy thoái Volcker sâu.", en: "Commodity prices collapse as Volcker recession deepens." } },
      ],
      current: [
        { date: "2020-08", text: { vi: "Vàng phá $2,000/oz lần đầu.", en: "Gold breaks $2,000/oz for the first time." } },
        { date: "2022-03", text: { vi: "Nickel short-squeeze LME; lúa mì nhân đôi do chiến tranh Ukraine.", en: "Nickel short-squeeze on LME; wheat doubles on Ukraine war." } },
        { date: "2023-10", text: { vi: "Uranium >$70/lb; move đầu tiên bền vững kể từ Fukushima.", en: "Uranium >$70/lb; first sustained move since Fukushima." } },
        { date: "2024", text: { vi: "Vàng liên tục phá đỉnh (> $2,700/oz); đồng chặt.", en: "Gold repeatedly breaks record highs (> $2,700/oz); copper tightness." } },
      ],
    },
    {
      id: "inflation",
      label: { vi: "Lạm phát", en: "Inflation" },
      color: "var(--chart-line-4)",
      historical: [
        { date: "1971-08", text: { vi: "Kiểm soát giá tiền lương áp đặt.", en: "Wage–price controls imposed." } },
        { date: "1974", text: { vi: "CPI headline >12% hậu cấm vận.", en: "Headline CPI >12% post-embargo." } },
        { date: "1979-80", text: { vi: "CPI đỉnh 14.8% (3/1980).", en: "CPI peaks 14.8% (Mar 1980)." } },
        { date: "1982", text: { vi: "Lạm phát hạ dưới 4% khi suy thoái cắn.", en: "Inflation falls below 4% as recession bites." } },
      ],
      current: [
        { date: "2021-04", text: { vi: "CPI nhảy; ban đầu framed 'transitory'.", en: "CPI jumps; initially framed as 'transitory'." } },
        { date: "2022-06", text: { vi: "CPI đỉnh 9.1% YoY.", en: "CPI peaks 9.1% YoY." } },
        { date: "2023-06", text: { vi: "Headline hạ 3%; core dính ~4-5%.", en: "Headline falls to 3%; core sticky around 4–5%." } },
        { date: "2024", text: { vi: "Dịch vụ core ex-shelter chậm nhưng shelter dính.", en: "Core services ex-shelter slow but shelter inflation sticky." } },
      ],
    },
    {
      id: "fed",
      label: { vi: "Chính sách tiền tệ", en: "Monetary policy" },
      color: "var(--chart-line-2)",
      historical: [
        { date: "1970-02", text: { vi: "Burns thành chủ tịch Fed; áp lực chính trị nới lỏng.", en: "Burns becomes Fed chair; political pressure to ease." } },
        { date: "1979-08", text: { vi: "Volcker thành chủ tịch; dịch chuyển monetary-targeting.", en: "Volcker becomes chair; monetary-targeting shift." } },
        { date: "1979-10", text: { vi: "'Saturday Night Special' — bỏ target Fed funds; lãi suất bay.", en: "'Saturday Night Special' — Fed funds target abandoned; rate soars." } },
        { date: "1981", text: { vi: "Fed funds >19%; suy thoái sâu.", en: "Fed funds >19%; deep recession." } },
      ],
      current: [
        { date: "2020-03", text: { vi: "Fed cắt zero; QE4 + facility repo.", en: "Fed cuts to zero; QE4 + repo facilities launched." } },
        { date: "2022-03", text: { vi: "Tăng đầu tiên chu kỳ (từ zero).", en: "First hike of cycle (from zero)." } },
        { date: "2023-07", text: { vi: "Lãi suất đạt 5.25-5.50%; giữ đó.", en: "Rates reach 5.25–5.50%; held there." } },
        { date: "2024-09", text: { vi: "Cắt 50bp đầu tiên; runoff bảng cân đối tiếp.", en: "First 50bp cut; balance-sheet runoff continues." } },
      ],
    },
    {
      id: "japan",
      label: { vi: "Nhật Bản / yen", en: "Japan / yen" },
      color: "var(--chart-line-5)",
      historical: [
        { date: "1971-12", text: { vi: "Smithsonian Agreement; yen đánh giá lại.", en: "Smithsonian Agreement; yen revalued." } },
        { date: "1978", text: { vi: "Yen mạnh sắc; BOE lo cho nhà xuất khẩu.", en: "Yen strengthens sharply; BOJ concern over exporters." } },
        { date: "1985-09", text: { vi: "Plaza Accord; phối hợp yen/d-mark mạnh vs dollar.", en: "Plaza Accord; coordinated yen/d-mark appreciation vs dollar." } },
      ],
      current: [
        { date: "2022-12", text: { vi: "BOJ mở rộng band YCC — nước đi surprise.", en: "BOJ widens YCC band — surprise move." } },
        { date: "2024-03", text: { vi: "BOJ kết thúc lãi suất âm; tăng đầu tiên 17 năm.", en: "BOJ ends negative rates; first hike in 17 years." } },
        { date: "2024-07", text: { vi: "Tăng thứ hai; USD/JPY >160 rồi đảo sắc.", en: "Second hike; USD/JPY >160 then reverses sharply." } },
        { date: "2024-08", text: { vi: "Yen carry unwind; spike VIX 5/8.", en: "Yen carry unwind; VIX spike Aug 5." } },
      ],
    },
    {
      id: "tech",
      label: { vi: "Công nghệ", en: "Technology" },
      color: "var(--chart-line-3)",
      historical: [
        { date: "1971-11", text: { vi: "Intel 4004 — vi xử lý thương mại đầu tiên.", en: "Intel 4004 — first commercial microprocessor." } },
        { date: "1975", text: { vi: "Altair 8800; Microsoft thành lập.", en: "Altair 8800; Microsoft founded." } },
        { date: "1981-08", text: { vi: "IBM PC phát hành.", en: "IBM PC released." } },
        { date: "1984", text: { vi: "Macintosh; Cisco thành lập; mạng tế bào thương mại.", en: "Macintosh; Cisco founded; cell network commercializes." } },
      ],
      current: [
        { date: "2020-06", text: { vi: "GPT-3 phát hành; kỷ nguyên transformer quy mô lớn bắt đầu.", en: "GPT-3 released; large-scale transformer era begins." } },
        { date: "2022-11", text: { vi: "ChatGPT ra mắt; surge adoption AI người tiêu dùng.", en: "ChatGPT launch; consumer AI adoption surge." } },
        { date: "2023", text: { vi: "Capex AI hyperscaler ~$200B/năm công bố.", en: "Hyperscaler AI capex ~$200B/yr announced." } },
        { date: "2024", text: { vi: "Cầu điện data-center vượt 4% điện Mỹ.", en: "Data-center power demand tops 4% US electricity." } },
      ],
    },
    {
      id: "assets",
      label: { vi: "Thị trường", en: "Markets" },
      color: "var(--chart-line)",
      historical: [
        { date: "1973-74", text: { vi: "Cổ phiếu sụp; trái phiếu cũng giảm — không hedge.", en: "Stocks crash; bonds also fall — no hedge." } },
        { date: "1980-01", text: { vi: "Vàng đỉnh $850; góc bạc sụp tháng 3.", en: "Gold peaks $850; silver corner collapses March." } },
        { date: "1982-08", text: { vi: "S&P 500 bắt đầu bull market 18 năm (P/E ~7).", en: "S&P 500 begins 18-year bull market (P/E ~7)." } },
      ],
      current: [
        { date: "2020-03", text: { vi: "Sụp COVID; bear→bull nhanh nhất lịch sử.", en: "COVID crash; fastest bear→bull in history." } },
        { date: "2022", text: { vi: "Cả cổ phiếu và trái phiếu giảm — năm tồi nhất 60/40 kể từ 1937.", en: "Both stocks and bonds fall — worst year for 60/40 since 1937." } },
        { date: "2023-24", text: { vi: "Rally mega-cap tech/AI; tập trung đa thập kỷ cao.", en: "Mega-cap tech/AI rally; concentration at multi-decade high." } },
        { date: "2024-08", text: { vi: "Yen-vix carry unwind; cú sốc biến động ngắn.", en: "Yen-vix carry unwind; short-lived volatility shock." } },
      ],
    },
  ],
};
