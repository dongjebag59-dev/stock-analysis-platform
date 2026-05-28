
# 모바일 최적화 버전 — layout="centered", 사이드바 없음, 터치 친화적 UI

import streamlit as st
import FinanceDataReader as fdr
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta, date
import requests
from bs4 import BeautifulSoup
import os
import pandas as pd

from common import (
    MARKET_INFO, ALL_MARKETS, MARKET_DISPLAYS, MARKET_FLAGS,
    FAVORITES_FILE, fmt_price, get_local_ip, load_favorites, save_favorites,
    make_qr, kakao_pay_button as _kakao_pay_button, handle_kakao_callback,
)


# 한글 폰트 설정
_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "NanumSquareR.ttf")
if os.path.exists(_font_path):
    fm.fontManager.addfont(_font_path)
    plt.rcParams['font.family'] = 'NanumSquareR'
plt.rcParams['axes.unicode_minus'] = False


# ── 페이지 설정 (모바일: centered, 사이드바 숨김) ──
st.set_page_config(
    page_title="주식 분석 📱",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 모바일 최적화 CSS
st.markdown("""
<style>
section[data-testid="stSidebar"] { display: none; }
.stButton > button { font-size: 1rem; padding: 0.5rem 1rem; }
.stTabs [data-baseweb="tab"] { font-size: 0.85rem; padding: 6px 8px; }
div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 8px; padding: 8px; }
</style>
""", unsafe_allow_html=True)


# ── 세션 상태 ──
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "m_market" not in st.session_state:
    st.session_state.m_market = 'KOSPI'
if "m_code" not in st.session_state:
    st.session_state.m_code = None
if "kakao_tid" not in st.session_state:
    st.session_state.kakao_tid = None
if "kakao_order_id" not in st.session_state:
    st.session_state.kakao_order_id = None
if "payment_msg" not in st.session_state:
    st.session_state.payment_msg = None

_local_ip = get_local_ip()
handle_kakao_callback()

# 결제 결과 토스트
if st.session_state.payment_msg:
    if st.session_state.payment_msg == "success":
        st.toast("💎 프리미엄 결제 완료! 모든 기능이 활성화되었습니다.", icon="✅")
    else:
        st.toast(st.session_state.payment_msg, icon="⚠️")
    st.session_state.payment_msg = None


# ── 데이터 함수 ──
@st.cache_data
def getData(code, datestart, dateend):
    try:
        df = fdr.DataReader(code, datestart, dateend)
        if 'Change' in df.columns:
            df = df.drop(columns='Change')
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def getSymbols(market='KOSPI'):
    df = fdr.StockListing(market)
    if market in ('KOSPI', 'KOSDAQ', 'KONEX'):
        if 'Marcap' in df.columns:
            df = df.sort_values('Marcap', ascending=False)
        return df[['Code', 'Name', 'Market']]
    df = df.copy()
    if df.index.name:
        df = df.reset_index()
    rename = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl in ('symbol', 'ticker', 'code', '코드') and 'Code' not in rename.values():
            rename[col] = 'Code'
        elif cl in ('name', '종목명', 'company') and 'Name' not in rename.values():
            rename[col] = 'Name'
    df = df.rename(columns=rename)
    if 'Code' not in df.columns:
        df = df.rename(columns={df.columns[0]: 'Code'})
    if 'Name' not in df.columns:
        df = df.rename(columns={df.columns[1]: 'Name'})
    df['Market'] = market
    result = df[['Code', 'Name', 'Market']].dropna(subset=['Code', 'Name'])
    return result[result['Code'].astype(str).str.strip() != ''].head(2000)

@st.cache_data(ttl=1800)
def get_mobile_news(stock_name: str, max_news: int = 5):
    q = stock_name.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
    soup = BeautifulSoup(res.text, "xml")
    return [
        {"title": item.title.text, "link": item.link.text, "date": item.pubDate.text}
        for item in soup.find_all("item")[:max_news]
    ]

def addBollingerBand_m(data, ax):
    d = data.reset_index(drop=True)
    d['MA20'] = d['Close'].rolling(20).mean()
    d['StDev'] = d['Close'].rolling(20).std()
    d['Upper'] = d['MA20'] + d['StDev'] * 2
    d['Lower'] = d['MA20'] - d['StDev'] * 2
    d = d[19:]
    ax.plot(d.index, d['Upper'], 'r--', linewidth=1, label='Upper')
    ax.plot(d.index, d['MA20'], 'c:', linewidth=1.5, label='MA20')
    ax.plot(d.index, d['Lower'], 'b--', linewidth=1, label='Lower')
    ax.legend(loc='best', fontsize=7)


# ════════════════════════════════
# 헤더
# ════════════════════════════════
st.markdown("## 📈 주식 분석 플랫폼")
st.caption("국내 3개 + 해외 5개 마켓 | RSI · MACD | 포트폴리오 시뮬레이터")

# 플랜 뱃지 + 토글
if st.session_state.is_premium:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.success("💎 **프리미엄** 플랜 이용 중")
    with c2:
        if st.button("해제", key="m_to_free"):
            st.session_state.is_premium = False
            st.rerun()
else:
    st.info("🆓 **무료** 플랜")
    _kakao_pay_button(_local_ip, 8502, key="m_top", mobile=True)

st.caption("💻 PC 버전 → [localhost:8501](http://localhost:8501)")
st.markdown("---")


# ════════════════════════════════
# 관심종목 빠른 선택
# ════════════════════════════════
favorites = load_favorites()
if favorites:
    st.markdown("##### ⭐ 관심 종목")
    cols = st.columns(min(len(favorites), 3))
    for i, fav in enumerate(favorites[:3]):
        flag = MARKET_FLAGS.get(fav.get('market', ''), '🌐')
        with cols[i]:
            label = fav['name'].split('(')[0].strip()[:8]
            if st.button(f"{flag} {label}", key=f"mfav_{fav['code']}", use_container_width=True):
                st.session_state.m_market = fav.get('market', 'KOSPI')
                st.session_state.m_code = fav['code']
                st.rerun()
    st.markdown("---")


# ════════════════════════════════
# 종목 설정 폼
# ════════════════════════════════
with st.form(key='mobile_form'):
    st.markdown("#### ⚙️ 종목 설정")

    market_idx = ALL_MARKETS.index(st.session_state.m_market) \
        if st.session_state.m_market in ALL_MARKETS else 0
    selected_market_display = st.selectbox('마켓', MARKET_DISPLAYS, index=market_idx)
    z = ALL_MARKETS[MARKET_DISPLAYS.index(selected_market_display)]
    currency = MARKET_INFO[z]['currency']

    symbols = getSymbols(z)
    symbols['Display'] = symbols['Name'] + " (" + symbols['Code'] + ")"
    stock_list = list(symbols['Display'])

    default_idx = 0
    if st.session_state.m_code:
        matching = symbols[symbols['Code'] == st.session_state.m_code]
        if not matching.empty:
            disp = matching.iloc[0]['Name'] + " (" + matching.iloc[0]['Code'] + ")"
            if disp in stock_list:
                default_idx = stock_list.index(disp)

    selected_name = st.selectbox("종목", symbols['Display'], index=default_idx)
    selected_code = selected_name.split("(")[-1].replace(")", "")

    cd1, cd2 = st.columns(2)
    with cd1:
        date_start = st.date_input("시작일", (datetime.today() - timedelta(days=365)).date())
    with cd2:
        date_end = st.date_input("종료일", datetime.today().date())

    chart_type = st.selectbox("차트 유형", ["candle", "line", "ohlc"])
    show_bollinger = st.checkbox("볼린저밴드", value=True)

    submitted = st.form_submit_button("📊 조회하기", use_container_width=True, type="primary")

# 관심종목 추가 버튼 (폼 밖)
if st.button("⭐ 현재 종목 관심목록에 추가", use_container_width=True):
    favs = load_favorites()
    if any(f['code'] == selected_code for f in favs):
        st.info("이미 추가된 종목입니다.")
    else:
        favs.append({"code": selected_code, "name": selected_name, "market": z})
        save_favorites(favs)
        st.success(f"'{selected_name.split('(')[0].strip()}' 추가됨!")
        st.rerun()

st.markdown("---")


# ════════════════════════════════
# 메인 차트
# ════════════════════════════════
df = getData(selected_code, date_start, date_end)

if submitted:
    st.markdown(f"**{selected_name}** &nbsp; `{z}`")
    if not df.empty:
        marketcolors = mpf.make_marketcolors(up='red', down='blue', ohlc={'up': 'red', 'down': 'blue'})
        mpf_style = mpf.make_mpf_style(base_mpf_style='default', marketcolors=marketcolors)
        fig, ax = mpf.plot(
            df, volume=False, type=chart_type, style=mpf_style,
            figsize=(7, 4), fontscale=0.85, mav=(5, 20),
            mavcolors=('red', 'blue'), returnfig=True)
        if show_bollinger:
            addBollingerBand_m(df, ax[0])
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.warning("데이터를 불러오지 못했습니다. 종목 코드나 날짜를 확인해주세요.")

st.markdown("---")


# ════════════════════════════════
# 탭
# ════════════════════════════════
_lock = "" if st.session_state.is_premium else " 🔒"
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    '📊 요약',
    '📰 뉴스',
    f'📈 지표{_lock}',
    f'💰 시뮬레이터{_lock}',
    '💎 요금제',
])


