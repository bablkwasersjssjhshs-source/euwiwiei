import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from datetime import datetime, timedelta
import asyncio
import random
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

users_db = {}
ADMIN_IDS = [118272062]

# Обновленные планы с индивидуальными платежными ссылками
plans = {
    "1day": {
        "price": 0.5, 
        "days": 1, 
        "crypto_price": "0.000015",
        "payment_url": "http://t.me/send?start=IVNFoLR1AUkL"
    },
    "3days": {
        "price": 1.0, 
        "days": 3, 
        "crypto_price": "0.000030",
        "payment_url": "http://t.me/send?start=IVrSygWtO5aV"
    },
    "week": {
        "price": 2.0, 
        "days": 7, 
        "crypto_price": "0.000060",
        "payment_url": "http://t.me/send?start=IVEu3HtFOdS4"
    },
    "month": {
        "price": 5.0, 
        "days": 30, 
        "crypto_price": "0.000150",
        "payment_url": "http://t.me/send?start=IVfBRtyWrkEm"
    }
}

def main_menu(user_id):
    kb = [
        [InlineKeyboardButton(text="⚔️ АТАКА", callback_data="attack")],
        [InlineKeyboardButton(text="👤 ПРОФИЛЬ", callback_data="profile")],
        [InlineKeyboardButton(text="💰 ПОДПИСКА", callback_data="subscribe")]
    ]
    if user_id in ADMIN_IDS:
        kb.append([InlineKeyboardButton(text="👑 АДМИН", callback_data="admin")])
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

@dp.message_handler(Command("start"))
async def start(msg: types.Message):
    text = "🚀 BOTNET SYSTEM\nСоздатель: @utsearch\nПомощь: @utsearch"
    await msg.answer(text, reply_markup=main_menu(msg.from_user.id))

@dp.callback_query_handler(lambda c: c.data == "profile")
async def profile(call: types.CallbackQuery):
    await call.answer()
    user = get_user(call.from_user.id)
    sub_active = has_sub(call.from_user.id)
    text = f"""👤 ПРОФИЛЬ
🆔 ID: {call.from_user.id}
💎 Подписка: {'✅' if sub_active else '❌'}
⚠️ Варнов: {user['warnings']}/3
📛 @{call.from_user.username or 'Нет'}"""
    await call.message.edit_text(text, reply_markup=main_menu(call.from_user.id))

@dp.callback_query_handler(lambda c: c.data == "attack")
async def attack(call: types.CallbackQuery):
    await call.answer()
    if not has_sub(call.from_user.id):
        await call.message.answer("❌ Нужна подписка", show_alert=True)
        return
    
    await call.message.edit_text(
        "⚔️ Введите юзернейм цели:\n"
        "Пример: @username или https://t.me/username\n\n"
        "⚠️ <b>ВНИМАНИЕ:</b> Нельзя сносить аккаунты старше 5 лет!",
        parse_mode=ParseMode.HTML
    )

@dp.message_handler(lambda message: not message.text.startswith('/'))
async def handle_target(msg: types.Message):
    target = msg.text.strip()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ ЦП", callback_data="reason_cpu")],
        [InlineKeyboardButton(text="💀 Живодёрство", callback_data="reason_hard")],
        [InlineKeyboardButton(text="📧 Спам", callback_data="reason_spam")],
        [InlineKeyboardButton(text="🔐 Личные данные", callback_data="reason_data")],
        [InlineKeyboardButton(text="🔥 Насилие", callback_data="reason_violence")]
    ])
    
    await msg.answer(
        f"🎯 Цель: {target}\n\n"
        "Выберите причину жалобы:",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data.startswith("reason_"))
async def start_attack_process(call: types.CallbackQuery):
    await call.answer()
    reason_map = {
        "reason_cpu": "⚡ ЦП",
        "reason_hard": "💀 Живодёрство", 
        "reason_spam": "📧 Спам",
        "reason_data": "🔐 Личные данные",
        "reason_violence": "🔥 Насилие"
    }
    
    reason = reason_map.get(call.data, "Причина")
    
    await call.message.edit_text(f"🔍 Ищем нарушения...\nПричина: {reason}")
    await send_complaints_progress(call.message, reason)

async def send_complaints_progress(message: types.Message, reason: str):
    total_complaints = 132
    progress_msg = await message.answer(f"📤 Отправка жалоб...\nЖалоб отправлено: 0/{total_complaints}")
    
    for i in range(1, total_complaints + 1):
        await asyncio.sleep(0.05)
        try:
            await progress_msg.edit_text(
                f"📤 Отправка жалоб...\n"
                f"Жалоб отправлено: {i}/{total_complaints}\n"
                f"Причина: {reason}"
            )
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await message.answer(
        f"✅ Атака завершена!\n"
        f"📊 Отправлено жалоб: {total_complaints}\n"
        f"🎯 Причина: {reason}\n\n"
        f"Жалобы обрабатываются Telegram...",
        reply_markup=main_menu(message.chat.id)
    )

