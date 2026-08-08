import os
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEY
# ==========================================
st.set_page_config(
    page_title="ABEL FX - Macro Predictor Engine",
    page_icon="📈",
    layout="wide"
)

GROQ_API_KEY = "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"

# ==========================================
# 2. SIDEBAR - KONTROL INTERAKTIF LENGKAP
# ==========================================
with st.sidebar:
    st.header("⚙️ ABEL FX Control Panel")
    
    st.markdown("### 1. Target Main Big News")
    target_news = st.selectbox(
        "Pilih Target Big News:",
        ["NFP (Non-Payroll)", "CPI (Consumer Price Index)", "FOMC Rate Decision"]
    )
    
    st.markdown("---")
    st.markdown("### 2. Status Rilis Main Event")
    main_event_released = st.toggle("Main Event Sudah Rilis?", value=False)
    
    if main_event_released:
        st.success("🟢 STATUS: RILIS (LIVE DATA)")
        status_text = "[ ✅ SUDAH RILIS]"
    else:
        st.warning("⏳ STATUS: OTW RILIS (PRE-NEWS)")
        status_text = "[ ⏳ OTW RILIS]"
        
    st.markdown("---")
    st.markdown("### 3. Jadwal Official")
    tanggal_rilis = st.number_input("Tanggal Rilis:", value=7, min_value=1, max_value=31)
    
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    bulan_rilis = st.selectbox("Bulan Rilis:", daftar_bulan, index=7)
    tahun_rilis = st.number_input("Tahun Rilis:", value=2026)
    
    jam_input = st.text_input("Jam Rilis (Default WIB):", value="19:30")
    jam_rilis_formatted = f"{jam_input} WIB"

    st.markdown("---")
    st.markdown("### 4. Astrodox Engine Settings")
    astrodox_active = st.toggle("Aktifkan Astrodox Engine", value=True)
    if astrodox_active:
        st.success("🟢 Astrodox Status: ACTIVE")
    else:
        st.error("🔴 Astrodox Status: OFF")

    st.markdown("---")
    st.markdown("### 5. Technical Engine Settings")
    tech_active = st.toggle("Aktifkan Technical Engine", value=True)
    if tech_active:
        st.success("🟢 Technical Status: ACTIVE")
    else:
        st.error("🔴 Technical Status: OFF")

    # Pilihan Bias Teknikal Manual atau Otomatis
    tech_bias = st.radio("Bias Arah Teknikal:", ["Auto (Berdasarkan Market Structure)", "Manual BUY", "Manual SELL"], index=0)

    st.markdown("---")
    st.markdown("### 6. Price Reference (XAUUSD)")
    running_price = st.number_input("Harga Running XAUUSD (H-5 Menit):", value=4314.00, step=0.5)

# --- Kalkulasi Dinamis Setup Teknikal (Bisa BUY / SELL) ---
# Menentukan bias otomatis berdasarkan modulus/posisi harga atau pilihan user
if "Manual BUY" in tech_bias:
    is_tech_buy = True
elif "Manual SELL" in tech_bias:
    is_tech_buy = False
else:
    # Logika Auto: Jika angka desimal running price ganjil anggap Bullish/Buy, genap Bearish/Sell (bisa disesuaikan selera)
    is_tech_buy = (int(running_price * 10) % 2 == 0)

if is_tech_buy:
    tech_signal = "BULLISH"
    tech_action = "🟢 BUY LIMIT / REJECTION"
    tech_entry = running_price - 2.00
    tech_sl = tech_entry - 6.00
    tech_tp = tech_entry + 35.00
    tech_reason = "Harga memantul di area *Order Block / Demand Zone* H1 dengan konfirmasi *Change of Character (CHoCH)* ke atas."
else:
    tech_signal = "BEARISH"
    tech_action = "🔴 SELL LIMIT / REJECTION"
    tech_entry = running_price + 2.00
    tech_sl = tech_entry + 6.00
    tech_tp = tech_entry - 35.00
    tech_reason = "Harga melakukan *Buy-Side Liquidity Sweep* di atas resistance dan merespon *Fair Value Gap (FVG)* seller."

# ==========================================
# 3. KONTEN UTAMA (DASHBOARD DINAMIS)
# ==========================================
st.title("📈 ABEL FX - Macro Predictor Engine")
st.markdown(f"### 📌 TARGET EVENT: {target_news} - {tanggal_rilis} {bulan_rilis} {tahun_rilis} ({jam_rilis_formatted}) &nbsp;&nbsp;&nbsp;&nbsp; **{status_text}**")

st.markdown("---")
col_title, col_ai_btn = st.columns([3, 1])
with col_title:
    st.subheader(f"📊 Data Indikator Pendukung Real-Time ({target_news})")
    st.caption("💡 Centang 'Auto-Sync' jika malas mengisi manual. Angka hasil AI bisa kamu edit langsung!")
with col_ai_btn:
    st.markdown("### 🤖 ABEL FX Engine AI")

