import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="KAMALAND_MALL AI",
    page_icon="✨",
)

from utils.session import init_session_state
from utils.styles import apply_dark_theme
import views.dashboard   as dashboard
import views.sourcing    as sourcing
import views.image_gen   as image_gen
import views.copywriting as copywriting
import views.detail_page as detail_page

apply_dark_theme()
init_session_state()

# ── 페이지 전환 처리 (_nav → _current_page) ───────────────────
# 뷰에서 st.session_state["_nav"] = "페이지명" + st.rerun() 으로 호출
if "_nav" in st.session_state:
    nav_target = st.session_state.pop("_nav")
    st.session_state["_current_page"] = nav_target
    # radio 위젯 상태도 직접 설정 (key 사용 시 확실한 동기화)
    st.session_state["_sidebar_nav"] = nav_target

# ── 상수 ──────────────────────────────────────────────────────
PAGES = [
    "대시보드",
    "오늘 뭐 팔지? (소싱)",
    "대표 이미지 만들기",
    "상세페이지 후킹 문구",
    "상세페이지 생성",
]

PAGE_FUNCS = {
    "대시보드":             dashboard.render,
    "오늘 뭐 팔지? (소싱)": sourcing.render,
    "대표 이미지 만들기":   image_gen.render,
    "상세페이지 후킹 문구": copywriting.render,
    "상세페이지 생성":       detail_page.render,
}

WORKFLOW_STEPS = [
    ("🔍 소싱",   "sourcing_done",  "오늘 뭐 팔지? (소싱)"),
    ("🖼️ 이미지", "images_done",   "대표 이미지 만들기"),
    ("✍️ 문구",   "copy_done",     "상세페이지 후킹 문구"),
    ("📄 페이지", "detail_done",   "상세페이지 생성"),
]

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# ✨ KAMALAND")
    st.markdown("##### MALL AI")
    st.caption("AI 기반 무재고 위탁 판매 자동화")
    st.divider()

    # 전체 진행률
    done_count = sum(
        1 for _, key, _ in WORKFLOW_STEPS if st.session_state.get(key, False)
    )
    pct = done_count / len(WORKFLOW_STEPS)

    st.markdown(
        f"""<div style="display:flex;align-items:center;justify-content:space-between;
        margin-bottom:6px;">
        <span style="font-size:0.78rem;color:#A78BFA;font-weight:600;">전체 진행률</span>
        <span style="font-size:0.78rem;color:#7C3AED;font-weight:700;">{done_count}/{len(WORKFLOW_STEPS)} 완료</span>
        </div>""",
        unsafe_allow_html=True,
    )
    st.progress(pct)

    st.divider()

    # 네비게이션 라디오
    # _sidebar_nav 키로 직접 제어 (외부 전환 시 동기화)
    if "_sidebar_nav" not in st.session_state:
        st.session_state["_sidebar_nav"] = "대시보드"

    current_page: str = st.radio(
        "메뉴",
        PAGES,
        key="_sidebar_nav",
        label_visibility="collapsed",
    )
    # 선택된 페이지 동기화
    st.session_state["_current_page"] = current_page

    st.divider()

    # 단계별 완료 현황 (시각적 체크리스트)
    st.markdown(
        '<span style="font-size:0.75rem;color:#64748B;font-weight:600;'
        'letter-spacing:0.05em;">워크플로우</span>',
        unsafe_allow_html=True,
    )
    for label, key, page in WORKFLOW_STEPS:
        done    = st.session_state.get(key, False)
        is_cur  = (page == current_page)
        icon    = "✅" if done else ("▶" if is_cur else "⬜")
        col_txt = "#7C3AED" if done else ("#A78BFA" if is_cur else "#4B5563")
        weight  = "700" if (done or is_cur) else "400"
        st.markdown(
            f'<div style="font-size:0.8rem;color:{col_txt};font-weight:{weight};'
            f'padding:2px 0;line-height:1.8;">{icon} {label}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # API 연결 확인
    with st.expander("🔌 API 연결 확인"):
        if st.button("연결 테스트", use_container_width=True, key="api_test_btn"):
            from services.gemini_service import test_connection
            with st.spinner("테스트 중..."):
                ok, msg = test_connection()
            if ok:
                st.success(f"연결 성공  \n{msg}")
            else:
                st.error(f"연결 실패  \n{msg}")

    # 빠른 초기화
    with st.expander("⚙️ 설정"):
        if st.button("🔄 세션 초기화", use_container_width=True, key="sidebar_reset"):
            from utils.session import reset_all
            reset_all()
            for k in ["_sourcing_parsed", "_selected_keywords",
                      "_bg_removed_image", "_sidebar_nav", "_current_page"]:
                st.session_state.pop(k, None)
            st.rerun()

# ── 페이지 렌더링 ─────────────────────────────────────────────
PAGE_FUNCS[current_page]()
