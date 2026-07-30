import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

ADMIN_ID = 8836199481
ADMIN_USERNAME = "@topklamsmanager"

BOT_TOKEN = "8968489810:AAHWVtnM3ehigxF40wJzHmn1hR8z-p-iCmE"
GOLD_PRICE_PER_UNIT = 0.7  # 1 G = 0.7 ₽

SKIN_PHOTO_ID = None
START_PHOTO_ID = None

reviews_list = []

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

user_balances = {}


class Form(StatesGroup):
    waiting_for_topup_rubles = State()
    waiting_for_withdraw_gold = State()
    waiting_for_withdraw_photo = State()
    waiting_for_calc_rubles = State()
    waiting_for_calc_gold = State()
    waiting_for_admin_skin = State()
    waiting_for_admin_start_photo = State()
    waiting_for_review_comment = State()


# --- КЛАВИАТУРЫ ---

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="💸 Пополнить")
    builder.button(text="⭐ Вывести")
    builder.button(text="👤 Профиль")
    builder.button(text="🧮 Калькулятор")
    builder.button(text="🛍️ Каталог")
    builder.button(text="👨‍💻 Поддержка")
    builder.button(text="ℹ️ О боте")
    builder.button(text="🎯 Халява")
    builder.button(text="🎮 Сменить игру")
    builder.adjust(3, 3, 3)
    return builder.as_markup(resize_keyboard=True)

def calc_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="💰 Посчитать ₽ в G")
    builder.button(text="⭐ Посчитать G в ₽")
    builder.button(text="🏠 Главное меню")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def cancel_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="go_main_menu")
    return builder.as_markup()

def rating_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ 1", callback_data="rate_1")
    builder.button(text="⭐ 2", callback_data="rate_2")
    builder.button(text="⭐ 3", callback_data="rate_3")
    builder.button(text="⭐ 4", callback_data="rate_4")
    builder.button(text="⭐ 5", callback_data="rate_5")
    builder.button(text="Пропустить ❌", callback_data="rate_skip")
    builder.adjust(5, 1)
    return builder.as_markup()


# --- НАСТРОЙКИ АДМИНА ---

