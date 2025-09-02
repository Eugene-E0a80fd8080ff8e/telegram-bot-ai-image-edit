
from dotenv import load_dotenv
import os
load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")


from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import NetworkError, TimedOut

import re
import json
from session import Session


async def start(update: Update, context):
    await update.message.reply_text('Hello! I am a bot that can respond to messages addressed to me in a group.')


async def handle_message(update: Update, context):
    
    #print(type(update),update)
    #print(update.message)

    message = None
    if update.message is not None : message = update.message
    if update.edited_message is not None : message = update.edited_message

    if message.chat.id not in [-1002199005809, -1002211084712, -498556509, -4590114841, -1001858292142]: return

    chat_id = message.chat_id
    user_id = message.from_user.id
    username = message.from_user.username or f"{message.from_user.id}"
    
    print(f"[{datetime.datetime.now()}] chat_id: {chat_id}, user_id: {user_id}, username: {username}, message_id: {message.message_id}")
    
    text = ""
    if message.text is not None : text = message.text
    if message.caption is not None : text = message.caption
    
    print(f"Received message - Chat ID: {chat_id}, User ID: {user_id}, Username: {username}, text: {text}")
    
    sess = Session("sess")
    
    sess.append(sess.makeFilename("update","txt"), str(update))
    sess.append(sess.makeFilename("msg","txt"), str(message))
    
    if text == "ping":
        await message.reply_text("pong")
        return
    
    if m := re.search( r"(?:^|\s|\n|\r|\t|$)[Aa][Ii](?:^|\s|\n|\r|\t|$)", text, re.MULTILINE):
        prompt = re.sub( r"(?:^|\s|\n|\r|\t|$)[Aa][Ii](?:^|\s|\n|\r|\t|$)" , " " , text , re.MULTILINE)
    
        
        attached_photos = []
        if message.photo or (message.reply_to_message and message.reply_to_message.photo):
            
            photos = []
            if message.photo:
                photos.extend( message.photo )
            if (message.reply_to_message and message.reply_to_message.photo): 
                photos.extend( message.reply_to_message.photo )
            
            for photo in photos:
                #if message.photo : photo = message.photo[-1]
                #if (message.reply_to_message and message.reply_to_message.photo) : photo = message.reply_to_message.photo[-1]

                file = await photo.get_file()
                sess.append(sess.makeFilename("fileurl","txt"), str(file))
                
                """
                #current_dir = os.path.dirname(os.path.abspath(__file__))
                incoming_photo_filename = generate_unixtime_filename(username,"jpg")
                #incoming_path = os.path.join(current_dir, "incoming/",incoming_photo_filename)
                incoming_path = os.path.join("incoming/",incoming_photo_filename)
                #print(f"incoming_path={incoming_path}")

                attached_photo = await file.download_to_drive(custom_path=incoming_path)
                print(f"attached_photo={attached_photo}")
                """
        
    


    """
    if message.photo:
        # Get the largest photo
        file_id = message.photo[-1].file_id
        file = await context.bot.get_file(file_id)
        file_path = file.file_path
        
        # Create a session and download the image
        session = Session("incoming")
        local_filename = session.download_image(file_path)
        
        await message.reply_text(f"Image received and saved as {local_filename}")
        return

    if message.text:
        if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
            # This is a reply to the bot's message
            await message.reply_text("You replied to me!")
        elif f"@{context.bot.username}" in message.text:
            # The bot is mentioned in the message
            await message.reply_text("You mentioned me!")
        else:
            # Regular message
            pass
    """

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        
    

from session import Session
import datetime


##############################


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))

    print(f"started...")
    application.run_polling()

if __name__ == '__main__':
    ensure_directory("uploads")
    ensure_directory("incoming")

    main()