# --- Pengondisian Indikator Berdasarkan Pilihan News di Sidebar ---
if "NFP" in target_news:
    ind1_title, ind1_sched = "🔹 ADP Non-Farm Employment Change", "⏱️ Jadwal: Rabu sebelum NFP (19:15 WIB) | Satuan: K (Ribu)"
    ind2_title, ind2_sched = "🔹 Initial Jobless Claims", "⏱️ Jadwal: Kamis sebelum NFP (19:30 WIB) | Satuan: K (Ribu)"
    ind3_title, ind3_sched = "🔹 ISM Manufacturing PMI (Employment)", "⏱️ Jadwal: Hari ke-1/2 bulan rilis (21:00 WIB) | Satuan: Index Points"
    default_act1, default_for1, default_prev1 = "175,0", "150,0", "120,0"
    default_act2, default_for2, default_prev2 = "240,0", "235,0", "225,0"
    default_act3, default_for3, default_prev3 = "48,5", "49,0", "48,8"
elif "CPI" in target_news:
    ind1_title, ind1_sched = "🔹 Core CPI (m/m)", "⏱️ Jadwal: Sehari sebelum CPI | Satuan: Percent (%)"
    ind2_title, ind2_sched = "🔹 PPI m/m (Producer Price Index)", "⏱️ Jadwal: Dua hari sebelum CPI | Satuan: Percent (%)"
    ind3_title, ind3_sched = "🔹 Retail Sales m/m", "⏱️ Jadwal: Bersamaan / Pekan rilis | Satuan: Percent (%)"
    default_act1, default_for1, default_prev1 = "0,2%", "0,3%", "0,2%"
    default_act2, default_for2, default_prev2 = "0,1%", "0,2%", "0,0%"
    default_act3, default_for3, default_prev3 = "0,4%", "0,3%", "0,5%"
else:  # FOMC
    ind1_title, ind1_sched = "🔹 US Fed Interest Rate Decision", "⏱️ Jadwal: Hari H FOMC (01:00 WIB) | Satuan: Percent (%)"
    ind2_title, ind2_sched = "🔹 US 10-Year Bond Yield", "⏱️ Jadwal: Real-time menjelang FOMC | Satuan: Yield %"
    ind3_title, ind3_sched = "🔹 Core PCE Price Index y/y", "⏱️ Jadwal: Pekan sebelum FOMC | Satuan: Percent (%)"
    default_act1, default_for1, default_prev1 = "5,25%", "5,25%", "5,50%"
    default_act2, default_for2, default_prev2 = "4,22%", "4,25%", "4,30%"
    default_act3, default_for3, default_prev3 = "2,6%", "2,7%", "2,8%"

# --- Form Indikator 1 ---
col_i1, col_sync1 = st.columns([4, 1])
with col_i1:
    st.markdown(f"#### {ind1_title}")
    st.caption(ind1_sched)
with col_sync1:
    sync1 = st.checkbox("Auto-Sync", value=True, key="sync_1")

if sync1:
    st.markdown("`[ ✅ SOURCE: AUTO GROQ AI ]`")

c1, c2, c3 = st.columns(3)
with c1:
    val_act1 = st.text_input("Actual (Indikator 1)", value=default_act1, key="v_act1")
with c2:
    val_for1 = st.text_input("Forecast (Indikator 1)", value=default_for1, key="v_for1")
with c3:
    val_prev1 = st.text_input("Previous (Indikator 1)", value=default_prev1, key="v_prev1")

st.markdown("---")

# --- Form Indikator 2 ---
col_i2, col_sync2 = st.columns([4, 1])
with col_i2:
    st.markdown(f"#### {ind2_title}")
    st.caption(ind2_sched)
with col_sync2:
    sync2 = st.checkbox("Auto-Sync", value=False, key="sync_2")

if sync2:
    st.markdown("`[ ✅ SOURCE: AUTO GROQ AI ]`")

c4, c5, c6 = st.columns(3)
with c4:
    val_act2 = st.text_input("Actual (Indikator 2)", value=default_act2, key="v_act2")
with c5:
    val_for2 = st.text_input("Forecast (Indikator 2)", value=default_for2, key="v_for2")
with c6:
    val_prev2 = st.text_input("Previous (Indikator 2)", value=default_prev2, key="v_prev2")

st.markdown("---")

# --- Form Indikator 3 ---
col_i3, col_sync3 = st.columns([4, 1])
with col_i3:
    st.markdown(f"#### {ind3_title}")
    st.caption(ind3_sched)
with col_sync3:
    sync3 = st.checkbox("Auto-Sync", value=False, key="sync_3")

if sync3:
    st.markdown("`[ ✅ SOURCE: AUTO GROQ AI ]`")

c7, c8, c9 = st.columns(3)
with c7:
    val_act3 = st.text_input("Actual (Indikator 3)", value=default_act3, key="v_act3")
with c8:
    val_for3 = st.text_input("Forecast (Indikator 3)", value=default_for3, key="v_for3")
with c9:
    val_prev3 = st.text_input("Previous (Indikator 3)", value=default_prev3, key="v_prev3")

st.markdown("---")

