import re
import time
import string
import config
from telethon.sync import TelegramClient
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsSearch
from telethon import functions, errors
api_id = config.api_id
api_hash = config.api_hash
session = 'session.session'


async def inv_chat(link):
    hash = link.rsplit('/', 1)[1]
    async with TelegramClient(session, api_id, api_hash) as client:
        try:
            await client(functions.messages.ImportChatInviteRequest(
            hash=hash))
            res = await client(functions.messages.CheckChatInviteRequest(
                hash=hash
             ))
            if res.chat.megagroup is False:
                print(
                    'Похоже, вы отправили ссылку на закрытый канал. Уьедитесь, что вы собираете информацию из группы.')
                exit()
        except errors.ChannelsTooMuchError:
            print('Вы вступили в слишком большое количество чатов')
            exit()
        except errors.InviteHashEmptyError:
            print('Хеш приглашения пуст.')
            exit()
        except errors.InviteHashExpiredError:
            print('Срок действия чата, к которому пользователь пытался присоединиться, истек, и он больше не действителен.')
            exit()
        except errors.InviteHashInvalidError:
            print('Недействительная ссылка.')
            exit()
        except errors.SessionPasswordNeededError:
            print('Включена двухэтапная проверка, требуется пароль.')
            exit()
        except errors.UsersTooMuchError:
            print('Превышено максимальное количество пользователей (например, для создания чата).')
            exit()
        except errors.UserAlreadyParticipantError:
            res = await client(functions.messages.CheckChatInviteRequest(
                hash=hash
            ))
        return res.chat


async def check_chat(chat, type_link):
    # Проверка на то, является ли ссылка на чат чатом с последующей выгрузкой участников
    async with TelegramClient('session', api_id, api_hash) as client:
        try:
            if type_link == 'id':
                ch = await client.get_entity(int(chat))
            else:
                ch = await client.get_entity(chat)
            channel_type = 'Чаты'
            if ch.__class__.__name__ == 'Channel':
                if ch.megagroup is False:
                    res = await client(functions.channels.GetFullChannelRequest(
        channel=ch
    ))
                    if len(res.chats) != 2:
                        print("Канал не имеет закреплённого чата для комментариев")
                        return False
                    else:
                        channel_type = 'Каналы'
                        channel_title = ch.title
                        ch = await client.get_entity(res.chats[1])
                count_members = await client(functions.channels.GetFullChannelRequest(channel=ch))
                count_members = count_members.full_chat.participants_count
                aggressive = False
                if count_members > 5000:
                    aggressive = True
                admins = []
                titles = {}
                async for user in client.iter_participants(ch, filter=ChannelParticipantsAdmins):
                    admins.append(user)
                    title = await client.get_permissions(ch, user)
                    titles[f'{title.participant.user_id}'] = title.participant.rank
                if len(admins) == 0:
                    admins = None
                else:
                    admins = list_users(admins, titles)
                m = 1
                print('Выполняется стандартный парсинг...')
                members = []
                if not aggressive:
                    async for user in client.iter_participants(ch):
                        members.append(user)
                else:
                    ids = []
                    try:
                        async for user in client.iter_participants(ch):
                            if m % 200 == 0:
                                time.sleep(1)
                            members.append(user)
                            ids.append(user.id)
                            m += 1
                    except Exception as e:
                        if str(e) == "'ChannelParticipants' object is not subscriptable":
                            pass
                    print('Внимание! Следующая операция занимает продолжительное время: 15 минут для чата в 100 тысяч пользователей. '
                          'Мы в процессе оптимизации.')

                    for num, x in enumerate(string.ascii_lowercase):
                        print(f'\rВыполняется расширенный поиск по алфавиту... {num}/{len(string.ascii_lowercase)} ', end='')
                        m = 1
                        try:
                            async for user in client.iter_participants(ch, filter=ChannelParticipantsSearch(x)):
                                if m % 200 == 0:
                                    time.sleep(1)
                                if user.id in ids:
                                    continue
                                members.append(user)
                                ids.append(user.id)
                                m += 1
                        except Exception as e:
                            if str(e) == "'ChannelParticipants' object is not subscriptable":
                                continue
                if len(members) == 0:
                    members = None
                else:
                    members = list_users(members)
                if channel_type == 'Каналы':
                    limit = 3000
                    print(
                        f'Собираем сообщения. В зависимости от ваших прошлый запросов, действие может занять продолжительное время.\n'
                        f'Лимит - {limit}')
                    mess = await client(functions.messages.GetHistoryRequest(
                        peer=ch,
                        offset_id=0,
                        offset_date=None,
                        add_offset=0,
                        limit=limit,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))
                    mess_user = list_users(mess.users)
                    members = {**members, **mess_user}
                users = []
                for x in members:
                    user = {}
                    if admins is not None:
                        if str(members[x]['id']) in admins:
                            user['admin'] = admins[str(members[x]['id'])]['title'] or 'Администратор'
                        else:
                            user['admin'] = ''
                    else:
                        user['admin'] = ''
                    user['id'] = members[x]['id']
                    user['first_name'] = members[x]['first_name']
                    if members[x]['last_name'] is None:
                        user['last_name'] = ''
                    else:
                        user['last_name'] = members[x]['last_name']
                    if members[x]['username'] is None:
                        user['username'] = ''
                    else:
                        user['username'] = members[x]['username']
                    if members[x]['phone'] is None:
                        user['phone'] = ''
                    else:
                        user['phone'] = members[x]['phone']
                    if members[x]['bot'] is False:
                        user['bot'] = ''
                    else:
                        user['bot'] = 'True'
                    if members[x]['deleted'] is False:
                        user['deleted'] = ''
                    else:
                        user['deleted'] = 'True'
                    if members[x]['scam'] is False:
                        user['scam'] = ''
                    else:
                        user['scam'] = 'True'
                    if members[x]['was_online'] is None:
                        user['was_online'] = ''
                    else:
                        user['was_online'] = members[x]['was_online']
                    if members[x]['status'] is None:
                        user['status'] = ''
                    else:
                        user['status'] = members[x]['status']
                    users.append(user)
                if channel_type != 'Каналы':
                    channel_title = ch.title
                return {'status': 'ok', 'members': members, 'admins': admins,
                        'ch': ch, 'users': users, 'channel_type': channel_type,
                        'channel_title': channel_title}
            else:
                print('Вы ввели ссылку, которая не ведёт на открытую группу. Попробуйте другую.')
                return False
        except ValueError as e:
            return False


