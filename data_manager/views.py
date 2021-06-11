import json
import psycopg2
import numpy as np
from data_platform import local_settings
from django.db import connections
from django.shortcuts import render
from django.db.models import Q
from bs4 import BeautifulSoup
from unrar import rarfile
import requests
from data_manager.models import RegionPeriodIndicators, IncomingFiles, Regions, Periods, Rules, Indicators, Logging

regions_count = 98

def executeCommandSelect(cursor, command):
    cursor.execute(command)
    result = cursor.fetchone()
    if result is None:
        raise psycopg2.DatabaseError("Команда '{0}' вернула NULL".format(command))
    else:
        return result[0]

def getHeader(column):
    column = list(column)
    del column[:1]
    key = column[0]
    for i in range(1, len(column)):
        if column[i] is np.nan:
            column[i] = key
        else:
            key = column[i]
    return column

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

def get_logs(request):
    errors = Logging.objects.raw(('''SELECT * FROM data.logging order by created_at_date desc'''))

    return render(request, 'errorLogs_form.html', {
        'queryset': errors,
    })

def create_mapping_region(request):
    if 'file_name' in request.GET and request.GET['file_name']:
        file_name = request.GET.get('file_name')
        xls_value = request.GET.get('xls_value')
        date_value = request.GET.get('date')

        region_id_name = {
            1: ['Росс', '2009-01-01', '9999-01-01'],
            39: ['Адыгея', '2009-01-01', '9999-01-01'],
            40: ['Калмыкия', '2009-01-01', '9999-01-01'],
            95: ['Крымский', '2009-01-01', '9999-01-01'],
            41: ['Крым', '2009-01-01', '9999-01-01'],
            42: ['Краснодарский', '2009-01-01', '9999-01-01'],
            43: ['Астраханская', '2009-01-01', '9999-01-01'],
            44: ['Волгоградская', '2009-01-01', '9999-01-01'],
            45: ['Ростовская', '2009-01-01', '9999-01-01'],
            3: ['Северо-Западный', '2009-01-01', '9999-01-01'],
            5: ['Северо-Кавказский', '2009-01-01', '9999-01-01'],
            4: ['Южный', '2009-01-01', '9999-01-01'],
            2: ['Центральный', '2009-01-01', '9999-01-01'],
            7: ['Уральский', '2009-01-01', '9999-01-01'],
            9: ['Дальневосточный', '2009-01-01', '9999-01-01'],
            6: ['Приволжский', '2009-01-01', '9999-01-01'],
            8: ['Сибирский', '2009-01-01', '9999-01-01'],
            10: ['Белгородская', '2009-01-01', '9999-01-01'],
            11: ['Брянская', '2009-01-01', '9999-01-01'],
            12: ['Владимирская', '2009-01-01', '9999-01-01'],
            13: ['Воронежская', '2009-01-01', '9999-01-01'],
            14: ['Ивановская', '2009-01-01', '9999-01-01'],
            15: ['Калужская', '2009-01-01', '9999-01-01'],
            16: ['Костромская', '2009-01-01', '9999-01-01'],
            17: ['Курская', '2009-01-01', '9999-01-01'],
            18: ['Липецкая', '2009-01-01', '9999-01-01'],
            20: ['Орловская', '2009-01-01', '9999-01-01'],
            21: ['Рязанская', '2009-01-01', '9999-01-01'],
            22: ['Смоленская', '2009-01-01', '9999-01-01'],
            23: ['Тамбовская', '2009-01-01', '9999-01-01'],
            24: ['Тверская', '2009-01-01', '9999-01-01'],
            25: ['Тульская', '2009-01-01', '9999-01-01'],
            26: ['Ярославская', '2009-01-01', '9999-01-01'],
            28: ['Карелия', '2009-01-01', '9999-01-01'],
            29: ['Коми', '2009-01-01', '9999-01-01'],
            30: ['Архангельская', '2009-01-01', '9999-01-01'],
            31: ['Вологодская', '2009-01-01', '9999-01-01'],
            32: ['Калининградская', '2009-01-01', '9999-01-01'],
            33: ['Ленинградская', '2009-01-01', '9999-01-01'],
            34: ['Мурманская', '2009-01-01', '9999-01-01'],
            35: ['Новгородская', '2009-01-01', '9999-01-01'],
            36: ['Псковская', '2009-01-01', '9999-01-01'],
            47: ['Дагестан', '2009-01-01', '9999-01-01'],
            48: ['Ингушетия', '2009-01-01', '9999-01-01'],
            49: ['Кабардино-Балкарская', '2009-01-01', '9999-01-01'],
            50: ['Карачаево-Черкесская', '2009-01-01', '9999-01-01'],
            51: ['Северная Осетия', '2009-01-01', '9999-01-01'],
            52: ['Чеченская', '2009-01-01', '9999-01-01'],
            53: ['Ставропольский', '2009-01-01', '9999-01-01'],
            54: ['Башкортостан', '2009-01-01', '9999-01-01'],
            55: ['Марий Эл', '2009-01-01', '9999-01-01'],
            56: ['Мордовия', '2009-01-01', '9999-01-01'],
            57: ['Татарстан', '2009-01-01', '9999-01-01'],
            58: ['Удмуртская', '2009-01-01', '9999-01-01'],
            59: ['Чувашская', '2009-01-01', '9999-01-01'],
            60: ['Пермский', '2009-01-01', '9999-01-01'],
            19: ['Московская', '2009-01-01', '9999-01-01'],
            46: ['Севастополь', '2009-01-01', '9999-01-01'],
            27: ['Москва', '2009-01-01', '9999-01-01'],
            37: ['Санкт-Петербург', '2009-01-01', '9999-01-01'],
            61: ['Нижегородская', '2009-01-01', '9999-01-01'],
            63: ['Оренбургская', '2009-01-01', '9999-01-01'],
            64: ['Пензенская', '2009-01-01', '9999-01-01'],
            65: ['Самарская', '2009-01-01', '9999-01-01'],
            66: ['Саратовская', '2009-01-01', '9999-01-01'],
            67: ['Ульяновская', '2009-01-01', '9999-01-01'],
            68: ['Курганская', '2009-01-01', '9999-01-01'],
            69: ['Свердловская', '2009-01-01', '9999-01-01'],
            70: ['Тюменская', '2009-01-01', '9999-01-01'],
            71: ['Ханты-Мансийский', '2009-01-01', '9999-01-01'],
            72: ['Ямало-Ненецкий', '2009-01-01', '9999-01-01'],
            73: ['Челябинская', '2009-01-01', '9999-01-01'],
            78: ['Алтайский', '2009-01-01', '9999-01-01'],
            74: ['Алтай', '2009-01-01', '9999-01-01'],
            76: ['Тыва', '2009-01-01', '9999-01-01'],
            77: ['Хакасия', '2009-01-01', '9999-01-01'],
            80: ['Красноярский', '2009-01-01', '9999-01-01'],
            81: ['Иркутская', '2009-01-01', '9999-01-01'],
            82: ['Кемеровская', '2009-01-01', '9999-01-01'],
            83: ['Новосибирская', '2009-01-01', '9999-01-01'],
            85: ['Томская', '2009-01-01', '9999-01-01'],
            84: ['Омская', '2009-01-01', '9999-01-01'],
            86: ['Якутия', '2009-01-01', '9999-01-01'],
            87: ['Камчатский', '2009-01-01', '9999-01-01'],
            88: ['Приморский', '2009-01-01', '9999-01-01'],
            89: ['Хабаровский', '2009-01-01', '9999-01-01'],
            90: ['Амурская', '2009-01-01', '9999-01-01'],
            91: ['Магаданская', '2009-01-01', '9999-01-01'],
            92: ['Сахалинская', '2009-01-01', '9999-01-01'],
            93: ['Еврейская', '2009-01-01', '9999-01-01'],
            94: ['Чукотский', '2009-01-01', '9999-01-01'],
            79: ['Забайкальский', '2018-01-01', '9999-01-01'],
            97: ['Забайкальский', '2009-01-01', '2017-12-31'],
            75: ['Бурятия', '2018-01-01', '9999-01-01'],
            96: ['Бурятия', '2009-01-01', '2017-12-31'],
            38: ['Ненецкий', '2009-01-01', '9999-01-01']
        }

        cursor = connections['default'].cursor()

        get_max_id_command = "SELECT MAX(id) FROM data.mapping_xls_region"
        cursor.execute(get_max_id_command)
        max_id_number = cursor.fetchall()[0][0] + 1

        for key in region_id_name.keys():
            if region_id_name[key][0] in xls_value:
                if 'без' in xls_value:
                    insert_new_row_command = "INSERT INTO data.mapping_xls_region VALUES (%s, %s, %s, NULL, %s, %s)"
                    cursor.execute(insert_new_row_command,
                                   [max_id_number, file_name, xls_value, '2009-01-01', '9999-01-01'])
                else:
                    if (date_value >= region_id_name[key][1] and date_value <= region_id_name[key][2]):
                        insert_new_row_command = "INSERT INTO data.mapping_xls_region VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(insert_new_row_command,
                                       [max_id_number, file_name, xls_value, key, region_id_name[key][1], region_id_name[key][2]])

        return render(request, 'regionsMapping_form.html')

    return render(request, 'regionsMapping_form.html')

