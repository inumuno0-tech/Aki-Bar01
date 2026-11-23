"""Open Library 書目搜尋服務。"""
from .common import UpstreamError, get_json

SEARCH_URL = "https://openlibrary.org/search.json"
UNWANTED_TITLE = "araki - tokyo lucky hole"
LIGHT_NOVEL_QUERY = "The Devil Is a Part-Timer!"


class BookError(Exception):
    pass


def _to_book(item, *, recommendation=None):
    """將 Open Library 書目轉成模板可直接使用的欄位。"""
    cover_id = item.get("cover_i")
    book = {
        "title": item.get("title") or "未提供書名",
        "authors": item.get("author_name", [])[:3],
        "year": item.get("first_publish_year"),
        "subjects": item.get("subject", [])[:3],
        "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None,
        "url": "https://openlibrary.org" + item.get("key", ""),
    }
    if recommendation:
        book["recommendation"] = recommendation
    return book


def _light_novel_replacement():
    """從 Open Library 找一筆輕小說候選，失敗時不影響主要搜尋結果。"""
    try:
        data = get_json(SEARCH_URL,
                        params={"q": LIGHT_NOVEL_QUERY, "limit": 5},
                        cache_seconds=1800)
    except UpstreamError:
        return None

    for item in data.get("docs", []):
        authors = item.get("author_name", [])
        title = (item.get("title") or "").casefold()
        if "satoshi wagahara" in [author.casefold() for author in authors] and "devil" in title:
            return _to_book(item, recommendation="輕小說推薦")
    return None


def search_books(query):
    try:
        data = get_json(SEARCH_URL,
                        params={"q": query, "limit": 9}, cache_seconds=1800)
    except UpstreamError as exc:
        if "HTTP 422" in str(exc):
            raise BookError("Open Library 暫時無法接受這個關鍵字，請改用英文城市名或較簡短的旅遊主題。") from exc
        raise BookError(str(exc)) from exc
    books = []
    removed_unwanted_book = False
    for item in data.get("docs", []):
        # 這本書不適合作為旅遊閱讀推薦，因此從各種搜尋結果排除。
        title = (item.get("title") or "").casefold()
        if UNWANTED_TITLE in title:
            removed_unwanted_book = True
            continue
        books.append(_to_book(item))

    # 只在原結果真的含有被排除書籍時，補一筆輕小說推薦。
    if removed_unwanted_book:
        replacement = _light_novel_replacement()
        if replacement:
            books.append(replacement)
    return {"query": query, "books": books}
