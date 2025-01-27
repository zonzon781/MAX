import telebot
import requests
import json
import os
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

MM = telebot.TeleBot('6303886527:AAG6pgUeXdJ8_-jNgVCXjrDeCMooLe-7eU8')
YOUR_ADMIN_ID = 6719309443   # ايديك
USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"

CHANNELS = [
    {"name": "القناة الأولى", "username": "YYQJQ"},
    {"name": "القناة الثانية", "username": "YYQJQ"},
    {"name": "القناة الثالثة", "username": "YYQJQ"}
]

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return CHANNELS
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(CHANNELS, f)

def check_subscriptions(user_id):
    for channel in CHANNELS:
        try:
            member_status = MM.get_chat_member(f"@{channel['username']}", user_id).status
            if member_status not in ["member", "administrator", "creator"]:
                return False
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error accessing channel @{channel['username']} for user {user_id}: {e}")
            return False
    return True

def download_video(url, output_folder="downloads"):
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        ydl_opts = {
            'outtmpl': f'{output_folder}/%(title)s.%(ext)s',
            'format': 'best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        return str(e)

@MM.message_handler(commands=['start'])
def start_handler(mm):
    user_id = mm.from_user.id
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {"first_name": mm.from_user.first_name, "username": mm.from_user.username}
        save_users(users)

    if not check_subscriptions(user_id):
        markup = InlineKeyboardMarkup()
        for channel in CHANNELS:
            markup.add(InlineKeyboardButton(f"اشترك في {channel['name']} ✅", url=f"https://t.me/{channel['username']}"))
        markup.add(InlineKeyboardButton("تم الاشتراك ✅", callback_data="check_subscription"))
        MM.send_message(mm.chat.id, "❌ *عذرًا، يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:*", parse_mode="Markdown", reply_markup=markup)
        return

    main_menu(mm)

def main_menu(mm):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📥 تحميل فيديو", callback_data='download_videos'),
        InlineKeyboardButton("📢 قناتنا", url='https://t.me/YYQJQ'),
        InlineKeyboardButton("🤝 مشاركة البوت", switch_inline_query="")
    )
    if mm.from_user.id == YOUR_ADMIN_ID:
        markup.add(
            InlineKeyboardButton("👥 عرض عدد المستخدمين", callback_data='users_count'),
            InlineKeyboardButton("⚙️ إدارة البوت", callback_data='admin_menu')
        )

    MM.send_message(
        mm.chat.id,
        f"🎉 *مرحبًا بك عزيزي: 《{mm.from_user.first_name}》📝.*\n\n"
        "- يمكنك التنزيل من مواقع متعددة بتنسيقات مختلفة والإستماع إليها في أي وقت.\n\n"
        "- المواقع المدعومة: (Youtube، Instagram، Facebook، Twitter، Tiktok، Snapchat، Soundcloud، pinterest، Likee، kwai).",
        parse_mode="Markdown",
        reply_markup=markup
    )

