import html
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton,CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from analytics import *


router = Router()


key_info = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='ВИБІР ДІЙ')],
        [KeyboardButton(text='Фільтр по віку')],
        [KeyboardButton(text='Зріз таблиці')]
    ], resize_keyboard=True
)




class TableState(StatesGroup):
    waiting_for_link = State() #очікування посилання
    waiting_for_data = State() # осікування дати
    waiting_for_choice = State()
    waiting_for_operator = State() # чекаємо від користувача (>=, <=, ==),
    waiting_for_age = State() # Бот чекає ведення (віку)
    waiting_for_range = State() # Очікування координат (наприклад: "0 10 0 2")



@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Отримуємо дані, які вже були збережені в пам'яті бота
    data = await state.get_data()
    link = data.get('link')

    # Якщо користувач раніше ВЖЕ надсилав посилання, не мучимо його
    if link:
        await message.answer(
            '🤖 Таблиця вже завантажена в мою пам\'ять!\n'
            'Ти можеш одразу обирати дію на клавіатурі нижче.',
            reply_markup=key_info
        )
        await state.set_state(TableState.waiting_for_choice)
    else:
        # Якщо бот запущений вперше або пам'ять пуста — просимо лінк
        await state.clear()
        await message.answer('Привіт! Надішли мені посилання на свою Google Таблицю:')
        await state.set_state(TableState.waiting_for_link)


@router.message(TableState.waiting_for_link)
async def process_link(message: Message, state: FSMContext):
    user_link = message.text
    await message.answer('Дякую! Я отримав посилання. Зараз завантажу таблицю...')

    processing = get_clean_table_url(user_link)
    await state.update_data(link=processing)

    # Виводимо назви колонок для зручності користувача
    try:
        # 1. Завантажуємо таблицю один раз прямо тут
        df = load_and_clean_table(processing)

        # 2. Передаємо готовий df у функцію all_column
        columns_list = all_column(df)
        columns_text = ", ".join(columns_list)

        await message.answer(
            f"📋 <b>Доступні колонки в таблиці:</b>\n<code>{columns_text}</code>",
            parse_mode="HTML"
        )
    except Exception:
        await message.answer(
            "⚠️ Не вдалося автоматично зчитати назви колонок. Перевірте, чи таблиця відкрита для доступу."
        )

    await message.answer('Оберіть дію на клавіатурі нижче', reply_markup=key_info)
    await state.set_state(TableState.waiting_for_choice)

@router.message(TableState.waiting_for_choice, F.text == 'ВИБІР ДІЙ')
async def choice_info_data(message: Message, state: FSMContext):
    await message.answer('Добре! Напиши мені дату, за яку ти хочеш отримати звіт (наприклад, 20.06.2026):')
    await state.set_state(TableState.waiting_for_data)


"""Отримати дату"""

@router.message(TableState.waiting_for_data)
async def get_date(message: Message, state: FSMContext):
    user_date = message.text
    date = await state.get_data()
    link = date.get('link')

    # Спроба завантажити таблицю з захистом
    try:
        df = load_and_clean_table(link)
    except Exception:
        await message.answer(
            "❌ <b>Помилка завантаження таблиці!</b>\n"
            "Перевірте, будь ласка, чи відкритий доступ до таблиці за посиланням...",
            parse_mode="HTML"
        )
        await message.answer("Надішліть посилання на таблицю знову:")
        await state.set_state(TableState.waiting_for_link)
        return

    # ❗ Тут ДУБЛЬ ВИДАЛЕНО. Одразу переходимо до обробки даних:
    result_df = info_data(df, user_date)
    total_rows = len(result_df)
    # ... далі твій код виведення звіту

    rows_text = ''
    if total_rows > 0:
        for index, row in result_df.iterrows():
            rows_text += f"👤 <b>Запис №{index + 1}:</b>\n"
            for col_name in result_df.columns:
                rows_text += f"🔹 {col_name}: {row[col_name]}\n"
            rows_text += "-----------------------\n"

    # 2. Формуємо твій красивий звіт з емодзі
    report = f"📊 <b>Універсальний звіт за:</b> <code>{user_date}</code>\n"
    report += f"🔑 Пошук виконано за введеною датою\n"
    report += f"📈 <b>Всього записів (відфільтровано):</b> <code>{total_rows}</code>\n"
    report += "_______________________\n\n"

    # Якщо щось знайшли, додаємо вміст рядків у звіт
    if total_rows > 0:
        report += rows_text  # <--- Додаємо сюди наш згенерований текст рядків!
        report += "✅ Дані успішно оброблено!"
    else:
        report += "❌ Записів за цю дату не знайдено."

    # 3. Відправляємо звіт користувачу
    await message.answer(report, parse_mode="HTML")

    # 4. Повертаємо користувача в меню вибору дій
    await message.answer("Оберіть наступну дію або надішліть нову дату:")
    await state.set_state(TableState.waiting_for_choice)

