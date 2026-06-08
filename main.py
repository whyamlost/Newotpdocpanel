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

# Clean welcome image (professional tech background)
WELCOME_IMAGE = "https://i.imgur.com/8Z2vK8j.jpg"   # You can change this URL

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
global_markup = True

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

# ===================== START WITH IMAGE =====================
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.chat.id)
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "activations": {}}
    save_data()

    # Send clean welcome image
    try:
        bot.send_photo(msg.chat.id, WELCOME_IMAGE, caption="✅ *Simp OTP Bot Started*\n\nProfessional • Persistent • Auto Status", parse_mode="Markdown")
    except:
        bot.send_message(msg.chat.id, "✅ *Simp OTP Bot Started*")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Search Service", "💰 My Balance")
    markup.add("📱 My Numbers", "📊 My Account")
    markup.add("🔄 Auto Clicker", "❓ Help")

    bot.send_message(msg.chat.id, "Use buttons below 👇", reply_markup=markup)

# Rest of the bot (Admin commands, user commands, search, buy, etc.) remains the same as previous heavy version

# (To save space, I'm not repeating the entire code here. Keep the previous full version and only replace the /start function with the one above)

print("✅ Bot Started with Welcome Image")
bot.infinity_polling()
