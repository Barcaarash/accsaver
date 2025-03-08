from pyrogram import Client, errors, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, ReplyKeyboardRemove
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.raw import functions
from pyrogram.enums.chat_type import ChatType
import re, logging, json, os, asyncio, sqlite3, time, random, string, sys, math
import datetime


os.system('mkdir sessions')
#Log in
admins = [732607334, 703859331]
app_id, app_hash, app_token, app_session = 7801314, "6e266091eab2adc0a9d8c447d39c1514", "6494460466:AAFhifuajFu9lb7m_Ascc0s6C2SQtg0vN6w", "Saverbot"
app = Client(app_session, app_id, app_hash, bot_token=app_token)
sessions = {}
phone_code_hashs = {}
#default_proxy = {"scheme": 'socks5', "hostname": '127.0.0.1', "port": 9050}
default_proxy = {}

# Logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='./Pyro.log'
)

# DB Sql File
sql_connect = sqlite3.connect("Saver-DB.session")
my_cursor = sql_connect.cursor()
my_cursor.execute("""CREATE TABLE IF NOT EXISTS `users`(
`time` BIGINT NOT NULL PRIMARY KEY,
`id` BIGINT NOT NULL,
`step` TEXT,
`num_add` TEXT
)""")
my_cursor.execute("""CREATE TABLE IF NOT EXISTS `all_numbers`(
`time` BIGINT NOT NULL PRIMARY KEY,
`donator` BIGINT NOT NULL,
`number` TEXT NOT NULL,
`number_name` TEXT NOT NULL,
`number_id` BIGINT NOT NULL,
`is_deleted` INT DEFAULT 0
)""")
sql_connect.commit()

checkgetcode = ReplyKeyboardMarkup([
    [KeyboardButton("❪ Get-Code ❫")],
    [KeyboardButton("❪ Reverse ❫")]
], resize_keyboard=True, one_time_keyboard=True)

backbtn = ReplyKeyboardMarkup([
    [KeyboardButton("❪ Reverse ❫")]
], resize_keyboard=True, one_time_keyboard=True)

menubtn = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Add-Account 👽', b'addAccount')
    ],
    [
        InlineKeyboardButton('List Accounts 🔰', b'ListAccounts')
    ],
])

