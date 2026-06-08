import telebot
import requests
import time
import json
from datetime import datetime, timedelta
from telebot import types
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = "6323882775:AAHtMktiweybyV00wDs2Did1nMmhSFdHDMI"
API_KEY = "97fan9xef250tnsceje935zdqzsqbrs5"
ADMIN_ID = 5983584180

bot = telebot.TeleBot(BOT_TOKEN)
users = {}   # {user_id: {"balance": float, "activations": dict}}

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

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Search Service", "My Balance")
    markup.add("My Numbers", "My Account")
    markup.add("Auto Clicker", "Help")

    bot.send_message(msg.chat.id, 
        "Simp OTP Bot Started\nClean & Professional Version", 
        reply_markup=markup)

# ===================== ADMIN ONLY =====================
@bot.message_handler(commands=['addbalance'])
def add_balance(msg):
    if not is_admin(msg.chat.id):
        return
    try:
        _, target_id, amount = msg.text.split()
        target_id = int(target_id)
        amount = float(amount)
        if target_id not in users:
            users[target_id] = {"balance": 0.0, "activations": {}}
        users[target_id]["balance"] += amount
        bot.send_message(msg.chat.id, f"Added {amount} to user {target_id}")
        try:
            bot.send_message(target_id, f"Admin added {amount} to your balance")
        except:
            pass
    except:
        bot.send_message(msg.chat.id, "Usage: /addbalance <user_id> <amount>")

# ===================== USER COMMANDS =====================
@bot.message_handler(func=lambda m: m.text in ["My Balance", "my balance"])
def show_balance(msg):
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}
    bal = users[user_id]["balance"]
    bot.send_message(user_id, f"Your Balance: {bal:.2f}")

@bot.message_handler(func=lambda m: m.text in ["My Numbers", "my numbers"])
def show_numbers(msg):
    user_id = msg.chat.id
    if user_id not in users or not users[user_id]["activations"]:
        bot.send_message(user_id, "No active numbers")
        return
    for act_id, data in users[user_id]["activations"].items():
        remaining = max(0, int((data["expiry"] - datetime.now()).total_seconds() / 60))
        bot.send_message(user_id, f"Number: {data['phone']}\nID: {act_id}\nTime left: {remaining} min")

@bot.message_handler(func=lambda m: m.text in ["My Account", "my account"])
def dashboard(msg):
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}
    bal = users[user_id]["balance"]
    active = len(users[user_id]["activations"])
    bot.send_message(user_id, f"Account Dashboard\nBalance: {bal:.2f}\nActive Numbers: {active}")

@bot.message_handler(func=lambda m: m.text in ["Help", "help"])
def help_cmd(msg):
    bot.send_message(msg.chat.id, 
        "How to use:\n1. Tap Search Service\n2. Type service name (jiomart, swiggy, etc)\n3. Tap on service to buy\n4. Use Copy / Status / Cancel buttons")

# ===================== SEARCH =====================
@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    text = msg.text.strip().lower()
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}

    if text in ["search service", "search"]:
        bot.send_message(user_id, "Send service name (jiomart, swiggy, blinkit, rapido)")
        return

    bot.send_chat_action(user_id, 'typing')
    bot.send_message(user_id, f"Searching for {msg.text}...")

    resp = api_request({'action': 'getServices', 'api_key': API_KEY, 'country': 'in'})

    markup = types.InlineKeyboardMarkup(row_width=1)
    found = 0
    try:
        services = json.loads(resp)
        for sid, info in services.items():
            name = info.get("service_name", "").lower()
            if text in name or text in str(sid):
                price = float(info.get("service_price", 0))
                markup.add(types.InlineKeyboardButton(f"{sid} | {info.get('service_name')} - {price+1}", callback_data=f"svc_{sid}"))
                found += 1
                if found >= 15: break
    except:
        pass

    if found > 0:
        bot.send_message(user_id, f"Found {found} services", reply_markup=markup)
    else:
        bot.send_message(user_id, "No services found. Try jiomart or swiggy")

# ===================== BUY + AUTO RETRY =====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if call.data.startswith("svc_"):
        service_id = call.data.split("_")[1]

        # Check balance for normal users
        if not is_admin(user_id):
            if users[user_id]["balance"] < 11:   # 10 + 1 charge
                bot.send_message(user_id, "Insufficient balance. Ask admin to add funds.")
                return

        bot.send_chat_action(user_id, 'typing')

        # Smart Auto Retry
        for attempt in range(1, 13):
            resp = api_request({'action': 'getNumber', 'api_key': API_KEY, 'service': service_id, 'country': 'in'})
            if "ACCESS_NUMBER" in resp:
                break
            time.sleep(3 + attempt)

        if "ACCESS_NUMBER" in resp:
            try:
                parts = resp.split(':')
                act_id = parts[1]
                phone = parts[2] if len(parts) > 2 else "N/A"

                expiry = datetime.now() + timedelta(minutes=20)
                users[user_id]["activations"][act_id] = {"phone": phone, "expiry": expiry}

                # Deduct balance only for normal users
                if not is_admin(user_id):
                    users[user_id]["balance"] -= 11

                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("Copy Number", callback_data=f"copy_{phone}"),
                    types.InlineKeyboardButton("Check Status", callback_data=f"status_{act_id}")
                )
                markup.add(types.InlineKeyboardButton("Cancel Activation", callback_data=f"cancel_{act_id}"))

                bot.send_message(user_id, 
                    f"Success\nNumber: {phone}\nID: {act_id}\nTime left: 20 min", 
                    reply_markup=markup)
            except:
                bot.send_message(user_id, resp)
        else:
            bot.send_message(user_id, resp)

    elif call.data.startswith("copy_"):
        bot.send_message(user_id, call.data.split("_", 1)[1])

    elif call.data.startswith("status_"):
        act_id = call.data.split("_")[1]
        resp = api_request({'action': 'getStatus', 'api_key': API_KEY, 'id': act_id})
        bot.send_message(user_id, f"Status: {resp}")

    elif call.data.startswith("cancel_"):
        act_id = call.data.split("_")[1]
        resp = api_request({'action': 'setStatus', 'api_key': API_KEY, 'id': act_id, 'status': 8})
        bot.send_message(user_id, f"Cancelled: {resp}")
        if user_id in users and act_id in users[user_id]["activations"]:
            del users[user_id]["activations"][act_id]

print("Heavy Professional Version Started")
bot.infinity_polling()