def get_id_date_of_period(periods_items, value_year, value):
    for item in periods_items:
        if (value_year.split(' ')[0] == str(item[1].year)):
            if len(value.split('-')) == 1:
                if value[:3] == 'янв':
                    if len(item[2].split('-')) == 1:
                        return item[0], item[1]
                else:
                    if value[:3] in item[2]:
                        return item[0], item[1]
            elif value.split('-')[1][:3] in item[2]:
                return item[0], item[1]

def create_mapping_period(request):
    if 'file_name' in request.GET and request.GET['file_name']:
        file_name = request.GET.get('file_name')
        xls_value_year = request.GET.get('xls_value_year')
        xls_value = request.GET.get('xls_value')

        cursor = connections['default'].cursor()
        select_periods_command = "SELECT * FROM data.periods"
        cursor.execute(select_periods_command)
        periods_items = cursor.fetchall()

        period_id, date_value = get_id_date_of_period(periods_items, xls_value_year, xls_value)

        get_max_id_command = "SELECT MAX(id) FROM data.mapping_xls_period"
        cursor.execute(get_max_id_command)
        max_id_number = cursor.fetchall()[0][0] + 1

        insert_new_row_command = "INSERT INTO data.mapping_xls_period VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_new_row_command, [max_id_number, file_name, xls_value_year, xls_value, period_id, date_value])

        return render(request, 'periodsMapping_form.html')

    return render(request, 'periodsMapping_form.html')

