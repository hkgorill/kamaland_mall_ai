# KAMALAND_MALL AI 개발 계획서

> 작성일: 2026-05-17  
> 기반 문서: `docs/kamaland_mall_ai_spec.md`

---

## 1. 기존 스펙 검토 및 개선 포인트

### 1.1 모델 버전 업그레이드

| 항목 | 기존 스펙 | 권장 사항 | 이유 |
|------|----------|----------|------|
| 텍스트 생성 | Gemini 1.5 Pro | **Gemini 2.5 Flash** | 더 빠르고 저렴하며 추론 품질 향상. 장문 컨텍스트 지원(1M 토큰) |
| 이미지 생성 | Imagen (Inpainting) | **Gemini 2.0 Flash (이미지 생성)** + Imagen 3 병행 | `gemini-2.0-flash-exp`가 직접 이미지 생성 지원. Inpainting은 Vertex AI 필요로 로컬 환경에서 구현이 복잡함 → 배경 제거 후 재합성 방식으로 대체 |
| 이미지 배경 분리 | 미명시 | **`rembg` 라이브러리** | 로컬에서 무료로 배경 제거 가능, Imagen과 연계하여 합성 |

### 1.2 아키텍처 개선

**기존 문제점:**
- 단일 파일 구조로 확장성 부족
- 페이지 간 데이터 전달 방식 미명시 (st.session_state 전략 없음)
- URL 스크래핑 로직 미명시 (3.3 기능)
- 대시보드 기능 명세 없음
- API Key 관리 방식 미명시
- 생성물 저장/내보내기 기능 없음

**개선 방향:**
- 멀티 파일 모듈화 구조 (pages/, services/, utils/)
- 명확한 세션 상태(session_state) 설계로 워크플로우 데이터 흐름 보장
- `.env` 기반 설정 관리
- 생성 결과물 로컬 저장 기능

### 1.3 워크플로우 개선

기존 스펙은 각 기능이 독립적으로 동작하는 구조인데, 실제 판매 업무 흐름은 아래처럼 연결됩니다:

```
소싱 키워드 선택 → 상품 이미지 업로드/생성 → 후킹 문구 생성 → 상세페이지 통합
```

이 흐름을 **세션 상태로 이어주는 사이드바 워크플로우 진행도 UI** 추가를 권장합니다.

---

## 2. 최종 기술 스택

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| 언어 | Python | 3.11+ | 전체 |
| UI 프레임워크 | Streamlit | 최신 | 웹 앱 |
| AI (텍스트) | Google Generative AI SDK | 최신 | Gemini 2.5 Flash 호출 |
| AI (이미지) | Google Generative AI SDK | 최신 | Gemini 2.0 Flash 이미지 생성 |
| 이미지 처리 | Pillow, rembg | 최신 | 배경 제거 및 이미지 합성 |
| 웹 스크래핑 | requests, BeautifulSoup4 | 최신 | 상품 URL 파싱 |
| 설정 관리 | python-dotenv | 최신 | API Key 환경변수 관리 |
| 데이터 모델 | Pydantic | v2 | 구조화된 AI 응답 파싱 |

---

## 3. 프로젝트 디렉토리 구조