# ── Tab1: 요약 ──
with tab1:
    if df.empty:
        st.info("위 설정에서 종목을 선택하고 '조회하기'를 눌러주세요.")
    else:
        latest = df['Close'].iloc[-1]
        high   = df['Close'].max()
        low    = df['Close'].min()
        ret    = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100

        st.markdown(f"**{selected_name.split('(')[0].strip()}** · {z}")
        st.metric("최신 종가", fmt_price(latest, currency))

        c1, c2 = st.columns(2)
        with c1:
            st.metric("기간 최고가", fmt_price(high, currency))
        with c2:
            st.metric("기간 최저가", fmt_price(low, currency))

        if ret > 0:
            st.success(f"📈 수익률 **+{ret:.2f}%**")
        elif ret < 0:
            st.error(f"📉 수익률 **{ret:.2f}%**")
        else:
            st.info(f"수익률 {ret:.2f}%")

        # 거래량 요약
        if 'Volume' in df.columns:
            st.markdown("---")
            avg_vol = df['Volume'].mean()
            last_vol = df['Volume'].iloc[-1]
            st.metric("최근 거래량", f"{int(last_vol):,}")
            if last_vol > avg_vol * 1.5:
                st.warning("⚠️ 최근 거래량이 평균 대비 크게 증가했습니다.")
            else:
                st.info("거래량은 평균 수준입니다.")

        # RSI 빠른 신호
        if len(df) >= 20:
            st.markdown("---")
            _d = df['Close'].diff()
            _g = _d.where(_d > 0, 0.0)
            _l = -_d.where(_d < 0, 0.0)
            _rsi = 100 - (100 / (1 + _g.rolling(14).mean() / _l.rolling(14).mean()))
            rv = _rsi.iloc[-1]
            st.markdown("**📊 RSI 신호**")
            if rv >= 70:
                st.warning(f"⚠️ RSI {rv:.1f} — 과매수 (조정 가능성)")
            elif rv <= 30:
                st.info(f"💡 RSI {rv:.1f} — 과매도 (반등 가능성)")
            else:
                st.success(f"✅ RSI {rv:.1f} — 중립")


