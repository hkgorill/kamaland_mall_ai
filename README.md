# ✨ KAMALAND_MALL AI

AI 기반 무재고 위탁 판매 자동화 솔루션

상품 소싱 키워드 발굴부터 마케팅 이미지 생성, 카피라이팅, 상세페이지 완성까지  
전체 판매 준비 워크플로우를 자동화합니다.

---

## 주요 기능

| 단계 | 기능 | AI 모델 |
|------|------|---------|
| 🔍 소싱 | 트렌드 키워드 + 판매 포인트 자동 추출 | Gemini 2.5 Flash |
| 🖼️ 이미지 | 5가지 배경 컨셉 마케팅 이미지 생성 | Gemini 2.5 Flash Image |
| ✍️ 카피 | PAS+AIDA 프레임워크 후킹 문구 생성 | Gemini 2.5 Flash |
| 📄 상세페이지 | 모바일 상세페이지 HTML 자동 조립 | - |

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
- 상품 사진 업로드 → **배경 제거 미리보기** 로 결과 확인
- **이미지 5장 생성하기** 클릭 (병렬 처리로 약 20~40초 소요)
- 생성된 이미지는 `outputs/images/` 에 자동 저장

### 3️⃣ 상세페이지 후킹 문구
- 상품 정보 직접 입력 또는 URL 자동 추출 (네이버·쿠팡·11번가 등)
- **후킹 문구 생성하기** 클릭
- **편집 모드** 토글로 아이콘·제목·설명 개별 수정 가능

### 4️⃣ 상세페이지 생성
- 대표 이미지 선택 → 카피 확인 → **상세페이지 생성 및 미리보기**
- 모바일 프레임(430px)으로 실제 쇼핑몰 화면 미리보기
- HTML 파일 다운로드 후 쇼핑몰에 직접 업로드

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
│   ├── image_gen.py        # 이미지 생성
│   ├── copywriting.py      # 후킹 문구
│   └── detail_page.py      # 상세페이지
│
├── services/               # AI·외부 API 래퍼
│   ├── gemini_service.py   # 텍스트 생성 (Gemini 2.5 Flash)
│   ├── image_service.py    # 이미지 생성 (Gemini + rembg)
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
GEMINI_TEXT_MODEL  = "gemini-2.5-flash"           # 텍스트 생성
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"      # 이미지 편집
IMAGEN_MODEL       = "imagen-4.0-fast-generate-001" # 독립 이미지 생성
IMAGE_GEN_MAX_WORKERS = 3                           # 병렬 생성 수
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

## 라이선스

이 프로젝트는 개인·상업적 목적으로 자유롭게 사용할 수 있습니다.
