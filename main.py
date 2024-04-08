from configconfig import iam_token, folder_id, bot_token
from database import insert_row, count_all_symbol
import logging
import telebot
from speechkit import tts

bot = telebot.TeleBot(token=bot_token)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)
MAX_USER_TTS_SYMBOLS = 40
MAX_TTS_SYMBOLS = 10
MAX_LEN = 30




@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f'Привет {message.from_user.first_name}, я бот который умеет озвучивать'
                                      f'текст! Как только будешь готов[а], жми команду /tts, отправляй текст'
                                      f'для озвучки и жди ответа :)')

@bot.message_handler(commands=['tts'])
def tts_handler(message):
    bot.send_message(message.chat.id, 'Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, proccess_tts)

def proccess_tts(message):
    u_id = message.chat.id
    text = message.text

    if message.content_type != 'text':
        bot.send_message(u_id, 'Отправь текстовое сообщение')
        return
    if len(text) > MAX_LEN:
        bot.send_message(u_id, 'Сообщение слишком длинное, укороти его плиз')
    # Считаем символы в тексте и проверяем сумму потраченных символов
    text_symbol = is_tts_symbol_limit(message, text)
    if text_symbol is None:
        return

    # Записываем сообщение и кол-во символов в БД
    insert_row(u_id, text, text_symbol)

    # Получаем статус и содержимое ответа от SpeechKit
    status, content = tts(text)

    # Если статус True - отправляем голосовое сообщение, иначе - сообщение об ошибке
    if status:
        bot.send_voice(u_id, content)
    else:
        bot.send_message(u_id, content)

def is_tts_symbol_limit(message, text):
    user_id = message.from_user.id
    text_symbols = len(text)

    # Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = count_all_symbol(user_id) + text_symbols

    # Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= MAX_USER_TTS_SYMBOLS:
        msg = f"Превышен общий лимит SpeechKit TTS {MAX_USER_TTS_SYMBOLS}. Использовано: {all_symbols} символов. Доступно: {MAX_USER_TTS_SYMBOLS - all_symbols}"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем количество символов в тексте с максимальным количеством символов в тексте
    if text_symbols >= MAX_TTS_SYMBOLS:
        msg = f"Превышен лимит SpeechKit TTS на запрос {MAX_TTS_SYMBOLS}, в сообщении {text_symbols} символов"
        bot.send_message(user_id, msg)
        return None
    return len(text)

if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.infinity_polling()