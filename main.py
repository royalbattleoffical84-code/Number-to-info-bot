#!/usr/bin/env python3
"""
Telegram Number Info Bot
A complete Telegram bot for fetching mobile number information from an API.
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional, Any

import requests
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ===================================================
# CONFIGURATION
# ===================================================
# YAHAN APNA NAYA TOKEN DAALO (Space nahi hona chahiye)
BOT_TOKEN = "9264885271:AAGUIjI3kLzCRbHDUH7v3wLq-Eflhvu2Ovg"  # <-- Naya token yahan paste karo

API_URL = "https://sovitx-info.vercel.app/api/num-info?key=Sx_Demo&number=9876543210"

# ===================================================
# LOGGING SETUP
# ===================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================================================
# BOT INITIALIZATION
# ===================================================
# Try-Catch add karo token validation ke liye
try:
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
    # Test API connection
    bot.get_me()
    logger.info("✅ Bot connected successfully!")
except Exception as e:
    logger.error(f"❌ Bot initialization failed: {e}")
    logger.error("Please check your BOT_TOKEN")
    exit(1)

# ===================================================
# KEYBOARD FUNCTIONS
# ===================================================
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Create and return the main reply keyboard with the "🔍 Get Info" button.
    The keyboard remains visible to the user.
    """
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        row_width=1
    )
    btn_get_info = KeyboardButton("🔍 Get Info")
    keyboard.add(btn_get_info)
    return keyboard


# ===================================================
# UTILITY FUNCTIONS
# ===================================================
def is_valid_mobile_number(number: str) -> bool:
    """
    Validate if the given string is a 10-digit mobile number.
    Returns True if valid, False otherwise.
    """
    # Remove any whitespace
    number = number.strip()
    # Check if it's exactly 10 digits
    return bool(re.match(r'^\d{10}$', number))


def format_field(value: Any) -> str:
    """
    Format a field value. If the value is None, empty, or "null",
    return "Not Available". Otherwise return the value as string.
    """
    if value is None or value == "" or str(value).lower() == "null":
        return "Not Available"
    return str(value)


def format_record(record: Dict[str, Any], index: int) -> str:
    """
    Format a single record into a beautiful message.
    """
    mobile = format_field(record.get("mobile"))
    name = format_field(record.get("name"))
    fname = format_field(record.get("fname"))
    alt = format_field(record.get("alt"))
    circle = format_field(record.get("circle"))
    record_id = format_field(record.get("id"))
    email = format_field(record.get("email"))
    address = format_field(record.get("address"))

    # Build the formatted message
    message = f"""
╭━━━〔 📱 NUMBER INFO {index+1} 〕━━━⬣

👤 Name      : {name}
👨 Father    : {fname}
📞 Number    : {mobile}
📱 Alternate : {alt}
📡 Circle    : {circle}
🆔 ID        : {record_id}
📧 Email     : {email}

🏠 Address :
{address}

━━━━━━━━━━━━━━━━━━━━"""
    return message.strip()


def format_no_data(number: str) -> str:
    """
    Format the message when no data is found.
    """
    return f"""
╭━━━〔 ❌ NO DATA FOUND 〕━━━⬣

📞 Number : {number}

⚠️ Is Number Ka Koi Data Nahi Hai.

Please Try Another Number.

╰━━━━━━━━━━━━━━━━━━⬣"""


def fetch_number_info(number: str) -> Optional[Dict[str, Any]]:
    """
    Fetch number information from the API.
    Returns the JSON response as dictionary or None on error.
    """
    try:
        # Build the API URL with the user's number
        url = API_URL.format(USER_NUMBER=number)
        logger.info(f"Calling API: {url}")

        # Make the API request with a timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse JSON response
        data = response.json()
        return data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout error while fetching number {number}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while fetching number {number}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e} while fetching number {number}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error {e} while fetching number {number}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response for number {number}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching number {number}: {e}")
        return None


