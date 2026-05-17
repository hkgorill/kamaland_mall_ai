from __future__ import annotations

import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

import utils.session as session
from utils.html_template import build_detail_page_html

_PAGES_DIR = Path(__file__).parent.parent / "outputs" / "pages"
_PAGES_DIR.mkdir(parents=True, exist_ok=True)


def render() -> None:
    st.markdown("## 📄 상세페이지 생성")
    st.caption("이미지와 카피라이팅을 합쳐 완성된 상세페이지를 미리보기하고 다운로드합니다.")
    st.divider()

    left, right = st.columns([1, 1.5])

    copy: dict         = session.get("copy_result") or {}
    images_raw: list   = session.get("generated_images") or []
    success_imgs       = [it for it in images_raw if it.get("image") is not None]

    # ── 좌측: 데이터 설정 ──────────────────────────────────────
    with left:
        st.markdown("### ⚙️ 데이터 설정")

        # 이미지 선택
        hero_img: Image.Image | None = None
        if success_imgs:
            names = [it["name"] for it in success_imgs]
            sel_name = st.selectbox("대표 이미지 선택", names)
            hero_img = next(it["image"] for it in success_imgs if it["name"] == sel_name)
            st.image(hero_img, use_container_width=True)
        else:
            st.warning("대표 이미지가 없습니다. '대표 이미지 만들기' 단계를 먼저 완료하거나 아래에서 직접 업로드하세요.")
            fallback_file = st.file_uploader("이미지 직접 업로드", type=["jpg","jpeg","png"])
            if fallback_file:
                from PIL import Image as PILImage
                import io
                hero_img = PILImage.open(io.BytesIO(fallback_file.read()))
                st.image(hero_img, use_container_width=True)

        st.divider()

        # 카피 확인 및 간단 수정
        st.markdown("**카피라이팅 설정**")
        if not copy.get("main_title"):
            st.warning("후킹 문구 단계를 먼저 완료하거나 아래에서 직접 입력하세요.")

        main_title = st.text_input("메인 타이틀", value=copy.get("main_title", ""))
        sub_title  = st.text_input("서브 타이틀",  value=copy.get("sub_title", ""))
        cta_text   = st.text_input("CTA 문구",     value=copy.get("cta_text", "지금 바로 구매하기"))

        # 키포인트는 현재 세션 데이터 사용 (편집은 후킹 문구 페이지에서)
        key_points = copy.get("key_points", [])
        if key_points:
            with st.expander("핵심 소구점 확인", expanded=False):
                for pt in key_points:
                    st.markdown(f"- {pt.get('icon','')} **{pt.get('headline','')}**: {pt.get('description','')}")

        st.divider()

        # 오너클랜 상세 HTML 입력
        with st.expander("📦 오너클랜 상세 이미지 추가 (선택)", expanded=False):
            st.caption("오너클랜 상품 상세페이지 HTML 코드를 붙여넣으면 img 태그 이미지가 상세페이지 하단에 자동 삽입됩니다.")
            oc_html_raw = st.text_area(
                "상세 HTML 코드",
                key="oc_detail_html_input",
                height=130,
                placeholder='<p align="center"><img src="https://..."><br><img src="https://..."></p>',
                label_visibility="collapsed",
            )
            oc_detail_urls: list[str] = []
            if oc_html_raw:
                import re as _re
                oc_detail_urls = _re.findall(
                    r'<img[^>]+src=["\']([^"\']+)["\']',
                    oc_html_raw, _re.IGNORECASE,
                )
                if oc_detail_urls:
                    st.caption(f"✅ 이미지 {len(oc_detail_urls)}개 감지됨 — 상세페이지 하단에 포함됩니다.")
                    with st.expander(f"감지된 이미지 URL {len(oc_detail_urls)}개 확인"):
                        for u in oc_detail_urls:
                            st.markdown(f"- `{u[:60]}...`" if len(u) > 60 else f"- `{u}`")
                else:
                    st.warning("img 태그에서 URL을 찾을 수 없습니다. HTML을 확인해주세요.")

        include_privacy = st.checkbox(
            "📋 개인정보 제3자 제공 안내 포함",
            value=True,
            help="배송 정보가 위탁 공급사에 제공될 수 있음을 고객에게 고지합니다. (개인정보보호법 제17조 권장)",
        )
        gen_btn = st.button(
            "🚀 상세페이지 생성 및 미리보기",
            type="primary",
            use_container_width=True,
        )

    # ── 우측: 미리보기 ─────────────────────────────────────────
    with right:
        st.markdown("### 👁️ 모바일 미리보기")

        if gen_btn:
            # 세션 카피 업데이트
            updated_copy = dict(copy)
            updated_copy.update({"main_title": main_title, "sub_title": sub_title, "cta_text": cta_text})
            session.set("copy_result", updated_copy)

            extra_imgs = [
                it["image"]
                for it in success_imgs
                if it["image"] is not None and it["image"] is not hero_img
            ][:3]

            with st.spinner("상세페이지를 조립 중입니다..."):
                try:
                    html = build_detail_page_html(
                        main_title=main_title,
                        sub_title=sub_title,
                        key_points=key_points,
                        cta_text=cta_text,
                        hero_image=hero_img,
                        extra_images=extra_imgs,
                        include_privacy_notice=include_privacy,
                        oc_detail_image_urls=oc_detail_urls if oc_detail_urls else None,
                    )
                    session.set("detail_html", html)
                    session.set("detail_done", True)
                    _save_html(html)
                except Exception as e:
                    st.error(f"상세페이지 생성 실패: {e}")
                    session.set("detail_done", False)

            if session.get("detail_done"):
                st.toast("상세페이지 생성 완료! outputs/pages/ 에 저장되었습니다.", icon="📄")
                st.rerun()

        html_content: str = session.get("detail_html") or ""
        if html_content:
            _render_preview(html_content)
            st.divider()
            _render_download_section(html_content)
        else:
            # 안내 카드
            st.markdown(
                """<div style="background:#1A1A2E;border:1px dashed #2D2D4E;border-radius:12px;
                padding:3rem;text-align:center;color:#4B5563;">
                <div style="font-size:2.5rem;margin-bottom:1rem;">📱</div>
                <div style="font-size:0.9rem;">왼쪽에서 설정을 완료하고<br>
                <strong style="color:#7C3AED;">상세페이지 생성</strong> 버튼을 눌러주세요.</div>
                </div>""",
                unsafe_allow_html=True,
            )


