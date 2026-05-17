import base64
from PIL import Image
import io


def _image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def build_detail_page_html(
    main_title: str,
    sub_title: str,
    key_points: list[dict],
    cta_text: str,
    hero_image: Image.Image | None = None,
    extra_images: list[Image.Image] | None = None,
) -> str:
    hero_html = ""
    if hero_image:
        b64 = _image_to_base64(hero_image)
        hero_html = f'<img src="data:image/png;base64,{b64}" style="width:100%;display:block;" alt="대표이미지">'

    extra_html = ""
    if extra_images:
        for img in extra_images:
            b64 = _image_to_base64(img)
            extra_html += f'<img src="data:image/png;base64,{b64}" style="width:100%;display:block;margin-bottom:4px;" alt="추가이미지">'

    points_html = ""
    for pt in key_points:
        icon = pt.get("icon", "✅")
        headline = pt.get("headline", "")
        desc = pt.get("description", "")
        points_html += f"""
        <div class="point-card">
            <span class="point-icon">{icon}</span>
            <div>
                <div class="point-headline">{headline}</div>
                <div class="point-desc">{desc}</div>
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #111;
    color: #eee;
    max-width: 430px;
    margin: 0 auto;
  }}
  .hero {{ background: #000; }}
  .content {{ padding: 24px 16px; }}
  .main-title {{
    font-size: 1.6rem;
    font-weight: 800;
    line-height: 1.3;
    margin-bottom: 8px;
    background: linear-gradient(135deg, #a78bfa, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .sub-title {{
    font-size: 1rem;
    color: #aaa;
    margin-bottom: 28px;
    line-height: 1.5;
  }}
  .points-section {{ margin-bottom: 28px; }}
  .section-label {{
    font-size: 0.75rem;
    color: #7c3aed;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 12px;
  }}
  .point-card {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #1a1a2e;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 10px;
    border: 1px solid #2d2d4e;
  }}
  .point-icon {{ font-size: 1.5rem; flex-shrink: 0; }}
  .point-headline {{ font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }}
  .point-desc {{ font-size: 0.82rem; color: #aaa; line-height: 1.5; }}
  .extra-images {{ background: #000; }}
  .cta-section {{
    padding: 20px 16px 40px;
    text-align: center;
  }}
  .cta-btn {{
    display: block;
    width: 100%;
    padding: 16px;
    background: linear-gradient(135deg, #7c3aed, #5b21b6);
    color: #fff;
    font-size: 1.1rem;
    font-weight: 700;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    letter-spacing: 0.02em;
  }}
</style>
</head>
<body>
  <div class="hero">{hero_html}</div>
  <div class="content">
    <div class="main-title">{main_title}</div>
    <div class="sub-title">{sub_title}</div>
    <div class="points-section">
      <div class="section-label">핵심 포인트</div>
      {points_html}
    </div>
  </div>
  <div class="extra-images">{extra_html}</div>
  <div class="cta-section">
    <button class="cta-btn">{cta_text}</button>
  </div>
</body>
</html>"""
