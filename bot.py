import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ==========================================
# KONFIGURASI API & TOKEN
# ==========================================
TELEGRAM_TOKEN = "8635127207:AAEFWybWI1v4NtiiwvXqLCGtQ5TgnyRVWAM"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==========================================
# FUNGSI INTEGRASI AI (Llama 3 / Groq)
# ==========================================
def get_ai_macro_analysis(user_query):
    system_prompt = (
        "Kamu adalah Senior Quantitative Trader & Macro Analyst spesialis XAUUSD. "
        "Berikan analisis tajam, ringkas, dan profesional mengenai kondisi makroekonomi, "
        "sentimen dolar, atau trading setup jika diminta."
    )
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"⚠️ Gagal terhubung ke AI Engine (Error Code: {response.status_code})"
    except Exception as e:
        return f"⚠️ Terjadi kesalahan koneksi: {str(e)}"

# ==========================================
# HANDLER UTAMA PESAN TELEGRAM
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Memberikan indikator status "sedang mengetik..." di Telegram
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Panggil fungsi AI untuk memproses pesan user
    ai_response = get_ai_macro_analysis(user_message)

    # Kirim balik jawaban AI ke chat Telegram
    await update.message.reply_text(ai_response)

# ==========================================
# MENJALANKAN BOT
# ==========================================
if __name__ == '__main__':
    print("🤖 Bot Telegram Abel FX sedang mencoba terhubung...")
    
    # Inisialisasi aplikasi bot telegram
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Mendaftarkan handler untuk mendeteksi pesan teks masuk
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Bot Telegram Sukses Berjalan!")
    
    # Menjalankan bot secara polling terus-menerus
    app.run_polling()