@app.on_message()
async def MessageHandler(client,message):
    #print(message)
    chat_id = message.chat.id
    chat_name = message.chat.first_name
    message_id = message.id
    text = message.text if message.text != None else ''
    getuser = my_cursor.execute(f"SELECT * FROM `users` WHERE `id` = {chat_id} LIMIT 1").fetchone()
    
    if message.chat.type != ChatType.PRIVATE or chat_id not in admins:
        return

    elif text != None and (text.lower() == '/start' or text == '❪ Reverse ❫'):
        getuser = my_cursor.execute(f"SELECT * FROM `users` WHERE `id` = {chat_id} LIMIT 1")
        if getuser.fetchone() == None:
            getunix = int(time.time())
            my_cursor.execute(f"INSERT INTO `users` (`time`, `id`) VALUES ({getunix}, {chat_id})")
        
        my_cursor.execute(f"UPDATE `users` SET `step` = 'None' WHERE `id` = {chat_id}")
        sql_connect.commit()
        await app.send_message(chat_id, "❪↻❫ → **Connecting** ...", reply_markup=ReplyKeyboardRemove(selective=True))
        await asyncio.sleep(1.5)
        await app.send_message(chat_id, '''

❪•❫ → Wait !''', reply_markup = menubtn)
        
    elif 'getcode_' in getuser[2]:
        num = getuser[2].replace('getcode_', '')
        getcode = await getLastTelegramCode(num, 'getcode')
        getcode = getcode['status']
        if isinstance(getcode, int) and getcode > 0:
            await message.reply(f"""🎉 کد ورود با موفقیت دریافت شد

🔢 کد ورود: {getcode} 
☎️ شماره اکانت: +{num}

🗳 بازگشت به منوی اصلی: /start""")
        elif getcode == 'deleted':
            await message.reply("این سشن دیلیت شده است.", reply_markup=backbtn)
        else:
            await message.reply("هیچ کدی در 5 دقیقه اخیر دریافت نشده است.", reply_markup=backbtn)

    elif getuser[2] == 'addSessionNumber':
        
        expld = text.split("\n")
        if len(expld) == 3:
            number = expld[0]
            api_id = expld[1]
            api_hash = expld[2]
        else:
            number = text
            api_id = app_id
            api_hash = app_hash

        number.replace('+', '').replace(' ', '')

        checknum = my_cursor.execute(f"SELECT * FROM `all_numbers` WHERE `number` = '{number}' LIMIT 1").fetchone()
        if checknum != None:
            await message.reply("این شماره از قبل ثبت شده است.")
            return


        my_cursor.execute(f"UPDATE `users` SET `num_add` = '{number}'  WHERE `id` = {chat_id}")
        sql_connect.commit()

        client = Client(f'sessions/phone{number}',api_id,api_hash, proxy=default_proxy)
        await client.connect()

        try:

            getphone = await client.send_code(number)
            phone_code_hash = getphone.phone_code_hash
            await app.send_message(chat_id, f"""➦ **Send the 5-digit code** ?

**⇁ Example** : `#12345`""",reply_to_message_id=message_id)
            sessions[number] = client
            phone_code_hashs[number] = phone_code_hash
            my_cursor.execute(f"UPDATE `users` SET `step` = 'LoginCode'  WHERE `id` = {chat_id}")
            sql_connect.commit()

        except errors.PhoneNumberInvalid as error:
            await app.send_message(chat_id,"""❪✘❫ → Error !

→ **the number is wrong** 
""",reply_to_message_id = message_id)
        
        except errors.ApiIdInvalid as error:
            await app.send_message(chat_id,"""HashInfo شما به دلیل خرابی نتوانستیم شماره را لاگین کنیم""",parse_mode=ParseMode.HTML, reply_to_message_id = message_id)
            await MessageHandler(app, message)
            return
        
    elif getuser[2] == 'LoginCode':

        code = text.replace('#', '')

        if not code.isdigit() or len(code) != 5:
            await app.send_message(chat_id,"<code>❪✘❫ code wrong ! </code>",parse_mode=ParseMode.HTML,reply_to_message_id = message_id)
            return

        number = getuser[3]
        client = sessions[number]
        #Register and Login
        try:

            await client.sign_in(phone_number= number,phone_code_hash =phone_code_hashs[number], phone_code=code)
            getacc = await client.get_me()
            getacc_id = getacc.id
            getacc_name = getacc.first_name
            api_id = app.api_id
            api_hash = app.api_hash
            await client.disconnect()
            getunix = int(time.time())
            my_cursor.execute(f"INSERT INTO all_numbers (time, donator, number, number_name, number_id) VALUES ({getunix}, {chat_id}, '{number}', '{getacc_name}', {getacc_id})")
            for admin in admins:
                await app.send_message(admin, f"""اکانت جدید اهدا شده است

اهدا کننده: {chat_name} - {chat_id}
شماره اهدایی: {number} - {getacc_name} - {getacc_id}""")

            my_cursor.execute(f"UPDATE `users` SET `step` = 'None' WHERE `id` = {chat_id}")
            await app.send_message(chat_id,"<code>❪✓❫ Your account has been successfully received</code>",parse_mode=ParseMode.HTML, reply_to_message_id= message_id, reply_markup = menubtn)

        except errors.PhoneNumberUnoccupied as error:
            await client.sign_up(phone_number= number,phone_code_hash= phone_code_hashs[number], first_name= 'aliiim')
            getacc = await client.get_me()
            getacc_id = getacc.id
            getacc_name = getacc.first_name
            api_id = app.api_id
            api_hash = app.api_hash
            await client.disconnect()
            getunix = int(time.time())
            my_cursor.execute(f"INSERT INTO all_numbers (time, donator, number, number_name, number_id) VALUES ({getunix}, {chat_id}, '{number}', '{getacc_name}', {getacc_id})")
            for admin in admins:
                await app.send_message(admin, f"""اکانت جدید اهدا شد

اهدا کننده: {chat_name} - {chat_id}
شماره اهدایی: {number} - {getacc_name} - {getacc_id}""")

            my_cursor.execute(f"UPDATE `users` SET `step` = 'None' WHERE `id` = {chat_id}")
            await app.send_message(chat_id,"<code>❪✓❫ Your account has been successfully received</code>",parse_mode=ParseMode.HTML, reply_to_message_id= message_id, reply_markup = menubtn)

        except errors.SessionPasswordNeeded as error:
            await app.send_message(chat_id,"<b>🔒 | تایید دو مرحله ای اکانت فعال است !</b>",parse_mode=ParseMode.HTML, reply_to_message_id = message_id)
            await app.send_message(chat_id,f"<b>🔑 | لطفا رمز تایید دو مرحله ای را وارد کنید ! </b>",parse_mode=ParseMode.HTML,reply_markup=ForceReply(selective=True))
            my_cursor.execute(f"UPDATE `users` SET `step` = 'GetTwo-step'  WHERE `id` = {chat_id}")
            sql_connect.commit()

        except errors.PhoneCodeExpired as error:
            await app.send_message(chat_id,"<b>❪✘❫ | کد تایید منقضی شده است!</b>",parse_mode=ParseMode.HTML, reply_to_message_id= message_id)

        except errors.PhoneCodeInvalid as error:
            print(f"Error-> {error}")
            await app.send_message(chat_id,"<b>❪✘❫ | کد تایید منقضی شده است!</b>",parse_mode=ParseMode.HTML, reply_to_message_id= message_id)
            await app.send_message(chat_id,f"👈 | <b>لطفا کد جدید را وارد کنید</b> ...:",parse_mode=ParseMode.HTML,reply_markup=ForceReply(selective=True))
        except Exception as error:
            print(f"Error-> {error}")


    elif getuser[2] == 'GetTwo-step':
        number = getuser[3]
        client = sessions[number]
        getacc_id = 0
        getacc_name = 'nobody'
        api_id = 0
        api_hash = 'app hash'
        try:
            await client.check_password(text)
            getacc = await client.get_me()
            getacc_id = getacc.id
            getacc_name = getacc.first_name
            api_id = app.api_id
            api_hash = app.api_hash
            await client.disconnect()
        except Exception as e:
            print(f"Error-> {e}")
        else:
            print("Log in(two_step)")
            getunix = int(time.time())
            my_cursor.execute(f"INSERT INTO all_numbers (time, donator, number, number_name, number_id) VALUES ({getunix}, {chat_id}, '{number}', '{getacc_name}', {getacc_id})")
            #getch = await getDbJsonAttr('api_ch')
            for admin in admins:
                await app.send_message(admin, f"""اکانت جدید اهدا شده است

اهدا کننده: {chat_name} - {chat_id}
شماره اهدایی: {number} - {getacc_name} - {getacc_id}""")

            my_cursor.execute(f"UPDATE `users` SET `step` = 'None' WHERE `id` = {chat_id}")
            await app.send_message(chat_id,"<code>❪✓❫ Your account has been successfully received</code>",parse_mode=ParseMode.HTML, reply_to_message_id= message_id, reply_markup = menubtn)


