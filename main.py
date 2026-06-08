import telebot
import requests
import time
import json
import os
from datetime import datetime, timedelta
from telebot import types
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== CONFIG ==================
BOT_TOKEN = "6323882775:AAHtMktiweybyV00wDs2Did1nMmhSFdHDMI"
API_KEY = "97fan9xef250tnsceje935zdqzsqbrs5"
ADMIN_ID = 5983584180
DATA_FILE = "users.json"

bot = telebot.TeleBot(BOT_TOKEN)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2, default=str)

users = load_data()
global_markup = True  # +1₹ enabled by default

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

Thread(target=lambda: HTTPServer(("0.0.0.0", 8080), HealthHandler).serve_forever(), daemon=True).start()

def api_request(params):
    try:
        r = requests.get("https://otpdoctor.in/stubs/handler_api.php", params=params, timeout=15)
        return r.text.strip()
    except:
        return "Connection Error"

def is_admin(user_id):
    return user_id == ADMIN_ID

# ===================== START =====================
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.chat.id)
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}
    save_data()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Search Service", "💰 My Balance")
    markup.add("📱 My Numbers", "📊 My Account")
    markup.add("🔄 Auto Clicker", "❓ Help")

    bot.send_message(msg.chat.id, "✅ *Simp OTP Bot Started*", parse_mode="Markdown", reply_markup=markup)

# ===================== ADMIN =====================
@bot.message_handler(commands=['addbalance'])
def add_balance(msg):
    if not is_admin(msg.chat.id): return
    try:
        _, target_id, amount = msg.text.split()
        target_id = str(target_id)
        amount = float(amount)
        if target_id not in users:
            users[target_id] = {"balance": 0.0, "activations": {}}
        users[target_id]["balance"] += amount
        save_data()
        bot.send_message(msg.chat.id, f"✅ Added ₹{amount} to user {target_id}")
        try:
            bot.send_message(int(target_id), f"💰 Admin added ₹{amount} to your balance!")
        except:
            pass
    except:
        bot.send_message(msg.chat.id, "Usage: `/addbalance <user_id> <amount>`")

@bot.message_handler(commands=['stats'])
def admin_stats(msg):
    if not is_admin(msg.chat.id): return
    total_users = len(users)
    total_balance = sum(u.get("balance", 0) for u in users.values())
    active_total = sum(len(u.get("activations", {})) for u in users.values())

    text = f"📊 *Bot Stats*\n\n"
    text += f"Total Users: `{total_users}`\n"
    text += f"Total Balance: `₹{total_balance:.2f}`\n"
    text += f"Active Numbers: `{active_total}`\n\n"

    for uid, data in list(users.items()):
        bal = data.get("balance", 0)
        acts = data.get("activations", {})
        text += f"👤 User `{uid}`\n   Balance: `₹{bal:.2f}`\n"
        if acts:
            for act_id, act in acts.items():
                remaining = max(0, int((act["expiry"] - datetime.now()).total_seconds() / 60))
                text += f"   📱 {act.get('phone', 'N/A')} (ID: {act_id}) - {remaining} min\n"
        text += "\n"

    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

