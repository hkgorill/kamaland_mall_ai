# ✨ KAMALAND_MALL AI

AI 기반 무재고 위탁 판매 자동화 솔루션

상품 소싱 키워드 발굴부터 마케팅 이미지 생성, 카피라이팅, 상세페이지 완성까지  
전체 판매 준비 워크플로우를 자동화합니다.

---

## 주요 기능

| 단계 | 기능 | AI 모델 |
|------|------|---------|
| 🔍 소싱 | 트렌드 키워드 + 판매 포인트 자동 추출 | Gemini 2.5 Flash |
| 🖼️ 이미지 | AI 자동 생성(3장) + Gemini 웹/앱 직접 생성 후 업로드(최대 5장) | Gemini 2.5 Flash Image |
| ✍️ 카피 | PAS+AIDA 프레임워크 후킹 문구 생성 | Gemini 2.5 Flash |
| 📄 상세페이지 | 모바일 상세페이지 HTML 자동 조립 + 미리보기 | - |

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone <repo-url>
cd kamaland_mall_ai
```

### 2. 가상환경 생성 및 패키지 설치

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> rembg 첫 실행 시 u2net 모델(~176MB)을 자동 다운로드합니다.

### 3. API Key 설정

[Google AI Studio](https://aistudio.google.com/apikey)에서 API Key를 발급받습니다.

```bash
cp .env.example .env
```

`.env` 파일을 열어 API Key를 입력합니다:

```
GOOGLE_API_KEY=AIzaSy...your_key_here
```

> 이미지 생성(`gemini-2.5-flash-image`) 기능은 **유료 API Key** 가 필요합니다.

### 4. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

---

## 사용 방법

### 권장 워크플로우

```
대시보드 → 소싱 → 이미지 만들기 → 후킹 문구 → 상세페이지 생성
```

### 1️⃣ 오늘 뭐 팔지? (소싱)
- 추출할 키워드 수 입력 후 **키워드 추출하기** 클릭
- 추가 조건 선택으로 원하는 카테고리 필터링 가능
- 카드에서 원하는 키워드 체크 후 **선택 완료** → 후킹 문구로 자동 연동

### 2️⃣ 대표 이미지 만들기

이미지 생성은 **API 자동 생성**과 **직접 업로드** 두 가지 방법을 조합합니다.

**Step 1 — 원본 이미지 업로드**
- 상품 사진 업로드 → **배경 제거 미리보기** 로 결과 확인

**Step 2 — AI 자동 생성 (API 과금, 3가지 컨셉)**
- **이미지 3장 자동 생성하기** 클릭 (병렬 처리로 약 15~30초 소요)
- 생성 컨셉: 미니멀 스튜디오 / 야외 자연광 / 다크 럭셔리
- 생성된 이미지는 `outputs/images/` 에 자동 저장

**Step 3 — Gemini 웹/앱 직접 생성 후 업로드 (무료)**
- [gemini.google.com](https://gemini.google.com) 또는 Gemini 앱에서 상품 이미지를 첨부한 뒤, 앱 화면에 표시된 **5가지 복사용 프롬프트** 중 하나를 붙여넣어 이미지를 생성합니다.
- 생성된 이미지를 저장 후 업로더에 등록 (최대 5장)
- AI 자동 생성(3장) + 직접 업로드(최대 5장) = 최대 **8장** 활용 가능

> **Gemini 웹/앱 무료 한도:** Basic 20회/일 · AI Plus 50회/일 · Pro 100회/일

### 3️⃣ 상세페이지 후킹 문구
- 상품 정보 직접 입력 또는 URL 자동 추출 (네이버·쿠팡·11번가 등)
- **후킹 문구 생성하기** 클릭
- **편집 모드** 토글로 아이콘·제목·설명 개별 수정 가능

### 4️⃣ 상세페이지 생성
- AI 자동 생성 이미지 또는 직접 업로드 이미지 중 대표 이미지 선택
- 카피 확인 → **상세페이지 생성 및 미리보기**
- 모바일 프레임(430px)으로 실제 쇼핑몰 화면 미리보기
- HTML 파일 다운로드 후 쇼핑몰에 직접 업로드

---

## API 비용 구조

### Gemini API 과금 발생 시점

| 단계 | 모델 | 과금 여부 |
|------|------|----------|
| 소싱 키워드 추출 | gemini-2.5-flash | 과금 (소량) |
| 후킹 문구 생성 | gemini-2.5-flash | 과금 (소량) |
| 이미지 자동 생성 (3장) | gemini-2.5-flash-image | 과금 (주요 비용) |
| 상세페이지 HTML 조립 | — | 무료 (템플릿 렌더링) |
| Gemini 웹/앱 직접 생성 | — | 무료 (웹/앱 한도 내) |

### 워크플로우 1회 예상 비용

```
입력 토큰  ~2,000개  × $0.15/1M ≈ $0.0003
출력 토큰  ~7,000개  × $0.60/1M ≈ $0.0042
Thinking         0   (비활성화)  = $0
─────────────────────────────────────────
합계                             ≈ $0.005
```

> thinking 토큰($3.50/1M)은 `thinking_budget=0` 설정으로 비활성화되어 있습니다.  
> 활성화 시 워크플로우 1회 비용이 $0.12 수준으로 증가합니다.

---

## 프로젝트 구조

```
kamaland_mall_ai/
├── app.py                  # 메인 진입점·사이드바 라우팅
├── config.py               # 모델명·프롬프트 상수
├── requirements.txt
├── .env                    # API Key (git 제외)
│
├── views/                  # 페이지 모듈
│   ├── dashboard.py        # 대시보드
│   ├── sourcing.py         # 소싱 키워드
│   ├── image_gen.py        # 이미지 생성 (Step1~3)
│   ├── copywriting.py      # 후킹 문구
│   └── detail_page.py      # 상세페이지
│
├── services/               # AI·외부 API 래퍼
│   ├── gemini_service.py   # 텍스트 생성 (Gemini 2.5 Flash, thinking 비활성화)
│   ├── image_service.py    # 이미지 생성 (Gemini + rembg, thinking 비활성화)
│   └── scraper_service.py  # URL 스크래핑
│
├── utils/
│   ├── session.py          # 세션 상태 관리
│   ├── styles.py           # Dark Mode CSS
│   └── html_template.py    # 상세페이지 HTML 빌더
│
├── outputs/                # 생성 결과물 자동 저장 (git 제외)
│   ├── images/             # 생성된 상품 이미지
│   └── pages/              # 생성된 상세페이지 HTML
│
└── tests/
    ├── test_services.py    # 서비스 단위 테스트
    └── test_e2e.py         # E2E 통합 테스트
