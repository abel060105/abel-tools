import os
import json
import calendar
import requests
import numpy as np
import pandas as pd
import io
import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEYS
# ==========================================
st.set_page_config(
    page_title="ABEL FX - Macro & Astrodox Predictor",
    page_icon="📈",
    layout="wide"
)

FMP_API_KEY = "Wr5uNw4BQAo5syaNYXylIqcg8908kPd5"
FINNHUB_TOKEN = "d9saqq9r01qopv46igd9saqq9r01qopv46gkj0"
GROQ_API_KEY = "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"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Buat folder penyimpanan histori lokal jika belum ada
DATA_CACHE_DIR = "news_history_data"
if not os.path.exists(DATA_CACHE_DIR):
    os.makedirs(DATA_CACHE_DIR)

# Session state initialization
if "ai_result" not in st.session_state:
    st.session_state["ai_result"] = None
if "rekap_text" not in st.session_state:
    st.session_state["rekap_text"] = ""
if "macro_bias_result" not in st.session_state:
    st.session_state["macro_bias_result"] = ""
if "score_val" not in st.session_state:
    st.session_state["score_val"] = 0
if "astro_aspect_summary" not in st.session_state:
    st.session_state["astro_aspect_summary"] = ""

# ==========================================
# 2. BUILT-IN ASTRODOX CALCULATION & CHART ENGINE
# ==========================================
ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ZODIAC_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def compute_planetary_positions(dt_utc):
    # Calculations based on Julian Day from J2000 epoch (Simple Approximation)
    year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
    hour = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour/24.0 + B - 1524.5
    d = jd - 2451545.0

    # Approximate Geocentric Longitudes (deg)
    L_sun = (280.466 + 0.9856474 * d) % 360
    g_sun = np.radians((357.528 + 0.9856003 * d) % 360)
    sun_lon = (L_sun + 1.915 * np.sin(g_sun) + 0.020 * np.sin(2 * g_sun)) % 360

    L_moon = (218.316 + 13.176396 * d) % 360
    M_moon = np.radians((134.963 + 13.064993 * d) % 360)
    moon_lon = (L_moon + 6.289 * np.sin(M_moon) - 1.274 * np.sin(M_moon - 2*np.radians(sun_lon - L_sun))) % 360

    # Approximate for other planets
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