```
kamaland_mall_ai/
├── app.py                        # 메인 진입점 (사이드바 네비게이션, 세션 초기화)
├── .env                          # API Keys (git 제외)
├── .env.example                  # 환경변수 샘플
├── requirements.txt
├── config.py                     # 전역 설정 (모델명, 프롬프트 상수 등)
│
├── pages/                        # 각 페이지 모듈
│   ├── dashboard.py              # 대시보드
│   ├── sourcing.py               # 오늘 뭐 팔지? (소싱)
│   ├── image_gen.py              # 대표 이미지 만들기
│   ├── copywriting.py            # 상세페이지 후킹 문구
│   └── detail_page.py            # 상세페이지 생성 및 미리보기
│
├── services/                     # AI/외부 API 래퍼
│   ├── gemini_service.py         # 텍스트 생성 (Gemini 2.5 Flash)
│   ├── image_service.py          # 이미지 생성 + 배경 처리
│   └── scraper_service.py        # URL 스크래핑
│
├── utils/
│   ├── session.py                # session_state 키 상수 및 초기화 헬퍼
│   └── html_template.py          # 상세페이지 HTML/CSS 템플릿 생성기
│
├── outputs/                      # 생성 결과물 로컬 저장 (git 제외)
│   ├── images/
│   └── pages/
│
└── docs/
    ├── kamaland_mall_ai_spec.md
    └── dev_plan.md               # 본 문서
```

---

## 4. 세션 상태(Session State) 설계

페이지 간 데이터 흐름을 보장하기 위한 세션 키 정의:

```python
# utils/session.py 에서 관리
SESSION_KEYS = {
    "sourcing_keywords": [],        # 소싱 페이지 → 후킹문구 페이지 연동
    "uploaded_image": None,         # 업로드된 원본 이미지 (bytes)
    "generated_images": [],         # 생성된 이미지 리스트 (PIL.Image)
    "product_info": "",             # 상품 정보 텍스트
    "copy_result": {                # 후킹 문구 결과
        "main_title": "",
        "sub_title": "",
        "key_points": [],
    },
    "selected_image_idx": 0,        # 상세페이지에서 선택한 이미지
}
```

---

## 5. 핵심 기능 상세 설계

### 5.1 대시보드

스펙에 명세 없으므로 실용적으로 구성:
- 오늘의 작업 현황 요약 카드 (세션 상태 기반)
- 워크플로우 진행 단계 표시 (소싱 → 이미지 → 문구 → 상세페이지)
- 빠른 이동 버튼

### 5.2 오늘 뭐 팔지? (소싱)

```python
# 프롬프트 전략
system_prompt = """
당신은 국내 온라인 쇼핑몰 MD 전문가입니다.
현재 트렌드와 계절성을 고려하여 위탁 판매에 적합한 소형/생필품 키워드를 추천합니다.
각 키워드에는 간단한 판매 포인트를 덧붙여 주세요.
"""
```

**개선 포인트:**
- 단순 키워드 리스트 → 키워드 + 판매 포인트 + 예상 타겟 고객 포함
- 선택한 키워드를 세션에 저장하여 후킹 문구 페이지와 연동

### 5.3 대표 이미지 만들기

**기존 스펙의 Inpainting 방식 문제:**
- Google AI Studio Imagen Inpainting은 Vertex AI SDK 필요 → 로컬 개발 복잡
- 대안: `rembg`로 배경 제거 → Gemini 2.0 Flash로 새 배경과 합성 이미지 생성

**구현 전략:**
```
원본 이미지 업로드
    ↓
rembg로 배경 제거 (투명 PNG 추출)
    ↓
Gemini 2.0 Flash에 원본 이미지 + 배경 컨셉 프롬프트 전송
    ↓
5가지 컨셉 이미지 병렬 생성
    ↓
갤러리 렌더링 + 각 이미지 다운로드 버튼
```

**5가지 배경 컨셉:**
1. 미니멀 화이트 스튜디오
2. 고급 호텔/라이프스타일
3. 야외 자연광 (따뜻한 보케)
4. 다크 럭셔리 (검정 배경, 스팟 조명)
5. 플랫레이 (소품 조합)

### 5.4 상세페이지 후킹 문구

**PAS + AIDA 복합 프레임워크 적용:**

