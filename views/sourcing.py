from __future__ import annotations

import re
import streamlit as st
import utils.session as session
from config import SOURCING_SYSTEM_PROMPT


# ── 내부 파서 ─────────────────────────────────────────────────

def _parse_keywords(text: str) -> list[dict]:
    """
    AI 응답 → 구조화된 키워드 목록.
    기대 형식: - **키워드**: 판매포인트 | 타겟: 구매층
    """
    items: list[dict] = []
    pattern = re.compile(
        r"-\s+\*\*(.+?)\*\*\s*[:：]\s*(.+?)(?:\s*\|\s*타겟[:：]\s*(.+))?$",
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        items.append({
            "keyword":      m.group(1).strip(),
            "selling_point": m.group(2).strip(),
            "target":       (m.group(3) or "일반 소비자").strip(),
        })
    # fallback: 파싱 실패 → 줄 단위 처리
    if not items:
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("-"):
                continue
            clean = re.sub(r"\*+", "", line[1:]).strip()
            if clean:
                items.append({"keyword": clean, "selling_point": "", "target": ""})
    return items


# ── 체크박스 콜백 ─────────────────────────────────────────────

def _on_keyword_toggle(item: dict, chk_key: str) -> None:
    """체크박스 클릭 즉시 _selected_keywords 동기화 (렌더 전 실행)."""
    kw = item["keyword"]
    is_checked = st.session_state.get(chk_key, False)
    sel: list = list(st.session_state.get("_selected_keywords", []))  # 복사본

    if is_checked and not any(k["keyword"] == kw for k in sel):
        sel.append(item)
    elif not is_checked:
        sel = [k for k in sel if k["keyword"] != kw]

    st.session_state["_selected_keywords"] = sel


# ── 오너클랜 상품 카드 렌더 ───────────────────────────────────

def _render_oc_products(products: list[dict], keyword_idx: int) -> None:
    cols = st.columns(min(len(products), 3))
    for j, prod in enumerate(products):
        with cols[j % 3]:
            if prod.get("image_url"):
                st.image(prod["image_url"], use_container_width=True)
            name = prod["name"]
            display_name = (name[:28] + "…") if len(name) > 28 else name
            st.markdown(
                f"""<div style="font-size:0.78rem;font-weight:600;color:#E8E8F0;
                margin:4px 0 6px;line-height:1.3;">{display_name}</div>""",
                unsafe_allow_html=True,
            )
            st.link_button("🔗 오너클랜 보기", prod["product_url"], use_container_width=True)
            if st.button("✅ 이 상품 선택", key=f"oc_sel_{keyword_idx}_{j}", use_container_width=True):
                _select_oc_product(prod)


def _select_oc_product(prod: dict) -> None:
    import utils.session as _sess
    _sess.set("oc_selected_product", prod)
    _sess.set("sourcing_done", True)
    # 카피라이팅 입력에 상품명 + URL 자동 채움
    _sess.set(
        "product_info",
        f"상품명: {prod['name']}\n오너클랜 상품 URL: {prod['product_url']}",
    )
    import streamlit as _st
    _st.toast(f"'{prod['name'][:20]}' 선택 완료! 대표 이미지를 생성하세요.", icon="✅")
    _st.session_state["_nav"] = "대표 이미지 만들기"
    _st.rerun()


# ── 메인 렌더 ─────────────────────────────────────────────────

def render() -> None:
    st.markdown("## 🔍 오늘 뭐 팔지? (소싱)")
    st.caption("트렌디한 위탁 판매 아이템 키워드를 AI가 추천합니다. 마음에 드는 키워드를 선택해 다음 단계로 연동하세요.")
    st.divider()

    left, right = st.columns([1, 1.8])

    # ── 좌측: 설정 패널 ────────────────────────────────────────
    with left:
        st.markdown("### ⚙️ 설정")
        count = st.number_input("추출할 키워드 수", min_value=1, max_value=20, value=5, step=1)

        options = st.multiselect(
            "추가 조건 (선택)",
            ["SNS 바이럴 아이템", "계절성 상품", "리필·소모품", "선물용", "반려동물", "가성비"],
            default=[],
        )
        run = st.button("🔄 키워드 추출하기", type="primary", use_container_width=True)

        # 이미 선택된 키워드 요약 표시
        selected = st.session_state.get("_selected_keywords", [])
        if selected:
            st.divider()
            st.markdown("**선택된 키워드**")
            for kw in selected:
                st.markdown(f"- {kw['keyword']}")

            if st.button("✅ 선택 완료 → 후킹 문구로", type="primary", use_container_width=True):
                # 세션에 선택 결과 저장
                session.set("sourcing_keywords", selected)
                session.set("sourcing_done", True)
                session.set(
                    "product_info",
                    "\n".join(
                        f"- **{k['keyword']}**: {k['selling_point']}" for k in selected
                    ),
                )
                st.session_state["_nav"] = "상세페이지 후킹 문구"
                st.rerun()

    # ── 우측: 결과 패널 ────────────────────────────────────────
    with right:
        st.markdown("### 📋 추천 키워드")

        if run:
            from services.gemini_service import generate_text
            condition_str = ("추가 조건: " + ", ".join(options)) if options else ""
            prompt = (
                f"현재 날짜 기준으로 국내 온라인 위탁 판매에 최적화된 소형/생필품 키워드 {count}개를 추천해주세요.\n"
                f"{condition_str}\n\n"
                f"각 키워드는 반드시 아래 형식으로 작성하세요 (형식 이외 텍스트 없이):\n"
                f"- **[키워드]**: [판매 포인트 한 줄] | 타겟: [주요 구매층]\n\n"
                f"계절성, SNS 바이럴 가능성, 경쟁 강도를 고려해주세요."
            )
            with st.spinner("AI가 트렌드를 분석 중입니다..."):
                try:
                    result = generate_text(prompt, system_prompt=SOURCING_SYSTEM_PROMPT, temperature=0.8)
                    parsed = _parse_keywords(result)
                    # 이전 체크박스 위젯 상태 초기화 (재추출 시 상태 불일치 방지)
                    old_count = len(st.session_state.get("_sourcing_parsed", []))
                    for j in range(old_count):
                        st.session_state.pop(f"kw_chk_{j}", None)
                    st.session_state["_sourcing_parsed"] = parsed
                    st.session_state["_selected_keywords"] = []
                    st.toast(f"키워드 {len(parsed)}개 추출 완료!", icon="🔍")
                except Exception as e:
                    st.error(f"키워드 추출 실패: {e}")

        parsed_list: list[dict] = st.session_state.get("_sourcing_parsed", [])

        if not parsed_list:
            st.info("왼쪽에서 키워드 수를 설정하고 '추출하기' 버튼을 눌러주세요.")
            return

        # 키워드 카드 렌더링
        if "_selected_keywords" not in st.session_state:
            st.session_state["_selected_keywords"] = []

        st.caption(f"총 {len(parsed_list)}개 키워드 · 체크박스로 선택 후 왼쪽 '선택 완료' 버튼을 눌러주세요")

        for i, item in enumerate(parsed_list):
            kw  = item["keyword"]
            sp  = item["selling_point"]
            tgt = item["target"]
            chk_key = f"kw_chk_{i}"

            # _selected_keywords 를 단일 진실 소스로 사용
            is_selected = any(k["keyword"] == kw for k in st.session_state.get("_selected_keywords", []))

            col_chk, col_card = st.columns([0.08, 0.92])
            with col_chk:
                st.checkbox(
                    "",
                    value=is_selected,
                    key=chk_key,
                    on_change=_on_keyword_toggle,
                    args=(item, chk_key),
                    label_visibility="collapsed",
                )

            with col_card:
                border_color = "#7C3AED" if is_selected else "#2D2D4E"
                st.markdown(
                    f"""<div style="background:#1A1A2E;border:1.5px solid {border_color};
                    border-radius:10px;padding:0.9rem 1.1rem;margin-bottom:2px;">
                    <div style="font-weight:700;font-size:1rem;color:#E8E8F0;margin-bottom:4px;">
                      🏷️ {kw}</div>
                    <div style="font-size:0.83rem;color:#A78BFA;margin-bottom:2px;">
                      💡 {sp}</div>
                    <div style="font-size:0.78rem;color:#64748B;">
                      👥 타겟: {tgt}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # ── 오너클랜 상품 매핑 ─────────────────────────────────
        st.divider()
        st.markdown("#### 🛒 오너클랜 상품 찾기")
        st.caption("키워드별 오너클랜 상품을 조회하여 판매할 상품을 선택하세요. (www.ownerclan.com)")

        for i, item in enumerate(parsed_list):
            kw = item["keyword"]
            oc_key = f"oc_products_{i}"

            label_col, btn_col = st.columns([0.65, 0.35])
            with label_col:
                st.markdown(f"**🏷️ {kw}**")
            with btn_col:
                if st.button(
                    "🔍 오너클랜 검색",
                    key=f"oc_btn_{i}",
                    use_container_width=True,
                ):
                    from services.ownerclan_service import search_products
                    with st.spinner(f"'{kw}' 오너클랜 상품 검색 중... (약 5~15초)"):
                        products = search_products(kw, max_results=5)
                    st.session_state[oc_key] = products
                    st.session_state[f"oc_searched_{i}"] = True

            oc_products: list[dict] = st.session_state.get(oc_key, [])
            if oc_products:
                _render_oc_products(oc_products, i)
            elif st.session_state.get(f"oc_searched_{i}"):
                st.warning(f"'{kw}'에 해당하는 오너클랜 상품을 찾지 못했습니다.")
            st.markdown("")
