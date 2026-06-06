"""
Mindful Machines Journal — Automated Blog Post Generator
Generates a post using the Anthropic API and publishes it to Blogger.
"""

import os
import json
import random
import datetime
import anthropic
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ── Configuration ────────────────────────────────────────────────────────────

BLOG_ID = os.environ["BLOGGER_BLOG_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"]

TOPICS_FILE = os.path.join(os.path.dirname(__file__), "topics.json")

# ── Topic selection ───────────────────────────────────────────────────────────

def load_topics():
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def pick_topic(topics: list[dict]) -> dict:
    """Pick a topic, preferring ones not recently used."""
    state_file = os.path.join(os.path.dirname(__file__), ".last_topic_index")
    used_indices = set()
    if os.path.exists(state_file):
        with open(state_file) as f:
            try:
                used_indices = set(json.load(f))
            except Exception:
                pass

    available = [i for i in range(len(topics)) if i not in used_indices]
    if not available:
        available = list(range(len(topics)))
        used_indices = set()

    idx = random.choice(available)
    used_indices.add(idx)

    # Keep state file small — only track last 10
    trimmed = list(used_indices)[-10:]
    with open(state_file, "w") as f:
        json.dump(trimmed, f)

    return topics[idx]

# ── Content generation ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the voice of Mindful Machines Journal — a thoughtful,
human-centred publication exploring the intersection of artificial intelligence,
psychology, and education.

Your writing style is:
- Warm, intelligent, accessible — never jargon-heavy
- Grounded in evidence and research, but written for curious non-specialists
- Reflective and questioning — you surface implications, not just facts
- Structured clearly: a strong hook, well-organised body, a meaningful close

Every post should leave the reader with something to think about or try."""

def generate_post(topic: dict) -> dict:
    """Call Claude to generate a full blog post. Returns title, body HTML, labels."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_prompt = f"""Write a blog post for Mindful Machines Journal on this topic:

Title idea: {topic['title']}
Angle: {topic['angle']}
Key themes: {', '.join(topic['themes'])}
Target reader: {topic.get('audience', 'curious professionals interested in AI, psychology, and learning')}

Requirements:
- 600–900 words
- HTML formatted (use <h2>, <p>, <ul>/<li>, <strong> — no <html>/<body> wrapper)
- Begin with a compelling opening paragraph (no heading above it)
- 2–3 subheadings (h2) to break up the piece
- End with a brief, thoughtful closing paragraph
- Tone: warm, intelligent, reflective

Return a JSON object with exactly these keys:
{{
  "title": "the final post title",
  "body": "the full HTML body",
  "labels": ["label1", "label2", "label3"]
}}

Return ONLY the JSON — no markdown fences, no extra text."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": user_prompt}],
        system=SYSTEM_PROMPT,
    )

    raw = message.content[0].text.strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)

# ── Blogger publish ───────────────────────────────────────────────────────────

def get_blogger_service():
    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    return build("blogger", "v3", credentials=creds)

def publish_post(service, title: str, body: str, labels: list[str]) -> str:
    post_body = {
        "title": title,
        "content": body,
        "labels": labels,
    }
    result = service.posts().insert(
        blogId=BLOG_ID,
        body=post_body,
        isDraft=False,
    ).execute()
    return result.get("url", "")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[{datetime.datetime.utcnow().isoformat()}] Starting post generation...")

    topics = load_topics()
    topic = pick_topic(topics)
    print(f"  Topic: {topic['title']}")

    post = generate_post(topic)
    print(f"  Generated: {post['title']}")

    service = get_blogger_service()
    url = publish_post(service, post["title"], post["body"], post["labels"])
    print(f"  Published: {url}")
    print("Done.")

if __name__ == "__main__":
    main()
