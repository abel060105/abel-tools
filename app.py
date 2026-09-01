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
            
            css_wallpaper = """
            <style>
                .stApp {
                    background: transparent !important;
                }
                #bg-video {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    z-index: -999;
                    object-fit: cover;
                }
                @media only screen and (max-width: 768px) {
                    #bg-video {
                        object-fit: cover;
                    }
                }
                section[data-testid="stSidebar"] {
                    background: rgba(10, 15, 28, 0.85) !important;
                }
                .welcome-box, .info-box {
                    background: rgba(11, 16, 30, 0.92) !important;
                    backdrop-filter: blur(12px);
                    border: 1px solid rgba(0, 212, 255, 0.3) !important;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
                }
            </style>

            <video autoplay muted loop playsinline webkit-playsinline id="bg-video">
                <source src="data:video/mp4;base64,REPLACE_BASE64" type="video/mp4">
            </video>

            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var video = document.getElementById('bg-video');
                    if (video) {
                        var playPromise = video.play();
                        if (playPromise !== undefined) {
                            playPromise.catch(function(error) {
                                document.body.addEventListener('touchstart', function() {
                                    video.play();
                                }, { once: true });
                                document.body.addEventListener('click', function() {
                                    video.play();
                                }, { once: true });
                            });
                        }
                    }
                });
            </script>
            """.replace("REPLACE_BASE64", encoded)
            
            st.markdown(css_wallpaper, unsafe_allow_html=True)
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
    ABEL FX Tools<br>
    <span style="color:#64748b;">v3.3 (Bookmap Heat Axis Highlight)</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# ASTRODOX ENGINE
# ==========================================
ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ZODIAC_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def compute_planetary_positions(dt_utc):
    year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
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
        ax.bar(x=(theta_start + theta_end)/2, height=0.25, width=np.radians(30),
               bottom=0.75, color=colors[i], alpha=0.6, edgecolor='#555555')
        ax.text((theta_start + theta_end)/2, 0.88, ZODIAC_SYMBOLS[i],
                color='white', fontsize=16, ha='center', va='center', fontweight='bold')
    for name, deg in planet_degrees.items():
        rad = np.radians(deg)
        ax.plot(rad, 0.70, marker='o', color='#00ffff', markersize=7)
        ax.text(rad, 0.60, name.split()[-1], color='white', fontsize=13, ha='center', va='center', fontweight='bold')
    aspect_counts = {"merah": 0, "hijau": 0, "biru": 0, "kuning": 0}
    planets_keys = list(planet_degrees.keys())
    deg_list = list(planet_degrees.values())
    for i in range(len(planets_keys)):
        for j in range(i+1, len(planets_keys)):
            d1, d2 = deg_list[i], deg_list[j]
            diff = abs(d1 - d2) % 360
            if diff > 180: diff = 360 - diff
            rad1, rad2 = np.radians(d1), np.radians(d2)
            if abs(diff-90) <= 7 or abs(diff-180) <= 7:
                ax.plot([rad1, rad2], [0.70, 0.70], color='#ff3333', alpha=0.85, linewidth=1.6)
                aspect_counts["merah"] += 1
            elif abs(diff-120) <= 7:
                ax.plot([rad1, rad2], [0.70, 0.70], color='#00ff66', alpha=0.85, linewidth=1.6)
                aspect_counts["hijau"] += 1
            elif abs(diff-60) <= 6:
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
# MARKET DATA
# ==========================================
def get_okx_orderbook(symbol="XAUT-USDT", limit=400):
    try:
        url = f"https://www.okx.com/api/v5/market/books?instId={symbol}&sz={limit}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("code") != "0":
            return None, None, data.get("msg", "Error")
        book = data["data"][0]
        bids = [[float(p), float(q)] for p, q, *_ in book["bids"]]
        asks = [[float(p), float(q)] for p, q, *_ in book["asks"]]
        return bids, asks, None
    except Exception as e:
        return None, None, str(e)