@dp.message(Command("setskin"))
async def set_skin_command(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    await state.set_state(Form.waiting_for_admin_skin)
    await message.answer(
        "📸 **Админ, отправь фото скина UMP45 Arid!**",
        parse_mode="Markdown"
    )

@dp.message(Form.waiting_for_admin_skin, F.photo)
async def process_admin_skin_photo(message: types.Message, state: FSMContext):
    global SKIN_PHOTO_ID
    SKIN_PHOTO_ID = message.photo[-1].file_id
    await state.clear()
    await message.answer("✅ **Картинка скина успешно сохранена!**", parse_mode="Markdown")


@dp.message(Command("setstartphoto"))
async def set_start_photo_command(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    await state.set_state(Form.waiting_for_admin_start_photo)
    await message.answer(
        "📸 **Админ, отправь фото для команды /start!**",
        parse_mode="Markdown"
    )

@dp.message(Form.waiting_for_admin_start_photo, F.photo)
async def process_admin_start_photo(message: types.Message, state: FSMContext):
    global START_PHOTO_ID
    START_PHOTO_ID = message.photo[-1].file_id
    await state.clear()
    await message.answer("✅ **Приветственное фото сохранено!**", parse_mode="Markdown")


# --- ОБРАБОТКА /START И МЕНЮ ---

@dp.message(Command("start"))
async def start_command_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    start_caption = (
        "<b>Что умеет этот бот?</b>\n\n"
        "Приветствуем тебя в нашем боте 👋\n\n"
        "Здесь ты сможешь честно и выгодно купить донат\n\n"
        "Наши отзывы - @topklams_otz"
    )

    if START_PHOTO_ID:
        try:
            await message.answer_photo(
                photo=START_PHOTO_ID,
                caption=start_caption,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Ошибка отправки фото start: {e}")
            await message.answer(start_caption, parse_mode="HTML")
    else:
        await message.answer(start_caption, parse_mode="HTML")

    await message.answer(
        "🏠 <b>Главное меню</b>\n"
        "Для взаимодействия с ботом используй клавиатуру\n\n"
        "Если у вас возникли вопросы обращайтесь в поддержку 📝",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "🏠 Главное меню")
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 <b>Главное меню</b>\n"
        "Для взаимодействия с ботом используй клавиатуру\n\n"
        "Если у вас возникли вопросы обращайтесь в поддержку 📝",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

@dp.callback_query(F.data == "go_main_menu")
async def process_main_menu_inline(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n"
        "Для взаимодействия с ботом используй клавиатуру\n\n"
        "Если у вас возникли вопросы обращайтесь в поддержку 📝",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )
    await callback.answer()


# --- 👤 ПРОФИЛЬ ---

@dp.message(F.text == "👤 Профиль")
async def profile_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0.0)
    await message.answer(
        f"👤 <b>Ваш профиль:</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Имя: {message.from_user.first_name}\n"
        f"💰 Ваш баланс: <b>{balance:.2f} G</b>",
        parse_mode="HTML",
        reply_markup=cancel_inline_keyboard()
  )
          # --- 💸 ПОПОЛНЕНИЕ ---

@dp.message(F.text == "💸 Пополнить")
async def topup_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_for_topup_rubles)
    await message.answer(
        "🍯 <b>Введите сумму в ₽, на которую хотите закупиться</b>\n"
        "<i>(Минимальная сумма пополнения: 70 ₽)</i>",
        parse_mode="HTML",
        reply_markup=cancel_inline_keyboard()
    )

@dp.message(Form.waiting_for_topup_rubles, F.text.isdigit())
async def topup_process(message: types.Message, state: FSMContext):
    rubles = float(message.text)
    
    if rubles < 70:
        await message.answer(
            "❌ <b>Минимальная сумма пополнения — 70 ₽!</b>\n"
            "Введите сумму от 70 и выше:",
            parse_mode="HTML",
            reply_markup=cancel_inline_keyboard()
        )
        return

    gold = round(rubles / GOLD_PRICE_PER_UNIT, 2)
    await state.update_data(topup_gold=gold)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Связаться с оператором", callback_data="mock_pay")
    builder.button(text="🧪 [Тест] Симулировать успешную оплату", callback_data="test_add_balance")
    builder.button(text="🏠 Главное меню", callback_data="go_main_menu")
    builder.adjust(1)

    await message.answer(
        f"За <b>{rubles:.0f} ₽</b> вы получите: <b>{gold} G</b>\n\n"
        "Сообщение об успешной оплате придет автоматически через 1-5 мин",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

@dp.message(Form.waiting_for_topup_rubles)
async def topup_invalid_input(message: types.Message):
    await message.answer("❌ <b>Пожалуйста, введите сумму числом (например, 100):</b>", parse_mode="HTML", reply_markup=cancel_inline_keyboard())

@dp.callback_query(F.data == "mock_pay")
async def mock_pay_handler(callback: types.CallbackQuery):
    await callback.message.answer(
        f"Для оплаты переведите средства и напишите оператору: {ADMIN_USERNAME}",
        reply_markup=cancel_inline_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "test_add_balance")
async def test_add_balance_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    gold_to_add = data.get("topup_gold", 100.0)
    user_id = callback.from_user.id
    
    user_balances[user_id] = round(user_balances.get(user_id, 0.0) + gold_to_add, 2)
    
    await callback.message.answer(
        f"✅ <b>Тестовое пополнение прошло успешно!</b>\n"
        f"Вам начислено: <b>{gold_to_add} G</b>\n"
        f"Текущий баланс: <b>{user_balances[user_id]:.2f} G</b>",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )
    await state.clear()
    await callback.answer()


# --- ⭐ ВЫВОД ---

@dp.message(F.text == "⭐ Вывести")
async def withdraw_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0.0)

    if balance < 100:
        await message.answer(
            "❌ <b>Недостаточно голды для вывода!</b>\n\n"
            f"Ваш текущий баланс: <b>{balance:.2f} G</b>\n"
            "📦 Минимальная сумма для вывода: <b>100 G</b>.\n"
            "Пополните баланс через раздел «💸 Пополнить».",
            parse_mode="HTML",
            reply_markup=cancel_inline_keyboard()
        )
        return

    await state.set_state(Form.waiting_for_withdraw_gold)
    await message.answer(
        f"<b>Шаг 1 из 2:</b>\n"
        f"Ваш баланс: <b>{balance:.2f} G</b>\n\n"
        f"Введите количество голды для вывода (минимум 100 G):",
        parse_mode="HTML",
        reply_markup=cancel_inline_keyboard()
    )

@dp.message(Form.waiting_for_withdraw_gold, F.text.isdigit())
async def withdraw_gold_step(message: types.Message, state: FSMContext):
    amount = float(message.text)
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0.0)

    if amount < 100:
        await message.answer(
            "❌ <b>Минимальная сумма вывода — 100 G!</b>\n"
            "Введите сумму от 100 и выше:",
            parse_mode="HTML",
            reply_markup=cancel_inline_keyboard()
        )
        return

    if amount > balance:
        await message.answer(
            f"❌ Вы не можете вывести больше, чем у вас есть!\n"
            f"Ваш баланс: <b>{balance:.2f} G</b>. Введите меньшую сумму:",
            parse_mode="HTML",
            reply_markup=cancel_inline_keyboard()
        )
        return

    base_price = amount * 1.25
    random_cents = round(random.uniform(0.01, 0.09), 2)
    price_with_commission = round(base_price + random_cents, 2)

    await state.update_data(withdraw_amount=amount, market_price=price_with_commission)
    await state.set_state(Form.waiting_for_withdraw_photo)

    caption_text = (
        f"<b>Шаг 2 из 2: Инструкция по выставлению</b>\n\n"
        f"1. Зайдите в Standoff 2 на рынок.\n"
        f"2. Найдите скин: <b>UMP45 \"Arid\"</b>\n"
        f"3. Выставьте его на продажу ровно за: <b>{price_with_commission} G</b>\n"
        f"<i>(Вы получите чистыми {amount:.0f} G с учетом комиссии рынка)</i>\n\n"
        f"📸 После этого отправьте <b>скриншот</b> выставленного скина сюда:"
    )

    if SKIN_PHOTO_ID:
        try:
            await message.answer_photo(
                photo=SKIN_PHOTO_ID,
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=cancel_inline_keyboard()
            )
        except Exception:
            await message.answer(caption_text, parse_mode="HTML", reply_markup=cancel_inline_keyboard())
    else:
        await message.answer(caption_text, parse_mode="HTML", reply_markup=cancel_inline_keyboard())