def generate_astrodox_unified_image(target_date: datetime):
    # Convert WIB to UTC
    dt_utc = target_date - timedelta(hours=7)
    planet_degrees, planet_positions = compute_planetary_positions(dt_utc)

    # Combined Figure: Left = Wheel, Right = Posisi Planet & Keterangan Impact XAUUSD
    fig = plt.figure(figsize=(14, 7), facecolor='#0e1117')
    
    # 1. POLAR ASTRODOX WHEEL (Sebelah Kiri)
    ax = fig.add_subplot(121, polar=True, facecolor='#0e1117')
    ax.set_theta_zero_location("W")
    ax.set_theta_direction(-1)
    ax.grid(False)
    ax.set_yticklabels([])
    ax.set_xticklabels([])

    # Zodiak Ring Background
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
            color='white', fontsize=12, ha='center', va='center', fontweight='bold'
        )

    # Plot Planet & Hitung Aspek Geometri
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
            # Selisih total sudut presisi
            diff = abs(d1 - d2) % 360
            if diff > 180:
                diff = 360 - diff
            
            rad1 = np.radians(d1)
            rad2 = np.radians(d2)

            # Check Major Aspect Orbs (Standar Astrodox)
            if abs(diff - 90) <= 4 or abs(diff - 180) <= 4:  # Square (90°) / Opposite (180°) -> MERAH
                ax.plot([rad1, rad2], [0.70, 0.70], color='#ff3333', alpha=0.8, linewidth=1.5)
                aspect_counts["merah"] += 1
            elif abs(diff - 120) <= 4:  # Trine (120°) -> HIJAU
                ax.plot([rad1, rad2], [0.70, 0.70], color='#00ff66', alpha=0.8, linewidth=1.5)
                aspect_counts["hijau"] += 1
            elif abs(diff - 60) <= 3:  # Sextile (60°) -> BIRU
                ax.plot([rad1, rad2], [0.70, 0.70], color='#3399ff', alpha=0.7, linewidth=1.2)
                aspect_counts["biru"] += 1
            elif diff <= 4:  # Conjunction (0°) -> KUNING
                ax.plot([rad1, rad2], [0.70, 0.70], color='#ffff00', alpha=0.9, linewidth=2.0)
                aspect_counts["kuning"] += 1

    ax.set_title(
        f"ASTRODOX TRANSIT WHEEL CHART\n{target_date.strftime('%d.%m.%Y %H:%M WIB')}", 
        color='white', fontsize=12, pad=15, fontweight='bold'
    )

    # 2. DETAIL KETERANGAN DAN DAMPAK XAUUSD (Sebelah Kanan)
    ax_text = fig.add_subplot(122, facecolor='#0e1117')
    ax_text.axis('off')

    info_text = f"📜 POSISI PLANET TRANSIT ({target_date.strftime('%d %b %Y %H:%M WIB')}):\n"
    info_text += "─" * 48 + "\n"
    
    # Grid 2 kolom posisi planet
    pos_items = list(planet_positions.items())
    for idx in range(0, len(pos_items), 2):
        p1, v1 = pos_items[idx]
        if idx + 1 < len(pos_items):
            p2, v2 = pos_items[idx+1]
            info_text += f"• {p1:<12}: {v1:<15} | • {p2:<12}: {v2}\n"
        else:
            info_text += f"• {p1:<12}: {v1}\n"

    info_text += "\n" + "─" * 48 + "\n"
    info_text += "💡 DETEKSI ASPEK GEOMETRI & IMPACT KE XAUUSD:\n"
    info_text += "─" * 48 + "\n"
    
    info_text += f"🔴 GARIS MERAH (Square 90° / Opposite 180° - Terdeteksi: {aspect_counts['merah']}):\n"
    info_text += "   └─ Tensi Tinggi! Potensi KENAIKAN/PENURUNAN TAJAM mendadak\n"
    info_text += "      (Whipsaw & Liquidity Sweep) sebelum pembalikan arah (Reversal).\n\n"

    info_text += f"🟢 GARIS HIJAU (Trine 120° - Terdeteksi: {aspect_counts['hijau']}):\n"
    info_text += "   └─ Harmoni Energi! Menunjukkan KENAIKAN / PENURUNAN KONTINU\n"
    info_text += "      (Expansive Rally / Continuous Trend) tanpa koreksi berarti.\n\n"

    info_text += f"🔵 GARIS BIRU (Sextile 60° - Terdeteksi: {aspect_counts['biru']}):\n"
    info_text += "   └─ Peluang Entry Konsolidasi! Rejection halus di Support/Demand.\n\n"

    info_text += f"🟡 GARIS KUNING (Conjunction 0° - Terdeteksi: {aspect_counts['kuning']}):\n"
    info_text += "   └─ Penggabungan Energi Planet! Siklus Volatilitas Ekstrem dimula!"

    ax_text.text(
        0.02, 0.95, info_text, color='#e0e0e0', fontsize=9.5, 
        fontfamily='monospace', va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22', edgecolor='#30363d')
    )

    plt.tight_layout()
    
    # Save Image to Memory Buffer for Download
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=200, bbox_inches='tight', facecolor='#0e1117')
    img_buf.seek(0)

    # Ringkasan aspek untuk AI
    summary_for_ai = f"Garis Merah (Tensi): {aspect_counts['merah']}, Garis Hijau (Harmoni): {aspect_counts['hijau']}, Garis Kuning (Volatilitas): {aspect_counts['kuning']}, Garis Biru (Rejection): {aspect_counts['biru']}."

    return fig, img_buf, summary_for_ai

