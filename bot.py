import os
import io
import logging
import pymongo
import pytesseract
import PIL.Image
import google.generativeai as genai
import requests  # For making API requests
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, BOT_TOKEN, GOOGLE_API_KEY, MONGO_URI, DB_NAME, GOOGLE_CSE_ID

# Initialize bot
app = Client(
    "gemini_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.MARKDOWN
)

# Configure Google API
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # Use the newer model

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]
chat_collection = db["chat_history"]
files_collection = db["file_analysis"]

# Logging setup
logging.basicConfig(level=logging.INFO)

### 1️⃣ USER REGISTRATION ###
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Check if user exists
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "phone_number": None
        })

        # Ask for phone number
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Share Phone Number", request_contact=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await message.reply_text("📲 Please share your phone number for verification.", reply_markup=keyboard)
    else:
        await message.reply_text("✅ You are already registered!")

@app.on_message(filters.contact)
async def contact_handler(client: Client, message: Message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number

    # Update user with phone number
    users_collection.update_one({"user_id": user_id}, {"$set": {"phone_number": phone_number}})
    await message.reply_text("✅ Phone number saved successfully!")


### 2️⃣ GEMINI AI CHAT ###
@app.on_message(filters.command("gem"))
async def gemini_handler(client: Client, message: Message):
    loading_message = await message.reply_text("⏳ Generating response, please wait...")

    try:
        if len(message.text.strip()) <= 5:
            await message.reply_text(" Provide a prompt after the command.")
            return

        prompt = message.text.split(maxsplit=1)[1]
        response = model.generate_content(prompt)
        response_text = response.text

        # Store chat in MongoDB
        chat_collection.insert_one({
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "query": prompt,
            "response": response_text,
            "timestamp": message.date
        })

        # Send response
        if len(response_text) > 4000:
            parts = [response_text[i:i + 4000] for i in range(0, len(response_text), 4000)]
            for part in parts:
                await message.reply_text(part)
        else:
            await message.reply_text(response_text)

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.reply_text(f"❌ An error occurred: {str(e)}")
    finally:
        await loading_message.delete()


### 3️⃣ IMAGE & FILE ANALYSIS WITH OCR AND IMAGE ANALYSIS ###
@app.on_message(filters.photo | filters.document)
async def analyze_file(client: Client, message: Message):
    processing_message = await message.reply_text("⏳ Analyzing file, please wait...")

    try:
        # Download file
        file_info = await client.get_messages(message.chat.id, message.id)
        file_name = file_info.document.file_name if file_info.document else "image.jpg"
        img_data = await client.download_media(message, in_memory=True)

        # Convert image (if applicable)
        if message.photo or (file_info.document and file_info.document.mime_type.startswith("image")):
            img = PIL.Image.open(io.BytesIO(img_data.getbuffer()))

            # Perform OCR to extract text from the image
            try:
                extracted_text = pytesseract.image_to_string(img)
                if extracted_text.strip() == "":
                    extracted_text = "No text found in the image."
            except Exception as ocr_error:
                logging.error(f"OCR Error: {ocr_error}")
                extracted_text = "OCR failed to extract text from the image."

            # Analyze the image using Google Generative AI
            try:
                prompt = f"""
                Analyze the following image and provide details:
                1. Describe the visual content (objects, scenes, etc.).
                2. Extract and summarize any text found in the image.
                3. Provide insights or context based on the image.

                Extracted Text: {extracted_text}
                """
                response = model.generate_content([prompt, img])  # Pass both text and image to the model
                response_text = response.text
            except Exception as ai_error:
                logging.error(f"AI Analysis Error: {ai_error}")
                response_text = "Failed to analyze the image using AI."

            # Store file metadata in MongoDB
            files_collection.insert_one({
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "file_name": file_name,
                "description": response_text,
                "timestamp": message.date
            })

            await message.reply_text(f"📄 Image Analysis:\n{response_text}")

        else:
            # Handle non-image files (e.g., PDFs, documents)
            try:
                response = model.generate_content(f"Analyze the content of this file: {file_name}")
                response_text = response.text
            except Exception as file_error:
                logging.error(f"File Analysis Error: {file_error}")
                response_text = "Failed to analyze the file."

            # Store file metadata in MongoDB
            files_collection.insert_one({
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "file_name": file_name,
                "description": response_text,
                "timestamp": message.date
            })

            await message.reply_text(f"📄 File Analysis:\n{response_text}")

    except Exception as e:
        logging.error(f"Error during file analysis: {e}")
        await message.reply_text("❌ An error occurred while analyzing the file.")

    finally:
        await processing_message.delete()


### 4️⃣ WEB SEARCH USING GOOGLE CUSTOM SEARCH API ###
@app.on_message(filters.command("websearch"))
async def web_search(client: Client, message: Message):
    if len(message.text.strip()) <= 10:
        await message.reply_text(" Please provide a search query after /websearch.")
        return

    search_query = message.text.split(maxsplit=1)[1]
    loading_message = await message.reply_text("🔍 Searching the web...")

    try:
        # Perform web search using Google Custom Search API
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "q": search_query,
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,  # Custom Search Engine ID
            "num": 5  # Number of results to fetch
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        search_results = response.json()

        # Format the results
        if "items" not in search_results:
            await message.reply_text(" No results found.")
            return

        result_text = "🌍 **Web Search Results:**\n\n"
        for item in search_results["items"]:
            result_text += f"🔗 [{item['title']}]({item['link']})\n"
            result_text += f"📄 {item['snippet']}\n\n"

        # Store search in MongoDB
        chat_collection.insert_one({
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "query": f"Web Search: {search_query}",
            "response": result_text,
            "timestamp": message.date
        })

        await message.reply_text(result_text, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Web search error: {e}")
        await message.reply_text("❌ An error occurred while searching the web.")

    finally:
        await loading_message.delete()


### RUN THE BOT ###
if __name__ == "__main__":
    app.run()