@dp.message(Form.waiting_for_withdraw_gold)
async def withdraw_invalid_input(message: types.Message):
    await message.answer("❌ <b>Пожалуйста, введите число голды для вывода:</b>", parse_mode="HTML", reply_markup=cancel_inline_keyboard())

@dp.message(Form.waiting_for_withdraw_photo, F.photo)
async def withdraw_photo_step(message: types.Message, state: FSMContext):
    global SKIN_PHOTO_ID
    if not SKIN_PHOTO_ID:
        SKIN_PHOTO_ID = message.photo[-1].file_id

    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    user = message.from_user
    amount = float(data.get('withdraw_amount', 0))
    market_price = data.get('market_price', 0)

    if amount > 0:
        user_balances[user.id] = round(user_balances.get(user.id, 0.0) - amount, 2)
        new_balance = user_balances[user.id]

        await message.answer(
            "✅ <b>Заявка на вывод успешно отправлена!</b>\n\n"
            f"Списано с баланса: <b>{amount:.0f} G</b>\n"
            f"Остаток на балансе: <b>{new_balance:.2f} G</b>\n\n"
            "Оператор выкупит ваш скин в ближайшее время.",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

        admin_text = (
            f"🚨 <b>НОВАЯ ЗАЯВКА НА ВЫКУП!</b>\n\n"
            f"👤 Покупатель: @{user.username or 'нет_юзернейма'} (ID: <code>{user.id}</code>)\n"
            f"💰 Вывод чистыми: <b>{amount:.0f} G</b>\n"
            f"🎯 Скин: <b>UMP45 \"Arid\"</b>\n"
            f"🏷 Выставлен за уникальную цену: <b>{market_price} G</b>"
        )

        try:
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ошибка при отправке заявки админу: {e}")

        await state.clear()

        await message.answer(
            "⭐ <b>Пожалуйста, оцените качество обслуживания:</b>\n"
            "Ваша оценка помогает нам становиться лучше!",
            parse_mode="HTML",
            reply_markup=rating_inline_keyboard()
        )


# --- 📝 ОЦЕНКИ И ОТЗЫВЫ ---

@dp.callback_query(F.data.startswith("rate_"))
async def process_rating(callback: types.CallbackQuery, state: FSMContext):
    rate_val = callback.data.split("_")[1]

    if rate_val == "skip":
        await callback.message.edit_text("Спасибо за покупку! Ждем вас снова! 😉")
        await callback.answer()
        return

    rating = int(rate_val)
    await state.update_data(review_rating=rating)
    await state.set_state(Form.waiting_for_review_comment)

    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить комментарий ➡️", callback_data="skip_comment")

    await callback.message.edit_text(
        f"Вы поставили: <b>{rating} ⭐</b>\n\n"
        "✍️ **Напишите ваш отзыв или комментарий к покупке** (или нажмите кнопку ниже, чтобы пропустить):",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.message(Form.waiting_for_review_comment, F.text)
async def process_review_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rating = data.get("review_rating", 5)
    comment = message.text
    user = message.from_user

    reviews_list.append({
        "rating": rating,
        "text": comment,
        "user": user.username or user.first_name
    })

    await message.answer("🎉 **Спасибо за ваш отзыв! Нам очень приятно.**", parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "skip_comment")
async def skip_comment_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating = data.get("review_rating", 5)
    user = callback.from_user

    reviews_list.append({
        "rating": rating,
        "text": "Без комментария",
        "user": user.username or user.first_name
    })

    await callback.message.edit_text("🎉 **Спасибо за вашу оценку!**", parse_mode="Markdown")
    await state.clear()
    await callback.answer()


# --- ℹ️ О БОТЕ И ОСТАЛЬНЫЕ КНОПКИ ---

@dp.message(F.text == "ℹ️ О боте")
async def about_handler(message: types.Message, state: FSMContext):
    await state.clear()
    total_reviews = len(reviews_list)
    avg_rating = round(sum(r['rating'] for r in reviews_list) / total_reviews, 2) if total_reviews > 0 else 5.0
    stars_str = "⭐" * int(round(avg_rating))

    text = (
        "⚡ <b>Topklams shop — молниеносный вывод товара на ваш аккаунт!</b>\n\n"
        "Ежедневно нам доверяют десятки людей, не упусти выгоду и ты! 👇\n\n"
        f"✨ Средняя оценка: <b>{stars_str} ({avg_rating}/5)</b>\n"
        f"📝 Всего отзывов: <b>{total_reviews}</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=cancel_inline_keyboard())

@dp.message(F.text == "🧮 Калькулятор")
async def calc_menu_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✨ **Выберите вариант подсчета на клавиатуре:**",
        parse_mode="Markdown",
        reply_markup=calc_keyboard()
    )

@dp.message(F.text == "💰 Посчитать ₽ в G")
async def calc_rubles_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_for_calc_rubles)
    await message.answer("💳 **Введите сумму в рублях (₽):**\n_(Например: 150)_", parse_mode="Markdown")

@dp.message(Form.waiting_for_calc_rubles, F.text.isdigit())
async def calc_rubles_process(message: types.Message, state: FSMContext):
    rubles = float(message.text)
    gold = round(rubles / GOLD_PRICE_PER_UNIT, 2)
    await message.answer(
        f"📊 **Результат расчета:**\n\n💵 За **{rubles:.0f} ₽** вы получите: **{gold} G**",
        parse_mode="Markdown",
        reply_markup=calc_keyboard()
    )
    await state.clear()

@dp.message(F.text == "⭐ Посчитать G в ₽")
async def calc_gold_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_for_calc_gold)
    await message.answer("🪙 **Введите количество голды (G):**\n_(Например: 500)_", parse_mode="Markdown")

