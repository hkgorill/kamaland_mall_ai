"""
E2E 통합 테스트: 소싱 → 이미지 → 카피라이팅 → 상세페이지 전체 흐름 검증
실행: python tests/test_e2e.py
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    s = PASS if ok else FAIL
    print(f"{s} {name}" + (f"  —  {detail}" if detail else ""))


# ── 공통 데이터 준비 ───────────────────────────────────────────

SAMPLE_PATH = "/tmp/e2e_product.jpg"

def _make_test_image() -> bytes:
    """외부 의존 없이 테스트용 상품 이미지 생성."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (400, 400), color=(230, 220, 210))
    draw = ImageDraw.Draw(img)
    # 단순한 상품 형태 그리기 (머그컵 모양)
    draw.rectangle([120, 100, 280, 280], fill=(240, 240, 230), outline=(180, 160, 140), width=3)
    draw.rectangle([280, 160, 310, 220], fill=(240, 240, 230), outline=(180, 160, 140), width=3)
    draw.ellipse([130, 95, 270, 130], fill=(200, 185, 170))
    draw.text((160, 175), "PRODUCT", fill=(150, 130, 110))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

if not Path(SAMPLE_PATH).exists():
    data = _make_test_image()
    Path(SAMPLE_PATH).write_bytes(data)
    print(f"{INFO} 테스트 이미지 생성: {len(data)//1024}KB")
else:
    data = Path(SAMPLE_PATH).read_bytes()

SAMPLE_BYTES = _make_test_image()  # 항상 신선한 이미지 사용
print(f"{INFO} 테스트 이미지: {len(SAMPLE_BYTES)//1024}KB (로컬 생성)")


# ── STEP 1: 소싱 키워드 추출 ──────────────────────────────────

print(f"\n{INFO} ═══ STEP 1: 소싱 키워드 추출 ═══")

from services.gemini_service import generate_text
from views.sourcing import _parse_keywords
from config import SOURCING_SYSTEM_PROMPT

t0 = time.time()
try:
    prompt = (
        "국내 온라인 위탁 판매에 최적화된 소형/생필품 키워드 3개를 추천해주세요.\n"
        "각 키워드는 반드시 아래 형식으로:\n"
        "- **[키워드]**: [판매 포인트] | 타겟: [주요 구매층]"
    )
    raw = generate_text(prompt, system_prompt=SOURCING_SYSTEM_PROMPT, temperature=0.7)
    parsed = _parse_keywords(raw)
    check("키워드 추출", len(parsed) >= 1, f"{len(parsed)}개 ({time.time()-t0:.1f}s)")
    if parsed:
        check("키워드 파싱 구조", all("keyword" in k for k in parsed),
              f"예: {parsed[0]['keyword']}")
except Exception as e:
    check("키워드 추출", False, str(e)[:80])
    parsed = [{"keyword": "무선 이어폰", "selling_point": "고음질", "target": "직장인"}]

SELECTED_KEYWORDS = parsed[:2]


# ── STEP 2: 카피라이팅 생성 ───────────────────────────────────

print(f"\n{INFO} ═══ STEP 2: 카피라이팅 생성 ═══")

from services.gemini_service import generate_json
from config import COPYWRITING_SYSTEM_PROMPT

product_info = "\n".join(
    f"- **{k['keyword']}**: {k.get('selling_point', '')}" for k in SELECTED_KEYWORDS
)

t0 = time.time()
COPY_RESULT: dict = {}
try:
    output_fmt = """
JSON 형식으로만 응답:
{
  "main_title": "메인 타이틀 (20자 이내)",
  "sub_title": "서브 타이틀 (40자 이내)",
  "key_points": [
    {"icon": "이모지", "headline": "소구점1", "description": "설명1"},
    {"icon": "이모지", "headline": "소구점2", "description": "설명2"},
    {"icon": "이모지", "headline": "소구점3", "description": "설명3"}
  ],
  "cta_text": "CTA 문구"
}"""
    raw_json = generate_json(
        f"상품 정보:\n{product_info}\n\n{output_fmt}",
        system_prompt=COPYWRITING_SYSTEM_PROMPT,
    )
    COPY_RESULT = json.loads(raw_json)
    has_all = all(k in COPY_RESULT for k in ["main_title", "sub_title", "key_points", "cta_text"])
    check("카피라이팅 생성", has_all, f"타이틀: {COPY_RESULT.get('main_title','')[:20]} ({time.time()-t0:.1f}s)")
    check("소구점 3개", len(COPY_RESULT.get("key_points", [])) == 3,
          f"{len(COPY_RESULT.get('key_points', []))}개")
