from __future__ import annotations

import re
import concurrent.futures
import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer": "https://www.ownerclan.com/V2/product/search.php",
}
_BASE_URL = "https://www.ownerclan.com"
_TIMEOUT = 12
_MAX_WORKERS = 5


def search_products(keyword: str, max_results: int = 5) -> list[dict]:
    """
    오너클랜에서 키워드로 상품 검색.
    반환: [{"selfcode", "name", "image_url", "product_url"}]
    """
    selfcodes = _get_selfcodes(keyword, max_results)
    if not selfcodes:
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        future_to_code = {
            executor.submit(_fetch_product_info, code): code
            for code in selfcodes
        }
        fetched: dict[str, dict] = {}
        for future in concurrent.futures.as_completed(future_to_code):
            code = future_to_code[future]
            result = future.result()
            if result:
                fetched[code] = result

    # getSelfcodes 랭킹 순서 유지
    return [fetched[code] for code in selfcodes if code in fetched]


def _get_selfcodes(keyword: str, max_results: int) -> list[str]:
    """getSelfcodes.php 로 상품코드 목록 조회 (reCAPTCHA 불필요)."""
    try:
        resp = requests.post(
            f"{_BASE_URL}/V2/_ajax/getSelfcodes.php",
            headers=_HEADERS,
            data={
                "searchKeyword": keyword,
                "searchType": "all",
                "pageNum": "1",
                "listNum": str(max_results),
                "rankType": "rankUp",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        codes = resp.json()
        return codes[:max_results] if isinstance(codes, list) else []
    except Exception:
        return []


def _fetch_product_info(selfcode: str) -> dict | None:
    """view.php 에서 상품명·이미지 추출."""
    product_url = f"{_BASE_URL}/V2/product/view.php?selfcode={selfcode}"
    try:
        resp = requests.get(product_url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        html = resp.text

        # og:title ("오너클랜 - 상품명" 형태)
        m_title = re.search(r'property="og:title"\s+content="([^"]+)"', html)
        name = m_title.group(1) if m_title else selfcode
        name = re.sub(r'^오너클랜\s*[-–]\s*', '', name).strip()

        # og:image (content= 가 다음 줄에 위치)
        m_img = re.search(
            r'property="og:image"[^>]*>\s*<[^>]+content="(https://[^"]+)"',
            html, re.DOTALL,
        )
        if not m_img:
            m_img = re.search(
                r'property="og:image"\s+content="(https://[^"]+)"',
                html, re.DOTALL,
            )
        image_url = m_img.group(1) if m_img else ""

        return {
            "selfcode": selfcode,
            "name": name,
            "image_url": image_url,
            "product_url": product_url,
        }
    except Exception:
        return None
