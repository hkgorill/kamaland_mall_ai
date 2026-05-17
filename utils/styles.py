import streamlit as st

_CUSTOM_CSS = """
<style>
/* 사이드바 스타일 */
[data-testid="stSidebar"] {
    background-color: #0D0D1A;
    border-right: 1px solid #2D2D4E;
}

/* 메인 영역 배경 */
[data-testid="stAppViewContainer"] > .main {
    background-color: #0F0F0F;
}

/* 카드 컨테이너 */
.card {
    background-color: #1A1A2E;
    border: 1px solid #2D2D4E;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* 진행 단계 뱃지 */
.step-done   { color: #7C3AED; font-weight: 600; }
.step-active { color: #A78BFA; font-weight: 600; }
.step-todo   { color: #4B5563; }

/* 섹션 제목 */
.section-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #E8E8F0;
    margin-bottom: 0.5rem;
}

/* Primary 버튼 강조 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C3AED, #5B21B6);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* 이미지 갤러리 아이템 */
.gallery-item {
    border: 2px solid #2D2D4E;
    border-radius: 8px;
    overflow: hidden;
    transition: border-color 0.2s;
}
.gallery-item:hover {
    border-color: #7C3AED;
}

/* 워크플로우 진행바 */
.workflow-progress {
    font-size: 0.82rem;
    line-height: 2;
}
</style>
"""


def apply_dark_theme() -> None:
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)
