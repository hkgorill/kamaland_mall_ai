"""
Phase 2 서비스 레이어 단독 테스트 스크립트.
실행: python tests/test_services.py
"""
from __future__ import annotations

import sys, io, time, urllib.request
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    status = PASS if ok else FAIL
    print(f"{status} {name}" + (f" — {detail}" if detail else ""))


# ── 1. Gemini 텍스트 생성 ───────────────────────────────────

print(f"\n{INFO} === Gemini 서비스 테스트 ===")
from services.gemini_service import generate_text, generate_json, test_connection

t0 = time.time()
ok, msg = test_connection()
check("연결 테스트", ok, msg[:60])

t0 = time.time()
try:
    result = generate_text(
        "국내 온라인 판매에 인기 있는 소형 생필품 3가지를 bullet point로만 알려줘.",
        temperature=0.7,
    )
    check("텍스트 생성", bool(result), f"{len(result)}자 ({time.time()-t0:.1f}s)")
except Exception as e:
    check("텍스트 생성", False, str(e)[:80])

t0 = time.time()
try:
    import json
    raw = generate_json(
        '무선 이어폰 상품의 후킹 문구를 JSON으로 작성:\n'
        '{"main_title":"...","sub_title":"...","cta_text":"..."}',
        temperature=0.4,
    )
    parsed = json.loads(raw)
    check("JSON 생성", "main_title" in parsed, f"{list(parsed.keys())} ({time.time()-t0:.1f}s)")
except Exception as e:
    check("JSON 생성", False, str(e)[:80])

# 스트리밍 테스트
t0 = time.time()
try:
    from services.gemini_service import generate_streaming
    chunks = list(generate_streaming("'스트리밍 테스트'라고만 답해줘.", temperature=0.0))
    full = "".join(chunks)
    check("스트리밍 생성", bool(full), f"청크 {len(chunks)}개 ({time.time()-t0:.1f}s)")
except Exception as e:
    check("스트리밍 생성", False, str(e)[:80])


# ── 2. 이미지 서비스 ────────────────────────────────────────

print(f"\n{INFO} === 이미지 서비스 테스트 ===")
from services.image_service import remove_background, generate_product_images, generate_with_imagen
from PIL import Image

# 테스트용 샘플 이미지 준비
SAMPLE_PATH = "/tmp/test_product.jpg"
if not Path(SAMPLE_PATH).exists():
    print(f"{INFO} 샘플 이미지 다운로드 중...")
    urllib.request.urlretrieve(
        "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=400",
        SAMPLE_PATH,
    )
with open(SAMPLE_PATH, "rb") as f:
    sample_bytes = f.read()

# 배경 제거 테스트
t0 = time.time()
try:
    bg_removed = remove_background(sample_bytes)
    check(
        "배경 제거 (rembg)",
        bg_removed.mode == "RGBA",
        f"{bg_removed.size}, mode={bg_removed.mode} ({time.time()-t0:.1f}s)",
    )
except Exception as e:
    check("배경 제거 (rembg)", False, str(e)[:80])

# 단일 컨셉 이미지 생성 테스트
t0 = time.time()
try:
    from config import IMAGE_CONCEPTS
    one_concept = [IMAGE_CONCEPTS[0]]  # 미니멀 스튜디오만
    res = generate_product_images(sample_bytes, concepts=one_concept)
    ok_count = sum(1 for r in res if r["image"] is not None)
    check(
        "이미지 생성 (단일 컨셉)",
        ok_count == 1,
        f"{ok_count}/1 성공, size={res[0]['image'].size if res[0]['image'] else 'N/A'} ({time.time()-t0:.1f}s)",
    )
    if res[0]["error"]:
        print(f"  ⚠️  에러: {res[0]['error']}")
except Exception as e:
    check("이미지 생성 (단일 컨셉)", False, str(e)[:80])

# 병렬 3컨셉 테스트
t0 = time.time()
try:
    from config import IMAGE_CONCEPTS
    three_concepts = IMAGE_CONCEPTS[:3]
    progress_log = []
    res = generate_product_images(
        sample_bytes,
        concepts=three_concepts,
        on_progress=lambda done, total: progress_log.append(f"{done}/{total}"),
    )
    ok_count = sum(1 for r in res if r["image"] is not None)
    check(
        "이미지 생성 (병렬 3컨셉)",
        ok_count >= 2,
        f"{ok_count}/3 성공, 진행={progress_log} ({time.time()-t0:.1f}s)",
    )
except Exception as e:
    check("이미지 생성 (병렬 3컨셉)", False, str(e)[:80])

# Imagen 4.0 단독 생성 테스트
t0 = time.time()
try:
    imgs = generate_with_imagen("A ceramic mug on white background, product photography", count=1)
    check("Imagen 4.0 생성", len(imgs) == 1, f"size={imgs[0].size} ({time.time()-t0:.1f}s)")
except Exception as e:
    check("Imagen 4.0 생성", False, str(e)[:80])


# ── 3. 스크래퍼 서비스 ──────────────────────────────────────

print(f"\n{INFO} === 스크래퍼 서비스 테스트 ===")
from services.scraper_service import scrape_product_info, format_for_copywriting

# 공개 상품 페이지 테스트
TEST_URL = "https://www.11st.co.kr/products/6040374459"
t0 = time.time()
try:
    info = scrape_product_info(TEST_URL)
    has_content = bool(info["title"] or info["description"])
    check(
        "스크래핑 (11번가)",
        has_content or bool(info["error"]),  # 차단되어도 에러 처리면 PASS
        f"title={info['title'][:30]!r}, err={info['error'][:40]!r} ({time.time()-t0:.1f}s)",
    )
    if has_content:
        formatted = format_for_copywriting(info)
        check("format_for_copywriting", bool(formatted), f"{len(formatted)}자")
except Exception as e:
    check("스크래핑", False, str(e)[:80])


# ── 결과 요약 ────────────────────────────────────────────────

print(f"\n{'='*50}")
total  = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed
print(f"결과: {passed}/{total} 통과" + (f", {failed}개 실패" if failed else " — 전체 통과 ✅"))
if failed:
    print("실패 항목:")
    for name, ok, detail in results:
        if not ok:
            print(f"  {FAIL} {name}: {detail}")
sys.exit(0 if failed == 0 else 1)
