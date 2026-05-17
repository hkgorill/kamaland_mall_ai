from __future__ import annotations

import datetime
from pathlib import Path

import streamlit as st

import utils.session as session

_IMAGES_DIR = Path(__file__).parent.parent / "outputs" / "images"
_PAGES_DIR  = Path(__file__).parent.parent / "outputs" / "pages"


def render() -> None:
    # ── 헤더 ──────────────────────────────────────────────────
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일")
    st.markdown(
        f"""<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
        <div>
          <div style="font-size:1.7rem;font-weight:800;color:#E8E8F0;">
            👋 오늘도 잘 팔아봅시다!</div>
          <div style="font-size:0.85rem;color:#64748B;margin-top:2px;">{today}</div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── 전체 진행률 ────────────────────────────────────────────
    steps = [
        ("sourcing_done",  "🔍 소싱 키워드",  "오늘 뭐 팔지? (소싱)"),
        ("images_done",    "🖼️ 대표 이미지",  "대표 이미지 만들기"),
        ("copy_done",      "✍️ 후킹 문구",    "상세페이지 후킹 문구"),
        ("detail_done",    "📄 상세페이지",   "상세페이지 생성"),
    ]
    done_flags = [session.get(key) for key, _, _ in steps]
    done_count = sum(done_flags)
    pct        = done_count / len(steps)

    col_pct, col_bar = st.columns([1, 4])
    with col_pct:
        st.markdown(
            f"""<div style="text-align:center;padding:0.5rem;">
            <div style="font-size:2rem;font-weight:800;color:#7C3AED;">{done_count}/4</div>
            <div style="font-size:0.75rem;color:#64748B;">단계 완료</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col_bar:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.progress(pct, text=f"전체 진행률 {int(pct*100)}%")
        # 다음 단계 안내
        next_step = next(((lbl, pg) for done, (_, lbl, pg) in zip(done_flags, steps) if not done), None)
        if next_step:
            lbl, pg = next_step
            st.caption(f"▶ 다음 단계: **{lbl}**")
        else:
            st.caption("🎉 모든 단계 완료! 상세페이지를 확인하세요.")

    st.divider()

    # ── 4단계 상태 카드 ────────────────────────────────────────
    step_cols = st.columns(4)
    current_page = st.session_state.get("_current_page", "대시보드")

    for col, (done, (key, label, page)) in zip(step_cols, zip(done_flags, steps)):
        with col:
            is_current = (page == current_page)
            border_col = "#7C3AED" if done else ("#A78BFA" if is_current else "#2D2D4E")
            bg_col     = "#1E1030" if done else "#1A1A2E"
            status_txt = "✅ 완료" if done else ("🔵 진행중" if is_current else "⬜ 대기")
            status_col = "#7C3AED" if done else ("#A78BFA" if is_current else "#4B5563")

            st.markdown(
                f"""<div style="background:{bg_col};border:1.5px solid {border_col};
                border-radius:12px;padding:1.1rem;text-align:center;">
                <div style="font-size:1.5rem;margin-bottom:4px;">{label.split()[0]}</div>
                <div style="font-weight:600;font-size:0.82rem;color:#E8E8F0;margin-bottom:8px;">
                  {' '.join(label.split()[1:])}</div>
                <div style="font-size:0.78rem;color:{status_col};font-weight:700;margin-bottom:10px;">
                  {status_txt}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if not done:
                if st.button(f"{'시작' if not any(done_flags) else '이동'} →",
                             key=f"dash_go_{key}", use_container_width=True):
                    st.session_state["_nav"] = page
                    st.rerun()

    st.divider()

    # ── 세션 결과 미리보기 ─────────────────────────────────────
    col_left, col_right = st.columns([1, 1])

    with col_left:
        _render_keywords_preview()
        _render_copy_preview()

    with col_right:
        _render_image_preview()
        _render_saved_files()

    st.divider()

    # ── 푸터 액션 ─────────────────────────────────────────────
    rst_col, _ = st.columns([1, 3])
    with rst_col:
        if st.button("🔄 세션 초기화", type="secondary", use_container_width=True):
            session.reset_all()
            # sourcing 파서 임시 상태도 초기화
            for k in ["_sourcing_parsed", "_selected_keywords", "_bg_removed_image", "_api_results"]:
                st.session_state.pop(k, None)
            st.rerun()


# ── 미리보기 컴포넌트 ──────────────────────────────────────────

def _render_keywords_preview() -> None:
    keywords: list = session.get("sourcing_keywords") or []
    if not keywords:
        return
    st.markdown("**🔍 소싱 키워드**")
    if isinstance(keywords[0], dict):
        for kw in keywords[:4]:
            st.markdown(
                f"""<div style="background:#1A1A2E;border:1px solid #2D2D4E;border-radius:8px;
                padding:0.5rem 0.8rem;margin-bottom:4px;font-size:0.82rem;">
                🏷️ <strong style="color:#E8E8F0;">{kw['keyword']}</strong>
                <span style="color:#64748B;"> — {kw.get('selling_point','')[:30]}</span>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        for line in keywords[:4]:
            st.markdown(f"- {line}")
    if len(keywords) > 4:
        st.caption(f"외 {len(keywords)-4}개")
    st.markdown("")


def _render_copy_preview() -> None:
    copy: dict = session.get("copy_result") or {}
    if not copy.get("main_title"):
        return
    st.markdown("**✍️ 카피라이팅 결과**")
    st.markdown(
        f"""<div style="background:#1A1A2E;border:1px solid #7C3AED;border-radius:10px;padding:1rem;">
        <div style="font-size:0.68rem;color:#7C3AED;font-weight:800;letter-spacing:0.1em;margin-bottom:4px;">
          MAIN TITLE</div>
        <div style="font-size:1rem;font-weight:700;color:#E8E8F0;margin-bottom:8px;">
          {copy['main_title']}</div>
        <div style="font-size:0.78rem;color:#94A3B8;">{copy.get('sub_title','')}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("")


def _render_image_preview() -> None:
    images_raw: list = session.get("generated_images") or []
    ok_items = [it for it in images_raw if it.get("image") is not None]
    if not ok_items:
        return
    st.markdown("**🖼️ 생성된 이미지**")
    thumb_cols = st.columns(min(len(ok_items), 3))
    for col, item in zip(thumb_cols, ok_items[:3]):
        with col:
            st.image(item["image"], caption=item["name"], use_container_width=True)
    if len(ok_items) > 3:
        st.caption(f"외 {len(ok_items)-3}장")
    st.markdown("")


def _render_saved_files() -> None:
    img_files  = sorted(_IMAGES_DIR.glob("*.png"), reverse=True)[:3]
    page_files = sorted(_PAGES_DIR.glob("*.html"),  reverse=True)[:3]
    if not img_files and not page_files:
        return

    st.markdown("**💾 저장된 결과물**")
    for f in img_files:
        size_kb = f.stat().st_size // 1024
        mtime   = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M")
        st.markdown(
            f"""<div style="font-size:0.78rem;color:#64748B;padding:2px 0;">
            🖼 {f.name[:30]}  <span style="color:#4B5563;">{size_kb}KB · {mtime}</span>
            </div>""",
            unsafe_allow_html=True,
        )
    for f in page_files:
        size_kb = f.stat().st_size // 1024
        mtime   = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M")
        st.markdown(
            f"""<div style="font-size:0.78rem;color:#64748B;padding:2px 0;">
            📄 {f.name[:30]}  <span style="color:#4B5563;">{size_kb}KB · {mtime}</span>
            </div>""",
            unsafe_allow_html=True,
        )
