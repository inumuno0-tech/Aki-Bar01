"""Open Library 書目搜尋服務。"""
from .common import UpstreamError, get_json


class BookError(Exception):
    pass


def search_books(query):
    try:
        data = get_json("https://openlibrary.org/search.json",
                        params={"q": query, "limit": 9}, cache_seconds=1800)
    except UpstreamError as exc:
        if "HTTP 422" in str(exc):
            raise BookError("Open Library 暫時無法接受這個關鍵字，請改用英文城市名或較簡短的旅遊主題。") from exc
        raise BookError(str(exc)) from exc
    books = []
    for item in data.get("docs", []):
        cover_id = item.get("cover_i")
        books.append({
            "title": item.get("title") or "未提供書名",
            "authors": item.get("author_name", [])[:3],
            "year": item.get("first_publish_year"),
            "subjects": item.get("subject", [])[:3],
            "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None,
            "url": "https://openlibrary.org" + item.get("key", ""),
        })
    return {"query": query, "books": books}
