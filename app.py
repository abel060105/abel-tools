import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import requests

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
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
    .prompt-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px 20px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #c9d1d9;
        white-space: pre-wrap;
        line-height: 1.5;
    }
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background-color: #0d1117;
    }
</style>
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
        ax.bar(
            x=(theta_start + theta_end) / 2, height=0.25, width=np.radians(30),
            bottom=0.75, color=colors[i], alpha=0.6, edgecolor='#555555'
        )
        ax.text(
            (theta_start + theta_end) / 2, 0.88, ZODIAC_SYMBOLS[i],
            color='white', fontsize=16, ha='center', va='center', fontweight='bold'
        )

    planets_keys = list(planet_degrees.keys())
    deg_list = list(planet_degrees.values())

    for name, deg in planet_degrees.items():
        rad = np.radians(deg)
        ax.plot(rad, 0.70, marker='o', color='#00ffff', markersize=7)
        short_symbol = name.split()[-1]
        ax.text(rad, 0.60, short_symbol, color='white', fontsize=13, ha='center', va='center', fontweight='bold')

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

    ax.set_title(
        f"{target_date.strftime('%d.%m.%Y %H:%M WIB')}",
        color='white', fontsize=16, pad=18, fontweight='bold'
    )

    plt.tight_layout()

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=220, bbox_inches='tight', facecolor='#0e1117')
    img_buf.seek(0)

    return fig, img_buf, aspect_counts, planet_positions


# ==========================================
# ORDERBOOK XAUT
# ==========================================

def get_binance_orderbook(limit=15):
    try:
        url = f"https://api.binance.com/api/v3/depth?symbol=XAUTUSDT&limit={limit}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if "bids" not in data:
            return [], [], data.get("msg", "Binance error")
        bids = [[float(p), float(q)] for p, q in data["bids"]]
        asks = [[float(p), float(q)] for p, q in data["asks"]]
        return bids, asks, None
    except Exception as e:
        return [], [], str(e)

def get_bybit_orderbook(limit=15):
    try:
        url = f"https://api.bybit.com/v5/market/orderbook?category=spot&symbol=XAUTUSDT&limit={limit}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("retCode") != 0:
            return [], [], data.get("retMsg", "Bybit error")
        result = data["result"]
        bids = [[float(p), float(q)] for p, q in result.get("b", [])]
        asks = [[float(p), float(q)] for p, q in result.get("a", [])]
        return bids, asks, None
    except Exception as e:
        return [], [], str(e)

def get_okx_orderbook(limit=15):
    try:
        url = f"https://www.okx.com/api/v5/market/books?instId=XAUT-USDT&sz={limit}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("code") != "0":
            return [], [], data.get("msg", "OKX error")
        book = data["data"][0]
        bids = [[float(p), float(q)] for p, q, *_ in book["bids"]]
        asks = [[float(p), float(q)] for p, q, *_ in book["asks"]]
        return bids, asks, None
    except Exception as e:
        return [], [], str(e)

def display_orderbook(bids, asks, exchange_name, error=None):
    if error:
        st.error(f"**{exchange_name}**: {error}")
        return

    if not bids or not asks:
        st.warning(f"**{exchange_name}**: Data kosong")
        return

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    spread = best_ask - best_bid
    mid = (best_bid + best_ask) / 2

    st.markdown(f"**{exchange_name}** | Mid: `{mid:.2f}` | Spread: `{spread:.2f}`")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Bids (Buy)**")
        for price, qty in bids[:10]:
            st.write(f"`{price:.2f}` — {qty:.4f}")

    with col2:
        st.markdown("**Asks (Sell)**")
        for price, qty in asks[:10]:
            st.write(f"`{price:.2f}` — {qty:.4f}")


# ==========================================
# BERANDA UTAMA
# ==========================================
st.title("🔮 ABEL FX — Astrodox Wheel")
st.caption("Roda Transit Planet + Rekap Aspek Geometri | Siap untuk di-copy ke AI eksternal")

st.markdown("---")

# ----- Selector Tanggal & Jam -----
st.subheader("📅 Atur Waktu Transit")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    tanggal = st.number_input("Tanggal", min_value=1, max_value=31, value=12)

with col2:
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    bulan_dict = {nama: i + 1 for i, nama in enumerate(daftar_bulan)}
    bulan_nama = st.selectbox("Bulan", daftar_bulan, index=7)
    bulan = bulan_dict[bulan_nama]

with col3:
    tahun = st.number_input("Tahun", min_value=2000, max_value=2100, value=2026)

with col4:
    jam = st.number_input("Jam (WIB)", min_value=0, max_value=23, value=19)

with col5:
    menit = st.number_input("Menit", min_value=0, max_value=59, value=30)

try:
    event_datetime = datetime(int(tahun), int(bulan), int(tanggal), int(jam), int(menit))
