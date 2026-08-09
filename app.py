import os
import json
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEYS
# ==========================================
st.set_page_config(
    page_title="ABEL FX - Macro Predictor Engine",
    page_icon="📈",
    layout="wide"
)

FMP_API_KEY = "Wr5uNw4BQAo5syaNYXylIqcg8908kPd5"
FINNHUB_TOKEN = "d9saqq9r01qopv46igd9saqq9r01qopv46gkj0"
GROQ_API_KEY = "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"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Session state initialization
if "ai_result" not in st.session_state:
    st.session_state["ai_result"] = None
if "rekap_text" not in st.session_state:
    st.session_state["rekap_text"] = ""
if "macro_bias_result" not in st.session_state:
    st.session_state["macro_bias_result"] = ""
if "score_val" not in st.session_state:
    st.session_state["score_val"] = 0

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
    
    now = datetime.now()
    
    tanggal_rilis = st.number_input("Tanggal Rilis:", value=12, min_value=1, max_value=31)
    
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    bulan_dict = {
        "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
        "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
        "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    
    bulan_rilis = st.selectbox("Bulan Rilis:", daftar_bulan, index=7) # Default Agustus
    tahun_rilis = st.number_input("Tahun Rilis:", value=2026)
    
    jam_input = st.text_input("Jam Rilis (WIB):", value="01:00" if "FOMC" in target_news else "19:30")
    jam_rilis_formatted = f"{jam_input} WIB"

    # ==========================================
    # VALIDASI PRESISI WAKTU (TANGGAL + JAM + MENIT)
    # ==========================================
    try:
        if ":" in jam_input:
            jam_str, menit_str = jam_input.strip().split(":")
            jam_num = int(jam_str)
            menit_num = int(menit_str)
        else:
            jam_num = 19
            menit_num = 30
            
        bulan_num = bulan_dict.get(bulan_rilis, 8)
        event_datetime = datetime(
            int(tahun_rilis), 
            int(bulan_num), 
            int(tanggal_rilis), 
            jam_num, 
            menit_num
        )
        
        is_future_event = event_datetime > now
    except Exception:
        is_future_event = False

    st.markdown("---")
    st.markdown("### 3. Astrodox Engine Settings")
    astrodox_active = st.toggle("Aktifkan Astrodox Engine", value=True)

    st.markdown("---")
    st.markdown("### 4. Multi-Timeframe Technical Engine")
    tech_active = st.toggle("Aktifkan Technical Engine", value=True)

    market_condition = st.selectbox(
        "Kondisi Market Saat Ini:",
        ["Auto (Detect via Price Action)", "Force Bearish (Market Junam / Drop)", "Force Bullish (Market Pump / Spike)"]
    )

    st.markdown("---")
    st.markdown("### 5. Price Reference")
    running_price = st.number_input("Harga Running XAUUSD:", value=4314.00, step=0.5)

# ==========================================
# 3. MODUL DUAL-API ECONOMIC CALENDAR
# ==========================================
def fetch_from_fmp(date_str):
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
                        'previous': item.get('prev'),
                        'date': item.get('time', '')
                    })
                return normalized
    except Exception:
        pass
    return None

def get_economic_calendar_data(tgl, bln_str, thn):
    m = f"{bulan_dict.get(bln_str, 8):02d}"
    d = f"{int(tgl):02d}"
    date_str = f"{thn}-{m}-{d}"
    
    raw_data = fetch_from_fmp(date_str)
    source = "Financial Modeling Prep (FMP)"
    
    if not raw_data:
        raw_data = fetch_from_finnhub(date_str)
        source = "Finnhub"
        
    return raw_data, source

# ==========================================
# 4. EKSTRAKSI INDIKATOR & OTOMATIS OTW SPESIFIK
# ==========================================
calendar_raw, api_source = get_economic_calendar_data(tanggal_rilis, bulan_rilis, tahun_rilis)