```python
system_prompt = """
당신은 KAMALAND_MALL의 전문 마케터입니다. 
PAS(Problem-Agitation-Solution) + AIDA(Attention-Interest-Desire-Action) 복합 프레임워크를 활용합니다.
"""

output_format = """
반드시 아래 JSON 형식으로만 응답하세요:
{
  "main_title": "메인 타이틀 (20자 이내, 강렬한 한 줄)",
  "sub_title": "서브 타이틀 (40자 이내, 문제 공감 또는 혜택 강조)",
  "key_points": [
    {"icon": "이모지", "headline": "소구점 제목", "description": "설명 (2줄 이내)"},
    {"icon": "이모지", "headline": "소구점 제목", "description": "설명 (2줄 이내)"},
    {"icon": "이모지", "headline": "소구점 제목", "description": "설명 (2줄 이내)"}
  ],
  "cta_text": "구매 행동 유도 문구 (예: 지금 바로 경험해보세요!)"
}
"""
```

**개선 포인트:**
- Pydantic으로 AI 응답 파싱 → 파싱 실패 시 명확한 에러 메시지
- URL 입력 시 BeautifulSoup으로 제품명, 설명 자동 추출 후 textarea에 자동 채움
- 소싱 페이지에서 선택한 키워드 자동 연동 옵션

### 5.5 상세페이지 생성

**HTML 템플릿 설계:**
- 모바일 기준 (max-width: 430px) 수직 스크롤 레이아웃
- 섹션 구성: 대표이미지 → 메인타이틀 → 핵심소구점 3개 → 추가 이미지 슬라이더 → CTA 버튼
- `st.components.v1.html`로 미리보기
- 'HTML 복사하기' + 'HTML 파일 다운로드' 기능 제공

---

## 6. 개발 단계 (Phase)

### Phase 1: 프로젝트 기반 구축 (1~2일)

**목표:** 실행 가능한 뼈대 완성

- [ ] 디렉토리 구조 생성
- [ ] `requirements.txt` 작성 및 가상환경 설정
- [ ] `.env` + `config.py` 설정 (API Key, 모델명 상수)
- [ ] `app.py` 기본 구조 (사이드바 네비게이션, 페이지 라우팅)
- [ ] `utils/session.py` 세션 초기화 헬퍼
- [ ] Dark Mode 공통 CSS 스타일 적용
- [ ] Gemini API 연결 테스트 (Hello World 수준)

**완료 기준:** `streamlit run app.py` 실행 시 사이드바 네비게이션이 있는 빈 앱 동작

---

### Phase 2: AI 서비스 레이어 구축 (2~3일)

**목표:** 모든 AI/외부 API 래퍼 완성 및 단독 테스트 통과

- [ ] `services/gemini_service.py`
  - `generate_text(prompt, system_prompt)` 함수
  - `generate_structured(prompt, pydantic_model)` 함수 (JSON 모드)
  - API 오류/재시도 로직 (최대 3회)
- [ ] `services/image_service.py`
  - `remove_background(image_bytes)` → rembg 활용
  - `generate_product_images(image_bytes, concept)` → Gemini 2.0 Flash
- [ ] `services/scraper_service.py`
  - `scrape_product_info(url)` → requests + BS4, User-Agent 위장
  - 주요 쇼핑몰(쿠팡, 네이버 스마트스토어) 파서 우선 지원
- [ ] 각 서비스 단독 테스트 스크립트 작성

**완료 기준:** 각 서비스를 단독 실행하여 AI 응답 확인 가능

---

### Phase 3: 핵심 기능 페이지 구현 (3~4일)

**목표:** 4개 핵심 기능 페이지 완성

- [ ] `pages/sourcing.py` - 소싱 키워드 추출
  - 개수 입력 → 키워드+판매포인트 리스트 출력
  - 키워드 선택 체크박스 → 세션 저장
- [ ] `pages/image_gen.py` - 대표 이미지 생성
  - 파일 업로드 → 배경 제거 미리보기 → 5장 생성 → 갤러리
  - 각 이미지 다운로드 버튼