async def getNumbers(offset = 0, limit = 15):
    accs = []
    accs.append(
        [
        InlineKeyboardButton(f"شماره اکانت", 'null'),
        InlineKeyboardButton("حذف", 'null')
        ]
    )
    checknum = my_cursor.execute(f"SELECT * FROM `all_numbers` WHERE `is_deleted` = 0 LIMIT {limit} OFFSET {offset}").fetchall()
    for num in checknum:
        accs.append(
            [
            InlineKeyboardButton(f"{num[3]}: +{num[2]}", f"select_{num[4]}"),
            InlineKeyboardButton("🗑", f"delnum_{num[4]}_{offset}")
            ]
        )
    
    nextoffset = offset+limit
    backoffset = offset-limit
    checknum_next = my_cursor.execute(f"SELECT * FROM `all_numbers` WHERE `is_deleted` = 0 LIMIT {limit} OFFSET {nextoffset}").fetchall()
    if len(checknum_next) > 0:
        if offset == 0:
            accs.append(
                [
                    InlineKeyboardButton(f"صفحه بعدی", f"nextnumbers{nextoffset}")
                ]
            )
        else:
            accs.append(
                [
                    InlineKeyboardButton(f"صفحه قبلی", f"backnumbers{backoffset}"), InlineKeyboardButton(f"صفحه بعدی", f"nextnumbers{nextoffset}")
                ]
            )

    else:
        if offset > 0:
            accs.append(
                [
                    InlineKeyboardButton(f"صفحه قبلی", f"backnumbers{backoffset}")
                ]
            )

    return accs


async def deleteNumber(number_id):
    my_cursor.execute(f"DELETE FROM `all_numbers` WHERE `number_id` = '{number_id}'")
    sql_connect.commit()

    return True


async def getLastTelegramCode(number, work = 'check'):
    app_id, app_hash, app_session = 7801314, "6e266091eab2adc0a9d8c447d39c1514", f"phone{number}"
    get_cli = Client(app_session, app_id, app_hash, workdir="sessions/")
    
    code = 0
    username = None
    try:

        await get_cli.connect()

        if work == 'getcode':

            async for msg in get_cli.get_chat_history(777000, 1):
                ekhtelaf = datetime.datetime.today() - msg.date
                before = datetime.timedelta(minutes=5)
                if re.search(r"^Login code\: (\d+)\.", msg.text) and ekhtelaf < before:
                    code = int(re.search(r"^Login code\: (\d+)\.", msg.text)[1])
        
        elif work == 'check':
            getmecli = await get_cli.get_me()
            username = getmecli.username
            await get_cli.read_chat_history(777000, 0)

        await get_cli.disconnect()

    except (errors.AuthKeyDuplicated, errors.AuthKeyUnregistered, errors.UserDeactivated, errors.UserDeactivatedBan, errors.SessionRevoked):

        my_cursor.execute(f"UPDATE `all_numbers` SET `is_deleted` = 1 WHERE `number` = '{number}'")
        sql_connect.commit()
        return {'status': 'deleted'}


    if work == 'getcode':
        return {'status': code}
    
    elif work == 'check':
        return {'status': username}


