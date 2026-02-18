import os
import re
import json
import logging
from datetime import datetime, timezone
import urllib.request
import urllib.error
import urllib.parse

import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import anthropic

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
FAST_NOTE_URL = os.environ.get("FAST_NOTE_URL")
FAST_NOTE_TOKEN = os.environ.get("FAST_NOTE_TOKEN")
FAST_NOTE_VAULT = os.environ.get("FAST_NOTE_VAULT", "Obsidian")
CATEGORIES = os.environ.get("CATEGORIES", "Article,Video,Tweet,Tutorial,Resource,Personal,Other")
NOTE_FOLDER = os.environ.get("NOTE_FOLDER", "collections")

# Initialize Claude client
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# URL pattern
URL_PATTERN = re.compile(r'https?://[^\s]+')

# Noise patterns to remove from messages
NOISE_PATTERNS = [
    r'[,，]?\s*复制打开抖音.*$',
    r'[,，]?\s*复制此链接.*$',
    r'[,，]?\s*[Cc]opy and open Xiaohongshu.*$',
    r'[,，]?\s*打开抖音.*$',
    r'[,，]?\s*打开小红书.*$',
    r'[,，]?\s*点击链接.*$',
]


# ─── Fast Note Sync API ──────────────────────────────────────────────

def _api_request(method: str, endpoint: str, data: dict | None = None) -> dict:
    """Call Fast Note Sync REST API."""
    url = f"{FAST_NOTE_URL.rstrip('/')}/api{endpoint}"

    if method == "GET" and data:
        qs = urllib.parse.urlencode(data)
        url = f"{url}?{qs}"
        payload = None
    else:
        payload = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FAST_NOTE_TOKEN}",
        },
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def save_to_obsidian(title: str, category: str, content: str) -> tuple[bool, str, str]:
    """Save a note to Obsidian via Fast Note Sync.

    Returns:
        (success, error_message, note_path)
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    # Sanitize title for filename
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:60].strip()
    note_path = f"{NOTE_FOLDER}/{date_str}-{safe_title}.md"

    # Determine if content is a URL
    is_url = bool(URL_PATTERN.match(content.strip()))
    source_line = f'source: "{content.strip()}"' if is_url else ""

    # Build frontmatter
    fm_lines = [
        "---",
        f'title: "{title}"',
        f"category: {category}",
        f"date: {date_str}",
    ]
    if source_line:
        fm_lines.append(source_line)
    fm_lines += ["type: collection", "---"]
    frontmatter = "\n".join(fm_lines)

    # Build full markdown
    md_content = f"{frontmatter}\n\n{content}\n"

    try:
        _api_request("POST", "/note", {
            "vault": FAST_NOTE_VAULT,
            "path": note_path,
            "content": md_content,
        })
        return True, "", note_path
    except Exception as e:
        logger.error(f"Failed to save to Obsidian: {e}")
        return False, str(e), ""


def update_category(note_path: str, new_category: str) -> tuple[bool, str]:
    """Update the category of an existing note via PATCH /note/frontmatter."""
    try:
        _api_request("PATCH", "/note/frontmatter", {
            "vault": FAST_NOTE_VAULT,
            "path": note_path,
            "updates": {"category": new_category},
        })
        return True, ""
    except Exception as e:
        logger.error(f"Failed to update category: {e}")
        return False, str(e)


def ensure_index_page() -> None:
    """Create or update the _index.md Dataview table page."""
    index_path = f"{NOTE_FOLDER}/_index.md"
    index_content = (
        '---\n'
        'title: Content Collection\n'
        'cssclasses: [wide-page]\n'
        '---\n'
        '\n'
        '# 📚 Content Collection\n'
        '\n'
        '```dataview\n'
        'TABLE category AS "Category", date AS "Date", source AS "Source"\n'
        f'FROM "{NOTE_FOLDER}"\n'
        'WHERE type = "collection"\n'
        'SORT date DESC\n'
        '```\n'
    )
    try:
        _api_request("POST", "/note", {
            "vault": FAST_NOTE_VAULT,
            "path": index_path,
            "content": index_content,
        })
        logger.info(f"Index page ensured at {index_path}")
    except Exception as e:
        logger.error(f"Failed to ensure index page: {e}")


# ─── Message Parsing ────────────────────────────────────────────────

def extract_message_parts(message: str) -> tuple[str | None, str | None, bool]:
    """Extract title and URL from message.

    Returns:
        (title, url, needs_fetching)
    """
    url_match = URL_PATTERN.search(message)
    if not url_match:
        return None, None, False

    url = url_match.group()
    text_before_url = message[:url_match.start()].strip()

    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        text_before_url = re.sub(pattern, '', text_before_url, flags=re.IGNORECASE).strip()

    if text_before_url and len(text_before_url) > 2:
        return text_before_url, url, False
    else:
        return None, url, True


# ─── URL Content Fetching ───────────────────────────────────────────

def is_twitter_url(url: str) -> bool:
    return bool(re.search(r'(twitter\.com|x\.com)/\w+/status/\d+', url))


def fetch_twitter_content(url: str) -> str | None:
    try:
        oembed_url = f"https://publish.twitter.com/oembed?url={url}"
        response = requests.get(oembed_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'html' in data:
            soup = BeautifulSoup(data['html'], 'html.parser')
            blockquote = soup.find('blockquote')
            if blockquote:
                paragraphs = blockquote.find_all('p')
                tweet_text = ' '.join(p.get_text() for p in paragraphs)
                if tweet_text:
                    return tweet_text.strip()
        if 'author_name' in data:
            return f"Tweet by {data['author_name']}"
        return None
    except Exception as e:
        logger.error(f"Failed to fetch Twitter content: {e}")
        return None


def fetch_url_content(url: str) -> str | None:
    if is_twitter_url(url):
        content = fetch_twitter_content(url)
        if content:
            return content

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for selector in [
            ('meta', {'property': 'og:description'}),
            ('meta', {'attrs': {'name': 'twitter:description'}}),
            ('meta', {'attrs': {'name': 'description'}}),
            ('meta', {'property': 'og:title'}),
        ]:
            tag = soup.find(selector[0], **selector[1]) if len(selector) > 1 else None
            if tag and tag.get('content'):
                return tag['content']

        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        return None
    except Exception as e:
        logger.error(f"Failed to fetch URL content: {e}")
        return None


# ─── Claude AI ──────────────────────────────────────────────────────

def get_categories() -> list[str]:
    return [c.strip() for c in CATEGORIES.split(",") if c.strip()]


def get_category_from_claude(title: str) -> str:
    try:
        categories = get_categories()
        categories_list = "\n".join(f"- {c}" for c in categories)
        message = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": f"""Based on this title, assign ONE category from this list:
{categories_list}