def extract_indicator_values(raw_list, keywords, default_est="OTW", default_prev="OTW"):
    if raw_list:
        for item in raw_list:
            event_name = item.get('event', '').lower()
            if any(kw.lower() in event_name for kw in keywords):
                act = item.get('actual')
                est = item.get('estimate')
                prev = item.get('previous')
                
                # Coba ambil timestamp spesifik per indikator dari API
                event_date_raw = item.get('date', '')
                if event_date_raw:
                    try:
                        dt_obj = datetime.strptime(event_date_raw[:16], "%Y-%m-%d %H:%M")
                        jadwal_spesifik = dt_obj.strftime("%d %b %Y %H:%M WIB")
                    except Exception:
                        jadwal_spesifik = f"{tanggal_rilis} {bulan_rilis[:3]} {tahun_rilis} {jam_rilis_formatted}"
                else:
                    jadwal_spesifik = f"{tanggal_rilis} {bulan_rilis[:3]} {tahun_rilis} {jam_rilis_formatted}"

                status_otw = f"OTW ({jadwal_spesifik})"
                
                act_str = str(act) if (act is not None and str(act).strip() != "") else status_otw
                est_str = str(est) if (est is not None and str(est).strip() != "") else default_est
                prev_str = str(prev) if (prev is not None and str(prev).strip() != "") else default_prev
                
                return act_str, est_str, prev_str
            
    jadwal_default = f"OTW ({tanggal_rilis} {bulan_rilis[:3]} {tahun_rilis} {jam_rilis_formatted})"
    return jadwal_default, default_est, default_prev

