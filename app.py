import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import requests
import pandas as pd
import time

st.set_page_config(
    page_title="ABEL FX Tools",
    page_icon="⚡",
    layout="wide"
)

# ================= CSS =================
st.markdown("""
<style>
    /* ========== SIDEBAR ========== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1c 0%, #111827 50%, #0f172a 100%) !important;
        border-right: 1px solid #1e293b !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }
    
    /* Radio button styling */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 6px;
    }
    
    section[data-testid="stSidebar"] label {
        background: #1e293b !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        margin-bottom: 6px !important;
        border: 1px solid #334155 !important;
        transition: all 0.2s ease;
    }
    
    section[data-testid="stSidebar"] label:hover {
        background: #334155 !important;
        border-color: #00d4ff !important;
    }
    
    /* Selected radio */
    section[data-testid="stSidebar"] label[data-baseweb="radio"] {
        background: #0ea5e9 !important;
    }

    /* Title di sidebar */
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
        color: #64748b;
        font-size: 12px;
        margin-bottom: 20px;
    }

    /* ========== LAINNYA ========== */
    .welcome-box {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 55px 30px;
        text-align: center;
        margin-top: 40px;
    }
    
    .info-box {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        color: #e2e8f0;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown('<div class="sidebar-brand">⚡ ABEL FX</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-sub">Trading Tools</div>', unsafe_allow_html=True)

menu = st.sidebar.radio(
    "menu",
    ["🏠  Menu Utama", "🔮  Astrodox", "📊  Orderbook"],
    index=0,
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align:center; color:#475569; font-size:12px; padding-top:10px;">
    ABEL FX Tools<br>
    <span style="color:#334155;">v1.0</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# ASTRODOX ENGINE (sama seperti sebelumnya)
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

    fig = plt.figure(figsize=(10.5, 10.5), facecolor='#0e1117')
    ax = fig.add_subplot(111, polar=True, facecolor='#0e1117')
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
    plt.savefig(img_buf, format='png', dpi=220, bbox_inches='tight', facecolor='#0e1117')
    img_buf.seek(0)
    return fig, img_buf, aspect_counts, planet_positions


# ==========================================
# ORDERBOOK FUNCTIONS
# ==========================================
def get_okx_orderbook(symbol="XAUT-USDT", limit=50):
    try:
        url = f"https://www.okx.com/api/v5/market/books?instId={symbol}&sz={limit}"
        r = requests.get(url, timeout=8)
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
    except: return None

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
    except: return []

def add_cumulative(orders):
    result, cumulative = [], 0.0
    for price, size in orders:
        cumulative += size
        result.append({"price": price, "size": size, "cumulative": cumulative})
    return result

def show_orderbook_visual(bids, asks, min_cum=0.0, sort_order="Default (Harga)"):
    if not bids or not asks:
        st.warning("Data orderbook kosong")
        return
    bids_data = add_cumulative(bids)
    asks_data = add_cumulative(asks)
    if min_cum > 0:
        bids_data = [x for x in bids_data if x["cumulative"] >= min_cum]
        asks_data = [x for x in asks_data if x["cumulative"] >= min_cum]
    if not bids_data or not asks_data:
        st.warning(f"Tidak ada level dengan cumulative ≥ {min_cum}")
        return
    if sort_order == "Size Kecil → Besar":
        bids_data = sorted(bids_data, key=lambda x: x["cumulative"])
        asks_data = sorted(asks_data, key=lambda x: x["cumulative"])
    elif sort_order == "Size Besar → Kecil":
        bids_data = sorted(bids_data, key=lambda x: x["cumulative"], reverse=True)
        asks_data = sorted(asks_data, key=lambda x: x["cumulative"], reverse=True)

    max_cum = max(max([x["cumulative"] for x in bids_data[:30]], default=1),
                  max([x["cumulative"] for x in asks_data[:30]], default=1))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🟢 Beli (Bids)")
        for item in bids_data[:25]:
            pct = min(item["cumulative"] / max_cum, 1.0)
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                background:linear-gradient(90deg,#0d3b2e {pct*100}%,transparent 0%);
                padding:6px 10px;margin:3px 0;border-radius:6px;">
                <span style="color:#00ff9d;font-weight:bold;">{item['cumulative']:,.1f}</span>
                <span style="color:white;">{item['price']:,.2f}</span></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("### 🔴 Jual (Asks)")
        for item in asks_data[:25]:
            pct = min(item["cumulative"] / max_cum, 1.0)
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                background:linear-gradient(270deg,#3b0d0d {pct*100}%,transparent 0%);
                padding:6px 10px;margin:3px 0;border-radius:6px;">
                <span style="color:white;">{item['price']:,.2f}</span>
                <span style="color:#ff4d4d;font-weight:bold;">{item['cumulative']:,.1f}</span></div>""", unsafe_allow_html=True)


