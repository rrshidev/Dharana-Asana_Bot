# Задаём UTC-8 шифрацию
# -*- coding: utf-8 -*-
# Импортируем всё, что только можно
import logging
import os
import random
from os import listdir
from os.path import join, isfile

from aiogram import Bot, Dispatcher, executor, types
from config import Token
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# хз чё тут, походу из конфиг файла логируем бот-токен
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# включаем бот-токен и диспетчер
bot = Bot(token=Token)
dp = Dispatcher(bot)

directory = '/root/asana_bot/Arunodaya/bot_data/catalog/'
directory_2 = '/root/asana_bot/Arunodaya/bot_data/basics/'
directory_3 = '/root/asana_bot/Arunodaya/bot_data/steps/'
asana_types = [item for item in listdir(directory) if not isfile(join(directory, item))]
asana_types_random = [item for item in listdir(directory) if isfile(join(directory, item))]
asana_list = []
asana_data = {}

# basics and step list's for work

basics_types = []
basics_types1 = [item for item in listdir(directory_2) if isfile(join(directory_2, item))]
for basic in basics_types1:
    basic = basic[:-4:]
    basics_types.append(basic)
basics_types = list(set(basics_types))
basics_types.sort()

steps_types = []
steps_types1 = [item for item in listdir(directory_3) if isfile(join(directory_3, item))]
for step in steps_types1:
    step = step[:-4:]
    steps_types.append(step)
steps_types.sort()


# list of asanas for random.choice

random_asana_list = []

# string with asana from random_asana_lift after random.choice()

randomize_asana = ''

for asana_type in asana_types:

    # get only files

    file_list = [os.path.splitext(item)[0] for item in listdir(os.path.join(directory, asana_type)) if isfile(join(directory, asana_type, item))]

    # remove duplicates

    file_list = list(set(file_list))
    asana_data[asana_type] = file_list
    asana_list.extend(file_list)

directory1 = ''

for i in asana_types:
    directory1 = directory + i
    l = [os.path.splitext(item)[0] for item in listdir(os.path.join(directory1)) if isfile(join(directory1, item))]
    l = list(set(l))
    random_asana_list.append(l)
    directory1 = ''

# TODO: change this approach
asana_types_description = {
    'sit_lie': ['Асаны сидя и лёжа', 'Список асан сидя и лёжа'],
    'stay': ['Асаны стоя', 'Список асан стоя'],
    'hand': ['Балансы на руках', 'Список балансов на руках'],
    'coup': ['Перевёрнутые асаны', 'Список перевернутых асан'],
    'sag': ['Прогибы', 'Список асан с прогибами'],
    'power': ['Силовые асаны', 'Список силовых асан'],
}

# Menu of asana's

main_markup = InlineKeyboardMarkup() \
    .add(InlineKeyboardButton('!Каталог асан!', callback_data='catalog'))\
    .add(InlineKeyboardButton('Основы йоги', callback_data='basics'))\
    .add(InlineKeyboardButton('8 ступеней йоги', callback_data='steps'))\
    .add(InlineKeyboardButton('Асана дня, согласно карме', callback_data='random_asana'))

menu_keyboard = InlineKeyboardMarkup()
for asana_type in asana_types:
    menu_keyboard.add(InlineKeyboardButton(asana_types_description[asana_type][0], callback_data=asana_type))

menu_basics_keyboard = InlineKeyboardMarkup()
for basic in basics_types:
    menu_basics_keyboard.add(InlineKeyboardButton(basic, callback_data=basic))

menu_steps_keyboard = InlineKeyboardMarkup()
for step in steps_types:
    menu_steps_keyboard.add(InlineKeyboardButton(step, callback_data=step))


# START command
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Намаскар!\nЭто YogaBot - энциклопедия йогических асан!\nВведи название асаны на русском языке, например: бакасана или адхо мукха шванасана!\n\nЕсли не знаешь названий асан, воспользуйся удобным Каталогом асан, где все позы классифицированы по разделам.\n\nНайди нужное название асаны и нажми на кнопку с ним!",
        reply_markup=main_markup)


