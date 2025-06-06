import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
ACCESS_TOKEN      = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_FB   = os.getenv("ACCESS_TOKEN_FB")
IG_USER_ID        = os.getenv("IG_USER_ID")
SOURCE_FILE       = os.getenv("SOURCE_URLS_FILE", "normal_posts.txt")
REELS_FILE        = os.getenv("REELS_FILE", "reels.txt")
WEEKLY_FAVS_FILE  = os.getenv("WEEKLY_FAVS_FILE", "weekly_favorites.txt")
POST_HOUR         = int(os.getenv("POST_HOUR", "18"))
POST_MINUTE       = int(os.getenv("POST_MINUTE", "00"))
MORNING_POST_HOUR = int(os.getenv("MORNING_POST_HOUR", "8"))
MORNING_POST_MINUTE = int(os.getenv("POST_MINUTE", "00"))
PUBLIC_HOST       = os.getenv("PUBLIC_HOST")
LOCAL_SERVER_PORT = int(os.getenv("LOCAL_SERVER_PORT", "8000"))
INSTAGRAM_BASE    = "https://graph.instagram.com/v22.0"