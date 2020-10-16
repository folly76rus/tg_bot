import config
import logging
import asyncio
from emoji import emojize
from aiogram import Bot, Dispatcher, executor, types
from sqlighter import SQLighter
from rustattoo import RusTattoo

# задаем уровень логов
logging.basicConfig(level=logging.INFO)

# инициализируем бота
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

# инициализируем соединение с БД
db = SQLighter('db.db')

# инициализируем парсер
rt = RusTattoo(db)


# Команда активации подписки
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его
        db.add_subscriber(message.from_user.id)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, True)

    await message.answer(
        "Вы успешно подписались на рассылку!")


# Команда отписки
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы итак не подписаны.")
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, False)
        await message.answer("Вы успешно отписаны от рассылки.")


# проверяем наличие новых игр и делаем рассылки
async def scheduled(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        # проверяем наличие новых игр
        new_publication = rt.new_publication()
        if new_publication:
            subscriptions = db.get_subscriptions()
            like_keyboard = types.InlineKeyboardMarkup().row(
                types.InlineKeyboardButton(f"👍 {new_publication['like']}", callback_data=1),
                types.InlineKeyboardButton(f"👎 {new_publication['dislike']}", callback_data=-1)
            )
            # отправляем всем новость
            for s in subscriptions:
                await bot.send_photo(
                    s[1],
                    new_publication['url_photo'],
                    caption=('[Смотреть]({0})'.format(new_publication['link'])),
                    disable_notification=True,
                    parse_mode='MarkdownV2',
                    reply_markup=like_keyboard
                )
                # обновляем ключ
                db.add_publication(new_publication['id'], status=True)
                # db.update_file_id_publication(new_publication['id'], msg['photo'][0]['file_id'])

# запускаем лонг поллинг
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled(10))  # пока что оставим 10 секунд (в качестве теста)
    executor.start_polling(dp, skip_updates=True)
