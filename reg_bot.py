# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ContextTypes
import json, os, asyncio, logging, re

user_map = {}

TOKEN         = "8624449565:AAHqQwaSpm0WjI3JJqSruhnhWcNKCY2Mduo"
ADMIN         = "https://t.me/STC_01?text=Halo%20admin%20ini%20ID%20saya%20:"
ADMIN_CHAT_ID = 7895551759

APK_FILE_ID = "BQACAgUAAxkBAAMMaeCv3fvYte1LQP2MZ7RZ6cPRHkUAAuMkAALY_9lW5StK1bZp4OI7BA"
MENU_PHOTO  = "AgACAgUAAxkBAAMKaeCvzyc-vV6MEedlx73XvJ4NaYsAAhkQaxuHmQlXVci1_ODyJC8BAAMCAAN3AAM7BA"
DATA_FILE   = "users.json"

logging.basicConfig(level=logging.INFO)

# ===== AUTO DELETE =====
async def auto_delete(message, delay=120, skip=False):
    if skip:
        return
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        print("Delete error:", e)

# ===== DATABASE =====
def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            print("Load error:", e)
            return {}
    return {}

def save_users(data):
    json.dump(data, open(DATA_FILE, "w"), indent=2)

users = load_users()

# ===== LOCK BUTTON =====
active_buttons = {}

def is_button_active(chat_id, button_key):
    return active_buttons.get((chat_id, button_key), False)

def set_button_active(chat_id, button_key, status=True):
    active_buttons[(chat_id, button_key)] = status

async def unlock_button_after(chat_id, button_key, delay):
    await asyncio.sleep(delay)
    set_button_active(chat_id, button_key, False)

# ===== ADMIN MAP =====
pending_map = {}

def is_private(update: Update):
    return update.effective_chat and update.effective_chat.type == "private"

# ===== MENU AWAL =====
async def menu_awal(update):
    keyboard = [
        [InlineKeyboardButton("1. Daftar akun baru", callback_data="daftar")],
        [InlineKeyboardButton("2. Sudah punya akun", callback_data="sudah")]
    ]
    sent = await update.message.reply_text(
        "Hallo kak Untuk aktivasi atau daftar akun silahkan pilih tombol di bawah ini :",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(sent, 120))

# ===== PIN START =====
async def pin_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("START", callback_data="start_menu")]]
    msg = await update.message.reply_text(
        "Untuk Aktivasi akun silahkan Klik tombol di bawah untuk membuka menu:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    try:
        await msg.pin()
    except:
        pass

# ===== FORWARD USER KE ADMIN =====
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg  = update.message
    user = msg.from_user
    log_text = (
        f"\n📩 CHAT MASUK\n"
        f"Nama: {user.first_name}\n"
        f"Username: @{user.username}\n"
        f"ID: {user.id}\n"
        f"Pesan:\n{msg.text}\n"
        f"-------------------\n"
    )
    sent = await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=log_text)
    pending_map[sent.message_id] = user.id
    try:
        forwarded = await context.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=msg.chat.id,
            message_id=msg.message_id
        )
        pending_map[forwarded.message_id] = user.id
    except Exception as e:
        print("Forward error:", e)

# ===== ADMIN REPLY SYSTEM =====
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.chat.id != ADMIN_CHAT_ID:
        return
    if not msg.reply_to_message:
        return
    user_id = pending_map.get(msg.reply_to_message.message_id)
    if not user_id:
        print("USER TIDAK KETEMU:", msg.reply_to_message.message_id)
        return
    await context.bot.send_message(chat_id=user_id, text=f"💬 Admin reply:\n\n{msg.text}")