# ── Tab2: 뉴스 ──
with tab2:
    stock_nm = selected_name.split("(")[0].strip()
    st.markdown(f"**📰 {stock_nm} 관련 뉴스**")
    try:
        news_items = get_mobile_news(stock_nm)
        if news_items:
            for item in news_items:
                st.markdown(f"**[{item['title']}]({item['link']})**")
                st.caption(item['date'])
                st.markdown("---")
        else:
            st.info("관련 뉴스가 없습니다.")
    except Exception:
        st.error("뉴스를 불러오는 중 오류가 발생했습니다.")

    if z in ('KOSPI', 'KOSDAQ', 'KONEX'):
        naver_url = f'https://finance.naver.com/item/main.naver?code={selected_code}'
        st.markdown(f"[📊 네이버 증권 바로가기]({naver_url})")


# ── Tab3: 투자 지표 (프리미엄) ──
with tab3:
    if not st.session_state.is_premium:
        st.warning("🔒 **프리미엄 전용** 기능입니다.")
        st.markdown("""
- 📊 RSI 차트 & 과매수/과매도 신호
- 📈 MACD 차트 & 매수/매도 신호
- ⚠️ 연환산 변동성 분석
""")
        _kakao_pay_button(_local_ip, 8502, key="m_up3", mobile=True)
    elif df.empty:
        st.info("먼저 종목을 조회해주세요.")
    elif len(df) < 20:
        st.info("데이터가 부족합니다. (최소 20일 이상 필요)")
    else:
        close = df['Close']
        ret_p = (close.iloc[-1] / close.iloc[0] - 1) * 100
        vol_p = close.pct_change().dropna().std() * (252 ** 0.5) * 100

        cx, cy = st.columns(2)
        with cx:
            st.metric("기간 수익률", f"{ret_p:.2f}%")
        with cy:
            st.metric("연환산 변동성", f"{vol_p:.2f}%",
                      help="20% 이하 안정 | 20~40% 보통 | 40% 이상 고변동")
        st.markdown("---")

        # RSI 차트
        st.markdown("**RSI (14일)**")
        d = close.diff()
        g = d.where(d > 0, 0.0)
        l = -d.where(d < 0, 0.0)
        rsi = 100 - (100 / (1 + g.rolling(14).mean() / l.rolling(14).mean()))
        rsi_v = rsi.iloc[-1]

        fig_r, ax_r = plt.subplots(figsize=(6, 2))
        ax_r.plot(close.index, rsi, color='#9B59B6', linewidth=1.2)
        ax_r.axhline(70, color='red', linestyle='--', linewidth=0.8, label='과매수(70)')
        ax_r.axhline(30, color='blue', linestyle='--', linewidth=0.8, label='과매도(30)')
        ax_r.fill_between(close.index, rsi, 70, where=(rsi >= 70), alpha=0.2, color='red')
        ax_r.fill_between(close.index, rsi, 30, where=(rsi <= 30), alpha=0.2, color='blue')
        ax_r.set_ylim(0, 100)
        ax_r.legend(fontsize=7, loc='upper left')
        ax_r.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig_r)
        plt.close(fig_r)

        if rsi_v >= 70:
            st.error(f"RSI {rsi_v:.1f} → 과매수")
        elif rsi_v <= 30:
            st.info(f"RSI {rsi_v:.1f} → 과매도")
        else:
            st.success(f"RSI {rsi_v:.1f} → 중립")

        st.markdown("---")

        # MACD 차트
        st.markdown("**MACD (12, 26, 9)**")
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal

        fig_m, ax_m = plt.subplots(figsize=(6, 2))
        ax_m.plot(close.index, macd, color='#4ECDC4', linewidth=1.2, label='MACD')
        ax_m.plot(close.index, signal, color='#FF6B6B', linewidth=1.2, label='Signal')
        bar_c = ['#FF6B6B' if v >= 0 else '#4169E1' for v in hist]
        ax_m.bar(close.index, hist, color=bar_c, alpha=0.4, width=1)
        ax_m.axhline(0, color='gray', linestyle='--', alpha=0.5)
        ax_m.legend(fontsize=7)
        ax_m.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig_m)
        plt.close(fig_m)

        mn, sn = macd.iloc[-1], signal.iloc[-1]
        if mn > sn:
            st.success("MACD → 상승 신호 🟢")
        else:
            st.error("MACD → 하락 신호 🔴")

        st.markdown("---")
        # 최근 수익률
        st.markdown("**최근 수익률**")
        r1, r5, r20 = st.columns(3)
        for col, n in zip([r1, r5, r20], [1, 5, 20]):
            if len(close) > n:
                rv = (close.iloc[-1] / close.iloc[-n-1] - 1) * 100
                col.metric(f"{n}일", f"{rv:.2f}%")


