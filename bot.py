import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

GENRES = {
    "🎬 Jangari": 28, "😢 Drama": 18, "😂 Komediya": 35,
    "👻 Horror": 27, "🔪 Triller": 53, "💕 Romantika": 10749,
    "🦸 Marvel": 878, "🌀 Fantastika": 878, "🕵️ Detektiv": 9648,
    "🗺️ Sarguzasht": 12, "📜 Tarixiy": 36, "😈 Kriminal": 80,
    "🎌 Anime": 16
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Film izlash", callback_data="search")],
        [InlineKeyboardButton("🎭 Janr bilan izlash", callback_data="genres")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")]
    ]
    text = (
        "👋 *Xush kelibsiz!*\n\n"
        "🎬 Men kino va seriallar botiman!\n\n"
        "📌 *Nima qila olaman:*\n"
        "• Kino va serial qidirish\n"
        "• Janr bo'yicha qidirish\n"
        "• Aktyor haqida ma'lumot\n"
        "• Film reytingi va tavsifi\n\n"
        "Kino nomini yozing yoki tugma bosing!"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 *Yordam*\n\n"
        "/start — Bosh menyu\n"
        "/help — Yordam\n"
        "/about — Bot haqida\n\n"
        "🔍 Film nomini yozing — qidiradi\n"
        "🎭 Janr tanlang — ro'yxat chiqadi"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *Bot haqida*\n\n"
        "🤖 Bot nomi: Kino Bot\n"
        "📌 Username: @muslm_bilol7_bot\n\n"
        "🎬 Bu bot yordamida:\n"
        "• Millionlab filmlar haqida ma'lumot\n"
        "• Aktyor va rejissorlar haqida\n"
        "• Janr bo'yicha qidirish\n"
        "• Reyting va tavsiflar\n\n"
        "📡 Ma'lumotlar: TMDB bazasi"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

def format_movie(movie):
    title = movie.get("title", "Noma'lum")
    rating = movie.get("vote_average", 0)
    date = movie.get("release_date", "")[:4]
    overview = movie.get("overview", "Tavsif yo'q")[:200]
    poster = IMG_BASE + movie.get("poster_path", "") if movie.get("poster_path") else None
    return title, rating, date, overview, poster

async def search_tmdb(query):
    url = f"{TMDB_BASE}/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query, "language": "uz-UZ"}
    r = requests.get(url, params=params).json()
    results = r.get("results", [])
    if not results:
        params["language"] = "ru-RU"
        r = requests.get(url, params=params).json()
        results = r.get("results", [])
    return results[:5]

async def search_actor(query):
    url = f"{TMDB_BASE}/search/person"
    params = {"api_key": TMDB_API_KEY, "query": query, "language": "uz-UZ"}
    r = requests.get(url, params=params).json()
    return r.get("results", [])[:3]

async def get_by_genre(genre_id):
    url = f"{TMDB_BASE}/discover/movie"
    params = {"api_key": TMDB_API_KEY, "with_genres": genre_id, "language": "uz-UZ", "sort_by": "popularity.desc"}
    r = requests.get(url, params=params).json()
    return r.get("results", [])[:5]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text

    actor_results = await search_actor(query)
    if actor_results:
        actor = actor_results[0]
        name = actor.get("name", "Noma'lum")
        known_for = actor.get("known_for_department", "")
        popularity = actor.get("popularity", 0)
        movies = actor.get("known_for", [])

        movie_list = ""
        for m in movies[:3]:
            movie_list += f"• {m.get('title', m.get('name', '?'))}\n"

        text = (
            f"🎭 *{name}*\n"
            f"🎬 Sohasi: {known_for}\n"
            f"⭐ Mashhurlik: {popularity:.1f}\n\n"
            f"📽️ *Mashhur filmlari:*\n{movie_list}"
        )
        keyboard = [[InlineKeyboardButton("🔍 Film qidirish", callback_data="search")]]
        photo = actor.get("profile_path")
        if photo:
            await update.message.reply_photo(
                photo=f"https://image.tmdb.org/t/p/w500{photo}",
                caption=text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    results = await search_tmdb(query)
    if not results:
        await update.message.reply_text("❌ Film topilmadi. Boshqa nom kiriting.")
        return

    for movie in results[:3]:
        title, rating, date, overview, poster = format_movie(movie)
        text = f"🎬 *{title}* ({date})\n⭐ {rating}/10\n\n📝 {overview}"
        keyboard = [[InlineKeyboardButton("🔗 Ko'proq", url=f"https://www.themoviedb.org/movie/{movie['id']}")]]
        if poster:
            await update.message.reply_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_genres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for name in GENRES:
        row.append(InlineKeyboardButton(name, callback_data=f"genre_{name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await update.callback_query.edit_message_text(text="🎭 Janrni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "genres":
        await show_genres(update, context)
    elif query.data == "about":
        text = (
            "ℹ️ *Bot haqida*\n\n"
            "🤖 Kino Bot — film va seriallar bazasi\n"
            "📡 TMDB ma'lumotlar bazasi asosida\n\n"
            "🎬 Imkoniyatlar:\n"
            "• Film qidirish\n"
            "• Aktyor qidirish\n"
            "• Janr bo'yicha qidirish\n"
            "• Reyting va tavsif"
        )
        await query.edit_message_text(text=text, parse_mode="Markdown")
    elif query.data == "search":
        await query.edit_message_text(text="🔍 Qidirmoqchi bo'lgan kino yoki aktyor nomini yozing:")
    elif query.data.startswith("genre_"):
        genre_name = query.data[6:]
        genre_id = GENRES.get(genre_name, 28)
        results = await get_by_genre(genre_id)
        for movie in results[:3]:
            title, rating, date, overview, poster = format_movie(movie)
            text = f"🎬 *{title}* ({date})\n⭐ {rating}/10\n\n📝 {overview}"
            keyboard = [[InlineKeyboardButton("🔗 Ko'proq", url=f"https://www.themoviedb.org/movie/{movie['id']}")]]
            if poster:
                await query.message.reply_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Bosh menyu"),
        BotCommand("help", "Yordam"),
        BotCommand("about", "Bot haqida"),
    ])

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()