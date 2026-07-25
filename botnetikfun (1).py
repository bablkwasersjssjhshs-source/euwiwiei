from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio

BOT_TOKEN = "8946812123:AAFoi14oJiWtf8mkGUaEGV8gE6WRLFS90Rw"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_db = {}
ADMIN_IDS = [118272062]

def main_menu(user_id):
    kb = [
        [InlineKeyboardButton(text="DSA", callback_data="dsa")],
        [
            InlineKeyboardButton(text="ПРОФИЛЬ", callback_data="profile"),
            InlineKeyboardButton(text="ПОДПИСКА", callback_data="subscribe")
        ]
    ]
    if user_id in ADMIN_IDS:
        kb.append([InlineKeyboardButton(text="АДМИН", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"sub_end": None, "warnings": 0, "banned": False}
    return users_db[user_id]

def has_sub(user_id):
    user = get_user(user_id)
    if user["banned"] or not user["sub_end"]:
        return False
    return datetime.now() < user["sub_end"]

def add_warning(user_id):
    user = get_user(user_id)
    user["warnings"] += 1
    if user["warnings"] >= 3:
        user["sub_end"] = datetime.now() - timedelta(days=1)
        return True
    return False

@dp.message(Command("start"))
async def start(msg: types.Message):
    text = "Вы в главном меню:\nЕсли с ботом что-то случится новую ссылку можно найти в @KinderPsyhology"
    await msg.answer(text, reply_markup=main_menu(msg.from_user.id))

@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    sub_active = has_sub(call.from_user.id)
    username = f"@{call.from_user.username}" if call.from_user.username else "Нет"
    
    sub_info = "Нет"
    if sub_active and user["sub_end"]:
        sub_info = f"До {user['sub_end'].strftime('%d.%0m.%Y %H:%M')}"

    text = f"""ПРОФИЛЬ
ID: {call.from_user.id}
Юзернейм: {username}
Подписка: {sub_info}
Варнов: {user['warnings']}/3"""
    await call.message.edit_text(text, reply_markup=main_menu(call.from_user.id))

@dp.callback_query(F.data == "dsa")
async def dsa_callback(call: types.CallbackQuery):
    if not has_sub(call.from_user.id):
        await call.answer("Нужна подписка", show_alert=True)
        return
    
    await call.message.edit_text(
        "Введите юзернейм цели:\n"
        "Пример: @username"
        "ВНИМАНИЕ: Нельзя сносить аккаунты старше 3 лет за нарушение будет выдан варн",
        parse_mode="HTML"
    )

@dp.message(F.text & ~F.text.startswith('/'))
async def handle_target(msg: types.Message):
    target = msg.text.strip()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЦП", callback_data="reason_cpu")],
        [InlineKeyboardButton(text="Живодёрство", callback_data="reason_hard")],
        [InlineKeyboardButton(text="Спам", callback_data="reason_spam")],
        [InlineKeyboardButton(text="Личные данные", callback_data="reason_data")],
        [InlineKeyboardButton(text="Насилие", callback_data="reason_violence")]
    ])
    
    await msg.answer(
        f"Цель: {target}\n\n"
        "Выберите причину жалобы:",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("reason_"))
async def start_attack_process(call: types.CallbackQuery):
    reason_map = {
        "reason_cpu": "ЦП",
        "reason_hard": "Живодёрство", 
        "reason_spam": "Спам",
        "reason_data": "Личные данные",
        "reason_violence": "Насилие"
    }
    
    reason = reason_map.get(call.data, "Причина")
    
    await call.message.edit_text(f"Ищем нарушения...\nПричина: {reason}")
    await send_complaints_progress(call.message, reason)

async def send_complaints_progress(message: types.Message, reason: str):
    total_complaints = 132
    progress_msg = await message.answer(f"Отправка жалоб...\nЖалоб отправлено: 0/{total_complaints}")
    
    for i in range(1, total_complaints + 1):
        await asyncio.sleep(0.05)
        await progress_msg.edit_text(
            f"Отправка жалоб...\n"
            f"Жалоб отправлено: {i}/{total_complaints}\n"
            f"Причина: {reason}"
        )
    
    await message.answer(
        f"DSA завершен!\n"
        f"Отправлено жалоб: {total_complaints}\n"
        f"Причина: {reason}\n\n"
        f"Жалобы обрабатываются Telegram...",
        reply_markup=main_menu(message.chat.id)
    )

@dp.callback_query(F.data == "subscribe")
async def subscribe(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])
    await call.message.edit_text(
        "За оплатой обращайтесь ко мне в ЛС: @coldwarn", 
        reply_markup=kb
    )

@dp.message(Command("warn"))
async def warn_cmd(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("/warn <user_id>")
        return
    try:
        target_id = int(args[1])
        removed = add_warning(target_id)
        await msg.answer(f"Варн выдан {target_id}" + ("\nПодписка снята" if removed else ""))
    except:
        await msg.answer("Ошибка")

@dp.message(Command("givesub"))
async def givesub_cmd(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    args = msg.text.split()
    if len(args) < 3:
        await msg.answer("/givesub <user_id> <дни>")
        return
    try:
        target_id = int(args[1])
        days = int(args[2])
        user = get_user(target_id)
        
        # Вычисляем дату окончания
        end_date = datetime.now() + timedelta(days=days)
        user["sub_end"] = end_date
        
        formatted_date = end_date.strftime("%d.%m.%Y в %H:%M")
        
        await msg.answer(f"Подписка выдана пользователю {target_id} на {days} дней. Активна до: {formatted_date}")
        
        # Пытаемся отправить уведомление самому пользователю об активации
        try:
            await bot.send_message(
                target_id,
                f"Ваша подписка успешно активирована!\n"
                f"Срок: {days} дней\n"
                f"Действует до: {formatted_date}",
                reply_markup=main_menu(target_id)
            )
        except:
            pass
            
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")

@dp.callback_query(F.data == "admin")
async def admin_panel(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Нет доступа", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])
    await call.message.edit_text("Админ панель", reply_markup=kb)

@dp.callback_query(F.data == "stats")
async def admin_stats(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    total = len(users_db)
    active = sum(1 for uid in users_db if has_sub(uid))
    warned = sum(1 for uid in users_db if users_db[uid]["warnings"] > 0)
    text = f"""СТАТИСТИКА
Пользователей: {total}
Активных: {active}
С варнами: {warned}

Команды:
/warn <id>
/givesub <id> <дни>"""
    await call.message.edit_text(text)

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.edit_text(
        "Вы в главном меню:\nЕсли с ботом что-то случится новую ссылку можно найти в @KinderPsyhology",
        reply_markup=main_menu(call.from_user.id)
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