except json.JSONDecodeError as e:
    check("카피라이팅 생성", False, f"JSON 파싱 실패: {e}")
except Exception as e:
    check("카피라이팅 생성", False, str(e)[:80])

if not COPY_RESULT:
    COPY_RESULT = {
        "main_title": "테스트 타이틀", "sub_title": "서브",
        "key_points": [{"icon": "✅", "headline": "P1", "description": "D1"}],
        "cta_text": "구매하기",
    }


# ── STEP 3: 이미지 생성 (1컨셉만 테스트) ─────────────────────

print(f"\n{INFO} ═══ STEP 3: 이미지 생성 (단일 컨셉) ═══")

from services.image_service import generate_product_images
from config import IMAGE_CONCEPTS

t0 = time.time()
GENERATED_IMGS: list[dict] = []
try:
    results_img = generate_product_images(SAMPLE_BYTES, concepts=[IMAGE_CONCEPTS[0]])
    ok = sum(1 for r in results_img if r["image"] is not None)
    check("이미지 생성 (1컨셉)", ok >= 1,
          f"{ok}/1 성공, size={results_img[0]['image'].size if results_img[0]['image'] else 'N/A'} ({time.time()-t0:.1f}s)")
    GENERATED_IMGS = results_img
except Exception as e:
    check("이미지 생성 (1컨셉)", False, str(e)[:80])


# ── STEP 4: HTML 상세페이지 빌드 ──────────────────────────────

print(f"\n{INFO} ═══ STEP 4: HTML 상세페이지 빌드 ═══")

from utils.html_template import build_detail_page_html

hero_img = GENERATED_IMGS[0]["image"] if GENERATED_IMGS and GENERATED_IMGS[0]["image"] else None

try:
    html = build_detail_page_html(
        main_title=COPY_RESULT["main_title"],
        sub_title=COPY_RESULT["sub_title"],
        key_points=COPY_RESULT["key_points"],
        cta_text=COPY_RESULT["cta_text"],
        hero_image=hero_img,
    )
    has_content = (
        COPY_RESULT["main_title"] in html
        and COPY_RESULT["cta_text"] in html
        and "<html" in html
        and len(html) > 1000
    )
    check("HTML 빌드", has_content, f"{len(html):,}자")
    check("이미지 포함 여부", ("base64" in html) == (hero_img is not None),
          "hero image " + ("포함" if hero_img else "없음 (정상)"))
except Exception as e:
    check("HTML 빌드", False, str(e)[:80])
    html = ""


# ── STEP 5: 파일 저장 ─────────────────────────────────────────

print(f"\n{INFO} ═══ STEP 5: 파일 저장 ═══")

import datetime
from pathlib import Path

PAGES_DIR  = Path("outputs/pages")
IMAGES_DIR = Path("outputs/images")

# HTML 저장
if html:
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = PAGES_DIR / f"e2e_test_{ts}.html"
    try:
        path.write_text(html, encoding="utf-8")
        check("HTML 파일 저장", path.exists(), str(path.name))
    except Exception as e:
        check("HTML 파일 저장", False, str(e)[:60])
else:
    print(f"{SKIP} HTML 파일 저장  —  HTML 빌드 실패로 건너뜀")

# 이미지 저장 확인 (image_service 가 자동 저장)
img_files = list(IMAGES_DIR.glob("*.png"))
check("이미지 파일 자동 저장", len(img_files) >= 1,
      f"{len(img_files)}개 파일 존재")


# ── STEP 6: 세션 상태 키 검증 ─────────────────────────────────

print(f"\n{INFO} ═══ STEP 6: 세션 키 검증 ═══")

from utils.session import DEFAULTS

REQUIRED_KEYS = [
    "sourcing_keywords", "sourcing_done",
    "uploaded_image_bytes", "generated_images", "images_done",
    "product_info", "copy_result", "copy_done",
    "detail_html", "detail_done",
]
missing = [k for k in REQUIRED_KEYS if k not in DEFAULTS]
check("세션 키 완전성", len(missing) == 0,
      f"누락: {missing}" if missing else f"{len(REQUIRED_KEYS)}개 모두 존재")


# ── 결과 요약 ──────────────────────────────────────────────────

print(f"\n{'═'*55}")
total  = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"E2E 결과: {passed}/{total} 통과" + (f", {failed}개 실패" if failed else " — 전체 통과 ✅"))
if failed:
    print("실패 항목:")
    for name, ok, detail in results:
        if not ok:
            print(f"  {FAIL} {name}: {detail}")

sys.exit(0 if failed == 0 else 1)