# ── Tab4: 포트폴리오 시뮬레이터 (프리미엄) ──
with tab4:
    if not st.session_state.is_premium:
        st.warning("🔒 **프리미엄 전용** 기능입니다.")
        st.markdown("""
- 📅 특정 날짜에 투자했다면 지금 얼마?
- 💰 원금 대비 현재 평가액 & 손익
- 📊 투자 기간 내 평가액 변화 그래프
""")
        _kakao_pay_button(_local_ip, 8502, key="m_up4", mobile=True)
    else:
        st.markdown(f"**{selected_name.split('(')[0].strip()}** 투자 시뮬레이션")

        sa, sb = st.columns(2)
        with sa:
            sim_date = st.date_input("투자 날짜",
                (datetime.today() - timedelta(days=365)).date(),
                min_value=date(2000, 1, 1), max_value=datetime.today().date(),
                key="m_sim_date")
        with sb:
            sim_amount = st.number_input(
                f"투자 금액 ({currency})",
                min_value=1,
                value=1_000_000 if currency == '원' else (10_000 if currency == 'USD' else 100_000),
                step=100_000 if currency == '원' else (1_000 if currency == 'USD' else 10_000),
                key="m_sim_amount")

        if st.button("💰 계산하기", use_container_width=True, type="primary", key="m_calc"):
            try:
                h = getData(selected_code, sim_date, datetime.today().date())
                if h.empty:
                    st.error("데이터가 없습니다. 거래일을 확인해주세요.")
                else:
                    bp = h['Close'].iloc[0]
                    cp = h['Close'].iloc[-1]
                    buy_date = h.index[0].strftime('%Y년 %m월 %d일')
                    shares = sim_amount / bp
                    cv = shares * cp
                    profit = cv - sim_amount
                    ret = (cv / sim_amount - 1) * 100

                    st.markdown(f"**실제 매수일:** {buy_date}")
                    st.markdown(f"**매수가:** {fmt_price(bp, currency)} &nbsp;|&nbsp; **현재가:** {fmt_price(cp, currency)}")

                    st.metric("투자 원금", fmt_price(sim_amount, currency))
                    st.metric("현재 평가액", fmt_price(cv, currency))
                    prefix = "+" if profit >= 0 else ""
                    st.metric("손익", f"{prefix}{fmt_price(abs(profit), currency)}", delta=f"{ret:.2f}%")

                    # 평가액 변화 차트
                    iv = (h['Close'] / bp) * sim_amount
                    fig_s, ax_s = plt.subplots(figsize=(6, 3))
                    ax_s.plot(h.index, iv, color='#2ECC71', linewidth=1.5, label='평가액')
                    ax_s.axhline(sim_amount, color='gray', linestyle='--', linewidth=1,
                                 label=f'원금 ({fmt_price(sim_amount, currency)})')
                    ax_s.fill_between(h.index, iv, sim_amount,
                                      where=(iv >= sim_amount), alpha=0.2, color='green')
                    ax_s.fill_between(h.index, iv, sim_amount,
                                      where=(iv < sim_amount), alpha=0.2, color='red')
                    ax_s.set_ylabel(f'평가액 ({currency})')
                    ax_s.legend(fontsize=8)
                    ax_s.grid(True, alpha=0.3)
                    plt.tight_layout()
                    st.pyplot(fig_s)
                    plt.close(fig_s)

                    if ret >= 20:
                        st.success(f"🎉 {ret:.2f}% 수익! 훌륭한 투자입니다.")
                    elif ret > 0:
                        st.success(f"📈 {ret:.2f}% 수익 중입니다.")
                    elif ret > -10:
                        st.warning(f"📊 {abs(ret):.2f}% 손실 중입니다.")
                    else:
                        st.error(f"📉 {abs(ret):.2f}% 손실 중입니다.")
            except Exception as e:
                st.error(f"계산 중 오류가 발생했습니다: {str(e)}")