# HELP command
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.reply(
        'Напиши название асаны и получишь её описание и фото\n\n Если не знаешь названий асан, воспользуйся удобным Каталогом асан, где все позы классифицированы по разделам. Жми на кнопку с названием и получишь полное описание и отстройку асаны. А также качественное фото с ней!\nОчисти свою карму, выполнив Асану дня!🧘🤸‍♂️🙏\n\nСписок команд бота:\n\n----> /start 🚀 - Активация YogaBot\n----> /info - Полезная информация об асанах ❓❗️\n----> /about_us - об авторах и реализаторах проекта',
        reply_markup=main_markup)

# WHAT command

@dp.message_handler(commands=['what'])
async def what_command(message: types.Message):
    await message.reply(
        '✅Бот содержит более 100 асан йоги.\n\n Для их поиска перейди в раздел «!Каталог асан!», выбери интересующий, в котором асаны удобно классифицированы, найди в нем нужную из предложенных и нажми соответсвующую кнопку🟢 \nЕсли знаешь название асаны , то введи его на русском языке, например: Бакасана или Адхо мукха шванасана!⌨️ \n\n✅Бот содержит все основные базовые понятия йоги в разделах «Основы йоги» и «8 ступеней йоги». Выбери интересующий раздел, найди в нем нужную тему, нажми соответствующую кнопку 🟢 и получи его описание.', reply_markup=main_markup)


# Info command
@dp.message_handler(commands=['info'])
async def help_command(message: types.Message):
    await message.reply(
        'Асана - статичная поза, разработанная древними мудрецами таким образом, чтобы оказвать определённое воздествие на разум.\nПосредством растягивания-сжимания, скручивания физического тела, и используя метод диафрагмального дыхания во время упражнений, происходит благоприятное воздействие на эндокринную систему желез внутренней секреции человека. Что положительным образом сказывается на состоянии психики. И ментального здоровья человека в целом.\nДалее оздоровлённая психика и подготовленное тело служат инструментом для познания главного объекта в медитации.\nДуха. Высшего сознания. Истины. Бога. Творца.\n\n\nТаким образом, асана - не является самостоятельной дисциплиной или отдельной йогой. Асана является подготовительной практикой, призванной подготовить разум и тело к медитации.\n\n\nБот носит информативный характер. Не выполняйте асаны самостоятельно, если имеете хронические заболевания, психические отклонения. Рекомеднуется осваивать этот раздел йоги с опытным наставником. Обязательно выполняйте разминку перед началом практики.',
        reply_markup=main_markup)


# About_us command
@dp.message_handler(commands=['about_us'])
async def help_command(message: types.Message):
    await message.reply(
        'Арунодая - старший программист(кодревью, рефакторинг, кодинг, мудрые советы). Йогин! --> @Arun0daya \n\nОлег - автор проекта online-школы йоги Dharana.ru, частью которого является этот бот(Фото, описание, идеи, маркетинг). Йогин!--> @yogaolleg \nwww.instagram.com/yogaolleg/ \n\nРишидэв - автор бота, идейный вдохновитель проекта online-школы йоги Dharana.ru. Младший программист(кодинг, асаны). Йогин! --> @RrshiDev',
        reply_markup=main_markup)


# Print txt & photo of asana
@dp.message_handler()
async def echo(message: types.Message):
    x = message.text
    x = x.title()
    if x in asana_list:
        await replay_with_asana_data(x, message, message.from_user.id)
    else:
        await message.answer('Проверь название или воспользуйся каталогом асан!', reply_markup=main_markup)


# work of menu
@dp.callback_query_handler(lambda c: c.data == 'catalog')
async def callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Разделы асан:', reply_markup=menu_keyboard)
# menu asana type handler
@dp.callback_query_handler(lambda c: c.data in asana_types)
async def callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
                           f'{asana_types_description[callback_query.data][1]} приведен ниже.\nНажми кнопку с искомой асаной\nПолучишь её фото и описание!')
    for asana in asana_data[callback_query.data]:
        asana_button = InlineKeyboardMarkup().add(InlineKeyboardButton(asana, callback_data=asana))
        await bot.send_message(callback_query.from_user.id, 'Йогическая поза', reply_markup=asana_button)
        with open(os.path.join(directory, callback_query.data, f'{asana}.png'), 'rb') as f:
            img = f.read()
            await bot.send_photo(callback_query.from_user.id, img)
