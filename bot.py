import logging
import os
import shutil
import uuid
import time
import threading
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from instagram_service import InstagramService
from video_service import VideoService
from keep_alive import keep_alive

# Start the web server for Render
keep_alive()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Initialize Services
insta = InstagramService()
video_processor = VideoService()

PAGE_SIZE = 10

# --- Cleanup Logic ---
def cleanup_loop():
    """Periodically cleans up old temp files to save disk space on Render."""
    TEMP_DIR = "temp_downloads"
    MAX_AGE_SECONDS = 600 # 10 minutes
    
    while True:
        try:
            if os.path.exists(TEMP_DIR):
                current_time = time.time()
                for item in os.listdir(TEMP_DIR):
                    item_path = os.path.join(TEMP_DIR, item)
                    # Check if it's a directory (request ID)
                    if os.path.isdir(item_path):
                        # Get modification time
                        mtime = os.path.getmtime(item_path)
                        if current_time - mtime > MAX_AGE_SECONDS:
                            try:
                                shutil.rmtree(item_path)
                                logging.info(f"Cleaned up old temp dir: {item}")
                            except Exception as e:
                                logging.error(f"Failed to delete {item}: {e}")
            
            time.sleep(300) # Check every 5 minutes
        except Exception as e:
            logging.error(f"Error in cleanup loop: {e}")
            time.sleep(300)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
cleanup_thread.start()
# ---------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="👋 Hi! Send me an Instagram video link (Post or Reel). I'll extract the sharpest frames for you to choose from."
    )

