import telebot
import os
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_БОТА"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Хранилище оплативших пользователей
paid_users = set()

@app.route('/')
def index():
    return "Бот работает", 200

@app.route('/webhook', methods=['POST'])
def liqpay_webhook():
    data = request.json
    print("Получен webhook:", data)

    # Проверка успешной оплаты
    if data.get("status") == "success":
        telegram_id = int(data.get("order_id"))
        paid_users.add(telegram_id)

        bot.send_message(telegram_id, "✅ Оплата получена! Вот ваш файл:")
        with open("emotracker_prompt.pdf", "rb") as f:
            bot.send_document(telegram_id, f)

    return "OK", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👋 Привет! Это эмоциональный трекер для родителей.\n\nЧтобы получить файл, сначала оплатите по ссылке: /buy")

@bot.message_handler(commands=['buy'])
def send_payment_link(message):
    telegram_id = message.chat.id
    # Ссылка на оплату с order_id = telegram_id
    payment_url = f"https://www.liqpay.ua/api/3/checkout?order_id={telegram_id}"
    bot.send_message(telegram_id,
        f"💳 Оплата через LiqPay:\n{payment_url}\n\nПосле оплаты файл будет отправлен автоматически.")

@bot.message_handler(commands=['getfile'])
def send_file(message):
    user_id = message.chat.id
    if user_id in paid_users:
        with open("ilovepdf_merged.pdf", "rb") as f:
            bot.send_document(user_id, f)
    else:
        bot.send_message(user_id,
            "💡 Похоже, вы ещё не оплатили.\nПожалуйста, перейдите по ссылке /buy и завершите оплату.")

# Запуск Flask-сервера и Telegram-бота
if __name__ == '__main__':
    from threading import Thread
    Thread(target=lambda: bot.polling(non_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