# ── 미리보기 렌더러 ────────────────────────────────────────────

def _render_preview(html_content: str) -> None:
    """CSS 주입 방식으로 phone frame 시뮬레이션 (중첩 iframe 없이)."""
    phone_css = """<style id="_pf">
html { background:#0E0E1A; min-height:100%; }
body {
  max-width:430px !important;
  width:430px !important;
  margin:20px auto !important;
  border:2px solid #2D2D4E !important;
  border-radius:0 0 16px 16px !important;
  box-shadow:0 0 50px rgba(124,58,237,0.25) !important;
  overflow-x:hidden !important;
  padding-top:0 !important;
}
</style>"""
    notch = (
        '<div style="background:#000;width:430px;margin:20px auto 0;'
        'border:2px solid #2D2D4E;border-bottom:none;border-radius:16px 16px 0 0;'
        'height:28px;display:flex;align-items:center;justify-content:center;">'
        '<div style="width:80px;height:6px;background:#1a1a1a;border-radius:3px;"></div>'
        '</div>'
    )
    modified = html_content.replace("</head>", phone_css + "</head>", 1)
    modified = modified.replace("<body>", "<body>" + notch, 1)
    components.html(modified, height=900, scrolling=True)


def _render_download_section(html_content: str) -> None:
    col_dl, col_copy = st.columns(2)
    with col_dl:
        st.download_button(
            label="⬇️ HTML 파일 다운로드",
            data=html_content.encode("utf-8"),
            file_name=f"detail_page_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            use_container_width=True,
        )
    with col_copy:
        if st.button("📋 HTML 코드 복사", use_container_width=True):
            st.code(html_content[:500] + "\n...(생략)...", language="html")
            st.toast("아래 코드 블록에서 복사하세요.", icon="📋")


def _save_html(html_content: str) -> None:
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = _PAGES_DIR / f"detail_{ts}.html"
    try:
        path.write_text(html_content, encoding="utf-8")
    except Exception:
        pass
