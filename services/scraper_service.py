from __future__ import annotations

import re
import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_TIMEOUT = 12


# ── 공개 인터페이스 ──────────────────────────────────────────

def scrape_product_info(url: str) -> dict:
    """
    URL에서 상품 정보 추출.
    반환: {"title": str, "description": str, "features": list[str], "error": str}
    """
    result = {"title": "", "description": "", "features": [], "error": ""}
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 쇼핑몰별 전용 파서 우선 시도
        if "smartstore.naver.com" in url:
            parsed = _parse_naver(soup)
        elif "coupang.com" in url:
            parsed = _parse_coupang(soup)
        else:
            parsed = _parse_generic(soup)

        result.update(parsed)

    except requests.exceptions.Timeout:
        result["error"] = "요청 시간이 초과되었습니다."
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 403:
            result["error"] = f"접근이 차단되었습니다 (403). 상품 정보를 직접 입력해주세요."
        else:
            result["error"] = f"HTTP 오류: {code}"
    except Exception as e:
        result["error"] = f"스크래핑 실패: {str(e)[:100]}"

    return result


def format_for_copywriting(scraped: dict) -> str:
    """스크래핑 결과를 카피라이팅 입력 텍스트로 변환."""
    parts = []
    if scraped.get("title"):
        parts.append(f"상품명: {scraped['title']}")
    if scraped.get("description"):
        parts.append(f"설명: {scraped['description']}")
    if scraped.get("features"):
        parts.append("특징:\n" + "\n".join(f"- {f}" for f in scraped["features"][:6]))
    return "\n\n".join(parts)


# ── 내부 파서 ────────────────────────────────────────────────

def _parse_naver(soup: BeautifulSoup) -> dict:
    """네이버 스마트스토어 전용 파서."""
    title = _og_content(soup, "og:title") or _tag_text(soup, "title")
    desc  = _og_content(soup, "og:description")

    # 상품 특징 추출 (li 태그 내 짧은 문장들)
    features = _extract_list_items(soup, max_items=8)

    # 상품명에서 스토어명 제거 (예: "스토어명 : 상품명" → "상품명")
    if ":" in title:
        title = title.split(":", 1)[-1].strip()

    return {"title": _clean(title), "description": _clean(desc), "features": features}


def _parse_coupang(soup: BeautifulSoup) -> dict:
    """쿠팡 전용 파서."""
    title = _og_content(soup, "og:title") or ""
    desc  = _og_content(soup, "og:description") or ""

    # 쿠팡은 상품명 h2 태그에 있는 경우 많음
    if not title:
        h2 = soup.find("h2", class_=re.compile(r"product.*name|name.*product", re.I))
        if h2:
            title = h2.get_text(strip=True)

    features = _extract_list_items(soup, max_items=8)
    return {"title": _clean(title), "description": _clean(desc), "features": features}


def _parse_generic(soup: BeautifulSoup) -> dict:
    """범용 파서 (og 태그 → title 태그 → 본문 순 fallback)."""
    title = _og_content(soup, "og:title") or _tag_text(soup, "title") or ""
    desc  = _og_content(soup, "og:description") or ""

    if not desc:
        # 본문에서 의미 있는 단락 추출
        for tag in soup.find_all(["p", "li", "div"], limit=30):
            text = tag.get_text(strip=True)
            if 30 < len(text) < 500 and not _is_boilerplate(text):
                desc = text
                break

    features = _extract_list_items(soup, max_items=6)
    return {"title": _clean(title), "description": _clean(desc), "features": features}


# ── 유틸 ─────────────────────────────────────────────────────

def _og_content(soup: BeautifulSoup, property_name: str) -> str:
    tag = soup.find("meta", property=property_name)
    if tag and tag.get("content"):
        return tag["content"]
    return ""


def _tag_text(soup: BeautifulSoup, tag_name: str) -> str:
    tag = soup.find(tag_name)
    return tag.get_text(strip=True) if tag else ""


def _extract_list_items(soup: BeautifulSoup, max_items: int = 6) -> list[str]:
    """li 태그에서 짧고 의미 있는 항목 추출."""
    items = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if 5 < len(text) < 100 and not _is_boilerplate(text):
            items.append(_clean(text))
            if len(items) >= max_items:
                break
    return items


_BOILERPLATE_KEYWORDS = {
    "로그인", "회원가입", "장바구니", "cookie", "javascript",
    "copyright", "privacy", "terms", "sns", "공유", "팔로우",
}

def _is_boilerplate(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _BOILERPLATE_KEYWORDS)


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()
