# 📈 주식 분석 통합 플랫폼

국내외 8개 시장을 지원하는 Streamlit 기반 주식 분석 웹 애플리케이션입니다.  
기술적 지표 분석과 포트폴리오 시뮬레이터, 카카오페이 연동 프리미엄 구독 모델을 포함합니다.

🌐 **라이브 데모**: [stock-analysis-dongjebag.streamlit.app](https://stock-analysis-platform-yowxfjcpgtwnpthddwwrt.streamlit.app)

---

## 🖥️ 화면 구성

| 구분 | URL | 설명 |
|------|-----|------|
| 포트폴리오 | `http://localhost:8500` | 프로젝트 소개 랜딩 페이지 |
| 주식 분석 앱 | `http://localhost:8501` | 전체 기능 메인 앱 |

---

## ✨ 주요 기능

### 📊 시장 및 종목
- **국내**: KOSPI, KOSDAQ, KONEX
- **해외**: 미국(NYSE/NASDAQ), 일본(TSE), 홍콩(HKEX), 베트남(HOSE)
- 시장별 통화 자동 적용 (₩, $, ¥, HK$, ₫)
- 즐겨찾기 종목 저장 및 빠른 전환

### 📉 기술적 지표
- **캔들스틱 차트** (mplfinance) — candle / ohlc / line 타입 선택
- **RSI** — 14일 기준 과매수/과매도 구간 표시 및 신호 해석
- **MACD** — EMA 12/26/9 기반 추세 신호
- **볼린저 밴드** — 20일 이동평균 ±2σ

### 🔒 프리미엄 기능 (구독 모델)
| 기능 | 무료 | 프리미엄 |
|------|:----:|:--------:|
| 기본 차트 & 요약 | ✅ | ✅ |
| 뉴스 & 거래량 분석 | ✅ | ✅ |
| 관심종목 저장 | 최대 3개 | 무제한 |
| RSI · MACD 지표 | ❌ | ✅ |
| 종목 비교 (최대 3개) | ❌ | ✅ |
| 포트폴리오 수익 시뮬레이터 | ❌ | ✅ |

결제는 **카카오페이** 연동 (`.streamlit/secrets.toml`에 `KAKAO_ADMIN_KEY` 설정 시 활성화)

---

## 🛠️ 기술 스택

| 분류 | 라이브러리 |
|------|-----------|
| 프레임워크 | Streamlit |
| 데이터 수집 | FinanceDataReader |
| 차트 | mplfinance, matplotlib |
| 데이터 처리 | pandas, numpy |
| 기타 | qrcode, beautifulsoup4, requests |
| 배포 | Docker, Docker Compose, Streamlit Cloud |

---

## 🚀 실행 방법

### 방법 1 — 배치 파일 (Windows)
```
start_all.bat
```
더블클릭 한 번으로 2개 서버가 자동 시작됩니다.

### 방법 2 — 수동 실행
```bash
# 포트폴리오 페이지
streamlit run portfolio.py --server.port 8500

# 주식 분석 앱
streamlit run app.py --server.port 8501
```

### 방법 3 — Docker Compose
```bash
docker compose up -d
```

---

## 📦 설치

```bash
pip install -r requirements.txt
```

> Python 3.11 이상 권장

---

## 📁 프로젝트 구조

```
My First Project/
├── app.py              # 주식 분석 메인 앱 (포트 8501)
├── portfolio.py        # 포트폴리오 랜딩 페이지 (포트 8500)
├── common.py           # 공통 유틸 & 카카오페이 함수
├── requirements.txt    # 패키지 목록
├── Dockerfile
├── docker-compose.yml
├── start_all.bat       # Windows 일괄 실행 스크립트
├── resources/
│   ├── NanumSquareR.ttf        # 한글 폰트
│   ├── background_*.png        # 배경 이미지
│   └── lottie_*.json           # 애니메이션
└── .streamlit/
    ├── config.toml             # 테마 설정
    └── secrets.toml            # API 키 (git 제외)
```

---

## 🔑 카카오페이 결제 설정 (선택)

`.streamlit/secrets.toml` 파일을 생성하고 아래 내용을 추가합니다:

```toml
KAKAO_ADMIN_KEY = "여기에_카카오_Admin_Key_입력"
APP_BASE_URL = "https://your-app.streamlit.app"  # 배포 URL
```

키가 없으면 자동으로 데모 모드로 동작합니다.

---

## 📬 Contact

- GitHub: [@dongjebag59-dev](https://github.com/dongjebag59-dev)
- Email: dongjebag59@gmail.com
