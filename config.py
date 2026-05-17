import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# 모델명 (변경 시 여기서만 수정)
GEMINI_TEXT_MODEL  = "gemini-2.5-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"      # 이미지 입력→출력 (배경 교체)
IMAGEN_MODEL       = "imagen-4.0-fast-generate-001" # 텍스트→이미지 (독립 생성)

# 이미지 생성 병렬 처리 워커 수
IMAGE_GEN_MAX_WORKERS = 3

APP_TITLE = "KAMALAND_MALL AI"
APP_ICON = "✨"

# 이미지 생성 컨셉 3가지 (API 과금 절감용; 나머지 2장은 Gemini 웹/앱에서 직접 생성 후 업로드)
IMAGE_CONCEPTS = [
    ("미니멀 스튜디오", "clean white minimalist studio background, soft diffused lighting, product photography"),
    ("야외 자연광", "outdoor natural light, warm golden bokeh background, lifestyle product photography"),
    ("다크 럭셔리", "dark black background, dramatic spot lighting, luxury high-end product photography"),
]

# 소싱 프롬프트
SOURCING_SYSTEM_PROMPT = """당신은 국내 온라인 쇼핑몰 전문 MD입니다.
현재 트렌드, 계절성, SNS 바이럴 가능성을 종합적으로 고려하여
위탁 판매에 최적화된 소형/생필품 아이템 키워드를 추천합니다."""

# 카피라이팅 프롬프트
COPYWRITING_SYSTEM_PROMPT = """당신은 KAMALAND_MALL의 시니어 마케터입니다.
PAS(Problem-Agitation-Solution)와 AIDA(Attention-Interest-Desire-Action) 복합 프레임워크를 활용하여
소비자의 구매 욕구를 강하게 자극하는 카피라이팅을 작성합니다.
간결하고 강렬하며 한국 소비자에게 친숙한 표현을 사용합니다."""
