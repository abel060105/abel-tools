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

# API Key Gemini yang diberikan
GEMINI_API_KEY = "AQ.Ab8RN6KECAro03DXeXEdO_pHhORwDWq-Q5svAinyIcuPI5O7xg"

# ==========================================
# 2. FUNGSI UTAMA (FETCH NEWS & AI ANALYZER)
# ==========================================
def fetch_economic_calendar():
    """Mengambil data berita/kalender ekonomi dari API publik Forex Factory yang stabil"""
    url = "https://nfp.ourfx.workers.dev/"
    fallback_url = "https://nfp-calendar.pages.dev/api/calendar"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return pd.DataFrame(data)
    except Exception:
        pass

    try:
        response = requests.get(fallback_url, headers=headers, timeout=6)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return pd.DataFrame(data)
    except Exception:
        pass

    st.info("ℹ️ Menampilkan sampel data struktur berita (API utama sedang dipelihara/offline).")
    sample_data = [
        {"title": "USD Non-Farm Employment Change", "country": "USD", "date": "2026-08-07T12:30:00Z", "impact": "High", "forecast": "175K", "previous": "143K"},
        {"title": "USD Unemployment Rate", "country": "USD", "date": "2026-08-07T12:30:00Z", "impact": "High", "forecast": "4.1%", "previous": "4.1%"},
        {"title": "USD CPI m/m", "country": "USD", "date": "2026-08-12T12:30:00Z", "impact": "High", "forecast": "0.2%", "previous": "0.1%"}
    ]
    return pd.DataFrame(sample_data)

def analyze_news_with_gemini(news_text):
    """Mengirim data berita ke Gemini API untuk analisis sentimen & dampaknya"""
    if not GEMINI_API_KEY:
        return "⚠️ API Key Gemini tidak terdeteksi."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}

    prompt = f"""
    SISTEM: Kamu adalah seorang Senior Macroeconomic Analyst & Quantitative Trader berpengalaman di pasar Forex & Gold (XAU/USD) yang analitis dan presisi.
    
    TUGAS: Analisis data kalender ekonomi berikut:

    {news_text}

    Berikan analisis terstruktur dalam Bahasa Indonesia dengan format berikut:
    1. **Ringkasan Eksekutif**: Rangkuman singkat dampak berita terhadap fundamental pasar.
    2. **Sentimen USD**: (Bullish / Bearish / Netral) beserta alasan singkat berdasarkan data Actual vs Forecast.
    3. **Proyeksi Dampak pada Gold (XAU/USD)**: Potensi pergerakan harga Gold (Skenario Naik/Turun/Sideways).
    4. **Trading Bias & Rekomendasi Action**: Bias harian (Long/Short) dan area pertimbangan entry/risk management.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ Gagal memproses AI: Error Code {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Gagal menghubungi Gemini API: {e}"

# ==========================================
# 3. DASHBOARD STREAMLIT (UI/UX)
# ==========================================
st.title("📈 ABEL FX - Economic Calendar & AI Market Intelligence")
st.caption("Real-time Macroeconomic Event Monitor & AI Analysis for USD / XAUUSD Pairs")

tab1, tab2 = st.tabs(["📊 Kalender Ekonomi & AI Analyst", "📉 TradingView Chart & Technicals"])

with tab1:
    st.subheader("🗓️ Kalender Ekonomi Minggu Ini")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        load_btn = st.button("🔄 Reload Data Berita", use_container_width=True)
    
    df_news = fetch_economic_calendar()

    if not df_news.empty:
        st.dataframe(df_news, use_container_width=True, height=300)
        
        st.markdown("---")
        st.subheader("🤖 AI Market Analysis (Google Gemini Flash)")
        
        if st.button("🚀 Jalankan Analisis AI Terhadap Berita", type="primary"):
            with st.spinner("Gemini AI sedang menganalisis dampak makroekonomi..."):
                news_summary = df_news.to_string()
                analysis_result = analyze_news_with_gemini(news_summary)
                st.markdown(analysis_result)
    else:
        st.warning("Data berita belum dapat dimuat. Pastikan koneksi internet stabil atau coba tekan tombol reload.")

with tab2:
    st.subheader("📉 Chart Live TradingView (XAUUSD)")
    
    tradingview_widget = """
    <!-- TradingView Widget BEGIN -->
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
    <!-- TradingView Widget END -->
    """
    components.html(tradingview_widget, height=620)
