import pandas as pd
import re


def get_clean_table_url(url_scv: str) -> str:
    # Якщо це посилання на публікацію (вже містить /pub), його міняти НЕ ТРЕБА!
    if '/pub' in url_scv:
        return url_scv

    # Якщо це звичайне робоче посилання з браузера, чистимо його як зазвичай
    if 'docs.google.com/spreadsheets' in url_scv and '/edit' in url_scv:
        return url_scv.split('/edit')[0] + '/export?format=csv'

    return url_scv


def load_and_clean_table(url_scv: str) -> pd.DataFrame:
    df = pd.read_csv(get_clean_table_url(url_scv))
    # Прибираємо повністю пусті рядки та колонки
    df = df.dropna(axis=0, how='all')
    df = df.dropna(axis=1, how='all')
    return df


def all_column(df: pd.DataFrame) -> list:
    """Просто повертає список колонок із вже завантаженого DataFrame"""
    return df.columns.tolist()


def parse_date_universal(date_input):
    """
    Супер-універсальна функція для розпізнавання дат.
    Перетворює будь-який формат (2026.05.25, 25.05.2026, 2026-05-25, 25/05/2026)
    у чистий об'єкт дати Python.
    """
    if pd.isna(date_input):
        return None

    # Перетворюємо в рядок і прибираємо зайві пробіли
    date_str = str(date_input).strip()

    # Замінюємо всі можливі роздільники (крапки, косі риски) на дефіси
    normalized_str = re.sub(r"[./]", "-", date_str)

    # Список форматів, які ми намагаємось примусово перевірити
    formats_to_try = [
        "%d-%m-%Y",  # 25-05-2026 (День першим)
        "%Y-%m-%d",  # 2026-05-25 (Рік першим)
        "%m-%d-%Y"  # На всяк випадок американський
    ]

    for fmt in formats_to_try:
        try:
            return pd.to_datetime(normalized_str, format=fmt).date()
        except (ValueError, TypeError):
            continue

    # Якщо жорсткі формати не спрацювали — вмикаємо «розумне» автовизначення Pandas
    try:
        return pd.to_datetime(date_str, dayfirst=True, errors='coerce').date()
    except Exception:
        return None


def info_data(df: pd.DataFrame, user_date: str) -> pd.DataFrame:
    """Безпечно фільтрує DataFrame за будь-яким форматом дати"""
    # 1. Парсимо дату, яку ввів користувач
    converted_user_date = parse_date_universal(user_date)

    # Якщо користувач ввів текст або дурницю, яку неможливо розпізнати
    if converted_user_date is None:
        return pd.DataFrame()

    # 2. Шукаємо колонку 'Дата' (ігноруючи регістр великих/малих літер)
    found_date_col = None
    for col in df.columns:
        if str(col).strip().lower() == 'дата':
            found_date_col = col
            break

    # 3. Якщо знайшли колонку — універсально парсимо КОЖЕН рядок у таблиці
    if found_date_col:
        # Створюємо тимчасову копію колонки, де всі дати приведені до єдиного типу через наш супер-парсер
        temp_date_series = df[found_date_col].apply(parse_date_universal)

        # Фільтруємо оригінальний df за допомогою маски
        filtered_df = df[temp_date_series == converted_user_date]
        return filtered_df

    return pd.DataFrame()


def select_age_columns(df: pd.DataFrame, user_input: str, operator: str) -> pd.DataFrame:
    columns_age = ['год', 'рік', 'вік', 'возраст', 'age']
    found_age_col = None

    for real_col in df.columns:
        if str(real_col).strip().lower() in columns_age:
            found_age_col = real_col
            break

    if found_age_col is None:
        return pd.DataFrame()

    try:
        age_number = int(user_input.strip())
        # Робимо копію, щоб не міняти оригінал
        df_clean = df.copy()
        df_clean[found_age_col] = pd.to_numeric(df_clean[found_age_col], errors='coerce').fillna(0).astype(int)

        if operator == '>=': return df_clean[df_clean[found_age_col] >= age_number]
        if operator == '<=': return df_clean[df_clean[found_age_col] <= age_number]
        if operator == '==': return df_clean[df_clean[found_age_col] == age_number]
    except:
        return pd.DataFrame()
    return pd.DataFrame()


def select_row_col(df: pd.DataFrame, user_input: str) -> pd.DataFrame:
    try:
        start_r, end_r, start_c, end_c = user_input.split(' ')
        result_df = df.iloc[int(start_r):int(end_r), int(start_c):int(end_c)]
        return result_df
    except Exception:
        return df