def handle_number_lookup(message: Message, number: str) -> None:
    """
    Handle the number lookup process.
    This function is called after the user sends a valid mobile number.
    """
    chat_id = message.chat.id

    # Send searching message
    searching_msg = bot.send_message(chat_id, "🔍 Searching Information...")

    # Fetch data from API
    data = fetch_number_info(number)

    # Check if we got valid data
    if data is None:
        # API error occurred
        bot.edit_message_text(
            "⚠️ Server Error.\n\nPlease Try Again Later.",
            chat_id,
            searching_msg.message_id
        )
        return

    # Check if data contains records
    records = data.get("data", [])
    if not records or not isinstance(records, list):
        # No data found
        no_data_msg = format_no_data(number)
        bot.edit_message_text(no_data_msg, chat_id, searching_msg.message_id)
        return

    # We have records - display them
    total_records = len(records)

    # Delete the searching message
    bot.delete_message(chat_id, searching_msg.message_id)

    # Send each record as a separate message
    for idx, record in enumerate(records):
        formatted_record = format_record(record, idx)
        bot.send_message(chat_id, formatted_record)

    # Send total records count
    bot.send_message(chat_id, f"📊 Total Records : {total_records}")


# ===================================================
# BOT HANDLERS
# ===================================================
@bot.message_handler(commands=['start'])
def handle_start(message: Message) -> None:
    """
    Handle the /start command.
    Send a welcome message and display the main keyboard.
    """
    chat_id = message.chat.id
    welcome_message = """
🌟 <b>Welcome to Number Info Bot!</b>

Get detailed information about any Indian mobile number instantly.

Simply press the button below to get started.

━━━━━━━━━━━━━━━━━━━
<b>📌 How it works:</b>
1️⃣ Press <code>🔍 Get Info</code>
2️⃣ Send any 10-digit mobile number
3️⃣ Get detailed information

<i>Powered by Flex-Giftyou Number Info API</i>
"""

    # Send welcome message with the main keyboard
    bot.send_message(
        chat_id,
        welcome_message,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda message: message.text == "🔍 Get Info")
def handle_get_info(message: Message) -> None:
    """
    Handle the "🔍 Get Info" button press.
    Ask the user to send a mobile number.
    """
    chat_id = message.chat.id

    info_message = """
📱 <b>Please Send Mobile Number</b>

Example:
<code>1234567890</code>

✅ Send Any Valid 10 Digit Mobile Number.
"""

    bot.send_message(
        chat_id,
        info_message,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@bot.message_handler(content_types=['text'])
def handle_text_messages(message: Message) -> None:
    """
    Handle all text messages (including mobile number input).
    """
    chat_id = message.chat.id
    user_input = message.text.strip()

    # Ignore command messages (they're handled by other handlers)
    if user_input.startswith('/'):
        return

    # Check if the input is a valid mobile number
    if is_valid_mobile_number(user_input):
        # Valid number - process it
        handle_number_lookup(message, user_input)
    else:
        # Invalid input - send error message
        error_message = """
❌ <b>Invalid Mobile Number.</b>

Please send a valid 10-digit mobile number.
Example: <code>1234567890</code>
"""

        bot.send_message(
            chat_id,
            error_message,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )


# ===================================================
# ERROR HANDLING
# ===================================================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message: Message) -> None:
    """
    Catch-all handler for any messages that weren't handled above.
    """
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "Please use the <b>🔍 Get Info</b> button to get started.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# ===================================================
# POLLING WITH ERROR HANDLING
# ===================================================
def run_bot() -> None:
    """
    Run the bot with error handling and automatic restart.
    """
    logger.info("Starting Number Info Bot...")
    logger.info(f"Bot Token: {BOT_TOKEN[:10]}...")
    logger.info(f"API URL: {API_URL}")

    while True:
        try:
            # Remove webhook if any
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=1, timeout=60)
        except telebot.apihelper.ApiTelegramException as e:
            if "404" in str(e):
                logger.error("❌ INVALID BOT TOKEN! Please check your BOT_TOKEN")
                logger.error("Create a new bot from @BotFather and update the token")
                break
            else:
                logger.error(f"Telegram API error: {e}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)


# ===================================================
# MAIN ENTRY POINT
# ===================================================
if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