async def replay_with_asana_data(data, message, user_id):
    # get asana type
    asana_files_path = ''
    for a_type, a_list in asana_data.items():
        if data in a_list:
            asana_files_path = join(directory, a_type, data)
            break
    with open(f'{asana_files_path}.txt', 'r') as t:
        with open(f'{asana_files_path}.jpg', 'rb') as f:
            txt = t.read()
            img = f.read()
            await bot.send_message(user_id, txt)
            await bot.send_photo(user_id, img)
            await message.reply('Каталог', reply_markup=main_markup)


# Print txt & photo of asana by buttons
@dp.callback_query_handler(lambda c: c.data in asana_list)
async def callback(callback_query: types.CallbackQuery):
    await replay_with_asana_data(callback_query.data, callback_query.message, callback_query.from_user.id)

# Random_asana_button workship
@dp.callback_query_handler(lambda c: c.data == 'random_asana')
async def callback(callback_query: types.CallbackQuery):
    randomize_asana = random.choice(random.choice(random_asana_list))
    for a_type, a_list in asana_data.items():
        asana_files_path = ''
        if randomize_asana in a_list:
            asana_files_path = join(directory, a_type, randomize_asana)
            break

    with open(f'{asana_files_path}.txt', 'r') as t:
        with open(f'{asana_files_path}.jpg', 'rb') as f:
            txt = t.read()
            img = f.read()
            await bot.send_message(callback_query.from_user.id, txt)
            await bot.send_photo(callback_query.from_user.id, img)
            await bot.send_message(callback_query.from_user.id, text='Каталог', reply_markup=main_markup)


# handlers for basics ans steps of yoga parts

@dp.callback_query_handler(lambda c: c.data == 'basics')
async def callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Основные понятия и термины йоги:', reply_markup=menu_basics_keyboard)

@dp.callback_query_handler(lambda c: c.data in basics_types)
async def callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Раздел йоги:')
    bp = callback_query.data + '.png'
    bt = callback_query.data + '.txt'
    if bp in basics_types1:
        with open(os.path.join(directory_2, bt), 'r') as t:
            with open(os.path.join(directory_2, bp), 'rb') as p:
                txt = t.read()
                img = p.read()
                if len(txt) > 4096:
                    for sim in range(0, len(txt), 4096):
                        await bot.send_message(callback_query.from_user.id, txt[sim:sim+4096])
                    await bot.send_photo(callback_query.from_user.id, img)
                    await bot.send_message(callback_query.from_user.id, text='Каталог', reply_markup=main_markup)
                else:
                    await bot.send_message(callback_query.from_user.id, txt)
                    await bot.send_photo(callback_query.from_user.id, img)
                    await bot.send_message(callback_query.from_user.id, text='Каталог', reply_markup=main_markup)
    elif bt in basics_types1:
        with open(os.path.join(directory_2, bt), 'r') as t:
            txt = t.read()
            if len(txt) > 4096:
                for sim in range(0, len(txt),4096):
                    await bot.send_message(callback_query.from_user.id, txt[sim:sim+4096])
                await bot.send_message(callback_query.from_user.id, text='Каталог', reply_markup=main_markup)
            else:
                await bot.send_message(callback_query.from_user.id, txt)
                await bot.send_message(callback_query.from_user.id, text='Каталог', reply_markup=main_markup)

                #await message.reply('Каталог', reply_markup=main_markup)


@dp.callback_query_handler(lambda c: c.data == 'steps')
async def callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,'8 ступеней йоги:',reply_markup=menu_steps_keyboard)
@dp.callback_query_handler(lambda c: c.data in steps_types)
async def callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Ступень йоги:')
    st = callback_query.data + '.txt'
    if st in steps_types1:
        with open(os.path.join(directory_3, st),'r') as t:
            txt = t.read()
            if len(txt) >= 4096:
                for sim in range(0, len(txt), 4096):
                    await bot.send_message(callback_query.from_user.id, txt[sim:sim + 4096])
                await bot.send_message(callback_query.from_user.id, text='Каталог', reply_markup=main_markup)
                await message.reply('Каталог', reply_markup=main_markup)
            else:
                await bot.send_message(callback_query.from_user.id, txt)
                await bot.send_message(callback_query.from_user.id, text='Каталог', reply_markup=main_markup)
                await message.reply('Каталог', reply_markup=main_markup)


# Non-stop bot-work
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