"""Створюємо кнопку з операторами (>=, <=, ==)"""


key_operators = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🔘 Старше або рівні', callback_data='>=')],
        [InlineKeyboardButton(text='🔘 Молодше або рівні', callback_data='<=')],
        [InlineKeyboardButton(text='🔘 Точно такого віку', callback_data='==')],
    ]
)

@router.message(TableState.waiting_for_choice, F.text == 'Фільтр по віку')
async def operator_info(message: Message, state: FSMContext):
    await message.answer('Оберіть дію', reply_markup=key_operators)
    await state.set_state(TableState.waiting_for_operator)


"""Ловим InlineKey кнопки"""


# Було:
# @router.callback_query(TableState.waiting_for_operator, F.data.in_(['>=', '<=', '==']))

# Стало (тимчасово для перевірки):
@router.callback_query(F.data.in_(['>=', '<=', '==']))
async def process_operator_choice(callback_query: CallbackQuery, state: FSMContext):
    # Отримуємо дані
    operator_data = callback_query.data

    # Екрануємо дані, щоб знак '<' або '=' не сприймалися як HTML-теги
    safe_operator = html.escape(operator_data)

    await state.update_data(operator_sign=operator_data)
    await callback_query.answer()

    # Використовуємо екрановані дані для повідомлення
    await callback_query.message.answer(
        f"Чудово! Ти обрав оператор: <b>{safe_operator}</b>.\n"
        f"Тепер напиши мені вік цифрою (наприклад, 25):",
        parse_mode="HTML"
    )
    await state.set_state(TableState.waiting_for_age)


@router.message(TableState.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    user_age = message.text
    data = await state.get_data()
    link = data.get('link')
    operator = data.get('operator_sign') # Тут зберігається '<=', '>=' або '=='

    df = load_and_clean_table(link)
    result_df = select_age_columns(df, user_input=user_age, operator=operator)

    # 1. Екрануємо оператор та вік для заголовка
    safe_op = html.escape(str(operator))
    safe_age = html.escape(str(user_age))
    report = f"🔍 <b>Результат фільтрації ({safe_op} {safe_age}):</b>\n\n"

    # 2. Формуємо тіло звіту
    if result_df is not None and not result_df.empty:
        for index, row in result_df.iterrows():
            report += f"👤 <b>Запис №{index + 1}</b>\n"
            for col_name in result_df.columns:
                val = row[col_name]
                if pd.notna(val):
                    # Екрануємо і назву колонки, і значення
                    safe_col = html.escape(str(col_name))
                    safe_val = html.escape(str(val))
                    report += f"🔹 <i>{safe_col}:</i> {safe_val}\n"
            report += "──────────────────\n"
    else:
        report += "❌ Жодного збігу не знайдено."

    # 3. Відправляємо звіт
    # Якщо звіт дуже довгий, він може викликати іншу помилку,
    # але зараз ми прибрали причину помилки "Unsupported start tag"
    await message.answer(report, parse_mode="HTML", reply_markup=key_info)
    await state.set_state(TableState.waiting_for_choice)


@router.message(TableState.waiting_for_choice, F.text == 'Зріз таблиці')
async def ask_for_range(message: Message, state: FSMContext):
    await message.answer(
        "✂️ <b>Режим зрізу таблиці</b>\n\n"
        "Введіть 4 цифри через пробіл:\n"
        "<code>рядки_від рядки_до кол_від кол_до</code>\n\n"
        "<i>Пример: 0 5 2 5 (рядки 0-4, колонки 2-4)</i>",
        parse_mode="HTML"
    )
    await state.set_state(TableState.waiting_for_range)


@router.message(TableState.waiting_for_range)
async def process_range(message: Message, state: FSMContext):
    user_input = message.text
    data = await state.get_data()
    link = data.get('link')

    # Завантажуємо таблицю
    df = load_and_clean_table(link)

    # Використовуємо твою універсальну функцію
    result_df = select_row_col(df, user_input)

    # Формуємо звіт безпечно через html.escape
    report = f"✂️ <b>Результат зрізу:</b>\n\n"

    if not result_df.empty:
        for index, row in result_df.iterrows():
            report += f"👤 <b>Рядок {index}</b>\n"
            for col_name in result_df.columns:
                val = row[col_name]
                if pd.notna(val):
                    report += f"🔹 <i>{html.escape(str(col_name))}:</i> {html.escape(str(val))}\n"
            report += "──────────────────\n"
    else:
        report += "❌ Нічого не знайдено."

    await message.answer(report, parse_mode="HTML", reply_markup=key_info)
    await state.set_state(TableState.waiting_for_choice)
