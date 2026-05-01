"""
Data Generator — creates all CSV files and PDF documents
for the Insights Assistant knowledge base.
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DOCS_DIR = Path("docs")
DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

random.seed(42)

# ── Constants ─────────────────────────────────────────────────────────────────
TITLES = [
    "Stellar Run", "Dark Orbit", "Last Kingdom", "Neon Drift",
    "Shadow Protocol", "Echo Chamber", "Iron Fable", "Crimson Tide",
    "The Hollow", "Bright Horizons", "Comedy Chaos", "Laugh Track",
    "Funny Business", "Jest Mode", "Roast Masters"
]
GENRES = ["Sci-Fi", "Action", "Drama", "Thriller", "Comedy"]
TITLE_GENRE = {
    "Stellar Run": "Sci-Fi", "Dark Orbit": "Sci-Fi", "Neon Drift": "Sci-Fi",
    "Last Kingdom": "Drama", "Iron Fable": "Drama", "The Hollow": "Drama",
    "Shadow Protocol": "Thriller", "Echo Chamber": "Thriller", "Crimson Tide": "Thriller",
    "Bright Horizons": "Action", "Shadow Protocol": "Action",
    "Comedy Chaos": "Comedy", "Laugh Track": "Comedy",
    "Funny Business": "Comedy", "Jest Mode": "Comedy", "Roast Masters": "Comedy"
}
CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
          "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat"]
SEGMENTS = ["18-24", "25-34", "35-44", "45-54", "55+"]
PLATFORMS = ["Mobile", "Web", "Smart TV", "Tablet"]

def rand_date(start="2025-01-01", end="2025-12-31"):
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    return s + timedelta(days=random.randint(0, (e - s).days))

# ── 1. movies.csv ─────────────────────────────────────────────────────────────
movies = []
for i, title in enumerate(TITLES, 1):
    genre = TITLE_GENRE.get(title, random.choice(GENRES))
    # Stellar Run and Dark Orbit are intentionally top performers
    base = 900 if title in ["Stellar Run", "Dark Orbit"] else random.randint(200, 850)
    # Comedy titles intentionally underperform
    if genre == "Comedy":
        base = random.randint(80, 250)
    movies.append({
        "movie_id": i,
        "title": title,
        "genre": genre,
        "release_date": rand_date("2024-06-01", "2025-03-01").strftime("%Y-%m-%d"),
        "budget_usd": random.randint(1_000_000, 50_000_000),
        "runtime_minutes": random.randint(85, 160),
        "language": random.choice(["English", "Hindi", "Telugu"]),
        "rating": round(random.uniform(5.5, 9.8) if base > 400 else random.uniform(3.0, 6.5), 1),
    })
pd.DataFrame(movies).to_csv(DATA_DIR / "movies.csv", index=False)
print("✓ movies.csv")

# ── 2. viewers.csv ────────────────────────────────────────────────────────────
viewers = []
for i in range(1, 501):
    viewers.append({
        "viewer_id": i,
        "age_segment": random.choice(SEGMENTS),
        "city": random.choice(CITIES),
        "platform": random.choice(PLATFORMS),
        "subscription_tier": random.choice(["Free", "Basic", "Premium"]),
        "joined_date": rand_date("2022-01-01", "2024-12-01").strftime("%Y-%m-%d"),
    })
pd.DataFrame(viewers).to_csv(DATA_DIR / "viewers.csv", index=False)
print("✓ viewers.csv")

# ── 3. watch_activity.csv ─────────────────────────────────────────────────────
activity = []
movie_ids = [m["movie_id"] for m in movies]
for i in range(1, 2001):
    movie = random.choice(movies)
    # Stellar Run gets 3x more watch events (trending logic)
    if random.random() < 0.15:
        movie = next(m for m in movies if m["title"] == "Stellar Run")
    activity.append({
        "activity_id": i,
        "viewer_id": random.randint(1, 500),
        "movie_id": movie["movie_id"],
        "watch_date": rand_date("2025-01-01", "2025-04-30").strftime("%Y-%m-%d"),
        "watch_duration_minutes": random.randint(10, movie["runtime_minutes"]),
        "completed": random.choice([True, False, True]),  # skew True
        "device": random.choice(PLATFORMS),
    })
pd.DataFrame(activity).to_csv(DATA_DIR / "watch_activity.csv", index=False)
print("✓ watch_activity.csv")

# ── 4. reviews.csv ────────────────────────────────────────────────────────────
reviews = []
for i in range(1, 801):
    movie = random.choice(movies)
    sentiment = "positive" if movie["rating"] >= 7.0 else "negative" if movie["rating"] < 5.5 else "neutral"
    reviews.append({
        "review_id": i,
        "movie_id": movie["movie_id"],
        "viewer_id": random.randint(1, 500),
        "score": random.randint(1, 10),
        "sentiment": sentiment,
        "review_date": rand_date("2025-01-01", "2025-04-30").strftime("%Y-%m-%d"),
    })
pd.DataFrame(reviews).to_csv(DATA_DIR / "reviews.csv", index=False)
print("✓ reviews.csv")

# ── 5. marketing_spend.csv ────────────────────────────────────────────────────
marketing = []
for movie in movies:
    for month in range(1, 5):
        marketing.append({
            "movie_id": movie["movie_id"],
            "title": movie["title"],
            "month": f"2025-{month:02d}",
            "channel": random.choice(["Social Media", "OTT Ads", "TV", "Influencer"]),
            "spend_usd": random.randint(10_000, 500_000),
            "impressions": random.randint(50_000, 5_000_000),
            "clicks": random.randint(1_000, 200_000),
        })
pd.DataFrame(marketing).to_csv(DATA_DIR / "marketing_spend.csv", index=False)
print("✓ marketing_spend.csv")

# ── 6. regional_performance.csv ───────────────────────────────────────────────
regional = []
for city in CITIES:
    for movie in movies:
        regional.append({
            "city": city,
            "movie_id": movie["movie_id"],
            "title": movie["title"],
            "month": f"2025-{random.randint(1,4):02d}",
            "views": random.randint(100, 15000) if movie["title"] != "Stellar Run" else random.randint(8000, 20000),
            "engagement_score": round(random.uniform(2.0, 10.0), 2),
            "avg_watch_pct": round(random.uniform(30.0, 95.0), 1),
        })
pd.DataFrame(regional).to_csv(DATA_DIR / "regional_performance.csv", index=False)
print("✓ regional_performance.csv")

# ── 7. PDF Documents (plain text written to .txt then saved as .pdf) ──────────
def write_pdf(filename: str, title: str, content: str):
    """Write a simple text-based PDF using only stdlib (no reportlab needed)."""
    # We write as plain .txt — PyPDF/LangChain will load it fine as a text doc
    # For a real submission use reportlab; here we keep zero extra deps
    path = DOCS_DIR / filename
    path.write_text(f"{title}\n{'='*60}\n\n{content}", encoding="utf-8")
    print(f"✓ {filename}")

write_pdf("quarterly_executive_report.txt", "Q1 2025 Executive Report", """
EXECUTIVE SUMMARY — Q1 2025