def create_rules(request):
    if 'rule_textarea' in request.GET and request.GET['rule_textarea']:
        rule = request.GET.get('rule_textarea')
        rule_error = request.GET.get('error_textarea')

        try:
            connection = psycopg2.connect(
                host=local_settings.DATABASES['default']['HOST'],
                port=5432,
                user='postgres',
                password='postgres',
                database='postgres')
            connection.autocommit = False
            cursor = connection.cursor()
            command = "INSERT INTO data.rules(user_id, code, description_log, flag) VALUES (1, '{0}', '{1}', true)" \
                .format(rule, rule_error)
            cursor.execute(command)
            connection.commit()
            #messages.success(request, "Правило успешно создано." )

        except Exception as error:
            print("Ошибка ввода данных. Сообщение: ", error)

        finally:
            cursor.close()
            connection.close()

        return render(request, 'rulesCreation_form.html')

    return render(request, 'rulesCreation_form.html')

def executeCommandSelect(cursor, command):
    cursor.execute(command)
    result = cursor.fetchone()
    if result is None:
        raise psycopg2.DatabaseError("Команда '{0}' вернула NULL".format(command))
    else:
        return result[0]

def enterDataRulesCheck(rule_name, region_name, date, file_name, idicator_name, cursor):
    command = "SELECT id FROM data.rules WHERE code = '{0}' ".format(rule_name)
    xrule = executeCommandSelect(cursor, command)

    command = "SELECT id FROM data.regions WHERE name = '{0}' ".format(region_name)
    xregion = executeCommandSelect(cursor, command)
    command = "SELECT id FROM data.indicators WHERE name = '{0}' AND xls_filename = '{1}'".format(
        idicator_name, file_name)
    xindicator = executeCommandSelect(cursor, command)

    command = "SELECT id FROM data.periods WHERE value = '{0}' ".format(date + '-01')
    xperiod = executeCommandSelect(cursor, command)

    return [xrule, xregion, xindicator, xperiod]

