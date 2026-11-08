import base64
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import requests
import pandas as pd
import time
from collections import defaultdict
import streamlit.components.v1 as components
import plotly.graph_objects as go

st.set_page_config(
    page_title="ABEL FX Tools",
    page_icon="⚡",
    layout="wide"
)

# ================= THEME & BACKGROUND =================
def apply_theme_and_background(theme_mode, video_file):
    css_base = """
    <style>
        section[data-testid="stSidebar"] {
            backdrop-filter: blur(12px);
            border-right: 1px solid #1e293b !important;
        }
        section[data-testid="stSidebar"] > div {
            background: transparent !important;
        }
        .sidebar-brand {
            text-align: center;
            font-size: 24px;
            font-weight: 800;
            color: #00d4ff;
            padding: 18px 0 8px 0;
            letter-spacing: 1.5px;
        }
        .sidebar-sub {
            text-align: center;
            color: #94a3b8;
            font-size: 12px;
            margin-bottom: 20px;
        }
        .welcome-box {
            border-radius: 18px;
            padding: 85px 30px;
            text-align: center;
            margin-top: 40px;
        }
        .info-box {
            border-radius: 12px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
        }
    </style>
    """
    st.markdown(css_base, unsafe_allow_html=True)

    if theme_mode == "🖼️ Wallpaper Mode":
        try:
            with open(video_file, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            components.html(f"""
                <script>
                (function() {{
                    const parent = window.parent.document;
                    let old = parent.getElementById('bg-video');
                    if (old) old.remove();
                    let v = parent.createElement('video');
                    v.id = 'bg-video';
                    v.autoplay = true;
                    v.muted = true;
                    v.loop = true;
                    v.playsInline = true;
                    v.src = "data:video/mp4;base64,{encoded}";
                    v.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-999;object-fit:cover;";
                    parent.body.prepend(v);
                    v.play().catch(()=>{{
                        parent.body.addEventListener('click', ()=>v.play(), {{once:true}});
                        parent.body.addEventListener('touchstart', ()=>v.play(), {{once:true}});
                    }});
                    let style = parent.getElementById('bg-style');
                    if (!style) {{
                        style = parent.createElement('style');
                        style.id = 'bg-style';
                        style.innerHTML = `.stApp{{background:transparent !important;}} section[data-testid="stSidebar"]{{background:rgba(10,15,28,0.85) !important;}} .welcome-box,.info-box{{background:rgba(11,16,30,0.92) !important;backdrop-filter:blur(12px);border:1px solid rgba(0,212,255,0.3) !important;box-shadow:0 8px 32px 0 rgba(0,0,0,0.5);}}`;
                        parent.head.appendChild(style);
                    }}
                }})();
                </script>
            """, height=0)
        except Exception as e:
            st.warning(f"Gagal load video background: {e}")
    elif theme_mode == "🌙 Dark Clean":
        st.markdown("""
        <style>
            .stApp { background-color: #070a0f !important; }
            section[data-testid="stSidebar"] { background-color: #0b1118 !important; }
            .welcome-box, .info-box {
                background: #0b1118 !important;
                border: 1px solid #1e293b !important;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            .stApp { background-color: #ffffff !important; color: #000000 !important; }
            section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
            .welcome-box, .info-box {
                background: #f8f9fa !important;
                border: 1px solid #d1d5db !important;
                color: #111827 !important;
            }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown('<div class="sidebar-brand">⚡ ABEL FX</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-sub">Trading Tools</div>', unsafe_allow_html=True)
st.sidebar.markdown("### 📌 Navigasi Menu")

if "active_menu" not in st.session_state:
    st.session_state.active_menu = "🏠 Menu Utama"

def sidebar_menu_button(label, icon, target_key):
    is_active = st.session_state.active_menu == target_key
    button_label = f"{icon}  {label}"
    active_border = "border-left: 4px solid #00d4ff !important;" if is_active else "border-left: 4px solid transparent !important;"
    active_bg = "background-color: rgba(0, 212, 255, 0.15) !important; color: #00d4ff !important;" if is_active else ""
    st.markdown(f"""
    <style>
    div.stButton > button[kind="secondary"][data-baseweb="button"]:has-text("{label}") {{
        text-align: left !important;
        width: 100% !important;
        border-radius: 6px !important;
        margin-bottom: 4px !important;
        {active_border}
        {active_bg}
    }}
    </style>
    """, unsafe_allow_html=True)
    if st.sidebar.button(button_label, use_container_width=True, key=f"btn_{target_key}"):
        st.session_state.active_menu = target_key
        st.rerun()

sidebar_menu_button("Menu Utama", "🏠", "🏠 Menu Utama")
sidebar_menu_button("Astrodox", "🔮", "🔮 Astrodox")
sidebar_menu_button("Orderbook", "📊", "📊 Orderbook")
sidebar_menu_button("Kalkulator", "🧮", "🧮 Kalkulator")

menu = st.session_state.active_menu

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Tema Tampilan")
selected_theme = st.sidebar.selectbox(
    "Pilih Tema",
    ["🖼️ Wallpaper Mode", "🌙 Dark Clean", "☀️ Light Clean"],
    index=0,
    label_visibility="collapsed"
)
apply_theme_and_background(selected_theme, "bg.mp4")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align:center; color:#94a3b8; font-size:12px; padding-top:5px;">
    ABEL FX Tools
</div>
""", unsafe_allow_html=True)

# ==========================================
# ASTRODOX ENGINE
# ==========================================
ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ZODIAC_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def compute_planetary_positions(dt_utc):
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day
    hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour / 24.0 + B - 1524.5
    d = jd - 2451545.0
    L_sun = (280.466 + 0.9856474 * d) % 360
    g_sun = np.radians((357.528 + 0.9856003 * d) % 360)
    sun_lon = (L_sun + 1.915 * np.sin(g_sun) + 0.020 * np.sin(2 * g_sun)) % 360
    L_moon = (218.316 + 13.176396 * d) % 360
    M_moon = np.radians((134.963 + 13.064993 * d) % 360)
    moon_lon = (L_moon + 6.289 * np.sin(M_moon) - 1.274 * np.sin(M_moon - 2 * np.radians(sun_lon - L_sun))) % 360
    mercury_lon = (sun_lon + 18.0 * np.sin(np.radians((29.0 + 4.092 * d) % 360))) % 360
    venus_lon = (sun_lon + 42.0 * np.sin(np.radians((210.0 + 1.602 * d) % 360))) % 360
    mars_lon = (355.43 + 0.524033 * d + 10.0 * np.sin(np.radians((19.0 + 0.524 * d) % 360))) % 360
    jupiter_lon = (34.35 + 0.083091 * d) % 360
    saturn_lon = (50.08 + 0.033459 * d) % 360
    uranus_lon = (58.00 + 0.011728 * d) % 360
    neptune_lon = (358.00 + 0.005981 * d) % 360
    pluto_lon = (302.00 + 0.003970 * d) % 360
    raw_degs = {
        "Sun ☉": sun_lon,
        "Moon ☽": moon_lon,
        "Mercury ☿": mercury_lon,
        "Venus ♀": venus_lon,
        "Mars ♂": mars_lon,
        "Jupiter ♃": jupiter_lon,
        "Saturn ♄": saturn_lon,
        "Uranus ♅": uranus_lon,
        "Neptune ♆": neptune_lon,
        "Pluto ♇": pluto_lon
    }
    formatted_pos = {}
    for name, deg in raw_degs.items():
        z_idx = int(deg // 30)
        z_deg = int(deg % 30)
        z_min = int(((deg % 30) - z_deg) * 60)
        formatted_pos[name] = f"{ZODIAC_NAMES[z_idx]} {z_deg}°{z_min:02d}'"
    return raw_degs, formatted_pos

def generate_astrodox_wheel_only(target_date: datetime):
    dt_utc = target_date - timedelta(hours=7)
    planet_degrees, planet_positions = compute_planetary_positions(dt_utc)
    fig = plt.figure(figsize=(10.5, 10.5), facecolor='#070a0f')
    ax = fig.add_subplot(111, polar=True, facecolor='#070a0f')
    ax.set_theta_zero_location("W")
    ax.set_theta_direction(-1)
    ax.grid(False)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    colors = ['#4a2e2b', '#3e3b26', '#1e3a2b', '#1e2b3a'] * 3
    for i in range(12):
        theta_start = np.radians(i * 30)
        theta_end = np.radians((i + 1) * 30)
        ax.bar(
            x=(theta_start + theta_end) / 2,
            height=0.25,
            width=np.radians(30),
            bottom=0.75,
            color=colors[i],
            alpha=0.6,
            edgecolor='#555555'
        )
        ax.text(
            (theta_start + theta_end) / 2,
            0.88,
            ZODIAC_SYMBOLS[i],
            color='white',
            fontsize=16,
            ha='center',
            va='center',
            fontweight='bold'
        )
    for name, deg in planet_degrees.items():
        rad = np.radians(deg)
        ax.plot(rad, 0.70, marker='o', color='#00ffff', markersize=7)
        ax.text(rad, 0.60, name.split()[-1], color='white', fontsize=13, ha='center', va='center', fontweight='bold')
    aspect_counts = {"merah": 0, "hijau": 0, "biru": 0, "kuning": 0}
    planets_keys = list(planet_degrees.keys())
    deg_list = list(planet_degrees.values())
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
                ax.plot([rad1, rad2], [0.70, 0.70], color='#ff3333', alpha=0.85, linewidth=1.6)
                aspect_counts["merah"] += 1
            elif abs(diff - 120) <= 7:
                ax.plot([rad1, rad2], [0.70, 0.70], color='#00ff66', alpha=0.85, linewidth=1.6)
                aspect_counts["hijau"] += 1
            elif abs(diff - 60) <= 6:
                ax.plot([rad1, rad2], [0.70, 0.70], color='#3399ff', alpha=0.75, linewidth=1.3)
                aspect_counts["biru"] += 1
            elif diff <= 7:
                ax.plot([rad1, rad2], [0.70, 0.70], marker='*', color='#ffff00', alpha=0.9, linewidth=2.2, markersize=9)
                aspect_counts["kuning"] += 1
    ax.set_title(f"{target_date.strftime('%d.%m.%Y %H:%M WIB')}", color='white', fontsize=16, pad=18, fontweight='bold')
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=220, bbox_inches='tight', facecolor='#070a0f')
    img_buf.seek(0)
    return fig, img_buf, aspect_counts, planet_positions

# ==========================================
# MARKET DATA - FUTURES BINANCE + BYBIT, OKX SPOT (KARENA OKX GAK PUNYA XAUT FUTURES)
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

PROXY_PREFIX = "https://api.allorigins.win/raw?url="

def _safe_json(resp):
    try:
        txt = resp.text.strip()
        if not txt:
            return None
        if txt[0] not in "{[":
            return None
        return resp.json()
    except Exception:
        return None

def _to_binance_symbol(s):
    return s.replace("-", "").upper()

def _to_bybit_symbol(s):
    return s.replace("-", "").upper()

def _get_via_proxy(url):
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        d = _safe_json(r)
        if d:
            return d
    except:
        pass
    try:
        proxy_url = PROXY_PREFIX + url
        r = requests.get(proxy_url, timeout=12, headers=HEADERS)
        d = _safe_json(r)
        return d
    except:
        return None

# >>> OKX SPOT - karena OKX tidak punya XAUT-USDT-SWAP / XAUT-USD-SWAP, dipaksain futures error terus <<<
def get_okx_orderbook(symbol="XAUT-USDT", limit=400):
    try:
        url = f"https://www.okx.com/api/v5/market/books?instId={symbol}&sz={limit}"
        r = requests.get(url, timeout=10, headers=HEADERS)
        data = _safe_json(r)
        if not data or data.get("code") != "0":
            return None, None, data.get("msg", "Error") if data else "Error"
        book = data["data"][0]
        bids = [[float(p), float(q)] for p, q, *_ in book["bids"]]
        asks = [[float(p), float(q)] for p, q, *_ in book["asks"]]
        return bids, asks, None
    except Exception as e:
        return None, None, str(e)

def get_okx_ticker(symbol="XAUT-USDT"):
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
        r = requests.get(url, timeout=8, headers=HEADERS)
        data = _safe_json(r)
        if not data or data.get("code") != "0":
            return None
        t = data["data"][0]
        last = float(t["last"])
        open24h = float(t["open24h"])
        change_pct = ((last - open24h) / open24h * 100) if open24h else 0
        return {
            "last": last,
            "high24h": float(t["high24h"]),
            "low24h": float(t["low24h"]),
            "vol24h": float(t["vol24h"]),
            "change_pct": change_pct
        }
    except:
        return None

def get_okx_trades(symbol="XAUT-USDT", limit=40):
    try:
        url = f"https://www.okx.com/api/v5/market/trades?instId={symbol}&limit={limit}"
        r = requests.get(url, timeout=8, headers=HEADERS)
        data = _safe_json(r)
        if not data or data.get("code") != "0":
            return []
        result = []
        for t in data["data"]:
            result.append({
                "time": datetime.fromtimestamp(int(t["ts"]) / 1000).strftime("%H:%M:%S"),
                "price": float(t["px"]),
                "size": float(t["sz"]),
                "side": t["side"]
            })
        return result
    except:
        return []

# ================= TAMBAHAN REQUEST: BINANCE + BYBIT + GABUNGAN =================
# >>> FUTURES - Binance fapi via proxy <<<
def get_binance_orderbook(symbol="XAUT-USDT", limit=100):
    sym = _to_binance_symbol(symbol)
    urls = [
        f"https://fapi.binance.com/fapi/v1/depth?symbol={sym}&limit={limit}",
        f"https://api.binance.com/fapi/v1/depth?symbol={sym}&limit={limit}",
    ]
    for url in urls:
        data = _get_via_proxy(url)
        if data and "bids" in data and "asks" in data:
            bids = [[float(p), float(q)] for p, q in data["bids"]]
            asks = [[float(p), float(q)] for p, q in data["asks"]]
            return bids, asks, None
    return None, None, "Binance: respon bukan JSON (coba Refresh lagi)"

def get_binance_ticker(symbol="XAUT-USDT"):
    sym = _to_binance_symbol(symbol)
    urls = [
        f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={sym}",
        f"https://api.binance.com/fapi/v1/ticker/24hr?symbol={sym}",
    ]
    for url in urls:
        t = _get_via_proxy(url)
        if t and "lastPrice" in t:
            last = float(t["lastPrice"])
            open24h = float(t["openPrice"])
            change_pct = ((last - open24h) / open24h * 100) if open24h else 0
            return {
                "last": last,
                "high24h": float(t["highPrice"]),
                "low24h": float(t["lowPrice"]),
                "vol24h": float(t["volume"]),
                "change_pct": change_pct
            }
    return None

def get_binance_trades(symbol="XAUT-USDT", limit=40):
    sym = _to_binance_symbol(symbol)
    urls = [
        f"https://fapi.binance.com/fapi/v1/trades?symbol={sym}&limit={limit}",
        f"https://api.binance.com/fapi/v1/trades?symbol={sym}&limit={limit}",
    ]
    for url in urls:
        data = _get_via_proxy(url)
        if isinstance(data, list):
            out = []
            for t in data:
                if t.get("isBuyerMaker"):
                    side = "sell"
                else:
                    side = "buy"
                out.append({
                    "time": datetime.fromtimestamp(int(t["time"]) / 1000).strftime("%H:%M:%S"),
                    "price": float(t["price"]),
                    "size": float(t["qty"]),
                    "side": side
                })
            return out
    return []

# >>> FUTURES - Bybit linear via proxy <<<
def get_bybit_orderbook(symbol="XAUT-USDT", limit=50):
    sym = _to_bybit_symbol(symbol)
    hosts = ["https://api.bybit.com", "https://api.bytick.com"]
    for host in hosts:
        url = f"{host}/v5/market/orderbook?category=linear&symbol={sym}&limit={limit}"
        data = _get_via_proxy(url)
        if data and data.get("retCode") == 0:
            book = data["result"]
            bids = [[float(p), float(q)] for p, q in book["b"]]
            asks = [[float(p), float(q)] for p, q in book["a"]]
            return bids, asks, None
    return None, None, "Bybit: respon bukan JSON (rate-limit / Cloudflare, coba Refresh lagi)"

def get_bybit_ticker(symbol="XAUT-USDT"):
    sym = _to_bybit_symbol(symbol)
    hosts = ["https://api.bybit.com", "https://api.bytick.com"]
    for host in hosts:
        url = f"{host}/v5/market/tickers?category=linear&symbol={sym}"
        data = _get_via_proxy(url)
        if data and data.get("retCode") == 0:
            t = data["result"]["list"][0]
            last = float(t["lastPrice"])
            if t.get("prevPrice24h"):
                open24h = float(t["prevPrice24h"])
            else:
                open24h = last
            if t.get("price24hPcnt"):
                change_pct = float(t.get("price24hPcnt", 0)) * 100
            else:
                if open24h:
                    change_pct = (last - open24h) / open24h * 100
                else:
                    change_pct = 0
            return {
                "last": last,
                "high24h": float(t["highPrice24h"]),
                "low24h": float(t["lowPrice24h"]),
                "vol24h": float(t["volume24h"]),
                "change_pct": change_pct
            }
    return None

def get_bybit_trades(symbol="XAUT-USDT", limit=40):
    sym = _to_bybit_symbol(symbol)
    hosts = ["https://api.bybit.com", "https://api.bytick.com"]
    for host in hosts:
        url = f"{host}/v5/market/recent-trade?category=linear&symbol={sym}&limit={limit}"
        data = _get_via_proxy(url)
        if data and data.get("retCode") == 0:
            out = []
            for t in data["result"]["list"]:
                if t.get("side", "").lower() == "buy":
                    side = "buy"
                else:
                    side = "sell"
                out.append({
                    "time": datetime.fromtimestamp(int(t["time"]) / 1000).strftime("%H:%M:%S"),
                    "price": float(t["price"]),
                    "size": float(t["size"]),
                    "side": side
                })
            return out
    return []

def get_combined_orderbook(symbol="XAUT-USDT", limit=400):
    all_bids = []
    all_asks = []
    errors = []
    b1, a1, e1 = get_okx_orderbook(symbol, limit=limit)
    if b1:
        all_bids.extend(b1)
        all_asks.extend(a1)
    else:
        errors.append(f"OKX: {e1}")
    b2, a2, e2 = get_binance_orderbook(symbol, limit=100)
    if b2:
        all_bids.extend(b2)
        all_asks.extend(a2)
    else:
        errors.append(f"Binance: {e2}")
    b3, a3, e3 = get_bybit_orderbook(symbol, limit=50)
    if b3:
        all_bids.extend(b3)
        all_asks.extend(a3)
    else:
        errors.append(f"Bybit: {e3}")
    if not all_bids and not all_asks:
        return None, None, " | ".join(errors)

    def merge(orders):
        d = defaultdict(float)
        for p, q in orders:
            key = round(p, 1)
            d[key] += q
        merged = [[k, v] for k, v in d.items()]
        merged = sorted(merged, key=lambda x: x[0])
        return merged

    bids_m = sorted(merge(all_bids), key=lambda x: x[0], reverse=True)
    asks_m = sorted(merge(all_asks), key=lambda x: x[0])
    if errors:
        st.session_state["combined_warning"] = " | ".join(errors)
    else:
        st.session_state["combined_warning"] = None
    return bids_m, asks_m, None

def get_combined_ticker(symbol="XAUT-USDT"):
    for fn in [get_okx_ticker, get_binance_ticker, get_bybit_ticker]:
        t = fn(symbol)
        if t:
            return t
    return None

def get_combined_trades(symbol="XAUT-USDT", limit=40):
    all_trades = []
    all_trades.extend(get_okx_trades(symbol, limit))
    all_trades.extend(get_binance_trades(symbol, limit))
    all_trades.extend(get_bybit_trades(symbol, limit))
    all_trades.sort(key=lambda x: x["time"], reverse=True)
    return all_trades[:limit]
# ================= END TAMBAHAN BINANCE/BYBIT =================

def get_xauusd_price():
    try:
        r = requests.get("https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT", timeout=6)
        data = r.json()
        if "symbols" in data and len(data["symbols"]) > 0:
            return float(data["symbols"][0]["price"])
    except:
        pass
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=6)
        data = r.json()
        if "price" in data:
            return float(data["price"])
    except:
        pass
    return None

