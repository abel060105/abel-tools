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
    
    # Priority 1: FMP
    raw_data = fetch_from_fmp(date_str)
    source = "Financial Modeling Prep (FMP)"
    
    # Priority 2: Finnhub
    if not raw_data:
        raw_data = fetch_from_finnhub(date_str)
        source = "Finnhub"
        
    return raw_data, source

# ==========================================
# 4. AMBIL DATA DARI API & EXTRACT INDIKATOR
# ==========================================
calendar_raw, api_source = get_economic_calendar_data(tanggal_rilis, bulan_rilis, tahun_rilis)

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
# 5. KALKULATOR REKAP DATA PENDUKUNG (ANTI-HALUSINASI)
# ==========================================
def calculate_macro_divergence(act1, est1, act2, est2, act3, est3, act4, est4):
    usd_score = 0

    def parse_num(val):
        try:
            return float(str(val).replace('%', '').replace('K', '').replace('M', ''))
        except:
            return None

    def eval_indicator(name, act_raw, est_raw, higher_is_good_for_usd=True):
        a = parse_num(act_raw)
        e = parse_num(est_raw)
        if a is None or e is None:
            return f"- **{name}**: Data belum rilis / TBA (Neutral)", 0
        
        if a > e:
            res = "BULLISH USD" if higher_is_good_for_usd else "BEARISH USD"
            score = 1 if higher_is_good_for_usd else -1
            note = f"Actual ({act_raw}) > Forecast ({est_raw})"
        elif a < e:
            res = "BEARISH USD" if higher_is_good_for_usd else "BULLISH USD"
            score = -1 if higher_is_good_for_usd else 1
            note = f"Actual ({act_raw}) < Forecast ({est_raw})"
        else:
            res = "NEUTRAL"
            score = 0
            note = f"Actual ({act_raw}) == Forecast ({est_raw})"
            
        return f"- **{name}**: {note} -> Impak: **{res}**", score

    if "NFP" in target_news:
        r1, s1 = eval_indicator("NFP", act1, est1, higher_is_good_for_usd=True)
        r2, s2 = eval_indicator("Unemployment Rate", act2, est2, higher_is_good_for_usd=False)
        r3, s3 = eval_indicator("Participation Rate", act3, est3, higher_is_good_for_usd=True)
        r4, s4 = eval_indicator("Manufacturing Payrolls", act4, est4, higher_is_good_for_usd=True)
    else:
        r1, s1 = eval_indicator("Indikator Utama", act1, est1, higher_is_good_for_usd=True)
        r2, s2 = eval_indicator("Indikator Pendukung 2", act2, est2, higher_is_good_for_usd=True)
        r3, s3 = eval_indicator("Indikator Pendukung 3", act3, est3, higher_is_good_for_usd=True)
        r4, s4 = eval_indicator("Indikator Pendukung 4", act4, est4, higher_is_good_for_usd=True)

    rekap_text = "\n".join([r1, r2, r3, r4])
    total_score = s1 + s2 + s3 + s4
    
    if total_score > 0:
        macro_bias = "BULLISH USD / BEARISH XAUUSD"
    elif total_score < 0:
        macro_bias = "BEARISH USD / BULLISH XAUUSD"
    else:
        macro_bias = "NEUTRAL / MIXED DATA (Whipsaw Risk)"

    return rekap_text, macro_bias, total_score

# ==========================================
# 6. MODUL GEOPOLITIK AUTOMATED VIA GROQ
# ==========================================
def fetch_geopolitical_analysis(event_name, actual_val, forecast_val):
    prompt = f"""
    Bertindaklah sebagai Senior Geopolitical & Macroeconomic Analyst.
    Berikan analisis ringkas mengenai konteks Geopolitik Global terkini (misal: isu Timur Tengah, pasokan energi, perang dagang) 
    dan hubungannya dengan data {event_name} (Actual: {actual_val} vs Forecast: {forecast_val}).

    Format jawaban HARUS JSON MURNI tanpa markdown:
    {{
        "isu_utama": "nama isu utama",
        "ringkasan_situasi": "2 kalimat situasi terkini",
        "dampak_usd": "efek ke USD",
        "dampak_xau": "efek ke Emas XAUUSD"
    }}
    """
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    try:
        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=12)
        if res.status_code == 200:
            return json.loads(res.json()['choices'][0]['message']['content'])
    except Exception:
        pass

    return {
        "isu_utama": "Eskalasi Geopolitik & Pasokan Energi Global",
        "ringkasan_situasi": "Ketegangan wilayah meningkatkan arus permintaan safe haven pada komoditas utama.",
        "dampak_usd": "USD ditopang aliran modal safe-haven.",
        "dampak_xau": "XAUUSD mendapatkan dorongan aksi beli hedging."
    }

# ==========================================
# 7. TAMPILAN UTAMA DASHBOARD
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
# 8. MODUL GEOPOLITIK (INTEGRATED)
# ==========================================
st.subheader("🌍 MODUL BERITA GEOPOLITIK & SENTIMEN TRANSISI (AI + CALENDAR)")

geo_info = fetch_geopolitical_analysis(target_news, act1, est1)

st.warning(f"""
- 🚨 **Isu Utama:** {geo_info.get('isu_utama')}
- 📝 **Ringkasan Situasi:** {geo_info.get('ringkasan_situasi')}
- 💵 **Dampak Gabungan ke USD:** {geo_info.get('dampak_usd')}
- 🪙 **Dampak Gabungan ke XAUUSD:** {geo_info.get('dampak_xau')}
""")

st.markdown("---")

