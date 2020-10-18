import re
import asyncio
from bot import dp
from bot import bot
from sqlighter import SQLighter
from rustattoo import RusTattoo
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, ContentTypes

# инициализируем соединение с БД
db = SQLighter('db.db')
# инициализируем парсер
rt = RusTattoo(db)
like = CallbackData("like", "action")


@dp.message_handler(commands=['givepost'])
async def new_post(m: Message):
    # проверяем наличие новых игр
    new_publication = rt.new_publication()
    if new_publication:
        subscriptions = db.get_subscriptions()
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.insert(InlineKeyboardButton(text="👍 0", callback_data=like.new(action=1)))
        keyboard.insert(InlineKeyboardButton(text="👎 0", callback_data=like.new(action=0)))
        # отправляем всем новость
        for s in subscriptions:
            await bot.send_photo(
                s[1],
                new_publication['url_photo'],
                caption=('[Смотреть]({0})'.format(new_publication['link'])),
                disable_notification=True,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
            # добовляем пост в базу и ставить статус, что опубликован
            db.add_publication(new_publication['id'], status=True)


# проверяем наличие новых игр и делаем рассылки
async def scheduled(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        # проверяем наличие новых игр
        new_publication = rt.new_publication()
        if new_publication:
            subscriptions = db.get_subscriptions()
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.insert(InlineKeyboardButton(text="👍 0", callback_data=like.new(action=1)))
            keyboard.insert(InlineKeyboardButton(text="👎 0", callback_data=like.new(action=0)))
            # отправляем всем новость
            for s in subscriptions:
                await bot.send_photo(
                    s[1],
                    new_publication['url_photo'],
                    caption=('[Смотреть]({0})'.format(new_publication['link'])),
                    disable_notification=True,
                    parse_mode='MarkdownV2',
                    reply_markup=keyboard
                )
                # добовляем пост в базу и ставить статус, что опубликован
                db.add_publication(new_publication['id'], status=True)


# Команда активации подписки
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: Message):
    if not db.subscriber_exists(message.from_user.id):
        # если юзера нет в базе, добавляем его
        db.add_subscriber(message.from_user.id)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, True)

    await message.answer(
        "Вы успешно подписались на рассылку!")


# Команда отписки
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: Message):
    if not db.subscriber_exists(message.from_user.id):
        # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы итак не подписаны.")
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, False)
        await message.answer("Вы успешно отписаны от рассылки.")


@dp.callback_query_handler(like.filter())
async def call(c: CallbackQuery, state: FSMContext, callback_data: dict):
    message_id = str(c.message.message_id)
    liked = int(callback_data.get("action"))

    markup = c.message.reply_markup.inline_keyboard[0]
    pos = int(re.search(r"(\d+)", markup[0]["text"])[0])
    neg = int(re.search(r"(\d+)", markup[1]["text"])[0])

    async with state.proxy() as data:
        prev_like = data.get(message_id, None)
        data[message_id] = liked
        if prev_like is not None:
            if liked and prev_like:
                pos -= 1
                await c.answer(f"Вы убрали реакцию")
                data[message_id] = None

            elif not liked and not prev_like:
                neg -= 1
                await c.answer(f"Вы убрали реакцию")
                data[message_id] = None

            elif liked:
                pos += 1
                neg -= 1
                await c.answer(f"Вам Понравилось")
            else:
                pos -= 1
                neg += 1
                await c.answer(f"Вам Не Понравилось")

        else:
            if liked:
                pos += 1
                await c.answer(f"Вам Понравилось")

            else:
                neg += 1
                await c.answer(f"Вам Не Понравилось")

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.insert(InlineKeyboardButton(text=f"👍 {pos}", callback_data=like.new(action=1)))
    keyboard.insert(InlineKeyboardButton(text=f"👎 {neg}", callback_data=like.new(action=0)))
    await c.message.edit_reply_markup(keyboard)