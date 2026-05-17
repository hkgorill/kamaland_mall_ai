from __future__ import annotations

import io
import streamlit as st
from PIL import Image
import utils.session as session
from config import IMAGE_CONCEPTS

# Gemini 웹/앱에서 사용할 복사용 프롬프트 5가지
_MANUAL_PROMPTS = [
    (
        "☕ 카페 라이프스타일",
        "이 상품 이미지를 사용해서 배경만 교체한 전문 상품 사진을 만들어주세요.\n"
        "배경: 아늑한 카페 인테리어, 원목 테이블, 커피잔과 노트 소품, 따뜻한 조명과 보케 효과\n"
        "상품의 형태·색상·디테일은 정확히 유지해주세요. 고해상도 상업용 제품 사진 스타일.",
    ),
    (
        "🏠 모던 홈 인테리어",
        "이 상품 이미지를 사용해서 배경만 교체한 전문 상품 사진을 만들어주세요.\n"
        "배경: 모던 미니멀 인테리어, 밝은 화이트 벽, 원목 선반·소품, 부드러운 자연광 채광\n"
        "상품의 형태·색상·디테일은 정확히 유지해주세요. 라이프스타일 잡지 화보 스타일.",
    ),
    (
        "📸 SNS 감성 플랫레이",
        "이 상품 이미지를 사용해서 SNS 감성 플랫레이 스타일로 편집해주세요.\n"
        "구도: 탑뷰(위에서 아래로), 파스텔 톤 배경, 꽃잎·리본·계절 소품 배치\n"
        "상품의 형태·색상·디테일은 정확히 유지해주세요. 인스타그램 제품 사진 스타일.",
    ),
    (
        "💜 프리미엄 그라데이션",
        "이 상품 이미지를 사용해서 배경만 교체한 고급 제품 사진을 만들어주세요.\n"
        "배경: 딥 퍼플-블루 또는 골드-베이지 그라데이션, 부드러운 그림자, 하이라이트 반사 효과\n"
        "상품의 형태·색상·디테일은 정확히 유지해주세요. 럭셔리 브랜드 광고 스타일.",
    ),
    (
        "🌿 계절 감성 아웃도어",
        "이 상품 이미지를 사용해서 배경만 교체한 아웃도어 라이프스타일 사진을 만들어주세요.\n"
        "배경: 봄 정원 또는 가을 낙엽 환경, 초록 식물·꽃, 따뜻한 골든아워 햇빛\n"
        "상품의 형태·색상·디테일은 정확히 유지해주세요. 자연 감성 라이프스타일 잡지 스타일.",
    ),
]


def _pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _fetch_image_bytes_from_url(url: str) -> bytes:
    """URL에서 이미지 다운로드 → bytes 반환. 실패 시 예외 발생."""
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.ownerclan.com/",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    ct = resp.headers.get("Content-Type", "")
    if "image" not in ct and not url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise ValueError(f"이미지 URL이 아닙니다 (Content-Type: {ct})")
    return resp.content


