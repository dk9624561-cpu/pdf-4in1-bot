"""
Telegram PDF 4-in-1 Handout Bot
Converts presentation slide PDFs into 4-in-1 printable A4 sheets (2x2 grid).

Author: Antigravity AI
"""

import os
import sys
import shutil
import logging
import asyncio
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminal
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from pdf_converter import convert_pdf_to_4in1
import fitz

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TEMP_DIR = Path(__file__).parent / "temp_files"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# User layout preference memory: user_id -> '4in1' | '2in1' | '6in1'
user_preferences = {}

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("PDF4in1Bot")


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP server handler for Render Web Service health checks and UptimeRobot."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - PDF 4-in-1 Handout Bot is running 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        # Silence routine health check logs to keep terminal clean
        return


def start_health_check_server():
    """Start an HTTP server on $PORT for Render Web Service compatibility."""
    port = int(os.getenv("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check HTTP server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Could not start health check server on port {port}: {e}")


async def self_ping_loop():
    """Periodically ping self URL to keep Render free tier awake 24/7."""
    await asyncio.sleep(15)
    external_url = os.getenv("RENDER_EXTERNAL_URL")
    if not external_url:
        port = os.getenv("PORT", "10000")
        external_url = f"http://127.0.0.1:{port}"

    logger.info(f"Self-ping keepalive activated for URL: {external_url}")
    while True:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(external_url)
                logger.info(f"Keep-alive self-ping status: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive self-ping notice: {e}")
        await asyncio.sleep(240)  # Ping every 4 minutes (240s)


async def post_init(application):
    """Called after application initialization to start background tasks."""
    asyncio.create_task(self_ping_loop())


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command."""
    user = update.effective_user
    name = user.first_name if user else "Friend"
    text = (
        f"👋 **Namaste {name}!**\n\n"
        f"Main **PDF 4-in-1 Handout Bot** hoon.\n\n"
        f"📌 **Mera Kaam:**\n"
        f"Aap mujhe koi bhi PPT ya Slide wala PDF document bhejenge, "
        f"main usko **1 Page me 4 Slides (2x2 Grid, A4 Landscape)** me convert karke bhej dunga—"
        f"bilkul printing aur reading ke liye perfect!\n\n"
        f"🚀 **Kaise use karein?**\n"
        f"Bas apna koi bhi **PDF file** yahan send kijiye.\n\n"
        f"⚙️ **Commands:**\n"
        f"• `/layout` - Choose layout (4-in-1, 2-in-1, 6-in-1)\n"
        f"• `/help` - Help & details"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /help command."""
    text = (
        "📖 **PDF 4-in-1 Bot Help Guide:**\n\n"
        "1️⃣ **PDF bhejein:** Koi bhi slides ya PPT PDF yahan share karein.\n"
        "2️⃣ **Auto-Conversion:** Bot automatically 4-in-1 A4 Landscape format me layout bana dega.\n"
        "3️⃣ **High Quality:** Original vector text, diagrams aur images 100% crisp rahenge.\n"
        "4️⃣ **Print Friendly:** Clean light-gray border aur white background ke saath aata hai.\n\n"
        "⚡ *Note:* Telegram Bot API standard file limit 20MB hai."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def layout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows user to select preferred layout."""
    keyboard = [
        [
            InlineKeyboardButton("📄 4-in-1 (Default - 4 Slides)", callback_data="set_layout:4in1"),
        ],
        [
            InlineKeyboardButton("📑 2-in-1 (2 Slides Vert.)", callback_data="set_layout:2in1"),
            InlineKeyboardButton("📋 6-in-1 (6 Slides 3x2)", callback_data="set_layout:6in1"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    current = user_preferences.get(update.effective_user.id, "4in1")
    await update.message.reply_text(
        f"⚙️ **Select Layout:**\nCurrent Layout: **{current}**\n\nApna pasandida layout select karein:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles layout selection callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("set_layout:"):
        layout = data.split(":", 1)[1]
        user_preferences[query.from_user.id] = layout
        await query.edit_message_text(
            f"✅ Layout set to **{layout}**! Ab koi bhi PDF bhejiye, ye isi layout me banega.",
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming PDF documents."""
    doc = update.message.document
    if not doc:
        return

    file_name = doc.file_name or "document.pdf"
    if not file_name.lower().endswith(".pdf"):
        await update.message.reply_text(
            "⚠️ Kripya sirf **.pdf** file bhejiye.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check file size (Telegram Bot API allows up to 20MB download)
    file_size_mb = doc.file_size / (1024 * 1024) if doc.file_size else 0
    if file_size_mb > 20:
        await update.message.reply_text(
            f"⚠️ File size ({file_size_mb:.1f} MB) is too large for direct Telegram bot download (Max limit 20 MB).\n"
            f"💡 Aap is file ko PC par local script se convert kar sakte hain:\n"
            f"`python pdf_converter.py \"path_to_pdf\"`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    user_id = update.effective_user.id
    selected_layout = user_preferences.get(user_id, "4in1")

    # Send status message
    status_msg = await update.message.reply_text(
        f"📥 **Downloading PDF:** `{file_name}`...\nKripya thoda intezaar karein.",
        parse_mode=ParseMode.MARKDOWN
    )

    clean_stem = Path(file_name).stem
    input_path = TEMP_DIR / f"{user_id}_{doc.file_id}.pdf"
    output_filename = f"{clean_stem}_{selected_layout}.pdf"
    output_path = TEMP_DIR / f"{user_id}_{doc.file_id}_{selected_layout}.pdf"

    try:
        # Download file
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(custom_path=str(input_path))

        # Check total pages
        src_pdf = fitz.open(str(input_path))
        orig_pages = len(src_pdf)
        src_pdf.close()

        await status_msg.edit_text(
            f"⚙️ **Converting:** `{file_name}`\n"
            f"• Total Slides: **{orig_pages}**\n"
            f"• Target Layout: **{selected_layout}** (A4 Landscape)\n"
            f"Processing high-resolution vector layout...",
            parse_mode=ParseMode.MARKDOWN
        )

        # Run conversion in worker thread to prevent blocking event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            convert_pdf_to_4in1,
            str(input_path),
            str(output_path),
            selected_layout,
        )

        out_pdf = fitz.open(str(output_path))
        out_pages = len(out_pdf)
        out_pdf.close()

        await status_msg.edit_text(
            f"📤 **Uploading:** `{output_filename}`\n"
            f"• Slides: {orig_pages} ➔ Pages: {out_pages}...",
            parse_mode=ParseMode.MARKDOWN
        )

        caption = (
            f"✅ **Conversion Complete!**\n\n"
            f"📄 **Original Slides:** {orig_pages}\n"
            f"📑 **{selected_layout} Pages:** {out_pages}\n"
            f"📐 **Format:** A4 Landscape Grid\n"
            f"✨ Print ready vector quality!"
        )

        with open(output_path, "rb") as f_out:
            await update.message.reply_document(
                document=f_out,
                filename=output_filename,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )

        # Delete status message
        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Error converting document: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ **Error aaya conversion me:**\n`{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )
    finally:
        # Cleanup temp files
        if input_path.exists():
            try:
                input_path.unlink()
            except Exception:
                pass
        if output_path.exists():
            try:
                output_path.unlink()
            except Exception:
                pass


def main():
    """Bot entry point."""
    if not BOT_TOKEN:
        print("\n" + "=" * 60)
        print("ERROR: BOT_TOKEN is missing!")
        print("Please set your BOT_TOKEN in .env file.")
        print("Example: BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstUVwxYZ")
        print("=" * 60 + "\n")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🚀 Starting PDF 4-in-1 Handout Telegram Bot...")
    print("=" * 60)

    # Start health check HTTP server in background thread for Render
    health_thread = threading.Thread(target=start_health_check_server, daemon=True)
    health_thread.start()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("layout", layout_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))

    print("✅ Bot is online and listening for PDFs!")
    app.run_polling()


if __name__ == "__main__":
    main()
