from __future__ import annotations

import os
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import instaloader
import requests
from yt_dlp import YoutubeDL
from functools import partial
from config import LOCAL_SERVER_PORT, PUBLIC_HOST

loader = instaloader.Instaloader(download_videos=True)
_server_thread = None

def start_reel_server():
    global _server_thread
    if not PUBLIC_HOST or _server_thread:
        return
    handler = partial(SimpleHTTPRequestHandler, directory=os.path.abspath("reels"))
    httpd = ThreadingHTTPServer(("0.0.0.0", LOCAL_SERVER_PORT), handler)
    _server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    _server_thread.start()
    print("Server started on port", LOCAL_SERVER_PORT)

def download_reel(post_url: str, output_dir: str = "reels") -> str:
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(post_url, download=True)
        return ydl.prepare_filename(info)


def list_formats(post_url: str):
    """List available video/audio formats using yt_dlp without downloading."""
    with YoutubeDL() as ydl:
        info = ydl.extract_info(post_url, download=False)
        for f in info.get("formats", []):
            print(
                f"format_id: {f['format_id']}, ext: {f['ext']}, "
                f"resolution: {f.get('resolution')}, fps: {f.get('fps')}, "
                f"note: {f.get('format_note')}"
            )


def extract_shortcode(post_url: str) -> str:
    path = urlparse(post_url).path  # e.g. "/reel/C_LY1ccxW4E/"
    parts = path.strip("/").split("/")  # ["reel", "C_LY1ccxW4E"]
    if len(parts) >= 2 and parts[0] in ("p", "reel"):
        return parts[1]
    raise ValueError(f"Invalid Instagram post URL: {post_url}")

def load_urls(path: str):
    with open(path) as f:
        urls = [l.strip() for l in f if l.strip()]
    if not urls:
        raise RuntimeError(f"No URLs in {path}")
    return urls


def save_urls(path: str, urls: list):
    with open(path, "w") as f:
        f.write("\n".join(urls) + "\n")


def fetch_post_by_url(url: str):
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) < 2 or parts[0] not in ("p", "reel"):
        raise ValueError(f"Bad URL: {url}")
    post = instaloader.Post.from_shortcode(loader.context, parts[1])
    author = post.owner_username
    tagged_users = post.tagged_users

    # location_name = post._node['location']['name'] if 'location' in post._node else None
    location_id = None
    # if location_name:
        # location_id = get_facebook_location_id(location_name)

    caption = (post.caption or "").strip()
    if getattr(post, "mediacount", 1) > 1:
        nodes = post.get_sidecar_nodes()
        media = [n.video_url if n.is_video else n.display_url for n in nodes]
        return media, caption, location_id, author, False, True, tagged_users
    if post.is_video:
        return post.video_url, caption, location_id, author, True, False, tagged_users
    return post.url, caption, location_id, author, False, False, tagged_users

