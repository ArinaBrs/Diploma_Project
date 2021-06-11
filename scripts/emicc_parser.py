import pandas as pd
import numpy as np
import psycopg2
from data_platform import local_settings

# Путь к папке группы, к которой принадлежит файл
path = r'C:\Users\User\Desktop\Diploma\emicc'

# Переменные, уникальные для файла
# Имя файла
file_name = 'data.xls'
# Коды листов файла
codes = ['оборот_розничной_торговли_%_пред_месяц_емиис',
         'оборот_розничной_торговли_непродовольственными_%_пред_месяц_емиис',
         'оборот_розничной_торговли_пищевыми_продуктами_%_пред_месяц_емиис']

# Статичные переменные
full_file_name = path + '\\' + file_name
catchError = False

# functions_start
def getHeaderEmiss(column):
    column = list(column)
    del column[:2]
    key = column[0]
    for i in range(1, len(column)):
        if column[i] is np.nan:
            column[i] = key
        else:
            key = column[i]
    return column

def getFile(file):
    xls_file = pd.read_excel(file, header=None)
    print(0)
    xls_file.drop(index=[0,1], columns=[0, 3], inplace=True)
    print(1)
    header1 = getHeaderEmiss(xls_file.iloc[0])
    print(2)
    header2 = getHeaderEmiss(xls_file.iloc[1])
    print(3)
    df = xls_file[2:]
    print(4)
    df.set_index([1, 2], inplace=True)
    print(5)
    df.columns = [header1, header2]
    print(6)
    return df

def executeCommandSelect(cursor, command):
    cursor.execute(command)
    result = cursor.fetchone()
    if result is None:
        raise psycopg2.DatabaseError("Command '{0}' return null".format(command))
    else:
        return result[0]

def parsing_sheet(file, file_name, xfile_id, code):
    global cursor, connection
    # Получаем indicator_id
    command = "select id from data.indicators where code = '{0}' and xls_filename = '{1}'".format(code, file_name)
    xindicator_id = executeCommandSelect(cursor, command)
    # Получение данных
    for level in file.columns:
        column_3 = level[0]
        column_4 = level[1]
        command = "select period_id from data.mapping_xls_period where xls_filename = '{0}' and xls_value_year = '{1}' and xls_value = '{2}'".format(
            file_name, column_3, column_4);
        xperiod_id = executeCommandSelect(cursor, command)
        command = "select date_value from data.mapping_xls_period where xls_filename = '{0}' and xls_value_year = '{1}' and xls_value = '{2}'".format(
            file_name, column_3, column_4);
        xperiod_value = executeCommandSelect(cursor, command)
        for indx in range(len(file.index)):
            command = "select region_id from data.mapping_xls_region where xls_filename = '{0}' and xls_value = '{1}' and '{2}' between date_from and date_to".format(
                file_name, file.index[indx], xperiod_value);
            xvalue = file.iloc[indx][level]
            if pd.isna(xvalue):
                continue
            xregion_id = executeCommandSelect(cursor, command)
            if xregion_id is None:
                continue
            command = "INSERT INTO data.region_period_indicators(region_id, indicator_id, period_id, value, file_id) VALUES ({0}, {1}, {2}, {3}, {4})".format(
                xregion_id, xindicator_id, xperiod_id, xvalue, xfile_id)
            #cursor.execute(command)
            connection.commit()
# functions_end

try:
    connection = psycopg2.connect(
        host=local_settings.DATABASES['default']['HOST'],
        port=5432,
        user='postgres',
        password='postgres',
        database='postgres')
    connection.autocommit = False
    cursor = connection.cursor()

    file_command = "select id from data.incoming_files where filename = '{0}' and status = true order by uploaded_date desc  limit 1".format(
        file_name)
    lastfile_id = executeCommandSelect(cursor, file_command)

    command = "INSERT INTO data.incoming_files (filename, uploaded_date , status) VALUES ('{0}', current_timestamp, false) RETURNING ID".format(
        file_name)
    xfile_id = executeCommandSelect(cursor, command)
    connection.commit()
    labels = ['Все товары и услуги', 'Непродовольственные товары', 'Продовольственные товары']
    df = getFile(full_file_name)

    for i in range(len(labels)):
        code = codes[i]
        parsing_sheet(df.loc[labels[i]], file_name, xfile_id, code)

    command = "UPDATE data.incoming_files SET status = true WHERE ID = {0}".format(xfile_id);
    #cursor.execute(command)
    connection.commit()
    command = "delete from data.region_period_indicators where file_id = {0}".format(lastfile_id)
    #cursor.execute(command)
    connection.commit()

except Exception as error:
    connection.commit()
    print("Ошибка транзакции. Остановка парсинга. Отмена всех операций транзакции. Сообщение: ", error)
    if xfile_id is not None:
        command = "delete from data.region_period_indicators where file_id = {0}".format(xfile_id)
        #cursor.execute(command)
        connection.commit()

finally:
    cursor.close()
    connection.close()