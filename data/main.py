import json
from xlwt import Workbook
import xlwt
import os
import asyncio
from my_functions import *


api_id = config.api_id
api_hash = config.api_hash
session = 'session.session'
loop = asyncio.get_event_loop()

def create_json_prettifier():

    class Enc(json.JSONEncoder):

        def default(self, o):
            t = str(type(o))
            if t == "<class 'datetime.datetime'>" or t == "<class 'bytes'>":
                return str(o)
            try:
                return o.__dict__
            except:
                return t

    return lambda data: json.dumps(data, indent=4, cls=Enc, ensure_ascii=False)


json_prettifier = create_json_prettifier()

# Получаем чат пользователя, проверяем, что за ссылку он отправил и ожидаем правильной ссылки
while True:
    link = input('Введите ссылку на чат: ')
    res = check_link(link)
    if not res:
        print('Неверная ссылка. Попробуйте другую.')
    elif res == 'url' or res == 'id':
        if res == 'id':
            res = loop.run_until_complete(check_chat(link, 'id'))
        else:
            res = loop.run_until_complete(check_chat(link, 'url'))
        if res is not False and res['status'] == 'ok':
            members = res['members']
            admins = res['admins']
            chat = res['ch']
            users = res['users']
            channel_type = res['channel_type']
            channel_title = res['channel_title']
            break
        elif res is not False and res['status'] == 'error' and res['error_type'] == 'too_many_users':
            chat = res['ch']
            channel_type = res['channel_type']
            channel_title = res['channel_title']
            break
    elif res == 'close':
        chat = loop.run_until_complete(inv_chat(link))
        res = loop.run_until_complete(check_chat(chat, 'url'))
        if res is not False and res['status'] == 'ok':
            members = res['members']
            admins = res['admins']
            chat = res['ch']
            users = res['users']
            channel_type = 'Чаты'
            channel_title = chat.title
            break
        elif res is not False and res['status'] == 'error' and res['error_type'] == 'too_many_users':
            chat = res['ch']
            channel_type = 'Чаты'
            channel_title = chat.title
            break
for x in ['\\', '|', '"', '/', ':',
        '?', '*', '<', '>']:
    channel_title = channel_title.replace(x, ' ')
if os.path.exists(f'../Чаты') is False:
    os.mkdir(f'../Чаты')
if os.path.exists(f'../Каналы') is False:
    os.mkdir(f'../Каналы')
if os.path.exists(f'../{channel_type}/{channel_title}') is False:
    os.mkdir(f'../{channel_type}/{channel_title}')
if res['status'] == 'ok':
    with open(f'../{channel_type}/{channel_title}/Участники {channel_title}.json', 'w', encoding='utf8') as f:
        with open(f'../{channel_type}/{channel_title}/Участники {channel_title}.txt', 'w', encoding='utf8') as file:
            all_users = {
                'admins': admins,
                'users': members
            }
            f.write(json_prettifier(all_users))
            if admins is not None:
                file.write('Администраторы:\n')
                for x in admins:
                    file.write(f'{str(admins[x])}\n')
            if len(members)>0:
                file.write('Пользователи:\n')
                for x in members:
                    file.write(f'{str(members[x])}\n')
    wb = Workbook()
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd.mm.yyyy hh:mm:ss'
    style = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue;'
                        'font: colour white, bold True;')
    n_list = 1
    sheet1 = wb.add_sheet(f'Users_{n_list}')
    sheet1.write(0, 0, 'Администраторы', style)
    sheet1.write(0, 1, 'ID', style)
    sheet1.write(0, 2, 'First Name', style)
    sheet1.write(0, 3, 'Last Name', style)
    sheet1.write(0, 4, 'Username', style)
    sheet1.write(0, 5, 'Телефон', style)
    sheet1.write(0, 6, 'Бот', style)
    sheet1.write(0, 7, 'Удалён', style)
    sheet1.write(0, 8, 'Скам', style)
    sheet1.write(0, 9, 'Был онлайн', style)
    n = 1
    q = 1
    for x in users:
        sheet1.col(0).width = 256 * 17
        sheet1.col(1).width = 256 * 17
        sheet1.col(2).width = 256 * 25
        sheet1.col(3).width = 256 * 25
        sheet1.col(4).width = 256 * 25
        sheet1.col(5).width = 256 * 17
        sheet1.col(6).width = 256 * 7
        sheet1.col(7).width = 256 * 7
        sheet1.col(8).width = 256 * 7
        sheet1.col(9).width = 256 * 25
        sheet1.write(n, 0, x['admin'])
        sheet1.write(n, 1, x['id'])
        sheet1.write(n, 2, x['first_name'])
        sheet1.write(n, 3, x['last_name'])
        sheet1.write(n, 4, x['username'])
        sheet1.write(n, 5, x['phone'])
        sheet1.write(n, 6, x['bot'])
        sheet1.write(n, 7, x['deleted'])
        sheet1.write(n, 8, x['scam'])
        sheet1.write(n, 9, x['was_online'], date_format)
        n += 1
        q += 1
        if n == 30000:
            n_list += 1
            sheet1 = wb.add_sheet(f'Users_{n_list}"')
            n = 1
    wb.save(f'../{channel_type}/{channel_title}/Участники {channel_title}.xls')



while True:
    otvet = input('\nЖелаете ли вы сохранить историю сообщений?\n1 - да\n2 - нет ')
    if str(otvet) == '1' or str(otvet) == '2':
        break
if str(otvet) == '1':
    loop.run_until_complete(dump_messages(chat, channel_title))
input('\nСканирование закончено. Можете нажать "Enter", чтобы закрыть окно.')
