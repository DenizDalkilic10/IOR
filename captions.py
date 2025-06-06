from openai import OpenAI
from config import OPENAI_API_KEY


def generate_caption(orig: str, author: str) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    sp = (
        "You are a creative social media assistant of a nature and wildlife conservation organization on Instagram.\n"
        "Your task is to thoughtfully and powerfully feature another author’s capture, aiming to deepen love and awareness of nature.\n\n"
        "Use only the context of animals, plants, and nature from the original post’s caption.\n"
        "- Do NOT use information about the time the capture was made or published.\n"
        "- If the original caption does not mention specific wildlife species or habitat, use the general context from the original caption for inspiration. Play safe.\n\n"
        "Output format (in this order):\n"
        "1. One attention-grabbing paragraph featuring the content as well as mentioning the original author tagged as '@{author}'.\n"
        "2. One paragraph educating about the featured wildlife or habitat and raising awareness.\n"
        "3. One short section inviting readers to visit 'Untold Stories', where talented individuals worldwide share nature stories; mention the link is in the profile.\n"
        "4. On a new line, end with the phrase: Discover, Learn, Protect®\n\n"
        "Style and constraints:\n"
        "- Keep the text organized and written at B2 English level (upper intermediate).\n"
        "- 10 relevant hashtags in lowercase letters in the format '#{tag}'. Prioritize captions from the original post if relevant. \n"
        "- Do NOT assume or use pronouns for the author.\n"
        "- The entire output must be complete and under 2200 characters, including the hashtags.\n"
    )
    rp = f"Original by @{author}: “{orig}”"
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role":"system","content":sp},{"role":"user","content": rp}],
        temperature=1.0
    )
    return resp.choices[0].message.content.strip()


def generate_weekly_caption(entries: list[tuple[str, str]]) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    system = (
        "You are a social media assistant for a wildlife conservation organization on Instagram.\n"
        "Create a Weekly Favorites carousel featuring exactly five nature shots.\n\n"
        "Begin with one attention-grabbing paragraph introducing the Weekly Favorites concept and its celebration of nature’s beauty.\n\n"
        "For each of the five posts, write exactly two short sentences: one highlighting the featured shot, and one crediting the author with “@{author}”.\n\n"
        "End with one inviting paragraph encouraging readers to share which shot they love most and to explore Untold Stories via the link in our profile.\n\n"
        "Conclude with “Discover, Learn, Protect®” on a new line.\n\n"
        "Use clear, engaging B2 English, keep it organized, and include exactly 3 relevant hashtags.\n"
        "The full output must be complete and under 2000 characters."
    )
    user_content = "\n".join(
        f"{i+1}. @{author}: “{caption}”" for i, (caption, author) in enumerate(entries)
    )
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_content}],
        temperature=0.7,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()