def manage_rules(request):
    rules = Rules.objects.all()
    indicators = Indicators.objects.filter(~Q(name__contains="LSTM") & ~Q(name__contains="SARIMA"))

    if 'rule_name' in request.GET and request.GET['rule_name']:
        rule_name = request.GET.get('rule_name')
        region_name = request.GET.get('region_name')
        date = request.GET.get('date')
        file_name = request.GET.get('file_name')
        indicator_name = request.GET.get('indicator_name')

        try:
            connection = psycopg2.connect(
                host=local_settings.DATABASES['default']['HOST'],
                port=5432,
                user='postgres',
                password='postgres',
                database='postgres')
            connection.autocommit = False
            cursor = connection.cursor()

            entryDataRulesCheck = enterDataRulesCheck(rule_name, region_name, date, file_name, indicator_name, cursor)
            connection.commit()
            command = "INSERT INTO data.rules_checking(rule_id, region_id, indicator_id, period_id, status, created_at) VALUES ('{0}', '{1}', '{2}', '{3}', true, current_timestamp)".format(
                entryDataRulesCheck[0], entryDataRulesCheck[1], entryDataRulesCheck[2], entryDataRulesCheck[3])
            cursor.execute(command)
            connection.commit()

        except Exception as error:
            print("Ошибка транзакции. Отмена всех операций. Сообщение: ", error)

        finally:
            cursor.close()
            connection.close()

    return render(request, 'rulesManage_form.html', {
        'regions': regionsFilter(),
        'rules': rules,
        'indicators': indicators
    })

def get_monitoring(request):
    uploaded_files = IncomingFiles.objects.raw('''SELECT * FROM data.incoming_files order by uploaded_date desc''')

    ort1 = request.GET.get('ort1')
    products1 = request.GET.get('products1')
    non_food1 = request.GET.get('non-food1')
    ort2 = request.GET.get('ort2')
    products2 = request.GET.get('products2')
    non_food2 = request.GET.get('non-food2')
    emiss = request.GET.get('emiss')

    file_scripts = {
        ort1: r'C:\Users\User\mysite\scripts\05_01_parser.py',
        products1: r'C:\Users\User\mysite\scripts\05_02_parser.py',
        non_food1: r'C:\Users\User\mysite\scripts\05_03_parser.py',
        ort2: r'C:\Users\User\mysite\scripts\095_106_parser.py',
        products2: r'C:\Users\User\mysite\scripts\107_118_parser.py',
        non_food2: r'C:\Users\User\mysite\scripts\119_130_parser.py',
        emiss: r'C:\Users\User\mysite\scripts\emicc_parser.py'
    }

    for key in file_scripts:
        if key != None:
            exec(open(file_scripts[key], encoding='utf8').read())

    return render(request, 'monitoring_form.html', {
        'queryset': uploaded_files,
    })

