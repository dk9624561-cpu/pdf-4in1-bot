# 📑 Telegram PDF 4-in-1 Handout Bot

A Telegram bot and offline Python tool that transforms slide-based PDFs (PowerPoint / Keynote / Lecture handouts) into printable **4-in-1 A4 Landscape sheets** in a clean 2x2 grid.

---

## ✨ Features

- **4-in-1 Handout Layout:** Arranges 4 slides per A4 page in landscape orientation (2x2 grid).
- **Aspect Ratio Preserved:** Automatically detects slide proportions (16:9 widescreen or 4:3) and centers them neatly in each quadrant.
- **Crystal Clear Quality:** Preserves original vector text and embedded HD images using PyMuPDF (`fitz`).
- **Clean Aesthetic:** Adds clean white backgrounds and subtle border lines around each slide.
- **Multiple Layout Options:** Supports `4in1` (default), `2in1` (vertical stack), and `6in1` (3x2 grid).
- **Dual Mode:**
  - 🤖 **Telegram Bot:** Send any PDF in chat, and get back the converted handout PDF instantly.
  - 💻 **Offline CLI & Batch Mode:** Run directly on your computer to convert a single PDF or an entire directory of PDFs with zero internet dependency.

---

## 🚀 Quick Start (Local / Self-Hosted)

### 1. Clone the repository
```bash
git clone https://github.com/dk9624561-cpu/pdf-4in1-bot.git
cd pdf-4in1-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Bot Token
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and paste your bot token obtained from [@BotFather](https://t.me/BotFather):
```env
BOT_TOKEN=your_telegram_bot_token_here
```

### 4. Run the Bot
- On Windows: Double click `run_bot.bat` or run:
  ```bash
  python bot.py
  ```
- On Linux / Mac:
  ```bash
  python3 bot.py
  ```

---

## 💻 Offline CLI Usage (Without Telegram)

You can convert PDFs locally without running the Telegram bot:

### Convert a Single PDF:
```bash
python pdf_converter.py "path/to/slides.pdf"
```
*Output will be saved as `slides_4in1.pdf`.*

### Specify Output Path or Layout:
```bash
python pdf_converter.py "input.pdf" -o "output.pdf" -l 4in1
# Options for -l: 4in1, 2in1, 6in1
```

### Batch Convert an Entire Folder:
```bash
python pdf_converter.py "D:/My_Lecture_Slides_Folder"
```
*(On Windows, you can also drag & drop a PDF or folder directly onto `convert_folder.bat`)*

---

## 🛠️ Bot Commands

| Command | Description |
|---|---|
| `/start` | Starts the bot and shows a welcome guide |
| `/help` | Explains how to use the bot and file limits |
| `/layout` | Choose default layout (`4in1`, `2in1`, `6in1`) |

---

## 📦 Requirements

- Python 3.8+
- [PyMuPDF (fitz)](https://github.com/pymupdf/PyMuPDF)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

---

## 📄 License

MIT License