# ===== MENU START =====
async def show_start_menu(query):
    chat_id = query.message.chat.id
    key = "start_menu"
    if is_button_active(chat_id, key):
        try:
            await query.answer("Tunggu menu sebelumnya...", show_alert=False)
        except:
            pass
        return
    set_button_active(chat_id, key, True)
    keyboard = [
        [InlineKeyboardButton("1. Daftar Akun baru",            callback_data="daftar")],
        [InlineKeyboardButton("2. Sudah punya akun",            callback_data="sudah")],
        [InlineKeyboardButton("3. Install aplikasi autotrade",  callback_data="install_apk")],
        [InlineKeyboardButton("4. Video Tutorial STC",          callback_data="tutorial")],
        [InlineKeyboardButton("5. Cara blokir akun",            callback_data="blokir_menu")],
        [InlineKeyboardButton("6. Berbicara dengan admin",      url=ADMIN)],
        [InlineKeyboardButton("7. Cara ubah kata sandi",        callback_data="ubah_password")],
        [InlineKeyboardButton("8. Akun Tidak Aktif",            callback_data="akun_tidak_aktif")]
    ]
    sent = await query.message.reply_photo(
        photo=MENU_PHOTO,
        caption="*MENU STC AUTOTRADE*\n\nAktivasi akun Silahkan pilih menu di bawah:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(sent, 300))
    asyncio.create_task(unlock_button_after(chat_id, key, 300))

# ===== INSTALL APK =====
async def install_apk_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("Aktivasi ke admin", url=ADMIN)]]
    sent1 = await query.message.reply_text(
        "Untuk download & install aplikasi STC autotrade pastikan Akun kamu sudah teraktivasi",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    sent2 = await query.message.reply_document(APK_FILE_ID)
    asyncio.create_task(auto_delete(sent1, 120))
    asyncio.create_task(auto_delete(sent2, 300))

# ======================================================
# ===== HANDLE PESAN (FULL + VIP ANTI TYPO) =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg  = update.message
    text = msg.text.lower() if msg.text else ""

    # ======================================================
    #  AUTO RESPON KEYWORD APK
    keywords = [
        "install","instal","intal","insall","instaal","instl",
        "download","donlod","donwload","dwnload","dwonload",
        "apk","aplikasi","apknya","apk nya","file apk",
        "app","apps","application","unduh","pasang","setup"
    ]
    pattern = r"(inst|insal|instal|apk|aplikasi|download|donlod|app)"
    if any(k in text for k in keywords) or re.search(pattern, text):
        keyboard = [[InlineKeyboardButton("Aktivasi ke admin", url=ADMIN)]]
        sent1 = await msg.reply_text(
            "Untuk download & install aplikasi STC autotrade pastikan Akun kamu sudah teraktivasi.\n\nKlik dan Install ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        sent2 = await msg.reply_document(APK_FILE_ID)
        asyncio.create_task(auto_delete(sent1, 120))
        asyncio.create_task(auto_delete(sent2, 300))
        return  # STOP

    # ======================================================
    #  AUTO RESPON VIP (ANTI TYPO)
    if text:
        vip_patterns = [
            r"\bvip\b",
            r"v\s*i\s*p",
            r"vj?p",
            r"viip+",
            r"veep",
            r"fip",
            r"join\s*v+i+p+",
            r"gabung\s*v+i+p+",
            r"masuk\s*v+i+p+",
            r"cara\s*(join|masuk)?\s*v+i+p+",
            r"grup\s*v+i+p+",
            r"group\s*v+i+p+",
            r"vip\s*group",
            r"vip\s*grup",
            r"grop\s*v+i+p+",
            r"grub\s*v+i+p+",
            r"masok\s*v+i+p+",
            r"msk\s*v+i+p+",
            r"jn\s*v+i+p+",
        ]
        if any(re.search(p, text) for p in vip_patterns):
            keyboard = [[InlineKeyboardButton("Hubungi admin", url=ADMIN)]]
            sent = await msg.reply_text(
                " *AKSES VIP STC AUTOTRADE*\n\n"
                "Untuk masuk VIP group pastikan akun kamu sudah teraktivasi di STC Autotrade.\n"
                "Silahkan hubungi admin untuk aktivasi.\n\n"
                "*Keuntungan masuk VIP:*\n\n"
                "1. Edukasi trading\n"
                "2. Materi Trading\n"
                "3. Robot autotrade permanent free\n"
                "4. Signal EA full 24 jam\n"
                "5. Signal Realtime update setiap hari\n"
                "6. Trading bareng dengan 6 mentor pilihan\n\n"
                " *Segera gabung VIP Sekarang (GRATIS)*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            asyncio.create_task(auto_delete(sent, 120))
            return  # STOP

    # ======================================================
    #  DETEKSI ID (ANGKA 6–12 DIGIT)
    match = re.search(r"\b\d{6,12}\b", text or "")
    if match:
        keyboard = [[InlineKeyboardButton("Kirim ID ke admin", url=ADMIN)]]
        sent = await msg.reply_text(
            "Silahkan kirimkan ID anda ke admin untuk proses aktivasi ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        asyncio.create_task(auto_delete(sent, 120))
        return  # STOP

    # ======================================================
    #  FORWARD KE ADMIN
    await forward_to_admin(update, context)

    # ======================================================
    #  FILE ID LOGGER
    file_id = None
    if msg.document:      file_id = msg.document.file_id
    elif msg.video:       file_id = msg.video.file_id
    elif msg.photo:       file_id = msg.photo[-1].file_id
    elif msg.audio:       file_id = msg.audio.file_id
    elif msg.voice:       file_id = msg.voice.file_id
    elif msg.video_note:  file_id = msg.video_note.file_id
    elif msg.sticker:     file_id = msg.sticker.file_id

    if file_id:
        sent = await msg.reply_text(f"📎 File ID:\n{file_id}")
        asyncio.create_task(auto_delete(sent, 120))
        return

    # ======================================================
    #  MENU AWAL
    await menu_awal(update)

# ===== BUTTON HANDLER =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    data    = query.data
    chat_id = query.message.chat.id
    await query.answer()

    if data == "start_menu":
        await show_start_menu(query)
        return

    if is_button_active(chat_id, data):
        try:
            await query.answer("Tunggu proses sebelumnya...", show_alert=False)
        except:
            pass
        return

    set_button_active(chat_id, data, True)

    if data == "daftar":
        keyboard = [
            [InlineKeyboardButton("Cara lihat ID", url="https://youtube.com/shorts/Q79NSH6__J8?si=QKSZxSfhohEZA89z")],
            [InlineKeyboardButton("Kirim ID ke admin", url=ADMIN)]
        ]
        sent = await query.message.reply_text(
            "Silahkan lakukan pendaftaran akun baru klik link berikut :\n\nhttps://stcbroker.id\n\n"
            "Setelah pendaftaran selesai, silahkan kirim ID akun contoh 180882779 kirim ke Admin.\n\n"
            "Untuk melihat ID akun silahkan lihat video klik disini :",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        asyncio.create_task(auto_delete(sent, 120))
        asyncio.create_task(unlock_button_after(chat_id, data, 120))

    elif data == "sudah":
        keyboard = [
            [InlineKeyboardButton("Cara melihat ID akun", url="https://youtube.com/shorts/Q79NSH6__J8?si=QKSZxSfhohEZA89z")],
            [InlineKeyboardButton("Kirim ID ke admin", url=ADMIN)]
        ]
        sent = await query.message.reply_text(
            "Jika sudah memiliki Akun silahkan kirim ID akun kamu contoh : 18070299 klik tombol berikut",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        asyncio.create_task(auto_delete(sent, 120))
        asyncio.create_task(unlock_button_after(chat_id, data, 120))

    elif data == "tutorial":
        keyboard = [[InlineKeyboardButton("Tonton Tutorial", url="https://youtu.be/JxCoITVwHu4?si=Vqutcl1FJ-NFWiyH")]]
        sent = await query.message.reply_text(
            "Silahkan tonton tutorial STC Autotrade:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        asyncio.create_task(auto_delete(sent, 120))
        asyncio.create_task(unlock_button_after(chat_id, data, 120))

    elif data == "blokir_menu":
        keyboard = [
            [InlineKeyboardButton("Video Cara Blokir", url="https://youtube.com/shorts/qfZrJhFq5y8?si=MCYzyDSgcfsoHweB")],
            [InlineKeyboardButton("Hubungi admin", url=ADMIN)]
        ]
        sent = await query.message.reply_text(
            "Ikuti langkah blokir akun melalui video berikut:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        asyncio.create_task(auto_delete(sent, 120))

    elif data == "ubah_password":
        keyboard = [
            [InlineKeyboardButton("Ubah Kata Sandi", url="https://stcbroker.id")],
            [InlineKeyboardButton("Lihat Video", url="https://youtube.com/shorts/K54KC4Bbrw0?si=4lrFAqqJ5pD7uNmN")]
        ]
        sent = await query.message.reply_text(
            "Untuk mengubah kata sandi silahkan klik link di bawah ini.\n\nJika masih bingung, silahkan tonton video tutorial:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        asyncio.create_task(auto_delete(sent, 120))
        asyncio.create_task(unlock_button_after(chat_id, data, 120))

    elif data == "akun_tidak_aktif":
        sent = await query.message.reply_text(
            "Jika akun TIDAK AKTIF di aplikasi STC Autotrade.\n\n"
            "Silahkan ikuti langkah - langkah berikut :\n\n"
            "1. Blokir akun lama : https://youtube.com/shorts/qfZrJhFq5y8?si=RWJfZiGOTA_56HcR\n\n"
            "2. Wajib Tutup semua tab setelah blokir akun lama.\n"
            "https://youtube.com/shorts/MsbWd_OvGf8?si=QR0nLd0hqmXurEsf\n\n"
            "3. Kemudian Daftar akun baru klik disini\n\n"
            "https://stcbroker.id\n\n"
            "4. Jika sudah Kirimkan ID baru ke saya untuk aktivasi.",
            disable_web_page_preview=True
        )
        asyncio.create_task(auto_delete(sent, 120))
        asyncio.create_task(unlock_button_after(chat_id, data, 120))

# ===== RUN =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",     pin_start_button))
app.add_handler(CommandHandler("startmenu", pin_start_button))
app.add_handler(CallbackQueryHandler(install_apk_button, pattern="install_apk"))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.REPLY,    admin_reply))
app.add_handler(MessageHandler(~filters.COMMAND, handle_message))

print("BOT STC AUTO TRADE SIAP!")
app.run_polling()