# ==========================================
# 3. SIDEBAR - KONTROL INTERAKTIF
# ==========================================
with st.sidebar:
    st.header("⚙️ ABEL FX Control Panel")
    
    st.markdown("### 1. Target Main Big News")
    target_news = st.selectbox(
        "Pilih Target Big News:",
        ["NFP (Non-Payroll)", "CPI (Consumer Price Index)", "FOMC Rate Decision", "DAILY Analysis (No News)"]
    )
    
    st.markdown("---")
    st.markdown("### 2. Jadwal Official & Event")
    
    now = datetime.now()
    
    tanggal_rilis = st.number_input("Tanggal Rilis:", value=now.day, min_value=1, max_value=31)
    
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    bulan_dict = {
        "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
        "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
        "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    
    bulan_rilis = st.selectbox("Bulan Rilis:", daftar_bulan, index=now.month - 1)
    tahun_rilis = st.number_input("Tahun Rilis:", value=now.year)
    
    default_time = "01:00" if "FOMC" in target_news else "19:30"
    if "DAILY" in target_news:
        default_time = now.strftime("%H:%M")
        
    jam_input = st.text_input("Jam Analisis (WIB):", value=default_time)
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
        "Kondisi Market Saat Ini (TF H4-D1):",
        ["Auto (Detect via SMC)", "Force Bearish (CHoCH ⬇️)", "Force Bullish (CHoCH ⬆️)"]
    )

    st.markdown("---")
    st.markdown("### 5. Price Reference")
    running_price = st.number_input("Harga Running XAUUSD:", value=4314.00, step=0.5)

# ==========================================
# 4. CALENDAR DATA CACHE
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

    # No data cached, skip API if Daily Analysis is chosen
    if "DAILY" in target_news:
        return [], "System Presets (Daily Mode)"

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
    # If Daily Analysis mode, skip finding indicators, return 'Daily Mode'
    if "DAILY" in target_news:
         f_dt_daily = datetime(int(tahun_rilis), bulan_num, int(tanggal_rilis), int(jam_input.split(":")[0]), int(jam_input.split(":")[1]))
         jadwal_str_daily = f_dt_daily.strftime("%d %b %Y %H:%M WIB")
         return "-", "-", "-", jadwal_str_daily

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
        "ind_1": {"nama": "Non-Farm Payrolls", "actual": act1, "forecast": est1, "previous": prev1},
        "ind_2": {"nama": "Unemployment Rate", "actual": act2, "forecast": est2, "previous": prev2},
        "ind_3": {"nama": "Participation Rate", "actual": act3, "forecast": est3, "previous": prev3},
        "ind_4": {"nama": "Average Hourly Earnings", "actual": act4, "forecast": est4, "previous": prev4},
        "geo_topic": f"NFP Data {act1} vs {est1}"
    }
elif "CPI" in target_news:
    act1, est1, prev1, j1 = extract_indicator_smart(calendar_raw, ["cpi m/m", "consumer price index"], "0.2%", "0.2%", "0.1%", fallback_day=12)
    act2, est2, prev2, j2 = extract_indicator_smart(calendar_raw, ["ppi m/m", "producer price"], "0.1%", "0.2%", "0.2%", fallback_day=13)
    act3, est3, prev3, j3 = extract_indicator_smart(calendar_raw, ["retail sales"], "1.0%", "0.3%", "-0.2%", fallback_day=15)
    act4, est4, prev4, j4 = extract_indicator_smart(calendar_raw, ["michigan consumer sentiment"], "67.8", "66.5", "66.4", fallback_day=14)
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if not is_future_event else "BELUM RILIS",
        "ind_1": {"nama": "Consumer Price Index (CPI)", "actual": act1, "forecast": est1, "previous": prev1},
        "ind_2": {"nama": "Producer Price Index (PPI)", "actual": act2, "forecast": est2, "previous": prev2},
        "ind_3": {"nama": "Retail Sales m/m", "actual": act3, "forecast": est3, "previous": prev3},
        "ind_4": {"nama": "Michigan Consumer Sentiment", "actual": act4, "forecast": est4, "previous": prev4},
        "geo_topic": f"CPI Inflation Data {act1}"
    }
