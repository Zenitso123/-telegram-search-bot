from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup
import os

# Bot token
TOKEN = "7179539970:AAGRUIV32K6jNBBNRQ8zadrROOdTH4Uvcjs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('سلام! من یک ربات جستجوگر هستم. کلمه یا عبارت مورد نظر خود را ارسال کنید.')

async def search_google(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text
    await update.message.reply_text("🔍 در حال جستجو...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
        }
        response = requests.get(
            'https://www.google.com/search',
            params={'q': query},
            headers=headers
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for g in soup.find_all('a'):
            if '/url?q=' in str(g.get('href', '')):
                link = g.get('href').split('/url?q=')[1].split('&')[0]
                if 'google.com' not in link and 'youtube.com' not in link:
                    results.append(link)
        
        if results:
            message = "🔍 نتایج جستجو:\n\n"
            for i, url in enumerate(results[:5], 1):
                message += f"{i}. {url}\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ متأسفانه نتیجه‌ای پیدا نشد.")
    
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ خطا در جستجو. لطفاً دوباره تلاش کنید.")

def main():
    # Create application
    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_google))

    # Start bot
    print("🤖 ربات شروع به کار کرد...")
    app.run_polling()

if __name__ == '__main__':
    main()
