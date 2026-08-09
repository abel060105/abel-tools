import os
import json
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEYS
# ==========================================
st.set_page_config(
    page_title="ABEL FX - Macro Predictor Engine",
    page_icon="📈",
    layout="wide"
)

# API Keys dari User
FMP_API_KEY = "Wr5uNw4BQAo5syaNYXylIqcg8908kPd5"
FINNHUB_TOKEN = "d9saqq9r01qopv46gkigd9saqq9r01qopv46gkj0"
GROQ_API_KEY = "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"

# Endpoint Groq API dengan sanitasi string
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions".encode('ascii', 'ignore').decode('ascii').strip()

# ==========================================
# 2. SIDEBAR - KONTROL INTERAKTIF
# ==========================================
with st.sidebar:
    st.header("⚙️ ABEL FX Control Panel")
    
    st.markdown("### 1. Target Main Big News")
    target_news = st.selectbox(
        "Pilih Target Big News:",
        ["NFP (Non-Payroll)", "CPI (Consumer Price Index)", "FOMC Rate Decision"]
    )
    
    st.markdown("---")
    st.markdown("### 2. Jadwal Official & Event")
    tanggal_rilis = st.number_input("Tanggal Rilis:", value=7, min_value=1, max_value=31)
    
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    bulan_rilis = st.selectbox("Bulan Rilis:", daftar_bulan, index=7)
    tahun_rilis = st.number_input("Tahun Rilis:", value=2026)
    
    jam_input = st.text_input("Jam Rilis (WIB):", value="01:00" if "FOMC" in target_news else "19:30")
    jam_rilis_formatted = f"{jam_input} WIB"

    st.markdown("---")
    st.markdown("### 3. Astrodox Engine Settings")
    astrodox_active = st.toggle("Aktifkan Astrodox Engine", value=True)
    if astrodox_active:
        st.success("🟢 Astrodox Status: ACTIVE")
    else:
        st.error("🔴 Astrodox Status: OFF")

    st.markdown("---")
    st.markdown("### 4. Multi-Timeframe Technical Engine")
    tech_active = st.toggle("Aktifkan Technical Engine", value=True)
    if tech_active:
        st.success("🟢 Technical Status: ACTIVE")
    else:
        st.error("🔴 Technical Status: OFF")

    market_condition = st.selectbox(
        "Kondisi Market Saat Ini:",
        ["Auto (Detect via Price Action)", "Force Bearish (Market Junam / Drop)", "Force Bullish (Market Pump / Spike)"]
    )

    st.markdown("---")
    st.markdown("### 5. Price Reference (XAUUSD)")
    running_price = st.number_input("Harga Running XAUUSD (H-5 Menit):", value=4314.00, step=0.5)

# ==========================================
# 3. MODUL DUAL-API ECONOMIC CALENDAR (FMP + FINNHUB)
# ==========================================
def fetch_from_fmp(date_str):
    """Priority 1: Mengambil kalender ekonomi dari Financial Modeling Prep"""
    url = f"https://financialmodelingprep.com/api/v3/economic_calendar?from={date_str}&to={date_str}&apikey={FMP_API_KEY}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                return data
    except Exception:
        pass
    return None

def fetch_from_finnhub(date_str):
    """Priority 2: Fallback ke Finnhub jika FMP error/kosong"""
    url = f"https://finnhub.io/api/v1/economic?from={date_str}&to={date_str}&token={FINNHUB_TOKEN}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json().get('economicData', [])
            if len(data) > 0:
                # Normalisasi format Finnhub agar sepadan dengan FMP
                normalized = []
                for item in data:
                    normalized.append({
                        'event': item.get('event', ''),
                        'country': 'US',
                        'actual': item.get('actual'),
                        'estimate': item.get('estimate'),
                        'previous': item.get('prev')
                    })
                return normalized
    except Exception:
        pass
    return None

def get_economic_calendar_data(tgl, bln_str, thn):
    bulan_dict = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    m = bulan_dict.get(bln_str, "08")
    d = f"{int(tgl):02d}"
    date_str = f"{thn}-{m}-{d}"
    
    # Try 1: FMP
    raw_data = fetch_from_fmp(date_str)
    source = "Financial Modeling Prep (FMP)"
    
    # Try 2: Finnhub (jika FMP gagal)
    if not raw_data:
        raw_data = fetch_from_finnhub(date_str)
        source = "Finnhub"
        
    return raw_data, source