- [ ] `pages/copywriting.py` - 후킹 문구
  - 텍스트 직접 입력 / URL 스크래핑 탭 전환
  - 결과: 메인타이틀, 서브타이틀, 소구점 3개 카드 형태 출력
  - '수정하기' 인라인 편집 기능
- [ ] `pages/detail_page.py` - 상세페이지 생성
  - 세션 데이터 자동 로드 + 수동 입력 fallback
  - 실시간 미리보기 (모바일 프레임)
  - HTML 다운로드

**완료 기준:** 각 페이지 단독으로 기능 동작 확인

---

### Phase 4: 통합 및 대시보드 (1~2일)

**목표:** 워크플로우 연결 + 대시보드 완성

- [ ] `pages/dashboard.py`
  - 세션 기반 작업 진행 현황 카드
  - 각 단계 바로가기 버튼
  - 오늘 날짜, 환영 메시지
- [ ] 사이드바에 워크플로우 진행률 표시 (단계별 체크마크)
- [ ] 세션 데이터가 다음 페이지에 자동 연동되는 흐름 검증
- [ ] `outputs/` 폴더에 생성물 자동 저장 (이미지, HTML)

**완료 기준:** 소싱 → 이미지 → 문구 → 상세페이지 전체 흐름 연속으로 동작

---

### Phase 5: UX 개선 및 마무리 (1일)

**목표:** 실사용 가능한 완성도

- [ ] 모든 페이지 에러 처리 (`st.error`, `st.warning`) 점검
- [ ] 로딩 스피너 + 진행률 표시 (`st.progress`)
- [ ] `@st.cache_data` 적용으로 동일 입력 재호출 방지
- [ ] `.env.example` 및 간단한 `README.md` 작성
- [ ] 전체 워크플로우 E2E 테스트

---

## 7. 환경 설정

### 필요 API Key

```bash
# .env
GOOGLE_API_KEY=your_gemini_api_key_here
```

Google AI Studio(aistudio.google.com)에서 무료 발급 가능.

### 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### requirements.txt (예정)

```
streamlit>=1.35
google-genai>=1.0          # 최신 Google AI SDK (Gemini 2.x 지원)
python-dotenv
Pillow
rembg                       # 배경 제거
requests
beautifulsoup4
pydantic>=2.0
```

---

## 8. 기술적 주의사항 및 리스크

| 리스크 | 내용 | 대응 방안 |
|--------|------|----------|
| Gemini 이미지 생성 제한 | `gemini-2.0-flash-exp` 이미지 생성은 실험적 기능, API 변경 가능 | Imagen 3 (`imagen-3.0-generate-004`) fallback 준비 |
| rembg 초기 로딩 | 첫 실행 시 모델 다운로드 (~170MB) | `@st.cache_resource`로 모델 1회만 로드 |
| 쇼핑몰 스크래핑 차단 | 쿠팡, 네이버 등 봇 차단 정책 | User-Agent 설정, 실패 시 수동 입력 안내 |
| API 비용 | Gemini 2.5 Flash는 무료 티어 존재 | 무료 한도 초과 시 `st.warning`으로 안내 |
| Streamlit 세션 초기화 | 브라우저 새로고침 시 세션 초기화 | 중요 생성물은 `outputs/` 폴더에 자동 저장 |

---

## 9. 향후 확장 고려사항 (현재 범위 외)

- 상품 자동 등록 (쇼피파이/스마트스토어 API 연동)
- 배치 처리 (여러 상품 동시 처리)
- 히스토리 DB (SQLite) - 생성 이력 관리
- 경쟁사 가격 모니터링

---

## 10. 개발 우선순위 요약

```
Phase 1 (기반) → Phase 2 (서비스) → Phase 3 (기능) → Phase 4 (통합) → Phase 5 (완성)
예상 총 기간: 8~12일 (1인 개발 기준)
```

Phase 3의 각 페이지는 병렬 개발 가능하므로, 2인 이상 시 기간 단축 가능합니다.
