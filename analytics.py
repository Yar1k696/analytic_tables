import pandas as pd
import re


def get_clean_table_url(url_scv: str) -> str:
    if 'docs.google.com/spreadsheets' in url_scv:
        return url_scv.split('/edit')[0] + '/export?format=csv'
    else:
        return url_scv


# Виводим всі колонки

def all_column(url_scv: str):
    df = pd.read_csv(url_scv, nrows=0)
    return df.columns.tolist()


'''робим дату в одном форматі'''


def normalize_date_format(user_date: str) -> str:
    return re.sub(r"[./]", "-", user_date)


'''иводим інфо. по даті'''
'''Безопасно фильтрует DataFrame по введенной пользователем дате'''


def info_data(df: pd.DataFrame, user_input: str) -> pd.DataFrame:
    columns_name = ['Date', 'date', 'дата', 'Дата']
    clean_input = normalize_date_format(user_input)
    try:
        target_date = pd.to_datetime(clean_input, dayfirst=True).date()
        for col in columns_name:
            if col in df.columns:
                df_copy = df.copy()
                df_copy[col] = pd.to_datetime(df_copy[col], dayfirst=True).dt.date
                return df_copy[df_copy[col] == target_date]
    except Exception:
        return df


'''РОБИМО Ф-ЦІЇ .loc '''

def select_age_columns(df: pd.DataFrame, user_input: str, operator: str) -> pd.DataFrame:

    columns_age = ['год', 'рік', 'вік', 'возраст', 'age']
    columns_name = ['имя', 'ім\'я', 'name', 'фио', 'піб', 'сотрудник', 'працівник', 'user', 'fio']


    found_age_col = None
    found_name_col = None

    #Беремо колонки з df виводимо в список
    actual_columns = df.columns.tolist()
    clean_input = user_input.lower()

    for col_age in columns_age:
        if col_age in actual_columns:
            found_age_col = col_age


    for col_name in columns_name:
        if col_name in df.columns:
            found_name_col = col_name

    age_number = int(clean_input)

    if operator == '>=':
        adult_names = df.loc[df[found_age_col] >= age_number, found_name_col]
        return adult_names


    elif operator == '<=':
        adult_names = df.loc[df[found_age_col] <= age_number, found_name_col]
        return adult_names

    elif operator == '==':
        adult_names = df.loc[df[found_age_col] == age_number, found_name_col]
        return adult_names
    return df