def get_files_indicators(request):
    file_name_query = request.GET.get('file_name')

    if file_name_query != '' and file_name_query is not None:
        if file_name_query == 'Оборот розничной торговли':
            indicator_id_name = {
                "млн. руб": ["1", "9", "52"],
                "% к соотв. месяцу": ["2", "12", "53"],
                "млн. руб к соотв. периоду": ["3", "10", "54"],
                "% к пред. месяцу": ["4", "11", "55"]
            }
            file_end = "%торговли%"
        else:
            if file_name_query == 'Оборот розничной торговли пищевыми продуктами':
                indicator_id_name = {
                    "млн. руб": ["5", "13", "56"],
                    "% к соотв. месяцу": ["6", "14", "57"],
                    "млн. руб к соотв. периоду": ["7", "15", "58"],
                    "% к пред. месяцу": ["8", "16", "59"]
                }
                file_end = "%продуктами%"
            else:
                if file_name_query == 'Оборот розничной торговли непродовольственными товарами':
                    indicator_id_name = {
                        "млн. руб": ["7", "21", "68"],
                        "% к соотв. месяцу": ["20", "24", "71"],
                        "млн. руб к соотв. периоду": ["18", "22", "69"],
                        "% к пред. месяцу": ["19", "23", "70"]
                    }
                    file_end = "%непродовольственными%"

    return file_end, indicator_id_name


def predict_values(request):
    if 'file_name' in request.GET and request.GET['file_name']:
        labels = []
        data = []
        labels_predict = []
        data_predict = []

        qs = RegionPeriodIndicators.objects.all()
        file_name_query = request.GET.get('file_name')
        region_name_query = request.GET.get('region_name')
        indicator_name_query = request.GET.get('indicator_name')

        file_end, indicator_id_name = get_files_indicators(request)

        if indicator_name_query == 'млн. руб':
            january_period_id = []
            period_value = {}

            for item in Periods.objects.raw('SELECT * FROM data.periods WHERE EXTRACT (month FROM value) = 1 order by value'):
                january_period_id.append(item.id)

            query = '''select * from data.region_period_indicators rpi
                            join data.regions r
                                on rpi.region_id = r.id
                            join data.periods p
                                on rpi.period_id = p.id
                            join data.incoming_files if_
                                on rpi.file_id = if_.id
                            where (if_.filename LIKE %s) and (if_.status = True) and (rpi.indicator_id = %s or rpi.indicator_id = %s) and r.name = %s
                            and p.id NOT IN (62, 63, 64) 
                            order by p.value '''

            for item in RegionPeriodIndicators.objects.raw(query,
                [file_end, indicator_id_name[indicator_name_query][0], indicator_id_name[indicator_name_query][1], region_name_query]):
                period_value[item.period_id] = item.value
                labels.append(item.value_label)

            for key in period_value.keys():
                if key not in january_period_id:
                    data.append(period_value[key] - period_value[key - 1])
                else:
                    data.append(period_value[key])
        else:
            query = '''select * from data.region_period_indicators rpi
                        join data.periods p
                            on rpi.period_id = p.id
                        join data.incoming_files if_
                            on rpi.file_id = if_.id
                        join data.regions r
                            on rpi.region_id = r.id
                        where (if_.filename LIKE %s) and (if_.status = True) and
                            r.name=%s and (indicator_id=%s or indicator_id=%s) and p.id NOT IN (62, 63, 64)
                        order by p.value '''

            for item in RegionPeriodIndicators.objects.raw(query,
                [file_end, region_name_query, indicator_id_name[indicator_name_query][0], indicator_id_name[indicator_name_query][1]]):
                labels.append(item.value_label)
                data.append(item.value)

        pred_query = '''select * from data.region_period_indicators rpi
                        join data.periods p
                            on rpi.period_id = p.id
                        join data.regions r
                            on rpi.region_id = r.id
                        where rpi.file_id IS NULL and r.name=%s and indicator_id=%s'''

        for item in RegionPeriodIndicators.objects.raw(pred_query,
            [region_name_query, indicator_id_name[indicator_name_query][2]]):
            labels_predict.append(item.value_label)
            data_predict.append(item.value)

        data_values = data + [None] * (len(data_predict))
        data_predict_values = [None] * len(data) + data_predict

        return render(request, 'predictionCharts.html', {
            'regions': regionsFilter(),
            'labels': labels,
            'index': labels + labels_predict,
            'current': json.dumps(data_values),
            'pred': json.dumps(data_predict_values),
            'queryset': qs,
            'reg': region_name_query,
            'file': file_name_query,
            'indicator': indicator_name_query
        })

    return render(request, 'predictionCharts.html', {
        'regions': regionsFilter()
    })

