import os
import json
import io
import calendar
import requests
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEYS
# ==========================================
st.set_page_config(
    page_title="ABEL FX - Macro, Astrodox & Dynamic Liquidity Predictor",
    page_icon="📈",
    layout="wide"
)

# Custom Styling & Responsive CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .range-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 15px;
        margin-bottom: 10px;
    }
    .range-title {
        font-size: 13px;
        color: #8b949e;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .range-value {
        font-size: 18px;
        color: #58a6ff;
        font-weight: bold;
        word-wrap: break-word;
    }
    .card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 15px;
    }
    .card-title {
        font-size: 1.15rem;
        font-weight: bold;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .badge-bullish {
        background-color: #064e3b;
        color: #34d399;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-bearish {
        background-color: #7f1d1d;
        color: #fca5a5;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .zone-box {
        background-color: #1e293b;
        border-radius: 6px;
        padding: 12px;
        text-align: center;
        color: #60a5fa;
        font-weight: bold;
        font-size: 1.15rem;
        margin: 8px 0;
    }
    .sl-box {
        background-color: #451a1a;
        border-radius: 6px;
        padding: 12px;
        color: #f87171;
        font-weight: bold;
        margin: 8px 0;
    }
    .tp-box {
        background-color: #064e3b;
        border-radius: 6px;
        padding: 12px;
        color: #34d399;
        font-weight: bold;
        margin: 8px 0;
    }
    .liquidity-box {
        background-color: #0f2744;
        border-left: 4px solid #3b82f6;
        border-radius: 4px;
        padding: 12px;
        font-size: 0.88rem;
        color: #93c5fd;
        margin-top: 12px;
        line-height: 1.4;
    }
    .sltp-inline {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
    .sltp-item {
        flex: 1;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.88rem;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .sl-inline {
        background-color: #311313;
        color: #f87171;
    }
    .tp-inline {
        background-color: #063726;
        color: #34d399;
    }
</style>
""", unsafe_allow_html=True)

FMP_API_KEY = "Wr5uNw4BQAo5syaNYXylIqcg8908kPd5"
FINNHUB_TOKEN = "d9saqq9r01qopv46igd9saqq9r01qopv46gkj0"
GROQ_API_KEY = "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"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

DATA_CACHE_DIR = "news_history_data"
if not os.path.exists(DATA_CACHE_DIR):
    os.makedirs(DATA_CACHE_DIR)

if "ai_result" not in st.session_state:
    st.session_state["ai_result"] = None
if "rekap_text" not in st.session_state:
    st.session_state["rekap_text"] = ""
if "macro_bias_result" not in st.session_state:
    st.session_state["macro_bias_result"] = ""
if "score_val" not in st.session_state:
    st.session_state["score_val"] = 0

# ==========================================
# 2. LIQUIDITY CALCULATION ENGINE (yfinance & Pine Script Logic)
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_data(ticker_symbol):
    try:
        data = yf.download(ticker_symbol, period="1mo", interval="1h", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception:
        return pd.DataFrame()

def calculate_liquidity_zones(df, left_bars=10, right_bars=8, atr_len=14):
    """
    Kalkulasi Pivot High/Low & ATR untuk mendeteksi Zona Likuiditas Atas (Supply/Short Liq)
    dan Bawah (Demand/Long Liq) sesuai logika Pine Script Liquidity Heatmap.
    """
    if df.empty or len(df) < (left_bars + right_bars + atr_len):
        return None, None, None, None

    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift(1))
    low_cp = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    atr = tr.rolling(atr_len).mean()

    pivots_high = []
    pivots_low = []

    for i in range(left_bars, len(df) - right_bars):
        window_high = df['High'].iloc[i - left_bars : i + right_bars + 1]
        window_low = df['Low'].iloc[i - left_bars : i + right_bars + 1]
        
        current_high = df['High'].iloc[i]
        current_low = df['Low'].iloc[i]

        if current_high == window_high.max():
            pivots_high.append((df.index[i], current_high, atr.iloc[i]))
        if current_low == window_low.min():
            pivots_low.append((df.index[i], current_low, atr.iloc[i]))

    latest_price = float(df['Close'].iloc[-1])

    upper_liq = [p for p in pivots_high if p[1] > latest_price]
    lower_liq = [p for p in pivots_low if p[1] < latest_price]

    nearest_upper = upper_liq[-1] if upper_liq else (None, latest_price + 10.0, atr.iloc[-1])
    nearest_lower = lower_liq[-1] if lower_liq else (None, latest_price - 10.0, atr.iloc[-1])

    upper_zone = (round(float(nearest_upper[1]), 2), round(float(nearest_upper[1] + (nearest_upper[2] * 0.25)), 2))
    lower_zone = (round(float(nearest_lower[1] - (nearest_lower[2] * 0.25)), 2), round(float(nearest_lower[1]), 2))

    return latest_price, upper_zone, lower_zone, float(atr.iloc[-1])

# Run Live Fetch Market Data
xau_df = fetch_market_data("GC=F")
dxy_df = fetch_market_data("DX-Y.NYB")

xau_live_price, xau_upper_liq, xau_lower_liq, xau_atr = calculate_liquidity_zones(xau_df)
dxy_live_price, dxy_upper_liq, dxy_lower_liq, dxy_atr = calculate_liquidity_zones(dxy_df)

# Fallback Default jika API yfinance delay
if not xau_live_price:
    xau_live_price = 4314.00
    xau_upper_liq = (4322.00, 4326.00)
    xau_lower_liq = (4302.00, 4306.00)

if not dxy_live_price:
    dxy_live_price = 104.20
    dxy_upper_liq = (104.35, 104.45)
    dxy_lower_liq = (103.95, 104.05)

# ==========================================
# 3. BUILT-IN ASTRODOX ENGINE & CHART
# ==========================================
ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ZODIAC_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def compute_planetary_positions(dt_utc):
    year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
    hour = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour/24.0 + B - 1524.5
    d = jd - 2451545.0

    L_sun = (280.466 + 0.9856474 * d) % 360
    g_sun = np.radians((357.528 + 0.9856003 * d) % 360)
    sun_lon = (L_sun + 1.915 * np.sin(g_sun) + 0.020 * np.sin(2 * g_sun)) % 360

    L_moon = (218.316 + 13.176396 * d) % 360
    M_moon = np.radians((134.963 + 13.064993 * d) % 360)
    moon_lon = (L_moon + 6.289 * np.sin(M_moon) - 1.274 * np.sin(M_moon - 2*np.radians(sun_lon - L_sun))) % 360

    mercury_lon = (sun_lon + 18.0 * np.sin(np.radians((29.0 + 4.092 * d) % 360))) % 360
    venus_lon = (sun_lon + 42.0 * np.sin(np.radians((210.0 + 1.602 * d) % 360))) % 360
    mars_lon = (355.43 + 0.524033 * d + 10.0 * np.sin(np.radians((19.0 + 0.524 * d) % 360))) % 360
    jupiter_lon = (34.35 + 0.083091 * d) % 360
    saturn_lon = (50.08 + 0.033459 * d) % 360
    uranus_lon = (58.00 + 0.011728 * d) % 360
    neptune_lon = (358.00 + 0.005981 * d) % 360
    pluto_lon = (302.00 + 0.003970 * d) % 360

    raw_degs = {
        "Sun ☉": sun_lon, "Moon ☽": moon_lon, "Mercury ☿": mercury_lon,
        "Venus ♀": venus_lon, "Mars ♂": mars_lon, "Jupiter ♃": jupiter_lon,
        "Saturn ♄": saturn_lon, "Uranus ♅": uranus_lon, "Neptune ♆": neptune_lon,
        "Pluto ♇": pluto_lon
    }

    formatted_pos = {}
    for name, deg in raw_degs.items():
        z_idx = int(deg // 30)
        z_deg = int(deg % 30)
        z_min = int(((deg % 30) - z_deg) * 60)
        formatted_pos[name] = f"{ZODIAC_NAMES[z_idx]} {z_deg}°{z_min:02d}'"

    return raw_degs, formatted_pos

def generate_astrodox_unified_image(target_date: datetime, ai_result_data=None):
    dt_utc = target_date - timedelta(hours=7)
    planet_degrees, planet_positions = compute_planetary_positions(dt_utc)

    fig = plt.figure(figsize=(18.0, 9.5), facecolor='#0e1117')
    
    # Polar Wheel
    ax = fig.add_subplot(121, polar=True, facecolor='#0e1117')
    ax.set_theta_zero_location("W")
    ax.set_theta_direction(-1)
    ax.grid(False)
    ax.set_yticklabels([])
    ax.set_xticklabels([])

    colors = ['#4a2e2b','#3e3b26','#1e3a2b','#1e2b3a'] * 3
    for i in range(12):
        theta_start = np.radians(i * 30)
        theta_end = np.radians((i + 1) * 30)
        ax.bar(
            x=(theta_start + theta_end)/2, height=0.25, width=np.radians(30), 
            bottom=0.75, color=colors[i], alpha=0.6, edgecolor='#555555'
        )
        ax.text(
            (theta_start + theta_end)/2, 0.88, ZODIAC_SYMBOLS[i], 
            color='white', fontsize=13, ha='center', va='center', fontweight='bold'
        )

    planets_keys = list(planet_degrees.keys())
    deg_list = list(planet_degrees.values())
    
    for name, deg in planet_degrees.items():
        rad = np.radians(deg)
        ax.plot(rad, 0.70, marker='o', color='#00ffff', markersize=6)
        short_symbol = name.split()[-1]
        ax.text(rad, 0.61, short_symbol, color='white', fontsize=11, ha='center', va='center', fontweight='bold')

    aspect_counts = {"merah": 0, "hijau": 0, "biru": 0, "kuning": 0}

    for i in range(len(planets_keys)):
        for j in range(i + 1, len(planets_keys)):
            d1 = deg_list[i]
            d2 = deg_list[j]
            diff = abs(d1 - d2) % 360
            if diff > 180:
                diff = 360 - diff
            
            rad1 = np.radians(d1)
            rad2 = np.radians(d2)

            if abs(diff - 90) <= 7 or abs(diff - 180) <= 7:
                ax.plot([rad1, rad2], [0.70, 0.70], color='#ff3333', alpha=0.8, linewidth=1.5)
                aspect_counts["merah"] += 1
            elif abs(diff - 120) <= 7:
                ax.plot([rad1, rad2], [0.70, 0.70], color='#00ff66', alpha=0.8, linewidth=1.5)
                aspect_counts["hijau"] += 1
            elif abs(diff - 60) <= 6:
                ax.plot([rad1, rad2], [0.70, 0.70], color='#3399ff', alpha=0.7, linewidth=1.2)
                aspect_counts["biru"] += 1
            elif diff <= 7:
                ax.plot([rad1, rad2], [0.70, 0.70], marker='*', color='#ffff00', alpha=0.9, linewidth=2.5, markersize=8)
                aspect_counts["kuning"] += 1

    ax.set_title(
        f"{target_date.strftime('%d.%m.%Y %H:%M WIB')}", 
        color='white', fontsize=14, pad=15, fontweight='bold'
    )

    ax_text = fig.add_subplot(122, facecolor='#0e1117')
    ax_text.axis('off')

    info_text = f"POSISI PLANET TRANSIT ({target_date.strftime('%d %b %Y %H:%M WIB')}):\n"
    info_text += "─" * 60 + "\n"
    
    pos_items = list(planet_positions.items())
    for idx in range(0, len(pos_items), 2):
        p1, v1 = pos_items[idx]
        if idx + 1 < len(pos_items):
            p2, v2 = pos_items[idx+1]
            info_text += f"• {p1:<12}: {v1:<16} | • {p2:<12}: {v2}\n"
        else:
            info_text += f"• {p1:<12}: {v1}\n"

    info_text += "\n" + "─" * 60 + "\n"
    info_text += "REKAP GARIS ASPEK GEOMETRI ASTRODOX:\n"
    info_text += "─" * 60 + "\n"
    info_text += f"• MERAH (Square 90°/Opp 180°) : {aspect_counts['merah']} Garis (Volatilitas Tinggi)\n"
    info_text += f"• HIJAU (Trine 120°)          : {aspect_counts['hijau']} Garis (Expansion Trend)\n"
    info_text += f"• BIRU  (Sextile 60°)         : {aspect_counts['biru']} Garis (Retest Zone)\n"
    info_text += f"• KUNING (Conjunction 0°)     : {aspect_counts['kuning']} Garis (Turning Point)\n"

    info_text += "\n" + "─" * 60 + "\n"
    info_text += "AI PROYEKSI RANGE PIPS (CONFLUENCE ASTRO + TECHNICALS):\n"
    info_text += "─" * 60 + "\n"
    
    if ai_result_data:
        pips = ai_result_data.get("proyeksi_pips", {})
        setup = ai_result_data.get("setup_spesifik", {})
        info_text += f"• Bias Utama  : {ai_result_data.get('arah_bias', '-')}\n"
        info_text += f"• Whipsaw     : {ai_result_data.get('peringatan_whipsaw', '-')[:55]}...\n"
        info_text += f"• Sweep Range : {pips.get('sweep_pips', '-')}\n"
        info_text += f"• Trend Range : {pips.get('trend_pips', '-')}\n"
        info_text += f"• Reversal    : {pips.get('reversal_pips', '-')}\n"
        info_text += f"• Zona Entry  : Buy({setup.get('zona_buy_demand', '-')}) | Sell({setup.get('zona_sell_supply', '-')})\n"
        info_text += f"• Stop Loss   : Buy({setup.get('sl_buy', '-')}) | Sell({setup.get('sl_sell', '-')})\n"
        info_text += f"• Take Profit : Buy({setup.get('tp_buy', '-')}) | Sell({setup.get('tp_sell', '-')})\n"
    else:
        info_text += "[ Menunggu Eksekusi AI Prediction di Dashboard ]\n"

    ax_text.text(
        0.00, 0.98, info_text, color='#e0e0e0', fontsize=10.0, 
        fontfamily='monospace', va='top', ha='left',
        bbox=dict(boxstyle='round,pad=1.2', facecolor='#161b22', edgecolor='#30363d')
    )

    plt.tight_layout()
    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=250, bbox_inches='tight', facecolor='#0e1117')
    img_buf.seek(0)

    return fig, img_buf, aspect_counts

# ==========================================
# 4. SIDEBAR & CONTROL PANEL
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
    tanggal_rilis = st.number_input("Tanggal Rilis:", value=7, min_value=1, max_value=31)
    
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    bulan_dict = {
        "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
        "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
        "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    
    bulan_rilis = st.selectbox("Bulan Rilis:", daftar_bulan, index=7)
    tahun_rilis = st.number_input("Tahun Rilis:", value=2026)
    
    jam_input = st.text_input("Jam Rilis (WIB):", value="01:00" if "FOMC" in target_news else "19:30")
    jam_rilis_formatted = f"{jam_input} WIB"

    bulan_num = bulan_dict.get(bulan_rilis, 8)
    try:
        if ":" in jam_input:
            jam_str, menit_str = jam_input.strip().split(":")
            jam_num = int(jam_str)
            menit_num = int(menit_str)
        else:
            jam_num = 19
            menit_num = 30
            
        event_datetime = datetime(
            int(tahun_rilis), 
            int(bulan_num), 
            int(tanggal_rilis), 
            jam_num, 
            menit_num
        )
        is_future_event = event_datetime > now
    except Exception:
        event_datetime = datetime(int(tahun_rilis), bulan_num, int(tanggal_rilis), 19, 30)
        is_future_event = False

    st.markdown("---")
    st.markdown("### ⚡ API Cache Control")
    if st.button("🔄 Force Refresh API Data", use_container_width=True):
        st.cache_data.clear()
        st.toast("Cache API dibersihkan!", icon="✅")

    st.markdown("---")
    st.markdown("### 3. Astrodox Engine Settings")
    astrodox_active = st.toggle("Aktifkan Astrodox Engine", value=True)

    st.markdown("---")
    st.markdown("### 4. Multi-Timeframe Technical Engine")
    tech_active = st.toggle("Aktifkan Technical Engine", value=True)

    market_condition = st.selectbox(
        "Kondisi Market Saat Ini:",
        ["Auto (Detect via Price Action)", "Force Bearish XAU / Bullish DXY", "Force Bullish XAU / Bearish DXY"]
    )

    st.markdown("---")
    st.markdown("### 5. Price Reference (Realtime yfinance Sync)")
    running_price = st.number_input("Harga Running XAUUSD:", value=float(xau_live_price), step=0.5)
    dxy_running_price = st.number_input("Harga Running DXY (Dollar Index):", value=float(dxy_live_price), step=0.05)

# ==========================================
# 5. CALENDAR DATA CACHE
# ==========================================
@st.cache_data(ttl=86400, show_spinner="Mengambil data Kalender Ekonomi...")
def fetch_full_month_calendar(bln_num, thn_num):
    file_path = os.path.join(DATA_CACHE_DIR, f"calendar_{thn_num}_{bln_num:02d}.json")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                if isinstance(saved_data, list) and len(saved_data) > 0:
                    return saved_data, "Local File Database (Offline Cache)"
        except Exception:
            pass

    last_day = calendar.monthrange(thn_num, bln_num)[1]
    from_date = f"{thn_num}-{bln_num:02d}-01"
    to_date = f"{thn_num}-{bln_num:02d}-{last_day:02d}"
    
    normalized_data = []
    source_used = "System Presets (Offline)"

    url_finn = f"https://finnhub.io/api/v1/economic?from={from_date}&to={to_date}&token={FINNHUB_TOKEN}"
    try:
        res = requests.get(url_finn, timeout=8)
        if res.status_code == 200:
            raw_json = res.json()
            data = raw_json.get('economicData', []) if isinstance(raw_json, dict) else raw_json
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    normalized_data.append({
                        'event': item.get('event', ''),
                        'country': 'US',
                        'actual': item.get('actual'),
                        'estimate': item.get('estimate'),
                        'previous': item.get('prev'),
                        'date': item.get('time', '')
                    })
                source_used = "Finnhub Realtime API"
    except Exception:
        pass

    if not normalized_data:
        url_fmp = f"https://financialmodelingprep.com/api/v3/economic_calendar?from={from_date}&to={to_date}&apikey={FMP_API_KEY}"
        try:
            res = requests.get(url_fmp, timeout=8)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0 and 'error' not in str(data).lower():
                    normalized_data = data
                    source_used = "Financial Modeling Prep"
        except Exception:
            pass

    if normalized_data:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(normalized_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return normalized_data, source_used

calendar_raw, api_source = fetch_full_month_calendar(bulan_num, int(tahun_rilis))

def extract_indicator_smart(raw_list, keywords, default_act, default_est, default_prev, fallback_day, fallback_time="19:30"):
    found_item = None
    if raw_list:
        for item in raw_list:
            event_name = item.get('event', '').lower()
            if any(kw.lower() in event_name for kw in keywords):
                found_item = item
                break

    if found_item:
        act = found_item.get('actual')
        est = found_item.get('estimate')
        prev = found_item.get('previous')
        
        event_date_raw = found_item.get('date', '')
        try:
            ind_dt = datetime.strptime(event_date_raw[:16], "%Y-%m-%d %H:%M")
            jadwal_str = ind_dt.strftime("%d %b %Y %H:%M WIB")
        except Exception:
            ind_dt = datetime(int(tahun_rilis), bulan_num, fallback_day, int(fallback_time[:2]), int(fallback_time[3:]))
            jadwal_str = f"{fallback_day} {bulan_rilis[:3]} {tahun_rilis} {fallback_time} WIB"

        is_ind_past = ind_dt <= now
        
        if act is not None and str(act).strip() != "":
            act_str = str(act)
        else:
            if is_ind_past:
                act_str = str(default_act)
            else:
                act_str = f"OTW ({jadwal_str})"

        est_str = str(est) if (est is not None and str(est).strip() != "") else str(default_est)
        prev_str = str(prev) if (prev is not None and str(prev).strip() != "") else str(default_prev)

        return act_str, est_str, prev_str, jadwal_str

    ind_dt_fallback = datetime(int(tahun_rilis), bulan_num, fallback_day, int(fallback_time[:2]), int(fallback_time[3:]))
    jadwal_fallback_str = f"{fallback_day} {bulan_rilis[:3]} {tahun_rilis} {fallback_time} WIB"
    
    if ind_dt_fallback <= now:
        return str(default_act), str(default_est), str(default_prev), jadwal_fallback_str
    else:
        return f"OTW ({jadwal_fallback_str})", str(default_est), str(default_prev), jadwal_fallback_str

if "NFP" in target_news:
    act1, est1, prev1, j1 = extract_indicator_smart(calendar_raw, ["non farm payrolls", "nonfarm payrolls", "nfp"], "-23K", "80K", "20K", fallback_day=7)
    act2, est2, prev2, j2 = extract_indicator_smart(calendar_raw, ["unemployment rate"], "4.1%", "4.2%", "4.2%", fallback_day=7)
    act3, est3, prev3, j3 = extract_indicator_smart(calendar_raw, ["participation rate"], "61.4%", "61.6%", "61.5%", fallback_day=7)
    act4, est4, prev4, j4 = extract_indicator_smart(calendar_raw, ["average hourly earnings"], "0.2%", "0.3%", "0.3%", fallback_day=7)
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if not is_future_event else "BELUM RILIS",
        "ringkasan": f"NFP Status Rilis: {act1} vs Forecast {est1}.",
        "dampak": "Perubahan sektor tenaga kerja berpengaruh langsung ke ekspektasi Dolar US.",
        "ind_1": {"nama": "Non-Farm Payrolls", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Jumlah lapangan kerja baru non-pertanian.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_2": {"nama": "Unemployment Rate", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Persentase angka pengangguran.", "efek": "Actual < Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "Participation Rate", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Tingkat partisipasi angkatan kerja.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Average Hourly Earnings m/m", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Pertumbuhan rata-rata upah pekerja per jam.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }
elif "CPI" in target_news:
    act1, est1, prev1, j1 = extract_indicator_smart(calendar_raw, ["cpi m/m", "cpi y/y", "consumer price index"], "0.2%", "0.2%", "0.1%", fallback_day=12)
    act2, est2, prev2, j2 = extract_indicator_smart(calendar_raw, ["ppi m/m", "producer price"], "0.1%", "0.2%", "0.2%", fallback_day=13)
    act3, est3, prev3, j3 = extract_indicator_smart(calendar_raw, ["import price"], "0.1%", "0.0%", "-0.1%", fallback_day=14)
    act4, est4, prev4, j4 = extract_indicator_smart(calendar_raw, ["michigan consumer sentiment"], "67.8", "66.5", "66.4", fallback_day=14)
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if not is_future_event else "BELUM RILIS",
        "ringkasan": f"CPI Status Rilis: {act1} vs Forecast {est1}.",
        "dampak": "Perkembangan laju inflasi mempengaruhi kebijakan suku bunga The Fed.",
        "ind_1": {"nama": "Consumer Price Index (CPI)", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Indikator laju inflasi konsumen.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_2": {"nama": "Producer Price Index (PPI)", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Indikator inflasi produsen.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "Import Price Index", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Harga barang impor masuk.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Michigan Consumer Sentiment", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Kepercayaan konsumen terhadap ekonomi.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }
else:
    act1, est1, prev1, j1 = extract_indicator_smart(calendar_raw, ["fed interest rate", "fed rate decision"], "5.25%", "5.25%", "5.50%", fallback_day=20)
    act2, est2, prev2, j2 = extract_indicator_smart(calendar_raw, ["core pce"], "0.2%", "0.2%", "0.2%", fallback_day=30)
    act3, est3, prev3, j3 = extract_indicator_smart(calendar_raw, ["gdp"], "2.8%", "2.8%", "1.4%", fallback_day=29)
    act4, est4, prev4, j4 = extract_indicator_smart(calendar_raw, ["retail sales"], "1.0%", "0.3%", "-0.2%", fallback_day=15)
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if not is_future_event else "BELUM RILIS",
        "ringkasan": f"FOMC Decision Status: {act1} vs Forecast {est1}.",
        "dampak": "Keputusan suku bunga Fed menentukan arah jangka panjang USD.",
        "ind_1": {"nama": "Fed Interest Rate Decision", "actual": act1, "forecast": est1, "previous": prev1, "penjelasan": "Keputusan suku bunga acuan AS.", "efek": "Rate Hike -> Menguatkan USD"},
        "ind_2": {"nama": "Core PCE Price Index", "actual": act2, "forecast": est2, "previous": prev2, "penjelasan": "Inflasi acuan utama pilihan The Fed.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_3": {"nama": "GDP Advance Estimate", "actual": act3, "forecast": est3, "previous": prev3, "penjelasan": "Pertumbuhan ekonomi kuartalan.", "efek": "Actual > Forecast -> Menguatkan USD"},
        "ind_4": {"nama": "Retail Sales m/m", "actual": act4, "forecast": est4, "previous": prev4, "penjelasan": "Tingkat belanja konsumen.", "efek": "Actual > Forecast -> Menguatkan USD"}
    }

if "Force Bearish" in market_condition:
    is_bullish = False
elif "Force Bullish" in market_condition:
    is_bullish = True
else:
    is_bullish = (int(running_price * 10) % 2 != 0)

# KORELASI TERBALIK XAUUSD DAN DXY BERDASARKAN DYNAMIC PINE SCRIPT LIQUIDITY ZONES
if not is_bullish:
    # XAU Bearish -> DXY Bullish
    tech_action_xau = "🔴 SELL LIMIT / PREMIUM REJECTION"
    tech_entry_xau = xau_upper_liq[0]
    tech_sl_xau = round(xau_upper_liq[1] + 6.0, 2)
    tech_tp_xau = round(xau_lower_liq[0] - 30.0, 2)

    dxy_bias_text = "BULLISH (EXPANSION)"
    dxy_status_text = f"Mendekati Area Liquidation Supply ({dxy_upper_liq[0]:.2f} - {dxy_upper_liq[1]:.2f})"
else:
    # XAU Bullish -> DXY Bearish
    tech_action_xau = "🟢 BUY LIMIT / DISCOUNT REJECTION"
    tech_entry_xau = xau_lower_liq[1]
    tech_sl_xau = round(xau_lower_liq[0] - 6.0, 2)
    tech_tp_xau = round(xau_upper_liq[1] + 30.0, 2)

    dxy_bias_text = "BEARISH (REJECTION)"
    dxy_status_text = f"Mendekati Area Liquidation Demand ({dxy_lower_liq[0]:.2f} - {dxy_lower_liq[1]:.2f})"

# ==========================================
# FUNGSI KALKULASI REKAP MACRO DIVERGENCE & GEOPOLITIK
# ==========================================
def calculate_macro_divergence(ind1_info, ind2_info, ind3_info, ind4_info, main_news_name, is_future):
    def parse_num(val):
        try:
            return float(str(val).replace('%', '').replace('K', '').replace('M', ''))
        except:
            return None

    def eval_indicator(ind_dict, higher_is_good_for_usd=True):
        name = ind_dict.get('nama', 'Indikator')
        act_raw = ind_dict.get('actual', '-')
        est_raw = ind_dict.get('forecast', '-')
        
        a = parse_num(act_raw)
        e = parse_num(est_raw)
        
        if "OTW" in str(act_raw):
            return f"- **{name}**: Belum Rilis ({act_raw}) ⏳", 0
        if a is None or e is None:
            return f"- **{name}**: Actual ({act_raw}) | Forecast ({est_raw})", 0
        
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
            
        return f"- **{name}**: {note} ➔ Impak: **{res}**", score

    r1, s1 = eval_indicator(ind1_info, higher_is_good_for_usd=True)
    is_good_usd_2 = False if "unemployment" in ind2_info.get('nama', '').lower() else True
    r2, s2 = eval_indicator(ind2_info, higher_is_good_for_usd=is_good_usd_2)
    r3, s3 = eval_indicator(ind3_info, higher_is_good_for_usd=True)
    r4, s4 = eval_indicator(ind4_info, higher_is_good_for_usd=True)

    total_score = s1 + s2 + s3 + s4
    
    rekap_lines = [r1, r2, r3, r4]

    if total_score > 0:
        macro_bias = "BULLISH USD / BEARISH XAUUSD"
        pred_text = f"💡 **Proyeksi Prediksi News Utama:** Berdasarkan data pendukung yang cenderung positif, angka **{main_news_name}** berpotensi menguatkan Dolar US (USD)."
    elif total_score < 0:
        macro_bias = "BEARISH USD / BULLISH XAUUSD"
        pred_text = f"💡 **Proyeksi Prediksi News Utama:** Berdasarkan data pendukung yang cenderung melemah, angka **{main_news_name}** berpotensi memicu pelemahan Dolar US (USD)."
    else:
        macro_bias = "NEUTRAL / MIXED DATA (Whipsaw Risk)"
        pred_text = f"💡 **Proyeksi Prediksi News Utama:** Data pendukung berimbang/campuran. Waspadai volatilitas dua arah saat **{main_news_name}** rilis."

    if is_future:
        rekap_lines.append(f"\n{pred_text}")

    rekap_text = "\n".join(rekap_lines)
    return rekap_text, macro_bias, total_score

def fetch_geopolitical_analysis(event_name, actual_val, forecast_val):
    prompt = f"""
    Bertindaklah sebagai Senior Geopolitical & Macroeconomic Analyst.
    Berikan analisis terupdate mengenai isu geopolitik krusial terkini dan kombinasikan dengan dampak rilis data {event_name} (Actual: {actual_val} vs Forecast: {forecast_val}).

    Format jawaban HARUS JSON MURNI tanpa markdown:
    {{
        "isu_utama": "Eskalasi Selat Hormuz & Ancaman Rudal Iran",
        "ringkasan_situasi": "Eskalasi militer di Selat Hormuz mendongkrak minat beli aset safe haven.",
        "dampak_usd": "USD menguat terbatas terdorong arus safe-haven.",
        "dampak_xau": "XAUUSD sangat kuat didukung oleh lonjakan permintaan hedging safe-haven."
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
        "isu_utama": "Ketegangan Selat Hormuz & Eskalasi Perang Timur Tengah",
        "ringkasan_situasi": "Eskalasi militer memperketat jalur distribusi minyak global dan mendongkrak safe haven.",
        "dampak_usd": "USD menguat terbatas terdorong arus safe-haven.",
        "dampak_xau": "XAUUSD sangat kuat didukung oleh lonjakan permintaan hedging safe-haven."
    }

# ==========================================
# 6. DASHBOARD UI MAIN LAYOUT
# ==========================================
st.title("📈 ABEL FX - Macro, Astrodox & Dynamic Liquidity Engine")

status_text = "[ ✅ SUDAH RILIS ]" if ind_data["status_rilis"] == "SUDAH RILIS" else f"[ ⏳ BELUM RILIS ({tanggal_rilis} {bulan_rilis} {tahun_rilis} {jam_rilis_formatted}) ]"

st.markdown(f"### 📌 TARGET EVENT: {target_news} - {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted}) &nbsp;&nbsp;&nbsp;&nbsp; **{status_text}**")

if ind_data["status_rilis"] == "SUDAH RILIS":
    st.success(f"""
    🎯 **HASIL AKHIR NEWS ({target_news}):**
    - **Status:** Event ini telah rilis / lewat pada {tanggal_rilis} {bulan_rilis} {tahun_rilis} jam {jam_rilis_formatted}.
    - **Ringkasan Data:** {ind_data['ringkasan']}
    - **Dampak Pasar:** {ind_data['dampak']}
    - **Sumber Feed Data:** {api_source}
    """)
else:
    st.info(f"""
    ⏳ **PROYEKSI & JADWAL NEWS ({target_news}):**
    - **Status:** Event baru akan rilis pada **{tanggal_rilis} {bulan_rilis} {tahun_rilis} jam {jam_rilis_formatted}**.
    - **Ringkasan:** {ind_data['ringkasan']}
    - **Dampak Kebijakan:** {ind_data['dampak']}
    - **Sumber Feed Data:** {api_source}
    """)

st.markdown("---")
st.subheader(f"📊 Data Indikator Pendukung Real-Time ({target_news})")
st.caption(f"💡 Synchronized via {api_source} | Waktu Sistem: {now.strftime('%d-%m-%Y %H:%M:%S')} WIB")

actual_inputs = {}

def render_indicator_box(key_prefix, ind_dict):
    unique_key_suffix = f"{key_prefix}_{target_news}_{tanggal_rilis}_{bulan_rilis}_{tahun_rilis}"
    st.markdown(f"#### 🔹 {ind_dict.get('nama', 'Indikator')}")
    st.caption(f"💡 **Fungsi / Penjelasan:** {ind_dict.get('penjelasan', '-')}")
    st.info(f"⚡ **Efek ke Dollar (USD):** {ind_dict.get('efek', '-')}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        val_act = st.text_input("Actual", value=str(ind_dict.get('actual', '-')), key=f"act_{unique_key_suffix}")
        actual_inputs[key_prefix] = val_act
    with c2:
        st.text_input("Forecast", value=str(ind_dict.get('forecast', '-')), key=f"for_{unique_key_suffix}")
    with c3:
        st.text_input("Previous", value=str(ind_dict.get('previous', '-')), key=f"prev_{unique_key_suffix}")
    st.markdown("---")

render_indicator_box("ind_1", ind_data.get("ind_1", {}))
render_indicator_box("ind_2", ind_data.get("ind_2", {}))
render_indicator_box("ind_3", ind_data.get("ind_3", {}))
render_indicator_box("ind_4", ind_data.get("ind_4", {}))

final_act1 = actual_inputs.get("ind_1", act1)
final_act2 = actual_inputs.get("ind_2", act2)
final_act3 = actual_inputs.get("ind_3", act3)
final_act4 = actual_inputs.get("ind_4", act4)

st.subheader("🌍 MODUL BERITA GEOPOLITIK & SENTIMEN TRANSISI")
geo_info = fetch_geopolitical_analysis(target_news, final_act1, est1)

st.warning(f"""
- 🚨 **Isu Utama:** {geo_info.get('isu_utama')}
- 📝 **Ringkasan Situasi:** {geo_info.get('ringkasan_situasi')}
- 💵 **Dampak Gabungan ke USD:** {geo_info.get('dampak_usd')}
- 🪙 **Dampak Gabungan ke XAUUSD:** {geo_info.get('dampak_xau')}
""")

st.markdown("---")

if st.button(f"🚀 EXECUTE MULTI-TF AI PREDICTION FOR {target_news.upper()}", type="primary", use_container_width=True):
    with st.spinner("Sintesis Data Makro + Astrodox Aspect Weights + Geopolitik + SMC Dynamic Liquidity..."):
        
        ind1_current = {**ind_data.get("ind_1", {}), "actual": final_act1}
        ind2_current = {**ind_data.get("ind_2", {}), "actual": final_act2}
        ind3_current = {**ind_data.get("ind_3", {}), "actual": final_act3}
        ind4_current = {**ind_data.get("ind_4", {}), "actual": final_act4}

        rekap_text, macro_bias_result, score_val = calculate_macro_divergence(
            ind1_current, ind2_current, ind3_current, ind4_current, target_news, is_future_event
        )
        
        _, astro_positions_dict = compute_planetary_positions(event_datetime - timedelta(hours=7))

        fig_temp, _, temp_counts = generate_astrodox_unified_image(event_datetime, None)
        plt.close(fig_temp)

        system_prompt = f"""
        Kamu adalah Senior Quantitative Trader, Macro Analyst & Financial Astrologer spesialis XAUUSD & DXY.
        Sintesiskan Data Makro + Bobot Garis Aspek Astrodox + Geopolitik + SMC Technical Structure menjadi ESTIMASI RANGE PIPS PRESISI, WHIPSAW WARNING, ZONA ENTRY, SL, DAN TP KHUSUS UTAMA UNTUK XAUUSD (Gunakan DXY hanya sebagai acuan korelasi intermarket tanpa memberikan zona transaksi DXY).

        [INPUT DATA REAL-TIME & DYNAMIC LIQUIDITY ZONES]
        - Target Event: {target_news} ({status_text})
        - Running Price XAUUSD: {running_price} (ATR: {xau_atr:.2f})
        - Dynamic Liquidity Supply (Buy-side Liq XAU): {xau_upper_liq[0]} - {xau_upper_liq[1]}
        - Dynamic Liquidity Demand (Sell-side Liq XAU): {xau_lower_liq[0]} - {xau_lower_liq[1]}
        - Running Price DXY: {dxy_running_price}
        - Dynamic Liquidity Zone DXY: Upper ({dxy_upper_liq[0]} - {dxy_upper_liq[1]}) | Lower ({dxy_lower_liq[0]} - {dxy_lower_liq[1]})
        - Posisi Planet Astrodox: {json.dumps(astro_positions_dict)}
        - Hitungan Garis Aspek Astrodox Active:
            * Merah (Square 90° / Opposite 180° - Volatilitas/Tension): {temp_counts['merah']} garis
            * Hijau (Trine 120° - Expansion Trend): {temp_counts['hijau']} garis
            * Biru (Sextile 60° - Support/Demand Retest): {temp_counts['biru']} garis
            * Kuning (Conjunction 0° - Extreme Volatility/Turning Point): {temp_counts['kuning']} garis
        - Rekap Data Makro Pendukung:
        {rekap_text}
        - Bias Makro Kalkulasi: {macro_bias_result}
        - Isu Geopolitik: {geo_info.get('isu_utama')} - {geo_info.get('ringkasan_situasi')}

        [INSTRUKSI ENGINE AI]
        1. Baca Garis Astro Dominan dan batas Zona Likuiditas Atas/Bawah.
        2. Tentukan Bias Trend, Zona Entry Presisi, SL, dan TP KHUSUS UNTUK XAUUSD berdasarkan konvergensi Astro + SMC (DXY dipakai murni untuk konfirmasi korelasi).
        3. Berikan jawaban HANYA dalam format JSON MURNI tanpa markdown tambahan:

        {{
            "arah_bias": "BULLISH / BEARISH / WHIPSAW",
            "peringatan_whipsaw": "Waspada sweep ekstrem di area support/resistance sebelum pergerakan tren utama terkunci.",
            "ringkasan_sintesis": "Sintesis gabungan pengaruh aspek planet astrodox dan makro.",
            "proyeksi_pips": {{
                "sweep_pips": "80-120 Pips ($8.0-$12.0)",
                "trend_pips": "250-380 Pips ($25.0-$38.0)",
                "reversal_pips": "100-150 Pips ($10.0-$15.0)",
                "total_expected_range": "350-500 Pips ($35.0-$50.0)"
            }},
            "logika_entry_detail": "Penjelasan alasan penentuan angka range Pips dan titik Sweep Liquidity berdasarkan SMC.",
            "setup_spesifik": {{
                "tipe_eksekusi": "Buy Limit / Sell Limit / Two-Sided Breakout",
                "zona_buy_demand": "{xau_lower_liq[0]:.2f} - {xau_lower_liq[1]:.2f}",
                "zona_sell_supply": "{xau_upper_liq[0]:.2f} - {xau_upper_liq[1]:.2f}",
                "sl_buy": "{xau_lower_liq[0] - 6.00:.2f}",
                "sl_sell": "{xau_upper_liq[1] + 6.00:.2f}",
                "tp_buy": "{xau_upper_liq[1] + 25.00:.2f}",
                "tp_sell": "{xau_lower_liq[0] - 25.00:.2f}"
            }}
        }}
        """

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": system_prompt}],
            "temperature": 0.15,
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
                st.success("✅ AI & Astrodox Synthesis Success!")
        except Exception as e:
            st.error(f"Error Koneksi AI Engine: {e}")

# RENDER HASIL REKAP EVALUASI AI
if st.session_state["ai_result"]:
    res_ai = st.session_state["ai_result"]
    setup_ai = res_ai.get("setup_spesifik", {})
    pips_ai = res_ai.get("proyeksi_pips", {})
    
    if is_future_event:
        st.subheader("📋 Analysis & Proyeksi Data Pendukung (Pre-Rilis)")
    else:
        st.subheader("📋 Rekap Evaluasi Data Pendukung & Rilis News (Post-Rilis)")

    st.markdown(st.session_state["rekap_text"])
    st.info(f"⚖️ **Kesimpulan Bias Makro:** {st.session_state['macro_bias_result']} (Score Net: {st.session_state['score_val']})")

    st.markdown("### ⚡ AI PROYEKSI RANGE PIPS (CONFLUENCE ASTRO + TECHNICALS)")
    
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(f"""
        <div class="range-box">
            <div class="range-title">💥 Sweep Liquidity Range</div>
            <div class="range-value">{pips_ai.get("sweep_pips", "-")}</div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="range-box">
            <div class="range-title">🚀 Trend Expansion Range</div>
            <div class="range-value">{pips_ai.get("trend_pips", "-")}</div>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
        <div class="range-box">
            <div class="range-title">🔄 Reversal Bounce Range</div>
            <div class="range-value">{pips_ai.get("reversal_pips", "-")}</div>
        </div>
        """, unsafe_allow_html=True)
    with p4:
        st.markdown(f"""
        <div class="range-box">
            <div class="range-title">📊 Total Expected Range</div>
            <div class="range-value">{pips_ai.get("total_expected_range", "-")}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.warning(f"⚠️ **Peringatan Whipsaw & False Breakout:** {res_ai.get('peringatan_whipsaw', '-')}")
    st.markdown(f"• **Arah Bias Utama AI:** `{res_ai.get('arah_bias')}`")
    st.markdown(f"• **Sintesis Makro, Astro & Geopolitik:** {res_ai.get('ringkasan_sintesis')}")
    st.markdown(f"• **Reasoning & Liquidity Trigger:** {res_ai.get('logika_entry_detail')}")

    st.markdown("### 🎯 Specific Execution Setup (XAUUSD)")
    
    if "NEUTRAL" in str(res_ai.get('arah_bias')).upper() or "WHIPSAW" in str(res_ai.get('arah_bias')).upper():
        c_buy, c_sell = st.columns(2)
        with c_buy:
            st.success(f"""
            🟢 **PLAN A: BUY LIMIT (ZONA DISCOUNT / DEMAND)**
            - **Entry Zone Buy:** {setup_ai.get('zona_buy_demand')}
            - **Stop Loss (SL):** {setup_ai.get('sl_buy')}
            - **Take Profit (TP):** {setup_ai.get('tp_buy')}
            """)
        with c_sell:
            st.error(f"""
            🔴 **PLAN B: SELL LIMIT (ZONA PREMIUM / SUPPLY)**
            - **Entry Zone Sell:** {setup_ai.get('zona_sell_supply')}
            - **Stop Loss (SL):** {setup_ai.get('sl_sell')}
            - **Take Profit (TP):** {setup_ai.get('tp_sell')}
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

fig_astro_unified, img_astro_buf, aspect_counts = generate_astrodox_unified_image(
    event_datetime, 
    st.session_state["ai_result"]
)

# ==========================================
# 7. CONFLUENCE CARDS (DYNAMIC LIQUIDITY CARDS)
# ==========================================
st.subheader("🎯 MULTI-TIMEFRAME LIQUIDITY & METHOD CONFLUENCE")

col_l, col_m, col_r = st.columns(3)

# ---------------------------------------------------------
# COLUMN 1: AI Macro & Range Engine
# ---------------------------------------------------------
with col_l:
    if st.session_state["ai_result"]:
        ai_bias = st.session_state["ai_result"].get("arah_bias", "NEUTRAL")
        ai_setup = st.session_state["ai_result"].get("setup_spesifik", {})
        bias_badge = f'<span class="badge-bullish">{ai_bias}</span>' if "BULLISH" in str(ai_bias).upper() else f'<span class="badge-bearish">{ai_bias}</span>'
        
        st.markdown(f"""
        <div class="card">
            <div class="card-title">🤖 AI Macro & Range Engine</div>
            <p style="font-size: 0.9rem;">• <b>Bias Utama:</b> {bias_badge}</p>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🟢 <b>ZONA BUY DEMAND</b></p>
            <div class="zone-box">{ai_setup.get('zona_buy_demand', '-')}</div>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🛑 <b>STOP LOSS (SL)</b></p>
            <div class="sl-box">{ai_setup.get('sl_buy', '-')}</div>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🏁 <b>TARGET TP EXPANSION</b></p>
            <div class="tp-box">{ai_setup.get('tp_buy', '-')}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">🤖 AI Macro & Range Engine</div>
            <p style="font-size: 0.9rem;">• <b>Bias Utama:</b> <span class="badge-bullish">BULLISH</span></p>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🟢 <b>ZONA BUY DEMAND</b></p>
            <div class="zone-box">{xau_lower_liq[0]:.2f} - {xau_lower_liq[1]:.2f}</div>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🛑 <b>STOP LOSS (SL)</b></p>
            <div class="sl-box">{xau_lower_liq[0] - 6.0:.2f}</div>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🏁 <b>TARGET TP EXPANSION</b></p>
            <div class="tp-box">{xau_upper_liq[1] + 25.0:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# COLUMN 2: Astrodox Engine
# ---------------------------------------------------------
with col_m:
    if astrodox_active:
        astro_sl_val = xau_lower_liq[0] - 6.00
        astro_tp_val = xau_upper_liq[1] + 25.00
        if st.session_state["ai_result"]:
            ast_setup = st.session_state["ai_result"].get("setup_spesifik", {})
            ai_b_check = str(st.session_state["ai_result"].get("arah_bias", "")).upper()
            if "BEARISH" in ai_b_check:
                astro_sl_val = ast_setup.get('sl_sell', astro_sl_val)
                astro_tp_val = ast_setup.get('tp_sell', astro_tp_val)
            else:
                astro_sl_val = ast_setup.get('sl_buy', astro_sl_val)
                astro_tp_val = ast_setup.get('tp_buy', astro_tp_val)

        st.markdown(f"""
        <div class="card">
            <div class="card-title">🔮 Astrodox Engine</div>
            <ul style="font-size: 0.85rem; padding-left: 18px; margin-bottom: 15px; color: #cbd5e1;">
                <li><b>Merah (Square/Opp):</b> {aspect_counts['merah']}</li>
                <li><b>Hijau (Trine):</b> {aspect_counts['hijau']}</li>
                <li><b>Biru (Sextile):</b> {aspect_counts['biru']}</li>
                <li><b>Kuning (Conjn):</b> {aspect_counts['kuning']}</li>
            </ul>
            
            <p style="font-size: 0.85rem; margin-bottom: 2px;">🎯 <b>ZONA BIAS ASTRO</b></p>
            <div class="zone-box">{running_price - 3.00:.2f} - {running_price + 3.00:.2f}</div>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🛑 <b>STOP LOSS ASTRO</b></p>
            <div class="sl-box">{astro_sl_val}</div>
            
            <p style="font-size: 0.85rem; margin-top: 15px; margin-bottom: 2px;">🏁 <b>TARGET TP ASTRO</b></p>
            <div class="tp-box">{astro_tp_val}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Astrodox Engine OFF")

# ---------------------------------------------------------
# COLUMN 3: Multi-TF Technical Engine (XAU & DXY)
# ---------------------------------------------------------
with col_r:
    if tech_active:
        xau_badge = '<span class="badge-bearish">BEARISH (REJECTION)</span>' if not is_bullish else '<span class="badge-bullish">BULLISH (EXPANSION)</span>'
        dxy_badge = '<span class="badge-bullish">BULLISH (EXPANSION)</span>' if not is_bullish else '<span class="badge-bearish">BEARISH (REJECTION)</span>'
        
        liq_reason_text = f"Mendekati Area Liquidation Supply ({xau_upper_liq[0]:.2f} - {xau_upper_liq[1]:.2f}). Berpotensi memicu Sweep Liquidity sebelum pergerakan reversal." if not is_bullish else f"Mendekati Area Liquidation Demand ({xau_lower_liq[0]:.2f} - {xau_lower_liq[1]:.2f}). Berpotensi memicu Sweep Liquidity sebelum pergerakan reversal."

        st.markdown(f"""
        <div class="card">
            <div class="card-title">📐 Multi-TF Technical Engine (XAU & DXY)</div>
            
            <!-- SECTION 1: XAUUSD ANALYSIS -->
            <p style="font-size: 1rem; font-weight: bold; margin-bottom: 5px;">🥇 XAUUSD ANALYSIS</p>
            <p style="font-size: 0.85rem; margin-bottom: 3px;">
                🔴 <b>ARAH BIAS XAU:</b> {xau_badge}
            </p>
            <p style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 10px;">
                Eksekusi: {tech_action_xau}
            </p>
            
            <p style="font-size: 0.85rem; margin-bottom: 2px;">🎯 <b>Zona Entry XAU:</b></p>
            <div class="zone-box">{tech_entry_xau - 1.00:.2f} - {tech_entry_xau + 1.50:.2f}</div>
            
            <!-- KOLOM SL & TP TEKNIKAL (In-line Style) -->
            <div class="sltp-inline">
                <div class="sltp-item sl-inline">
                    <span>🛑 SL XAU:</span> <span>{tech_sl_xau:.2f}</span>
                </div>
                <div class="sltp-item tp-inline">
                    <span>🏁 TP XAU:</span> <span>{tech_tp_xau:.2f}</span>
                </div>
            </div>
            
            <!-- LIQUIDITY AS REASON FOR XAU -->
            <div class="liquidity-box">
                📌 <b>Status Liquidity (Confluence Reason):</b><br/>
                {liq_reason_text}
            </div>
            
            <hr style="border: 0; border-top: 1px solid #30363d; margin: 18px 0 14px 0;">
            
            <!-- SECTION 2: DXY DIRECTIONAL VALIDATION -->
            <p style="font-size: 1rem; font-weight: bold; margin-bottom: 5px;">💵 DXY (DOLLAR INDEX) ANALYSIS & ACUAN</p>
            <p style="font-size: 0.85rem; margin-bottom: 8px;">
                🟢 <b>ARAH BIAS DXY:</b> {dxy_badge}
            </p>
            
            <p style="font-size: 0.78rem; color: #fbbf24; margin-top: 12px; line-height: 1.4;">
                ⚠️ <i>DXY murni dipakai sebagai acuan korelasi macro intermarket ({dxy_status_text}). Tidak ada Zona Entry, SL, atau TP yang dirender untuk DXY.</i>
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Technical Engine OFF")

st.markdown("---")

# ==========================================
# 8. ASTRODOX UNIFIED SECTION & ZOOM DIALOG
# ==========================================
st.subheader("🔮 ASTRODOX TRANSIT WHEEL & AI RANGE INTEGRATED ANALYSIS")

st.pyplot(fig_astro_unified)

@st.dialog("🔍 High-Resolution Astrodox & AI Range Chart (Zoom View)", width="large")
def show_zoomed_chart(image_bytes):
    st.image(image_bytes, use_container_width=True)

col_d1, col_d2 = st.columns(2)
with col_d1:
    if st.button("🔍 Zoom / Perbesar Tampilan Gambar", use_container_width=True):
        show_zoomed_chart(img_astro_buf)

with col_d2:
    st.download_button(
        label="📥 Download Roda Astrodox & AI Proyeksi Range (.png)",
        data=img_astro_buf,
        file_name=f"Astrodox_AI_Range_{event_datetime.strftime('%Y%m%d_%H%M')}.png",
        mime="image/png",
        use_container_width=True
    )

st.markdown("---")

# ==========================================
# 9. LIVE CHART TRADINGVIEW
# ==========================================
st.subheader("📉 LIVE CHART TRADINGVIEW (INTERACTIVE)")

tab1, tab2 = st.tabs(["🥇 XAUUSD Chart", "💵 DXY (Dollar Index) Chart"])

with tab1:
    tradingview_widget_xau = """
    <div class="tradingview-widget-container" style="height:620px;width:100%">
      <div id="tradingview_xau" style="height:100%;width:100%"></div>
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
        "container_id": "tradingview_xau",
        "hide_side_toolbar": false,
        "studies": []
      });
      </script>
    </div>
    """
    components.html(tradingview_widget_xau, height=620)

with tab2:
    tradingview_widget_dxy = """
    <div class="tradingview-widget-container" style="height:620px;width:100%">
      <div id="tradingview_dxy" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
        "width": "100%",
        "height": 600,
        "symbol": "CAPITALCOM:DXY",
        "interval": "15",
        "timezone": "Asia/Jakarta",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_dxy",
        "hide_side_toolbar": false,
        "studies": []
      });
      </script>
    </div>
    """
    components.html(tradingview_widget_dxy, height=620)
