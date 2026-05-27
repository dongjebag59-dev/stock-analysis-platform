
# portfolio.py — 포트폴리오 메인 페이지 (포트 8500)

import streamlit as st
import socket
from io import BytesIO
try:
    import qrcode
    _HAS_QR = True
except ImportError:
    _HAS_QR = False


st.set_page_config(
    page_title="Portfolio | 주식 분석 플랫폼",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 전역 CSS
st.markdown("""
<style>
section[data-testid="stSidebar"] { display: none; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; }
.divider { border: none; border-top: 1px solid #e5e7eb; margin: 2rem 0; }

/* 프로젝트 카드 */
.proj-card {
    background: #fff;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    border-top: 5px solid;
    height: 100%;
}
/* 기술 배지 */
.badge {
    display: inline-block;
    padding: 3px 11px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 700;
    margin: 3px 2px;
    border: 1px solid;
}
/* QR 래퍼 */
.qr-box {
    background: #f9fafb;
    border-radius: 14px;
    padding: 18px 12px;
    text-align: center;
    border: 1px solid #e5e7eb;
}
/* 하이라이트 박스 */
.highlight {
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 0.87rem;
    line-height: 1.6;
    margin-top: 14px;
}
</style>
""", unsafe_allow_html=True)


# ── QR 헬퍼 ──────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

@st.cache_data
def make_qr(url, color="#1a1a2e"):
    if not _HAS_QR:
        return None
    qr = qrcode.QRCode(version=1, box_size=7, border=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=color, back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

_ip       = get_local_ip()
pc_url    = f"http://{_ip}:8501"
mobile_url = f"http://{_ip}:8502"
pc_qr     = make_qr(pc_url,  color="#1a1a2e")
mobile_qr = make_qr(mobile_url, color="#e53e3e")


# ════════════════════════════════════════
# HERO
# ════════════════════════════════════════
st.markdown("""
<div style="text-align:center; padding:56px 0 36px 0;">
  <p style="font-size:.8rem; letter-spacing:5px; text-transform:uppercase;
            color:#9ca3af; margin-bottom:10px;">PORTFOLIO · 2026</p>
  <h1 style="font-size:3rem; font-weight:900; color:#111827;
             line-height:1.15; margin:0;">
    Python Full-Stack<br>
    <span style="background:linear-gradient(90deg,#FF6B6B,#f97316);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
      Developer
    </span>
  </h1>
  <p style="font-size:1.15rem; color:#6b7280; margin-top:14px;">
    AI · 데이터 분석 · 웹 서비스 개발 포트폴리오
  </p>

  <div style="display:flex; justify-content:center; gap:8px;
              flex-wrap:wrap; margin-top:22px;">
    <span style="background:#dbeafe; color:#1d4ed8; padding:5px 14px;
                 border-radius:20px; font-size:.82rem; font-weight:700;">🐍 Python</span>
    <span style="background:#dcfce7; color:#15803d; padding:5px 14px;
                 border-radius:20px; font-size:.82rem; font-weight:700;">⚡ FastAPI</span>
    <span style="background:#f3e8ff; color:#7e22ce; padding:5px 14px;
                 border-radius:20px; font-size:.82rem; font-weight:700;">🌐 Django</span>
    <span style="background:#ffedd5; color:#c2410c; padding:5px 14px;
                 border-radius:20px; font-size:.82rem; font-weight:700;">📊 Streamlit</span>
    <span style="background:#fce7f3; color:#be185d; padding:5px 14px;
                 border-radius:20px; font-size:.82rem; font-weight:700;">🤖 AI / LLM</span>
    <span style="background:#e0f2fe; color:#0369a1; padding:5px 14px;
                 border-radius:20px; font-size:.82rem; font-weight:700;">🐳 Docker</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── 요약 지표 ─────────────────────────────
c1, c2, c3, c4 = st.columns(4)
cards = [
    ("#667eea,#764ba2", "4개", "완성 프로젝트"),
    ("#f093fb,#f5576c", "8개", "지원 주식 마켓"),
    ("#4facfe,#00f2fe", "3개", "AI 모델 활용"),
    ("#43e97b,#38f9d7", "2개", "PC + 모바일 버전"),
]
for col, (grad, num, label) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
<div style="background:linear-gradient(135deg,{grad}); color:white;
            border-radius:14px; padding:22px; text-align:center; margin-bottom:4px;">
  <div style="font-size:2.2rem; font-weight:900; line-height:1;">{num}</div>
  <div style="font-size:.82rem; opacity:.9; margin-top:5px;">{label}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ════════════════════════════════════════
# PROJECT 1 — 주식 분석 통합 플랫폼
# ════════════════════════════════════════
st.markdown("## 📈 1차 프로젝트 &nbsp; 주식 분석 통합 플랫폼")
st.caption("국내+해외 8개 마켓 | RSI·MACD·볼린저밴드 | 구독 수익 모델 | PC+모바일 이중 버전")
st.markdown("")

left1, right1 = st.columns([1.3, 1], gap="large")

with left1:
    st.markdown("""
#### 핵심 기능
| | 기능 | 설명 |
|--|------|------|
| 🇰🇷🇺🇸🇯🇵🇨🇳🇻🇳 | **8개 마켓** | KOSPI·KOSDAQ·KONEX + NYSE·NASDAQ·TSE·HKEX·HOSE |
| 📊 | **기술 지표** | RSI·MACD·볼린저밴드 차트 & 신호 자동 해석 |
| 🔁 | **종목 비교** | 최대 3개 종목 누적 수익률 동시 비교 |
| 💰 | **포트폴리오 시뮬레이터** | "그때 샀다면 지금 얼마?" 자동 계산 |
| 💎 | **구독 수익 모델** | 무료/프리미엄 기능 게이팅 + 요금제 페이지 |
| 📱 | **모바일 버전** | 별도 최적화 앱 (centered 레이아웃, 터치 UX) |
""")

    st.markdown("#### Tech Stack")
    st.markdown("""
<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;">
  <span class="badge" style="background:#FF6B6B18;color:#c0392b;border-color:#FF6B6B55;">Streamlit 1.51</span>
  <span class="badge" style="background:#3776AB18;color:#2c5f8a;border-color:#3776AB55;">Python 3.11</span>
  <span class="badge" style="background:#00897B18;color:#005f56;border-color:#00897B55;">FinanceDataReader</span>
  <span class="badge" style="background:#F9731618;color:#c05600;border-color:#F9731655;">mplfinance</span>
  <span class="badge" style="background:#8B5CF618;color:#5b21b6;border-color:#8B5CF655;">pandas · numpy</span>
  <span class="badge" style="background:#2496ED18;color:#1361a0;border-color:#2496ED55;">Docker Compose</span>
  <span class="badge" style="background:#43e97b18;color:#15803d;border-color:#43e97b55;">qrcode · BeautifulSoup</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="highlight" style="background:#fff7ed; border-left:4px solid #f97316;">
  <b>💡 경쟁 차별점</b><br>
  네이버 증권·증권사 HTS와 달리 <b>초보 투자자를 위한 지표 해설</b>과
  <b>포트폴리오 시뮬레이터</b>를 제공합니다.<br>
  프리미엄 구독 모델로 실제 상용화 가능한 구조를 구현했습니다.
</div>
""", unsafe_allow_html=True)

with right1:
    st.markdown("#### QR 코드로 바로 접속")
    q1, q2 = st.columns(2)
    with q1:
        st.markdown("""
<div class="qr-box">
  <div style="font-size:.85rem; font-weight:700; color:#1a1a2e; margin-bottom:10px;">💻 PC 버전</div>
""", unsafe_allow_html=True)
        if pc_qr:
            st.image(pc_qr, width=155)
        st.markdown(f"<div style='font-size:.7rem;color:#6b7280;margin-top:6px;word-break:break-all;'>{pc_url}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with q2:
        st.markdown("""
<div class="qr-box">
  <div style="font-size:.85rem; font-weight:700; color:#e53e3e; margin-bottom:10px;">📱 모바일 버전</div>
""", unsafe_allow_html=True)
        if mobile_qr:
            st.image(mobile_qr, width=155)
        st.markdown(f"<div style='font-size:.7rem;color:#6b7280;margin-top:6px;word-break:break-all;'>{mobile_url}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    st.markdown("""
<div class="highlight" style="background:#1a1a2e; color:#e5e7eb; font-family:monospace; font-size:.78rem; line-height:1.9;">
  <span style="color:#FF6B6B; font-weight:700;"># 실행 방법</span><br>
  <span style="color:#6ee7b7;">$</span> start_all.bat &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#6b7280;"># Windows</span><br>
  <span style="color:#6ee7b7;">$</span> docker compose up <span style="color:#6b7280;"># Docker</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ════════════════════════════════════════
# PROJECT 2 — 사장봇
# ════════════════════════════════════════
st.markdown("## 🤖 해커톤 &nbsp; 사장봇 — AI 마케팅 콘텐츠 자동화")
st.caption("GPT-4o-mini | Few-Shot Prompting | 블로그·리뷰·쇼츠·썸네일 4종 동시 생성 | 네이버 SEO 최적화")
st.markdown("")

l2, r2 = st.columns(2, gap="large")
with l2:
    st.markdown("""
#### 주요 기능
- ✍️ **블로그 포스팅** 자동 작성 (SEO 최적화)
- ⭐ **리뷰 답변** 자동 생성
- 🎬 **유튜브 쇼츠** 대본 + 썸네일 문구 동시 생성
- 🔍 **네이버 SEO** — C-Rank / D.I.A+ 알고리즘 반영
- 💬 **Few-Shot Prompting** 업종별 말투 커스터마이징
- 🔐 **JWT 인증** / SQLite 사용자 관리
- 🚀 **Docker + AWS EC2 + GitHub Actions** CI/CD 자동 배포
""")

with r2:
    st.markdown("#### Tech Stack")
    st.markdown("""
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">
  <span class="badge" style="background:#05998818;color:#037360;border-color:#05998855;">FastAPI</span>
  <span class="badge" style="background:#00A67E18;color:#007a5e;border-color:#00A67E55;">OpenAI GPT-4o-mini</span>
  <span class="badge" style="background:#2496ED18;color:#1361a0;border-color:#2496ED55;">Docker</span>
  <span class="badge" style="background:#FF990018;color:#a85800;border-color:#FF990055;">AWS EC2</span>
  <span class="badge" style="background:#24292E18;color:#1a1f23;border-color:#24292E55;">GitHub Actions</span>
  <span class="badge" style="background:#3776AB18;color:#2c5f8a;border-color:#3776AB55;">SQLite · JWT</span>
</div>

<div class="highlight" style="background:#fff7ed; border-left:4px solid #f97316;">
  <b>🏆 핵심 성과</b><br>
  네이버 SEO 알고리즘 C-Rank · D.I.A+를 분석해 최적화된 프롬프트를 설계,
  마케팅 콘텐츠 <b>4종을 10초 이내</b>에 동시 생성하는 파이프라인 구현.
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ════════════════════════════════════════
# PROJECT 3 — Focus Memo
# ════════════════════════════════════════
st.markdown("## 📝 2차 프로젝트 &nbsp; Focus Memo — 스마트 메모 관리")
st.caption("Django · SQLite · 자동 키워드 추출 · 로그인 기반 개인 메모 공간")
st.markdown("")

l3, r3 = st.columns(2, gap="large")
with l3:
    st.markdown("""
#### 주요 기능
- 📌 **메모 CRUD** — 작성·수정·삭제·조회
- 🏷️ **자동 키워드 추출** — 내용에서 핵심 키워드 자동 분류 (soynlp)
- 🔍 **카테고리/키워드 검색** — 빠른 메모 검색
- 🔐 **@login_required** 인증 — 사용자별 독립 메모 공간
- 🛠️ **Django Admin** — 관리자 페이지 활용
""")

with r3:
    st.markdown("#### Tech Stack")
    st.markdown("""
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">
  <span class="badge" style="background:#0C4B3318;color:#0a3d2b;border-color:#0C4B3355;">Django</span>
  <span class="badge" style="background:#00375618;color:#002a40;border-color:#00375655;">SQLite</span>
  <span class="badge" style="background:#3776AB18;color:#2c5f8a;border-color:#3776AB55;">Python</span>
  <span class="badge" style="background:#56347918;color:#3d2457;border-color:#56347955;">soynlp (NLP)</span>
  <span class="badge" style="background:#f3f4f618;color:#374151;border-color:#d1d5db;">HTML · CSS · Bootstrap</span>
</div>

<div class="highlight" style="background:#f0fdf4; border-left:4px solid #16a34a;">
  <b>💡 차별점</b><br>
  단순 메모 앱을 넘어 <b>자동 키워드 추출 + 카테고리 분류</b>로
  나중에 찾기 쉬운 "스마트 메모장"을 구현했습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ════════════════════════════════════════
# PROJECT 4 — 뽀모도로 타이머 (토티)
# ════════════════════════════════════════
st.markdown("## ⏱️ 3차 프로젝트 &nbsp; 토티 — AI 뽀모도로 타이머")
st.caption("FastAPI · Gemini 2.5 · ASMR 플레이어 · AI 플랜 추천 · 집중 통계")
st.markdown("")

l4, r4 = st.columns(2, gap="large")
with l4:
    st.markdown("""
#### 주요 기능
- ⏰ **뽀모도로 타이머** — 집중/휴식 사이클 자동 관리
- 🤖 **AI 플랜 추천** — Gemini 2.5가 오늘의 집중 블록을 자동 설계
- 🎵 **ASMR 플레이어** — 집중력 향상 배경음 재생
- 📊 **집중 통계** — 일별/주별 집중 시간 시각화
- 📝 **세션 메모** — 집중 중 빠른 메모 기록
""")

with r4:
    st.markdown("#### Tech Stack")
    st.markdown("""
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">
  <span class="badge" style="background:#05998818;color:#037360;border-color:#05998855;">FastAPI</span>
  <span class="badge" style="background:#1A73E818;color:#0f4d9a;border-color:#1A73E855;">Gemini 2.5</span>
  <span class="badge" style="background:#8B5CF618;color:#5b21b6;border-color:#8B5CF655;">Python</span>
  <span class="badge" style="background:#F9731618;color:#c05600;border-color:#F9731655;">JavaScript</span>
  <span class="badge" style="background:#f3f4f618;color:#374151;border-color:#d1d5db;">SQLite</span>
</div>

<div class="highlight" style="background:#f5f3ff; border-left:4px solid #7c3aed;">
  <b>💡 차별점</b><br>
  기존 타이머 앱과 달리 <b>AI가 할 일을 분석해 집중 블록을 자동 설계</b>하고,
  ASMR로 집중 환경까지 함께 제공합니다.
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ════════════════════════════════════════
# FOOTER — QR + 접속 방법
# ════════════════════════════════════════
st.markdown("""
<div style="text-align:center; margin-bottom:24px;">
  <h2 style="font-size:1.6rem; font-weight:800; color:#111827;">
    📱 지금 바로 주식 분석 플랫폼 사용해보기
  </h2>
  <p style="color:#6b7280; font-size:.95rem;">
    같은 Wi-Fi 환경에서 QR 코드를 스캔하거나 주소를 직접 입력하세요.
  </p>
</div>
""", unsafe_allow_html=True)

f1, f2, f3 = st.columns([1, 1, 1.2], gap="large")

with f1:
    st.markdown("""
<div class="qr-box" style="background:white; border:2px solid #e5e7eb;">
  <div style="font-weight:800; font-size:1rem; color:#1a1a2e; margin-bottom:12px;">
    💻 PC 버전
  </div>
""", unsafe_allow_html=True)
    if pc_qr:
        st.image(pc_qr, width=190)
    st.markdown(f"""
  <div style="margin-top:10px;">
    <a href="{pc_url}" target="_blank" style="
      display:inline-block; background:#1a1a2e; color:white;
      padding:8px 20px; border-radius:8px; text-decoration:none;
      font-size:.82rem; font-weight:700; margin-top:6px;">
      → 바로가기
    </a>
    <div style="font-size:.72rem; color:#9ca3af; margin-top:8px;">{pc_url}</div>
  </div>
</div>""", unsafe_allow_html=True)

with f2:
    st.markdown("""
<div class="qr-box" style="background:white; border:2px solid #fecaca;">
  <div style="font-weight:800; font-size:1rem; color:#e53e3e; margin-bottom:12px;">
    📱 모바일 버전
  </div>
""", unsafe_allow_html=True)
    if mobile_qr:
        st.image(mobile_qr, width=190)
    st.markdown(f"""
  <div style="margin-top:10px;">
    <a href="{mobile_url}" target="_blank" style="
      display:inline-block; background:#e53e3e; color:white;
      padding:8px 20px; border-radius:8px; text-decoration:none;
      font-size:.82rem; font-weight:700; margin-top:6px;">
      → 바로가기
    </a>
    <div style="font-size:.72rem; color:#9ca3af; margin-top:8px;">{mobile_url}</div>
  </div>
</div>""", unsafe_allow_html=True)

with f3:
    st.markdown("""
<div style="background:#111827; color:#f9fafb; border-radius:14px; padding:24px; height:100%;">
  <div style="font-size:.9rem; font-weight:800; color:#FF6B6B; margin-bottom:14px;">
    🚀 서버 실행 방법
  </div>
  <div style="font-family:monospace; font-size:.8rem; line-height:2; color:#d1d5db;">
    <span style="color:#9ca3af;"># Windows — 더블클릭</span><br>
    <span style="color:#6ee7b7;">▶</span> start_all.bat<br><br>
    <span style="color:#9ca3af;"># Docker 배포</span><br>
    <span style="color:#6ee7b7;">$</span> docker compose up -d<br><br>
    <span style="color:#9ca3af;"># 개별 실행</span><br>
    <span style="color:#6ee7b7;">$</span> streamlit run app.py<br>
    <span style="color:#6ee7b7;">$</span> streamlit run app_mobile.py<br>
    &nbsp;&nbsp;&nbsp;<span style="color:#fbbf24;">--server.port 8502</span><br><br>
    <span style="color:#9ca3af;"># 포트폴리오</span><br>
    <span style="color:#6ee7b7;">$</span> streamlit run portfolio.py<br>
    &nbsp;&nbsp;&nbsp;<span style="color:#fbbf24;">--server.port 8500</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("""
<div style="text-align:center; padding:20px 0; color:#9ca3af; font-size:.82rem;">
  © 2026 Portfolio &nbsp;·&nbsp; Powered by Streamlit &nbsp;·&nbsp;
  <a href="mailto:dongjebag59@gmail.com" style="color:#6b7280;">dongjebag59@gmail.com</a>
</div>
""", unsafe_allow_html=True)
