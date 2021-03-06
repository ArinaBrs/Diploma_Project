import psycopg2
import pandas as pd
import xlrd
import glob
import os
from data_platform import local_settings

# Переменные, которые теоретически могут изменяться
# Количество регионов
regions_count = 98
# Путь к папке группы, к которой принадлежит файл
path = r'C:\Users\User\Desktop\Diploma'

# Переменные, уникальные для файла
# Имя файла
file_name = '05-01 оборот розничной торговли.xls'
# Папка, в которой лежит файл
list_of_files = glob.glob('{0}/*'.format(path))
folder = max(list_of_files, key=os.path.getctime)
# Коды листов файла
codes = ['оборот_розничной_торговли_млн',
         'оборот_розничной_торговли_%_соотв_месяц',
         'оборот_розничной_торговли_млн_соотв_период',
         'оборот_розничной_торговли_%_пред_месяц']

# Статичные переменные
full_file_name = folder + "\\05 торговля" + '\\' + file_name
catchError = False

# functions_start
def executeCommandSelect(cursor, command):
    cursor.execute(command)
    result = cursor.fetchone()
    if result is None:
        raise psycopg2.DatabaseError("Команда '{0}' вернула NULL".format(command))
    else:
        return result[0]


def parsing_sheet(file, file_name, xfile_id, code, cursor, connection):
    # Получаем indicator_id
    command = "select id from data.indicators where code = '{0}' and xls_filename = '{1}'".format(code, file_name)
    print(1)
    cursor.execute(command)
    result = cursor.fetchone()
    if result is None:
        raise psycopg2.DatabaseError("Команда '{0}' вернула NULL".format(command))
    else:
        xindicator_id = result[0]

    # Получение данных
    for level in file.columns:
        column_3 = level[2]
        column_4 = level[3]
        command = "select period_id from data.mapping_xls_period where xls_filename = '{0}' and xls_value_year = '{1}' and xls_value = '{2}'".format(
            file_name, column_3, column_4);
        print(2)
        cursor.execute(command)
        result = cursor.fetchone()
        if result is None:
            raise psycopg2.DatabaseError("Команда '{0}' вернула NULL".format(command))
        else:
            xperiod_id = result[0]
        command = "select date_value from data.mapping_xls_period where xls_filename = '{0}' and xls_value_year = '{1}' and xls_value = '{2}'".format(
            file_name, column_3, column_4);
        print(3)
        cursor.execute(command)
        result = cursor.fetchone()
        if result is None:
            raise psycopg2.DatabaseError("Команда '{0}' вернула NULL".format(command))
        else:
            xperiod_value = result[0]
        for indx in range(len(file.index)):
            command = "select region_id from data.mapping_xls_region where xls_filename = '{0}' and xls_value = '{1}' and '{2}' between date_from and date_to".format(
                file_name, file.index[indx], xperiod_value);
            xvalue = file.iloc[indx][level]
            if pd.isna(xvalue) or xvalue == '-' or xvalue == '…':
                continue
            print(4)
            cursor.execute(command)
            result = cursor.fetchone()
            if result is None:
                raise psycopg2.DatabaseError("Команда '{0}' вернула NULL".format(command))
            else:
                xregion_id = result[0]
            if xregion_id is None:
                continue
            command = "INSERT INTO data.region_period_indicators(region_id, indicator_id, period_id, value, file_id) VALUES ({0}, {1}, {2}, {3}, {4})".format(
                xregion_id, xindicator_id, xperiod_id, xvalue, xfile_id)
            #cursor.execute(command)
            connection.commit()


# functions_end

try:
    xfile_id = None
    connection = psycopg2.connect(
        host=local_settings.DATABASES['default']['HOST'],
        port=5432,
        user='postgres',
        password='postgres',
        database='postgres')
    connection.autocommit = False
    cursor = connection.cursor()

    xls = xlrd.open_workbook(full_file_name, on_demand=True)
    sheets = xls.sheet_names()

    file_command = "select id from data.incoming_files where filename = '{0}' and status = true order by uploaded_date desc  limit 1".format(
        file_name)
    print(5)
    lastfile_id = executeCommandSelect(cursor, file_command)
    command = "INSERT INTO data.incoming_files (filename, uploaded_date, status) VALUES ('{0}', current_timestamp, false) RETURNING ID".format(
        file_name)
    xfile_id = executeCommandSelect(cursor, command)
    connection.commit()

    for i in range(len(sheets)):
        sheet_name = sheets[i]
        code = codes[i]
        file = pd.read_excel(full_file_name, header=[0, 1, 2, 3], sheet_name=sheet_name, index_col=0);
        file.drop(file.tail(len(file.index) - regions_count).index, inplace=True)
        parsing_sheet(file, file_name, xfile_id, code, cursor, connection)

    command = "UPDATE data.incoming_files SET status = true WHERE ID = {0}".format(xfile_id)
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