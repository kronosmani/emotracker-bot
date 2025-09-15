import telebot
import os

# 🔐 Вставь сюда токен своего Telegram-бота от BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_БОТА"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👋 Привет! Это эмоциональный трекер для родителей.\n\nЧтобы получить файл, сначала оплатите по ссылке: /buy")

@bot.message_handler(commands=['buy'])
def send_payment_link(message):
    bot.send_message(message.chat.id,
        "💳 Оплата через ПриватБанк:\nhttps://www.privat24.ua/send/3g1gh\n\nПосле оплаты нажмите /getfile")

@bot.message_handler(commands=['getfile'])
def send_file(message):
    try:
        with open("ilovepdf_merged.pdf", "rb") as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при отправке файла: {e}")

bot.polling(non_stop=True)