# ==========================================
# HALAMAN
# ==========================================
if menu == "🏠  Menu Utama":
    st.markdown("""
    <div class="welcome-box">
        <h1 style="color:#00d4ff;font-size:42px;margin-bottom:12px;">Welcome to ABEL Tools</h1>
        <p style="color:#94a3b8;font-size:18px;">Tools trading berbasis Astrodox & Market Data</p>
        <p style="color:#64748b;font-size:15px;margin-top:12px;">Pilih menu di sidebar kiri untuk mulai</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1: st.info("**🔮 Astrodox**\n\nRoda transit planet + rekap aspek geometri untuk analisa XAUUSD.")
    with c2: st.info("**📊 Orderbook**\n\nOrderbook realtime, ticker, volume, recent trades & dominasi buyer/seller.")
    st.caption("ABEL FX Tools • Powered by OKX Public API")

elif menu == "🔮  Astrodox":
    st.title("🔮 Astrodox Wheel")
    st.caption("Roda Transit Planet + Rekap Aspek Geometri")
    st.markdown("---")
    st.subheader("📅 Atur Waktu Transit")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: tanggal = st.number_input("Tanggal",1,31,12)
    with c2:
        bulan_list = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
        bulan_nama = st.selectbox("Bulan", bulan_list, index=7)
        bulan = bulan_list.index(bulan_nama)+1
    with c3: tahun = st.number_input("Tahun",2000,2100,2026)
    with c4: jam = st.number_input("Jam",0,23,19)
    with c5: menit = st.number_input("Menit",0,59,30)

    try:
        event_datetime = datetime(int(tahun),int(bulan),int(tanggal),int(jam),int(menit))
    except:
        st.error("Tanggal tidak valid")
        st.stop()

    st.markdown(f"**Waktu:** `{event_datetime.strftime('%d %B %Y %H:%M WIB')}`")
    st.markdown("---")

    fig, img_buf, aspect_counts, planet_positions = generate_astrodox_wheel_only(event_datetime)
    st.subheader("🔮 Roda Astrodox Transit")
    st.pyplot(fig, use_container_width=True)
    st.download_button("📥 Download Roda", img_buf, f"Astrodox_{event_datetime.strftime('%Y%m%d_%H%M')}.png", "image/png")

    st.markdown("---")
    st.subheader("📋 Dashboard Info")
    pos_lines = []
    pos_items = list(planet_positions.items())
    for i in range(0, len(pos_items), 2):
        p1,v1 = pos_items[i]
        if i+1 < len(pos_items):
            p2,v2 = pos_items[i+1]
            pos_lines.append(f"• {p1:<12}: {v1:<16}  |  • {p2:<12}: {v2}")
        else:
            pos_lines.append(f"• {p1:<12}: {v1}")
    pos_text = "\n".join(pos_lines)
    aspek_text = f"""• MERAH  (Square/Opp) : {aspect_counts['merah']} → Volatilitas Tinggi
• HIJAU  (Trine)      : {aspect_counts['hijau']} → Expansion
• BIRU   (Sextile)    : {aspect_counts['biru']} → Retest
• KUNING (Conjunction): {aspect_counts['kuning']} → Turning Point"""

    st.markdown(f"""<div class="info-box">
    <strong>POSISI PLANET ({event_datetime.strftime('%d %b %Y %H:%M WIB')})</strong><br>{"─"*60}<br>
    {pos_text.replace(chr(10),"<br>")}<br><br>
    <strong>REKAP ASPEK</strong><br>{"─"*60}<br>
    {aspek_text.replace(chr(10),"<br>")}</div>""", unsafe_allow_html=True)

elif menu == "📊  Orderbook":
    st.title("📊 Orderbook & Market Data")
    c1,c2,c3,c4 = st.columns([2,2,2,1])
    with c1: symbol = st.selectbox("Pair", ["XAUT-USDT","BTC-USDT"])
    with c2: min_cum = st.number_input("Min Cumulative", 0.0, value=0.0, step=1.0)
    with c3: sort_order = st.selectbox("Urutan", ["Default (Harga)","Size Kecil → Besar","Size Besar → Kecil"])
    with c4:
        st.write(""); st.write("")
        auto_refresh = st.checkbox("Auto Refresh")

    limit = st.selectbox("Jumlah Level", [20,30,50,100], index=2)

    if st.button("🔄 Refresh Sekarang", type="primary") or auto_refresh or "market_data" not in st.session_state:
        with st.spinner(f"Mengambil data {symbol}..."):
            bids, asks, err = get_okx_orderbook(symbol, limit)
            ticker = get_okx_ticker(symbol)
            trades = get_okx_trades(symbol, 40)
            st.session_state.market_data = {"bids":bids,"asks":asks,"err":err,"ticker":ticker,"trades":trades,"symbol":symbol}

    data = st.session_state.market_data
    ticker, trades, bids, asks, err = data.get("ticker"), data.get("trades",[]), data.get("bids"), data.get("asks"), data.get("err")

    if ticker:
        sign = "+" if ticker["change_pct"] >= 0 else ""
        st.markdown(f"### {data.get('symbol')}")
        m1,m2,m3,m4,m5 = st.columns(5)
        m1.metric("Harga Terakhir", f"{ticker['last']:,.2f}")
        m2.metric("Perubahan 24jam", f"{sign}{ticker['change_pct']:.2f}%")
        m3.metric("High 24jam", f"{ticker['high24h']:,.2f}")
        m4.metric("Low 24jam", f"{ticker['low24h']:,.2f}")
        m5.metric("Volume 24jam", f"{ticker['vol24h']:,.2f}")

        if trades:
            buy_vol = sum(t["size"] for t in trades if t["side"]=="buy")
            sell_vol = sum(t["size"] for t in trades if t["side"]=="sell")
            total = buy_vol + sell_vol or 1
            buy_pct = buy_vol/total*100
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
    st.subheader("Orderbook")
    if err: st.error(err)
    else: show_orderbook_visual(bids, asks, min_cum, sort_order)

    st.markdown("---")
    st.subheader("Recent Trades")
    if trades:
        df = pd.DataFrame(trades)
        df["side"] = df["side"].map({"buy":"🟢 Buy","sell":"🔴 Sell"})
        df = df.rename(columns={"time":"Waktu","price":"Harga","size":"Jumlah","side":"Arah"})
        st.dataframe(df, use_container_width=True, height=350, hide_index=True)
    else:
        st.info("Belum ada data trades")

    if auto_refresh:
        time.sleep(3)
        st.rerun()
