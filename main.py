import os
TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
HF_API_KEY = os.environ.get('HF_API_KEY', '')  # Якщо не використовуєте HFimport logging
import logging
import time
import re
import asyncio
import requests
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler
)
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid
from datetime import datetime, timezone

# Завантаження конфігурації
load_dotenv()
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
HF_API_KEY = os.getenv("HF_API_KEY", "").strip()
NETLIFY_URL = os.getenv("NETLIFY_URL", "https://your-site.netlify.app").strip()

# Налаштування
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Стани розмови
MAIN_MENU, AGE, GENDER, FOCUS_AREA, CHALLENGE, FEEDBACK, FEEDBACK_REASON = range(7)

# Тексти
WELCOME_TEXT = (
    "🌿 Вітаю! Я — Mental Bot\n"
    "Твій особистий помічник для саморозвитку та продуктивності.\n\n"
    "Обери дію нижче 👇"
)

ABOUT_TEXT = (
    "ℹ️ *Про проект Mental*:\n\n"
    "Ми — команда ентузіастів, яка вірить, що кожен може стати кращою версією себе. "
    "Наша місія — допомогти тобі підвищити продуктивність та досягти цілей.\n\n"
    "Цей бот — твій персональний помічник, який:\n"
    "• Допомагає визначити пріоритети\n"
    "• Надає персоналізовані стратегії\n"
    "• Допомагає подолати прокрастинацію\n"
    "• Підтримує на шляху до твоїх цілей"
)

SOCIAL_TEXT = (
    "🌐 *Наші соціальні мережі та канали*:\n"
    "Слідкуй за нами на різних платформах, щоб отримувати корисні матеріали, поради та мотивацію!"
)

# Головне меню
def main_menu_keyboard():
    return [
        [InlineKeyboardButton("🧠 ОТРИМАТИ ПРОФІЛЬ", callback_data="get_profile")],
        [InlineKeyboardButton("📚 МОЇ ПРОФІЛІ", callback_data="my_profiles")],
        [InlineKeyboardButton("🌐 СОЦМЕРЕЖІ", callback_data="social")],
        [InlineKeyboardButton("❓ ПРО ПРОЕКТ", callback_data="about")]
    ]

# Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = main_menu_keyboard()
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# Обробник головного меню
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_profile":
        context.user_data.clear()
        keyboard = [
            [InlineKeyboardButton("18-24", callback_data="18-24")],
            [InlineKeyboardButton("25-34", callback_data="25-34")],
            [InlineKeyboardButton("35-44", callback_data="35-44")],
            [InlineKeyboardButton("45+", callback_data="45+")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]
        await query.edit_message_text(
            text="🔮 **Оберіть вашу вікову категорію:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return AGE
        
    elif query.data == "my_profiles":
        return await show_profiles(query, context)
        
    elif query.data == "social":
        keyboard = [
            [InlineKeyboardButton("📢 Наш Telegram-канал", url="https://t.me/ATeO682")],
            [InlineKeyboardButton("Instagram", url="https://instagram.com/")],
            [InlineKeyboardButton("TikTok", url="https://www.tiktok.com/uk-UA")],
            [InlineKeyboardButton("Patreon", url="https://www.patreon.com/ru-RU")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]
        await query.edit_message_text(
            text=SOCIAL_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return MAIN_MENU
        
    elif query.data == "about":
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
        await query.edit_message_text(
            text=ABOUT_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return MAIN_MENU
        
    elif query.data == "back":
        return await show_main_menu(query)
        
    return MAIN_MENU

# Питання 1: Вік
async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "back":
        return await show_main_menu(query)
    
    context.user_data['age'] = query.data
    
    # Питання 2: Стать
    keyboard = [
        [InlineKeyboardButton("Чоловік", callback_data="male")],
        [InlineKeyboardButton("Жінка", callback_data="female")],
        [InlineKeyboardButton("Інше/Не вказувати", callback_data="other")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    await query.edit_message_text(
        text="👤 **Оберіть вашу стать:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return GENDER

# Питання 2: Стать
async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "back":
        keyboard = [
            [InlineKeyboardButton("18-24", callback_data="18-24")],
            [InlineKeyboardButton("25-34", callback_data="25-34")],
            [InlineKeyboardButton("35-44", callback_data="35-44")],
            [InlineKeyboardButton("45+", callback_data="45+")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]
        await query.edit_message_text(
            text="🔮 **Оберіть вашу вікову категорію:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return AGE
    
    context.user_data['gender'] = query.data
    
    # Питання 3: Основна сфера фокусу
    keyboard = [
        [InlineKeyboardButton("Кар'єра та професійний ріст", callback_data="career")],
        [InlineKeyboardButton("Особисті стосунки", callback_data="relationships")],
        [InlineKeyboardButton("Фінансова стабільність", callback_data="finance")],
        [InlineKeyboardButton("Фізичне здоров'я", callback_data="health")],
        [InlineKeyboardButton("Психічний добробут", callback_data="wellbeing")],
        [InlineKeyboardButton("Особистий розвиток", callback_data="self_improvement")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    await query.edit_message_text(
        text="🎯 **У якій сфері ви хочете досягти найбільшого прогресу?**\n"
             "Цей вибір допоможе нам створити персоналізований план дій.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return FOCUS_AREA

# Питання 3: Основна сфера фокусу
async def handle_focus_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "back":
        keyboard = [
            [InlineKeyboardButton("Чоловік", callback_data="male")],
            [InlineKeyboardButton("Жінка", callback_data="female")],
            [InlineKeyboardButton("Інше/Не вказувати", callback_data="other")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]
        await query.edit_message_text(
            text="👤 **Оберіть вашу стать:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return GENDER
    
    context.user_data['focus_area'] = query.data
    
    # Контекстно-залежні питання
    questions = {
        "career": {
            "text": "💼 **Який професійний виклик для вас найактуальніший?**",
            "options": [
                ["Знайти нову роботу", "new_job"],
                ["Підвищити продуктивність", "productivity"],
                ["Подолати вигорання", "burnout"],
                ["Розвинути лідерські якості", "leadership"]
            ]
        },
        "relationships": {
            "text": "❤️ **Що для вас найважливіше у стосунках зараз?**",
            "options": [
                ["Покращити існуючі стосунки", "improve_relations"],
                ["Знайти партнера", "find_partner"],
                ["Вирішити конфлікти", "resolve_conflicts"],
                ["Побудувати здорові межі", "set_boundaries"]
            ]
        },
        "finance": {
            "text": "💰 **Який фінансовий пріоритет є найважливішим?**",
            "options": [
                ["Збільшити доходи", "increase_income"],
                ["Оптимізувати витрати", "optimize_expenses"],
                ["Створити фінансову подушку", "financial_cushion"],
                ["Почати інвестувати", "start_investing"]
            ]
        },
        "health": {
            "text": "💪 **На якому аспекті здоров'я ви хочете зосередитись?**",
            "options": [
                ["Покращити фізичну форму", "improve_fitness"],
                ["Налагодити харчування", "improve_nutrition"],
                ["Покращити сон", "improve_sleep"],
                ["Подолати хронічну втому", "overcome_fatigue"]
            ]
        },
        "wellbeing": {
            "text": "🧠 **Що найбільше впливає на ваш психічний стан?**",
            "options": [
                ["Зменшити стрес", "reduce_stress"],
                ["Підвищити самоповагу", "increase_selfesteem"],
                ["Подолати тривожність", "overcome_anxiety"],
                ["Знайти внутрішній баланс", "find_balance"]
            ]
        },
        "self_improvement": {
            "text": "🌱 **Який навик ви хочете розвинути в першу чергу?**",
            "options": [
                ["Подолати прокрастинацію", "overcome_procrastination"],
                ["Навчитись ефективно навчатись", "learn_to_learn"],
                ["Розвинути нову звичку", "develop_habit"],
                ["Покращити тайм-менеджмент", "improve_timemanagement"]
            ]
        }
    }
    
    q = questions[query.data]
    keyboard = [
        [InlineKeyboardButton(text, callback_data=data)] for text, data in q['options']
    ] + [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
    
    await query.edit_message_text(
        text=q['text'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CHALLENGE

# Питання 4: Конкретний запит та генерація профілю
async def handle_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "back":
        keyboard = [
            [InlineKeyboardButton("Кар'єра та професійний ріст", callback_data="career")],
            [InlineKeyboardButton("Особисті стосунки", callback_data="relationships")],
            [InlineKeyboardButton("Фінансова стабільність", callback_data="finance")],
            [InlineKeyboardButton("Фізичне здоров'я", callback_data="health")],
            [InlineKeyboardButton("Психічний добробут", callback_data="wellbeing")],
            [InlineKeyboardButton("Особистий розвиток", callback_data="self_improvement")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]
        await query.edit_message_text(
            text="🎯 **У якій сфері ви хочете досягти найбільшого прогресу?**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return FOCUS_AREA
    
    context.user_data['challenge'] = query.data
    
    # Повідомлення про процес створення
    processing_message = await query.edit_message_text(
        text="✨ Генеруємо ваш персональний профіль...",
        parse_mode="Markdown"
    )
    
    # Анімація завантаження
    messages = [
        "🔍 Аналізуємо ваші відповіді...",
        "📊 Створюємо персоналізований план...",
        "🎨 Додаємо останні штрихи..."
    ]
    
    for msg in messages:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=processing_message.message_id,
            text=msg,
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
    
    # Генерація профілю через AI
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        prompt = (
            f"Створи детальний психологічний профіль у форматі HTML. "
            f"Вік: {context.user_data['age']}, Стать: {context.user_data['gender']}. "
            f"Сфера фокусу: {context.user_data['focus_area']}. "
            f"Основна проблема: {context.user_data['challenge']}.\n\n"
            "Використовуй підзаголовки <h2>, списки <ul> та абзаци <p>."
        )
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
            headers=headers,
            json={"inputs": prompt},
            timeout=45
        )
        
        if response.status_code == 200:
            profile_content = response.json()[0]['generated_text']
        else:
            logger.error(f"HF API error: {response.status_code} - {response.text}")
            profile_content = "<h1>Помилка генерації</h1><p>Будь ласка, спробуйте пізніше</p>"
    except Exception as e:
        logger.error(f"AI generation error: {str(e)}")
        profile_content = "<h1>Помилка сервера</h1><p>Спробуйте ще раз через декілька хвилин</p>"
    
    # Збереження даних (оновлена частина)
    user_id = query.from_user.id
    profile_id = str(uuid.uuid4())  # Генеруємо UUID як строку
    profile_url = f"{NETLIFY_URL}/.netlify/functions/get-profile?id={profile_id}"
    
    try:
        profile_data = {
            "id": profile_id,
            "user_id": user_id,
            "username": query.from_user.username or f"user{user_id}",
            "first_name": query.from_user.first_name,
            "age_group": context.user_data['age'],
            "gender": context.user_data['gender'],
            "focus_area": context.user_data['focus_area'],
            "challenge": context.user_data['challenge'],
            "profile_content": profile_content,
            "profile_url": profile_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table("profiles").insert(profile_data).execute()
        context.user_data['profile_id'] = profile_id
        context.user_data['profile_url'] = profile_url
        
    except Exception as e:
        logger.error(f"Supabase save error: {str(e)}")
        profile_url = f"{NETLIFY_URL}/error"
        context.user_data['profile_url'] = profile_url
    
    # Надсилання результату
    user_name = query.from_user.first_name or "Друже"
    text = (
        f"✨ {user_name}, ваш особистий профіль готовий!\n\n"
        f"Перегляньте ваш персональний аналіз за посиланням:\n{profile_url}"
    )
    
    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=processing_message.message_id,
        text=text,
        parse_mode=None
    )
    
    # Запит зворотного зв'язку
    keyboard = [
        [InlineKeyboardButton("👍 Так, сподобалось!", callback_data="feedback_yes")],
        [InlineKeyboardButton("👎 Ні, не сподобалось", callback_data="feedback_no")]
    ]
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="💬 Чи сподобався вам ваш персональний профіль?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return FEEDBACK
# Обробник зворотного зв'язку
async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    try:
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
    except Exception as e:
        logger.error(f"Помилка видалення повідомлення: {str(e)}")
    
    if query.data == "feedback_yes":
        try:
            supabase.table("feedback").insert({
                "profile_id": context.user_data.get('profile_id'),
                "user_id": query.from_user.id,
                "liked": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Feedback save error: {str(e)}")
        
        keyboard = [
            [InlineKeyboardButton("💳 Підтримати проект", callback_data="donate")],
            [InlineKeyboardButton("📤 Поділитися профілем", switch_inline_query=f"Мій психологічний профіль: {context.user_data.get('profile_url', '')}")],
            [InlineKeyboardButton("🔙 Назад до меню", callback_data="back")]
        ]
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🎉 Раді, що вам сподобалось!\n\n"
                 "Якщо ви хочете підтримати наш проект, ви можете зробити донат. "
                 "Це допоможе нам розвивати бота та додавати нові функції.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return MAIN_MENU
        
    elif query.data == "feedback_no":
        try:
            supabase.table("feedback").insert({
                "profile_id": context.user_data.get('profile_id'),
                "user_id": query.from_user.id,
                "liked": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Feedback save error: {str(e)}")
        
        keyboard = [
            [InlineKeyboardButton("Недостатньо персоналізовано", callback_data="reason_not_personal")],
            [InlineKeyboardButton("Некорисні поради", callback_data="reason_not_helpful")],
            [InlineKeyboardButton("Поганий дизайн", callback_data="reason_bad_design")],
            [InlineKeyboardButton("Інша причина", callback_data="reason_other")]
        ]
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="😔 Шкодуємо, що вам не сподобалось.\n\n"
                 "Будь ласка, вкажіть причину, щоб ми могли покращити сервіс:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return FEEDBACK_REASON

# Обробник причини негативного відгуку
async def handle_feedback_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    reason = query.data.replace("reason_", "")
    
    try:
        supabase.table("feedback").update({
            "reason": reason
        }).eq("user_id", query.from_user.id).order("created_at", desc=True).limit(1).execute()
    except Exception as e:
        logger.error(f"Feedback reason save error: {str(e)}")
    
    keyboard = [[InlineKeyboardButton("🔙 Назад до меню", callback_data="back")]]
    
    await query.edit_message_text(
        text="🙏 Дякуємо за ваш відгук! Ми обов'язково врахуємо його при покращенні сервісу.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# Обробник донату
async def handle_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    text = (
        "💛 **Дякуємо за бажання підтримати наш проект!**\n\n"
        "Mental створюють українські студенти-психологи. Ваша підтримка допоможе:\n"
        "• Безкоштовно розвивати проект\n"
        "• Створювати нові інструменти аналізу\n"
        "• Допомагати іншим знайти себе\n\n"
        "[Тицьніть тут, щоб зробити донат](https://example.com/donate)"
    )
    
    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    return MAIN_MENU

# Показати збережені профілі
async def show_profiles(query, context):
    user_id = query.from_user.id
    try:
        response = supabase.table("profiles").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        profiles = response.data
        
        if not profiles:
            await query.edit_message_text(
                text="📭 У вас ще немає збережених профілів. Створіть перший!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
            )
            return MAIN_MENU
        
        keyboard = []
        for profile in profiles:
            created_date = datetime.fromisoformat(profile['created_at']).strftime("%d.%m.%Y")
            profile_name = f"{get_focus_label(profile['focus_area'])} - {get_challenge_label(profile['challenge'])} ({created_date})"
            keyboard.append([InlineKeyboardButton(profile_name, url=profile['profile_url'])])
        
        keyboard.append([InlineKeyboardButton("🗑️ Видалити профілі старші 30 днів", callback_data="delete_old")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        
        await query.edit_message_text(
            text="📚 Ваші збережені профілі:\n(натисніть, щоб переглянути)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Помилка отримання профілів: {e}")
        await query.edit_message_text(
            text="❗️ Сталася помилка при отриманні ваших профілів. Спробуйте пізніше.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
        )
        return MAIN_MENU

# Видалити старі профілі
async def delete_old_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    try:
        response = supabase.table("profiles").delete().eq("user_id", user_id).lt("created_at", cutoff_date).execute()
        deleted_count = len(response.data)
        
        await query.edit_message_text(
            text=f"✅ Видалено {deleted_count} старих профілів!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
        )
    except Exception as e:
        logger.error(f"Помилка видалення профілів: {e}")
        await query.edit_message_text(
            text="❗️ Сталася помилка при видаленні профілів. Спробуйте пізніше.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
        )
    
    return MAIN_MENU

# Функція для показу головного меню
async def show_main_menu(query):
    keyboard = main_menu_keyboard()
    await query.edit_message_text(
        text=WELCOME_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# Допоміжні функції
def get_gender_label(gender_code):
    labels = {
        "male": "Чоловік",
        "female": "Жінка",
        "other": "Інше/Не вказувати"
    }
    return labels.get(gender_code, "Не вказано")

def get_focus_label(focus_code):
    labels = {
        "career": "Кар'єра",
        "relationships": "Стосунки",
        "finance": "Фінанси",
        "health": "Здоров'я",
        "wellbeing": "Псих. добробут",
        "self_improvement": "Особ. розвиток"
    }
    return labels.get(focus_code, "Не вказано")

def get_challenge_label(challenge_code):
    labels = {
        "new_job": "Нова робота",
        "productivity": "Продуктивність",
        "burnout": "Вигорання",
        "leadership": "Лідерство",
        "improve_relations": "Покращити стосунки",
        "find_partner": "Знайти партнера",
        "resolve_conflicts": "Вирішити конфлікти",
        "set_boundaries": "Здорові межі",
        "increase_income": "Збільшити доходи",
        "optimize_expenses": "Оптимізувати витрати",
        "financial_cushion": "Фін. подушка",
        "start_investing": "Інвестування",
        "improve_fitness": "Фітнес",
        "improve_nutrition": "Харчування",
        "improve_sleep": "Сон",
        "overcome_fatigue": "Хронічна втома",
        "reduce_stress": "Зменшити стрес",
        "increase_selfesteem": "Самоповага",
        "overcome_anxiety": "Тривожність",
        "find_balance": "Внутр. баланс",
        "overcome_procrastination": "Прокрастинація",
        "learn_to_learn": "Ефективне навчання",
        "develop_habit": "Нові звички",
        "improve_timemanagement": "Тайм-менеджмент"
    }
    return labels.get(challenge_code, "Не вказано")

# Обробник помилок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update.message:
        await update.message.reply_text("❌ Сталася неочікувана помилка. Спробуйте ще раз пізніше.")

# Запуск бота
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu)],
            AGE: [CallbackQueryHandler(handle_age)],
            GENDER: [CallbackQueryHandler(handle_gender)],
            FOCUS_AREA: [CallbackQueryHandler(handle_focus_area)],
            CHALLENGE: [CallbackQueryHandler(handle_challenge)],
            FEEDBACK: [CallbackQueryHandler(handle_feedback)],
            FEEDBACK_REASON: [CallbackQueryHandler(handle_feedback_reason)]
        },
        fallbacks=[
            CallbackQueryHandler(main_menu, pattern="^back$"),
            CommandHandler('start', start)
        ]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_donate, pattern="^donate$"))
    application.add_handler(CallbackQueryHandler(delete_old_profiles, pattern="^delete_old$"))
    application.add_error_handler(error_handler)
    
    print("Бот Mental запущено! Чекаємо повідомлень...")
    application.run_polling()

if __name__ == '__main__':
    main()
