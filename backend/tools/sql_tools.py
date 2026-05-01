"""
SQL Tools — secure pandas-based query functions.

Rules enforced here:
  - No raw PII ever returned (viewer names, emails, payment info)
  - Results capped at max_rows_to_llm before reaching the agent
  - Each function has a single, auditable responsibility
"""
import logging
import pandas as pd
from backend.data_loader import store
from backend.config import settings

log = logging.getLogger(__name__)


def _cap(df: pd.DataFrame) -> pd.DataFrame:
    """Hard cap rows sent to LLM — prevents prompt stuffing."""
    return df.head(settings.max_rows_to_llm)


# ── Tool 1 ────────────────────────────────────────────────────────────────────
def get_top_performing_titles(year: int = 2025, top_n: int = 10) -> str:
    """
    Returns top N titles by total watch count for a given year.
    Source: watch_activity.csv + movies.csv
    """
    try:
        wa = store.watch_activity.copy()
        wa["watch_date"] = pd.to_datetime(wa["watch_date"])
        wa = wa[wa["watch_date"].dt.year == year]

        counts = (
            wa.groupby("movie_id")
            .size()
            .reset_index(name="total_views")
        )
        merged = counts.merge(
            store.movies[["movie_id", "title", "genre", "rating"]],
            on="movie_id"
        ).sort_values("total_views", ascending=False)

        result = _cap(merged[["title", "genre", "rating", "total_views"]])
        log.info(f"[Tool] get_top_performing_titles(year={year}, top_n={top_n})")
        return result.head(top_n).to_string(index=False)
    except Exception as e:
        log.error(f"[Tool Error] get_top_performing_titles: {e}")
        return f"Error retrieving top titles: {str(e)}"


# ── Tool 2 ────────────────────────────────────────────────────────────────────
def get_title_trend(title: str) -> str:
    """
    Returns monthly view trend for a specific title.
    Source: watch_activity.csv + movies.csv
    """
    try:
        wa = store.watch_activity.copy()
        wa["watch_date"] = pd.to_datetime(wa["watch_date"])
        wa["month"] = wa["watch_date"].dt.to_period("M").astype(str)

        movie = store.movies[
            store.movies["title"].str.lower() == title.lower()
        ]
        if movie.empty:
            return f"Title '{title}' not found in database."

        movie_id = movie.iloc[0]["movie_id"]
        trend = (
            wa[wa["movie_id"] == movie_id]
            .groupby("month")
            .size()
            .reset_index(name="views")
            .sort_values("month")
        )
        log.info(f"[Tool] get_title_trend(title={title})")
        return f"Monthly trend for '{title}':\n" + trend.to_string(index=False)
    except Exception as e:
        log.error(f"[Tool Error] get_title_trend: {e}")
        return f"Error retrieving trend: {str(e)}"


# ── Tool 3 ────────────────────────────────────────────────────────────────────
def compare_titles(title_a: str, title_b: str) -> str:
    """
    Side-by-side comparison of two titles across views, rating,
    completion rate, and avg marketing spend.
    Source: movies.csv + watch_activity.csv + marketing_spend.csv
    """
    try:
        results = []
        for title in [title_a, title_b]:
            movie = store.movies[
                store.movies["title"].str.lower() == title.lower()
            ]
            if movie.empty:
                results.append(f"'{title}': not found")
                continue

            mid = movie.iloc[0]["movie_id"]
            genre = movie.iloc[0]["genre"]
            rating = movie.iloc[0]["rating"]

            wa = store.watch_activity[store.watch_activity["movie_id"] == mid]
            views = len(wa)
            completion = (
                round(wa["completed"].mean() * 100, 1)
                if not wa.empty else 0
            )

            spend = store.marketing[store.marketing["movie_id"] == mid]["spend_usd"].sum()

            results.append(
                f"Title      : {title}\n"
                f"Genre      : {genre}\n"
                f"Rating     : {rating}\n"
                f"Total Views: {views}\n"
                f"Completion%: {completion}%\n"
                f"Mktg Spend : ${spend:,.0f}"
            )

        log.info(f"[Tool] compare_titles({title_a}, {title_b})")
        return "\n\n".join(results)
    except Exception as e:
        log.error(f"[Tool Error] compare_titles: {e}")
        return f"Error comparing titles: {str(e)}"


