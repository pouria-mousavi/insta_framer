import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Instagram Credentials
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")

# Processing Settings
BLUR_THRESHOLD = 100.0 # Threshold for Laplacian variance (higher is sharper)
# Removed FRAME_INTERVAL to process every frame as requested

