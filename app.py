import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import requests
import pandas as pd
import time

st.set_page_config(
    page_title="ABEL FX - Astrodox Wheel",
    page_icon="🔮",
    layout="wide"
)

st.markdown("""
<style>
    .info-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px 22px;
        margin-top: 10px;
        margin-bottom: 20px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        color: #e0e0e0;
        line-height: 1.55;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("ABEL FX")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Pilih Halaman",
    ["🔮 Astrodox", "📊 Orderbook"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("ABEL FX Tools")

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
        ax.bar(x=(theta_start + theta_end) / 2, height=0.25, width=np.radians(30),
               bottom=0.75, color=colors[i], alpha=0.6, edgecolor='#555555')
        ax.text((theta_start + theta_end) / 2, 0.88, ZODIAC_SYMBOLS[i],
                color='white', fontsize=16, ha='center', va='center', fontweight='bold')

    for name, deg in planet_degrees.items():
        rad = np.radians(deg)
        ax.plot(rad, 0.70, marker='o', color='#00ffff', markersize=7)
        short_symbol = name.split()[-1]
        ax.text(rad, 0.60, short_symbol, color='white', fontsize=13, ha='center', va='center', fontweight='bold')

    aspect_counts = {"merah": 0, "hijau": 0, "biru": 0, "kuning": 0}
    planets_keys = list(planet_degrees.keys())
    deg_list = list(planet_degrees.values())

    for i in range(len(planets_keys)):
        for j in range(i + 1, len(planets_keys)):
            d1 = deg_list[i]
            d2 = deg_list[j]
            diff = abs(d1 - d2) % 360
            if diff > 180: diff = 360 - diff
            rad1, rad2 = np.radians(d1), np.radians(d2)

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


def add_cumulative(orders):
    result = []
    cumulative = 0.0
    for price, size in orders:
        cumulative += size
        result.append({
            "price": price,
            "size": size,
            "cumulative": cumulative
        })
    return result


def show_orderbook_visual(bids, asks, min_cum=0.0):
    if not bids or not asks:
        st.warning("Data kosong")
        return

    bids_data = add_cumulative(bids)
    asks_data = add_cumulative(asks)

    # Filter cumulative
    if min_cum > 0:
        bids_data = [x for x in bids_data if x["cumulative"] >= min_cum]
        asks_data = [x for x in asks_data if x["cumulative"] >= min_cum]

    if not bids_data or not asks_data:
        st.warning(f"Tidak ada level dengan cumulative ≥ {min_cum}")
        return

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid = (best_bid + best_ask) / 2
    spread = best_ask - best_bid

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Best Bid", f"{best_bid:,.2f}")
    c2.metric("Best Ask", f"{best_ask:,.2f}")
    c3.metric("Mid", f"{mid:,.2f}")
    c4.metric("Spread", f"{spread:.2f}")

    st.markdown("---")

    # Ambil max cumulative untuk scaling bar
    max_cum = max(
        max([x["cumulative"] for x in bids_data[:25]], default=1),
        max([x["cumulative"] for x in asks_data[:25]], default=1)
    )

    col_bid, col_ask = st.columns(2)

    with col_bid:
        st.markdown("### 🟢 Beli (Bids)")
        for item in bids_data[:25]:
            pct = min(item["cumulative"] / max_cum, 1.0)
            bar = "█" * int(pct * 20)
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; background:linear-gradient(90deg, #0d3b2e {pct*100}%, transparent 0%); padding:4px 8px; margin:2px 0; border-radius:4px;'>"
                f"<span style='color:#00ff9d'>{item['cumulative']:,.0f}</span>"
                f"<span style='color:white'>{item['price']:,.2f}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    with col_ask:
        st.markdown("### 🔴 Jual (Asks)")
        for item in asks_data[:25]:
            pct = min(item["cumulative"] / max_cum, 1.0)
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; background:linear-gradient(270deg, #3b0d0d {pct*100}%, transparent 0%); padding:4px 8px; margin:2px 0; border-radius:4px;'>"
                f"<span style='color:white'>{item['price']:,.2f}</span>"
                f"<span style='color:#ff4d4d'>{item['cumulative']:,.0f}</span>"
                f"</div>",
                unsafe_allow_html=True
            )


# ==========================================
# HALAMAN ASTRODOX
# ==========================================
if menu == "🔮 Astrodox":
    st.title("🔮 ABEL FX — Astrodox Wheel")
    st.caption("Roda Transit Planet + Rekap Aspek Geometri")

    st.markdown("---")
    st.subheader("📅 Atur Waktu Transit")

    c1, c2, c3, c4, c5 = st.columns(5)
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

    st.markdown(f"**Waktu:** `{event_datetime.strftime('%d %B %Y %H:%M WIB')}`")
    st.markdown("---")

    fig, img_buf, aspect_counts, planet_positions = generate_astrodox_wheel_only(event_datetime)
    st.subheader("🔮 Roda Astrodox Transit")
    st.pyplot(fig, use_container_width=True)
    st.download_button("📥 Download Roda", img_buf, f"Astrodox_{event_datetime.strftime('%Y%m%d_%H%M')}.png", "image/png")

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

    aspek_text = f"""• MERAH  (Square/Opp) : {aspect_counts['merah']} → Volatilitas Tinggi
• HIJAU  (Trine)      : {aspect_counts['hijau']} → Expansion
• BIRU   (Sextile)    : {aspect_counts['biru']} → Retest
• KUNING (Conjunction): {aspect_counts['kuning']} → Turning Point"""

    st.markdown(f"""
    <div class="info-box">
    <strong>POSISI PLANET ({event_datetime.strftime('%d %b %Y %H:%M WIB')})</strong><br>
    {"─"*60}<br>
    {pos_text.replace(chr(10), "<br>")}<br><br>
    <strong>REKAP ASPEK</strong><br>
    {"─"*60}<br>
    {aspek_text.replace(chr(10), "<br>")}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("ABEL FX Astrodox Wheel")


# ==========================================
# HALAMAN ORDERBOOK
# ==========================================
elif menu == "📊 Orderbook":
    st.title("📊 Orderbook")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        symbol = st.selectbox("Pair", ["XAUT-USDT", "BTC-USDT"], index=0)
    with col2:
        min_cum = st.number_input("Min Cumulative (XAUT/BTC)", min_value=0.0, value=0.0, step=1.0)
    with col3:
        st.write("")
        st.write("")
        auto_refresh = st.checkbox("Auto Refresh", value=False)

    limit = st.selectbox("Jumlah Level", [20, 30, 50, 100], index=2)

    if st.button("🔄 Refresh Sekarang", type="primary") or auto_refresh or "ob_data" not in st.session_state:
        with st.spinner(f"Mengambil data {symbol}..."):
            st.session_state.ob_data = get_okx_orderbook(symbol, limit)

    bids, asks, err = st.session_state.ob_data

    if err:
        st.error(err)
    else:
        show_orderbook_visual(bids, asks, min_cum)

    if auto_refresh:
        time.sleep(3)
        st.rerun()

    st.caption("Semakin panjang bar = semakin besar cumulative volume. Mirip tampilan di aplikasi exchange.")
