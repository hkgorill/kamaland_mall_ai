from __future__ import annotations

import io
import time
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from google import genai
from google.genai import types
from config import (
    GOOGLE_API_KEY,
    GEMINI_IMAGE_MODEL,
    IMAGEN_MODEL,
    IMAGE_CONCEPTS,
    IMAGE_GEN_MAX_WORKERS,
)

_OUTPUTS_DIR = Path(__file__).parent.parent / "outputs" / "images"
_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

_MAX_IMAGE_SIZE = 1536  # 긴 변 기준 픽셀 (API 전송 최적화)
_RETRY_DELAY = 3.0

# 모듈 레벨 싱글톤
_genai_client: genai.Client | None = None
_rembg_session = None


def _get_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(api_key=GOOGLE_API_KEY)
    return _genai_client


def _get_rembg_session():
    global _rembg_session
    if _rembg_session is None:
        from rembg import new_session
        _rembg_session = new_session("u2net")
    return _rembg_session


def _resize_for_api(img: Image.Image) -> Image.Image:
    """API 전송 전 이미지 크기 최적화 (긴 변 _MAX_IMAGE_SIZE 이하로)."""
    w, h = img.size
    max_side = max(w, h)
    if max_side <= _MAX_IMAGE_SIZE:
        return img
    ratio = _MAX_IMAGE_SIZE / max_side
    return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)


def remove_background(image_bytes: bytes) -> Image.Image:
    """rembg로 배경 제거 → 투명 PNG(RGBA) 반환."""
    from rembg import remove
    session = _get_rembg_session()
    result_bytes = remove(image_bytes, session=session)
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")


def _generate_one(
    image_bytes: bytes,
    concept_name: str,
    concept_prompt: str,
    attempt: int = 0,
) -> tuple[str, Image.Image | None, str]:
    """
    단일 컨셉 이미지 생성.
    반환: (concept_name, PIL.Image | None, error_msg)
    """
    client = _get_client()
    try:
        # 각 스레드가 독립적인 PIL 객체 생성 (스레드 안전)
        img = Image.open(io.BytesIO(image_bytes))
        img = _resize_for_api(img)

        prompt = (
            f"You are a professional e-commerce product photographer. "
            f"Keep the product in the image EXACTLY as it is — shape, color, and details must not change. "
            f"Replace ONLY the background with: {concept_prompt}. "
            f"The product must remain centered and clearly visible. "
            f"High resolution, sharp focus, professional lighting."
        )
        resp = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[prompt, img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        for part in resp.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                result_img = Image.open(io.BytesIO(part.inline_data.data))
                return concept_name, result_img, ""

        return concept_name, None, "이미지 응답 없음"

    except Exception as e:
        msg = str(e)
        # 429 Rate limit → 잠시 후 재시도
        if "429" in msg and attempt < 2:
            time.sleep(_RETRY_DELAY * (attempt + 1))
            return _generate_one(image_bytes, concept_name, concept_prompt, attempt + 1)
        return concept_name, None, msg[:100]


def generate_product_images(
    image_bytes: bytes,
    concepts: list[tuple[str, str]] | None = None,
    on_progress: callable | None = None,
) -> list[dict]:
    """
    5가지 컨셉 이미지 병렬 생성.

    반환: [
        {"name": str, "image": PIL.Image | None, "error": str},
        ...
    ]
    on_progress(completed: int, total: int) 콜백 지원.
    """
    if concepts is None:
        concepts = IMAGE_CONCEPTS

    total = len(concepts)
    results_map: dict[str, dict] = {}
    completed = 0

    with ThreadPoolExecutor(max_workers=IMAGE_GEN_MAX_WORKERS) as executor:
        future_to_name = {
            executor.submit(_generate_one, image_bytes, name, prompt): name
            for name, prompt in concepts
        }
        for future in as_completed(future_to_name):
            concept_name, img, error = future.result()
            results_map[concept_name] = {"name": concept_name, "image": img, "error": error}
            completed += 1
            if on_progress:
                on_progress(completed, total)

    # 원래 concepts 순서 유지
    ordered = [results_map[name] for name, _ in concepts if name in results_map]

    # 성공한 이미지 로컬 저장
    _save_outputs(ordered)

    return ordered


def _save_outputs(results: list[dict]) -> None:
    """생성된 이미지를 outputs/images/ 에 저장."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for item in results:
        if item["image"] is not None:
            safe_name = item["name"].replace(" ", "_").replace("/", "-")
            path = _OUTPUTS_DIR / f"{ts}_{safe_name}.png"
            try:
                item["image"].save(path, format="PNG")
            except Exception:
                pass  # 저장 실패는 무시 (UI 기능은 정상 동작)


def generate_with_imagen(prompt: str, count: int = 1) -> list[Image.Image]:
    """
    Imagen 4.0으로 텍스트→이미지 독립 생성.
    배경 제거 + 텍스트 프롬프트만으로 상품 이미지가 필요할 때 fallback으로 사용.
    """
    client = _get_client()
    resp = client.models.generate_images(
        model=IMAGEN_MODEL,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=count),
    )
    return [
        Image.open(io.BytesIO(gi.image.image_bytes))
        for gi in resp.generated_images
    ]
