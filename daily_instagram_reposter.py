#!/usr/bin/env python3
import os
import random
import threading
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import instaloader
from openai import OpenAI
import requests
from yt_dlp import YoutubeDL
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Load variables from .env into the process environment
load_dotenv()

# ─────────────── CONFIGURATION ───────────────
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
ACCESS_TOKEN     = os.getenv("FB_ACCESS_TOKEN")
ACCESS_TOKEN_2     = os.getenv("FB_ACCESS_TOKEN_2")
IG_USER_ID       = os.getenv("IG_USER_ID")
URLS_FILE        = os.getenv("SOURCE_URLS_FILE", "source_urls.txt")
POST_HOUR        = int(os.getenv("POST_HOUR", "10"))
POST_MINUTE      = int(os.getenv("POST_MINUTE", "0"))

# For serving downloaded reels locally
PUBLIC_HOST      = os.getenv("PUBLIC_HOST")  # e.g. https://abcd1234.ngrok.io
LOCAL_SERVER_PORT= int(os.getenv("LOCAL_SERVER_PORT", "8000"))

INSTAGRAM_BASE   = "https://graph.instagram.com/v22.0"
FACEBOOK_BASE    = "https://graph.facebook.com/v22.0"

# ─────────────── SERVE REELS DIRECTORY ───────────────
if PUBLIC_HOST:
    def _serve_reels():
        os.makedirs("reels", exist_ok=True)
        os.chdir("reels")
        ThreadingHTTPServer(("0.0.0.0", LOCAL_SERVER_PORT), SimpleHTTPRequestHandler).serve_forever()
    threading.Thread(target=_serve_reels, daemon=True).start()

# ─────────────── HELPERS ───────────────
loader = instaloader.Instaloader()

def download_reel(post_url: str, output_dir: str = "reels") -> str:
    """Download an IG Reel MP4 locally and return its file path."""
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        "format": "mp4",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(post_url, download=True)
        return ydl.prepare_filename(info)

def load_source_urls(path: str):
    """Read all non-empty lines from the file."""
    with open(path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]
    if not urls:
        raise RuntimeError(f"No URLs found in {path}")
    return urls

def save_source_urls(path: str, urls: list):
    """Overwrite the source URLs file with remaining URLs."""
    with open(path, "w") as f:
        for url in urls:
            f.write(f"{url}\n")

def fetch_post_by_url(post_url: str):
    """
    Given an IG post URL, returns:
      - media: URL or list of URLs for carousel
      - caption_text
      - author_username
      - is_video
      - is_carousel
    """
    parsed = urlparse(post_url)
    parts = parsed.path.strip('/').split('/')
    if len(parts) < 2 or parts[0] not in ("p", "reel"):
        raise ValueError(f"Invalid Instagram post URL: {post_url}")
    shortcode = parts[1]
    post = instaloader.Post.from_shortcode(loader.context, shortcode)
    author = post.owner_username
    caption = (post.caption or "").strip()

    # carousel
    if getattr(post, "mediacount", 1) > 1:
        urls = [node.video_url if node.is_video else node.display_url
                for node in post.get_sidecar_nodes()]
        return urls, caption, author, False, True

    # single video
    if post.is_video:
        return post.video_url, caption, author, True, False

    # single image
    return post.url, caption, author, False, False

def generate_caption(original_caption: str, author: str) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = (
        "You are a social media assistant specializing in wildlife conservation. "
        "Write an engaging IG caption that:\n"
        "1. Opens strong\n"
        "2. Shares a conservation fact\n"
        f"3. Credits @{author}\n"
        "4. Asks a question\n"
        "5. Directs to the bio\n"
        "6. Ends with 'Discover, Learn and Protect'\n"
        "7. Uses exactly 7 relevant hashtags"
    )
    user_prompt = (
        f"Repost an Instagram post by @{author}.\n"
        f"Original caption: “{original_caption}”\n\n"
        "Generate a brand-new caption per the above guidelines."
    )
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )
    return resp.choices[0].message.content.strip()

def publish_to_instagram(media, caption: str, is_video: bool, is_carousel: bool) -> dict:
    """
    - IMAGE/CAROUSEL: graph.instagram.com
    - REELS (video): facebook graph with public URL
    """
    # carousel
    if is_carousel and isinstance(media, list):
        child_ids = []
        for url in media:
            payload = {
                "access_token": ACCESS_TOKEN,
                "is_carousel_item": "true",
                "image_url": url
            }
            r = requests.post(f"{INSTAGRAM_BASE}/{IG_USER_ID}/media", data=payload)
            r.raise_for_status()
            child_ids.append(r.json()["id"])
        parent = {
            "access_token": ACCESS_TOKEN,
            "caption": caption,
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids)
        }
        create = requests.post(f"{INSTAGRAM_BASE}/{IG_USER_ID}/media", data=parent)
        create.raise_for_status()
        cid = create.json()["id"]

    # single image
    elif not is_video:
        payload = {
            "access_token": ACCESS_TOKEN,
            "image_url": media,
            "caption": caption
        }
        create = requests.post(f"{INSTAGRAM_BASE}/{IG_USER_ID}/media", data=payload)
        create.raise_for_status()
        cid = create.json()["id"]

    # reel
    else:
        # if served locally via PUBLIC_HOST, build URL
        if media.endswith(".mp4") and PUBLIC_HOST:
            filename = os.path.basename(media)
            media_url = f"{PUBLIC_HOST.rstrip('/')}/{filename}"
        else:
            media_url = media
        payload = {
            "access_token": ACCESS_TOKEN,
            "media_type": "REELS",
            "caption": caption,
            "share_to_feed": "true"
        }
        create = requests.post(f"{INSTAGRAM_BASE}/{IG_USER_ID}/media", data=payload)
        create.raise_for_status()
        cid = create.json()["id"]

    # publish
    pub = requests.post(
        f"{FACEBOOK_BASE}/{IG_USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": ACCESS_TOKEN}
    )
    pub.raise_for_status()
    return pub.json()

def daily_job():
    urls   = load_source_urls(URLS_FILE)
    chosen = random.choice(urls)
    try:
        media, orig_caption, author, is_video, is_carousel = fetch_post_by_url(chosen)
        new_caption = generate_caption(orig_caption, author)
        print(f"[INFO] Posting {'carousel' if is_carousel else 'video' if is_video else 'image'} by @{author}")

        if is_video and not is_carousel:
            local_path = download_reel(chosen)
            result = publish_to_instagram(local_path, new_caption, True, False)
        else:
            result = publish_to_instagram(media, new_caption, is_video, is_carousel)

        print(f"[OK] Posted new media from {chosen}, ID: {result.get('id')}")
    except Exception as e:
        print(f"[ERROR] Failed to post {chosen}: {e}")
    else:
        remaining = [u for u in urls if u != chosen]
        save_source_urls(URLS_FILE, remaining)
        print(f"[INFO] Removed used URL: {chosen}")

if __name__ == "__main__":
    daily_job()
    # scheduler = BlockingScheduler(timezone="Europe/Amsterdam")
    # scheduler.add_job(
    #     daily_job,
    #     trigger='cron',
    #     hour=POST_HOUR,
    #     minute=POST_MINUTE
    # )
    # scheduler.start()
