# 📈 주식 분석 통합 플랫폼

국내외 8개 시장을 지원하는 Streamlit 기반 주식 분석 웹 애플리케이션입니다.  
PC 버전과 모바일 버전을 동시에 제공하며, 기술적 지표 분석과 프리미엄 구독 모델을 포함합니다.

---

## 🖥️ 화면 구성

| 구분 | URL | 설명 |
|------|-----|------|
| 포트폴리오 | `http://localhost:8500` | 프로젝트 소개 랜딩 페이지 |
| PC 버전 | `http://localhost:8501` | 와이드 레이아웃, 전체 기능 |
| 모바일 버전 | `http://localhost:8502` | 터치 최적화, 간소화 UI |

---

## ✨ 주요 기능

### 📊 시장 및 종목
- **국내**: KOSPI, KOSDAQ, KONEX
- **해외**: 미국(NYSE/NASDAQ), 일본(TSE), 홍콩(HKEX), 베트남(HOSE)
- 시장별 통화 자동 적용 (₩, $, ¥, HK$, ₫)
- 즐겨찾기 종목 저장 및 빠른 전환

### 📉 기술적 지표
- **캔들스틱 차트** (mplfinance)
- **RSI** — 14일 기준 과매수/과매도 구간 표시
- **MACD** — EMA 12/26/9 기반 추세 신호
- **볼린저 밴드** — 20일 이동평균 ±2σ

### 🔒 프리미엄 기능 (구독 모델)
| 기능 | 무료 | 프리미엄 |
|------|:----:|:--------:|
| 기본 차트 & 요약 | ✅ | ✅ |
| 뉴스 & 거래량 분석 | ✅ | ✅ |
| 투자 지표 (ROE, PER 등) | ❌ | ✅ |
| 종목 비교 (최대 5개) | ❌ | ✅ |
| 포트폴리오 수익 시뮬레이터 | ❌ | ✅ |

### 📱 QR 코드
- 로컬 IP 자동 감지 → 같은 Wi-Fi 내 모바일 기기에서 바로 접속 가능
- PC 버전 사이드바에서 모바일 QR 코드 제공

---

## 🛠️ 기술 스택

| 분류 | 라이브러리 |
|------|-----------|
| 프레임워크 | Streamlit 1.51 |
| 데이터 수집 | FinanceDataReader |
| 차트 | mplfinance, matplotlib, plotly |
| 분석 | pandas, numpy, scikit-learn |
| 기타 | qrcode, folium, wordcloud, soynlp |
| 배포 | Docker, Docker Compose |

---

## 🚀 실행 방법

### 방법 1 — 배치 파일 (Windows)
```
start_all.bat
```
더블클릭 한 번으로 3개 서버가 자동 시작됩니다.

### 방법 2 — 수동 실행
```bash
# 포트폴리오 페이지
streamlit run portfolio.py --server.port 8500

# PC 버전
streamlit run app.py --server.port 8501

# 모바일 버전
streamlit run app_mobile.py --server.port 8502
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
├── app.py              # PC 버전 메인 앱
├── app_mobile.py       # 모바일 버전 앱
├── portfolio.py        # 포트폴리오 랜딩 페이지
├── requirements.txt    # 패키지 목록
├── Dockerfile
├── docker-compose.yml
├── start_all.bat       # Windows 일괄 실행 스크립트
├── resources/
│   ├── NanumSquareR.ttf        # 한글 폰트
│   ├── background_*.png        # 배경 이미지
│   └── lottie_*.json           # 애니메이션
└── .streamlit/
    └── config.toml             # 테마 설정
```

---

## 📬 Contact

- GitHub: [@dongjebag59-dev](https://github.com/dongjebag59-dev)
- Email: dongjebag59@gmail.com