# ── Tool 4 ────────────────────────────────────────────────────────────────────
def get_city_engagement(month: str = None) -> str:
    """
    Returns top cities ranked by average engagement score.
    Source: regional_performance.csv
    """
    try:
        rp = store.regional.copy()
        if month:
            rp = rp[rp["month"] == month]

        city_stats = (
            rp.groupby("city")
            .agg(
                avg_engagement=("engagement_score", "mean"),
                total_views=("views", "sum"),
                avg_watch_pct=("avg_watch_pct", "mean"),
            )
            .round(2)
            .sort_values("avg_engagement", ascending=False)
            .reset_index()
        )
        log.info(f"[Tool] get_city_engagement(month={month})")
        return _cap(city_stats).to_string(index=False)
    except Exception as e:
        log.error(f"[Tool Error] get_city_engagement: {e}")
        return f"Error retrieving city engagement: {str(e)}"


# ── Tool 5 ────────────────────────────────────────────────────────────────────
def get_genre_performance() -> str:
    """
    Returns aggregated performance metrics broken down by genre.
    Source: movies.csv + watch_activity.csv + reviews.csv
    """
    try:
        wa = store.watch_activity.copy()
        merged = wa.merge(
            store.movies[["movie_id", "genre"]],
            on="movie_id"
        )
        genre_stats = (
            merged.groupby("genre")
            .agg(
                total_views=("activity_id", "count"),
                avg_completion=("completed", "mean"),
            )
            .round(3)
            .reset_index()
        )
        genre_stats["avg_completion"] = (
            genre_stats["avg_completion"] * 100
        ).round(1).astype(str) + "%"

        ratings = (
            store.movies.groupby("genre")["rating"]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={"rating": "avg_rating"})
        )
        result = genre_stats.merge(ratings, on="genre").sort_values(
            "total_views", ascending=False
        )
        log.info("[Tool] get_genre_performance()")
        return result.to_string(index=False)
    except Exception as e:
        log.error(f"[Tool Error] get_genre_performance: {e}")
        return f"Error retrieving genre performance: {str(e)}"


# ── Tool 6 ────────────────────────────────────────────────────────────────────
def get_audience_segments() -> str:
    """
    Returns engagement breakdown by age segment and platform.
    NOTE: No individual viewer identity is exposed — aggregates only.
    Source: viewers.csv + watch_activity.csv
    """
    try:
        wa = store.watch_activity.copy()
        merged = wa.merge(
            store.viewers[["viewer_id", "age_segment", "platform"]],
            on="viewer_id"
        )
        seg = (
            merged.groupby(["age_segment", "platform"])
            .agg(total_views=("activity_id", "count"))
            .reset_index()
            .sort_values("total_views", ascending=False)
        )
        log.info("[Tool] get_audience_segments()")
        return _cap(seg).to_string(index=False)
    except Exception as e:
        log.error(f"[Tool Error] get_audience_segments: {e}")
        return f"Error retrieving audience segments: {str(e)}"


# ── Tool 7 ────────────────────────────────────────────────────────────────────
def get_chart_data(chart_type: str = "genre_views") -> dict:
    """
    Returns structured data for frontend Chart.js visualizations.
    chart_type options: 'genre_views', 'top_titles', 'city_engagement'
    """
    try:
        if chart_type == "genre_views":
            wa = store.watch_activity.merge(
                store.movies[["movie_id", "genre"]], on="movie_id"
            )
            data = wa.groupby("genre").size().reset_index(name="views")
            return {
                "labels": data["genre"].tolist(),
                "values": data["views"].tolist(),
                "title": "Views by Genre",
            }

        elif chart_type == "top_titles":
            wa = store.watch_activity.merge(
                store.movies[["movie_id", "title"]], on="movie_id"
            )
            data = (
                wa.groupby("title").size()
                .reset_index(name="views")
                .sort_values("views", ascending=False)
                .head(8)
            )
            return {
                "labels": data["title"].tolist(),
                "values": data["views"].tolist(),
                "title": "Top Titles by Views",
            }

        elif chart_type == "city_engagement":
            data = (
                store.regional.groupby("city")["engagement_score"]
                .mean()
                .round(2)
                .reset_index()
                .sort_values("engagement_score", ascending=False)
                .head(8)
            )
            return {
                "labels": data["city"].tolist(),
                "values": data["engagement_score"].tolist(),
                "title": "Avg Engagement Score by City",
            }

        return {"error": f"Unknown chart_type: {chart_type}"}
    except Exception as e:
        log.error(f"[Tool Error] get_chart_data: {e}")
        return {"error": str(e)}
