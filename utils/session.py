import streamlit as st

# 세션 상태 키 정의
DEFAULTS: dict = {
    # 소싱
    "sourcing_keywords": [],
    "sourcing_done": False,
    # 이미지 생성
    "uploaded_image_bytes": None,
    "uploaded_image_name": "",
    "generated_images": [],       # list of {"name": str, "image": PIL.Image|None, "error": str}
    "images_done": False,
    # 카피라이팅
    "product_info": "",
    "copy_result": {
        "main_title": "",
        "sub_title": "",
        "key_points": [],
        "cta_text": "",
    },
    "copy_done": False,
    # 상세페이지
    "selected_image_idx": 0,
    "detail_html": "",
    "detail_done": False,
}


def init_session_state() -> None:
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def get(key: str):
    return st.session_state.get(key, DEFAULTS.get(key))


def set(key: str, value) -> None:
    st.session_state[key] = value


def reset_all() -> None:
    for key, default in DEFAULTS.items():
        st.session_state[key] = default