```

---

## 설정 변경

`config.py` 에서 모델명 및 이미지 컨셉을 수정할 수 있습니다:

```python
GEMINI_TEXT_MODEL     = "gemini-2.5-flash"            # 텍스트 생성
GEMINI_IMAGE_MODEL    = "gemini-2.5-flash-image"       # 이미지 편집
IMAGEN_MODEL          = "imagen-4.0-fast-generate-001" # 독립 이미지 생성
IMAGE_GEN_MAX_WORKERS = 3                              # 병렬 생성 수

# AI 자동 생성 컨셉 (기본 3가지)
IMAGE_CONCEPTS = [
    ("미니멀 스튜디오", "clean white minimalist studio background ..."),
    ("야외 자연광",     "outdoor natural light, warm golden bokeh ..."),
    ("다크 럭셔리",     "dark black background, dramatic spot lighting ..."),
]
```

Thinking 토큰 비용이 걱정되는 경우 `services/gemini_service.py` 에서 확인:

```python
# 현재 설정 (비활성화 — 비용 절감 모드)
thinking_config=types.ThinkingConfig(thinking_budget=0)

# 품질 우선이 필요한 경우 소량 허용 (예: 1024 토큰)
thinking_config=types.ThinkingConfig(thinking_budget=1024)
```

---

## 테스트 실행

```bash
# 서비스 단위 테스트
python tests/test_services.py

# E2E 통합 테스트
python tests/test_e2e.py
```

---

## 요구 사항

- Python 3.11+
- Google AI Studio API Key (유료 플랜 권장)
- 인터넷 연결 필수 (AI API 호출)
- 저장 공간: 이미지 파일 당 ~1MB

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-17 | Phase 1~5: 전체 기능 초기 구현 완료 |
| 2026-05-17 | API 비용 최적화: thinking 토큰 비활성화 (~96% 절감) |
| 2026-05-17 | 이미지 전략 변경: AI 3장 + Gemini 웹/앱 직접 생성 수동 업로드 추가 |
| 2026-05-17 | 모바일 미리보기 수정: 중첩 iframe → CSS 주입 방식으로 전환 |

---

## 라이선스

이 프로젝트는 개인·상업적 목적으로 자유롭게 사용할 수 있습니다.