def get_data_for_charts(request):
    if 'file_name' in request.GET and request.GET['file_name']:
        labels = []
        data = []

        qs = RegionPeriodIndicators.objects.all()
        file_name_query = request.GET.get('file_name')
        indicator_name_query = request.GET.get('indicator_name')
        region_name_query = request.GET.get('region_name')
        startDate = request.GET.get('date_min')
        endDate = request.GET.get('date_max')
        is_accumulated = request.GET.get('accumulated')

        file_end, indicator_id_name = get_files_indicators(request)

        query = '''select * from data.region_period_indicators rpi
                        join data.regions r
                            on rpi.region_id = r.id
                        join data.periods p
                            on rpi.period_id = p.id
                        join data.incoming_files if_
                            on rpi.file_id = if_.id
                        where (if_.filename LIKE %s) and (if_.status = True) and (rpi.indicator_id = %s or rpi.indicator_id = %s) and r.name = %s
                            and p.value >= %s and p.value <= %s '''

        if indicator_name_query == 'млн. руб' and is_accumulated == None:
            january_period_id = []
            period_value = {}

            for item in Periods.objects.raw('SELECT * FROM data.periods WHERE EXTRACT (month FROM value) = 1'):
                january_period_id.append(item.id)

            for item in RegionPeriodIndicators.objects.raw(query,
                [file_end, indicator_id_name[indicator_name_query][0], indicator_id_name[indicator_name_query][1],
                region_name_query, startDate+'-01', endDate+'-01']):
                period_value[item.period_id] = item.value
                labels.append(item.value_label)

            for key in period_value.keys():
                if key not in january_period_id:
                    data.append(period_value[key] - period_value[key-1])
                else:
                    data.append(period_value[key])

        else:
            for item in RegionPeriodIndicators.objects.raw(query,
               [file_end, indicator_id_name[indicator_name_query][0], indicator_id_name[indicator_name_query][1],
                region_name_query, startDate + '-01', endDate + '-01']):
                labels.append(item.value_label)
                data.append(item.value)

        return render(request, 'regionsCharts.html', {
            'regions': regionsFilter(),
            'labels': labels,
            'data': data,
            'queryset': qs,
            'reg': region_name_query,
            'file': file_name_query
        })

    return render(request, 'regionsCharts.html', {
        'regions': regionsFilter()
    })

def downloadRosstatFiles(request):
    if 'file_name' in request.GET and request.GET['file_name']:
        url = request.GET.get('file_name')
        archive_folder = request.GET.get('download-archive')
        data_folder = request.GET.get('download-data')

        download_data(url, archive_folder, data_folder)

        return render(request, "downloadData_form.html", {
            'links': find_archive_urls()
        })

    return render(request, "downloadData_form.html", {
        'links': find_archive_urls()
    })

def find_archive_urls():
    root = 'https://rosstat.gov.ru'
    r = requests.get('https://rosstat.gov.ru/folder/11109/document/13259')
    tags = BeautifulSoup(r.text, features="html.parser").find_all('a')
    links = [tag.get('href') for tag in tags if tag.get('href') is not None and tag.get('href').endswith('.rar')]
    links = [root + link for link in links]
    return links

def download_archive(url, filename):
    r = requests.get(url, allow_redirects=True)
    if r.ok is False:
        raise ConnectionError('Неверная ссылка')
    open(filename, 'wb').write(r.content)

def unrar(archive, folder):
    rar = rarfile.RarFile(archive)
    rar.extractall(folder)

def download_data(url, archive_folder, data_folder):
    if archive_folder[len(archive_folder)-1] == '\\':
        full_archive_name = '{0}rosstat.rar'.format(archive_folder)
    else:
        full_archive_name = '{0}\\rosstat.rar'.format(archive_folder)
    download_archive(url, full_archive_name)
    unrar(full_archive_name, data_folder)

def login(request):
    return render(request, 'login_form.html')

def regionsFilter():
    district_region = {}

    for district in Regions.objects.filter(region_type__contains="округ"):
        region = []
        for item in Regions.objects.filter(par=district.id):
            region.append(item.name)
        district_region[district.name] = region

    return district_region