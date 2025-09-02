
from dotenv import load_dotenv
import os
load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")


from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import NetworkError, TimedOut
from telegram.ext import ContextTypes

import re
import json
from session import Session
import datetime

from db import Database
db = Database()


async def start(update: Update, context):
    await update.message.reply_text('Hello! I am a bot that can respond to messages addressed to me in a group.')

media_group_id_to_picture = {}

def prettify_json(json_str):
    d = json.loads(json_str)
    return json.dumps(d,indent=4,ensure_ascii=False)
    

async def handle_message(update: Update, context):
    
    #print(type(update),update)
    #print(update.message)

    message = update.effective_message
    chat_id = message.chat_id
    user_id = update.effective_user.id
    username = message.from_user.username or f"{message.from_user.id}"
    text = (message.text if message.text else "") + (message.caption if message.caption else "")
    media_group_id= message.media_group_id if message.media_group_id else None
    
    if chat_id not in [-1002199005809, -1002211084712, -498556509, -4590114841, -1001858292142]: return
    
    delay = 1
    mentioned_photos = []
    
    photo_id = None
    if message.photo: photo_id = message.photo[-1].file_id
    
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Working-with-Files-and-Media
    
    db.add_message(user_id=user_id, 
                   chat_id=chat_id, 
                   message_id=message.id,
                   media_group_id= media_group_id,
                   message_text= text,
                   photo_id = photo_id,
                   message_json= prettify_json( message.to_json())
    )
                   
    if message.photo: 
        if not db.check_photo_by_id(photo_id):
            photo_file = await message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            db.add_photo(photo_id=photo_id, photo_blob=photo_bytes, media_group_id=media_group_id)
            
        if media_group_id:
            mentioned_photos.append( ("media_group_id", media_group_id) )
            delay = 5
        else: 
            mentioned_photos.append( ("photo_id", photo_id) )
            
    if message.reply_to_message and message.reply_to_message.photo :
        r_photo_id = message.reply_to_message.photo[-1].file_id
        r_media_group_id= message.reply_to_message.media_group_id if message.reply_to_message.media_group_id else None
        if not db.check_photo_by_id(r_photo_id):
            photo_file = await message.reply_to_message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            db.add_photo(photo_id=r_photo_id, photo_blob=photo_bytes, media_group_id=r_media_group_id)
            
        if r_media_group_id:
            mentioned_photos.append( ("media_group_id", r_media_group_id) )
            delay = 5
        else: 
            mentioned_photos.append( ("photo_id", r_photo_id) )

    
    print(f"[{datetime.datetime.now()}] chat_id: {chat_id}, user_id: {user_id}, username: {username}, message_id: {message.message_id}")
    
    text = ""
    if message.text is not None : text = message.text
    if message.caption is not None : text = message.caption
    
    print(f"Received message - Chat ID: {chat_id}, User ID: {user_id}, Username: {username}, text: {text}")
    
    sess = Session("sess")
    
    #sess.append(sess.makeFilename("update","txt"), str(update))
    sess.append(sess.makeFilename("update-j","txt"), prettify_json( update.to_json()))
    #sess.append(sess.makeFilename("msg","txt"), str(message))
    sess.append(sess.makeFilename("msg-j","txt"), prettify_json( message.to_json()))
        
    if text == "ping":
        await message.reply_text(f"pong / { json.dumps(mentioned_photos) }")
        #await message.reply_text("pong")
        return
    
    sess.append(sess.makeFilename("mentioned_photos","txt"), str(mentioned_photos))
    
    if m := re.search( r"(?:^|\s|\n|\r|\t|$)[Aa][Ii](?:^|\s|\n|\r|\t|$)", text, re.MULTILINE):
        prompt = re.sub( r"(?:^|\s|\n|\r|\t|$)[Aa][Ii](?:^|\s|\n|\r|\t|$)" , " " , text , re.MULTILINE)
        
        #if media_group_id :
        #    context.job_queue.run_once( delay_message_processing ,delay , chat_id=chat_id, user_id=user_id, data=(message,prompt,None,media_group_id))
        #else:
        #    context.job_queue.run_once( delay_message_processing ,delay , chat_id=chat_id, user_id=user_id, data=(message,prompt,photo_id,None))
        
        context.job_queue.run_once( delay_message_processing ,delay , chat_id=chat_id, user_id=user_id, data=(message,prompt,mentioned_photos))


async def delay_message_processing(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    #await context.bot.send_message(job.chat_id, text=f"reply")
    
    photos_bytes = []
    (message,prompt,mentioned_photos) = job.data
    
    for (t,tid) in mentioned_photos:
        if t == "media_group_id" :  photos_bytes.extend( db.get_photo_by_media_group_id(tid) )
        if t == "photo_id" :  photos_bytes.append( db.get_photo_by_id(tid) )
    #if photo_id:
    #    photos_bytes.append( db.get_photo_by_id(photo_id) )
    #if media_group_id:
    #    photos_bytes.extend( db.get_photo_by_media_group_id(media_group_id) )
        
    await process_prompt(context, prompt, photos_bytes)
    
    
async def process_prompt( context, prompt, photos_bytes ):
    sess2 = Session("sess2")
    sess2.append(sess2.makeFilename("prompt","txt"), prompt)
    for photo_bytes in photos_bytes:
        sess2.write(sess2.makeFilename("image","jpg"), photo_bytes)
        
    
    
    


##############################


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))

    print(f"started...")
    application.run_polling()

if __name__ == '__main__':
    #ensure_directory("uploads")
    #ensure_directory("incoming")
    
    main()
    
