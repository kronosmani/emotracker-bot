import os
import json
import base64
import hashlib
from flask import Flask, request
import telebot

# 🔐 Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
paid_users = set()

# 📦 Генерация ссылки на оплату
def create_payment_link(telegram_id):
    data = {
        "version": "3",
        "action": "pay",
        "amount": "1",
        "currency": "UAH",
        "description": "Тестова оплата Emotracker",
        "order_id": str(telegram_id),
        "sandbox": 1,
        "server_url": "https://emotracker-bot.onrender.com/liqpay",
        "public_key": LIQPAY_PUBLIC_KEY
    }

    json_data = json.dumps(data)
    encoded_data = base64.b64encode(json_data.encode()).decode()
    sign_string = LIQPAY_PRIVATE_KEY + encoded_data + LIQPAY_PRIVATE_KEY
    signature = base64.b64encode(hashlib.sha1(sign_string.encode()).digest()).decode()

    return f"https://www.liqpay.ua/api/3/checkout?data={encoded_data}&signature={signature}"

# 💬 Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👋 Привет! Это Emotracker.\nНажмите /buy, чтобы оплатить и получить файл.")

# 💳 Команда /buy
@bot.message_handler(commands=['buy'])
def send_payment_link(message):
    telegram_id = message.chat.id
    payment_url = create_payment_link(telegram_id)
    bot.send_message(telegram_id,
        f"💳 Оплата через LiqPay:\n{payment_url}\n\nПосле оплаты бот автоматически отправит вам файл.")

# 📁 Команда /getfile
@bot.message_handler(commands=['getfile'])
def send_file(message):
    user_id = message.chat.id
    if user_id in paid_users:
        try:
            with open("ilovepdf_merged.pdf", "rb") as f:
                bot.send_document(user_id, f)
        except Exception as e:
            bot.send_message(user_id, f"⚠️ Ошибка при отправке файла: {e}")
    else:
        bot.send_message(user_id,
            "💡 Похоже, вы ещё не оплатили. Нажмите /buy, чтобы оплатить.")

# 🔁 Webhook от LiqPay
@app.route('/liqpay', methods=['POST'])
def liqpay_webhook():
    data = request.json
    print("Webhook от LiqPay:", data)

    if data.get("status") == "success":
        telegram_id = int(data.get("order_id"))
        paid_users.add(telegram_id)

        bot.send_message(telegram_id, "✅ Оплата получена! Вот ваш файл:")
        try:
            with open("ilovepdf_merged.pdf", "rb") as f:
                bot.send_document(telegram_id, f)
        except Exception as e:
            bot.send_message(telegram_id, f"⚠️ Ошибка при отправке файла: {e}")

    return "OK", 200

# 📥 Webhook от Telegram
@app.route('/', methods=['POST'])
def telegram_webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# 🌐 Проверка сервера
@app.route('/', methods=['GET'])
def index():
    return "Бот работает", 200

# 🚀 Установка webhook при запуске
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url="https://emotracker-bot.onrender.com")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
