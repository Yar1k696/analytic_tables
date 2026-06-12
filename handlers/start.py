from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import pandas as pd


router = Router()


key_info = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Інформація по даті')]
    ], resize_keyboard=True
)




class TableState(StatesGroup):
    waiting_for_link = State() #очікування посилання
    waiting_for_data = State() # осікування дати
    waiting_for_column = State() #очікуєм вибор колонки




@router.message(CommandStart())
async def start(message: Message):
    await message.answer('Привіт', reply_markup=key_info)


@router.message(F.text == 'Інформація по даті')
async def ask_for_link(message: Message, state: FSMContext):
    await message.answer('Надішліть мені посилання на Google Таблицю або .csv файл, і я виведу інформацію')

    await state.set_state(TableState.waiting_for_link)


@router.message(TableState.waiting_for_link, F.text.contains('docs.google.com/spreadsheets') | F.text.endswith('.csv'))
async def  handle_table_url(message: Message, state: FSMContext):
    if 'docs.google.com/spreadsheets' in message.text:
        final_url = message.text.split('/edit')[0] + '/export?format=csv'
    else:
        final_url = message.text

    await state.update_data(saved_url=final_url)
    await message.answer('Виберіть колонку для Інформаії')
    await state.set_state(TableState.waiting_for_column)


@router.message(TableState.waiting_for_column)
async def column_selection(message: Message, state: FSMContext):
    user_url = await state.get_data()

    final_url = user_url.get('saved_url')
    if not final_url:
        await message.answer('Сталася помилка: посилання не знайдено.')
        return
    df = pd.read_csv(final_url)
    columns = df.columns.to_list()
    columns_text = ', '.join(columns)
    await message.answer(f'Доступні колонки:\n{columns_text}\n\nНапишіть назву колонки, яка вас цікавить:')
    await state.update_data(all_columns=columns)
    await state.set_state(TableState.waiting_for_data)






