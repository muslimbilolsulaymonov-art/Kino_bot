import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        [InlineKeyboardButton("🎭 Janr bilan izlash", callback_data="genres")]
    ]
    await update.message.reply_text(
        "👋 *Xush kelibsiz!*\n\n🎬 Kino nomini yozing yoki quyidagi tugmalardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
    await update.callback_query.edit_message_text(
        text="🎭 Janrni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def search_movie(query):
    url = f"{TMDB_BASE}/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query, "language": "uz-UZ"}
    r = requests.get(url, params=params).json()
    return r.get("results", [])[:5]

async def get_by_genre(genre_id):
    url = f"{TMDB_BASE}/discover/movie"
    params = {"api_key": TMDB_API_KEY, "with_genres": genre_id, "language": "uz-UZ", "sort_by": "popularity.desc"}
    r = requests.get(url, params=params).json()
    return r.get("results", [])[:5]

def format_movie(movie):
    title = movie.get("title", "Noma'lum")
    rating = movie.get("vote_average", 0)
    date = movie.get("release_date", "")[:4]
    overview = movie.get("overview", "Tavsif yo'q")[:150]
    poster = IMG_BASE + movie.get("poster_path", "") if movie.get("poster_path") else None
    return title, rating, date, overview, poster

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    results = await search_movie(query)
    if not results:
        await update.message.reply_text("❌ Film topilmadi. Boshqa nom kiriting.")
        return
    for movie in results[:3]:
        title, rating, date, overview, poster = format_movie(movie)
        text = f"🎬 *{title}* ({date})\n⭐ {rating}/10\n\n📝 {overview}"
        keyboard = [[InlineKeyboardButton("🔗 Ko'proq ma'lumot", url=f"https://www.themoviedb.org/movie/{movie['id']}")]]
        if poster:
            await update.message.reply_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "genres":
        await show_genres(update, context)
    elif query.data.startswith("genre_"):
        genre_name = query.data[6:]
        genre_id = GENRES.get(genre_name, 28)
        results = await get_by_genre(genre_id)
        for movie in results[:3]:
            title, rating, date, overview, poster = format_movie(movie)
            text = f"🎬 *{title}* ({date})\n⭐ {rating}/10\n\n📝 {overview}"
            keyboard = [[InlineKeyboardButton("🔗 Ko'proq ma'lumot", url=f"https://www.themoviedb.org/movie/{movie['id']}")]]
            if poster:
                await query.message.reply_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()