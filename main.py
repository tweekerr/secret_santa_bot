import json
import os
import random

import telebot
from dotenv import dotenv_values
from telebot import types
from telebot.types import Message

config = dotenv_values(".env")

debug = config["DEBUG"] == "True"
admins = config["ADMINS"].split(",")
backup_filename = config["BACKUP_FILENAME"]

bot = telebot.TeleBot(config["TELEGRAM_TOKEN"])


def is_from_admin(message: Message):
    return message.from_user.username in admins


def get_random_pairs(source: list):
    pairs = []
    clone = list(source)
    random.shuffle(clone)

    for num in source:
        if len(clone) == 1 and num == clone[0]:
            return get_random_pairs(source)
        while num == clone[0]:
            random.shuffle(clone)
        else:
            pairs.append((num, clone[0]))
            clone.pop(0)

    return pairs


def log_message(message: Message, func_name: str = None):
    if debug:
        print(f"[{func_name or 'unknown'}] Received message from " +
              f"'{message.from_user.username}' with text: '{message.text}'")


class User:
    def __init__(self, user_id: int, username: str, fullname: str):
        self.id = user_id
        self.username = username
        self.fullname = fullname
        self.awaiting_for_note = True
        self.note = "-"


is_event_started = False


def load_backup():
    if not os.path.exists(backup_filename):
        return {}
    with open(backup_filename, "r", encoding="utf8") as file:
        data = json.loads(file.read())
        db = {}
        for key, val in data.items():
            db.update({
                key: User(val["id"], val["username"], val["fullname"])
            })
        return db


database = load_backup()

if debug:
    database.update({
        # "the_best_beer_in_the_world": User(321321, "the_best_beer_in_the_world", "Honk Honk"),
        # "face_id": User(433434, "face_id", "Вася 666.1"),
        # "google": User(222222, "google", "Гугль Гром"),
        # "gool": User(434241, "gool", "Гугь Инсайд"),
        # "error_404": User(445555, "error_404", "Toloshnyi Miro"),
        # "jurilents": User(506352913, "jurilents", "Yurii"),
        "f_dana_19": User(512828062, "f_dana_19", "Богданка Фіть"),
        "vuradzu": User(302865773, "vuradzu", "tweeker"),
    })


def update_backup():
    with open(backup_filename, "w", encoding="utf8") as file:
        data = {u.username: u.__dict__ for u in database.values()}
        file.write(json.dumps(data, indent=2, ensure_ascii=False))


@bot.message_handler(commands=["start"], chat_types=["private"])
def cmd_start(message: Message):
    log_message(message, "cmd_start")
    if message.from_user.username in database.keys():
        bot.reply_to(message, "Ти вже береш участь в таємному Санті :)")
    else:
        user = User(
            message.from_user.id,
            message.from_user.username,
            ((message.from_user.first_name or "") + " " + (message.from_user.last_name or "")).strip())

        database.update({user.username: user})
        update_backup()
        bot.reply_to(message, "Привіт, тепер ти береш участь в Секретному Санті :)\n" +
                     "Якщо бажаєш, напиши мені які у тебе є побажання у наступному повідомленні і я передам їх твоєму " +
                     "Санті ;)\n\n"
                     "Якщо бажаєш, щоб Санта вибрав на свій розсуд - скинь \"-\""
                     )


@bot.message_handler(commands=["show_members"], chat_types=["private"])
def cmd_show_members(message: Message):
    log_message(message, "cmd_show_members")
    if len(database.keys()) == 0:
        bot.reply_to(message, "Поки тут порожньо...")
    else:
        text = "Список учасників:\n"
        for user in database.values():
            text += f"{user.fullname} – @{user.username}\n"
        bot.reply_to(message, text)


@bot.message_handler(commands=["remove_member"], chat_types=["private"])
def cmd_remove_member(message: Message):
    log_message(message, "cmd_remove_member")
    if not is_from_admin(message):
        return

    params = message.text.split(" ")
    if len(params) != 2:
        bot.reply_to(message, "Неправильний запит.")
    elif params[1] not in database.keys():
        bot.reply_to(message, "Такого учасника немає.")
    else:
        database.pop(params[1])
        update_backup()
        bot.reply_to(message, "Учасника видалено.")


@bot.message_handler(commands=["begin_event"], chat_types=["private"])
def cmd_begin_event(message: Message):
    log_message(message, "cmd_begin_event")
    global is_event_started
    if not is_from_admin(message):
        return
    if is_event_started:
        bot.reply_to(message, "Івент вже запущено.")
        return

    members = list(database.keys())

    if len(members) < 2:
        bot.reply_to(message, "Замало учасників для проведення івенту :(")
        return

    pairings = get_random_pairs(list(database.keys()))

    if debug:
        text = "Ок, якщо буде такий список?\n"
        for username in pairings:
            text += f"@{username[0]} дарує щось для @{username[1]}\n"
        bot.reply_to(message, text)

    for giftdiller_name, recipient_name in pairings:
        giftdiller: User = database[giftdiller_name]
        recipient: User = database[recipient_name]

        messageText = f"Гей, Санто! @{recipient_name} ({recipient.fullname}) чекає від тебе подаруночок під ялинкою ;)\n\n"

        if recipient.note != "-":
            messageText += "Орієнтир для тебе: " + recipient.note

        bot.send_message(giftdiller.id, messageText)

    is_event_started = True


@bot.message_handler(content_types=["text"], chat_types=["private"])
def txt_parse_wish(message: Message):
    log_message(message, "txt_parse_wish")
    if message.text.startswith("/"):
        return
    if message.from_user.username in database.keys():
        user = database[message.from_user.username]
        user.note = message.text
        update_backup()
        if message.text != "-":
            bot.reply_to(message,
                         f"Добре, коли буде розпочато івент, я передам твоєму Санті такий текст:\n\"{message.text}\"\n\n" +
                         f"P.S. _Якщо хочеш змінити його, відправ ще раз мені повідомлення_",
                         parse_mode="Markdown")
        else:
            bot.send_message(user.id,
                             "Якщо бажаєш змінити побажання, відправ мені ще раз повідомлення")

        bot.send_message(user.id, "Дякую, що доєднався, тепер чекай на повідомлення 🙂")
        user.awaiting_for_note = False
    else:
        cmd_start(message)


if __name__ == '__main__':
    print("Bot is starting...")
    bot.infinity_polling()
    print("Bot is stopping...")