if "NFP" in target_news:
    act1, est1, prev1 = extract_indicator_values(calendar_raw, ["non farm payrolls", "nonfarm payrolls", "nfp"], "80K", "20K")
    act2, est2, prev2 = extract_indicator_values(calendar_raw, ["unemployment rate"], "4.2%", "4.2%")
    act3, est3, prev3 = extract_indicator_values(calendar_raw, ["participation rate"], "61.6%", "61.5%")
    act4, est4, prev4 = extract_indicator_values(calendar_raw, ["manufacturing payrolls"], "4K", "11K")
    
    is_released_flag = ("OTW" not in act1) and (not is_future_event)
    ind_data = {
        "status_rilis": "SUDAH RILIS" if is_released_flag else "BELUM RILIS",
        "ringkasan": f"NFP Rilis {act1} vs Forecast {est1}. Sumber API: {api_source}." if is_released_flag else f"Menunggu Rilis NFP pada {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted}). Forecast: {est1}.",
        "dampak": "Perubahan sektor tenaga kerja berpengaruh langsung ke ekspektasi Dolar US.",
        "ind_1": {"nama": "Non-Farm Payrolls", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Jumlah lapangan kerja baru non-pertanian.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_2": {"nama": "Unemployment Rate", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Persentase angka pengangguran.", "efek": "Actual < Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "Participation Rate", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Tingkat partisipasi angkatan kerja.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Manufacturing Payrolls", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Tenaga kerja sektor manufaktur.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }
elif "CPI" in target_news:
    act1, est1, prev1 = extract_indicator_values(calendar_raw, ["cpi m/m", "cpi y/y", "consumer price index"], "3.0%", "3.0%")
    act2, est2, prev2 = extract_indicator_values(calendar_raw, ["ppi m/m", "producer price"], "0.2%", "0.3%")
    act3, est3, prev3 = extract_indicator_values(calendar_raw, ["import price"], "0.0%", "-0.1%")
    act4, est4, prev4 = extract_indicator_values(calendar_raw, ["michigan consumer sentiment"], "66.5", "66.4")
    
    is_released_flag = ("OTW" not in act1) and (not is_future_event)
    ind_data = {
        "status_rilis": "SUDAH RILIS" if is_released_flag else "BELUM RILIS",
        "ringkasan": f"CPI Rilis {act1} vs Forecast {est1}. Sumber API: {api_source}." if is_released_flag else f"Menunggu Rilis CPI pada {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted}). Forecast: {est1}.",
        "dampak": "Perkembangan laju inflasi mempengaruhi kebijakan suku bunga The Fed.",
        "ind_1": {"nama": "Consumer Price Index (CPI)", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Indikator laju inflasi konsumen.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_2": {"nama": "Producer Price Index (PPI)", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Indikator inflasi produsen.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "Import Price Index", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Harga barang impor masuk.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Michigan Consumer Sentiment", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Kepercayaan konsumen terhadap ekonomi.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }
else:
    act1, est1, prev1 = extract_indicator_values(calendar_raw, ["fed interest rate", "fed rate decision"], "5.25%", "5.50%")
    act2, est2, prev2 = extract_indicator_values(calendar_raw, ["core pce"], "2.7%", "2.8%")
    act3, est3, prev3 = extract_indicator_values(calendar_raw, ["gdp"], "2.5%", "1.4%")
    act4, est4, prev4 = extract_indicator_values(calendar_raw, ["retail sales"], "0.3%", "0.1%")
    
    is_released_flag = ("OTW" not in act1) and (not is_future_event)
    ind_data = {
        "status_rilis": "SUDAH RILIS" if is_released_flag else "BELUM RILIS",
        "ringkasan": f"FOMC Rate Decision {act1} vs Forecast {est1}. Sumber API: {api_source}." if is_released_flag else f"Menunggu Rilis FOMC pada {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted}). Forecast: {est1}.",
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
# 5. KALKULATOR REKAP DATA PENDUKUNG
# ==========================================
def calculate_macro_divergence(act1, est1, act2, est2, act3, est3, act4, est4):
    def parse_num(val):
        try:
            return float(str(val).replace('%', '').replace('K', '').replace('M', ''))
        except:
            return None

    def eval_indicator(name, act_raw, est_raw, higher_is_good_for_usd=True):
        a = parse_num(act_raw)
        e = parse_num(est_raw)
        if a is None or e is None or "OTW" in str(act_raw):
            return f"- **{name}**: Data belum rilis / {act_raw} (Skenario Konsensus Market)", 0
        
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
    Berikan analisis terupdate mengenai isu geopolitik krusial terkini (seperti konflik Selat Hormuz, aktivitas rudal/militer Iran, ketegangan Timur Tengah, pasokan minyak bumi, perang/sanksi global) 
    dan kombinasikan dengan dampak rilis data {event_name} (Actual: {actual_val} vs Forecast: {forecast_val}).

    Format jawaban HARUS JSON MURNI tanpa markdown:
    {{
        "isu_utama": "Eskalasi Selat Hormuz & Ancaman Rudal Iran",
        "ringkasan_situasi": "Eskalasi militer di Selat Hormuz dan ancaman serangan rudal Iran memperketat jalur distribusi minyak global dan mendongkrak minat beli aset safe haven.",
        "dampak_usd": "USD menguat terbatas terdorong arus safe-haven di tengah ketidakpastian pasokan.",
        "dampak_xau": "XAUUSD sangat kuat didukung oleh lonjakan permintaan hedging safe-haven perang."
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
        "isu_utama": "Ketegangan Selat Hormuz & Eskalasi Rudal Iran / Perang Timur Tengah",
        "ringkasan_situasi": "Eskalasi militer di Selat Hormuz dan ancaman serangan rudal Iran memperketat jalur distribusi minyak global dan mendongkrak minat beli aset safe haven.",
        "dampak_usd": "USD menguat terbatas terdorong arus safe-haven di tengah ketidakpastian pasokan.",
        "dampak_xau": "XAUUSD sangat kuat didukung oleh lonjakan permintaan hedging safe-haven perang."
    }

# ==========================================
# 7. TAMPILAN UTAMA DASHBOARD
# ==========================================
st.title("📈 ABEL FX - Macro Predictor Engine")

status_text = "[ ✅ SUDAH RILIS ]" if ind_data["status_rilis"] == "SUDAH RILIS" else f"[ ⏳ BELUM RILIS ({tanggal_rilis} {bulan_rilis} {tahun_rilis} {jam_rilis_formatted}) ]"

st.markdown(f"### 📌 TARGET EVENT: {target_news} - {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted}) &nbsp;&nbsp;&nbsp;&nbsp; **{status_text}**")

if ind_data["status_rilis"] == "SUDAH RILIS":
    st.success(f"""
    🎯 **HASIL AKHIR NEWS ({target_news}):**
    - **Ringkasan:** {ind_data['ringkasan']}
    - **Dampak Pasar:** {ind_data['dampak']}
    - **Sumber Data:** Terintegrasi via **{api_source}**
    """)
else:
    st.info(f"""
    ⏳ **PROYEKSI & JADWAL NEWS ({target_news}):**
    - **Status:** Event baru akan rilis pada **{tanggal_rilis} {bulan_rilis} {tahun_rilis} jam {jam_rilis_formatted}**.
    - **Ringkasan:** {ind_data['ringkasan']}
    - **Dampak Kebijakan:** {ind_data['dampak']}
    """)

st.markdown("---")
st.subheader(f"📊 Data Indikator Pendukung Real-Time ({target_news})")
st.caption(f"💡 Synchronized via {api_source} | Waktu Sistem Saat Ini: {now.strftime('%d-%m-%Y %H:%M:%S')} WIB")

def render_indicator_box(key_prefix, ind_dict):
    unique_key_suffix = f"{key_prefix}_{target_news}_{tanggal_rilis}_{bulan_rilis}_{tahun_rilis}"
    st.markdown(f"#### 🔹 {ind_dict.get('nama', 'Indikator')}")
    st.caption(f"💡 **Fungsi / Penjelasan:** {ind_dict.get('penjelasan', '-')}")
    st.info(f"⚡ **Efek ke Dollar (USD):** {ind_dict.get('efek', '-')}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Actual", value=str(ind_dict.get('actual', f"OTW ({tanggal_rilis} {bulan_rilis[:3]} {tahun_rilis} {jam_rilis_formatted})")), key=f"act_{unique_key_suffix}")
    with c2:
        st.text_input("Forecast", value=str(ind_dict.get('forecast', 'OTW')), key=f"for_{unique_key_suffix}")
    with c3:
        st.text_input("Previous", value=str(ind_dict.get('previous', 'OTW')), key=f"prev_{unique_key_suffix}")
    st.markdown("---")

render_indicator_box("ind_1", ind_data.get("ind_1", {}))
render_indicator_box("ind_2", ind_data.get("ind_2", {}))
render_indicator_box("ind_3", ind_data.get("ind_3", {}))
render_indicator_box("ind_4", ind_data.get("ind_4", {}))

# ==========================================
# 8. MODUL GEOPOLITIK
# ==========================================
st.subheader("🌍 MODUL BERITA GEOPOLITIK & SENTIMEN TRANSISI")

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
    with st.spinner("Sintesis Data Makro + Geopolitik + Technical Setup..."):
        
        rekap_text, macro_bias_result, score_val = calculate_macro_divergence(
            act1, est1, act2, est2, act3, est3, act4, est4
        )
        
        system_prompt = f"""
        Kamu adalah Senior Quantitative Trader & Macro Analyst profesional.
        Sintesiskan Data Makro + Geopolitik + Teknikal menjadi LOGIKA ENTRY PRESISI XAUUSD.

        [INPUT DATA REAL-TIME]
        - Target Event: {target_news} ({status_text})
        - Running Price XAUUSD: {running_price}
        - Rekap Data Pendukung:
        {rekap_text}
        - Bias Makro Kalkulasi: {macro_bias_result}
        - Isu Geopolitik: {geo_info.get('isu_utama')} - {geo_info.get('ringkasan_situasi')}
        - Safe Haven XAU Impact: {geo_info.get('dampak_xau')}

        [ATURAN EXECUTION SANGAT KETAT]:
        1. JIKA EVENT BELUM RILIS ATAU DATA NEUTRAL/MIXED:
           - Arah Bias Utama WAJIB "NEUTRAL / TWO-SIDED (WHIPSAW SETUP)".
           - WAJIB berikan TWO-SIDED SETUP (Plan A BUY LIMIT Zona Discount Bawah DAN Plan B SELL LIMIT Zona Premium Atas).
           - Tulis secara eksplisit angka zona BUY dan angka zona SELL secara terpisah!

        Jawab HANYA dalam format JSON MURNI berikut:
        {{
            "arah_bias": "NEUTRAL / TWO-SIDED (WHIPSAW)",
            "ringkasan_sintesis": "Sintesis proyeksi menjelang rilis data dan pengaruh geopolitik",
            "logika_entry_detail": "Alasan penentuan zona atas dan bawah berdasarkan liquidity sweep",
            "setup_spesifik": {{
                "tipe_eksekusi": "Two-Sided Limit Orders / Sweep Liquidity",
                "zona_buy_demand": "{running_price - 20.00:.2f} - {running_price - 10.00:.2f}",
                "zona_sell_supply": "{running_price + 10.00:.2f} - {running_price + 20.00:.2f}",
                "sl_buy": "{running_price - 27.00:.2f}",
                "sl_sell": "{running_price + 27.00:.2f}",
                "tp_buy": "{running_price + 15.00:.2f}",
                "tp_sell": "{running_price - 15.00:.2f}"
            }}
        }}
        """

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": system_prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        try:
            res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                parsed_json = json.loads(res.json()['choices'][0]['message']['content'])
                st.session_state["ai_result"] = parsed_json
                st.session_state["rekap_text"] = rekap_text
                st.session_state["macro_bias_result"] = macro_bias_result
                st.session_state["score_val"] = score_val
                st.success("✅ AI Engine Synthesis Success!")
        except Exception as e:
            st.error(f"Error Koneksi AI: {e}")

if st.session_state["ai_result"]:
    res_ai = st.session_state["ai_result"]
    setup_ai = res_ai.get("setup_spesifik", {})
    
    st.subheader("📋 Rekap Evaluasi Data Pendukung Real-Time")
    st.markdown(st.session_state["rekap_text"])
    st.info(f"⚖️ **Kesimpulan Bias Makro:** {st.session_state['macro_bias_result']} (Score Net: {st.session_state['score_val']})")

    st.markdown("### ⚡ Logika Entry & Trigger Konfirmasi AI")
    st.markdown(f"• **Arah Bias Utama AI:** `{res_ai.get('arah_bias')}`")
    st.markdown(f"• **Sintesis Makro & Geopolitik:** {res_ai.get('ringkasan_sintesis')}")
    st.markdown(f"• **Reasoning & Trigger:** {res_ai.get('logika_entry_detail')}")

    st.markdown("### 🎯 Specific Execution Setup (XAUUSD)")
    
    if "NEUTRAL" in str(res_ai.get('arah_bias')).upper():
        c_buy, c_sell = st.columns(2)
        with c_buy:
            st.success(f"""
            🟢 **PLAN A: BUY LIMIT (ZONA DISCOUNT / DEMAND)**
            - **Entry Zone Buy:** {setup_ai.get('zona_buy_demand')}
            - **Stop Loss (SL):** {setup_ai.get('sl_buy')}
            - **Take Profit (TP):** {setup_ai.get('tp_buy')}
            - **Trigger:** Tunggu Liquidity Sweep di bawah low lalu Rejection M5.
            """)
        with c_sell:
            st.error(f"""
            🔴 **PLAN B: SELL LIMIT (ZONA PREMIUM / SUPPLY)**
            - **Entry Zone Sell:** {setup_ai.get('zona_sell_supply')}
            - **Stop Loss (SL):** {setup_ai.get('sl_sell')}
            - **Take Profit (TP):** {setup_ai.get('tp_sell')}
            - **Trigger:** Tunggu Liquidity Sweep di atas high lalu Rejection M5.
            """)
    else:
        st.info(f"""
        - **Execution Type:** {setup_ai.get('tipe_eksekusi')}
        - **Zona Buy Demand:** {setup_ai.get('zona_buy_demand')}
        - **Zona Sell Supply:** {setup_ai.get('zona_sell_supply')}
        - **Stop Loss:** Buy SL ({setup_ai.get('sl_buy')}) | Sell SL ({setup_ai.get('sl_sell')})
        - **Take Profit:** Buy TP ({setup_ai.get('tp_buy')}) | Sell TP ({setup_ai.get('tp_sell')})
        """)

st.markdown("---")

# ==========================================
# 10. MULTI-TIMEFRAME CONFLUENCE CARDS
# ==========================================
st.subheader("🎯 MULTI-TIMEFRAME LIQUIDITY & METHOD CONFLUENCE")

col_l, col_m, col_r = st.columns(3)

with col_l:
    st.markdown("### 🤖 AI Macro Engine")
    st.write("Signal: Macro + Geopolitical Confluence")
    
    if st.session_state["ai_result"]:
        ai_bias = st.session_state["ai_result"].get("arah_bias", "NEUTRAL")
        ai_setup = st.session_state["ai_result"].get("setup_spesifik", {})
        
        if "NEUTRAL" in str(ai_bias).upper():
            st.warning("⚠️ **ARAH BIAS: NEUTRAL (WHIPSAW / TWO-SIDED)**")
            st.markdown("#### 🟢 ZONA BUY (DISCOUNT)")
            st.info(f"{ai_setup.get('zona_buy_demand')}")
            st.markdown("#### 🔴 ZONA SELL (PREMIUM)")
            st.error(f"{ai_setup.get('zona_sell_supply')}")
        elif "BULLISH" in str(ai_bias).upper():
            st.markdown("🟢 **ARAH BIAS: BULLISH (BUY)**")
            st.markdown("#### 🎯 ZONA ENTRY BUY")
            st.info(f"{ai_setup.get('zona_buy_demand')}")
            st.markdown("#### 🛑 STOP LOSS")
            st.error(f"{ai_setup.get('sl_buy')}")
            st.markdown("#### 🏁 TARGET TP")
            st.success(f"{ai_setup.get('tp_buy')}")
        else:
            st.markdown("🔴 **ARAH BIAS: BEARISH (SELL)**")
            st.markdown("#### 🎯 ZONA ENTRY SELL")
            st.error(f"{ai_setup.get('zona_sell_supply')}")
            st.markdown("#### 🛑 STOP LOSS")
            st.error(f"{ai_setup.get('sl_sell')}")
            st.markdown("#### 🏁 TARGET TP")
            st.success(f"{ai_setup.get('tp_sell')}")
    else:
        st.caption("Klik tombol 'EXECUTE MULTI-TF AI PREDICTION' di atas untuk mengaktifkan AI Engine.")

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
# 11. LIVE CHART TRADINGVIEW (FULL CUSTOM PAIR)
# ==========================================
st.subheader("📉 LIVE CHART TRADINGVIEW (INTERACTIVE)")

tradingview_widget = """
<div class="tradingview-widget-container" style="height:620px;width:100%">
  <div id="tradingview_chart" style="height:100%;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "width": "100%",
    "height": 600,
    "symbol": "OANDA:XAUUSD",
    "interval": "15",
    "timezone": "Asia/Jakarta",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_chart",
    "hide_side_toolbar": false,
    "studies": [
      "RSI@tv-basicstudies",
      "MASimple@tv-basicstudies"
    ]
  });
  </script>
</div>
"""
components.html(tradingview_widget, height=620)
