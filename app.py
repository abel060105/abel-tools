# ==============================================================================
# 1. INSTALL LIBRARY UTAMA
# ==============================================================================
!pip install -q streamlit pandas requests

# ==============================================================================
# 2. TULIS FILE DASHBOARD (app.py)
# ==============================================================================
with open("app.py", "w", encoding="utf-8") as f:
    f.write(r'''import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import requests
import json

st.set_page_config(page_title="ABEL FX - Macro, Liquidity & DeepSeek Astrodox", page_icon="📈", layout="wide")

now = datetime.datetime.now()

# -------------------------------------------------------------
# CONFIG API KEY DEEPSEEK
# -------------------------------------------------------------
DEEPSEEK_API_KEY = "sk-07b982ca8271453aa04ffc0ce4d9d1f0"

def get_deepseek_macro_data(indicator_name, event_name, default_fore, default_prev):
    """DeepSeek Engine 1: Forecast & Previous Estimator"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    Estimasi angka 'forecast' dan 'previous' terbaru untuk indikator '{indicator_name}' menjelang rilis '{event_name}'.
    Jawab HANYA JSON: {{"forecast": {default_fore}, "previous": {default_prev}}}
    """
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a precise JSON-only financial data provider."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=5)
        if res.status_code == 200:
            content = res.json()['choices'][0]['message']['content'].strip()
            if content.startswith("```"):
                content = content.split("```")[1].replace("json", "").strip()
            parsed = json.loads(content)
            return float(parsed.get('forecast', default_fore)), float(parsed.get('previous', default_prev))
    except Exception:
        pass
    return default_fore, default_prev

def analyze_with_deepseek_ai(event_name, main_released, inputs_data):
    """DeepSeek Engine 2: Financial Macro Impact Analyzer"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    summary_data = [f"- {item['name']}: Actual={item['act']}, Forecast={item['fore']}, Previous={item['prev']}" for item in inputs_data]
    data_str = "\n".join(summary_data)
    
    status_str = "SUDAH RILIS (POST-NEWS)" if main_released else "OTW RILIS (PRE-NEWS)"
    
    prompt = f"""
    Analisis data makro untuk '{event_name}' (Status Event: {status_str}):
    {data_str}
    Jawab HANYA JSON murni:
    {{
        "usd_impact": "BULLISH (SANGAT KUAT)" / "BEARISH (SANGAT LEMAH)" / "NETRAL / SIDEWAYS",
        "xau_signal": "BUY XAUUSD" / "SELL XAUUSD" / "WAIT / NO TRADE",
        "ai_bias": "BULLISH" / "BEARISH" / "NEUTRAL",
        "probability": 75,
        "ai_expansion_pips": 380
    }}
    """
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a senior macro forex analyst. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=8)
        if res.status_code == 200:
            content = res.json()['choices'][0]['message']['content'].strip()
            if content.startswith("```"):
                content = content.split("```")[1].replace("json", "").strip()
            parsed = json.loads(content)
            return (
                parsed.get("usd_impact"), 
                parsed.get("xau_signal"), 
                parsed.get("ai_bias"), 
                int(parsed.get("probability", 65)),
                int(parsed.get("ai_expansion_pips", 380))
            )
    except Exception:
        pass
    return None, None, None, None, 380

def get_deepseek_astrodox_analysis(event_name, date_str):
    """DeepSeek Engine 3: Astrodox Planetary Transit Synthesizer"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    Analisis posisi transit planet pada tanggal: {date_str} untuk '{event_name}'.
    Jawab HANYA JSON murni:
    {{
        "astro_bias": "BULLISH" / "BEARISH",
        "aspect_name": "Moon in Taurus Trine Venus & Jupiter",
        "pips_expansion": 380,
        "description": "Harmonisasi energi Jupiter & Bulan memicu penguatan Emas."
    }}
    """
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert financial astrologer for gold (XAUUSD). Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=8)
        if res.status_code == 200:
            content = res.json()['choices'][0]['message']['content'].strip()
            if content.startswith("```"):
                content = content.split("```")[1].replace("json", "").strip()
            parsed = json.loads(content)
            return (
                parsed.get("astro_bias", "BULLISH"),
                parsed.get("aspect_name", "Transit Aspect Active"),
                int(parsed.get("pips_expansion", 380)),
                parsed.get("description", "Analisis Astrodox berbasis transits planet.")
            )
    except Exception:
        pass
    return "BULLISH", "Moon/Sun Planetary Transits", 380, "Standard Astrodox Volatility Target"

st.title("⚡ ABEL FX - DUAL ENGINE & LIQUIDITY MAPPER")
st.caption("Sistem Prediksi News High Impact dengan Status Rilis Main Event & Expanded TP Target")

# -------------------------------------------------------------
# SIDEBAR: FILTER NEWS, JADWAL & SWITCH STATUS MAIN EVENT
# -------------------------------------------------------------
st.sidebar.header("⚙️ 1. Target Main Big News")
event_type = st.sidebar.selectbox(
    "Pilih Target Big News:",
    ["NFP (Non-Farm Payrolls)", "CPI (Consumer Price Index)", "FOMC (Interest Rate Decision)"]
)

st.sidebar.markdown("---")
st.sidebar.header("📡 2. Status Rilis Main Event")
main_released = st.sidebar.toggle("Main Event Sudah Rilis?", value=False)

if main_released:
    st.sidebar.success(f"✅ {event_type} STATUS: SUDAH RILIS")
else:
    st.sidebar.warning(f"⏳ {event_type} STATUS: OTW RILIS (PRE-NEWS)")

st.sidebar.markdown("---")
st.sidebar.header("📅 3. Jadwal Official")
manual_day = st.sidebar.number_input("Tanggal Rilis:", min_value=1, max_value=31, value=7, step=1)
months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
selected_month = st.sidebar.selectbox("Bulan Rilis:", months, index=7)
selected_year = st.sidebar.number_input("Tahun Rilis:", min_value=2024, max_value=2030, value=now.year, step=1)
manual_time = st.sidebar.text_input("Jam Rilis (WIB):", value="19:30 WIB" if "FOMC" not in event_type else "01:00 WIB")

date_formatted = f"{manual_day:02d} {selected_month} {selected_year}"

st.sidebar.markdown("---")
st.sidebar.header("🔮 4. Astrodox Engine Settings")
use_astrodox = st.sidebar.toggle("Aktifkan Astrodox Engine", value=True)

if use_astrodox:
    st.sidebar.success("🔮 Astrodox Status: ACTIVE")
else:
    st.sidebar.warning("⚪ Astrodox Status: OFF (Full Pure AI Mode)")

# Setup Data Indikator
if "NFP" in event_type:
    event_name = "Non-Farm Payrolls (NFP)"
    indicators = [
        {"name": "ADP Non-Farm Employment Change", "schedule": "Rabu sebelum NFP (19:15 WIB)", "unit": "K (Ribu)", "weight": 0.30, "invert": False, "def_act": 175.0, "def_fore": 150.0, "def_prev": 120.0},
        {"name": "Initial Jobless Claims", "schedule": "Kamis sebelum NFP (19:30 WIB)", "unit": "K (Ribu)", "weight": 0.25, "invert": True, "def_act": 240.0, "def_fore": 235.0, "def_prev": 225.0},
        {"name": "ISM Manufacturing PMI (Employment)", "schedule": "Hari ke-1/2 bulan rilis (21:00 WIB)", "unit": "Index Points", "weight": 0.25, "invert": False, "def_act": 48.5, "def_fore": 47.0, "def_prev": 46.5},
        {"name": "JOLTS Job Openings", "schedule": "Selasa sebelum NFP (21:00 WIB)", "unit": "M (Juta)", "weight": 0.20, "invert": False, "def_act": 8.1, "def_fore": 7.9, "def_prev": 7.8}
    ]
elif "CPI" in event_type:
    event_name = "Consumer Price Index (CPI)"
    indicators = [
        {"name": "Producer Price Index (PPI) MoM", "schedule": "1 Hari sebelum CPI (19:30 WIB)", "unit": "% (Persen)", "weight": 0.35, "invert": False, "def_act": 0.3, "def_fore": 0.2, "def_prev": 0.1},
        {"name": "Import Price Index MoM", "schedule": "2 Hari sebelum CPI (19:30 WIB)", "unit": "% (Persen)", "weight": 0.25, "invert": False, "def_act": 0.2, "def_fore": 0.1, "def_prev": -0.1},
        {"name": "Michigan Consumer Sentiment", "schedule": "Jumat minggu sebelumnya (21:00 WIB)", "unit": "Index Points", "weight": 0.20, "invert": False, "def_act": 68.5, "def_fore": 66.0, "def_prev": 64.2},
        {"name": "Core CPI Previous Trend", "schedule": "Bulan Lalu", "unit": "% (Persen)", "weight": 0.20, "invert": False, "def_act": 0.3, "def_fore": 0.3, "def_prev": 0.2}
    ]
else:
    event_name = "FOMC Interest Rate Decision"
    indicators = [
        {"name": "Core PCE Price Index MoM", "schedule": "Akhir bulan lalu (19:30 WIB)", "unit": "% (Persen)", "weight": 0.35, "invert": False, "def_act": 0.3, "def_fore": 0.2, "def_prev": 0.2},
        {"name": "GDP Advance Estimate QoQ", "schedule": "3 Minggu sebelum FOMC (19:30 WIB)", "unit": "% (Persen)", "weight": 0.25, "invert": False, "def_act": 2.8, "def_fore": 2.5, "def_prev": 1.4},
        {"name": "Retail Sales MoM", "schedule": "Tengah bulan (19:30 WIB)", "unit": "% (Persen)", "weight": 0.20, "invert": False, "def_act": 0.4, "def_fore": 0.3, "def_prev": 0.1},
        {"name": "Beige Book Tone", "schedule": "2 Minggu sebelum FOMC (01:00 WIB)", "unit": "Skala 1 (Dovish) - 5 (Hawkish)", "weight": 0.20, "invert": False, "def_act": 4.0, "def_fore": 3.0, "def_prev": 3.0}
    ]

# Header Judul Event dengan Status Rilis Main Event
st.markdown("---")
h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.subheader(f"📌 TARGET EVENT: {event_name} - {date_formatted} ({manual_time})")
with h_col2:
    if main_released:
        st.markdown("### <span style='color: #00FF66;'>[✅ SUDAH RILIS]</span>", unsafe_allow_html=True)
    else:
        st.markdown("### <span style='color: #FFCC00;'>[⏳ OTW RILIS]</span>", unsafe_allow_html=True)

# Input Harga Running
st.sidebar.markdown("---")
st.sidebar.header("🎯 Price Reference (XAUUSD)")
current_xau = st.sidebar.number_input("Harga Running XAUUSD (H-5 Menit):", value=4314.00, step=1.00)

col_left, col_right = st.columns([2, 1])

inputs_data = []
with col_left:
    st.write("### 📊 Data Indikator Pendukung Real-Time & Auto-Sync")
    st.caption("💡 *Centang 'Auto-Sync DeepSeek' jika malas mengisi manual. Angka hasil AI bisa kamu edit langsung!*")
    
    for idx, ind in enumerate(indicators):
        name_str = ind["name"]
        sched_str = ind["schedule"]
        unit_str = ind["unit"]
        
        c_head, c_toggle = st.columns([2.5, 1.5])
        with c_head:
            st.markdown(f"**🔹 {name_str}**")
            st.caption(f"⏱️ Jadwal: {sched_str} | Satuan: {unit_str}")
        with c_toggle:
            auto_sync = st.checkbox("🤖 Auto-Sync", value=False, key=f"auto_{idx}")
        
        val_fore = ind['def_fore']
        val_prev = ind['def_prev']
        
        if auto_sync:
            val_fore, val_prev = get_deepseek_macro_data(name_str, event_name, ind['def_fore'], ind['def_prev'])
            st.caption("`[🤖 SOURCE: AUTO DEEPSEEK AI]`")

        c1, c2, c3 = st.columns(3)
        act = c1.number_input("Actual", value=ind['def_act'], key=f"act_{idx}")
        fore = c2.number_input("Forecast", value=val_fore, key=f"fore_{idx}")
        prev = c3.number_input("Previous", value=val_prev, key=f"prev_{idx}")
        
        inputs_data.append({
            "name": ind['name'], 
            "act": act, 
            "fore": fore, 
            "prev": prev, 
            "w": ind['weight'], 
            "invert": ind['invert']
        })

with col_right:
    st.write("### 🤖 ABEL FX Engine AI (DeepSeek)")
    calc_btn = st.button("⚡ EXECUTE AI PREDICTION", type="primary", use_container_width=True)

# -------------------------------------------------------------
# EXECUTE PREDIKSI AI DEEPSEEK & ASTRODOX DYNAMIC ANALYZER
# -------------------------------------------------------------
usd, signal, ai_bias, prob, ai_expansion_pips = analyze_with_deepseek_ai(event_name, main_released, inputs_data)
if not (usd and signal):
    score = 0.0
    for item in inputs_data:
        diff_forecast = item['act'] - item['fore']
        diff_previous = item['act'] - item['prev']
        total_diff = (diff_forecast * 0.8) + (diff_previous * 0.2)
        if item['invert']:
            total_diff = -total_diff
        if total_diff > 0:
            score += item['w']
        elif total_diff < 0:
            score -= item['w']

    if score > 0.15:
        usd, signal, ai_bias, prob, ai_expansion_pips = "BULLISH (SANGAT KUAT)", "SELL XAUUSD", "BEARISH", int(65 + score * 25), 380
    elif score < -0.15:
        usd, signal, ai_bias, prob, ai_expansion_pips = "BEARISH (SANGAT LEMAH)", "BUY XAUUSD", "BULLISH", int(65 + abs(score) * 25), 380
    else:
        usd, signal, ai_bias, prob, ai_expansion_pips = "NETRAL / SIDEWAYS", "WAIT / NO TRADE", "NEUTRAL", 50, 0

# Fetch Dynamic Astrodox jika diaktifkan
if use_astrodox:
    astro_bias, astro_aspect_name, pips_expansion, astro_desc = get_deepseek_astrodox_analysis(event_name, date_formatted)
else:
    astro_bias, astro_aspect_name, pips_expansion, astro_desc = "OFF", "Astrodox Disabled", 0, "Astrodox Engine di-nonaktifkan oleh user."

st.markdown("---")
res1, res2, res3 = st.columns(3)

with res1:
    st.metric("Prediksi Dampak USD (DeepSeek)", usd)
with res2:
    st.metric("Rekomendasi XAUUSD (DeepSeek)", signal)
with res3:
    st.metric("Probabilitas AI", f"{min(prob, 92)}%")

# -------------------------------------------------------------
# INDEPENDENT ZONING & COINGLASS LIQUIDITY POOLS (FULL EXPANSION TP)
# -------------------------------------------------------------
st.markdown("---")
st.header("🎯 INDEPENDENT LIQUIDITY ZONES (AI vs ASTRO)")

# Area Immediate Entry Zone (Coinglass Local Pool)
upper_pool_min = current_xau + 1.50
upper_pool_max = current_xau + 4.00

lower_pool_min = current_xau - 4.00
lower_pool_max = current_xau - 1.50

# Target AI dengan Full Expansion Pips ($35 - $50 Expansion Target)
ai_pips_delta = ai_expansion_pips / 10.0 if ai_expansion_pips > 0 else 38.0

if ai_bias == "BULLISH":
    ai_entry_type = "🟢 BUY LIMIT (Lower Pool)"
    ai_entry_zone = f"{lower_pool_min:.2f} - {lower_pool_max:.2f}"
    ai_tp_target = f"{(current_xau + ai_pips_delta - 3.00):.2f} - {(current_xau + ai_pips_delta):.2f}"
elif ai_bias == "BEARISH":
    ai_entry_type = "🔴 SELL LIMIT (Upper Pool)"
    ai_entry_zone = f"{upper_pool_min:.2f} - {upper_pool_max:.2f}"
    ai_tp_target = f"{(current_xau - ai_pips_delta):.2f} - {(current_xau - ai_pips_delta + 3.00):.2f}"
else:
    ai_entry_type = "⚪ WAIT / NO TRADE"
    ai_entry_zone = "Pasar Sideways"
    ai_tp_target = "N/A"

# Target Astrodox
if use_astrodox:
    astro_pips_delta = pips_expansion / 10.0
    if astro_bias == "BULLISH":
        astro_entry_type = "🟢 BUY LIMIT (Lower Pool)"
        astro_entry_zone = f"{lower_pool_min:.2f} - {lower_pool_max:.2f}"
        astro_tp_target = f"{(current_xau + astro_pips_delta - 3.00):.2f} - {(current_xau + astro_pips_delta):.2f}"
    else:
        astro_entry_type = "🔴 SELL LIMIT (Upper Pool)"
        astro_entry_zone = f"{upper_pool_min:.2f} - {upper_pool_max:.2f}"
        astro_tp_target = f"{(current_xau - astro_pips_delta):.2f} - {(current_xau - astro_pips_delta + 3.00):.2f}"

# -------------------------------------------------------------
# CONFLUENCE & ROADMAP SKENARIO H-DETIK
# -------------------------------------------------------------
st.subheader("⚠️ CONFLUENCE & SKENARIO EXECUTION ROADMAP")

if not use_astrodox:
    st.info(f"💡 **PURE AI MODE ACTIVE:** Menggunakan 100% Signal AI DeepSeek -> **{ai_entry_type}** di zona `{ai_entry_zone}` dengan TP Target Expansion di `{ai_tp_target}`.")
else:
    if ai_bias == astro_bias:
        st.success(f"🟢 **FULL CONFLUENCE (AI & ASTRO SEARAH: {ai_bias})**\n\n"
                   f"Kedua Engine sepakat **{ai_bias}**! Gunakan eksekusi utama: **{ai_entry_type}** pada zona `{ai_entry_zone}` dengan Target TP Expansion di `{ai_tp_target}`.")
    elif ai_bias == "NEUTRAL":
        st.warning(f"⚪ **AI NEUTRAL vs ASTRODOX {astro_bias}**\n\n"
                   f"Data berita seimbang. Ikuti panduan Astrodox Engine: **{astro_entry_type}** pada zona `{astro_entry_zone}` dengan Target TP `{astro_tp_target}`.")
    else:
        st.error(f"🔴 **DIVERGENCE BENTROK (AI: {ai_bias} vs ASTRO: {astro_bias})**\n\n"
                 f"**Tergantung Liquidity mana yang disapu duluan pada H-Detik Rilis News:**\n"
                 f"* 📌 **Skenario A (Jika Naik Duluan):** Ambil **SELL LIMIT** AI di Upper Pool (`{upper_pool_min:.2f} - {upper_pool_max:.2f}`) dengan Target TP di `{ai_tp_target}`.\n"
                 f"* 📌 **Skenario B (Jika Turun Duluan):** Ambil **BUY LIMIT** Astrodox di Lower Pool (`{lower_pool_min:.2f} - {lower_pool_max:.2f}`) dengan Target TP di `{astro_tp_target}`.")

# -------------------------------------------------------------
# ZONA AI vs ASTRODOX (BOX COMPARISON)
# -------------------------------------------------------------
st.markdown("---")
ai_box, astro_box = st.columns(2)

with ai_box:
    st.subheader("🤖 AI Engine Liquidity Zone")
    st.write(f"**Arah Signal AI:** `{ai_bias}`")
    st.write(f"**Tipe Eksekusi:** `{ai_entry_type}`")
    st.markdown("#### 🎯 ZONA ENTRY AI POOL")
    st.code(ai_entry_zone)
    st.markdown(f"#### 🏁 TARGET TP AI EXPANSION (+{ai_expansion_pips} Pips)")
    st.code(ai_tp_target)

with astro_box:
    st.subheader("🔮 Astrodox Engine Liquidity Zone")
    if use_astrodox:
        st.write(f"**Arah Signal Astrodox:** `{astro_bias}` (`{astro_aspect_name}`)")
        st.write(f"**Tipe Eksekusi:** `{astro_entry_type}`")
        st.markdown("#### 🎯 ZONA ENTRY ASTRODOX POOL")
        st.code(astro_entry_zone)
        st.markdown(f"#### 🏁 TARGET TP ASTRODOX EXPANSION (+{pips_expansion} Pips)")
        st.code(astro_tp_target)
    else:
        st.info("🔮 **Astrodox Engine Di-nonaktifkan.**\n\nAktifkan switch 'Aktifkan Astrodox Engine' di sidebar jika ingin mengaktifkan kembali analisis Astrodox.")

# -------------------------------------------------------------
# TRADINGVIEW LIVE CHART EMBED
# -------------------------------------------------------------
st.markdown("---")
st.subheader("📉 LIVE CHART TRADINGVIEW (XAUUSD)")

tv_html = """
<div class="tradingview-widget-container" style="height:600px;width:100%;">
  <div id="tradingview_xau" style="height:calc(100% - 32px);width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "autosize": true,
    "symbol": "OANDA:XAUUSD",
    "interval": "5",
    "timezone": "Asia/Jakarta",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_xau"
  });
  </script>
</div>
"""
components.html(tv_html, height=620)
''')

# ==============================================================================
# 3. JALANKAN STREAMLIT SERVER & CLOUDFLARE TUNNEL (PUBLIC LINK)
# ==============================================================================
import subprocess
subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501"])

!wget -q -O cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
!chmod +x cloudflared
!./cloudflared tunnel --url http://localhost:8501
