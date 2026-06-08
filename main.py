import telebot
import requests
import time
import json
from datetime import datetime, timedelta
from telebot import types

BOT_TOKEN = "6323882775:AAHtMktiweybyV00wDs2Did1nMmhSFdHDMI"
API_KEY = "97fan9xef250tnsceje935zdqzsqbrs5"
ADMIN_ID = 5983584180

bot = telebot.TeleBot(BOT_TOKEN)
users = {}

def api_request(params):
    try:
        r = requests.get("https://otpdoctor.in/stubs/handler_api.php", params=params, timeout=15)
        return r.text.strip()
    except:
        return "❌ Connection Error"

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Search Service", "💰 My Balance")
    markup.add("📱 My Numbers")

    bot.send_message(msg.chat.id, "✅ *Simp OTP Bot Started*\nPublic Bot • +1₹ Charge", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['addbalance'])
def add_balance(msg):
    if msg.chat.id != ADMIN_ID: return
    try:
        _, uid, amt = msg.text.split()
        uid = int(uid)
        amt = float(amt)
        if uid not in users:
            users[uid] = {"balance": 0.0, "activations": {}}
        users[uid]["balance"] += amt
        bot.send_message(msg.chat.id, f"✅ Added ₹{amt} to user {uid}")
    except:
        bot.send_message(msg.chat.id, "Usage: `/addbalance <user_id> <amount>`")

@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    text = msg.text.strip().lower()
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}

    if text in ["🔍 search service", "search"]:
        bot.send_message(user_id, "Send service name like: jiomart, swiggy, blinkit")
        return

    if text == "💰 my balance":
        bal = users[user_id]["balance"]
        bot.send_message(user_id, f"💰 Balance: ₹{bal:.2f}")
        return

    if text == "📱 my numbers":
        bot.send_message(user_id, "No active numbers yet.")
        return

    bot.send_message(user_id, f"🔎 Searching {msg.text}...")
    time.sleep(2)
    resp = api_request({'action': 'getNumber', 'api_key': API_KEY, 'service': '12531', 'country': 'in'})
    bot.send_message(user_id, f"📲 Result:\n{resp}")

print("✅ Bot Started")
bot.infinity_polling()