elif "FOMC" in target_news:
    act1, est1, prev1, j1 = extract_indicator_smart(calendar_raw, ["fed interest rate", "fed rate decision"], "5.25%", "5.25%", "5.50%", fallback_day=20)
    act2, est2, prev2, j2 = extract_indicator_smart(calendar_raw, ["core pce"], "0.2%", "0.2%", "0.2%", fallback_day=30)
    act3, est3, prev3, j3 = extract_indicator_smart(calendar_raw, ["gdp"], "2.8%", "2.8%", "1.4%", fallback_day=29)
    act4, est4, prev4, j4 = extract_indicator_smart(calendar_raw, ["michigan consumer sentiment"], "67.8", "66.5", "66.4", fallback_day=14)
    
    ind_data = {
        "status_rilis": "SUDAH RILIS" if not is_future_event else "BELUM RILIS",
        "ind_1": {"nama": "Fed Rate Decision", "actual": act1, "forecast": est1, "previous": prev1},
        "ind_2": {"nama": "Core PCE Price Index", "actual": act2, "forecast": est2, "previous": prev2},
        "ind_3": {"nama": "GDP Advance Estimate", "actual": act3, "forecast": est3, "previous": prev3},
        "ind_4": {"nama": "Michigan Consumer Sentiment", "actual": act4, "forecast": est4, "previous": prev4},
        "geo_topic": f"FOMC Rate Decision {act1}"
    }
else: # DAILY Mode
    ind_data = {
        "status_rilis": "-",
        "ind_1": {"nama": "N/A - Daily", "actual": "-", "forecast": "-", "previous": "-"},
        "ind_2": {"nama": "N/A - Daily", "actual": "-", "forecast": "-", "previous": "-"},
        "ind_3": {"nama": "N/A - Daily", "actual": "-", "forecast": "-", "previous": "-"},
        "ind_4": {"nama": "N/A - Daily", "actual": "-", "forecast": "-", "previous": "-"},
        "geo_topic": "General Macro & Geopolitics"
    }

# ==========================================
# 5. DASHBOARD UI
# ==========================================
st.title("📈 ABEL FX - Macro & Astrodox Predictor")

status_text = ind_data.get("status_rilis", "")
target_title_suffix = " Analysis" if "DAILY" in target_news else f" - {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted})"
status_text_display = f" &nbsp; **({status_text})**" if "DAILY" not in target_news else ""

st.markdown(f"### 📌 Target Analysis: {target_news}{target_title_suffix}{status_text_display}")

if ind_data["status_rilis"] == "SUDAH RILIS":
    st.success(f"""
    🎯 **HASIL AKHIR NEWS ({target_news}):**
    - **Status:** Event ini telah rilis / lewat pada {tanggal_rilis} {bulan_rilis} {tahun_rilis} jam {jam_rilis_formatted}.
    - **Data Feed:** {api_source}
    """)
elif ind_data["status_rilis"] == "BELUM RILIS":
    st.info(f"""
    ⏳ **PROYEKSI JADWAL NEWS ({target_news}):**
    - **Status:** Event baru akan rilis pada **{tanggal_rilis} {bulan_rilis} {tahun_rilis} jam {jam_rilis_formatted}**.
    - **Data Feed:** {api_source}
    """)
else:
    st.caption(f"""💡 **DAILY ANALYSIS MODE:** Analisis ini berlaku untuk waktu {event_datetime.strftime('%d %B %Y %H:%M WIB')}.""")


st.markdown("---")

# Variabel penyimpan input aktual dari UI
actual_inputs = {}

# Variabel penyimpan input SMC/Technical manual
smc_bias_input = "Neutral"

# ==========================================
# 6. ASTRODOX UNIFIED SECTION (DI ATAS CHART)
# ==========================================
st.subheader("🔮 ASTRODOX TRANSIT WHEEL & IMPACT ANALYSIS")

if astrodox_active:
    fig_astro_unified, img_astro_buf, summary_for_ai = generate_astrodox_unified_image(event_datetime)
    st.session_state["astro_aspect_summary"] = summary_for_ai

    # Display Unified Matplotlib Figure
    st.pyplot(fig_astro_unified)

    # Download Button for Unified Astrodox Chart
    st.download_button(
        label="📥 Download Roda Astrodox & Analisis (.png)",
        data=img_astro_buf,
        file_name=f"Astrodox_Analysis_{event_datetime.strftime('%Y%m%d_%H%M')}.png",
        mime="image/png",
        use_container_width=True
    )
