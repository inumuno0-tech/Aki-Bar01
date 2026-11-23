"""WanderDesk Flask 應用程式與 Vercel Serverless 進入點。"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, render_template, request, send_from_directory
from services.book_service import BookError, search_books
from services.currency_service import CURRENCY_URL, POPULAR, CurrencyError, convert_currency, get_currencies
from services.weather_service import WeatherError, get_weather, search_places

app = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


@app.get("/style.css")
def stylesheet():
    """本機 Flask 開發時提供 CSS；Vercel Production 由 public/ CDN 提供。"""
    return send_from_directory(str(ROOT / "public"), "style.css")


@app.get("/")
def index():
    """首頁提供伺服器渲染表單與預設探索城市。"""
    currencies = get_currencies()
    return render_template("index.html", result=None, active="", currencies=currencies,
                           popular=POPULAR, city="", places=[], weather=None, books=None)


@app.post("/explore")
def explore():
    """同一表單流程可查天氣或書籍，錯誤以繁中友善訊息呈現。"""
    action = request.form.get("action", "").strip()
    city = request.form.get("city", "").strip()
    result = None
    error = None
    places = []
    weather = None
    books = None
    book_query = request.form.get("book_query", "").strip()
    try:
        if action == "weather":
            if not city or len(city) > 100:
                raise WeatherError("請輸入 1 至 100 個字元的城市名稱。")
            places = search_places(city)
            if not places:
                raise WeatherError("找不到這個城市，請試試英文名稱或其他拼法。")
            selected = request.form.get("place_index", "0")
            try:
                place = places[int(selected)]
            except (ValueError, IndexError):
                place = places[0]
            weather = get_weather(place=place)
            book_query = book_query or place.get("name", city)
            books = search_books(book_query)
        elif action == "books":
            if not book_query or len(book_query) > 120:
                raise BookError("請輸入 1 至 120 個字元的書籍或旅遊關鍵字。")
            books = search_books(book_query)
        else:
            error = "請從城市搜尋或書籍搜尋開始探索。"
    except (WeatherError, BookError) as exc:
        error = str(exc)
    return render_template("index.html", result=result, active=action, currencies=get_currencies(),
                           popular=POPULAR, city=city, places=places, weather=weather,
                           books=books, book_query=book_query, error=error)


@app.get("/api/currencies")
def currencies_api():
    """提供幣別代碼清單；失敗時服務層會回傳常見幣別。"""
    return jsonify({"currencies": get_currencies(), "source": CURRENCY_URL})


@app.get("/api/convert")
def convert_api():
    """非同步匯率換算端點，JSON 格式回傳結果或友善錯誤。"""
    try:
        data = convert_currency(request.args.get("amount", ""),
                                request.args.get("from", "TWD").upper(),
                                request.args.get("to", "JPY").upper())
        return jsonify({key: str(value) for key, value in data.items()})
    except CurrencyError as exc:
        return jsonify({"error": str(exc)}), 400


@app.errorhandler(413)
def too_large(_error):
    return render_template("index.html", result=None, active="", currencies=POPULAR,
                           popular=POPULAR, city="", places=[], weather=None, books=None,
                           error="提交的內容太長，請縮短後再試。"), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
