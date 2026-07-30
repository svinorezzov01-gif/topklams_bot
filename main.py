import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
)

# 1. Заглушка веб-сервера для Render (чтобы бот не падал по таймауту)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- НАСТРОЙКИ БОТА ---
TOKEN = "8968489810:AAGrqlSyaP-IIK2c5BS12C5vmA8EHSnemz8"  # Вставь сюда свой токен от BotFather
ADMIN_ID = 8836199481  # Впиши сюда свой цифровой Telegram ID для уведомлений
ADMIN_USERNAME = "@topklamsmanager"  # Менеджер для связи

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

GOLD_PRICE_PER_UNIT = 0.7  
user_balances = {}
reviews_list = []

# Состояния FSM
class Form(StatesGroup):
    waiting_for_topup_rubles = State()
    waiting_for_calc_rubles = State()
    waiting_for_calc_gold = State()
    waiting_for_skin_photo = State()

# --- КЛАВИАТУРЫ ---

def main_keyboard():
    kb = [
        [types.KeyboardButton(text="🛍️ Каталог"), types.KeyboardButton(text="💸 Пополнить")],
        [types.KeyboardButton(text="⭐ Вывести"), types.KeyboardButton(text="👤 Профиль")],
        [types.KeyboardButton(text="🧮 Калькулятор"), types.KeyboardButton(text="👨‍💻 Поддержка")],
        [types.KeyboardButton(text="ℹ️ О боте"), types.KeyboardButton(text="🎯 Халява")],
        [types.KeyboardButton(text="🎮 Сменить игру")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def cancel_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="go_main_menu")
    return builder.as_markup()

def calc_keyboard():
    kb = [
        [types.KeyboardButton(text="💰 Посчитать ₽ в G"), types.KeyboardButton(text="⭐ Посчитать G в ₽")],
        [types.KeyboardButton(text="🏠 Главное меню")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Каталог товаров со скриншота
PRODUCTS = {
    "pos_10": {"name": "💎 Чек позиций на 10 секунд", "rub": 50, "gold": 100},
    "klams_2": {"name": "💎 Кламси на 2 секунды", "rub": 70, "gold": 140},
    "pos_16": {"name": "💎 Чек позиций 16 секунд", "rub": 50, "gold": 75},
    "klams_15": {"name": "💎 Кламси 1.5 секунд", "rub": 70, "gold": 140},
    "pos_200": {"name": "💎 Чек позиций 200 секунд", "rub": 110, "gold": 225},
    "klams_13": {"name": "💎 Кламси 1.3 секунд", "rub": 65, "gold": 130},
    "pack_1": {"name": "✨ Пак: Кламси 1.3 сек + чек позиций 200 сек", "rub": 140, "gold": 300},
    "pack_2": {"name": "✨ Пак: Кламси 1.5 сек + чек позиций 10 сек", "rub": 100, "gold": 200},
}


# --- СТАРТ И МЕНЮ ---

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⚡ <b>Добро пожаловать в Topklams shop!</b>\n\nВыберите нужный раздел в меню ниже:",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

@router.callback_query(F.data == "go_main_menu")
async def go_main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🏠 Вы вернулись в главное меню:", reply_markup=main_keyboard())
    await callback.answer()

@router.message(F.text == "🏠 Главное меню")
async def go_main_menu_text(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Главное меню:", reply_markup=main_keyboard())


# --- 👤 ПРОФИЛЬ ---

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    balance = user_balances.get(user.id, 0.0)
    
    text = (
        "👤 <b>Ваш профиль:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.first_name}\n"
        f"💰 Ваш баланс: <b>{balance:.2f} G</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard())


# --- 🛍️ КАТАЛОГ И ПОКУПКА ---

@router.message(F.text == "🛍️ Каталог")
async def catalog_handler(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, item in PRODUCTS.items():
        builder.button(text=f"{item['name']} — {item['rub']}₽ / {item['gold']}г", callback_data=f"select_{key}")
    builder.button(text="🏠 Главное меню", callback_data="go_main_menu")
    builder.adjust(1)
    
    await message.answer(
        "📦 <b>Каталог товаров Top Klams:</b>\n\nВыберите интересующую вас позицию:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("select_"))
async def process_select_product(callback: CallbackQuery):
    product_key = callback.data.split("_", 1)[1]
    item = PRODUCTS.get(product_key)
    
    if not item:
        await callback.answer("Товар не найден!")
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Рубли ({item['rub']} ₽)", callback_data=f"pay_rub_{product_key}")
    builder.button(text=f"🟡 Голда ({item['gold']} G)", callback_data=f"pay_gold_{product_key}")
    builder.button(text="⬅️ Назад в каталог", callback_data="back_to_catalog")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📦 <b>{item['name']}</b>\n\n"
        f"💰 <b>Стоимость:</b>\n"
        f"• {item['rub']} рублей\n"
        f"• {item['gold']} голды\n\n"
        f"Выберите удобный способ оплаты:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, item in PRODUCTS.items():
        builder.button(text=f"{item['name']} — {item['rub']}₽ / {item['gold']}г", callback_data=f"select_{key}")
    builder.button(text="🏠 Главное меню", callback_data="go_main_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📦 <b>Каталог товаров Top Klams:</b>\n\nВыберите интересующую вас позицию:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Оплата голдой
@router.callback_query(F.data.startswith("pay_gold_"))
async def pay_gold_handler(callback: CallbackQuery, state: FSMContext):
    product_key = callback.data.split("_", 2)[2]
    item = PRODUCTS.get(product_key)
    user = callback.from_user
    
    await callback.message.edit_text(
        f"🟡 Вы выбрали оплату голдой за <b>{item['name']}</b> ({item['gold']} G).\n\n"
        f"⏳ Заявка отправлена менеджеру. Скоро вам пришлют скриншот скина для покупки.\n"
        f"Связь с менеджером: {ADMIN_USERNAME}",
        parse_mode="HTML",
        reply_markup=cancel_inline_keyboard()
    )
    
    if ADMIN_ID != 0:
        admin_text = (
            f"🔔 <b>Новый заказ за голду!</b>\n\n"
            f"👤 Покупатель: @{user.username or 'нет юзернейма'} (ID: <code>{user.id}</code>)\n"
            f"📦 Товар: {item['name']} — <b>{item['gold']} G</b>"
        )
        admin_builder = InlineKeyboardBuilder()
        admin_builder.button(text="📸 Прислать фото скина покупателю", callback_data=f"send_skin_{user.id}_{item['gold']}g")
        
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=admin_builder.as_markup())
    
    await callback.answer()

# Админ прикрепляет фото скина
@router.callback_query(F.data.startswith("send_skin_"))
async def admin_start_send_skin(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    buyer_id = parts[2]
    gold_amount = parts[3]
    
    await state.update_data(buyer_id=int(buyer_id), gold_amount=gold_amount)
    await state.set_state(Form.waiting_for_skin_photo)
    
    await callback.message.answer("📸 Отправьте **фотографию скина** (картинкой), который покупатель должен выставить на рынок:")
    await callback.answer()

@router.message(Form.waiting_for_skin_photo, F.photo)
async def admin_send_skin_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    buyer_id = data.get("buyer_id")
    gold_amount = data.get("gold_amount")
    photo = message.photo[-1].file_id
    
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="👨‍💻 Написать менеджеру", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")
        
        await bot.send_photo(
            chat_id=buyer_id,
            photo=photo,
            caption=(
                f"📸 <b>Менеджер прислал скин для покупки!</b>\n\n"
                f"Выставите этот скин на рынок ровно за <b>{gold_amount}</b>, "
                f"после чего отправьте скриншот успешной продажи менеджеру: {ADMIN_USERNAME}"
            ),
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        await message.answer("✅ Фото скина успешно отправлено покупателю!")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить фото покупателю: {e}")
    
    await state.clear()

# Оплата рублями
@router.callback_query(F.data.startswith("pay_rub_"))
async def pay_rub_handler(callback: CallbackQuery):
    product_key = callback.data.split("_", 2)[2]
    item = PRODUCTS.get(product_key)
    
    price_in_kopecks = item['rub'] * 100
    
    await callback.message.answer_invoice(
        title=item['name'],
        description=f"Покупка позиции {item['name']} в боте Top Klams",
        payload=f"buy_{product_key}",
        provider_token="",
        currency="RUB",
        prices=[LabeledPrice(label=item['name'], amount=price_in_kopecks)]
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await message.answer(
        "✅ <b>Оплата прошла успешно!</b>\n\n"
        f"Спасибо за покупку. Для получения товара отправьте скриншот чека менеджеру: {ADMIN_USERNAME}",
        parse_mode="HTML"
    )


# --- 💸 ПОПОЛНИТЬ И БАЛАНС ---

@router.message(F.text == "💸 Пополнить")
async def topup_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_for_topup_rubles)
    await message.answer(
        "💳 <b>Введите сумму для пополнения в рублях (₽):</b>\n_(Например: 100)_",
        parse_mode="HTML",
        reply_markup=cancel_inline_keyboard()
    )

@router.message(Form.waiting_for_topup_rubles, F.text.isdigit())
async def topup_process(message: types.Message, state: FSMContext):
    rubles = float(message.text)
    if rubles <= 0:
        await message.answer("❌ Сумма должна быть больше нуля.")
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

@router.message(Form.waiting_for_topup_rubles)
async def topup_invalid_input(message: types.Message):
    await message.answer("❌ <b>Пожалуйста, введите сумму числом (например, 100):</b>", parse_mode="HTML", reply_markup=cancel_inline_keyboard())

@router.callback_query(F.data == "mock_pay")
async def mock_pay_handler(callback: types.CallbackQuery):
    await callback.message.answer(
        f"Для оплаты переведите средства и напишите оператору: {ADMIN_USERNAME}",
        reply_markup=cancel_inline_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "test_add_balance")
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

@router.message(F.text == "⭐ Вывести")
async def withdraw_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0.0)
    
    await message.answer(
        f"⭐ <b>Вывод голды</b>\n\n"
        f"Ваш текущий баланс: <b>{balance:.2f} G</b>\n\n"
        f"Для вывода средств обратитесь к оператору: {ADMIN_USERNAME}",
        parse_mode="HTML",
        reply_markup=cancel_inline_keyboard()
    )


# --- ℹ️ О БОТЕ И ОСТАЛЬНОЕ ---

@router.message(F.text == "ℹ️ О боте")
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

@router.message(F.text == "🧮 Калькулятор")
async def calc_menu_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✨ **Выберите вариант подсчета на клавиатуре:**",
        parse_mode="Markdown",
        reply_markup=calc_keyboard()
    )

@router.message(F.text == "💰 Посчитать ₽ в G")
async def calc_rubles_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_for_calc_rubles)
    await message.answer("💳 **Введите сумму в рублях (₽):**\n_(Например: 150)_", parse_mode="Markdown")

@router.message(Form.waiting_for_calc_rubles, F.text.isdigit())
async def calc_rubles_process(message: types.Message, state: FSMContext):
    rubles = float(message.text)
    gold = round(rubles / GOLD_PRICE_PER_UNIT, 2)
    await message.answer(
        f"📊 **Результат расчета:**\n\n💵 За **{rubles:.0f} ₽** вы получите: **{gold} G**",
        parse_mode="Markdown",
        reply_markup=calc_keyboard()
    )
    await state.clear()

@router.message(F.text == "⭐ Посчитать G в ₽")
async def calc_gold_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_for_calc_gold)
    await message.answer("🪙 **Введите количество голды (G):**\n_(Например: 500)_", parse_mode="Markdown")

@router.message(Form.waiting_for_calc_gold, F.text.isdigit())
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

@router.message(F.text == "👨‍💻 Поддержка")
async def support_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"По всем вопросам обращайтесь к оператору: {ADMIN_USERNAME}", reply_markup=cancel_inline_keyboard())

@router.message(F.text == "🎯 Халява")
async def bonus_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🎁 Раздел промокодов и бонусов временно пуст.", reply_markup=cancel_inline_keyboard())

@router.message(F.text == "🎮 Сменить игру")
async def change_game_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("На данный момент доступна только игра **Standoff 2**.", parse_mode="HTML", reply_markup=cancel_inline_keyboard())


# --- ЗАПУСК ---

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
