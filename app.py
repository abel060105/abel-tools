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

DEEPSEEK_API_KEY = "sk-0447faee1bc448eb9ebf40f0c05fe9e6"  # Masukkan API Key DeepSeek kamu di sini

# ==========================================
# 2. FUNGSI UTAMA (FETCH NEWS & AI ANALYZER)
# ==========================================
def fetch_economic_calendar():
    """Mengambil data berita/kalender ekonomi dari Forex Factory API gratis"""
    url = "https://nfp.ourfx.workers.dev/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal mengambil data kalender ekonomi: {e}")
        return pd.DataFrame()

def analyze_news_with_deepseek(news_text):
    """Mengirim data berita ke DeepSeek API untuk analisis sentimen & dampaknya terhadap USD/XAUUSD"""
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "sk-0447faee1bc448eb9ebf40f0c05fe9e6":
        return "⚠️ Silakan masukkan DeepSeek API Key yang valid pada variabel DEEPSEEK_API_KEY."

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Kamu adalah seorang Senior Macroeconomic Analyst & Quantitative Trader berpengalaman di pasar Forex & Gold (XAU/USD).
    Analisis data kalender ekonomi berikut:

    {news_text}

    Berikan analisis terstruktur dalam Bahasa Indonesia dengan format berikut:
    1. **Ringkasan Eksekutif**: Rangkuman singkat dampak berita terhadap fundamental pasar.
    2. **Sentimen USD**: (Bullish / Bearish / Netral) beserta alasan singkat berdasarkan data Actual vs Forecast.
    3. **Proyeksi Dampak pada Gold (XAU/USD)**: Potensi pergerakan harga Gold (Skenario Naik/Turun/Sideways).
    4. **Trading Bias & Rekomendasi Action**: Bias harian (Long/Short) dan area pertimbangan entry/risk management.
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Kamu adalah analis pasar makroekonomi terkemuka yang presisi dan analitis."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"❌ Gagal memproses AI: Error Code {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Gagal menghubungi DeepSeek API: {e}"

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
        st.subheader("🤖 AI Market Analysis (DeepSeek V3)")
        
        if st.button("🚀 Jalankan Analisis AI Terhadap Berita", type="primary"):
            with st.spinner("DeepSeek AI sedang menganalisis dampak makroekonomi..."):
                news_summary = df_news.to_string()
                analysis_result = analyze_news_with_deepseek(news_summary)
                st.markdown(analysis_result)
    else:
        st.warning("Data berita belum dapat dimuat. Pastikan koneksi internet stabil atau coba tekan tombol reload.")

with tab2:
    st.subheader("📉 Chart Live TradingView (XAUUSD)")
    
    # Widget Live TradingView HTML
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
