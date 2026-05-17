from __future__ import annotations

import json
import streamlit as st
import utils.session as session
from config import COPYWRITING_SYSTEM_PROMPT

_OUTPUT_FORMAT = """
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요:
{
  "main_title": "메인 타이틀 (20자 이내, 강렬한 한 줄)",
  "sub_title": "서브 타이틀 (40자 이내, 문제 공감 또는 혜택 강조)",
  "key_points": [
    {"icon": "이모지", "headline": "소구점 제목 (10자 이내)", "description": "설명 (40자 이내)"},
    {"icon": "이모지", "headline": "소구점 제목 (10자 이내)", "description": "설명 (40자 이내)"},
    {"icon": "이모지", "headline": "소구점 제목 (10자 이내)", "description": "설명 (40자 이내)"}
  ],
  "cta_text": "구매 행동 유도 문구 (20자 이내, 예: 지금 바로 경험해보세요!)"
}
"""


def render() -> None:
    st.markdown("## ✍️ 상세페이지 후킹 문구")
    st.caption("PAS + AIDA 프레임워크로 구매 전환율을 높이는 카피를 생성합니다.")
    st.divider()

    # ── 입력 영역 ──────────────────────────────────────────────
    tab_text, tab_url = st.tabs(["📝 상품 정보 직접 입력", "🔗 URL에서 자동 추출"])

    product_info: str = ""

    with tab_text:
        # 소싱에서 키워드가 있으면 자동 채움
        sourcing_kws: list[dict] = session.get("sourcing_keywords") or []
        default_text: str = session.get("product_info") or ""
        if not default_text and sourcing_kws:
            if isinstance(sourcing_kws[0], dict):
                lines = [f"- **{k['keyword']}**: {k.get('selling_point','')}" for k in sourcing_kws[:5]]
            else:
                lines = [str(k) for k in sourcing_kws[:5]]
            default_text = "소싱 추천 키워드:\n" + "\n".join(lines)

        entered = st.text_area(
            "상품명, 특징, 타겟 고객, 가격대 등을 자유롭게 입력",
            value=default_text,
            height=180,
            placeholder="예) 상품명: 무선 이어폰\n특징: 30시간 배터리, 노이즈캔슬링, 방수IPX5\n타겟: 직장인, 운동하는 2030\n가격대: 2~3만원대",
        )
        if entered:
            product_info = entered

    with tab_url:
        url_val = st.text_input(
            "상품 URL 입력",
            placeholder="https://smartstore.naver.com/... 또는 https://www.coupang.com/...",
        )
        fetch_btn = st.button("🔗 URL에서 정보 가져오기", use_container_width=False)
        if fetch_btn:
            if url_val:
                from services.scraper_service import scrape_product_info, format_for_copywriting
                with st.spinner("URL에서 상품 정보를 가져오는 중..."):
                    scraped = scrape_product_info(url_val)
                if scraped["error"]:
                    st.error(scraped["error"])
                    st.info("차단된 경우 상품 정보를 직접 입력해주세요.")
                else:
                    formatted = format_for_copywriting(scraped)
                    session.set("product_info", formatted)
                    st.success("정보를 가져왔습니다. '직접 입력' 탭에서 확인·수정하세요.")
                    st.rerun()
            else:
                st.warning("URL을 입력해주세요.")

    st.divider()

    gen_btn = st.button(
        "✍️ 후킹 문구 생성하기",
        type="primary",
        disabled=not bool(product_info),
    )
    if not product_info:
        st.caption("상품 정보를 입력해야 버튼이 활성화됩니다.")

    if gen_btn and product_info:
        from services.gemini_service import generate_json
        session.set("product_info", product_info)
        prompt = (
            f"다음 상품 정보를 기반으로 구매 전환율을 높이는 카피라이팅을 작성해주세요:\n\n"
            f"{product_info}\n\n"
            f"{_OUTPUT_FORMAT}"
        )
        with st.spinner("카피라이팅 중입니다... (약 5~10초)"):
            try:
                raw_json = generate_json(prompt, system_prompt=COPYWRITING_SYSTEM_PROMPT)
                parsed = json.loads(raw_json)
                session.set("copy_result", parsed)
                session.set("copy_done", True)
                st.toast("카피라이팅 생성 완료!", icon="✍️")
                st.rerun()
            except json.JSONDecodeError:
                st.error("AI 응답 파싱에 실패했습니다. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"후킹 문구 생성 실패: {e}")

    # ── 결과 + 편집 영역 ───────────────────────────────────────
    copy: dict = session.get("copy_result") or {}
    if not copy.get("main_title"):
        return

    st.markdown("### 🎯 생성된 카피라이팅")

    # 편집 모드 토글
    edit_mode = st.toggle("✏️ 편집 모드", value=False)

    if edit_mode:
        _render_edit_mode(copy)
    else:
        _render_display_mode(copy)

    st.divider()
    if st.button("➡️ 상세페이지 생성으로 이동", type="secondary"):
        st.session_state["_nav"] = "상세페이지 생성"
        st.rerun()


# ── 표시 모드 ──────────────────────────────────────────────────

def _render_display_mode(copy: dict) -> None:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""<div style="background:#1A1A2E;border:1.5px solid #7C3AED;
            border-radius:12px;padding:1.4rem;height:100px;display:flex;flex-direction:column;justify-content:center;">
            <div style="font-size:0.68rem;color:#7C3AED;font-weight:800;letter-spacing:0.12em;margin-bottom:6px;">
              MAIN TITLE</div>
            <div style="font-size:1.25rem;font-weight:800;color:#E8E8F0;line-height:1.3;">
              {copy.get('main_title','')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f"""<div style="background:#1A1A2E;border:1px solid #2D2D4E;
            border-radius:12px;padding:1.4rem;height:100px;display:flex;flex-direction:column;justify-content:center;">
            <div style="font-size:0.68rem;color:#A78BFA;font-weight:800;letter-spacing:0.12em;margin-bottom:6px;">
              SUB TITLE</div>
            <div style="font-size:0.95rem;color:#CBD5E1;line-height:1.5;">
              {copy.get('sub_title','')}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("#### 핵심 소구점")
    pts = copy.get("key_points", [])
    if pts:
        cols = st.columns(len(pts))
        for col, pt in zip(cols, pts):
            with col:
                st.markdown(
                    f"""<div style="background:#1A1A2E;border:1px solid #2D2D4E;
                    border-radius:10px;padding:1rem;text-align:center;min-height:120px;">
                    <div style="font-size:2rem;">{pt.get('icon','✅')}</div>
                    <div style="font-weight:700;font-size:0.9rem;margin:6px 0 4px;color:#E8E8F0;">
                      {pt.get('headline','')}</div>
                    <div style="font-size:0.8rem;color:#94A3B8;line-height:1.4;">
                      {pt.get('description','')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    st.markdown(
        f"""<div style="background:#1A1A2E;border:1px solid #2D2D4E;border-radius:10px;
        padding:0.9rem 1.2rem;margin-top:1rem;font-size:0.9rem;color:#A78BFA;">
        🛍️ <strong>CTA:</strong> {copy.get('cta_text','')}
        </div>""",
        unsafe_allow_html=True,
    )


# ── 편집 모드 ──────────────────────────────────────────────────

def _render_edit_mode(copy: dict) -> None:
    st.caption("수정 후 '저장'을 눌러야 상세페이지에 반영됩니다.")

    new_main  = st.text_input("메인 타이틀", value=copy.get("main_title", ""))
    new_sub   = st.text_input("서브 타이틀",  value=copy.get("sub_title", ""))
    new_cta   = st.text_input("CTA 문구",     value=copy.get("cta_text", ""))

    st.markdown("**핵심 소구점 편집**")
    pts = copy.get("key_points", [{}, {}, {}])
    new_pts = []
    for i, pt in enumerate(pts):
        with st.expander(f"소구점 {i+1}: {pt.get('headline','')}", expanded=True):
            ec1, ec2, ec3 = st.columns([0.12, 0.38, 0.5])
            with ec1:
                icon = st.text_input("아이콘", value=pt.get("icon", "✅"), key=f"icon_{i}")
            with ec2:
                hl   = st.text_input("제목",  value=pt.get("headline", ""),    key=f"hl_{i}")
            with ec3:
                desc = st.text_input("설명",  value=pt.get("description", ""), key=f"desc_{i}")
            new_pts.append({"icon": icon, "headline": hl, "description": desc})

    if st.button("💾 편집 내용 저장", type="primary"):
        updated = {
            "main_title": new_main,
            "sub_title":  new_sub,
            "cta_text":   new_cta,
            "key_points": new_pts,
        }
        session.set("copy_result", updated)
        st.toast("편집 내용 저장 완료!", icon="💾")
        st.rerun()
