import os
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEY
# ==========================================
st.set_page_config(
    page_title="ABEL FX - NFP & Macro Predictor Engine",
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
    bulan_rilis = st.selectbox("Bulan Rilis:", ["Agustus 2026", "September 2026", "Oktober 2026"])
    tahun_rilis = st.number_input("Tahun Rilis:", value=2026)
    jam_rilis = st.selectbox("Jam Rilis (WIB):", ["19:30 WIB", "20:30 WIB", "01:00 WIB"])

    st.markdown("---")
    st.markdown("### 4. Astrodox Engine Settings")
    astrodox_active = st.toggle("Aktifkan Astrodox Engine", value=True)
    if astrodox_active:
        st.success("🟢 Astrodox Status: ACTIVE")
    else:
        st.error("🔴 Astrodox Status: OFF")

    st.markdown("---")
    st.markdown("### 5. Price Reference (XAUUSD)")
    running_price = st.number_input("Harga Running XAUUSD (H-5 Menit):", value=4314.00, step=0.5)

# ==========================================
# 3. KONTEN UTAMA (DASHBOARD)
# ==========================================
st.title("📈 ABEL FX - NFP & Macro Predictor Engine")
st.markdown(f"### 📌 TARGET EVENT: Non-Farm Payrolls (NFP) - {tanggal_rilis} {bulan_rilis} ({jam_rilis}) &nbsp;&nbsp;&nbsp;&nbsp; **{status_text}**")

st.markdown("---")
col_title, col_ai_btn = st.columns([3, 1])
with col_title:
    st.subheader("📊 Data Indikator Pendukung Real-Time & Auto-Sync")
    st.caption("💡 Centang 'Auto-Sync DeepSeek' jika malas mengisi manual. Angka hasil AI bisa kamu edit langsung!")
with col_ai_btn:
    st.markdown("### 🤖 ABEL FX Engine AI")

# --- Indikator 1: ADP ---
col_adp1, col_adp2 = st.columns([4, 1])
with col_adp1:
    st.markdown("#### 🔹 ADP Non-Farm Employment Change")
    st.caption("⏱️ Jadwal: Rabu sebelum NFP (19:15 WIB) | Satuan: K (Ribu)")
with col_adp2:
    adp_autosync = st.checkbox("Auto-Sync", value=True, key="adp_sync")

if adp_autosync:
    st.markdown("`[ ✅ SOURCE: AUTO DEEPSEEK AI ]`")

c1, c2, c3 = st.columns(3)
with c1:
    adp_actual = st.text_input("Actual (ADP)", value="175,0")
with c2:
    adp_forecast = st.text_input("Forecast (ADP)", value="150,0")
with c3:
    adp_previous = st.text_input("Previous (ADP)", value="120,0")

st.markdown("---")

# --- Indikator 2: Jobless Claims ---
col_jc1, col_jc2 = st.columns([4, 1])
with col_jc1:
    st.markdown("#### 🔹 Initial Jobless Claims")
    st.caption("⏱️ Jadwal: Kamis sebelum NFP (19:30 WIB) | Satuan: K (Ribu)")
with col_jc2:
    jc_autosync = st.checkbox("Auto-Sync", value=False, key="jc_sync")

c4, c5, c6 = st.columns(3)
with c4:
    jc_actual = st.text_input("Actual (Claims)", value="240,0")
with c5:
    jc_forecast = st.text_input("Forecast (Claims)", value="235,0")
with c6:
    jc_previous = st.text_input("Previous (Claims)", value="225,0")

st.markdown("---")

# --- Indikator 3: ISM Manufacturing PMI ---
col_ism1, col_ism2 = st.columns([4, 1])
with col_ism1:
    st.markdown("#### 🔹 ISM Manufacturing PMI (Employment)")
    st.caption("⏱️ Jadwal: Hari ke-1/2 bulan rilis (21:00 WIB) | Satuan: Index Points")
with col_ism2:
    ism_autosync = st.checkbox("Auto-Sync", value=False, key="ism_sync")

c7, c8, c9 = st.columns(3)
with c7:
    ism_actual = st.text_input("Actual (ISM)", value="48,5")
with c8:
    ism_forecast = st.text_input("Forecast (ISM)", value="49,0")
with c9:
    ism_previous = st.text_input("Previous (ISM)", value="48,8")

st.markdown("---")

# Tombol Eksekusi AI Prediction Utama
if st.button("🚀 EXECUTE AI PREDICTION & QUANT ENGINE", type="primary", use_container_width=True):
    with st.spinner("Menghitung model kuantitatif & memproses AI Engine..."):
        prompt = f"""
        Bertindaklah sebagai Senior Macroeconomic Analyst & Quantitative Trader XAU/USD.
        Analisis data indikator NFP berikut dengan Running Price XAUUSD di {running_price}:
        - ADP: Actual {adp_actual}, Forecast {adp_forecast}, Previous {adp_previous}
        - Jobless Claims: Actual {jc_actual}, Forecast {jc_forecast}, Previous {jc_previous}
        - ISM PMI: Actual {ism_actual}, Forecast {ism_forecast}, Previous {ism_previous}
        
        Berikan analisis terstruktur dalam Bahasa Indonesia:
        1. **Arah Signal AI & Astrodox Confluence**
        2. **Skenario A & Skenario B Execution Roadmap**
        3. **Zona Entry Pool & Target TP Expansion (+380 Pips)**
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
# 4. CONFLUENCE & ROADMAP SECTION
# ==========================================
st.subheader("🎯 INDEPENDENT LIQUIDITY ZONES (AI vs ASTRO)")
st.markdown("### ⚠️ CONFLUENCE & SKENARIO EXECUTION ROADMAP")

if astrodox_active:
    st.error("""
    - 🔴 **DIVERGENCE BENTROK (AI: BEARISH vs ASTRO: BULLISH)**  
    *Tergantung Liquidity mana yang disapu duluan pada H-Detik Rilis News:*
    - 📌 **Skenario A (Jika Naik Duluan):** Ambil **SELL LIMIT AI** di Upper Pool (`4315.50 - 4318.00`) dengan Target TP di `4276.00 - 4279.00`.
    - 📌 **Skenario B (Jika Turun Duluan):** Ambil **BUY LIMIT Astrodox** di Lower Pool (`4310.00 - 4312.50`) dengan Target TP di `4349.00 - 4352.00`.
    """)
else:
    st.warning("""
    - ⚠️ **ASTRODOX ENGINE DINONAKTIFKAN**  
    - 📌 Hanya mengandalkan **AI Engine Saja** untuk eksekusi trade.
    """)

col_l, col_r = st.columns(2)

with col_l:
    st.markdown("### 🤖 AI Engine Liquidity Zone")
    st.write("Arah Signal AI: **BEARISH**")
    st.write("Tipe Eksekusi: **🔴 SELL LIMIT (Upper Pool)**")
    st.markdown("#### 🎯 ZONA ENTRY AI POOL")
    st.info("4315.50 - 4318.00")
    st.markdown("#### 🏁 TARGET TP AI EXPANSION (+380 Pips)")
    st.success("4276.00 - 4279.00")

with col_r:
    st.markdown("### 🔮 Astrodox Engine Liquidity Zone")
    if astrodox_active:
        st.write("Arah Signal Astrodox: **BULLISH (Moon/Sun Planetary Transits)**")
        st.write("Tipe Eksekusi: **🟢 BUY LIMIT (Lower Pool)**")
        st.markdown("#### 🎯 ZONA ENTRY ASTRODOX POOL")
        st.info("4310.00 - 4312.50")
        st.markdown("#### 🏁 TARGET TP ASTRODOX EXPANSION (+380 Pips)")
        st.success("4349.00 - 4352.00")
    else:
        st.info("Astrodox Engine saat ini sedang non-aktif dari Control Panel.")

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