Title: {title}

Respond with ONLY the category name exactly as shown above, nothing else."""
            }]
        )
        category = message.content[0].text.strip()
        if category in categories:
            return category
        for c in categories:
            if c.lower() in category.lower() or category.lower() in c.lower():
                return c
        return categories[0] if categories else "Other"
    except Exception as e:
        logger.error(f"Failed to get category from Claude: {e}")
        categories = get_categories()
        return categories[0] if categories else "Other"


def get_title_and_category_from_claude(content: str, url: str) -> tuple[str, str]:
    try:
        if len(content) > 2000:
            content = content[:2000] + "..."
        categories = get_categories()
        categories_list = "\n".join(f"- {c}" for c in categories)
        source_line = f"\nURL: {url}" if url else ""
        message = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""Based on this content, provide:
1. A concise title (under 50 characters, match the source language - if content is Chinese, title should be Chinese)
2. A category from this list ONLY:
{categories_list}
{source_line}
Content: {content}

Respond in this exact format (two lines only):
TITLE: [your title here]
CATEGORY: [category exactly as shown above]"""
            }]
        )
        response_text = message.content[0].text.strip()
        lines = response_text.split('\n')

        title = "Untitled"
        default_category = categories[0] if categories else "Other"
        category = default_category

        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("CATEGORY:"):
                cat = line.replace("CATEGORY:", "").strip()
                if cat in categories:
                    category = cat
                else:
                    for c in categories:
                        if c.lower() in cat.lower() or cat.lower() in c.lower():
                            category = c
                            break

        return title, category
    except Exception as e:
        logger.error(f"Failed to get title and category from Claude: {e}")
        categories = get_categories()
        return "Untitled", categories[0] if categories else "Other"


# ─── Telegram Handler ───────────────────────────────────────────────

def format_category_options() -> str:
    return "\n".join(f"{i+1}. {cat}" for i, cat in enumerate(get_categories()))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    logger.info(f"Received message: {text[:100]}...")

    # Category selection reply (single number)
    if text.isdigit():
        num = int(text)
        categories = get_categories()
        if 1 <= num <= len(categories):
            pending = context.user_data.get("pending_category_edit")
            if pending:
                new_category = categories[num - 1]
                note_path = pending["note_path"]
                old_category = pending["category"]

                del context.user_data["pending_category_edit"]

                if new_category == old_category:
                    await update.message.reply_text(f"Category unchanged: {old_category}")
                    return

                success, error = update_category(note_path, new_category)
                if success:
                    await update.message.reply_text(
                        f"✅ Category updated: {old_category} → {new_category}"
                    )
                else:
                    await update.message.reply_text(f"❌ Failed to update category:\n{error}")
                return

    # Clear pending edit on new content
    if "pending_category_edit" in context.user_data:
        del context.user_data["pending_category_edit"]

    # Extract message parts
    title, url, needs_fetching = extract_message_parts(text)

    await update.message.reply_text("⏳ Processing...")

    try:
        if not url:
            # Pure text
            logger.info("Type C: Pure text detected")
            title, category = get_title_and_category_from_claude(text, "")
            content_to_save = text
        elif needs_fetching:
            # Pure URL
            logger.info(f"Type B: Pure URL detected, fetching content from {url}")
            content = fetch_url_content(url)
            if content:
                title, category = get_title_and_category_from_claude(content, url)
            else:
                title, category = get_title_and_category_from_claude(f"URL: {url}", url)
            content_to_save = url
        else:
            # Text + URL
            logger.info(f"Type A: Title detected: {title}")
            category = get_category_from_claude(title)
            content_to_save = url

        # Save to Obsidian
        success, error, note_path = save_to_obsidian(title, category, content_to_save)

        if success:
            context.user_data["pending_category_edit"] = {
                "note_path": note_path,
                "title": title,
                "category": category,
            }

            category_list = format_category_options()
            await update.message.reply_text(
                f"✅ Saved to Obsidian\n"
                f"Title: {title}\n"
                f"Category: {category}\n\n"
                f"Reply with a number to change category:\n{category_list}"
            )
        else:
            await update.message.reply_text(f"❌ Failed to save:\n{error}")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(f"❌ Error processing message:\n{str(e)}")


def main() -> None:
    missing_vars = []
    for var_name in ["TELEGRAM_BOT_TOKEN", "ANTHROPIC_API_KEY", "FAST_NOTE_URL", "FAST_NOTE_TOKEN"]:
        if not os.environ.get(var_name):
            missing_vars.append(var_name)

    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        return

    # Ensure index page exists on startup
    ensure_index_page()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Bot started — saving to Obsidian via Fast Note Sync")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