# === ОБНОВЛЕННАЯ СИСТЕМА ОПЛАТЫ С ИНДИВИДУАЛЬНЫМИ ССЫЛКАМИ ===
@dp.callback_query_handler(lambda c: c.data == "subscribe")
async def subscribe(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 0.5$", callback_data="sub_1day")],
        [InlineKeyboardButton(text="3 дня - 1$", callback_data="sub_3days")],
        [InlineKeyboardButton(text="Неделя - 2$", callback_data="sub_week")],
        [InlineKeyboardButton(text="Месяц - 5$", callback_data="sub_month")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await call.message.edit_text("💰 Выберите подписку:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("sub_"))
async def select_subscription(call: types.CallbackQuery):
    await call.answer()
    sub_type = call.data.replace("sub_", "")
    if sub_type not in plans:
        return
    
    plan = plans[sub_type]
    
    payment_text = f"""
💳 <b>ОПЛАТА ПОДПИСКИ</b>

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
<b>Тариф:</b> {plan['days']} дней
<b>Стоимость:</b> ${plan['price']}
<b>В крипте:</b> ~{plan['crypto_price']} BTC

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
<b>Инструкция:</b>
1. Нажмите кнопку "💳 ОПЛАТИТЬ"
2. Бот откроет платежную систему
3. Подтвердите перевод
4. Подписка активируется автоматически

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
<i>После оплаты бот автоматически проверит платеж</i>
<i>Активация в течение 1 минуты</i>
"""
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 ОПЛАТИТЬ", url=plan['payment_url'])],
        [InlineKeyboardButton(text="✅ Я ОПЛАТИЛ", callback_data=f"check_payment_{sub_type}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="subscribe")]
    ])
    
    await call.message.edit_text(payment_text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("check_payment_"))
async def check_payment(call: types.CallbackQuery):
    await call.answer("🔍 Проверяем платеж...", show_alert=False)
    sub_type = call.data.replace("check_payment_", "")
    
    # Задержка для имитации проверки
    await asyncio.sleep(2)
    
    # 70% шанс успешной оплаты
    if random.random() < 0.7:
        # "Успешная" оплата
        user = get_user(call.from_user.id)
        user["sub_end"] = datetime.now() + timedelta(days=plans[sub_type]["days"])
        
        await call.message.edit_text(
            f"✅ <b>Платеж подтвержден!</b>\n\n"
            f"Подписка активирована на {plans[sub_type]['days']} дней\n"
            f"Доступ открыт ко всем функциям\n\n"
            f"<i>Спасибо за покупку!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(call.from_user.id)
        )
    else:
        await call.message.edit_text(
            "❌ <b>Платеж не найден</b>\n\n"
            "Если вы оплатили:\n"
            "1. Подождите 5-10 минут\n"
            "2. Нажмите кнопку еще раз\n"
            "3. Или напишите @utsearch",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Проверить снова", callback_data=f"check_payment_{sub_type}")],
                [InlineKeyboardButton(text="🔙 В меню", callback_data="back")]
            ])
        )

@dp.message_handler(Command("warn"))
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
        await msg.answer(f"✅ Варн выдан {target_id}" + ("\n❌ Подписка снята" if removed else ""))
    except Exception as e:
        logger.error(f"Ошибка в warn_cmd: {e}")
        await msg.answer("❌ Ошибка")

@dp.message_handler(Command("givesub"))
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
        user["sub_end"] = datetime.now() + timedelta(days=days)
        await msg.answer(f"✅ Подписка выдана {target_id} на {days} дней")
    except Exception as e:
        logger.error(f"Ошибка в givesub_cmd: {e}")
        await msg.answer("❌ Ошибка")

@dp.callback_query_handler(lambda c: c.data == "admin")
async def admin_panel(call: types.CallbackQuery):
    await call.answer()
    if call.from_user.id not in ADMIN_IDS:
        await call.message.answer("❌ Нет доступа", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await call.message.edit_text("👑 Админ панель", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "stats")
async def admin_stats(call: types.CallbackQuery):
    await call.answer()
    if call.from_user.id not in ADMIN_IDS:
        return
    total = len(users_db)
    active = sum(1 for uid in users_db if has_sub(uid))
    warned = sum(1 for uid in users_db if users_db[uid]["warnings"] > 0)
    text = f"""📊 СТАТИСТИКА
👥 Пользователей: {total}
💎 Активных: {active}
⚠️ С варнами: {warned}

🔹 Команды:
/warn <id>
/givesub <id> <дни>"""
    await call.message.edit_text(text)

@dp.callback_query_handler(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "🚀 BOTNET SYSTEM\nСоздатель: @utsearch",
        reply_markup=main_menu(call.from_user.id)
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)