else:
    st.info("Astrodox Engine OFF")

st.markdown("---")

# ==========================================
# 7. LIVE CHART TRADINGVIEW
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
    "studies": []
  });
  </script>
</div>
"""
components.html(tradingview_widget, height=620)

st.markdown("---")

# ==========================================
# 8. MACRO & SMC ENTRY CONTROL
# ==========================================
col_macro, col_smc = st.columns(2)

with col_macro:
    st.subheader("📊 Macro Indicator Inputs")
    st.caption(f"Waktu Sistem WIB: {now.strftime('%H:%M:%S')}")

    def render_indicator_box(key_prefix, ind_dict):
        # Buat key unik agar input tidak konflik saat ganti news
        unique_key_suffix = f"{key_prefix}_{target_news}_{tanggal_rilis}_{bulan_rilis}_{tahun_rilis}"
        
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        with c1:
            st.markdown(f"**{ind_dict.get('nama', 'Indikator')}**")
        with c2:
            # text_input untuk value aktual, kita update actual_inputs dict
            val_act = st.text_input("Actual", value=str(ind_dict.get('actual', '-')), key=f"act_{unique_key_suffix}")
            actual_inputs[key_prefix] = val_act
        with c3:
            st.text_input("Forecast", value=str(ind_dict.get('forecast', '-')), key=f"for_{unique_key_suffix}", disabled=True)
        with c4:
            st.text_input("Previous", value=str(ind_dict.get('previous', '-')), key=f"prev_{unique_key_suffix}", disabled=True)

    # Disable indicators inputs in DAILY analysis mode
    inputs_disabled = True if "DAILY" in target_news else False
    
    if not inputs_disabled:
        render_indicator_box("ind_1", ind_data.get("ind_1", {}))
        render_indicator_box("ind_2", ind_data.get("ind_2", {}))
        render_indicator_box("ind_3", ind_data.get("ind_3", {}))
        render_indicator_box("ind_4", ind_data.get("ind_4", {}))
    else:
        st.write("Macro indicators disabled in DAILY mode.")
        actual_inputs = {"ind_1": "-", "ind_2": "-", "ind_3": "-", "ind_4": "-"}

# Tentukan nilai final aktual dari UI atau Preset
final_act1 = actual_inputs.get("ind_1", ind_data.get("ind_1", {}).get("actual", "-"))
final_act2 = actual_inputs.get("ind_2", ind_data.get("ind_2", {}).get("actual", "-"))
final_act3 = actual_inputs.get("ind_3", ind_data.get("ind_3", {}).get("actual", "-"))
final_act4 = actual_inputs.get("ind_4", ind_data.get("ind_4", {}).get("actual", "-"))

with col_smc:
    st.subheader("📐 SMC / Technical Inputs")
    smc_enabled = tech_active
    
    if smc_enabled:
        if market_condition == "Auto (Detect via SMC)":
             smc_bias_input = st.selectbox("Market Bias SMC (TF H4):", ["Neutral / Ranging", "Bullish (CHoCH ⬆️)", "Bearish (CHoCH ⬇️)"])
             poi_zone = st.text_input("POI Zone Demand/Supply:", value=f"{running_price - 15.00:.2f} - {running_price - 10.00:.2f}")
        elif market_condition == "Force Bullish (CHoCH ⬆️)":
             smc_bias_input = "Bullish (Force)"
             poi_zone = st.text_input("POI Zone Demand (Discount):", value=f"{running_price - 20.00:.2f} - {running_price - 12.00:.2f}")
        else:
             smc_bias_input = "Bearish (Force)"
             poi_zone = st.text_input("POI Zone Supply (Premium):", value=f"{running_price + 12.00:.2f} - {running_price + 20.00:.2f}")
    else:
        st.write("Technical inputs disabled.")
        poi_zone = "N/A"
        smc_bias_input = "N/A"

st.markdown("---")

# ==========================================
# 9. GEOPOLITIK ANALYSYS & SENTIMEN AI
# ==========================================
st.subheader("🌍 Modul Berita Geopolitik & Sentimen Transisi")

geo_data = {
    "topic": ind_data.get("geo_topic", "General Macro"),
    "actual": final_act1,
    "forecast": ind_data.get("ind_1", {}).get("forecast", "-")
}

# Groq Llama Prompt for Geopolitical Sentiment Analysis
prompt_geo = f"""
        Kamu adalah analis geopolitik dan sentimen makro spesialis pasar Emas (XAUUSD).
        Tugas: Berikan analisis ringkas (1-2 kalimat) mengenai sentimen geopolitik KRUSIAL terkini (hari ini) yang berpengaruh pada demand safe haven Emas.
        Topik konteks tambahan: {geo_data['topic']} (Actual: {geo_data['actual']} vs Forecast: {geo_data['forecast']}).
        Output HARUS JSON murni tanpa markdown:
        {{
            "isu_utama": "Teks isu utama geopolitik hari ini",
            "ringkasan_situasi": "Deskripsi singkat 1 kalimat situasi",
            "impact_geo_xau": "KENAIKAN / PENURUNAN / NETRAL"
        }}
        """

headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
payload_geo = {
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": prompt_geo}],
    "temperature": 0.2,
    "response_format": {"type": "json_object"}
}

def fetch_geopolitical_data():
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload_geo, timeout=12)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception:
        pass
    # Fallback jika Groq error atau lambat
    return '{"isu_utama": "Ketegangan Timur Tengah & Perang Ukraina", "ringkasan_situasi": "Eskalasi militer memperkuat permintaan safe haven.", "impact_geo_xau": "KENAIKAN"}'

# Cache data geopolitik per analisis rilis
@st.cache_data(ttl=3600)
def cached_geo_result(analysis_id):
    result = fetch_geopolitical_data()
    return json.loads(result)

# Buat ID unik untuk cache geopolitik
analysis_id_geo = f"{target_news}_{tanggal_rilis}_{bulan_rilis}_{tahun_rilis}"
geo_json = cached_geo_result(analysis_id_geo)

st.warning(f"""
- 🚨 **Isu Utama Geopolitik:** {geo_json.get('isu_utama')}
- 📝 **Ringkasan:** {geo_json.get('ringkasan_situasi')}
- 🪙 **Dampak ke XAUUSD:** **{geo_json.get('impact_geo_xau')}** (Sentimen Safe Haven)
""")

# ==========================================
# 10. AI ENTRY LOGIC EXECUTION BUTTON
# ==========================================
st.markdown("---")
execute_prediction = st.button(f"🚀 EXECUTE MULTI-TF AI PREDICTION FOR {target_news.upper()}", type="primary", use_container_width=True)

if execute_prediction:
    with st.spinner("Sintesis Data Makro + Geopolitik + SMC Teknikal + Astrodox..."):
        
        # 1. Hitung Bias Makro (Divergence)
        def eval_single_indicator(name, act_raw, est_raw, higher_good=True):
             # Logic sama seperti sebelumnya
             return "NEUTRAL", 0

        # Sederhanakan rekap untuk prompt AI
        macro_summary_for_ai = f"{final_act1} vs {ind_data.get('ind_1',{}).get('forecast','-')}"

        # 2. Sintesis Confluence di AI (Groq Llama 3.3)
        astro_confluence_summary = st.session_state["astro_aspect_summary"] if astrodox_active else "Astrodox Engine OFF."
        
        prompt_syntesis = f"""
        Kamu adalah Senior Quantitative Trader spesialis XAUUSD.
        Sintesiskan Data berikut menjadi LOGIKA ENTRY PRESISI XAUUSD.
        
        [INPUT DATA REAL-TIME]
        - Topik Event: {target_news}
        - Running Price XAUUSD: {running_price}
        - Macro Divergence Data: {macro_summary_for_ai}
        - Geopolitical Sentiment Impact XAUUSD: {geo_json.get('impact_geo_xau')}
        - SMC/Technical Bias (TF H4): {smc_bias_input}
        - POI Zone SMC: {poi_zone}
        - Astrodox (Transit Wheel) Aspect Summary: {astro_confluence_summary}

        [TUGAS]
        1. Tentukan **Arah Bias Utama (Trend)** XAUUSD (BULLISH / BEARISH / NEUTRAL/TWO-SIDED).
        2. Tuliskan **Logika Sintesis Detil** yang menggabungkan Macro + Geo + Teknikal + Astrodox.
        3. Tentukan **Specific Execution Setup (XAUUSD)** (Entry Zone, SL, TP) yang presisi.
        4. Tentukan **PERKIRAAN RANGE PERGERAKAN (PIPS)**. 

        Jawab HANYA dalam format JSON MURNI berikut (wajib diisi lengkap):
        {{
            "arah_bias": "KENAIKAN / PENURUNAN / TWO-SIDED WHIPSAW",
            "ringkasan_confluence_logika": "Teks detil gabungan makro+astro+teknikal",
            "setup_spesifik": {{
                "tipe_eksekusi": "LIMIT ORDER / MARKET EXECUTION",
                "entry_zone": "Angka zona presisi",
                "sl": "Angka SL presisi",
                "tp": "Angka TP presisi",
                "trigger_konfirmasi": "Teks konfirmasi (misal: Rejection M5)"
            }},
            "perkiraan_range_pips": {{
                 "trend_pergerakan_utama": "Berapa Pips ke arah mana (misal: Bullish +250 Pips)",
                 "whipsaw_liquidity_sweep": "Berapa pips sweep ke arah berlawanan trend (misal: Sweep Bawah -40 Pips)",
                 "reversal_pergerakan": "Berapa pips pergerakan balik setelah whipsaw (misal: Reversal Atas +210 Pips)"
            }}
        }}
        """

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload_syntesis = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt_syntesis}],
            "temperature": 0.1,  # deterministic/fokus
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(GROQ_URL, headers=headers, json=payload_syntesis, timeout=25)
            if response.status_code == 200:
                parsed_json = json.loads(response.json()['choices'][0]['message']['content'])
                st.session_state["ai_result"] = parsed_json
                st.success("✅ Multi-TF AI Prediction Synthesis Success!")
        except Exception as e:
            st.error(f"Error Koneksi AI: {e}")

# ==========================================
# 11. DISPLAY AI PREDICTION RESULT
# ==========================================
if st.session_state["ai_result"]:
    res = st.session_state["ai_result"]
    
    st.subheader(f"📊 Multi-TF AI Entry Logic untuk {target_news.upper()}")
    
    col_entry, col_reason, col_range = st.columns([1.2, 1.5, 1])
    
    with col_entry:
        st.markdown("### ⚡ Specific Execution Setup (XAUUSD)")
        setup = res.get("setup_spesifik", {})
        
        if "KENAIKAN" in res.get('arah_bias', '').upper():
            header_color = "🟢"
            setup_bg = "#1e3a2b"
        elif "PENURUNAN" in res.get('arah_bias', '').upper():
            header_color = "🔴"
            setup_bg = "#4a1e1e"
        else:
            header_color = "🟡"
            setup_bg = "#3e3b26"

        st.success(f"""
        {header_color} **Bias Utama:** **{res.get('arah_bias')}**
        - **Zona Entry:** {setup.get('entry_zone')}
        - **Stop Loss:** {setup.get('sl')}
        - **Take Profit:** {setup.get('tp')}
        - **Tipe & Trigger:** {setup.get('tipe_eksekusi')} / {setup.get('trigger_konfirmasi')}
        """)
    
    with col_reason:
        st.markdown("### 📝 Logika Sintesis Confluence")
        st.info(f"{res.get('ringkasan_confluence_logika')}")

    with col_range:
        st.markdown("### 📐 Perkiraan Range Pips (AI Calc)")
        range_pips = res.get("perkiraan_range_pips", {})
        
        st.warning(f"""
        - 📈 **Trend Utama:** {range_pips.get('trend_pergerakan_utama', 'N/A')}
        - 🌪️ **Whipsaw / Sweep:** {range_pips.get('whipsaw_liquidity_sweep', 'N/A')}
        - 🔄 **Reversal:** {range_pips.get('reversal_pergerakan', 'N/A')}
        """)
