import os
import glob
import subprocess
from flask import Flask, send_file, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(BASE_DIR, "demo_data", "expenses.csv")


def latest_report():
    reports = sorted(glob.glob(os.path.join(OUTPUT_DIR, "rapport-depenses-*.html")))
    return reports[-1] if reports else None


@app.route("/")
def index():
    report = latest_report()
    if report:
        return redirect(url_for("report"))
    return """
    <html><body style="font-family:system-ui;padding:40px;background:#f9fafb">
    <h2>Aucun rapport disponible</h2>
    <form method="post" action="/generate">
      <button type="submit" style="padding:10px 20px;background:#3b82f6;color:white;border:none;border-radius:6px;cursor:pointer;font-size:15px">
        Générer le rapport
      </button>
    </form>
    </body></html>
    """


@app.route("/report")
def report():
    path = latest_report()
    if not path:
        return redirect(url_for("index"))
    return send_file(path)


@app.route("/generate", methods=["POST"])
def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    subprocess.run(
        ["uv", "run", "python", "analyze.py", CSV_PATH, OUTPUT_DIR],
        cwd=BASE_DIR,
        capture_output=True,
    )
    return redirect(url_for("report"))


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5051))
    app.run(host=host, port=port, debug=False)