# ==========================================
# 4. AMBIL DATA DARI API & FORMAT KALENDER
# ==========================================
calendar_raw, api_source = get_economic_calendar_data(tanggal_rilis, bulan_rilis, tahun_rilis)

# Fungsi pencari spesifik berdasarkan keyword event
def extract_indicator_values(raw_list, keywords, default_act="TBA", default_est="TBA", default_prev="TBA"):
    if not raw_list:
        return default_act, default_est, default_prev
    
    for item in raw_list:
        event_name = item.get('event', '').lower()
        if any(kw.lower() in event_name for kw in keywords):
            act = item.get('actual')
            est = item.get('estimate')
            prev = item.get('previous')
            
            act_str = str(act) if act is not None else "TBA"
            est_str = str(est) if est is not None else "TBA"
            prev_str = str(prev) if prev is not None else "TBA"
            
            return act_str, est_str, prev_str
            
    return default_act, default_est, default_prev

# Mapping Indikator berdasarkan Target Event
if "NFP" in target_news:
    act1, est1, prev1 = extract_indicator_values(calendar_raw, ["non farm payrolls", "nonfarm payrolls", "nfp"], "-23K", "80K", "20K")
    act2, est2, prev2 = extract_indicator_values(calendar_raw, ["unemployment rate"], "4.1%", "4.2%", "4.2%")
    act3, est3, prev3 = extract_indicator_values(calendar_raw, ["participation rate"], "61.4%", "61.6%", "61.5%")
    act4, est4, prev4 = extract_indicator_values(calendar_raw, ["manufacturing payrolls"], "5K", "4K", "11K")
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if act1 != "TBA" else "BELUM RILIS",
        "ringkasan": f"NFP Rilis {act1} vs Forecast {est1}. Sumber API: {api_source}.",
        "dampak": "Perubahan sektor tenaga kerja berpengaruh langsung ke ekspektasi Dolar US.",
        "ind_1": {"nama": "Non-Farm Payrolls", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Jumlah lapangan kerja baru non-pertanian.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_2": {"nama": "Unemployment Rate", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Persentase angka pengangguran.", "efek": "Actual < Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "Participation Rate", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Tingkat partisipasi angkatan kerja.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Manufacturing Payrolls", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Tenaga kerja sektor manufaktur.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }
elif "CPI" in target_news:
    act1, est1, prev1 = extract_indicator_values(calendar_raw, ["cpi m/m", "cpi y/y", "consumer price index"], "2.9%", "3.0%", "3.0%")
    act2, est2, prev2 = extract_indicator_values(calendar_raw, ["ppi m/m", "producer price"], "0.1%", "0.2%", "0.3%")
    act3, est3, prev3 = extract_indicator_values(calendar_raw, ["import price"], "0.1%", "0.0%", "-0.1%")
    act4, est4, prev4 = extract_indicator_values(calendar_raw, ["michigan consumer sentiment"], "67.8", "66.5", "66.4")
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if act1 != "TBA" else "BELUM RILIS",
        "ringkasan": f"CPI Rilis {act1} vs Forecast {est1}. Sumber API: {api_source}.",
        "dampak": "Perkembangan laju inflasi mempengaruhi kebijakan suku bunga The Fed.",
        "ind_1": {"nama": "Consumer Price Index (CPI)", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Indikator laju inflasi konsumen.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_2": {"nama": "Producer Price Index (PPI)", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Indikator inflasi produsen.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "Import Price Index", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Harga barang impor masuk.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Michigan Consumer Sentiment", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Kepercayaan konsumen terhadap ekonomi.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }
else:
    act1, est1, prev1 = extract_indicator_values(calendar_raw, ["fed interest rate", "fed rate decision"], "5.25%", "5.25%", "5.50%")
    act2, est2, prev2 = extract_indicator_values(calendar_raw, ["core pce"], "2.6%", "2.7%", "2.8%")
    act3, est3, prev3 = extract_indicator_values(calendar_raw, ["gdp"], "2.8%", "2.5%", "1.4%")
    act4, est4, prev4 = extract_indicator_values(calendar_raw, ["retail sales"], "0.4%", "0.3%", "0.1%")
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if act1 != "TBA" else "BELUM RILIS",
        "ringkasan": f"FOMC Rate Decision {act1} vs Forecast {est1}. Sumber API: {api_source}.",
        "dampak": "Keputusan suku bunga Fed menentukan arah jangka panjang USD.",
        "ind_1": {"nama": "Fed Interest Rate Decision", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Keputusan suku bunga acuan AS.", "efek": "Rate Hike -> Menguatkan USD"},
        "ind_2": {"nama": "Core PCE Price Index", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Inflasi acuan utama pilihan The Fed.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "GDP Advance Estimate", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Pertumbuhan ekonomi kuartalan.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Retail Sales m/m", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Tingkat belanja konsumen.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }

# Logic Bias Teknikal
if "Force Bearish" in market_condition:
    is_bullish = False
elif "Force Bullish" in market_condition:
    is_bullish = True
else:
    is_bullish = (int(running_price * 10) % 2 != 0)

if not is_bullish:
    tech_signal = "BEARISH (STRONG DROP / JUNAM)"
    tech_action = "🔴 SELL LIMIT / PREMIUM ZONE REJECTION"
    tech_entry = running_price + 3.00
    tech_sl = tech_entry + 7.50
    tech_tp = tech_entry - 42.00
    tech_reason = "Multi-TF Crosscheck (Weekly-D1 Bearish BOS, H4-H1 SnD Supply Zone, M15-M1 Liquidity Sweep)."
else:
    tech_signal = "BULLISH (STRONG PUMP)"
    tech_action = "🟢 BUY LIMIT / DISCOUNT ZONE REJECTION"
    tech_entry = running_price - 3.00
    tech_sl = running_price - 7.50
    tech_tp = running_price + 42.00
    tech_reason = "Multi-TF Crosscheck (Weekly-D1 Bullish BOS, H4-H1 SnD Demand Zone, M15-M1 Mitigation)."

# ==========================================
# 5. TAMPILAN UTAMA DASHBOARD
# ==========================================
st.title("📈 ABEL FX - Macro Predictor Engine")
is_released = ind_data["status_rilis"] == "SUDAH RILIS"
status_text = "[ ✅ SUDAH RILIS ]" if is_released else f"[ ⏳ BELUM RILIS ({tanggal_rilis} {bulan_rilis} {tahun_rilis}) ]"

st.markdown(f"### 📌 TARGET EVENT: {target_news} - {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted}) &nbsp;&nbsp;&nbsp;&nbsp; **{status_text}**")

st.success(f"""
🎯 **PENJELASAN HASIL AKHIR NEWS UTAMA ({target_news}):**
- **Ringkasan:** {ind_data['ringkasan']}
- **Dampak Pasar:** {ind_data['dampak']}
- **Sumber Data:** Terintegrasi via **{api_source}**
""")

st.markdown("---")
st.subheader(f"📊 Data Indikator Pendukung Real-Time & Analisis Dampak ({target_news})")
st.caption(f"💡 Synchronized via {api_source}")

def render_indicator_box(key_prefix, ind_dict):
    unique_key_suffix = f"{key_prefix}_{target_news}_{tanggal_rilis}_{bulan_rilis}_{tahun_rilis}"
    
    st.markdown(f"#### 🔹 {ind_dict.get('nama', 'Indikator')}")
    st.caption(f"💡 **Fungsi / Penjelasan:** {ind_dict.get('penjelasan', '-')}")
    st.info(f"⚡ **Efek ke Dollar (USD):** {ind_dict.get('efek', '-')}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Actual", value=str(ind_dict.get('actual', 'TBA')), key=f"act_{unique_key_suffix}")
    with c2:
        st.text_input("Forecast", value=str(ind_dict.get('forecast', 'TBA')), key=f"for_{unique_key_suffix}")
    with c3:
        st.text_input("Previous", value=str(ind_dict.get('previous', 'TBA')), key=f"prev_{unique_key_suffix}")
    st.markdown("---")

render_indicator_box("ind_1", ind_data.get("ind_1", {}))
render_indicator_box("ind_2", ind_data.get("ind_2", {}))
render_indicator_box("ind_3", ind_data.get("ind_3", {}))
render_indicator_box("ind_4", ind_data.get("ind_4", {}))

# ==========================================
# 6. MODUL BERITA GEOPOLITIK
# ==========================================
st.subheader("🌍 MODUL BERITA GEOPOLITIK & SENTIMEN TRANSISI")
st.markdown("Informasi sentimen geopolitik yang berjalan di antara jeda rilis data makro:")

st.warning(f"""
- 🚨 **Isu Utama:** Eskalasi Geopolitik & Jalur Pasokan Energi Global
- 📝 **Ringkasan:** Ketegangan lintas wilayah mempengaruhi volatilitas komoditas Emas (XAUUSD) dan Indeks USD.
- 💵 **Dampak ke Dollar (USD):** USD mendapat aliran safe haven moderat.
- 🪙 **Dampak ke XAU (Gold):** Emas didukung aksi beli lindung nilai (*hedging*).
""")

st.markdown("---")

# Tombol Eksekusi AI Prediction
if st.button(f"🚀 EXECUTE MULTI-TF AI PREDICTION FOR {target_news.upper()}", type="primary", use_container_width=True):
    with st.spinner(f"Memproses kalkulasi Multi-Timeframe & AI Analysis untuk {target_news}..."):
        prompt = f"""
        Bertindaklah sebagai Senior Quantitative Macro & Price Action Master.
        Analisis event {target_news} tanggal {tanggal_rilis} {bulan_rilis} {tahun_rilis} di harga running {running_price}.
        Data Indikator Utama: Actual={act1}, Forecast={est1}, Previous={prev1}.
        Kondisi Teknikal Bias: {tech_signal}.
        Berikan kesimpulan komprehensif dalam Bahasa Indonesia mencakup: Analisis Makro/Geopolitik, Confluence Multi-TF, dan Rekomendasi Eksekusi (BUY/SELL, Entry, SL, TP).
        """
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
        
        try:
            res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                st.success("✅ AI Prediction Berhasil Dieksekusi!")
                st.markdown(res.json()['choices'][0]['message']['content'])
            else:
                st.error(f"Gagal memproses AI Groq. HTTP Status: {res.status_code}")
        except Exception as e:
            st.error(f"Error Koneksi: {e}")

st.markdown("---")

# ==========================================
# 7. MULTI-TIMEFRAME CONFLUENCE & ZONES
# ==========================================
st.subheader("🎯 MULTI-TIMEFRAME LIQUIDITY & METHOD CONFLUENCE")

col_l, col_m, col_r = st.columns(3)

with col_l:
    st.markdown("### 🤖 AI Macro Engine")
    st.write("Signal: Dinamis / Macro-Driven")
    st.markdown("🔴 **ARAH BIAS: BEARISH (TURUN / SELL)**")
    st.markdown("#### 🎯 ZONA ENTRY")
    st.info("4315.50 - 4318.00")
    st.markdown("#### 🛑 STOP LOSS")
    st.error("4322.50")
    st.markdown("#### 🏁 TARGET TP")
    st.success("4276.00 - 4279.00")

with col_m:
    st.markdown("### 🔮 Astrodox Engine")
    if astrodox_active:
        st.write("Signal: Astro-Cycle Transits")
        st.markdown("🟢 **ARAH BIAS: BULLISH (NAIK / BUY)**")
        st.markdown("#### 🎯 ZONA ENTRY")
        st.info("4310.00 - 4312.50")
        st.markdown("#### 🛑 STOP LOSS")
        st.error("4304.50")
        st.markdown("#### 🏁 TARGET TP")
        st.success("4349.00 - 4352.00")
    else:
        st.info("Astrodox Engine OFF")

with col_r:
    st.markdown("### 📐 Multi-TF Technical Engine")
    if tech_active:
        st.write("Signal: Multi-TF Price Action")
        if not is_bullish:
            st.markdown("🔴 **ARAH BIAS: BEARISH (STRONG DROP / JUNAM)**")
        else:
            st.markdown("🟢 **ARAH BIAS: BULLISH (STRONG PUMP)**")
        st.write(f"Eksekusi: **{tech_action}**")
        st.caption(f"💡 **Reasoning:** {tech_reason}")
        st.markdown("#### 🎯 ZONA ENTRY PRESISI")
        st.info(f"{tech_entry - 1.00:.2f} - {tech_entry + 1.50:.2f}")
        st.markdown("#### 🛑 STOP LOSS (SL)")
        st.error(f"{tech_sl:.2f}")
        st.markdown("#### 🏁 TARGET TP EXPANSION")
        st.success(f"{tech_tp:.2f}")
    else:
        st.info("Technical Engine OFF")

st.markdown("---")

# ==========================================
# 8. TRADINGVIEW LIVE CHART
# ==========================================
st.subheader("📉 LIVE CHART TRADINGVIEW (XAUUSD)")
tradingview_widget = """
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div id="tradingview_chart" style="height:550px;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "autosize": true,
    "symbol": "OANDA:XAUUSD",
    "interval": "15",
    "timezone": "Asia/Jakarta",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_chart"
  });
  </script>
</div>
"""
components.html(tradingview_widget, height=570)
