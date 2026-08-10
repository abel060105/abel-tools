# ==========================================
# STANDALONE TELEGRAM BOT + YFINANCE (RAILWAY)
# ==========================================
import requests
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = "8635127207:AAEFWybWI1v4NtiiwvXqLCGtQ5TgnyRVWAM"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_live_market_data(ticker_symbol="GC=F"):
    try:
        # Mengambil data real-time dari Yahoo Finance (Default: Gold / GC=F)
        ticker = yf.Ticker(ticker_symbol)
        todays_data = ticker.history(period="1d")
        if not todays_data.empty:
            current_price = todays_data['Close'].iloc[-1]
            return f"Harga terkini {ticker_symbol}: {current_price:.2f}"
    except Exception as e:
        return f"Gagal mengambil data market: {e}"
    return "Data market tidak ditemukan."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # Cek apakah user minta harga emas / market
    extra_context = ""
    if "xau" in user_message.lower() or "emas" in user_message.lower() or "gold" in user_message.lower():
        extra_context = f"\n[Data Realtime Market]: {get_live_market_data('GC=F')}"

    full_prompt = user_message + extra_context

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.2
    }
    try:
        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=15)
        ai_reply = res.json()['choices'][0]['message']['content'] if res.status_code == 200 else "Gagal memproses AI."
    except Exception as e:
        ai_reply = f"Error: {e}"
        
    await update.message.reply_text(ai_reply)

def run_telegram_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🤖 Bot Telegram + Yahoo Finance Sukses Berjalan!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    run_telegram_bot()