Overall platform performance exceeded projections by 18%.
Stellar Run emerged as the breakout title of the quarter,
driven by a viral social media campaign and strong word-of-mouth
among the 25-34 demographic. Watch time for Sci-Fi content
grew 42% quarter-over-quarter.

Dark Orbit maintained its position as the second-highest
performing title with 91% completion rates among Premium subscribers.

CONCERN: Comedy genre performance declined 31% vs Q4 2024.
Root cause analysis points to misaligned marketing spend on TV
channels when the target audience (18-24) is primarily on mobile.

RECOMMENDATION: Reallocate 40% of comedy marketing budget
from TV to Social Media and Influencer channels for Q2.
""")

write_pdf("campaign_performance_summary.txt", "Campaign Performance Summary — Q1 2025", """
CAMPAIGN HIGHLIGHTS

Stellar Run — #StellarRunChallenge (TikTok/Instagram)
- Impressions: 12.4 million
- Engagement rate: 8.7% (industry avg: 2.1%)
- Contributed to 340% spike in weekly views in March 2025
- Key driver: influencer partnerships with 3 creators (2M+ followers each)

Dark Orbit — Paid OTT Campaign
- CPM: $4.20 (below $6.00 target)
- Click-through rate: 3.1%
- Strong performance in Bangalore and Hyderabad markets

Comedy Titles — TV Broadcast Campaign
- Impressions: 8.1 million
- Engagement rate: 0.9% (below benchmark)
- Mismatch identified: TV audience skews 45+ while comedy content
  targets 18-24 age group. Campaign restructure recommended.
""")

write_pdf("audience_behavior_report.txt", "Audience Behavior Report — 2025", """
AUDIENCE INSIGHTS

Top engaged segment: 25-34 (avg session: 74 minutes)
Fastest growing segment: 18-24 (+28% YoY)
Highest churn risk: 55+ on Free tier

Platform breakdown:
- Mobile: 52% of total views (dominant)
- Smart TV: 28% (Premium subscribers)
- Web: 14%
- Tablet: 6%

City-level engagement leaders (Q1 2025):
1. Bangalore — avg engagement score 8.4
2. Hyderabad — avg engagement score 8.1
3. Mumbai — avg engagement score 7.9

Completion rates by genre:
- Sci-Fi: 84%
- Thriller: 79%
- Drama: 76%
- Action: 71%
- Comedy: 48% (lowest — content-audience fit issue suspected)
""")

write_pdf("content_roadmap.txt", "Content Roadmap — Q2-Q3 2025", """
UPCOMING TITLES PIPELINE

Q2 2025:
- Stellar Run: Season 2 (Sci-Fi) — greenlit based on S1 performance
- Project Mirage (Thriller) — post-production
- City Lights (Drama) — filming

Q3 2025:
- Dark Orbit: Origins (Sci-Fi prequel)
- The Comeback (Comedy — restructured for mobile-first audience)

STRATEGIC PRIORITIES:
1. Double down on Sci-Fi — highest ROI genre
2. Invest in mobile-first comedy format (short episodes, <25 min)
3. Expand regional language content for Tier-2 city growth
""")

write_pdf("policy_guidelines.txt", "Data & Content Policy Guidelines", """
DATA PRIVACY POLICY

All viewer data is pseudonymized at ingestion.
PII (names, emails, payment info) is stored in isolated secure vaults
and is NOT accessible through the analytics assistant.

The AI assistant has read-only access to:
- Aggregated viewing statistics
- Genre and title performance metrics
- Regional engagement scores
- Marketing spend summaries

The AI assistant does NOT have access to:
- Individual viewer identities
- Payment or billing information
- Raw behavioral logs with PII

ACCESS CONTROL:
- All data queries pass through validated tool functions
- No direct database access is exposed to the LLM
- Query results are filtered before being passed to the model
""")

print("\n✅ All data files generated successfully!")
print(f"   CSVs  → {DATA_DIR.resolve()}")
print(f"   Docs  → {DOCS_DIR.resolve()}")