@app.on_callback_query()
async def CallbackHandler(client, callback):
    data = callback.data
    v_id = callback.id
    chat_id = callback.from_user.id
    first_name = callback.from_user.first_name
    msg_id = callback.message.id
    getuser = my_cursor.execute(f"SELECT * FROM `users` WHERE `id` = {chat_id} LIMIT 1").fetchone()

    if data == "addAccount":
        my_cursor.execute(f"UPDATE `users` SET `step` = 'addSessionNumber' WHERE `id` = {chat_id}")
        sql_connect.commit()
        await app.send_message(chat_id, '''شماره اکانت مورد نظر را جهت افزودن به ربات ارسال کنید

**↬ Example :** `+989334445678`''', reply_markup=backbtn)
        
    elif data == "ListAccounts":
        getnums = await getNumbers(0)
        await app.send_message(chat_id, 'لیست شماره های شما', reply_markup=InlineKeyboardMarkup(getnums))
        my_cursor.execute(f"UPDATE `users` SET `step` = 'SelectAccount' WHERE `id` = {chat_id}")
        sql_connect.commit()

    elif re.search(r"^nextnumbers(\d+)$", data) and getuser[2] == 'SelectAccount':
        getoff = int(data.replace('nextnumbers', ''))
        getnums = await getNumbers(getoff)
        await app.edit_message_text(chat_id, msg_id, 'لیست شماره های شما', reply_markup=InlineKeyboardMarkup(getnums))

    elif re.search(r"^backnumbers(\d+)$", data) and getuser[2] == 'SelectAccount':
        getoff = int(data.replace('backnumbers', ''))
        getnums = await getNumbers(getoff)
        await app.edit_message_text(chat_id, msg_id, 'لیست شماره های شما', reply_markup=InlineKeyboardMarkup(getnums))

    elif re.search(r"^yesRnum_(\d+)_(\d+)$", data) and getuser[2] == 'SelectAccount':
        mtch = re.search(r"^yesRnum_(\d+)_(\d+)$", data)
        numid = int(mtch[1])
        offid = int(mtch[2])
        await deleteNumber(numid)
        getnums = await getNumbers(offid)
        await app.send_message(chat_id, f"شماره با آیدی {numid} با موفقیت از دیتابیس حذف شد.")
        await app.edit_message_text(chat_id, msg_id, 'لیست شماره های شما', reply_markup=InlineKeyboardMarkup(getnums))

    elif re.search(r"^delnum_(\d+)_(\d+)$", data) and getuser[2] == 'SelectAccount':
        mtch = re.search(r"^delnum_(\d+)_(\d+)$", data)
        numid = int(mtch[1])
        offid = int(mtch[2])
        await app.edit_message_text(chat_id, msg_id, 'آیا از حذف کامل این شماره اطمینان دارید؟', reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('خیر', f'backnumbers{offid}'),
                InlineKeyboardButton('بله مطمن هستم.', f'yesRnum_{numid}_{offid}')
            ],
        ]))

    
    elif re.search(r"^select_(\d+)$", data) and getuser[2] == 'SelectAccount':
        numid = int(re.search(r"^select_(\d+)$", data)[1])
        checknum = my_cursor.execute(f"SELECT * FROM `all_numbers` WHERE `number_id` = {numid}").fetchone()

        check = await getLastTelegramCode(checknum[2])
        check = check['status']

        if check != 'deleted':

            await app.send_message(chat_id, f"""🛍 شماره مجازی با موفقیت چک شد! 

📞 شماره اکانت: +{checknum[2]}
یوزرنیم اکانت: @{check}

📨 لطفا شماره را در تلگرام وارد کرده و روی دکمه دریافت کد بزنید …""", reply_markup=checkgetcode)
            my_cursor.execute(f"UPDATE `users` SET `step` = 'getcode_{checknum[2]}' WHERE `id` = {chat_id}")
            sql_connect.commit()


app.start()
asyncio.get_event_loop().run_forever()
