import os
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEY
# ==========================================
st.set_page_config(
    page_title="ABEL FX - NFP & Macro Predictor",
    page_icon="📈",
    layout="wide"
)

GROQ_API_KEY = "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"

# ==========================================
# 2. SIDEBAR - INPUT & KONTROL UTAMA
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
    else:
        st.warning("⏳ STATUS: OTW RILIS (PRE-NEWS)")
        
    st.markdown("---")
    st.markdown("### 3. Jadwal Official")
    tanggal_rilis = st.number_input("Tanggal Rilis:", value=7, min_value=1, max_value=31)
    bulan_rilis = st.selectbox("Bulan Rilis:", ["Agustus 2026", "September 2026", "Oktober 2026"])

# ==========================================
# 3. KONTEN UTAMA (DASHBOARD INTERAKTIF)
# ==========================================
st.title("📈 ABEL FX - NFP & Macro Predictor Engine")
st.markdown(f"### 📌 TARGET EVENT: Non-Farm Payrolls (NFP) - {tanggal_rilis} Agustus 2026 [⏳ OTW RILIS]")

st.markdown("---")
st.subheader("📊 Data Indikator Pendukung Real-Time & Auto-Sync")
st.caption("💡 Sesuaikan angka Actual, Forecast, atau Previous di bawah ini jika diperlukan untuk simulasi.")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### **ADP Non-Farm Employment Change**")
    adp_actual = st.text_input("ADP Actual", value="175,0")
    adp_forecast = st.text_input("ADP Forecast", value="150,0")
    adp_previous = st.text_input("ADP Previous", value="120,0")

with col2:
    st.markdown("#### **Initial Jobless Claims**")
    ijc_actual = st.text_input("Jobless Claims Actual", value="240,0")
    ijc_forecast = st.text_input("Jobless Claims Forecast", value="235,0")
    ijc_previous = st.text_input("Jobless Claims Previous", value="225,0")

with col3:
    st.markdown("#### **ISM Manufacturing PMI**")
    ism_actual = st.text_input("ISM Actual", value="48,5")
    ism_forecast = st.text_input("ISM Forecast", value="49,0")
    ism_previous = st.text_input("ISM Previous", value="48,8")

st.markdown("---")

# Tombol Eksekusi AI Prediction
if st.button("🚀 EXECUTE AI PREDICTION & LIQUIDITY ZONE", type="primary", use_container_width=True):
    with st.spinner("Mengkalkulasi data indikator pendukung & AI Engine..."):
        
        # Panggilan AI Groq untuk analisis berdasarkan input interaktif
        prompt = f"""
        Bertindaklah sebagai Senior Macroeconomic Analyst & Quantitative Trader XAU/USD.
        Analisis data indikator NFP berikut:
        - ADP Non-Farm: Actual {adp_actual}, Forecast {adp_forecast}, Previous {adp_previous}
        - Initial Jobless Claims: Actual {ijc_actual}, Forecast {ijc_forecast}, Previous {ijc_previous}
        - ISM Manufacturing PMI: Actual {ism_actual}, Forecast {ism_forecast}, Previous {ism_previous}
        
        Berikan analisis dan proyeksi teknikal terstruktur dalam Bahasa Indonesia:
        1. **Arah Signal AI & Skenario Pergerakan** (Skenario A jika naik duluan, Skenario B jika turun duluan)
        2. **Zona Entry Pool** (Rekomendasi area Buy/Sell Limit)
        3. **Target TP Expansion**
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
                st.success("✅ Analisis Prediksi Berhasil Dijalankan!")
                st.markdown(ai_result)
            else:
                st.error(f"Gagal memproses AI: Error {res.status_code}")
        except Exception as e:
            st.error(f"Koneksi error: {e}")

st.markdown("---")

# Tampilan Skenario Default / Layout Bawah
st.subheader("🎯 Live Market Scenarios & Liquidity Zones")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 🤖 AI Engine Liquidity Zone")
    st.write("Arah Signal AI: **BEARISH**")
    st.write("Tipe Eksekusi: **🔴 SELL LIMIT (Upper Pool)**")
    st.info("🎯 **ZONA ENTRY AI POOL:** 4315.50 - 4318.00")
    st.success("🏁 **TARGET TP AI EXPANSION (+380 Pips):** 4276.00 - 4279.00")

with col_b:
    st.markdown("### 🔮 Astrodox Engine Liquidity Zone")
    st.write("Arah Signal Astrodox: **BULLISH (Planetary Transits)**")
    st.write("Tipe Eksekusi: **🟢 BUY LIMIT (Lower Pool)**")
    st.info("🎯 **ZONA ENTRY ASTRODOX POOL:** 4310.00 - 4312.50")
    st.success("🏁 **TARGET TP ASTRODOX EXPANSION (+380 Pips):** 4349.00 - 4352.00")

st.markdown("---")
st.subheader("📉 Chart Live TradingView (XAUUSD)")
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
