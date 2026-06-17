from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import pandas as pd
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()


key_info = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Інформація по даті')]
    ], resize_keyboard=True
)




class TableState(StatesGroup):
    waiting_for_link = State() #очікування посилання
    waiting_for_data = State() # осікування дати