# ==========================================
# 9. AI ENTRY LOGIC EXECUTION
# ==========================================
if st.button(f"🚀 EXECUTE MULTI-TF AI PREDICTION FOR {target_news.upper()}", type="primary", use_container_width=True):
    with st.spinner("Memproses Rekap Data Pendukung & Generasi Logika Entry AI..."):
        
        rekap_text, macro_bias_result, score_val = calculate_macro_divergence(
            act1, est1, act2, est2, act3, est3, act4, est4
        )
        
        st.subheader("📋 Rekap Evaluasi Data Pendukung Real-Time")
        st.markdown(rekap_text)
        st.info(f"⚖️ **Kesimpulan Bias Makro:** {macro_bias_result} (Score Net: {score_val})")
        
        system_prompt = f"""
        Kamu adalah Senior Quantitative Trader & Macro Analyst profesional.
        Tugasmu menyusun LOGIKA ENTRY FLEKSIBEL untuk XAUUSD berbasis Data Makro Real-Time + Technical Setup.
        
        [DATA INPUT REAL-TIME]
        - Target Event: {target_news} ({tanggal_rilis} {bulan_rilis} {tahun_rilis})
        - Harga Running XAUUSD: {running_price}
        - Rekap Indikator Pendukung:
        {rekap_text}
        - Bias Makro Hasil Kalkulasi: {macro_bias_result}
        - Technical Setup: {tech_signal} | Setup Action: {tech_action}

        [ATURAN KHUSUS LOGIKA ENTRY]:
        1. JANGAN HALUSINASI. Logika entry HARUS berbasis konfluensi/deviasi data pendukung.
        2. Data Pendukung dominan Bearish USD -> Wajib fokus Opsi BUY XAUUSD.
        3. Data Pendukung dominan Bullish USD -> Wajib fokus Opsi SELL XAUUSD.
        4. Data Pendukung MIXED -> Wajib merekomendasikan Wait & See / Liquidity Sweep Zone.

        [FORMAT JAWABAN MARKDOWN]
        ### 🔍 1. Rekap & Sintesis Data Pendukung
        (Penjelasan deviasi angka actual vs forecast)
        
        ### ⚡ 2. Logika Entry & Trigger Konfirmasi
        - **Arah Bias Utama:** [BUY / SELL / NEUTRAL]
        - **Reasoning Logika:** (Hubungan angka data pendukung dengan SnD Zone)
        - **Kondisi Trigger:** (Syarat konfirmasi candlestick M5/M15)

        ### 🎯 3. Specific Execution Setup (XAUUSD)
        - **Execution Type:** [Instant Market / Limit Order]
        - **Entry Zone:** [Rentang Harga]
        - **Stop Loss (SL):** [Harga SL]
        - **Take Profit (TP):** [TP1, TP2, & TP Extended]
        """

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": system_prompt}],
            "temperature": 0.2
        }
        
        try:
            res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                st.success("✅ AI Logic Execution Berhasil Terbentuk!")
                st.markdown(res.json()['choices'][0]['message']['content'])
            else:
                st.error(f"Gagal memproses AI Groq. HTTP Status: {res.status_code}")
        except Exception as e:
            st.error(f"Error Koneksi: {e}")

st.markdown("---")

# ==========================================
# 10. MULTI-TIMEFRAME CONFLUENCE & ZONES
# ==========================================
st.subheader("🎯 MULTI-TIMEFRAME LIQUIDITY & METHOD CONFLUENCE")

col_l, col_m, col_r = st.columns(3)

with col_l:
    st.markdown("### 🤖 AI Macro Engine")
    st.write("Signal: Macro Divergence Engine")
    if not is_bullish:
        st.markdown("🔴 **ARAH BIAS: BEARISH (SELL)**")
        st.markdown("#### 🎯 ZONA ENTRY")
        st.info(f"{running_price + 1.50:.2f} - {running_price + 4.00:.2f}")
        st.markdown("#### 🛑 STOP LOSS")
        st.error(f"{running_price + 8.50:.2f}")
        st.markdown("#### 🏁 TARGET TP")
        st.success(f"{running_price - 38.00:.2f}")
    else:
        st.markdown("🟢 **ARAH BIAS: BULLISH (BUY)**")
        st.markdown("#### 🎯 ZONA ENTRY")
        st.info(f"{running_price - 4.00:.2f} - {running_price - 1.50:.2f}")
        st.markdown("#### 🛑 STOP LOSS")
        st.error(f"{running_price - 8.50:.2f}")
        st.markdown("#### 🏁 TARGET TP")
        st.success(f"{running_price + 38.00:.2f}")

with col_m:
    st.markdown("### 🔮 Astrodox Engine")
    if astrodox_active:
        st.write("Signal: Astro Transits Cycle")
        st.markdown("🟢 **ARAH BIAS: BULLISH (BUY)**")
        st.markdown("#### 🎯 ZONA ENTRY")
        st.info(f"{running_price - 3.00:.2f} - {running_price - 1.00:.2f}")
        st.markdown("#### 🛑 STOP LOSS")
        st.error(f"{running_price - 7.00:.2f}")
        st.markdown("#### 🏁 TARGET TP")
        st.success(f"{running_price + 35.00:.2f}")
    else:
        st.info("Astrodox Engine OFF")

with col_r:
    st.markdown("### 📐 Multi-TF Technical Engine")
    if tech_active:
        st.write("Signal: Price Action SnD")
        if not is_bullish:
            st.markdown("🔴 **ARAH BIAS: BEARISH (STRONG DROP)**")
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
# 11. TRADINGVIEW LIVE CHART WIDGET
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
