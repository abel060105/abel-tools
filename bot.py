# ==========================================
# STANDALONE TELEGRAM BOT (RUNS ON RAILWAY)
# ==========================================
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = "8635127207:AAEFWybWI1v4NtiiwvXqLCGtQ5TgnyRVWAM"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": user_message}],
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
    print("🤖 Bot Telegram Abel FX Sukses Berjalan & Siap Menerima Pesan!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    run_telegram_bot()
