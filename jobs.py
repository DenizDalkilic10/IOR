import os
import random
import json
import time

from utils import load_urls, save_urls, fetch_post_by_url, download_reel, list_formats, start_reel_server
from captions import generate_caption, generate_weekly_caption
from instagram_api import create_container, wait_for, publish_container, ReelContainer, MediaType, BaseContainer
from config import SOURCE_FILE, REELS_FILE, WEEKLY_FAVS_FILE, PUBLIC_HOST


def post_reel_job():
    urls = load_urls(REELS_FILE)
    choice = random.choice(urls)
    media, cap, location_id, author, is_video, is_carousel, tagged_users = fetch_post_by_url(choice)

    orig=download_reel(choice)
    today_date = time.strftime("%Y-%m-%d")
    short=f"{author}_today_{today_date}_reel.mp4"
    os.makedirs("reels",exist_ok=True)
    sp=os.path.join("reels",short)
    os.replace(orig,sp)
    # 2) serve
    start_reel_server()

    public_url=f"{PUBLIC_HOST.rstrip('/')}/{short}"

    caption = generate_caption(cap, author)
    print("Caption generated: ", caption)

    rc = ReelContainer(video_url=public_url, caption=caption, author_tag=author)
    print("Reel created")
    data = create_container(rc)
    wait_for(data["id"])
    publish_container(data["id"])
    print("Reel published")

    urls.remove(choice)
    save_urls(REELS_FILE, urls)


def post_image_job():
    urls = load_urls(SOURCE_FILE)
    choice = random.choice(urls)
    media, cap, location_id, author, is_video, is_carousel, tagged_users = fetch_post_by_url(choice)
    caption = generate_caption(cap, author)

    author_tag = [{"username": author, "x": 0.5, "y": 0.5}]
    #all_tags = author_tag + [{"username": u, "x": 0.1, "y": 0.1} for u in tagged_users]
    if is_carousel:
        ids = []
        for idx, img in enumerate(media):
            class CI(BaseContainer):
                @property
                def fields(self):
                    return {
                        "image_url": img,
                        "is_carousel_item": "true",
                        "user_tags": json.dumps(author_tag),
                    }
            ids.append(create_container(CI())["id"])
        class CAR(BaseContainer):
            @property
            def fields(self):
                return {
                    "media_type": MediaType.CAROUSEL.value,
                    "caption": caption,
                    # "location_id": location_id,
                    "children": ",".join(ids)
                }
        data = create_container(CAR())
    else:
        class IM(BaseContainer):
            @property
            def fields(self):
                return {
                    "image_url": media,
                    "caption": caption,
                    "user_tags": json.dumps(author_tag),
                }
        data = create_container(IM())
    publish_container(data["id"])

    urls.remove(choice)
    save_urls(SOURCE_FILE, urls)


def post_weekly_favorites_job():
    urls = load_urls(WEEKLY_FAVS_FILE)
    entries, used = [], []
    for url in urls:
        media, cap, location_id, author, is_video, is_carousel = fetch_post_by_url(url)
        if not is_video:
            entries.append((cap or "", author))
            used.append(url)
        if len(entries) == 5:
            break
    if len(entries) < 5:
        raise RuntimeError("Not enough image posts for weekly favorites")
    caption = generate_weekly_caption(entries)

    media_urls = []
    for url in used:
        media, _, _, _, is_video, is_carousel = fetch_post_by_url(url)
        if is_carousel:
            media = media[0]
        media_urls.append(media)

    tags = [{"username": author, "x": 0.5, "y": 0.5} for _, author in entries]
    ids = []
    for img in media_urls:
        class CI:
            @property
            def fields(self):
                return {
                    "image_url": img,
                    "is_carousel_item": "true",
                    "user_tags": json.dumps(tags),
                }
        ids.append(create_container(CI())["id"])
    class CAR:
        @property
        def fields(self):
            return {
                "media_type": MediaType.CAROUSEL.value,
                "caption": caption,
                "children": ",".join(ids),
                "user_tags": json.dumps(tags),
            }
    data = create_container(CAR())
    publish_container(data["id"])

    remaining = [u for u in urls if u not in used]
    save_urls(WEEKLY_FAVS_FILE, remaining)