# ===================== USER =====================
@bot.message_handler(func=lambda m: m.text in ["💰 My Balance", "my balance"])
def my_balance(msg):
    user_id = str(msg.chat.id)
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}
    bal = users[user_id]["balance"]
    bot.send_message(msg.chat.id, f"💰 *Your Balance*\n`₹{bal:.2f}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in ["📱 My Numbers", "my numbers"])
def my_numbers(msg):
    user_id = str(msg.chat.id)
    if user_id not in users or not users[user_id]["activations"]:
        bot.send_message(msg.chat.id, "❌ No active numbers.")
        return
    for act_id, data in users[user_id]["activations"].items():
        remaining = max(0, int((data["expiry"] - datetime.now()).total_seconds() / 60))
        bot.send_message(msg.chat.id, f"📱 `{data['phone']}`\n🆔 `{act_id}`\n⏳ {remaining} min left", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in ["📊 My Account", "my account"])
def my_account(msg):
    user_id = str(msg.chat.id)
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}
    bal = users[user_id]["balance"]
    active = len(users[user_id]["activations"])
    bot.send_message(msg.chat.id, f"📊 *Your Account*\nBalance: `₹{bal:.2f}`\nActive Numbers: `{active}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in ["❓ Help", "help"])
def help_cmd(msg):
    bot.send_message(msg.chat.id, 
        "❓ *Help*\n\n"
        "• Search Service → Type service name\n"
        "• Tap service to buy number\n"
        "• Use Copy / Status / Cancel buttons\n\n"
        "Developer: @Osamabinladennnnnn", parse_mode="Markdown")

# ===================== SEARCH =====================
@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    text = msg.text.strip().lower()
    user_id = str(msg.chat.id)
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}

    if text in ["🔍 search service", "search"]:
        bot.send_message(msg.chat.id, "Send service name like: jiomart, swiggy, blinkit, rapido, flipkart")
        return

    if text == "💰 my balance":
        my_balance(msg)
        return

    if text == "📱 my numbers":
        my_numbers(msg)
        return

    if text == "📊 my account":
        my_account(msg)
        return

    bot.send_chat_action(msg.chat.id, 'typing')
    bot.send_message(msg.chat.id, f"🔎 Searching for *{msg.text}*...")

    resp = api_request({'action': 'getServices', 'api_key': API_KEY, 'country': 'in'})

    markup = types.InlineKeyboardMarkup(row_width=1)
    found = 0
    try:
        services = json.loads(resp)
        term = text
        for sid, info in services.items():
            name = info.get("service_name", "").lower()
            if term in name or term in str(sid):
                price = float(info.get("service_price", 0))
                final_price = price + 1 if global_markup else price
                markup.add(types.InlineKeyboardButton(f"✅ {sid} | {info.get('service_name')} ₹{final_price}", callback_data=f"svc_{sid}"))
                found += 1
                if found >= 20: break
    except:
        pass

    if found > 0:
        bot.send_message(msg.chat.id, f"✅ Found {found} services (+1₹ extra)", parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(msg.chat.id, "❌ No services found. Try `jiomart` or `swiggy`")

# ===================== BUY =====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = str(call.message.chat.id)
    bot.answer_callback_query(call.id)

    if call.data.startswith("svc_"):
        service_id = call.data.split("_")[1]

        if not is_admin(int(user_id)):
            if users[user_id]["balance"] < 11:
                bot.send_message(int(user_id), "❌ Insufficient balance.")
                return

        bot.send_chat_action(int(user_id), 'typing')

        resp = api_request({'action': 'getNumber', 'api_key': API_KEY, 'service': service_id, 'country': 'in'})

        if "ACCESS_NUMBER" in resp:
            try:
                parts = resp.split(':')
                act_id = parts[1]
                phone = parts[2] if len(parts) > 2 else "N/A"

                expiry = datetime.now() + timedelta(minutes=20)
                users[user_id]["activations"][act_id] = {"phone": phone, "expiry": expiry}

                if not is_admin(int(user_id)):
                    users[user_id]["balance"] -= 11 if global_markup else 0

                save_data()

                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("📋 Copy Number", callback_data=f"copy_{phone}"),
                    types.InlineKeyboardButton("🔄 Check Status", callback_data=f"status_{act_id}")
                )
                markup.add(types.InlineKeyboardButton("❌ Cancel Activation", callback_data=f"cancel_{act_id}"))

                bot.send_message(int(user_id), 
                    f"✅ *Number Purchased!*\n\n"
                    f"📱 `{phone}`\n"
                    f"🆔 `{act_id}`\n"
                    f"⏳ 20 minutes left", 
                    parse_mode="Markdown", reply_markup=markup)
            except:
                bot.send_message(int(user_id), f"`{resp}`", parse_mode="Markdown")
        else:
            bot.send_message(int(user_id), f"`{resp}`", parse_mode="Markdown")

    elif call.data.startswith("copy_"):
        bot.send_message(int(user_id), f"`{call.data.split('_',1)[1]}`", parse_mode="Markdown")
    elif call.data.startswith("status_"):
        act_id = call.data.split("_")[1]
        resp = api_request({'action': 'getStatus', 'api_key': API_KEY, 'id': act_id})
        bot.send_message(int(user_id), f"📌 Status:\n`{resp}`", parse_mode="Markdown")
    elif call.data.startswith("cancel_"):
        act_id = call.data.split("_")[1]
        resp = api_request({'action': 'setStatus', 'api_key': API_KEY, 'id': act_id, 'status': 8})
        bot.send_message(int(user_id), f"❌ Cancelled:\n`{resp}`", parse_mode="Markdown")
        if user_id in users and act_id in users[user_id]["activations"]:
            del users[user_id]["activations"][act_id]
            save_data()

print("✅ Heavy Version with All Fixes Started")
bot.infinity_polling()
