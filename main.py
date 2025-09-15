import os
import json
import base64
import hashlib
from flask import Flask, request
import telebot
from threading import Thread

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
        "server_url": "https://emotracker-bot.onrender.com/webhook"
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
        "👋 Привет! Это эмоциональный трекер.\nНажмите /buy, чтобы оплатить и получить файл.")

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
@app.route('/webhook', methods=['POST'])
def liqpay_webhook():
    data = request.json
    print("Webhook получен:", data)

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

# 🌐 Проверка сервера
@app.route('/')
def index():
    return "Бот работает", 200

# 🚀 Запуск
if __name__ == '__main__':
    Thread(target=lambda: bot.polling(non_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
