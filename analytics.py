"""
analytics.py
Loads the Netflix dataset and produces seaborn/matplotlib charts as PNG bytes.
Keeps chart-generation logic separate from Flask routing.
"""
import io
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless backend, required for server-side rendering
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="darkgrid")

NETFLIX_RED = "#E50914"
PALETTE = "rocket"


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
    df["year_added"] = df["date_added"].dt.year
    df["primary_genre"] = df["listed_in"].str.split(",").str[0].str.strip()
    return df


def summary_stats(df: pd.DataFrame) -> dict:
    return {
        "total_titles": int(len(df)),
        "movies": int((df["type"] == "Movie").sum()),
        "tv_shows": int((df["type"] == "TV Show").sum()),
        "countries": int(df["country"].nunique()),
        "genres": int(df["primary_genre"].nunique()),
        "year_min": int(df["release_year"].min()),
        "year_max": int(df["release_year"].max()),
        "top_genre": df["primary_genre"].value_counts().idxmax(),
        "top_country": df["country"].value_counts().idxmax(),
        "top_rating": df["rating"].value_counts().idxmax(),
    }


def _fig_to_png_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def chart_type_distribution(df: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 5))
    counts = df["type"].value_counts()
    sns.barplot(x=counts.index, y=counts.values, hue=counts.index,
                palette=[NETFLIX_RED, "#221f1f"], legend=False, ax=ax)
    ax.set_title("Movies vs TV Shows", fontsize=14, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Count")
    for i, v in enumerate(counts.values):
        ax.text(i, v + 5, str(v), ha="center", fontweight="bold")
    return _fig_to_png_bytes(fig)


def chart_top_genres(df: pd.DataFrame, top_n: int = 10) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 6))
    counts = df["primary_genre"].value_counts().head(top_n)
    sns.barplot(x=counts.values, y=counts.index, hue=counts.index,
                palette=PALETTE, legend=False, ax=ax)
    ax.set_title(f"Top {top_n} Genres", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Titles")
    ax.set_ylabel("")
    return _fig_to_png_bytes(fig)


def chart_releases_over_time(df: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 5))
    yearly = df.groupby(["release_year", "type"]).size().reset_index(name="count")
    sns.lineplot(data=yearly, x="release_year", y="count", hue="type",
                 marker="o", palette=[NETFLIX_RED, "#221f1f"], ax=ax)
    ax.set_title("Titles Released by Year", fontsize=14, fontweight="bold")
    ax.set_xlabel("Release Year")
    ax.set_ylabel("Number of Titles")
    ax.legend(title="")
    return _fig_to_png_bytes(fig)


def chart_rating_distribution(df: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 5))
    order = df["rating"].value_counts().index
    sns.countplot(data=df, y="rating", order=order, hue="rating",
                  palette=PALETTE, legend=False, ax=ax)
    ax.set_title("Content Rating Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Count")
    ax.set_ylabel("Rating")
    return _fig_to_png_bytes(fig)


def chart_top_countries(df: pd.DataFrame, top_n: int = 10) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 6))
    counts = df["country"].value_counts().head(top_n)
    sns.barplot(x=counts.values, y=counts.index, hue=counts.index,
                palette=PALETTE, legend=False, ax=ax)
    ax.set_title(f"Top {top_n} Content-Producing Countries", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Titles")
    ax.set_ylabel("")
    return _fig_to_png_bytes(fig)


def chart_movie_duration_hist(df: pd.DataFrame) -> bytes:
    movies = df[df["type"] == "Movie"].copy()
    movies["duration_min"] = movies["duration"].str.extract(r"(\d+)").astype(float)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(movies["duration_min"].dropna(), bins=25, kde=True,
                 color=NETFLIX_RED, ax=ax)
    ax.set_title("Movie Duration Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Number of Movies")
    return _fig_to_png_bytes(fig)


def chart_additions_by_year(df: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 5))
    yearly = df.dropna(subset=["year_added"]).groupby("year_added").size()
    yearly = yearly[yearly.index >= 2013]
    sns.barplot(x=yearly.index.astype(int), y=yearly.values, hue=yearly.index,
                palette=PALETTE, legend=False, ax=ax)
    ax.set_title("Titles Added to Netflix by Year", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year Added")
    ax.set_ylabel("Number of Titles")
    plt.xticks(rotation=45)
    return _fig_to_png_bytes(fig)


def chart_heatmap_genre_rating(df: pd.DataFrame, top_n_genres: int = 8) -> bytes:
    top_genres = df["primary_genre"].value_counts().head(top_n_genres).index
    sub = df[df["primary_genre"].isin(top_genres)]
    pivot = pd.crosstab(sub["primary_genre"], sub["rating"])
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, cmap="rocket_r", annot=True, fmt="d", linewidths=0.5, ax=ax)
    ax.set_title("Genre vs Rating Heatmap", fontsize=14, fontweight="bold")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Genre")
    return _fig_to_png_bytes(fig)


CHART_REGISTRY = {
    "type_distribution": ("Movies vs TV Shows", chart_type_distribution),
    "top_genres": ("Top Genres", chart_top_genres),
    "releases_over_time": ("Releases Over Time", chart_releases_over_time),
    "rating_distribution": ("Rating Distribution", chart_rating_distribution),
    "top_countries": ("Top Countries", chart_top_countries),
    "movie_duration": ("Movie Duration Histogram", chart_movie_duration_hist),
    "additions_by_year": ("Titles Added by Year", chart_additions_by_year),
    "genre_rating_heatmap": ("Genre vs Rating Heatmap", chart_heatmap_genre_rating),
}
