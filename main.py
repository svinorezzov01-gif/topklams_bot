import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# Токен твоего бота (замени на актуальный без лишних пробелов)
TOKEN = "8968489810:AAGrqlSyaP-IIK2c5BS12C5vmA8EHSnemz8"
ADMIN_ID = 8836199481  # <--- Замени на свой реальный Telegram ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Фабрика колбэков для товаров каталога
class CatalogCallback(CallbackData, prefix="item"):
    item_id: str

# Состояния для вывода средств и отправки КФГ админом
class WithdrawState(StatesGroup):
    waiting_for_amount = State()

class AdminSendCfgState(StatesGroup):
    waiting_for_cfg = State()

# Список товаров (название в каталоге чистое, цены и описание — внутри товара)
PRODUCTS = {
    "item_1": {"name": "💎 Чек позиций на 10 секунд", "price": "50₽ / 100г", "desc": "Быстрый чек позиций на 10 секунд."},
    "item_2": {"name": "💎 Кламси на 2 секунды", "price": "70₽ / 140г", "desc": "Кламси со скоростью на 2 секунды."},
    "item_3": {"name": "💎 Чек позиций 16 секунд", "price": "50₽ / 75г", "desc": "Чек позиций расширенный на 16 секунд."},
    "item_4": {"name": "💎 Кламси 1.5 секунд", "price": "70₽ / 140г", "desc": "Кламси со скоростью 1.5 сек."},
    "item_5": {"name": "💎 Чек позиций 200 секунд", "price": "110₽ / 225г", "desc": "Долгосрочный чек позиций на 200 секунд."},
    "item_6": {"name": "💎 Кламси 1.3 секунд", "price": "65₽ / 130г", "desc": "Ускоренный кламси на 1.3 секунды."},
    "item_7": {"name": "✨ Пак: Кламси 1.3 сек + чек позиций 200 сек", "price": "150₽ / 300г", "desc": "Выгодный комбинированный пак."},
    "item_8": {"name": "✨ Пак: Кламси 1.5 сек + чек позиций 10 сек", "price": "120₽ / 240г", "desc": "Стартовый игровой пак."},
}

# Главное меню
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Каталог", callback_data="open_catalog")
    builder.button(text="💰 Пополнить", callback_data="top_up")
    builder.button(text="⭐ Вывести", callback_data="withdraw")
    builder.button(text="📞 Связаться с оператором", url="https://t.me/topklamsmanager")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🏠 **Главное меню Top Klams Shop**\n\nДобро пожаловать! Выберите нужный раздел:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 **Главное меню Top Klams Shop**\n\nДобро пожаловать! Выберите нужный раздел:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Открытие каталога (только названия без цен)
@dp.callback_query(F.data == "open_catalog")
async def show_catalog_cb(callback: CallbackQuery):
    keyboard_builder = InlineKeyboardBuilder()
    for key, data in PRODUCTS.items():
        keyboard_builder.button(
            text=data["name"], 
            callback_data=CatalogCallback(item_id=key)
        )
    keyboard_builder.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard_builder.adjust(1)
    
    await callback.message.edit_text(
        "📦 **Каталог товаров Top Klams:**\n\nВыберите интересующую вас позицию:",
        reply_markup=keyboard_builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Просмотр конкретного товара (тут появляются цены и кнопка покупки)
@dp.callback_query(CatalogCallback.filter())
async def show_product_details(callback: CallbackQuery, callback_data: CatalogCallback):
    item = PRODUCTS.get(callback_data.item_id)
    if not item:
        await callback.answer("Товар не найден!", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Купить за голду", callback_data=f"pay_gold_{callback_data.item_id}")
    builder.button(text="🔙 Назад в каталог", callback_data="open_catalog")
    builder.adjust(1)

    await callback.message.edit_text(
        f"📦 **{item['name']}**\n\n"
        f"📝 {item['desc']}\n\n"
        f"💰 **Цена:** {item['price']}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
    # Пополнение баланса
@dp.callback_query(F.data == "top_up")
async def process_top_up(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "💳 Введите сумму для пополнения в рублях (₽):\n_(Например: 100)_",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Запрос вывода средств (баланс берется условный, интегрируй под свою БД)
@dp.callback_query(F.data == "withdraw")
async def start_withdrawal(callback: CallbackQuery, state: FSMContext):
    balance = 67690.00  # Пример твоего баланса
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        f"⭐ **Вывод голды**\n\n"
        f"Ваш текущий баланс: **{balance} G**\n\n"
        f"Введите сумму голды, которую хотите вывести:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(WithdrawState.waiting_for_amount)
    await callback.answer()

@dp.message(WithdrawState.waiting_for_amount)
async def process_withdrawal_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Пожалуйста, введите сумму цифрами:")
        return

    amount = int(message.text)
    await state.clear()

    await message.answer(
        f"✅ **Заявка на вывод успешно создана!**\n\n"
        f"Сумма: **{amount} G**\n"
        f"Ожидайте обработки администратором.",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

# Покупка товара за голду -> отправка заявки админу
@dp.callback_query(F.data.startswith("pay_gold_"))
async def process_gold_payment(callback: CallbackQuery):
    item_key = callback.data.split("_")[2]
    item = PRODUCTS.get(item_key)
    user = callback.from_user

    await callback.message.edit_text(
        f"✅ Оплата товара **{item['name']}** успешно произведена!\n\n"
        f"⏳ Ожидайте, администратор скоро пришлет вам КФГ после проверки покупки скина.",
        parse_mode="Markdown"
    )
    
    admin_text = (
        f"🔔 **Новая покупка за голду!**\n\n"
        f"👤 Покупатель: @{user.username} (ID: `{user.id}`)\n"
        f"📦 Товар: {item['name']}\n"
        f"💰 Цена: {item['price']}\n\n"
        f"👇 Нажмите кнопку ниже, чтобы отправить КФГ покупателю:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Отправить КФГ покупателю", callback_data=f"send_cfg_{user.id}")
    builder.adjust(1)
    
    await bot.send_message(ADMIN_ID, admin_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

# Шаг админа: запуск отправки КФГ
@dp.callback_query(F.data.startswith("send_cfg_"))
async def admin_start_send_cfg(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав!", show_alert=True)
        return
        
    buyer_id = callback.data.split("_")[2]
    await state.update_data(buyer_id=int(buyer_id))
    
    await callback.message.answer(
        "📁 Отправьте в ответ **файл конфигурации (.cfg, .txt)** или **текст с кфг**, который нужно передать покупателю:"
    )
    await state.set_state(AdminSendCfgState.waiting_for_cfg)
    await callback.answer()

# Получение КФГ от админа и доставка покупателю
@dp.message(AdminSendCfgState.waiting_for_cfg)
async def admin_send_cfg_to_buyer(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    data = await state.get_data()
    buyer_id = data.get("buyer_id")
    
    try:
        if message.document:
            await bot.send_document(
                chat_id=buyer_id,
                document=message.document.file_id,
                caption="✅ **Ваш товар (КФГ) успешно получен!** Спасибо за покупку в Top Klams Shop.",
                parse_mode="Markdown"
            )
        elif message.text:
            await bot.send_message(
                chat_id=buyer_id,
                text=f"✅ **Ваш товар (КФГ):**\n\n`{message.text}`\n\nСпасибо за покупку в Top Klams Shop!",
                parse_mode="Markdown"
            )
            
        await message.answer("✅ КФГ успешно отправлен покупателю!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки (возможно, пользователь заблокировал бота): {e}")
        
    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