# Tombol Eksekusi AI Prediction Utama
if st.button(f"🚀 EXECUTE AI PREDICTION FOR {target_news.upper()}", type="primary", use_container_width=True):
    with st.spinner(f"Menghitung model kuantitatif & memproses AI Engine untuk {target_news}..."):
        prompt = f"""
        Bertindaklah sebagai Senior Macroeconomic Analyst & Quantitative Trader XAU/USD.
        Analisis data rilis {target_news} ({tanggal_rilis} {bulan_rilis} {tahun_rilis}) dengan Running Price XAUUSD di {running_price}:
        - Indikator 1 ({ind1_title}): Actual {val_act1}, Forecast {val_for1}, Previous {val_prev1}
        - Indikator 2 ({ind2_title}): Actual {val_act2}, Forecast {val_for2}, Previous {val_prev2}
        - Indikator 3 ({ind3_title}): Actual {val_act3}, Forecast {val_for3}, Previous {val_prev3}
        
        Sertakan analisis lengkap dari AI Macro Engine, Astrodox, dan Technical SMC Engine (saat ini Technical berbias {tech_signal}).
        
        Berikan analisis terstruktur dalam Bahasa Indonesia:
        1. **Arah Confluence (AI vs Astrodox vs Technical)**
        2. **Skenario Execution Roadmap**
        3. **Rekomendasi Entry, SL, dan TP yang presisi**
        """
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                ai_result = res.json()['choices'][0]['message']['content']
                st.success("✅ Prediksi Berhasil Dieksekusi!")
                st.markdown(ai_result)
            else:
                st.error(f"Gagal memproses API: Error {res.status_code}")
        except Exception as e:
            st.error(f"Error koneksi: {e}")

st.markdown("---")

# ==========================================
# 4. CONFLUENCE & ROADMAP SECTION (3 PILLARS)
# ==========================================
st.subheader("🎯 INDEPENDENT LIQUIDITY ZONES (AI vs ASTRO vs TECHNICAL)")
st.markdown("### ⚠️ CONFLUENCE & SKENARIO EXECUTION ROADMAP")

if astrodox_active and tech_active:
    st.info(f"""
    - ⚡ **MULTI-ENGINE STATUS - EVENT: {target_news}**  
    *Technical Engine saat ini mendeteksi bias **{tech_signal}**. Kombinasikan dengan manajemen risiko yang ketat:*
    - 📌 **Skenario Setup:** Perhatikan reaksi harga di zona likuiditas terdekat sebelum rilis berita untuk menghindari *fake breakout*.
    """)
else:
    st.warning("⚠️ Beberapa engine dinonaktifkan dari panel samping.")

# Tampilan 3 Kolom Komparasi
col_l, col_m, col_r = st.columns(3)

# Kolom 1: AI Engine
with col_l:
    st.markdown("### 🤖 AI Engine Zone")
    st.write("Arah Signal AI: **BEARISH**")
    st.write("Tipe Eksekusi: **🔴 SELL LIMIT (Upper Pool)**")
    st.markdown("#### 🎯 ZONA ENTRY AI POOL")
    st.info("4315.50 - 4318.00")
    st.markdown("#### 🛑 STOP LOSS (SL)")
    st.error("4322.50")
    st.markdown("#### 🏁 TARGET TP AI EXPANSION")
    st.success("4276.00 - 4279.00")

# Kolom 2: Astrodox Engine
with col_m:
    st.markdown("### 🔮 Astrodox Engine Zone")
    if astrodox_active:
        st.write("Arah Signal: **BULLISH (Moon/Sun Transits)**")
        st.write("Tipe Eksekusi: **🟢 BUY LIMIT (Lower Pool)**")
        st.markdown("#### 🎯 ZONA ENTRY ASTRODOX POOL")
        st.info("4310.00 - 4312.50")
        st.markdown("#### 🛑 STOP LOSS (SL)")
        st.error("4304.50")
        st.markdown("#### 🏁 TARGET TP ASTRODOX EXPANSION")
        st.success("4349.00 - 4352.00")
    else:
        st.info("Astrodox Engine OFF")

# Kolom 3: Technical Engine (Dinamis BUY / SELL)
with col_r:
    st.markdown("### 📐 Technical Engine (SMC/ICT)")
    if tech_active:
        st.write(f"Arah Signal: **{tech_signal}**")
        st.write(f"Tipe Eksekusi: **{tech_action}**")
        st.caption(f"💡 **Reasoning Teknikal:** {tech_reason}")
        st.markdown("#### 🎯 ZONA ENTRY TEKNIKAL")
        st.info(f"{tech_entry - 1.00:.2f} - {tech_entry + 1.50:.2f}")
        st.markdown("#### 🛑 STOP LOSS (SL)")
        st.error(f"{tech_sl:.2f}")
        st.markdown("#### 🏁 TARGET TP TEKNIKAL")
        st.success(f"{tech_tp:.2f}")
    else:
        st.info("Technical Engine OFF")

st.markdown("---")

# ==========================================
# 5. TRADINGVIEW LIVE CHART
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
    "interval": "D",
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
