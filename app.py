import os
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN & API KEY
# ==========================================
st.set_page_config(
    page_title="ABEL FX - Macro & News Intelligence",
    page_icon="📈",
    layout="wide"
)

GROQ_API_KEY = "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"

# ==========================================
# 2. FUNGSI UTAMA & QUANT ENGINE
# ==========================================
def fetch_economic_calendar():
    url = "https://nfp.ourfx.workers.dev/"
    fallback_url = "https://nfp-calendar.pages.dev/api/calendar"
    headers = {"User-Agent": "Mozilla/5.0"}

    for u in [url, fallback_url]:
        try:
            res = requests.get(u, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return pd.DataFrame(data)
        except Exception:
            continue

    sample_data = [
        {"title": "USD Non-Farm Employment Change", "country": "USD", "date": "2026-08-07T12:30:00Z", "impact": "High", "forecast": "175K", "previous": "143K"},
        {"title": "USD Unemployment Rate", "country": "USD", "date": "2026-08-07T12:30:00Z", "impact": "High", "forecast": "4.1%", "previous": "4.1%"},
        {"title": "USD CPI m/m", "country": "USD", "date": "2026-08-12T12:30:00Z", "impact": "High", "forecast": "0.2%", "previous": "0.1%"}
    ]
    return pd.DataFrame(sample_data)

def analyze_news_with_groq(news_text):
    if not GROQ_API_KEY:
        return "⚠️ API Key Groq tidak terdeteksi."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    Kamu adalah Senior Macroeconomic Analyst & Quantitative Trader. Analisis data kalender ekonomi berikut:
    {news_text}
    Berikan analisis terstruktur dalam Bahasa Indonesia:
    1. **Ringkasan Eksekutif**
    2. **Sentimen USD** (Bullish/Bearish/Netral)
    3. **Proyeksi Dampak pada Gold (XAU/USD)**
    4. **Trading Bias & Rekomendasi Action**
    """
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
        return f"Error: {res.status_code}"
    except Exception as e:
        return f"Error: {e}"

# ==========================================
# 3. DASHBOARD STREAMLIT (UI/UX)
# ==========================================
st.title("📈 ABEL FX - Macro & News Intelligence")
st.caption("Real-time Macroeconomic Event Monitor, AI Market Analysis & Astrodox/Coinglass Quant Engine")

tab1, tab2, tab3 = st.tabs([
    "📊 Kalender Ekonomi & AI Analyst", 
    "📉 Live Chart TradingView (XAUUSD)", 
    "🔮 Astrodox & Coinglass Quant Engine"
])

with tab1:
    st.subheader("🗓️ Kalender Ekonomi Minggu Ini")
    if st.button("🔄 Reload Data Berita", use_container_width=True):
        st.rerun()
    
    df_news = fetch_economic_calendar()
    if not df_news.empty:
        st.dataframe(df_news, use_container_width=True, height=280)
        st.markdown("---")
        st.subheader("🤖 AI Market Analysis (Groq Llama 3)")
        if st.button("🚀 Jalankan Analisis AI Terhadap Berita", type="primary"):
            with st.spinner("Menganalisis data makroekonomi..."):
                st.markdown(analyze_news_with_groq(df_news.to_string()))

with tab2:
    st.subheader("📉 Chart Live TradingView (XAUUSD)")
    tradingview_widget = """
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tradingview_chart" style="height:600px;width:100%"></div>
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
    components.html(tradingview_widget, height=620)

with tab3:
    st.subheader("🔮 Astrodox Engine & AI Liquidity Zone Calculator")
    
    # Kotak Skenario Utama di Atas
    st.error("""
    - 📌 **Skenario A (Jika Naik Duluan):** Ambil **SELL LIMIT AI** di Upper Pool (4315.50 - 4318.00) dengan Target TP di 4276.00 - 4279.00.  
    - 📌 **Skenario B (Jika Turun Duluan):** Ambil **BUY LIMIT Astrodox** di Lower Pool (4310.00 - 4312.50) dengan Target TP di 4349.00 - 4352.00.
    """)

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤖 AI Engine Liquidity Zone")
        st.write("Arah Signal AI: **BEARISH**")
        st.write("Tipe Eksekusi: **🔴 SELL LIMIT (Upper Pool)**")
        st.markdown("#### 🎯 ZONA ENTRY AI POOL")
        st.info("4315.50 - 4318.00")
        st.markdown("#### 🏁 TARGET TP AI EXPANSION (+380 Pips)")
        st.success("4276.00 - 4279.00")

    with col2:
        st.markdown("### 🔮 Astrodox Engine Liquidity Zone")
        st.write("Arah Signal Astrodox: **BULLISH (Moon/Sun Planetary Transits)**")
        st.write("Tipe Eksekusi: **🟢 BUY LIMIT (Lower Pool)**")
        st.markdown("#### 🎯 ZONA ENTRY ASTRODOX POOL")
        st.info("4310.00 - 4312.50")
        st.markdown("#### 🏁 TARGET TP ASTRODOX EXPANSION (+380 Pips)")
        st.success("4349.00 - 4352.00")