def get_okx_ticker(symbol="XAUT-USDT"):
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("code") != "0": return None
        t = data["data"][0]
        last = float(t["last"])
        open24h = float(t["open24h"])
        return {
            "last": last,
            "high24h": float(t["high24h"]),
            "low24h": float(t["low24h"]),
            "vol24h": float(t["vol24h"]),
            "change_pct": ((last - open24h) / open24h * 100) if open24h else 0
        }
    except:
        return None

def get_okx_trades(symbol="XAUT-USDT", limit=40):
    try:
        url = f"https://www.okx.com/api/v5/market/trades?instId={symbol}&limit={limit}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("code") != "0": return []
        return [{
            "time": datetime.fromtimestamp(int(t["ts"])/1000).strftime("%H:%M:%S"),
            "price": float(t["px"]),
            "size": float(t["sz"]),
            "side": t["side"]
        } for t in data["data"]]
    except:
        return []

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
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=6)
        data = r.json()
        if "price" in data:
            return float(data["price"])
    except:
        pass
    return None

def aggregate_orders(orders, aggregation: float, side: str = "bid"):
    if aggregation <= 0.1:
        return [[round(p, 1), s] for p, s in orders]

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

    bids_data = [{"price": p, "size": s, "notional": s * p} for p, s in bids]
    asks_data = [{"price": p, "size": s, "notional": s * p} for p, s in asks]

    if sort_order == "Size Kecil → Besar":
        bids_data = sorted(bids_data, key=lambda x: x["size"])
        asks_data = sorted(asks_data, key=lambda x: x["size"])
    elif sort_order == "Size Besar → Kecil":
        bids_data = sorted(bids_data, key=lambda x: x["size"], reverse=True)
        asks_data = sorted(asks_data, key=lambda x: x["size"], reverse=True)

    max_size = max(
        max([x["size"] for x in bids_data[:40]], default=1),
        max([x["size"] for x in asks_data[:40]], default=1)
    )
    max_display = 30 if aggregation >= 10 else 25

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

