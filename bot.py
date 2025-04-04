import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup
import urllib.parse
import random
import time
import os
from flask import Flask

# تنظیم کدگذاری به UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# تنظیم لاگر
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding='utf-8',
    filename='bot.log'  # ذخیره لاگ‌ها در فایل
)
logger = logging.getLogger(__name__)

# توکن ربات
TOKEN = "7179539970:AAGRUIV32K6jNBBNRQ8zadrROOdTH4Uvcjs"

# لیست User-Agent های مختلف
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

# Create Flask app for health check
app = Flask(__name__)

@app.route('/')
def health_check():
    return 'Bot is running!'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    try:
        await update.message.reply_text(
            "👋 سلام! به ربات جستجوگر خوش آمدید!\n\n"
            "برای جستجو، کافیست کلمه مورد نظر خود را تایپ کنید.\n"
            "من نتایج جستجو را از گوگل و داک‌داک‌گو برای شما پیدا می‌کنم."
        )
        logger.info(f"User {update.effective_user.id} started the bot")
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text("متأسفانه در اجرای دستور مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

async def search_google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجو در گوگل"""
    try:
        query = update.message.text
        await update.message.reply_text("🔍 در حال جستجو...")
        
        # انتخاب یک User-Agent تصادفی
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # ساخت URL جستجو
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        # ارسال درخواست به گوگل
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # پارس کردن نتایج
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = []
        
        # پیدا کردن لینک‌های نتایج
        for result in soup.select('div.g'):
            link = result.find('a')
            if link and link.get('href'):
                url = link['href']
                if url.startswith('/url?q='):
                    url = url.split('/url?q=')[1].split('&')[0]
                if url.startswith('http'):
                    search_results.append(url)
        
        if search_results:
            # ارسال نتایج
            message = "🔍 نتایج جستجو:\n\n"
            for i, url in enumerate(search_results[:5], 1):
                message += f"{i}. {url}\n"
            await update.message.reply_text(message)
            logger.info(f"Search successful for query: {query}")
        else:
            # اگر نتیجه پیدا نشد، از DuckDuckGo استفاده کن
            duck_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            response = requests.get(duck_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.select('.result__url')
            
            if results:
                message = "🔍 نتایج جستجو از DuckDuckGo:\n\n"
                for i, result in enumerate(results[:5], 1):
                    url = result.get('href', '')
                    if url.startswith('/'):
                        url = 'https://' + url.lstrip('/')
                    message += f"{i}. {url}\n"
                await update.message.reply_text(message)
                logger.info(f"DuckDuckGo search successful for query: {query}")
            else:
                await update.message.reply_text("❌ متأسفانه هیچ نتیجه‌ای پیدا نشد. لطفاً کلمه دیگری را امتحان کنید.")
                logger.warning(f"No results found for query: {query}")
        
        # تأخیر بین درخواست‌ها
        time.sleep(2)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        await update.message.reply_text("❌ خطا در ارتباط با سرور. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        await update.message.reply_text("❌ متأسفانه در جستجو مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت خطاها"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )

def main():
    """راه‌اندازی ربات"""
    try:
        # ایجاد برنامه
        application = Application.builder().token(TOKEN).build()
        
        # اضافه کردن هندلرها
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_google))
        
        # اضافه کردن هندلر خطا
        application.add_error_handler(error_handler)
        
        # شروع ربات
        print("🤖 ربات شروع به کار کرد...")
        logger.info("Bot started successfully")
        
        # اجرای ربات
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"❌ خطا در راه‌اندازی ربات: {str(e)}")

if __name__ == '__main__':
    main()
