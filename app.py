"""
Flask application: Netflix Movie & TV Show Data Analytics
Serves a dashboard with seaborn-generated charts, supports CSV upload,
and provides individual downloadable chart endpoints.
"""
import os
from flask import (
    Flask, render_template, send_file, request, redirect,
    url_for, flash, session, abort
)
from werkzeug.utils import secure_filename
import io

import analytics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(BASE_DIR, "data", "netflix_titles.csv")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"csv"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_active_csv_path() -> str:
    """Returns the path to the currently active dataset (uploaded or default)."""
    uploaded = session.get("active_csv")
    if uploaded and os.path.exists(uploaded):
        return uploaded
    return DEFAULT_CSV


@app.route("/")
def index():
    csv_path = get_active_csv_path()
    df = analytics.load_data(csv_path)
    stats = analytics.summary_stats(df)
    charts = [
        {"key": key, "title": title}
        for key, (title, _fn) in analytics.CHART_REGISTRY.items()
    ]
    using_upload = session.get("active_csv") is not None
    return render_template(
        "index.html",
        stats=stats,
        charts=charts,
        using_upload=using_upload,
        sample=df.head(10).to_dict(orient="records"),
        columns=list(df.columns),
    )


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("dataset")
    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))
    if not allowed_file(file.filename):
        flash("Please upload a .csv file.", "error")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    # Validate that it can actually be loaded and has expected-ish columns
    try:
        df = analytics.load_data(save_path)
        required = {"type", "release_year", "listed_in", "country", "rating", "duration"}
        missing = required - set(df.columns)
        if missing:
            flash(f"CSV is missing required columns: {', '.join(missing)}", "error")
            os.remove(save_path)
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"Could not parse CSV: {e}", "error")
        return redirect(url_for("index"))

    session["active_csv"] = save_path
    flash("Dataset uploaded and active! Charts below now reflect your data.", "success")
    return redirect(url_for("index"))


@app.route("/reset")
def reset():
    session.pop("active_csv", None)
    flash("Reverted to the sample dataset.", "success")
    return redirect(url_for("index"))


@app.route("/chart/<chart_key>.png")
def chart_png(chart_key):
    if chart_key not in analytics.CHART_REGISTRY:
        abort(404)
    csv_path = get_active_csv_path()
    df = analytics.load_data(csv_path)
    _title, chart_fn = analytics.CHART_REGISTRY[chart_key]
    png_bytes = chart_fn(df)
    return send_file(io.BytesIO(png_bytes), mimetype="image/png")


@app.route("/download/<chart_key>")
def download_chart(chart_key):
    if chart_key not in analytics.CHART_REGISTRY:
        abort(404)
    csv_path = get_active_csv_path()
    df = analytics.load_data(csv_path)
    _title, chart_fn = analytics.CHART_REGISTRY[chart_key]
    png_bytes = chart_fn(df)
    return send_file(
        io.BytesIO(png_bytes),
        mimetype="image/png",
        as_attachment=True,
        download_name=f"netflix_{chart_key}.png",
    )


@app.route("/download-data")
def download_data():
    csv_path = get_active_csv_path()
    return send_file(csv_path, as_attachment=True, download_name="netflix_titles.csv")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