# ── Tab5: 요금제 ──
with tab5:
    st.markdown("### 💎 요금제 안내")

    if st.session_state.is_premium:
        st.success("✅ **프리미엄 플랜** 이용 중")
        if st.button("무료 플랜으로 전환 (데모)", use_container_width=True):
            st.session_state.is_premium = False
            st.rerun()
    else:
        st.markdown("""
**🆓 무료** (영구 무료)
- ✅ 국내 3개 + 해외 5개 마켓
- ✅ 캔들 · 라인 · OHLC 차트
- ✅ 요약 · 뉴스 · 거래량
- ✅ 관심종목 3개
- ❌ RSI · MACD 지표
- ❌ 포트폴리오 시뮬레이터
- ❌ 관심종목 무제한

---

**💎 프리미엄** (월 ₩9,900)
- ✅ 무료 플랜 기능 전체
- ✅ RSI 차트 & 신호
- ✅ MACD 차트 & 신호
- ✅ 연환산 변동성 분석
- ✅ 포트폴리오 시뮬레이터
- ✅ 관심종목 무제한

---
""")
        _kakao_pay_button(_local_ip, 8502, key="m_tab5_main", mobile=True)
        st.caption("카카오페이를 통한 안전한 결제 · 언제든 해지 가능")

    st.markdown("---")
    st.markdown("#### 💻 PC 버전 바로가기")
    _pc_url = f"http://{_local_ip}:8501"
    if _HAS_QR:
        _qr = make_qr(_pc_url)
        if _qr:
            st.image(_qr, width=180)
    st.caption(_pc_url)
    st.markdown(f"[→ PC 버전 열기]({_pc_url})")