# خاص بالمدير
@MM.callback_query_handler(func=lambda call: call.data == 'admin_menu')
def admin_menu(call):
    if call.from_user.id == YOUR_ADMIN_ID:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📝 إرسال رسالة لجميع المستخدمين", callback_data='broadcast_message'),
            InlineKeyboardButton("➕ إضافة قناة للاشتراك الإجباري", callback_data='add_channel'),
            InlineKeyboardButton("🗑 حذف قناة من الاشتراك الإجباري", callback_data='remove_channel'),
            InlineKeyboardButton("⚙️ إيقاف أو تشغيل البوت", callback_data='toggle_bot')
        )
        MM.edit_message_text("اختر الخيار الذي ترغب فيه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    else:
        MM.answer_callback_query(call.id, "❌ هذا الخيار متاح فقط للمدير!")

@MM.callback_query_handler(func=lambda call: call.data == 'broadcast_message')
def broadcast_message(call):
    if call.from_user.id == YOUR_ADMIN_ID:
        MM.send_message(call.message.chat.id, "من فضلك، أرسل الرسالة التي تريد نشرها لجميع المستخدمين.")
        MM.register_next_step_handler(call.message, process_broadcast_message)
    else:
        MM.answer_callback_query(call.id, "❌ هذا الخيار متاح فقط للمدير!")

def process_broadcast_message(mm):
    message_type = None
    if mm.content_type == 'text':
        message_type = 'text'
    elif mm.content_type == 'photo':
        message_type = 'photo'
    elif mm.content_type == 'sticker':
        message_type = 'sticker'
    
    if message_type == 'text':
        message_to_broadcast = mm.text
        users = load_users()
        for user_id in users.keys():
            try:
                MM.send_message(user_id, message_to_broadcast)
            except Exception as e:
                print(f"خطأ في إرسال الرسالة للمستخدم {user_id}: {e}")
    elif message_type == 'photo':
        photo = mm.photo[-1].file_id  # أخذ أفضل صورة
        caption = mm.caption if mm.caption else ""
        users = load_users()
        for user_id in users.keys():
            try:
                MM.send_photo(user_id, photo, caption=caption)
            except Exception as e:
                print(f"خطأ في إرسال الصورة للمستخدم {user_id}: {e}")
    elif message_type == 'sticker':
        sticker = mm.sticker.file_id
        users = load_users()
        for user_id in users.keys():
            try:
                MM.send_sticker(user_id, sticker)
            except Exception as e:
                print(f"خطأ في إرسال الملصق للمستخدم {user_id}: {e}")
    MM.send_message(mm.chat.id, "تم إرسال الرسالة لجميع المستخدمين.")

@MM.callback_query_handler(func=lambda call: call.data == 'add_channel')
def add_channel(call):
    if call.from_user.id == YOUR_ADMIN_ID:
        MM.send_message(call.message.chat.id, "من فضلك، أرسل اسم القناة الجديدة (بدون @).")
        MM.register_next_step_handler(call.message, process_add_channel)
    else:
        MM.answer_callback_query(call.id, "❌ هذا الخيار متاح فقط للمدير!")

def process_add_channel(mm):
    new_channel_username = mm.text
    if new_channel_username not in [channel['username'] for channel in CHANNELS]:
        CHANNELS.append({"name": f"القناة {len(CHANNELS)+1}", "username": new_channel_username})
        save_channels()  # حفظ القنوات الجديدة
        MM.send_message(mm.chat.id, f"تم إضافة القناة @{new_channel_username} بنجاح.")
    else:
        MM.send_message(mm.chat.id, "هذه القناة موجودة بالفعل في القائمة.")

@MM.callback_query_handler(func=lambda call: call.data == 'remove_channel')
def remove_channel(call):
    if call.from_user.id == YOUR_ADMIN_ID:
        markup = InlineKeyboardMarkup()
        for channel in CHANNELS:
            markup.add(InlineKeyboardButton(f"حذف {channel['name']}", callback_data=f"remove_{channel['username']}"))
        MM.edit_message_text("اختر القناة التي تريد حذفها من الاشتراك الإجباري:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    else:
        MM.answer_callback_query(call.id, "❌ هذا الخيار متاح فقط للمدير!")

@MM.callback_query_handler(func=lambda call: call.data.startswith("remove_"))
def handle_remove_channel(call):
    if call.from_user.id == YOUR_ADMIN_ID:
        channel_to_remove = call.data.split('_')[1]
        global CHANNELS
        CHANNELS = [channel for channel in CHANNELS if channel['username'] != channel_to_remove]
        save_channels()
        MM.answer_callback_query(call.id, f"تم حذف القناة @{channel_to_remove} من الاشتراك الإجباري.")
        admin_menu(call.message)
    else:
        MM.answer_callback_query(call.id, "❌ هذا الخيار متاح فقط للمدير!")

@MM.callback_query_handler(func=lambda call: call.data == 'toggle_bot')
def toggle_bot(call):
    if call.from_user.id == YOUR_ADMIN_ID:
        bot_status = 'مفعل' if MM.is_polling else 'مغلق'
        if bot_status == 'مفعل':
            MM.send_message(call.message.chat.id, "تم إيقاف البوت.")
            MM.stop_polling()
        else:
            MM.send_message(call.message.chat.id, "تم تشغيل البوت.")
            MM.polling()
    else:
        MM.answer_callback_query(call.id, "❌ هذا الخيار متاح فقط للمدير!")

@MM.callback_query_handler(func=lambda call: call.data == 'users_count')
def users_count_handler(call):
    if call.from_user.id == YOUR_ADMIN_ID:
        users = load_users()
        MM.answer_callback_query(call.id, f"👥 إجمالي عدد المستخدمين: {len(users)}")
    else:
        MM.answer_callback_query(call.id, "❌ هذا الخيار متاح فقط للمدير!")

@MM.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_handler(call):
    if check_subscriptions(call.from_user.id):
        MM.answer_callback_query(call.id, "✅ شكراً لاشتراكك! يمكنك الآن استخدام البوت.")
        main_menu(call.message)
    else:
        MM.answer_callback_query(call.id, "❌ لم يتم الاشتراك في جميع القنوات المطلوبة!")

MM.polling()
