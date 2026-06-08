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
users = {}

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

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Search Service", "💰 My Balance")
    markup.add("📱 My Numbers", "Auto Clicker")

    bot.send_message(msg.chat.id, "✅ Bot is Live & Fixed", reply_markup=markup)

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
        bot.send_message(msg.chat.id, f"Added ₹{amt} to {uid}")
    except:
        bot.send_message(msg.chat.id, "Usage: /addbalance <user_id> <amount>")

@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    text = msg.text.strip().lower()
    user_id = msg.chat.id
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}

    if text in ["🔍 search service", "search"]:
        bot.send_message(user_id, "Type service name: jiomart, swiggy, blinkit, rapido, flipkart")
        return

    if text == "💰 my balance":
        bal = users[user_id]["balance"]
        bot.send_message(user_id, f"💰 Balance: ₹{bal:.2f}")
        return

    if text == "📱 my numbers":
        if not users[user_id]["activations"]:
            bot.send_message(user_id, "No active numbers")
            return
        for act_id, data in users[user_id]["activations"].items():
            remaining = max(0, int((data["expiry"] - datetime.now()).total_seconds() / 60))
            bot.send_message(user_id, f"Number: {data['phone']}\nID: {act_id}\nTime left: {remaining} min")
        return

    # Search
    bot.send_message(user_id, f"Searching {msg.text}...")
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
                markup.add(types.InlineKeyboardButton(f"{sid} | {info.get('service_name')} ₹{price+1}", callback_data=f"svc_{sid}"))
                found += 1
                if found >= 15: break
    except:
        pass

    if found > 0:
        bot.send_message(user_id, f"Found {found} services (+1₹)", reply_markup=markup)
    else:
        bot.send_message(user_id, "No services found. Try 'jiomart' or 'swiggy'")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if call.data.startswith("svc_"):
        service_id = call.data.split("_")[1]
        bot.send_message(user_id, "Buying number...")

        resp = api_request({'action': 'getNumber', 'api_key': API_KEY, 'service': service_id, 'country': 'in'})

        if "ACCESS_NUMBER" in resp:
            try:
                parts = resp.split(':')
                act_id = parts[1]
                phone = parts[2] if len(parts) > 2 else "N/A"

                expiry = datetime.now() + timedelta(minutes=20)
                users[user_id]["activations"][act_id] = {"phone": phone, "expiry": expiry}

                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("Copy Number", callback_data=f"copy_{phone}"),
                    types.InlineKeyboardButton("Check Status", callback_data=f"status_{act_id}")
                )
                markup.add(types.InlineKeyboardButton("Cancel", callback_data=f"cancel_{act_id}"))

                bot.send_message(user_id, f"Success\nNumber: {phone}\nID: {act_id}\n20 min", reply_markup=markup)
            except:
                bot.send_message(user_id, resp)
        else:
            bot.send_message(user_id, resp)

    elif call.data.startswith("copy_"):
        bot.send_message(user_id, call.data.split("_",1)[1])
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

print("✅ Bot Fixed & Running")
bot.infinity_polling()