except ValueError:
    st.error("Tanggal tidak valid (cek jumlah hari di bulan tersebut).")
    st.stop()

st.markdown(f"**Waktu yang dipilih:** `{event_datetime.strftime('%d %B %Y %H:%M WIB')}`")

st.markdown("---")

# ----- Generate Roda -----
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

# ----- ORDERBOOK XAUT -----
st.subheader("📊 Orderbook XAUT/USDT (Realtime)")

refresh = st.button("🔄 Refresh Orderbook")

if refresh or "orderbook_loaded" not in st.session_state:
    with st.spinner("Mengambil data orderbook..."):
        st.session_state.binance = get_binance_orderbook()
        st.session_state.bybit = get_bybit_orderbook()
        st.session_state.okx = get_okx_orderbook()
        st.session_state.orderbook_loaded = True

col_a, col_b, col_c = st.columns(3)

with col_a:
    b, a, e = st.session_state.binance
    display_orderbook(b, a, "Binance", e)

with col_b:
    b, a, e = st.session_state.bybit
    display_orderbook(b, a, "Bybit", e)

with col_c:
    b, a, e = st.session_state.okx
    display_orderbook(b, a, "OKX", e)

st.caption("Data diambil langsung dari public API exchange (Binance, Bybit, OKX). Klik Refresh untuk update.")

st.markdown("---")

# ----- Dashboard Info -----
st.subheader("📋 Dashboard Info Astrodox")

pos_lines = []
pos_items = list(planet_positions.items())
for idx in range(0, len(pos_items), 2):
    p1, v1 = pos_items[idx]
    if idx + 1 < len(pos_items):
        p2, v2 = pos_items[idx + 1]
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

# ==========================================
# PAPAN PROMPT 1
# ==========================================
st.subheader("📋 Papan Prompt 1 — Full Analysis (Makro + Geopolitik + 3 Setup)")

prompt_full = f"""Kamu adalah Senior Quantitative Trader + Macro Analyst + Financial Astrologer spesialis XAUUSD.

Gunakan data Astrodox di bawah ini + pengetahuan teknikal, makro, dan geopolitik terbaru kamu untuk menghasilkan analisis lengkap.

=== DATA ASTRODOX TRANSIT ===
Waktu: {event_datetime.strftime('%d %B %Y %H:%M WIB')}

POSISI PLANET:
{pos_text}

REKAP GARIS ASPEK GEOMETRI:
{aspek_text}

=== INSTRUKSI OUTPUT (WAJIB LENGKAP) ===

1. **Rekap Data News & Indikator Pendukung**
   - Tentukan sendiri news utama yang relevan (NFP / CPI / FOMC / dll) berdasarkan waktu di atas.
   - Tampilkan data pendukung yang paling relevan (Actual | Forecast | Previous).
   - AI yang menentukan indikator mana yang paling penting.

2. **Analisis Makro**
   - Bias makro saat ini (Bullish USD / Bearish USD / Neutral).
   - Skor dan alasan singkat berdasarkan data pendukung.

3. **Update Geopolitik Terbaru**
   - Isu geopolitik krusial terkini yang mempengaruhi XAUUSD & USD.
   - Dampak gabungan ke USD dan XAUUSD.

4. **Kesimpulan AI untuk Entry**
   - Bias utama: BULLISH / BEARISH / WHIPSAW / NEUTRAL
   - Peringatan Whipsaw (jika ada)
   - Proyeksi Range:
     • Sweep Range
     • Trend Range
     • Reversal Range

5. **3 Setup Entry Lengkap**
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

st.markdown("Salin prompt di bawah ini lalu paste ke AI (Grok / Claude / GPT / dll):")
st.code(prompt_full, language="text")
st.caption("Klik ikon copy di pojok kanan atas blok kode di atas untuk menyalin prompt.")

st.markdown("---")

# ==========================================
# PAPAN PROMPT 2
# ==========================================
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
3. **Sweep Range** : contoh 80-150 Pips ($8.0-$15.0)
4. **Trend Range** : contoh 200-350 Pips ($20.0-$35.0)
5. **Reversal Range** : contoh 80-130 Pips ($8.0-$13.0)

Catatan:
- Fokus hanya pada confluence Astro + Price Action / SMC structure.
- Tidak perlu memberikan zona entry, SL, atau TP (sudah di-handle di sistem lain).
- Jelaskan singkat alasan bias berdasarkan aspek dominan (Merah/Hijau/Biru/Kuning).
"""

st.markdown("Salin prompt di bawah ini lalu paste ke AI (Grok / Claude / GPT / dll):")
st.code(prompt_simple, language="text")
st.caption("Klik ikon copy di pojok kanan atas blok kode di atas untuk menyalin prompt.")

st.markdown("---")
st.caption("ABEL FX Astrodox Wheel • Simplified • Ready for external AI prompt")
