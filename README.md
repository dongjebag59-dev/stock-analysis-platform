# 📈 주식 분석 통합 플랫폼

국내외 8개 시장을 지원하는 Streamlit 기반 주식 분석 웹 애플리케이션입니다.  
종목 선택 즉시 인터랙티브 차트가 자동 갱신되며, 기술적 지표 분석과 프리미엄 구독 모델을 포함합니다.

🌐 **라이브 데모**: [stock-analysis-dongjebag.streamlit.app](https://stock-analysis-platform-yowxfjcpgtwnpthddwvwrt.streamlit.app)

---

## ✨ 주요 기능

### 🌏 시장 및 종목
- **국내**: KOSPI, KOSDAQ, KONEX
- **해외**: 미국(NYSE/NASDAQ), 일본(TSE), 홍콩(HKEX), 베트남(HOSE)
- 시장별 통화 자동 적용 (₩, $, ¥, HK$, ₫)
- 사이드바 상단 **KOSPI · KOSDAQ · S&P500 실시간 현황** (등락률 포함)
- **종목 검색** — 이름/코드 부분일치 필터 (예: `삼성`, `005930`)
- 즐겨찾기 저장·삭제·JSON 내보내기/가져오기

### 📉 인터랙티브 차트 (Plotly)
- **캔들스틱 · OHLC · 라인** 차트 — 줌, 호버, 패닝 지원
- **이동평균선** — MA5 · MA20 · MA60 · MA120 (조합 선택 가능)
- **볼린저 밴드** — 20일 이동평균 ±2σ
- **MACD 매매 신호** — 골든·데드크로스 마커 오버레이
- **52주 신고가 / 신저가 수평선** — 실선(고가) / 점선(저가)
- **거래량 서브플롯** — 메인 차트 하단 패널, Vol MA5 포함
- **빠른 기간 버튼** — 1M · 3M · 6M · 1Y · 3Y 원클릭 설정
- 차트 이미지 저장 시 **종목코드 + 날짜** 자동 파일명
- 데이터 기준일(최근 거래일) 차트 상단에 표시

### 📊 탭별 분석 기능

| 탭 | 내용 |
|----|------|
| **요약** | 기간 수익률, 52주 고·저·범위 지표, PER/EPS/PBR/BPS (한국 주식), RSI 신호 |
| **뉴스** | Google News 검색결과 + WSJ · Bloomberg · Reuters 링크 |
| **거래량** | 평균/최대 거래량, 최대 거래량 날짜, 이상 거래량 경고 |
| **투자 지표** 🔒 | RSI 차트 & 과열/과매도 신호, MACD 차트 & 신호, 연환산 변동성, 기간별 수익률 |
| **종목 비교** 🔒 | 최대 3종목 정규화 수익률 비교 |
| **포트폴리오** 🔒 | 최대 3종목 비중 시뮬레이터, CSV 다운로드, 실제 매수일 표시 |

### 🔒 프리미엄 플랜

| 기능 | 무료 | 프리미엄 |
|------|:----:|:--------:|
| 기본 차트 & 요약 | ✅ | ✅ |
| 뉴스 & 거래량 분석 | ✅ | ✅ |
| 관심종목 저장 | 최대 3개 | 무제한 |
| RSI · MACD 지표 | ❌ | ✅ |
| 종목 비교 (최대 3개) | ❌ | ✅ |
| 포트폴리오 수익 시뮬레이터 | ❌ | ✅ |

결제는 **카카오페이** 연동 (`.streamlit/secrets.toml`에 키 설정 시 활성화, 미설정 시 데모 모드)

### 🔗 링크 공유 & QR 코드
사이드바 하단 **링크 공유** 섹션에서 현재 종목 URL 복사 및 QR 코드 다운로드

```
?market=KOSPI&code=005930
```

---

## 🛠️ 기술 스택

| 분류 | 라이브러리 / 서비스 |
|------|-------------------|
| 프레임워크 | Streamlit 1.35+ |
| 데이터 수집 | FinanceDataReader, BeautifulSoup4 (네이버 금융 스크래핑) |
| 차트 | Plotly (make_subplots, 인터랙티브) |
| 데이터 처리 | pandas, numpy |
| 기타 | qrcode, requests |
| 자동화 | GitHub Actions (종목 목록 주간 자동 업데이트) |
| 배포 | Streamlit Cloud, Docker / Docker Compose |

---

## 🚀 실행 방법

### 방법 1 — 배치 파일 (Windows)
```
start_all.bat
```
더블클릭 한 번으로 서버가 자동 시작됩니다.

### 방법 2 — 수동 실행
```bash
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
├── app.py                   # 주식 분석 메인 앱
├── portfolio.py             # 포트폴리오 랜딩 페이지
├── common.py                # 공통 유틸 & 카카오페이 함수
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── start_all.bat            # Windows 일괄 실행 스크립트
├── scripts/
│   └── update_listings.py   # 종목 목록 갱신 스크립트
├── .github/
│   └── workflows/
│       └── update_listings.yml  # 주간 자동 업데이트 (GitHub Actions)
├── resources/
│   ├── listings/            # 8개 시장 정적 CSV + meta.json
│   ├── NanumSquareR.ttf
│   └── lottie_*.json
└── .streamlit/
    ├── config.toml          # 테마 설정
    └── secrets.toml         # API 키 (git 제외)
```

---

## 🔄 종목 목록 자동 업데이트

KRX API는 주말·공휴일에 접근이 불안정합니다.  
`resources/listings/` 에 정적 CSV를 저장해 두고, **GitHub Actions가 매주 월요일** 자동으로 갱신합니다.  
사이드바의 `📅 종목 목록 기준일:` 캡션에서 최근 갱신일을 확인할 수 있습니다.

수동 갱신이 필요한 경우:
```bash
python scripts/update_listings.py
```

---

## 🔑 카카오페이 결제 설정 (선택)

`.streamlit/secrets.toml` 파일을 생성하고 아래 내용을 추가합니다:

```toml
KAKAO_ADMIN_KEY = "여기에_카카오_Admin_Key_입력"
APP_BASE_URL = "https://your-app.streamlit.app"
```

키가 없으면 자동으로 데모 모드로 동작합니다.

---

## 📬 Contact

- GitHub: [@dongjebag59-dev](https://github.com/dongjebag59-dev)
- Email: dongjebag59@gmail.com
