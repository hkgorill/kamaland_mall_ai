from __future__ import annotations

import time
from typing import Generator
from google import genai
from google.genai import types
from config import GOOGLE_API_KEY, GEMINI_TEXT_MODEL

_MAX_RETRIES = 3
_RETRY_DELAY = 2.0

# 모듈 레벨 싱글톤 (Streamlit 외부에서도 동작)
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def _classify_error(e: Exception) -> str:
    msg = str(e)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        return "API 요청 한도 초과입니다. 잠시 후 다시 시도해주세요."
    if "401" in msg or "403" in msg or "API_KEY" in msg.upper():
        return "API Key가 유효하지 않습니다. .env 파일을 확인하세요."
    if "404" in msg or "NOT_FOUND" in msg:
        return "지정된 모델을 찾을 수 없습니다. config.py의 모델명을 확인하세요."
    if "SAFETY" in msg or "blocked" in msg.lower():
        return "안전 필터에 의해 응답이 차단되었습니다. 프롬프트를 수정해주세요."
    return f"API 오류: {msg[:200]}"


def generate_text(
    prompt: str,
    system_prompt: str = "",
    model: str = GEMINI_TEXT_MODEL,
    temperature: float = 0.8,
) -> str:
    """텍스트 생성. 실패 시 최대 _MAX_RETRIES 회 재시도."""
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_prompt or None,
    )
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            last_error = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY * (attempt + 1))
    raise RuntimeError(_classify_error(last_error)) from last_error


def generate_json(
    prompt: str,
    system_prompt: str = "",
    model: str = GEMINI_TEXT_MODEL,
    temperature: float = 0.4,
) -> str:
    """JSON 형식 응답 생성. response_mime_type으로 JSON 강제."""
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        system_instruction=system_prompt or None,
    )
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            last_error = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY * (attempt + 1))
    raise RuntimeError(_classify_error(last_error)) from last_error


def generate_streaming(
    prompt: str,
    system_prompt: str = "",
    model: str = GEMINI_TEXT_MODEL,
    temperature: float = 0.8,
) -> Generator[str, None, None]:
    """스트리밍 텍스트 생성. st.write_stream()에 전달해서 사용."""
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_prompt or None,
    )
    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        raise RuntimeError(_classify_error(e)) from e


def test_connection() -> tuple[bool, str]:
    """API 연결 상태 확인."""
    try:
        result = generate_text(
            "연결 테스트입니다. '연결 성공'이라고만 답해주세요.",
            temperature=0.0,
        )
        return True, result.strip()
    except Exception as e:
        return False, str(e)