def get_btcusd_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=8)
        data = r.json()
        if "bitcoin" in data and "usd" in data["bitcoin"]:
            return float(data["bitcoin"]["usd"])
    except:
        pass
    try:
        r = requests.get("https://api.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT", timeout=6)
        data = r.json()
        if "price" in data:
            return float(data["price"])
    except:
        pass
    return None

def aggregate_orders(orders, aggregation: float, side: str = "bid"):
    if aggregation <= 0.1:
        result = []
        for p, s in orders:
            result.append([round(p, 1), s])
        return result
    grouped = defaultdict(float)
    for price, size in orders:
        if side == "bid":
            key = (price // aggregation) * aggregation
        else:
            key = ((price + aggregation - 1e-9) // aggregation) * aggregation
        grouped[key] += size
    result = [[price, size] for price, size in grouped.items()]
    if side == "bid":
        result.sort(key=lambda x: x[0], reverse=True)
    else:
        result.sort(key=lambda x: x[0])
    return result

def show_orderbook_visual(bids, asks, aggregation=0.1, sort_order="Default (Harga)"):
    if not bids or not asks:
        st.warning("Data orderbook kosong")
        return
    bids = aggregate_orders(bids, aggregation, side="bid")
    asks = aggregate_orders(asks, aggregation, side="ask")
    bids_data = []
    for p, s in bids:
        bids_data.append({"price": p, "size": s, "notional": s * p})
    asks_data = []
    for p, s in asks:
        asks_data.append({"price": p, "size": s, "notional": s * p})
    if sort_order == "Size Kecil → Besar":
        bids_data = sorted(bids_data, key=lambda x: x["size"])
        asks_data = sorted(asks_data, key=lambda x: x["size"])
    elif sort_order == "Size Besar → Kecil":
        bids_data = sorted(bids_data, key=lambda x: x["size"], reverse=True)
        asks_data = sorted(asks_data, key=lambda x: x["size"], reverse=True)
    max_bid = max([x["size"] for x in bids_data[:40]], default=1)
    max_ask = max([x["size"] for x in asks_data[:40]], default=1)
    max_size = max(max_bid, max_ask)
    if aggregation >= 10:
        max_display = 30
    else:
        max_display = 25
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🟢 Beli (Bids)")
        for item in bids_data[:max_display]:
            pct = min(item["size"] / max_size, 1.0)
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                background:linear-gradient(90deg,#0d3b2e {pct*100}%,transparent 0%);
                padding:7px 12px;margin:3px 0;border-radius:6px;font-size:14px;">
                <span style="color:#00ff9d;font-weight:600;">{item['size']:,.2f} <span style="color:#94a3b8;font-size:12px;">(${item['notional']:,.0f})</span></span>
                <span style="color:inherit;font-weight:500;">{item['price']:,.1f}</span>
            </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("### 🔴 Jual (Asks)")
        for item in asks_data[:max_display]:
            pct = min(item["size"] / max_size, 1.0)
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                background:linear-gradient(270deg,#3b0d0d {pct*100}%,transparent 0%);
                padding:7px 12px;margin:3px 0;border-radius:6px;font-size:14px;">
                <span style="color:inherit;font-weight:500;">{item['price']:,.1f}</span>
                <span style="color:#ff4d4d;font-weight:600;">{item['size']:,.2f} <span style="color:#94a3b8;font-size:12px;">(${item['notional']:,.0f})</span></span>
            </div>""", unsafe_allow_html=True)

# ================= BARU: MAPPING XAUT -> XAUUSD / BTC -> BTCUSD =================
def _calc_spot_mapping(symbol_clean, token_last, spot_ref):
    if token_last is None or spot_ref is None:
        return None, None, None
    selisih = token_last - spot_ref
    if "XAUT" in symbol_clean:
        label = "XAUUSD"
    elif "BTC" in symbol_clean:
        label = "BTCUSD"
    else:
        label = "SPOT"
    return selisih, label, spot_ref

# ================= GAMBAR ZONA LIKUIDITAS + MAPPING XAUUSD =================
def generate_zona_image(high_heat_prices, symbol, exchange_label="", token_last=None, spot_ref=None):
    clean_symbol = symbol
    clean_exchange = exchange_label
    if "_" in symbol:
        parts = symbol.split("_")
        clean_symbol = parts[0]
        if len(parts) > 1:
            clean_exchange = "_".join(parts[1:])
        else:
            clean_exchange = exchange_label
    if clean_exchange == symbol:
        clean_exchange = ""
    if clean_exchange:
        title_pair = f"{clean_symbol} - {clean_exchange}"
    else:
        title_pair = clean_symbol
    now_wib = datetime.now() + timedelta(hours=7)
    time_str = now_wib.strftime('%d %b %Y %H:%M:%S WIB')
    selisih, spot_label, _ = _calc_spot_mapping(clean_symbol, token_last, spot_ref)
    sorted_zones = sorted(high_heat_prices, key=lambda x: x["min_price"], reverse=True)
    n = len(sorted_zones)
    fig_w = 12
    fig_h = 4.1 + n * 1.15
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor='#070a0f')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, fig_h)
    ax.axis('off')
    fig.patch.set_facecolor('#070a0f')
    ax.set_facecolor('#070a0f')
    ax.text(0.3, fig_h - 0.7, "⚡ ABEL FX - ZONA LIKUIDITAS TINGGI", color='#00d4ff', fontsize=16, fontweight='bold', va='center', ha='left')
    ax.text(0.3, fig_h - 1.25, f"{title_pair}  |  Heat Score > 15  |  {time_str}", color='#94a3b8', fontsize=11, va='center', ha='left')
    if selisih is not None:
        if selisih > 0:
            tag = "Premium"
        elif selisih < 0:
            tag = "Discount"
        else:
            tag = "Par"
        if "XAUT" in clean_symbol:
            token_name = "XAUT"
        elif "BTC" in clean_symbol:
            token_name = "BTC"
        else:
            token_name = "TOKEN"
        header_mapping = f"{token_name} {token_last:,.1f}  |  {spot_label} {spot_ref:,.1f}  |  Selisih {selisih:+.1f} ({tag})  |  Rumus: Zona {spot_label} = Zona {token_name} - Selisih"
        ax.text(0.3, fig_h - 1.75, header_mapping, color='#f5bc18', fontsize=11, fontweight='bold', va='center', ha='left')
        ax.plot([0.3, 9.7], [fig_h - 2.05, fig_h - 2.05], color='#1e293b', linewidth=1.5)
        y_top = fig_h - 2.65
    else:
        ax.plot([0.3, 9.7], [fig_h - 1.6, fig_h - 1.6], color='#1e293b', linewidth=1.5)
        y_top = fig_h - 2.15
    from matplotlib.patches import FancyBboxPatch
    for item in sorted_zones:
        p_min = item['min_price']
        p_max = item['max_price']
        h_val = item['heat']
        if h_val >= 22.0:
            border = '#ffffff'
        elif h_val >= 18.0:
            border = '#f5bc18'
        else:
            border = '#e06b1e'
        if p_min == p_max:
            price_str = f"{p_min:,.1f}"
        else:
            price_str = f"{p_min:,.1f} - {p_max:,.1f}"
        box = FancyBboxPatch(
            (0.3, y_top - 0.85),
            9.4,
            0.85,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor='#0b1118',
            edgecolor=border,
            linewidth=2.0
        )
        ax.add_patch(box)
        center_y = y_top - 0.425
        ax.text(0.6, center_y + 0.22, price_str, color='white', fontsize=15, fontweight='bold', va='center', ha='left')
        ax.text(0.6, center_y - 0.12, "RENTANG HARGA", color='#94a3b8', fontsize=8, fontweight='bold', va='center', ha='left')
        if selisih is not None:
            if p_min == p_max:
                spot_str = f"≈ {spot_label} {p_min - selisih:,.1f}"
            else:
                spot_str = f"≈ {spot_label} {p_min - selisih:,.1f} - {p_max - selisih:,.1f}"
            ax.text(0.6, center_y - 0.32, spot_str, color='#00d4ff', fontsize=11, fontweight='bold', va='center', ha='left')
        ax.text(9.4, center_y, f"Heat: {h_val:.1f}", color=border, fontsize=12, fontweight='bold', va='center', ha='right')
        y_top -= 1.15
    ax.text(0.3, 0.35, "ABEL FX Tools - Simpan zona ini untuk pengingat level. Bukan sinyal pasti, konfirmasi dengan struktur harga.", color='#64748b', fontsize=9, va='center', ha='left')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='#070a0f', pad_inches=0.2)
    plt.close(fig)
    buf.seek(0)
    return buf
# ================= END GAMBAR ZONA =================

# ==========================================
# ROLLING HEATMAP COMPONENT
# ==========================================
def render_rolling_heatmap(bids, asks, symbol, ref_price=None, last_price=None):
    st.markdown("### 🔥 Orderbook Liquidity Heatmap (Bookmap Theme)")
    st.caption("Visualisasi konsentrasi likuiditas real-time. Kotak harga menggunakan border transparan sesuai warna heat dan sejajar presisi.")
    if "heatmap_history" not in st.session_state:
        st.session_state.heatmap_history = {}
    heat_key = f"{symbol}_bookmap_heatmap"
    if heat_key not in st.session_state.heatmap_history:
        st.session_state.heatmap_history[heat_key] = {"times": [], "price_map": defaultdict(list)}
    history = st.session_state.heatmap_history[heat_key]
    current_time = datetime.now().strftime("%H:%M:%S")
    current_mid_price = 0
    if bids and asks:
        current_mid_price = (bids[0][0] + asks[0][0]) / 2
    current_snapshot = {}
    for p, s in bids + asks:
        if current_mid_price and (p < current_mid_price * 0.90 or p > current_mid_price * 1.10):
            continue
        rounded_p = round(p, 1)
        current_snapshot[rounded_p] = current_snapshot.get(rounded_p, 0) + s
    history["times"].append(current_time)
    if len(history["times"]) > 40:
        history["times"].pop(0)
    all_prices = sorted(list(current_snapshot.keys()))
    if not all_prices:
        st.info("Menunggu data heatmap terkumpul...")
        return
    for p in all_prices:
        if p not in history["price_map"]:
            history["price_map"][p] = []
        history["price_map"][p].append(current_snapshot.get(p, 0))
        if len(history["price_map"][p]) > len(history["times"]):
            history["price_map"][p] = history["price_map"][p][-len(history["times"]):]
    active_price_map = {}
    for p in all_prices:
        if p in history["price_map"] and len(history["price_map"][p]) == len(history["times"]):
            active_price_map[p] = history["price_map"][p]
    if not active_price_map:
        st.info("Mengumpulkan riwayat snapshot...")
        return
    y_prices = list(active_price_map.keys())
    z_matrix = [active_price_map[p] for p in y_prices]
    x_times = history["times"]
    flat_z = []
    for row in z_matrix:
        for val in row:
            flat_z.append(val)
    if flat_z:
        max_z_val = max(flat_z)
    else:
        max_z_val = 1.0
    raw_high_heat = []
    for i, p in enumerate(y_prices):
        if z_matrix[i]:
            avg_p_val = np.mean(z_matrix[i])
        else:
            avg_p_val = 0
        if max_z_val > 0:
            heat_score = min(25.0, (avg_p_val / max_z_val) * 25.0)
        else:
            heat_score = 0
        if heat_score > 15.0:
            raw_high_heat.append({"price": p, "heat": heat_score})
    high_heat_prices = []
    if raw_high_heat:
        raw_high_heat.sort(key=lambda x: x["price"])
        current_cluster = [raw_high_heat[0]]
        for item in raw_high_heat[1:]:
            if item["price"] - current_cluster[-1]["price"] <= 1.5:
                current_cluster.append(item)
            else:
                p_min = current_cluster[0]["price"]
                p_max = current_cluster[-1]["price"]
                max_h = max(c["heat"] for c in current_cluster)
                high_heat_prices.append({"min_price": p_min, "max_price": p_max, "heat": max_h})
                current_cluster = [item]
        p_min = current_cluster[0]["price"]
        p_max = current_cluster[-1]["price"]
        max_h = max(c["heat"] for c in current_cluster)
        high_heat_prices.append({"min_price": p_min, "max_price": p_max, "heat": max_h})
    bookmap_colorscale = [
        [0.0, '#040b18'],
        [0.2, '#0d2347'],
        [0.5, '#1d547f'],
        [0.75, '#e06b1e'],
        [0.9, '#f5bc18'],
        [1.0, '#ffffff']
    ]
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=x_times,
        y=y_prices,
        colorscale=bookmap_colorscale,
        hoverongaps=False,
        colorbar=dict(
            title=dict(text="Likuiditas", font=dict(color="#94a3b8")),
            x=-0.12,
            xanchor="right",
            len=0.85,
            thickness=14,
            tickfont=dict(color="#94a3b8")
        )
    ))
    annotations = []
    shapes = []
    for item in high_heat_prices:
        p_min = item['min_price']
        p_max = item['max_price']
        h_val = item['heat']
        mid_p = (p_min + p_max) / 2
        if h_val >= 22.0:
            color_code = "#ffffff"
        elif h_val >= 18.0:
            color_code = "#f5bc18"
        else:
            color_code = "#e06b1e"
        shapes.append(dict(
            type="rect",
            xref="paper",
            yref="y",
            x0=1.0,
            x1=1.07,
            y0=p_min - 0.5,
            y1=p_max + 0.5,
            fillcolor="rgba(0,0,0,0)",
            opacity=1.0,
            line=dict(color=color_code, width=2)
        ))
        if p_min == p_max:
            display_price_str = f"{p_min:,.1f}"
        else:
            display_price_str = f"{p_min:,.1f}"
        annotations.append(dict(
            xref="paper",
            yref="y",
            x=1.035,
            y=p_max + 0.2,
            text=f"<b>{display_price_str}</b>",
            showarrow=False,
            font=dict(size=9, color=color_code),
            xanchor="center",
            yanchor="bottom"
        ))
        annotations.append(dict(
            xref="paper",
            yref="y",
            x=1.085,
            y=mid_p,
            text=f"<b>{h_val:.1f}</b>",
            showarrow=False,
            font=dict(size=10, color=color_code),
            xanchor="left",
            yanchor="middle"
        ))
    fig_heat.update_layout(
        title=dict(text=f"Liquidity Heatmap — {symbol}", font=dict(color="#ffffff")),
        xaxis_title="",
        yaxis_title="Harga",
        height=540,
        margin=dict(l=80, r=125, t=30, b=10),
        paper_bgcolor='#070a0f',
        plot_bgcolor='#070a0f',
        font=dict(color='#94a3b8'),
        yaxis=dict(side="right", gridcolor="#111827", zeroline=False),
        xaxis=dict(gridcolor="#111827"),
        shapes=shapes,
        annotations=annotations
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.markdown("#### ⚡ Zona Likuiditas Tinggi (Heat Score > 15)")
    if "_" in symbol:
        clean_for_label = symbol.split("_")[0]
    else:
        clean_for_label = symbol
    selisih_web, spot_label_web, _ = _calc_spot_mapping(clean_for_label, last_price, ref_price)
    if selisih_web is not None:
        if selisih_web > 0:
            tag_web = "Premium"
        elif selisih_web < 0:
            tag_web = "Discount"
        else:
            tag_web = "Par"
        if "XAUT" in clean_for_label:
            token_name_web = "XAUT"
        elif "BTC" in clean_for_label:
            token_name_web = "BTC"
        else:
            token_name_web = "TOKEN"
        st.info(f"📐 Mapping: {token_name_web} {last_price:,.1f} | {spot_label_web} {ref_price:,.1f} | Selisih {selisih_web:+.1f} ({tag_web}) — Zona {spot_label_web} = Zona {token_name_web} - Selisih")
    if high_heat_prices:
        cols = st.columns(min(3, len(high_heat_prices)))
        sorted_zones_web = sorted(high_heat_prices, key=lambda x: x["min_price"], reverse=True)
        for idx, item in enumerate(sorted_zones_web):
            h_val = item['heat']
            p_min = item['min_price']
            p_max = item['max_price']
            if h_val >= 22.0:
                border_color = "#ffffff"
            elif h_val >= 18.0:
                border_color = "#f5bc18"
            else:
                border_color = "#e06b1e"
            if p_min == p_max:
                display_price_str = f"{p_min:,.1f}"
            else:
                display_price_str = f"{p_min:,.1f} - {p_max:,.1f}"
            with cols[idx % len(cols)]:
                mapping_html = ""
                if selisih_web is not None:
                    if p_min == p_max:
                        spot_str_web = f"{p_min - selisih_web:,.1f}"
                    else:
                        spot_str_web = f"{p_min - selisih_web:,.1f} - {p_max - selisih_web:,.1f}"
                    mapping_html = f"""<div style="color:#00d4ff;font-weight:700;font-size:13px;margin-top:4px;">≈ {spot_label_web} {spot_str_web}</div>"""
                st.markdown(f"""
                <div style="border: 2px solid {border_color}; background: transparent;
                     border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex;
                     justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                    <div>
                        <span style="color: #94a3b8; font-size: 11px; display: block; font-weight: 600;">RENTANG HARGA</span>
                        <span style="color: #ffffff; font-weight: 800; font-size: 16px;">{display_price_str}</span>
                        {mapping_html}
                    </div>
                    <div style="background: transparent; border: 1px solid {border_color}; color: {border_color}; font-weight: 800; font-size: 13px;
                         padding: 4px 8px; border-radius: 6px;">
                        Heat: {h_val:.1f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    if high_heat_prices:
        st.markdown("---")
        try:
            zona_buf = generate_zona_image(high_heat_prices, symbol, exchange_label=symbol, token_last=last_price, spot_ref=ref_price)
            st.download_button(
                label="📥 Download Zona Likuiditas (.png)",
                data=zona_buf,
                file_name=f"Zona_Likuiditas_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                use_container_width=True,
                key=f"dl_zona_{symbol}_{datetime.now().strftime('%H%M%S')}"
            )
            st.caption("Gambar berisi zona + mapping XAUUSD + jam snapshot WIB, biar bisa lo simpan / share.")
        except Exception as e:
            st.warning(f"Gagal bikin gambar zona: {e}")
    else:
        st.markdown("<p style='color: #94a3b8; font-style: italic;'>Belum ada level harga dengan heat > 15 saat ini.</p>", unsafe_allow_html=True)

# ==========================================
# HALAMAN
# ==========================================
if menu == "🏠 Menu Utama":
    pass

elif menu == "🔮 Astrodox":
    st.title("🔮 Astrodox Wheel")
    st.caption("Roda Transit Planet + Rekap Aspek Geometri | Siap untuk di-copy ke AI eksternal")
    st.markdown("---")
    st.subheader("📅 Atur Waktu Transit")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        tanggal = st.number_input("Tanggal", 1, 31, 12)
    with c2:
        bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        bulan_nama = st.selectbox("Bulan", bulan_list, index=7)
        bulan = bulan_list.index(bulan_nama) + 1
    with c3:
        tahun = st.number_input("Tahun", 2000, 2100, 2026)
    with c4:
        jam = st.number_input("Jam", 0, 23, 19)
    with c5:
        menit = st.number_input("Menit", 0, 59, 30)
    try:
        event_datetime = datetime(int(tahun), int(bulan), int(tanggal), int(jam), int(menit))
    except:
        st.error("Tanggal tidak valid")
        st.stop()
    st.markdown(f"**Waktu yang dipilih:** `{event_datetime.strftime('%d %B %Y %H:%M WIB')}`")
    st.markdown("---")
    fig, img_buf, aspect_counts, planet_positions = generate_astrodox_wheel_only(event_datetime)
    st.subheader("🔮 Roda Astrodox Transit")
    st.pyplot(fig, use_container_width=True)
    col_dl1, col_dl2 = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            label="📥 Download Roda (.png)",
            data=img_buf,
            file_name=f"Astrodox_Wheel_{event_datetime.strftime('%Y%m%d_%H%M')}.png",
            mime="image/png",
            use_container_width=True
        )
    st.markdown("---")
    st.subheader("📋 Dashboard Info Astrodox")
    pos_lines = []
    pos_items = list(planet_positions.items())
    for i in range(0, len(pos_items), 2):
        p1, v1 = pos_items[i]
        if i + 1 < len(pos_items):
            p2, v2 = pos_items[i + 1]
            pos_lines.append(f"• {p1:<12}: {v1:<16}  |  • {p2:<12}: {v2}")
        else:
            pos_lines.append(f"• {p1:<12}: {v1}")
    pos_text = "\n".join(pos_lines)
    aspek_text = f"""• MERAH  (Square 90° / Opp 180°) : {aspect_counts['merah']} Garis  → Volatilitas Tinggi
- HIJAU  (Trine 120°)            : {aspect_counts['hijau']} Garis  → Expansion Trend
- BIRU   (Sextile 60°)           : {aspect_counts['biru']} Garis  → Retest Zone
- KUNING (Conjunction 0°)        : {aspect_counts['kuning']} Garis  → Turning Point"""
    info_html = f"""
    <div class="info-box">
    <strong>POSISI PLANET TRANSIT ({event_datetime.strftime('%d %b %Y %H:%M WIB')}):</strong><br>
    {"─" * 68}<br>
    {pos_text.replace(chr(10), "<br>")}<br><br>
    <strong>REKAP GARIS ASPEK GEOMETRI ASTRODOX:</strong><br>
    {"─" * 68}<br>
    {aspek_text.replace(chr(10), "<br>")}
    </div>
    """
    st.markdown(info_html, unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("📋 Papan Prompt 1 — Full Analysis (Makro + Geopolitik + 3 Setup)")
    prompt_full_1 = f"""Cek dan update harga XAUUSD (Gold) secara realtime saat ini terlebih dahulu melalui pencarian/web.

Kamu adalah Senior Quantitative Trader + Macro Analyst + Financial Astrologer spesialis XAUUSD.

Gunakan data Astrodox di bawah ini + pengetahuan teknikal, makro, dan geopolitik terbaru kamu untuk menghasilkan analisis lengkap.

=== DATA ASTRODOX TRANSIT ===
Waktu: {event_datetime.strftime('%d %B %Y %H:%M WIB')}

POSISI PLANET:
{pos_text}

REKAP GARIS ASPEK GEOMETRI:
{aspek_text}

=== INSTRUKSI OUTPUT (WAJIB LENGKAP) ===

1. **Harga Realtime XAUUSD**
   - Tampilkan harga market Gold saat ini hasil pengecekan Anda.

2. **Rekap Data News & Indikator Pendukung**
   - Tentukan sendiri news utama yang relevan (NFP / CPI / FOMC / dll) berdasarkan waktu di atas.
   - Tampilkan data pendukung yang paling relevan (Actual | Forecast | Previous).
   - AI yang menentukan indikator mana yang paling penting.

3. **Analisis Makro**
   - Bias makro saat ini (Bullish USD / Bearish USD / Neutral).
   - Skor dan alasan singkat berdasarkan data pendukung.

4. **Update Geopolitik Terbaru**
   - Isu geopolitik krusial terkini yang mempengaruhi XAUUSD & USD.
   - Dampak gabungan ke USD dan XAUUSD.

5. **Kesimpulan AI untuk Entry**
   - Bias utama: BULLISH / BEARISH / WHIPSAW / NEUTRAL
   - Peringatan Whipsaw (jika ada)
   - Proyeksi Besaran Range (hanya tampilkan ukuran besaran jaraknya saja dalam bentuk Pips / Dollar, BUKAN harga dari sekian sampai sekian):
     - Sweep Range (contoh: 80-150 Pips / $8.0-$15.0)
     - Trend Range (contoh: 200-350 Pips / $20.0-$35.0)
     - Reversal Range (contoh: 80-130 Pips / $8.0-$13.0)

6. **3 Setup Entry Lengkap**
   A. Setup dari AI Macro Engine
      - Zona Entry
      - Stop Loss
      - Take Profit

   B. Setup dari Astrodox Engine
      - Zona Entry (berdasarkan aspek dominan)
      - Stop Loss
      - Take Profit

   C. Setup dari Orderflow / SMC / Liquidity
      - BSL / SSL
      - Supply & Demand / Order Block
      - FVG
      - Entry Zone + SL + TP (dua arah jika whipsaw)

Format jawaban harus rapi, jelas, dan siap dibaca trader.
Fokus pada confluence Astro + Makro + Orderflow.
"""
    st.markdown("Salin prompt bagian 1 di bawah ini lalu paste ke AI (Grok / Claude / GPT / dll):")
    st.code(prompt_full_1, language="text")
    st.caption("Klik ikon copy di pojok kanan atas blok kode di atas untuk menyalin prompt.")
    st.markdown("---")
    st.subheader("📋 Papan Prompt 2 — Simple Astrodox Only")
    prompt_simple = f"""Kamu adalah Senior Quantitative Trader + Financial Astrologer spesialis XAUUSD.

Gunakan data Astrodox di bawah ini + pengetahuan teknikal & makro kamu untuk memberikan proyeksi range pips yang presisi.

=== DATA ASTRODOX TRANSIT ===
Waktu: {event_datetime.strftime('%d %B %Y %H:%M WIB')}

POSISI PLANET:
{pos_text}

REKAP GARIS ASPEK GEOMETRI:
{aspek_text}

=== INSTRUKSI OUTPUT ===
Berikan jawaban dalam format ringkas dan jelas:

1. **Bias Utama** : BULLISH / BEARISH / WHIPSAW / NEUTRAL
2. **Peringatan Whipsaw** : (hanya jika ada risiko whipsaw yang signifikan, jika tidak ada cukup tulis "Tidak signifikan")
3. **Sweep Range** : (hanya tampilkan ukuran besaran jaraknya saja, contoh: 80-150 Pips / $8.0-$15.0)
4. **Trend Range** : (hanya tampilkan ukuran besaran jaraknya saja, contoh: 200-350 Pips / $20.0-$35.0)
5. **Reversal Range** : (hanya tampilkan ukuran besaran jaraknya saja, contoh: 80-130 Pips / $8.0-$13.0)

Catatan:
- Fokus hanya pada confluence Astro + Price Action / SMC structure.
- Tidak perlu memberikan zona entry, SL, atau TP (sudah di-handle di sistem lain).
- Jelaskan singkat alasan bias berdasarkan aspek dominan (Merah/Hijau/Biru/Kuning).
"""
    st.markdown("Salin prompt di bawah ini lalu paste ke AI (Grok / Claude / GPT / dll):")
    st.code(prompt_simple, language="text")
    st.caption("Klik ikon copy di pojok kanan atas blok kode di atas untuk menyalin prompt.")
    st.markdown("---")

elif menu == "📊 Orderbook":
    st.title("📊 Orderbook & Market Data")
    c1, c2, c3, c4 = st.columns([1.6, 1.5, 1.2, 1.2])
    with c1:
        symbol = st.selectbox("Pair", ["XAUT-USDT", "BTC-USDT"], key="pair_select")
    with c2:
        exchange = st.selectbox("Exchange", ["OKX", "Binance", "Bybit", "Gabungan 3 Exchange"], key="exchange_select", index=0)
    with c3:
        aggregation = st.selectbox(
            "Aggregation",
            [0.1, 1, 10, 100, 1000, 10000],
            index=0,
            format_func=lambda x: f"{x}"
        )
    with c4:
        st.write("")
        st.write("")
        auto_refresh = st.checkbox("Auto Refresh")
    sort_order = st.selectbox("Urutan", ["Default (Harga)", "Size Kecil → Besar", "Size Besar → Kecil"], index=0)
    depth = 400
    if "last_symbol" not in st.session_state:
        st.session_state.last_symbol = symbol
    if "last_exchange" not in st.session_state:
        st.session_state.last_exchange = exchange
    force_refresh = False
    if st.session_state.last_symbol != symbol or st.session_state.last_exchange != exchange:
        st.session_state.last_symbol = symbol
        st.session_state.last_exchange = exchange
        force_refresh = True
        if "market_data" in st.session_state:
            del st.session_state.market_data
        if "heatmap_history" in st.session_state:
            st.session_state.heatmap_history = {}
    if st.button("🔄 Refresh Sekarang", type="primary") or auto_refresh or force_refresh or "market_data" not in st.session_state:
        with st.spinner(f"Mengambil data {symbol} - {exchange}..."):
            if exchange == "OKX":
                bids, asks, err = get_okx_orderbook(symbol, limit=depth)
                ticker = get_okx_ticker(symbol)
                trades = get_okx_trades(symbol, 40)
            elif exchange == "Binance":
                bids, asks, err = get_binance_orderbook(symbol, limit=100)
                ticker = get_binance_ticker(symbol)
                trades = get_binance_trades(symbol, 40)
            elif exchange == "Bybit":
                bids, asks, err = get_bybit_orderbook(symbol, limit=50)
                ticker = get_bybit_ticker(symbol)
                trades = get_bybit_trades(symbol, 40)
            else:
                bids, asks, err = get_combined_orderbook(symbol, limit=depth)
                ticker = get_combined_ticker(symbol)
                trades = get_combined_trades(symbol, 40)
            if symbol == "XAUT-USDT":
                ref_price = get_xauusd_price()
            else:
                ref_price = get_btcusd_price()
            st.session_state.market_data = {
                "bids": bids,
                "asks": asks,
                "err": err,
                "ticker": ticker,
                "trades": trades,
                "symbol": symbol,
                "exchange": exchange,
                "ref_price": ref_price
            }
    data = st.session_state.get("market_data", {})
    ticker = data.get("ticker")
    trades = data.get("trades", [])
    bids = data.get("bids")
    asks = data.get("asks")
    err = data.get("err")
    ref_price = data.get("ref_price")
    if ticker:
        if ticker["change_pct"] >= 0:
            sign = "+"
        else:
            sign = ""
        st.markdown(f"### {data.get('symbol')} — {data.get('exchange', exchange)}")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Harga Terakhir", f"{ticker['last']:,.2f}")
        m2.metric("Perubahan 24jam", f"{sign}{ticker['change_pct']:.2f}%")
        m3.metric("High 24jam", f"{ticker['high24h']:,.2f}")
        m4.metric("Low 24jam", f"{ticker['low24h']:,.2f}")
        m5.metric("Volume 24jam", f"{ticker['vol24h']:,.2f}")
        if trades:
            buy_vol = sum(t["size"] for t in trades if t["side"] == "buy")
            sell_vol = sum(t["size"] for t in trades if t["side"] == "sell")
            total = buy_vol + sell_vol or 1
            buy_pct = buy_vol / total * 100
            st.markdown("#### Dominasi Buyer vs Seller")
            st.markdown(f"""
            <div style="display:flex;height:28px;border-radius:8px;overflow:hidden;margin-bottom:6px;">
                <div style="width:{buy_pct}%;background:#00c853;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:13px;">{buy_pct:.1f}%</div>
                <div style="width:{100-buy_pct}%;background:#ff1744;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:13px;">{100-buy_pct:.1f}%</div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:13px;">
                <span style="color:#00c853;">🟢 Buyer: {buy_vol:,.2f}</span>
                <span style="color:#ff1744;">🔴 Seller: {sell_vol:,.2f}</span>
            </div>""", unsafe_allow_html=True)
    st.markdown("---")
    if symbol == "XAUT-USDT":
        st.subheader("📈 XAUUSD (OANDA) vs XAUT")
        col1, col2 = st.columns([1.4, 1])
        with col1:
            tv_code = """
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js" async>
              {
              "symbols": [["OANDA:XAUUSD|1D"]],
              "chartOnly": false, "width": "100%", "height": 320, "locale": "en", "colorTheme": "dark", "autosize": true,
              "showVolume": false, "showMA": false, "hideDateRanges": false, "hideMarketStatus": false, "hideSymbolLogo": false,
              "scalePosition": "right", "scaleMode": "Normal", "fontFamily": "-apple-system, BlinkMacSystemFont, Trebuchet MS, Roboto, sans-serif",
              "fontSize": "10", "noTimeScale": false, "valuesTracking": "1", "changeMode": "price-and-percent", "chartType": "area",
              "lineWidth": 2, "lineType": 0, "dateRanges": ["1d|1","1m|30","3m|60","12m|1D","60m|1W","all|1M"]
            }
              </script>
            </div>
            """
            components.html(tv_code, height=340)
        with col2:
            st.markdown("#### Perhitungan Selisih XAUT")
            if ticker and ref_price:
                xaut = ticker["last"]
                selisih = xaut - ref_price
                st.metric(f"XAUT ({exchange})", f"{xaut:,.2f}")
                st.metric("XAUUSD (approx)", f"{ref_price:,.2f}")
                if selisih > 0:
                    delta_label = "Premium"
                else:
                    delta_label = "Discount"
                st.metric("Selisih", f"{selisih:+.2f}", delta=delta_label)
    else:
        st.subheader("₿ BTCUSD (OANDA) vs BTC-USDT")
        col1, col2 = st.columns([1.4, 1])
        with col1:
            tv_code = """
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js" async>
              {
              "symbols": [["OANDA:BTCUSD|1D"]],
              "chartOnly": false, "width": "100%", "height": 320, "locale": "en", "colorTheme": "dark", "autosize": true,
              "showVolume": false, "showMA": false, "hideDateRanges": false, "hideMarketStatus": false, "hideSymbolLogo": false,
              "scalePosition": "right", "scaleMode": "Normal", "fontFamily": "-apple-system, BlinkMacSystemFont, Trebuchet MS, Roboto, sans-serif",
              "fontSize": "10", "noTimeScale": false, "valuesTracking": "1", "changeMode": "price-and-percent", "chartType": "area",
              "lineWidth": 2, "lineType": 0, "dateRanges": ["1d|1","1m|30","3m|60","12m|1D","60m|1W","all|1M"]
            }
              </script>
            </div>
            """
            components.html(tv_code, height=340)
        with col2:
            st.markdown("#### Perhitungan Selisih BTC")
            if ticker and ref_price:
                btc = ticker["last"]
                selisih = btc - ref_price
                st.metric(f"BTC-USDT ({exchange})", f"{btc:,.2f}")
                st.metric("BTCUSD (approx)", f"{ref_price:,.2f}")
                if selisih > 0:
                    delta_label_btc = "Premium"
                else:
                    delta_label_btc = "Discount"
                st.metric("Selisih", f"{selisih:+.2f}", delta=delta_label_btc)
    st.markdown("---")
    st.subheader(f"Orderbook — {exchange}")
    if st.session_state.get("combined_warning"):
        st.warning(f"⚠️ Partial: {st.session_state.get('combined_warning')} — Data ditampilkan dari exchange yang berhasil.")
    if err and not bids:
        st.error(err)
    elif bids and asks:
        show_orderbook_visual(bids, asks, aggregation=aggregation, sort_order=sort_order)
        st.markdown("---")
        if ticker:
            last_for_heatmap = ticker["last"]
        else:
            last_for_heatmap = None
        render_rolling_heatmap(bids, asks, f"{symbol}_{exchange}", ref_price=ref_price, last_price=last_for_heatmap)
    elif err:
        st.error(err)
    else:
        st.info("Sedang memuat orderbook...")
    st.markdown("---")
    st.subheader("Recent Trades")
    if trades:
        df = pd.DataFrame(trades)
        df["side"] = df["side"].map({"buy": "🟢 Buy", "sell": "🔴 Sell"})
        df = df.rename(columns={"time": "Waktu", "price": "Harga", "size": "Jumlah", "side": "Arah"})
        st.dataframe(df, use_container_width=True, height=350, hide_index=True)
    else:
        st.info("Belum ada data trades")
    if auto_refresh:
        time.sleep(3)
        st.rerun()

elif menu == "🧮 Kalkulator":
    st.title("🧮 Kalkulator PnL & Converter")
    st.caption("Kalkulator khusus untuk teknik War News / Straddle Hedging XAUUSD | Kurs bisa diubah sendiri")
    st.markdown("---")
    st.subheader("💱 Kurs Saat Ini")
    kurs_idr = st.number_input(
        "1 USD = ... IDR",
        min_value=1000.0,
        max_value=100000.0,
        value=17000.0,
        step=100.0,
        format="%.0f",
        help="Masukkan kurs 1 USD ke Rupiah. Contoh: 17000"
    )
    kurs_usc_to_idr = kurs_idr / 100.0
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("1 USD", f"Rp {kurs_idr:,.0f}")
    with c2:
        st.metric("1 USC", f"Rp {kurs_usc_to_idr:,.2f}")
    with c3:
        st.metric("100 USC", f"Rp {kurs_idr:,.0f}")
    st.markdown("---")
    st.subheader("📈 Kalkulator PnL XAUUSD")
    account_type = st.radio(
        "Jenis Akun",
        ["Standard", "Cent"],
        horizontal=True,
        help="Standard: 1 lot = $1 per pip | Cent: 1 lot Cent = $0.01 per pip (1/100 dari Standard)"
    )
    if account_type == "Standard":
        st.caption("Asumsi Standard: **1 pip = $0.01 untuk 0.01 lot** → **1 pip = $1 per 1.00 lot**")
    else:
        st.caption("Asumsi Cent: **1 pip = $0.0001 untuk 0.01 lot Cent** → **1 pip = $0.01 per 1.00 lot Cent**")
    col_lot, col_sl, col_tp = st.columns(3)
    with col_lot:
        lot = st.number_input("Lot Size", min_value=0.01, max_value=100.0, value=0.01, step=0.01, format="%.2f")
    with col_sl:
        sl_pips = st.number_input("SL (Pips)", min_value=0.0, max_value=10000.0, value=1500.0, step=1.0, format="%.1f")
    with col_tp:
        tp_pips = st.number_input("TP (Pips)", min_value=0.0, max_value=10000.0, value=4000.0, step=1.0, format="%.1f")
    if account_type == "Standard":
        pip_value_usd = lot * 1.0
    else:
        pip_value_usd = lot * 0.01
    pnl_sl_usd = -sl_pips * pip_value_usd
    pnl_tp_usd = tp_pips * pip_value_usd
    pnl_sl_usc = pnl_sl_usd * 100
    pnl_tp_usc = pnl_tp_usd * 100
    pnl_sl_idr = pnl_sl_usd * kurs_idr
    pnl_tp_idr = pnl_tp_usd * kurs_idr
    st.markdown("#### Hasil Perhitungan PnL")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown("**🔴 Stop Loss**")
        st.metric("USD", f"{pnl_sl_usd:,.2f}")
        st.metric("USC", f"{pnl_sl_usc:,.1f}")
        st.metric("IDR", f"Rp {pnl_sl_idr:,.0f}")
    with r2:
        st.markdown("**🟢 Take Profit**")
        st.metric("USD", f"+{pnl_tp_usd:,.2f}")
        st.metric("USC", f"+{pnl_tp_usc:,.1f}")
        st.metric("IDR", f"Rp {pnl_tp_idr:,.0f}")
    with r3:
        st.markdown("**📊 Ringkasan**")
        st.metric("Pip Value", f"${pip_value_usd:,.4f}")
        if pnl_sl_usd != 0:
            risk_reward = abs(pnl_tp_usd / pnl_sl_usd)
        else:
            risk_reward = 0
        st.metric("Risk : Reward", f"1 : {risk_reward:.2f}")
        st.caption(f"{account_type} | Lot {lot} | SL {sl_pips} | TP {tp_pips}")
    st.markdown(f"""
    <div class="info-box">
    <strong>RINGKASAN CEPAT:</strong><br>
    Akun: <b>{account_type}</b> &nbsp;|&nbsp; Lot: <b>{lot}</b> &nbsp;|&nbsp; SL: <b>{sl_pips} pips</b> &nbsp;|&nbsp; TP: <b>{tp_pips} pips</b><br>
    ─────────────────────────────────────────────<br>
    - SL  → {pnl_sl_usd:,.2f} USD  =  {pnl_sl_usc:,.1f} USC  =  Rp {pnl_sl_idr:,.0f}<br>
    - TP  → +{pnl_tp_usd:,.2f} USD  =  +{pnl_tp_usc:,.1f} USC  =  Rp {pnl_tp_idr:,.0f}<br>
    - Risk:Reward ≈ 1 : {risk_reward:.2f}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🔄 Currency Converter (IDR • USD • USC)")
    st.caption(f"Menggunakan kurs yang kamu input di atas (1 USD = Rp {kurs_idr:,.0f})")
    tab1, tab2, tab3 = st.tabs(["💵 USD → IDR / USC", "🇮🇩 IDR → USD / USC", "🪙 USC → USD / IDR"])
    with tab1:
        usd_in = st.number_input("Masukkan jumlah USD", min_value=0.0, value=100.0, step=1.0, format="%.2f", key="conv_usd")
        idr_out = usd_in * kurs_idr
        usc_out = usd_in * 100
        c1, c2 = st.columns(2)
        with c1:
            st.success(f"**{usd_in:,.2f} USD** = **Rp {idr_out:,.0f}**")
        with c2:
            st.info(f"**{usd_in:,.2f} USD** = **{usc_out:,.1f} USC**")
    with tab2:
        idr_in = st.number_input("Masukkan jumlah IDR (Rupiah)", min_value=0.0, value=1700000.0, step=1000.0, format="%.0f", key="conv_idr")
        if kurs_idr > 0:
            usd_out = idr_in / kurs_idr
        else:
            usd_out = 0
        usc_out2 = usd_out * 100
        c1, c2 = st.columns(2)
        with c1:
            st.success(f"**Rp {idr_in:,.0f}** = **{usd_out:,.2f} USD**")
        with c2:
            st.info(f"**Rp {idr_in:,.0f}** = **{usc_out2:,.1f} USC**")
    with tab3:
        usc_in = st.number_input("Masukkan jumlah USC", min_value=0.0, value=1000.0, step=10.0, format="%.1f", key="conv_usc")
        usd_out3 = usc_in / 100
        idr_out3 = usd_out3 * kurs_idr
        c1, c2 = st.columns(2)
        with c1:
            st.success(f"**{usc_in:,.1f} USC** = **{usd_out3:,.2f} USD**")
        with c2:
            st.info(f"**{usc_in:,.1f} USC** = **Rp {idr_out3:,.0f}**")
    st.markdown("---")
    st.caption("Catatan: Standard = 1 lot = $1/pip | Cent = 1 lot = $0.01/pip. Hasil bisa sedikit berbeda tergantung broker (spread, komisi, dll).")
