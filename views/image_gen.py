from __future__ import annotations

import io
import streamlit as st
from PIL import Image
import utils.session as session
from config import IMAGE_CONCEPTS


def _pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def render() -> None:
    st.markdown("## 🖼️ 대표 이미지 만들기")
    st.caption("원본 상품 사진 업로드 → 배경 제거 확인 → 5가지 컨셉 마케팅 이미지 생성")
    st.divider()

    # ── STEP 1: 이미지 업로드 ─────────────────────────────────
    st.markdown("### Step 1 · 원본 이미지 업로드")
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
                session.set("_bg_removed_image", None)  # 새 이미지면 미리보기 초기화
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
                # 체크무늬 배경 위에 배경 제거 결과 표시
                checker_bg = _make_checker_bg(bg_removed.size)
                checker_bg.paste(bg_removed, mask=bg_removed.split()[3] if bg_removed.mode == "RGBA" else None)
                st.image(checker_bg, caption="배경 제거 결과", use_container_width=True)
                st.caption("✅ 배경 제거 완료 — 이제 이미지를 생성할 수 있습니다.")
            else:
                st.info("버튼을 눌러 배경 제거 결과를 미리 확인하세요.")
        else:
            st.info("왼쪽에서 이미지를 먼저 업로드해주세요.")

    st.divider()

    # ── STEP 2: 이미지 생성 ───────────────────────────────────
    st.markdown("### Step 2 · 5가지 컨셉 이미지 생성")

    has_image = session.get("uploaded_image_bytes") is not None
    run = st.button(
        "✨ 이미지 5장 생성하기",
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
            session.set("generated_images", results)
            ok = sum(1 for r in results if r["image"] is not None)
            session.set("images_done", ok > 0)
            progress_bar.progress(100)
            status_text.markdown(f"**{ok}장 생성 완료** ✅")
            st.toast(f"이미지 {ok}장 생성 완료!", icon="🖼️")
            st.rerun()
        except Exception as e:
            st.error(f"이미지 생성 실패: {e}")
            progress_bar.empty()
            status_text.empty()

    # ── 갤러리 ────────────────────────────────────────────────
    generated: list[dict] = session.get("generated_images") or []
    if generated:
        st.markdown("### 🎨 생성된 이미지 갤러리")
        ok_items = [item for item in generated if item["image"] is not None]
        fail_items = [item for item in generated if item["image"] is None]

        # 2열 그리드 레이아웃
        cols = st.columns(2)
        for idx, item in enumerate(ok_items):
            with cols[idx % 2]:
                st.markdown(f"**{item['name']}**")
                st.image(item["image"], use_container_width=True)
                st.download_button(
                    label="⬇️ 다운로드",
                    data=_pil_to_bytes(item["image"]),
                    file_name=f"product_{item['name']}.png",
                    mime="image/png",
                    key=f"dl_{item['name']}",
                    use_container_width=True,
                )
                st.markdown("")

        if fail_items:
            with st.expander(f"⚠️ 생성 실패 {len(fail_items)}건"):
                for item in fail_items:
                    st.warning(f"**{item['name']}**: {item.get('error', '알 수 없는 오류')}")

        st.success(f"총 {len(ok_items)}장 생성 완료 · outputs/images/ 폴더에도 저장되었습니다.")

        if st.button("➡️ 상세페이지 후킹 문구로 이동", type="secondary"):
            st.session_state["_nav"] = "상세페이지 후킹 문구"
            st.rerun()


def _make_checker_bg(size: tuple[int, int], block: int = 24) -> Image.Image:
    """투명도 확인용 체크무늬 배경 생성 (ImageDraw 사용으로 빠름)."""
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