async def send_frame_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    chat_id = update.effective_chat.id
    candidates = context.user_data.get('all_candidates', [])
    video_path = context.user_data.get('video_path')
    temp_dir = context.user_data.get('temp_dir')
    
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    
    # Slice top candidates for this page (candidates are sorted by score from analyze_video)
    # BUT wait, we want to show the best ones first.
    # So page 0 is top 10 best. Page 1 is next 10 best.
    page_candidates = candidates[start_idx:end_idx]
    
    if not page_candidates:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ No more frames available.")
        return

    # Save these specific frames
    # video_service.save_frames sorts them by TIME for display context
    frames = video_processor.save_frames(video_path, page_candidates, temp_dir)
    
    # Store currently displayed frames for selection mapping
    # We map "Selection 1" -> frames[0]
    context.user_data['displayed_frames'] = frames 
    
    media_group = []
    for i, (path, score) in enumerate(frames):
        media_group.append(InputMediaPhoto(open(path, 'rb'), caption=f"{i+1}"))
    
    await context.bot.send_media_group(chat_id=chat_id, media=media_group)
    
    # Navigation Buttons
    keyboard = []
    if end_idx < len(candidates):
         keyboard.append([InlineKeyboardButton("🔄 Load More (Next 10)", callback_data=f"page_{page+1}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"Showing frames {start_idx+1}-{start_idx+len(frames)} (ranked by quality).\nReply with numbers **1 to {len(frames)}** to download high-res.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: str, temp_dir: str):
    """Helper to process a downloaded video and present frames."""
    chat_id = update.effective_chat.id
    
    try:
        await context.bot.send_message(chat_id=chat_id, text="🎞 Extracting and analyzing frames...")
        
        # 1. Analyze to get ALL candidates
        all_candidates = video_processor.analyze_video(video_path)
        
        if not all_candidates:
            await context.bot.send_message(chat_id=chat_id, text="❌ No sharp frames found.")
            shutil.rmtree(temp_dir)
            return
            
        # Store in context
        context.user_data['all_candidates'] = all_candidates
        context.user_data['video_path'] = video_path
        context.user_data['temp_dir'] = temp_dir
        context.user_data['awaiting_selection'] = True
        
        # Send first page
        await send_frame_page(update, context, page=0)
        
    except Exception as e:
        logging.error(f"Error processing video: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ An error occurred during processing.")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    # Check if we are waiting for a selection
    if 'awaiting_selection' in context.user_data and context.user_data['awaiting_selection']:
        await handle_selection(update, context)
        return

    # Assume it's a URL
    if "instagram.com" not in text:
        await context.bot.send_message(chat_id=chat_id, text="Please send a valid Instagram link or the frame numbers you want (e.g., '1, 3').")
        return

    await context.bot.send_message(chat_id=chat_id, text="⏳ Checking content...")
    
    # Check content type (Playlist vs Single)
    content_info = insta.check_download_type(text)
    
    if content_info['type'] == 'playlist':
        count = content_info['count']
        
        msg = f"🔎 Found {count} stories/items in this link. Which one do you want?"
        keyboard = []
        row = []
        for i in range(1, count + 1):
            btn_text = f"Story {i}"
            row.append(InlineKeyboardButton(btn_text, callback_data=f"story_{i}"))
            if len(row) >= 3: 
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['pending_playlist_url'] = text
        await context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=reply_markup)
        
    elif content_info['type'] == 'video':
        # Single video, proceed directly
        request_id = str(uuid.uuid4())
        temp_dir = os.path.join("temp_downloads", request_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        await context.bot.send_message(chat_id=chat_id, text="⏳ Downloading...")
        video_path = insta.download_post(text, temp_dir)
        
        if not video_path:
             await context.bot.send_message(chat_id=chat_id, text="❌ Failed to download video.")
             shutil.rmtree(temp_dir)
             return
             
        await process_video(update, context, video_path, temp_dir)
        
    else:
        # Error or unknown
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Could not process link: {content_info.get('error', 'Unknown error')}")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    data = query.data
    chat_id = update.effective_chat.id
    
    if data.startswith("story_"):
        index = int(data.split("_")[1])
        url = context.user_data.get('pending_playlist_url')
        
        if not url:
            await query.edit_message_text("❌ Session expired. Please send the link again.")
            return
            
        await query.edit_message_text(f"⏳ Downloading Story {index}...")
        
        request_id = str(uuid.uuid4())
        temp_dir = os.path.join("temp_downloads", request_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        video_path = insta.download_post(url, temp_dir, playlist_index=index)
        
        if not video_path:
             await context.bot.send_message(chat_id=chat_id, text=f"❌ Failed to download Story {index}.")
             shutil.rmtree(temp_dir)
             return
             
        await process_video(update, context, video_path, temp_dir)

    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        await send_frame_page(update, context, page=page)

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    
    try:
        selection_indices = [int(x.strip()) - 1 for x in text.split(',') if x.strip().isdigit()]
        displayed_frames = context.user_data.get('displayed_frames', [])
        
        if not selection_indices:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Please enter valid numbers (e.g., '1, 3').")
            return

        selected_files = []
        for idx in selection_indices:
            if 0 <= idx < len(displayed_frames):
                selected_files.append(displayed_frames[idx][0]) # path
        
        if not selected_files:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ No valid frames selected from the current list.")
            return
            
        await context.bot.send_message(chat_id=chat_id, text="📤 Sending full quality files...")
        
        for file_path in selected_files:
            await context.bot.send_document(chat_id=chat_id, document=open(file_path, 'rb'))
            
        # Cleanup
        # We rely on the periodic cleanup loop to handle this now for robustness
        # But we can still cleanup here immediately to be nice
        temp_dir = context.user_data.get('temp_dir')
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logging.error(f"Cleanup error: {e}")
            
        # Reset state
        context.user_data['awaiting_selection'] = False
        context.user_data['frames'] = []
        context.user_data['all_candidates'] = []
        await context.bot.send_message(chat_id=chat_id, text="✅ Done! Send another link to start again.")

    except Exception as e:
        logging.error(f"Error handling selection: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ Error sending files.")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in environment variables.")
        exit(1)
    
    # Attempt login on startup
    if not insta.login():
         print("Warning: Instagram login failed. Private posts will not be accessible.")

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    callback_handler = CallbackQueryHandler(handle_callback_query)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler) 
    application.add_handler(callback_handler)
    
    print("Bot is polling...")
    application.run_polling()