# ==========================================
# ROLLING HEATMAP COMPONENT (BOOKMAP STYLE + HEAT > 15 HIGHLIGHT ON AXIS)
# ==========================================
def render_rolling_heatmap(bids, asks, symbol):
    st.markdown("### 🔥 Orderbook Liquidity Heatmap (Bookmap Theme)")
    st.caption("Visualisasi konsentrasi likuiditas real-time. Harga di sumbu kanan dengan heat > 15 diberi kotak penanda dengan warna sesuai tingkat heat-nya.")

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

    active_price_map = {p: history["price_map"][p] for p in all_prices if p in history["price_map"] and len(history["price_map"][p]) == len(history["times"])}

    if not active_price_map:
        st.info("Mengumpulkan riwayat snapshot...")
        return

    y_prices = list(active_price_map.keys())
    z_matrix = [active_price_map[p] for p in y_prices]
    x_times = history["times"]

    # Menghitung skala heat (0-25) untuk setiap harga
    flat_z = [val for row in z_matrix for val in row]
    max_z_val = max(flat_z) if flat_z else 1.0

    high_heat_prices = []
    for i, p in enumerate(y_prices):
        avg_p_val = np.mean(z_matrix[i]) if z_matrix[i] else 0
        heat_score = min(25.0, (avg_p_val / (max_z_val if max_z_val > 0 else 1.0)) * 25.0)
        if heat_score > 15.0:
            high_heat_prices.append({"price": p, "heat": heat_score})

    # Palet warna Bookmap
    bookmap_colorscale = [
        [0.0, '#040b18'],   # Biru sangat gelap
        [0.2, '#0d2347'],   # Biru gelap
        [0.5, '#1d547f'],   # Biru sedang
        [0.75, '#e06b1e'],  # Oranye
        [0.9, '#f5bc18'],   # Kuning terang
        [1.0, '#ffffff']    # Putih menyala
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

    # Menambahkan penanda kotak (shapes) dan keterangan teks pada sumbu harga kanan untuk heat > 15
    annotations = []
    shapes = []
    
    for item in high_heat_prices:
        p_val = item['price']
        h_val = item['heat']
        
        # Menentukan warna kotak highlight berdasarkan besaran heat score
        if h_val >= 22.0:
            box_color = "#ffffff"  # Putih menyala untuk heat sangat tinggi
        elif h_val >= 19.0:
            box_color = "#f5bc18"  # Kuning terang
        else:
            box_color = "#e06b1e"  # Oranye

        # Kotak highlight di area sumbu harga (y-axis kanan)
        shapes.append(dict(
            type="rect",
            xref="paper", yref="y",
            x0=1.0, x1=1.06,  # Sedikit di luar area plot sebelah kanan
            y0=p_val - (max(y_prices)*0.0005 if y_prices else 0.5), 
            y1=p_val + (max(y_prices)*0.0005 if y_prices else 0.5),
            fillcolor=box_color,
            opacity=0.85,
            line=dict(color=box_color, width=1)
        ))

        # Teks angka skor heat di sebelah kanan kotak harga
        annotations.append(dict(
            xref="paper", yref="y",
            x=1.075,
            y=p_val,
            text=f"<b>{h_val:.1f}</b>",
            showarrow=False,
            font=dict(size=10, color=box_color),
            xanchor="left",
            yanchor="middle"
        ))

    fig_heat.update_layout(
        title=dict(text=f"Liquidity Heatmap — {symbol}", font=dict(color="#ffffff")),
        xaxis_title="",
        yaxis_title="Harga",
        height=540,
        margin=dict(l=80, r=90, t=30, b=10), # Margin kanan diperlebar untuk ruang highlight axis
        paper_bgcolor='#070a0f',
        plot_bgcolor='#070a0f',
        font=dict(color='#94a3b8'),
        yaxis=dict(side="right", gridcolor="#111827", zeroline=False),
        xaxis=dict(gridcolor="#111827"),
        shapes=shapes,
        annotations=annotations
    )
    
    st.plotly_chart(fig_heat, use_container_width=True)

    # Panel Bawah: Detail Zona Likuiditas Tinggi (Heat > 15) dengan Warna Sinkron
    st.markdown("#### ⚡ Zona Likuiditas Tinggi (Heat Score > 15)")
    if high_heat_prices:
        cols = st.columns(min(3, len(high_heat_prices)))
        for idx, item in enumerate(sorted(high_heat_prices, key=lambda x: x["price"], reverse=True)):
            h_val = item['heat']
            # Sinkronisasi warna border dan badge panel bawah
            if h_val >= 22.0:
                b_color = "#ffffff"
                badge_bg = "#ffffff"
                badge_txt = "#000000"
            elif h_val >= 19.0:
                b_color = "#f5bc18"
                badge_bg = "#f5bc18"
                badge_txt = "#000000"
            else:
                b_color = "#e06b1e"
                badge_bg = "#e06b1e"
                badge_txt = "#ffffff"

            with cols[idx % len(cols)]:
                st.markdown(f"""
                <div style="border: 2px solid {b_color}; background: rgba(224, 107, 30, 0.08); 
                     border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex; 
                     justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #94a3b8; font-size: 11px; display: block;">HARGA HEAT</span>
                        <span style="color: #ffffff; font-weight: bold; font-size: 16px;">{item['price']:,.1f}</span>
                    </div>
                    <div style="background: {badge_bg}; color: {badge_txt}; font-weight: 800; font-size: 13px; 
                         padding: 4px 8px; border-radius: 6px;">
                        Heat: {h_val:.1f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
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
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: tanggal = st.number_input("Tanggal", 1, 31, 12)
    with c2:
        bulan_list = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
        bulan_nama = st.selectbox("Bulan", bulan_list, index=7)
        bulan = bulan_list.index(bulan_nama) + 1
    with c3: tahun = st.number_input("Tahun", 2000, 2100, 2026)
    with c4: jam = st.number_input("Jam", 0, 23, 19)
    with c5: menit = st.number_input("Menit", 0, 59, 30)
    
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
        if i+1 < len(pos_items):
            p2, v2 = pos_items[i+1]
            pos_lines.append(f"• {p1:<12}: {v1:<16}  |  • {p2:<12}: {v2}")
        else:
            pos_lines.append(f"• {p1:<12}: {v1}")
            
    pos_text = "\n".join(pos_lines)
    aspek_text = f"""• MERAH  (Square 90° / Opp 180°) : {aspect_counts['merah']} Garis  → Volatilitas Tinggi
• HIJAU  (Trine 120°)            : {aspect_counts['hijau']} Garis  → Expansion Trend
• BIRU   (Sextile 60°)           : {aspect_counts['biru']} Garis  → Retest Zone
• KUNING (Conjunction 0°)        : {aspect_counts['kuning']} Garis  → Turning Point"""

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

    # ========== PAPAN PROMPT 1 ==========
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
     • Sweep Range (contoh: 80-150 Pips / $8.0-$15.0)
     • Trend Range (contoh: 200-350 Pips / $20.0-$35.0)
     • Reversal Range (contoh: 80-130 Pips / $8.0-$13.0)

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

    # ========== PAPAN PROMPT 2 ==========
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
    
    c1, c2, c3 = st.columns([2, 2, 1.5])
    with c1:
        symbol = st.selectbox("Pair", ["XAUT-USDT", "BTC-USDT"], key="pair_select")
    with c2:
        aggregation = st.selectbox(
            "Aggregation",
            [0.1, 1, 10, 100, 1000, 10000],
            index=0,
            format_func=lambda x: f"{x}"
        )
    with c3:
        st.write("")
        st.write("")
        auto_refresh = st.checkbox("Auto Refresh")

    sort_order = st.selectbox("Urutan", ["Default (Harga)", "Size Kecil → Besar", "Size Besar → Kecil"], index=0)

    depth = 400

    if "last_symbol" not in st.session_state:
        st.session_state.last_symbol = symbol

    force_refresh = False
    if st.session_state.last_symbol != symbol:
        st.session_state.last_symbol = symbol
        force_refresh = True
        if "market_data" in st.session_state:
            del st.session_state.market_data

    if st.button("🔄 Refresh Sekarang", type="primary") or auto_refresh or force_refresh or "market_data" not in st.session_state:
        with st.spinner(f"Mengambil data {symbol}..."):
            bids, asks, err = get_okx_orderbook(symbol, limit=depth)
            ticker = get_okx_ticker(symbol)
            trades = get_okx_trades(symbol, 40)
            
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
        sign = "+" if ticker["change_pct"] >= 0 else ""
        st.markdown(f"### {data.get('symbol')}")
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
                st.metric("XAUT (OKX)", f"{xaut:,.2f}")
                st.metric("XAUUSD (approx)", f"{ref_price:,.2f}")
                st.metric("Selisih", f"{selisih:+.2f}", delta="Premium" if selisih > 0 else "Discount")

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
                st.metric("BTC-USDT (OKX)", f"{btc:,.2f}")
                st.metric("BTCUSD (approx)", f"{ref_price:,.2f}")
                st.metric("Selisih", f"{selisih:+.2f}", delta="Premium" if selisih > 0 else "Discount")

    st.markdown("---")
    st.subheader("Orderbook")
    
    if err:
        st.error(err)
    elif bids and asks:
        show_orderbook_visual(bids, asks, aggregation=aggregation, sort_order=sort_order)
        st.markdown("---")
        render_rolling_heatmap(bids, asks, symbol)
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
