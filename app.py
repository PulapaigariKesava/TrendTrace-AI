
import os
from datetime import date, datetime, timedelta, timezone

import requests
from flask import Flask, request, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

DAYS = 30
BLUESKY_URL = (
    "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
)


def safe_date(value):
    """Convert an ISO timestamp to a UTC calendar date."""
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).date()
    except (ValueError, TypeError):
        return None


def fetch_news(topic, start_date, end_date):
    """Retrieve up to 100 matching news articles."""
    if not NEWS_API_KEY:
        return [], "NewsAPI key missing. Check your .env file."

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": topic,
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "sortBy": "publishedAt",
                "pageSize": 100,
                "language": "en",
                "apiKey": NEWS_API_KEY,
            },
            timeout=20,
        )

        data = response.json()

        if response.status_code != 200:
            return [], data.get(
                "message", "NewsAPI request failed."
            )

        return data.get("articles", []), None

    except requests.RequestException:
        return [], "Could not connect to NewsAPI."
    except ValueError:
        return [], "NewsAPI returned an invalid response."


def fetch_bluesky(topic, start_date, end_date):
    """
    Search public Bluesky posts for the selected date range.
    Retrieve a bounded sample, not a complete network-wide count.
    """
    posts = []
    error = None
    cursor = None

    try:
        # Up to 5 pages of 100 posts to limit request volume.
        for _ in range(5):
            params = {
                "q": topic,
                "since": start_date.isoformat(),
                "until": (end_date + timedelta(days=1)).isoformat(),
                "sort": "latest",
                "limit": 100,
            }

            if cursor:
                params["cursor"] = cursor

            response = requests.get(
                BLUESKY_URL,
                params=params,
                timeout=20,
            )

            if response.status_code != 200:
                error = "Bluesky search is temporarily unavailable."
                break

            data = response.json()
            batch = data.get("posts", [])
            posts.extend(batch)

            cursor = data.get("cursor")
            if not cursor or not batch:
                break

    except requests.RequestException:
        error = "Could not connect to Bluesky."

    except ValueError:
        error = "Bluesky returned an invalid response."

    return posts, error


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b1020">
<title>TrendTrace AI | Trend Intelligence</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: Inter, Arial, sans-serif;
    background: #0b1020;
    color: #f1f5f9;
    line-height: 1.6;
}

a { color: inherit; text-decoration: none; }
.container { width: min(1120px, 92%); margin: auto; }

nav {
    background: #0b1020;
    border-bottom: 1px solid #202a40;
    position: sticky;
    top: 0;
    z-index: 5;
}

.nav-inner {
    min-height: 72px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
}

