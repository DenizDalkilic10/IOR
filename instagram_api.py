from __future__ import annotations

import json
import time
import requests
from enum import Enum
from config import INSTAGRAM_BASE, ACCESS_TOKEN, ACCESS_TOKEN_FB, IG_USER_ID

class MediaType(Enum):
    IMAGE = "IMAGE"
    REELS = "REELS"
    CAROUSEL = "CAROUSEL"

class BaseContainer:
    @property
    def fields(self) -> dict:
        raise NotImplementedError

class ReelContainer(BaseContainer):
    def __init__(self, video_url, caption=None, author_tag=None):
        self.media_type = MediaType.REELS
        self.video_url = video_url
        self.share_to_feed = True
        self.caption = caption
        self.user_tags = [{"username": author_tag}]

    @property
    def fields(self):
        return {
            "media_type": self.media_type.value,
            "share_to_feed": "true",
            "caption": self.caption,
            "video_url": self.video_url,
            "user_tags": json.dumps(self.user_tags),
        }


def create_container(container: BaseContainer) -> dict:
    params = {**container.fields, "access_token": ACCESS_TOKEN}
    res = requests.post(f"{INSTAGRAM_BASE}/{IG_USER_ID}/media", params=params)
    res.raise_for_status()
    return res.json()


def wait_for(container_id: str):
    url=f"{INSTAGRAM_BASE}/{container_id}"
    while True:
        print("Waiting for container to finish...")
        st = requests.get(url,params={"fields":"status_code","access_token":ACCESS_TOKEN}).json().get("status_code")
        if st=="FINISHED" or "IN_PROGRESS":
            time.sleep(10)
            break
        if st and st.startswith("ERROR"): raise RuntimeError(st)
        print("Status: ",st)


def publish_container(container_id: str) -> dict:
    time.sleep(20)  # Wait for the container to be ready
    res = requests.post(
        f"{INSTAGRAM_BASE}/{IG_USER_ID}/media_publish",
        params={"creation_id": container_id, "access_token": ACCESS_TOKEN},
    )
    res.raise_for_status()
    return res.json()

# def get_facebook_location_id(location_name: str) -> str | None:
#     search_url = "https://graph.facebook.com/v23.0/pages/search"
#     params = {
#         "type": "page",
#         "q": location_name,
#         "fields": "id",
#         "access_token": ACCESS_TOKEN_FB,
#         "limit": 5
#     }
#     r = requests.get(search_url, params=params)
#     r.raise_for_status()
#     data = r.json()
#
#     for page in data.get("data", []):
#         loc = page.get("location")
#         if loc and location_name.lower() in page["name"].lower():
#             # Optionally add more verification here
#             return page["id"]
#     return None