@dp.message(Form.waiting_for_calc_gold, F.text.isdigit())
async def calc_gold_process(message: types.Message, state: FSMContext):
    gold = int(message.text)
    rubles = round(gold * GOLD_PRICE_PER_UNIT, 2)
    market_price = round(gold * 1.25, 2)
    await message.answer(
        f"📊 **Результат расчета:**\n\n🪙 За **{gold} G** нужно заплатить: **{rubles} ₽**\n🏷 На рынке выставлять за: ~**{market_price} G**",
        parse_mode="Markdown",
        reply_markup=calc_keyboard()
    )
    await state.clear()

@dp.message(F.text == "🛍️ Каталог")
async def catalog_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📦 Воспользуйтесь кнопкой «💸 Пополнить» для покупки голды!", reply_markup=cancel_inline_keyboard())

@dp.message(F.text == "👨‍💻 Поддержка")
async def support_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"По всем вопросам обращайтесь к оператору: {ADMIN_USERNAME}", reply_markup=cancel_inline_keyboard())

@dp.message(F.text == "🎯 Халява")
async def bonus_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🎁 Раздел промокодов и бонусов временно пуст.", reply_markup=cancel_inline_keyboard())

@dp.message(F.text == "🎮 Сменить игру")
async def change_game_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("На данный момент доступна только игра **Standoff 2**.", reply_markup=cancel_inline_keyboard())


# --- ЗАПУСК ---

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
