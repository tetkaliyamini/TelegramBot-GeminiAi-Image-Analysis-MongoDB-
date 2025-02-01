# Telegram Bot with Gemini AI and Google Custom Search

This is a Telegram bot that integrates **Google's Gemini AI** for text and image analysis and **Google Custom Search JSON API** for web searches. The bot also uses **MongoDB** to store user data, chat history, and file analysis results.

---

## Features

1. **User Registration**:
   - Users can register with their phone number.
   - User data is stored in MongoDB.

2. **Gemini AI Chat**:
   - Users can interact with the bot using the `/gem` command.
   - The bot generates responses using Google's Gemini AI.

3. **Image and File Analysis**:
   - Users can send images or files to the bot.
   - The bot performs OCR (Optical Character Recognition) on images and analyzes them using Gemini AI.
   - Analysis results are stored in MongoDB.

4. **Web Search**:
   - Users can perform web searches using the `/websearch` command.
   - The bot fetches results using the Google Custom Search JSON API.

---

## Prerequisites

Before running the bot, ensure you have the following:

1. **Python 3.8+** installed.
2. A **Telegram Bot Token** from [BotFather](https://core.telegram.org/bots#botfather).
3. A **Google API Key** and **Custom Search Engine ID (CX)** from the [Google Cloud Console](https://console.cloud.google.com/).
4. A **MongoDB URI** for database storage.

---

## Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   Install Dependencies:

bash
Copy
pip install -r requirements.txt
Configure Environment Variables:
Create a config.py file in the root directory and add the following:

python
Copy
API_ID = "your_telegram_api_id"
API_HASH = "your_telegram_api_hash"
BOT_TOKEN = "your_telegram_bot_token"
GOOGLE_API_KEY = "your_google_api_key"
GOOGLE_CSE_ID = "your_custom_search_engine_id"
MONGO_URI = "your_mongodb_uri"
DB_NAME = "your_database_name"
Run the Bot:

bash
Copy
python bot.py
Commands
/start: Register with the bot.

/gem <prompt>: Chat with Gemini AI.

/websearch <query>: Perform a web search.

Send an Image/File: Analyze the image or file using Gemini AI.

File Structure
Copy
.
├── bot.py                # Main bot script
├── config.py             # Configuration file
├── requirements.txt      # List of dependencies
├── README.md             # This file
└── .gitignore            # Files to ignore in Git
Dependencies
pyrogram: For interacting with the Telegram API.

google-generativeai: For using Google's Gemini AI.

pymongo: For MongoDB integration.

pytesseract: For OCR (Optical Character Recognition).

Pillow: For image processing.

requests: For making API requests.