def render() -> None:
    st.markdown("## 🖼️ 대표 이미지 만들기")
    st.caption("원본 상품 사진 업로드 → 배경 제거 확인 → AI 자동 생성(3장, 과금) + 직접 업로드(최대 5장, 무료)")
    st.divider()

    # ── URL 자동 생성 (소싱 연동 또는 직접 URL 입력) ───────────
    oc_product: dict = session.get("oc_selected_product") or {}
    default_url = oc_product.get("image_url", "")

    st.markdown("### 🔗 URL로 이미지 3장 자동 생성 (오너클랜 연동)")
    st.caption("오너클랜 대표이미지 URL 또는 상품 이미지 URL을 입력하면 배경 교체 AI 이미지 3장을 자동 생성합니다.")

    url_col, btn_col = st.columns([3, 1])
    with url_col:
        img_url = st.text_input(
            "이미지 URL",
            value=default_url,
            placeholder="https://cdn.ownerclan.com/... 또는 다른 상품 이미지 URL",
            label_visibility="collapsed",
        )
    with btn_col:
        url_gen_btn = st.button(
            "✨ 자동 생성",
            type="primary",
            disabled=not bool(img_url),
            use_container_width=True,
        )

    if url_gen_btn and img_url:
        from services.image_service import generate_product_images
        try:
            with st.spinner("이미지를 다운로드하는 중..."):
                raw = _fetch_image_bytes_from_url(img_url)

            # 세션에 원본 이미지 저장 (Step 1과 공유)
            session.set("uploaded_image_bytes", raw)
            session.set("uploaded_image_name", "url_image.jpg")
            session.set("_bg_removed_image", None)
            st.session_state.pop("_api_results", None)
            session.set("generated_images", [])
            session.set("images_done", False)

            prog_col, status_col = st.columns([2, 1])
            with prog_col:
                progress_bar = st.progress(0)
            with status_col:
                status_text = st.empty()

            def _on_progress(done: int, total: int) -> None:
                progress_bar.progress(int(done / total * 100))
                status_text.markdown(f"**{done} / {total}** 완료")

            results = generate_product_images(raw, on_progress=_on_progress)
            st.session_state["_api_results"] = results
            ok = sum(1 for r in results if r["image"] is not None)
            progress_bar.progress(100)
            status_text.markdown(f"**{ok}장 생성 완료** ✅")
            st.toast(f"AI 이미지 {ok}장 생성 완료!", icon="🖼️")
            st.rerun()
        except Exception as e:
            st.error(f"이미지 처리 실패: {e}")

    # ── URL 생성 결과를 버튼 바로 아래에 즉시 표시 ────────────
    url_api_results: list[dict] = st.session_state.get("_api_results") or []
    url_ok_items = [r for r in url_api_results if r["image"] is not None]
    if url_ok_items:
        st.success(f"✅ AI 이미지 {len(url_ok_items)}장 생성 완료")
        img_cols = st.columns(len(url_ok_items))
        for col, item in zip(img_cols, url_ok_items):
            with col:
                st.markdown(f"**{item['name']}**")
                st.image(item["image"], use_container_width=True)
                st.download_button(
                    label="⬇️ 다운로드",
                    data=_pil_to_bytes(item["image"]),
                    file_name=f"product_{item['name']}.png",
                    mime="image/png",
                    key=f"dl_url_{item['name']}",
                    use_container_width=True,
                )
        if st.button("➡️ 상세페이지 후킹 문구로 이동", type="secondary", key="url_nav_copy"):
            st.session_state["_nav"] = "상세페이지 후킹 문구"
            st.rerun()

    st.divider()

    # ── STEP 1: 이미지 업로드 ─────────────────────────────────
    st.markdown("### Step 1 · 원본 이미지 업로드 (직접 촬영 이미지)")
    st.markdown(
        """<div style="background:#0d1117;border:1px solid #2D2D4E;border-radius:8px;
        padding:0.65rem 1rem;margin-bottom:0.8rem;font-size:0.79rem;color:#64748B;">
        📸 <strong style="color:#A78BFA;">저작권 안전 소싱 가이드</strong><br>
        <span style="color:#4B5563;">
        ✅ <strong>권장:</strong> 샘플 1개 직접 구매 후 스마트폰 촬영 → AI 배경 교체 (저작권 100% 본인 소유)<br>
        ✅ <strong>권장:</strong> 도매꾹·오너클랜 등 B2B 플랫폼 이미지 (판매자가 사용 허가 배포)<br>
        ✅ <strong>권장:</strong> AliExpress·Taobao 소싱 이미지 (해외 플랫폼, 국내 신고 리스크 낮음)<br>
        ⛔ <strong>비권장:</strong> 국내 B2C 타 판매자 이미지 무단 사용 (저작권·2차적저작물 침해 위험)
        </span></div>""",
        unsafe_allow_html=True,
    )
    upload_col, preview_col = st.columns([1, 1])

    with upload_col:
        uploaded = st.file_uploader(
            "JPG / PNG 파일을 업로드하세요",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )
        if uploaded:
            raw = uploaded.read()
            if raw != session.get("uploaded_image_bytes"):
                session.set("uploaded_image_bytes", raw)
                session.set("uploaded_image_name", uploaded.name)
                session.set("_bg_removed_image", None)
                st.session_state.pop("_api_results", None)  # 새 이미지면 API 결과 초기화
                session.set("generated_images", [])
                session.set("images_done", False)

        stored_bytes = session.get("uploaded_image_bytes")
        if stored_bytes:
            st.image(Image.open(io.BytesIO(stored_bytes)), caption="원본 이미지", use_container_width=True)

    with preview_col:
        stored_bytes = session.get("uploaded_image_bytes")
        bg_removed: Image.Image | None = st.session_state.get("_bg_removed_image")

        if stored_bytes:
            if st.button("🪄 배경 제거 미리보기", use_container_width=True, disabled=bg_removed is not None):
                from services.image_service import remove_background
                with st.spinner("배경을 제거하는 중입니다... (약 5~15초)"):
                    try:
                        result = remove_background(stored_bytes)
                        st.session_state["_bg_removed_image"] = result
                        st.toast("배경 제거 완료!", icon="🪄")
                        st.rerun()
                    except Exception as e:
                        st.error(f"배경 제거 실패: {e}")

            if bg_removed is not None:
                checker_bg = _make_checker_bg(bg_removed.size)
                checker_bg.paste(bg_removed, mask=bg_removed.split()[3] if bg_removed.mode == "RGBA" else None)
                st.image(checker_bg, caption="배경 제거 결과", use_container_width=True)
                st.caption("✅ 배경 제거 완료 — 이제 이미지를 생성할 수 있습니다.")
            else:
                st.info("버튼을 눌러 배경 제거 결과를 미리 확인하세요.")
        else:
            st.info("왼쪽에서 이미지를 먼저 업로드해주세요.")

    st.divider()

    # ── STEP 2: API 자동 생성 (3컨셉) ─────────────────────────
    st.markdown("### Step 2 · AI 자동 생성 — 3가지 컨셉 (API 과금)")

    has_image = session.get("uploaded_image_bytes") is not None
    run = st.button(
        "✨ 이미지 3장 자동 생성하기",
        type="primary",
        disabled=not has_image,
        use_container_width=False,
    )
    if not has_image:
        st.caption("이미지 업로드 후 활성화됩니다.")

    if run:
        from services.image_service import generate_product_images
        raw = session.get("uploaded_image_bytes")

        prog_col, status_col = st.columns([2, 1])
        with prog_col:
            progress_bar = st.progress(0)
        with status_col:
            status_text = st.empty()

        def _on_progress(done: int, total: int) -> None:
            progress_bar.progress(int(done / total * 100))
            status_text.markdown(f"**{done} / {total}** 완료")

        try:
            results = generate_product_images(raw, on_progress=_on_progress)
            st.session_state["_api_results"] = results  # 수동 업로드와 합산용 백업
            ok = sum(1 for r in results if r["image"] is not None)
            progress_bar.progress(100)
            status_text.markdown(f"**{ok}장 생성 완료** ✅")
            st.toast(f"AI 이미지 {ok}장 생성 완료!", icon="🖼️")
            st.rerun()
        except Exception as e:
            st.error(f"이미지 생성 실패: {e}")
            progress_bar.empty()
            status_text.empty()

    st.divider()

    # ── STEP 3: Gemini 웹/앱 직접 생성 후 업로드 ─────────────
    st.markdown("### Step 3 · Gemini 웹/앱에서 직접 생성 후 업로드 (무료)")
    st.caption(
        "gemini.google.com 또는 Gemini 앱에서 상품 이미지를 첨부한 뒤 아래 프롬프트를 사용하세요. "
        "Basic 무료 20회/일 · AI Plus 50회/일 · Pro 100회/일"
    )

    with st.expander("💡 복사해서 쓰는 Gemini 이미지 프롬프트 5가지", expanded=True):
        st.markdown(
            """<div style="background:#1A1A2E;border:1px solid #7C3AED;border-radius:8px;
            padding:0.7rem 1rem;margin-bottom:1rem;font-size:0.82rem;color:#94A3B8;">
            📌 <strong style="color:#A78BFA;">사용법:</strong>
            gemini.google.com 에서 상품 이미지를 첨부(📎)한 후 아래 프롬프트를 복사해 붙여넣고 전송하세요.</div>""",
            unsafe_allow_html=True,
        )
        for label, prompt_text in _MANUAL_PROMPTS:
            st.markdown(f"**{label}**")
            st.code(prompt_text, language=None)
            st.markdown("")

    manual_files = st.file_uploader(
        "Gemini에서 생성한 이미지 업로드 (최대 5장, JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="manual_uploader",
    )

    # 수동 업로드 이미지 처리
    manual_items: list[dict] = []
    if manual_files:
        for i, f in enumerate(manual_files[:5]):
            try:
                img = Image.open(io.BytesIO(f.read()))
                manual_items.append({"name": f"직접업로드_{i + 1}", "image": img, "error": ""})
            except Exception:
                pass

    # API 결과 + 수동 업로드 합산 → generated_images 갱신
    api_items: list[dict] = st.session_state.get("_api_results") or []
    combined = api_items + manual_items
    session.set("generated_images", combined)
    if combined:
        session.set("images_done", any(item["image"] is not None for item in combined))
    else:
        session.set("images_done", False)

    st.divider()

    # ── 통합 갤러리 ────────────────────────────────────────────
    ok_api  = [it for it in api_items   if it["image"] is not None]
    ok_man  = [it for it in manual_items if it["image"] is not None]
    fail_items = [it for it in combined  if it["image"] is None]
    total_ok = len(ok_api) + len(ok_man)

    if total_ok > 0:
        st.markdown(f"### 🎨 이미지 갤러리 (총 {total_ok}장)")

        if ok_api:
            st.caption("🤖 AI 자동 생성")
            cols = st.columns(min(len(ok_api), 3))
            for idx, item in enumerate(ok_api):
                with cols[idx % len(cols)]:
                    st.markdown(f"**{item['name']}**")
                    st.image(item["image"], use_container_width=True)
                    st.download_button(
                        label="⬇️ 다운로드",
                        data=_pil_to_bytes(item["image"]),
                        file_name=f"product_{item['name']}.png",
                        mime="image/png",
                        key=f"dl_api_{item['name']}",
                        use_container_width=True,
                    )
                    st.markdown("")

        if ok_man:
            st.caption("📤 직접 업로드")
            cols = st.columns(min(len(ok_man), 3))
            for idx, item in enumerate(ok_man):
                with cols[idx % len(cols)]:
                    st.markdown(f"**{item['name']}**")
                    st.image(item["image"], use_container_width=True)
                    st.markdown("")

        if fail_items:
            with st.expander(f"⚠️ 생성 실패 {len(fail_items)}건"):
                for item in fail_items:
                    st.warning(f"**{item['name']}**: {item.get('error', '알 수 없는 오류')}")

        _parts = []
        if ok_api:
            _parts.append(f"AI {len(ok_api)}장")
        if ok_man:
            _parts.append(f"직접업로드 {len(ok_man)}장")
        _detail = f"  ({' + '.join(_parts)})" if _parts else ""
        st.success(f"총 {total_ok}장 준비 완료{_detail}")

        if st.button("➡️ 상세페이지 후킹 문구로 이동", type="secondary"):
            st.session_state["_nav"] = "상세페이지 후킹 문구"
            st.rerun()


def _make_checker_bg(size: tuple[int, int], block: int = 24) -> Image.Image:
    """투명도 확인용 체크무늬 배경 생성."""
    from PIL import ImageDraw
    w, h = size
    bg   = Image.new("RGB", (w, h), (180, 180, 180))
    draw = ImageDraw.Draw(bg)
    for y in range(0, h, block):
        for x in range(0, w, block):
            if (x // block + y // block) % 2 == 0:
                draw.rectangle([x, y, min(x + block, w) - 1, min(y + block, h) - 1],
                                fill=(240, 240, 240))
    return bg
