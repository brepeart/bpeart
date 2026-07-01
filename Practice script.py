import feedparser
import argparse
import json
import webbrowser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# List of cybersecurity RSS feeds
feeds = [
    "https://feeds.feedburner.com/KrebsOnSecurity",
    "https://feeds.feedburner.com/TheHackersNews",
]

SEEN_ARTICLES_PATH = Path(".seen_articles.json")


def fetch_news():
    articles = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published,
                }
            )

    def published_dt(article):
        value = article.get("published")
        if not value:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (TypeError, ValueError):
            return datetime.min.replace(tzinfo=timezone.utc)

    articles.sort(key=published_dt, reverse=True)
    return articles


def load_seen_links():
    if not SEEN_ARTICLES_PATH.exists():
        return set()
    try:
        data = json.loads(SEEN_ARTICLES_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(str(item) for item in data)
    except (json.JSONDecodeError, OSError):
        pass
    return set()


def save_seen_links(seen_links):
    SEEN_ARTICLES_PATH.write_text(
        json.dumps(sorted(seen_links), indent=2),
        encoding="utf-8",
    )


def print_articles(articles, limit):
    for idx, article in enumerate(articles[:limit], start=1):
        print(f"{idx}. {article['title']}")
        print(f"   Published: {article['published']}")
        print(f"   Link: {article['link']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Fetch and display cybersecurity RSS articles.")
    parser.add_argument("--limit", type=int, default=5, help="Number of articles to show.")
    parser.add_argument("--open", action="store_true", help="Open shown article links in your browser.")
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="Show only articles not seen in previous runs.",
    )
    args = parser.parse_args()

    news_articles = fetch_news()

    if args.new_only:
        seen_links = load_seen_links()
        filtered_articles = [a for a in news_articles if a.get("link") not in seen_links]
        to_show = filtered_articles[: max(args.limit, 0)]
        print_articles(to_show, args.limit)

        for article in to_show:
            link = article.get("link")
            if link:
                seen_links.add(link)
        save_seen_links(seen_links)
    else:
        to_show = news_articles[: max(args.limit, 0)]
        print_articles(to_show, args.limit)

    if args.open:
        for article in to_show:
            link = article.get("link")
            if link:
                webbrowser.open(link)


if __name__ == "__main__":
    main()