.brand { font-size: 23px; font-weight: 800; }
.brand span, .accent { color: #38bdf8; }

.nav-links { display: flex; gap: 22px; color: #aab6cc; font-size: 14px; }
.nav-links a:hover { color: #38bdf8; }

.hero {
    text-align: center;
    padding: 66px 0 36px;
    background: radial-gradient(ellipse at 50% 0%, #15304b 0%, transparent 65%);
}

.eyebrow {
    color: #7dd3fc;
    background: #102239;
    border: 1px solid #24435d;
    display: inline-block;
    border-radius: 25px;
    padding: 6px 12px;
    font-size: 12px;
    margin-bottom: 20px;
}

h1 { font-size: clamp(35px, 6vw, 60px); line-height: 1.15; }
.hero p { color: #9caac0; max-width: 640px; margin: 16px auto 25px; }

.search-form {
    display: flex;
    gap: 8px;
    max-width: 680px;
    margin: auto;
    padding: 8px;
    background: #151e30;
    border: 1px solid #334155;
    border-radius: 14px;
}

.search-form input {
    flex: 1;
    min-width: 0;
    background: transparent;
    border: 0;
    outline: none;
    padding: 12px;
    color: white;
    font-size: 15px;
}

button {
    cursor: pointer;
    font: inherit;
}

.search-btn {
    border: 0;
    border-radius: 9px;
    padding: 10px 20px;
    background: #38bdf8;
    color: #07111f;
    font-weight: 800;
}

.chips {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 9px;
    margin-top: 20px;
}

.chip {
    border: 1px solid #2b3850;
    border-radius: 25px;
    padding: 7px 13px;
    color: #cbd5e1;
    background: #141d30;
    font-size: 13px;
}

.chip:hover { border-color: #38bdf8; color: #7dd3fc; }

main { padding-bottom: 55px; }

.section { margin-top: 36px; scroll-margin-top: 90px; }

.section-title {
    font-size: 25px;
    margin-bottom: 5px;
}

.muted { color: #94a3b8; font-size: 13px; }

.stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-top: 22px;
}

.stat, .panel, .article, .post {
    background: #131d30;
    border: 1px solid #26334a;
    border-radius: 15px;
}

.stat { padding: 19px; }
.stat-label { color: #94a3b8; font-size: 12px; }
.stat-value { font-size: 22px; font-weight: 800; margin-top: 7px; overflow-wrap: anywhere; }

.panel { padding: 22px; margin-top: 18px; }
.chart-wrap { position: relative; width: 100%; height: 330px; margin-top: 18px; }

.notice {
    margin-top: 16px;
    background: #172237;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 13px 15px;
    color: #cbd5e1;
    font-size: 13px;
}

.error { color: #fecaca; border-color: #7f303d; }

.article-grid, .post-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 15px;
    margin-top: 20px;
}

.article, .post { padding: 20px; overflow-wrap: anywhere; }

.tag {
    color: #7dd3fc;
    font-size: 11px;
    font-weight: 700;
    background: #102a40;
    padding: 4px 9px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 10px;
}

.article h3, .post h3 { font-size: 17px; line-height: 1.4; margin-bottom: 10px; }
.article p, .post p { color: #aab7ca; font-size: 13px; margin-bottom: 12px; }
.link { color: #38bdf8; font-size: 13px; font-weight: 700; }

footer {
    border-top: 1px solid #202a40;
    text-align: center;
    padding: 24px 0;
    color: #75839a;
    font-size: 12px;
}

@media (max-width: 750px) {
    .nav-links { gap: 12px; font-size: 12px; }
    .nav-links .optional { display: none; }
    .hero { padding-top: 48px; }
    .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .article-grid, .post-grid { grid-template-columns: 1fr; }
    .chart-wrap { height: 290px; }
    .stat { padding: 14px; }
    .stat-value { font-size: 18px; }
}

@media (max-width: 400px) {
    .brand { font-size: 19px; }
    .search-btn { padding: 9px 12px; }
    .search-form input { padding: 9px 5px; font-size: 13px; }
}
</style>
  <meta name="google-site-verification" content="te5R-_G6a7ffdQQMswbItutHRBXGsxJEnIexue-o9wA" />
</head>

<body>
<nav>
    <div class="container nav-inner">
        <a href="/" class="brand">TrendTrace<span> AI</span></a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="#analytics">Analytics</a>
            <a href="#articles" class="optional">News</a>
            <a href="#social" class="optional">Social</a>
        </div>
    </div>
</nav>

<header class="hero container">
    <div class="eyebrow">✦ TREND LIFECYCLE INTELLIGENCE</div>
    <h1>Every trend has a story.<br><span class="accent">Trace its journey.</span></h1>
    <p>Compare daily news coverage with publicly searchable Bluesky activity over the last 30 days.</p>

    <form class="search-form" method="POST" action="/#analytics">
        <input name="topic" maxlength="150" required
               placeholder="Search a topic, event or person..."
               value="{{ topic }}" aria-label="Topic">
        <button class="search-btn" type="submit">Analyze ↗</button>
    </form>

    <div class="chips">
        {% for item in topics %}
        <form method="POST" action="/#analytics">
            <input type="hidden" name="topic" value="{{ item }}">
            <button class="chip" type="submit">{{ item }}</button>
        </form>
        {% endfor %}
    </div>
</header>

<main class="container">
{% if topic %}
<section class="section" id="analytics">
    <h2 class="section-title">Trend lifecycle: {{ topic }}</h2>
    <p class="muted">Window: {{ start_date }} to {{ end_date }} · UTC dates</p>

    {% if errors %}
        {% for message in errors %}
        <div class="notice error">{{ message }}</div>
        {% endfor %}
    {% endif %}

    <div class="stats">
        <div class="stat">
            <div class="stat-label">First observed activity</div>
            <div class="stat-value">{{ first_day or "Not found" }}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Peak observed day ({{ peak_count }} item{% if peak_count != 1 %}s{% endif %})</div>
            <div class="stat-value">{{ peak_day or "Not found" }}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Last observed activity</div>
            <div class="stat-value">{{ last_day or "Not found" }}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Retrieved items</div>
            <div class="stat-value">{{ total_items }}</div>
        </div>
    </div>

    <div class="panel">
        <h3>Daily activity graph</h3>
        <p class="muted">Counts of retrieved items per UTC day, not total internet-wide popularity. The peak day is highlighted in amber.</p>
        {% if peak_day %}
        <p class="notice">Peak activity: {{ peak_day }} · {{ peak_count }} item{% if peak_count != 1 %}s{% endif %}</p>
        {% endif %}
        <div class="chart-wrap">
            <canvas id="trendChart" aria-label="Daily news and Bluesky activity graph"></canvas>
        </div>
        <div class="notice">
            <strong>How to read this:</strong>
            the peak is the highest daily combined count in the data retrieved.
            “Last observed” is not proof that the trend has ended. Search limits,
            API coverage and indexing can affect the shape of the graph.
        </div>
    </div>
</section>

<section class="section" id="articles">
    <h2 class="section-title">News coverage</h2>
    <p class="muted">Articles returned by NewsAPI for the selected period.</p>

    {% if articles %}
    <div class="article-grid">
        {% for article in articles %}
        <article class="article">
            <span class="tag">{{ article.source.name or "News source" }}</span>
            <h3>{{ article.title or "Untitled article" }}</h3>
            <p>{{ article.description or "No description available." }}</p>
            <p>Published: {{ article.publishedAt or "Unknown" }}</p>
            <a class="link" href="{{ article.url }}" target="_blank"
               rel="noopener noreferrer">Read original article ↗</a>
        </article>
        {% endfor %}
    </div>
    {% else %}
    <div class="notice">No news articles were retrieved for this period.</div>
    {% endif %}
</section>

<section class="section" id="social">
    <h2 class="section-title">Public social activity</h2>
    <p class="muted">A sample of publicly searchable Bluesky posts.</p>

    {% if posts %}
    <div class="post-grid">
        {% for post in posts %}
        <article class="post">
            <span class="tag">Bluesky · {{ post.day or "Date unknown" }}</span>
            <h3>@{{ post.handle }}</h3>
            <p>{{ post.text }}</p>
            <p>Likes: {{ post.likes }} · Reposts: {{ post.reposts }} · Replies: {{ post.replies }}</p>
            <a class="link" href="{{ post.url }}" target="_blank"
               rel="noopener noreferrer">View public post ↗</a>
        </article>
        {% endfor %}
    </div>
    {% else %}
    <div class="notice">No public Bluesky posts were retrieved for this search.</div>
    {% endif %}
</section>

<script>
const labels = {{ chart_labels | tojson }};
const newsCounts = {{ news_counts | tojson }};
const socialCounts = {{ social_counts | tojson }};
const peakIndex = {{ peak_index | tojson }};
const newsColors = newsCounts.map((_, index) =>
    index === peakIndex ? "rgba(245,158,11,0.85)" : "rgba(56,189,248,0.35)"
);
const socialColors = socialCounts.map((_, index) =>
    index === peakIndex ? "rgba(251,191,36,0.85)" : "rgba(167,139,250,0.35)"
);

const canvas = document.getElementById("trendChart");

if (canvas && window.Chart) {
    new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "News articles retrieved",
                    data: newsCounts,
                    borderColor: "#38bdf8",
                    backgroundColor: newsColors,
                    pointRadius: 2,
                    borderWidth: 2,
                    tension: 0.3
                },
                {
                    label: "Bluesky posts retrieved",
                    data: socialCounts,
                    borderColor: "#a78bfa",
                    backgroundColor: socialColors,
                    pointRadius: 2,
                    borderWidth: 2,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    labels: { color: "#cbd5e1" }
                }
            },
            scales: {
                x: {
                    ticks: { color: "#94a3b8", maxTicksLimit: 8 },
                    grid: { color: "rgba(148,163,184,0.08)" }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: "#94a3b8", precision: 0 },
                    grid: { color: "rgba(148,163,184,0.12)" }
                }
            }
        }
    });
} else if (canvas) {
    canvas.parentElement.innerHTML =
        "<p class='muted'>The graph library did not load. Check your internet connection and refresh.</p>";
}
</script>
{% else %}
<section class="section">
    <div class="panel">
        <h2>Start exploring a trend</h2>
        <p class="muted">Search a topic above to retrieve recent articles, public posts and a 30-day activity graph.</p>
    </div>
</section>
{% endif %}
</main>

<footer>
    <div class="container">TrendTrace AI · Evidence-led trend exploration</div>
</footer>
</body>
</html>
"""


TOPICS = [
    "Artificial Intelligence",
    "India",
    "Technology",
    "Business",
    "Sports",
    "Climate"
]


@app.get("/")
def landing():
    return render_template("landing.html", topics=TOPICS)


@app.route("/analytics", methods=["GET", "POST"])
def analytics():
    topic = ""
    articles = []
    posts = []
    errors = []
    peak_count = 0
    peak_index = None

    today = date.today()
    start_date = today - timedelta(days=DAYS - 1)
    end_date = today

    # Default graph arrays always contain the full 30-day window.
    day_list = [
        start_date + timedelta(days=i)
        for i in range(DAYS)
    ]
    news_by_day = {day.isoformat(): 0 for day in day_list}
    social_by_day = {day.isoformat(): 0 for day in day_list}

    if request.method == "POST":
        topic = request.form.get("topic", "").strip()[:150]

        if topic:
            articles, news_error = fetch_news(
                topic, start_date, end_date
            )

            if news_error:
                errors.append(news_error)

            raw_posts, social_error = fetch_bluesky(
                topic, start_date, end_date
            )

            if social_error:
                errors.append(social_error)

            # Count the articles returned by the API by publication day.
            for article in articles:
                published_day = safe_date(article.get("publishedAt"))

                if published_day and published_day.isoformat() in news_by_day:
                    news_by_day[published_day.isoformat()] += 1

            # Prepare public post cards and daily sample counts.
            for item in raw_posts:
                record = item.get("record", {})
                author = item.get("author", {})
                created = record.get("createdAt")
                post_day = safe_date(created)

                if post_day and post_day.isoformat() in social_by_day:
                    social_by_day[post_day.isoformat()] += 1

                handle = author.get("handle", "unknown")
                uri = item.get("uri", "")
                rkey = uri.rsplit("/", 1)[-1] if uri else ""

                posts.append({
                    "handle": handle,
                    "text": record.get("text", "[No text available]"),
                    "day": post_day.isoformat() if post_day else None,
                    "likes": item.get("likeCount", 0),
                    "reposts": item.get("repostCount", 0),
                    "replies": item.get("replyCount", 0),
                    "url": (
                        f"https://bsky.app/profile/{handle}/post/{rkey}"
                        if rkey else "https://bsky.app"
                    ),
                })

            # Build lifecycle metrics from observed counts only.
            combined = {
                day: news_by_day[day] + social_by_day[day]
                for day in news_by_day
            }

            active_days = [
                day for day, count in combined.items() if count > 0
            ]

            first_day = active_days[0] if active_days else None
            last_day = active_days[-1] if active_days else None

            if active_days:
                peak_count = max(combined[day] for day in active_days)
                peak_day = next(day for day in active_days if combined[day] == peak_count)
                peak_index = next(i for i, day in enumerate(combined) if day == peak_day)
            else:
                peak_day = None

        else:
            errors.append("Enter a topic to analyze.")
            first_day = last_day = peak_day = None
            peak_count = 0
            peak_index = None
    else:
        first_day = last_day = peak_day = None

    return render_template(
        "analytics.html",
        topic=topic,
        articles=articles,
        posts=posts[:30],
        errors=errors,
        topics=TOPICS,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        first_day=first_day,
        peak_day=peak_day,
        peak_count=peak_count,
        peak_index=peak_index,
        last_day=last_day,
        total_items=len(articles) + len(posts),
        chart_labels=[day.strftime("%d %b") for day in day_list],
        news_counts=[news_by_day[day.isoformat()] for day in day_list],
        social_counts=[social_by_day[day.isoformat()] for day in day_list],
    )


if __name__ == "__main__":
    app.run(debug=True)