async def dump_messages(chat, title):
    """Выгружаем сообщения"""
    async with TelegramClient(session, api_id, api_hash) as client:
        with open(f'../Чаты/{title}/Сообщения {title}.txt', 'w', encoding='utf8') as file:
            with open(f'../Чаты/{title}/Сообщения {title}.html', 'w', encoding='utf8') as f:
                n = 0
                print(f'\n')
                async for message in client.iter_messages(chat):
                    n += 1
                    if n == 100:
                        print(f'\rID текущего сообщения: {message.id} ', end='')
                        n = 0
                    file.write(f'{message}\n')
                    if message.media is not None:
                        f.write(
                            f'<fieldset><legend>{message.from_id} | {message.date} </legend>Image. <br>{message.message}<br><br><small>Message id:{message.id}</small></fieldset>\n')
                    else:
                        f.write(
                            f'<fieldset><legend>{message.from_id} | {message.date} </legend>{message.message}<br><br><small>{message}</small></fieldset>\n')


def check_link(link):
    try:
        if int(link):
            return 'id'
    except Exception as e:
        pass
    """Проверяем ссылку регуляркой и определяем, что хочет пользователь"""
    if re.match(r'https://t.me/joinchat/[a-z-_0-9]{1}[a-z-_0-9]{4,}$', link.lower()) or re.match(
            r'http://t.me/joinchat/[a-z-_A-Z0-9]{1}[a-z-_0-9]{4,}$', link.lower()):
        return 'close'
    elif re.match(r'https://t.me/[a-z]{1}[a-z_0-9]{4,31}$', link.lower()) or re.match(
            r'@[a-z]{1}[a-z_0-9]{4,31}$', link.lower()) or re.match(
        r'[a-z]{1}[a-z_0-9]{4,31}$', link.lower()
    ):
        return 'url'
    else:
        return False


def list_users(*args):
    members = args[0]
    users = {}
    for user in members:
        users[f'{user.id}'] = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'phone': user.phone,
            'bot': user.bot,
            'deleted': user.deleted,
            'scam': user.scam,
            'was_online': user.status.was_online.replace(tzinfo=None) if hasattr(user.status, 'was_online') else None,
            'status': {
                'UserStatusEmpty': 'Пусто',
                'UserStatusLastMonth': 'Месяц',
                'UserStatusLastWeek': 'Неделя',
                'UserStatusOffline': 'Офлайн',
                'UserStatusOnline': 'Онлайн',
                'UserStatusRecently': 'Недавно',
            }.get(user.status.__class__.__name__, None)
        }
    if len(args) == 2:
        titles = args[1]
        for key, value in titles.items():
            users[key]['title'] = value
    return users
