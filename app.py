
# 필요한 라이브러리
import streamlit as st
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
from streamlit_lottie import st_lottie
import requests
from bs4 import BeautifulSoup
import os
import math as _math
import json as _json
import pandas as pd

from common import (
    MARKET_INFO, ALL_MARKETS, MARKET_DISPLAYS, MARKET_FLAGS, WSJ_EXCHANGE,
    FAVORITES_FILE, fmt_price, get_local_ip, load_favorites, save_favorites,
    make_qr, kakao_pay_button as _kakao_pay_button, handle_kakao_callback,
)


# 페이지 설정
st.set_page_config(
    page_title="주식 분석 통합 플랫폼",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
for _k, _v in [("fav_code", None), ("fav_market", None), ("is_premium", False),
               ("kakao_tid", None), ("kakao_order_id", None), ("payment_msg", None)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

handle_kakao_callback()

# 로티 — 로컬 파일 우선, 실패 시 URL 폴백
_lottie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources",
    "lottie-full-movie-experience-including-music-news-video-weather-and-lots-of-entertainment.json")

@st.cache_data
def _load_lottie(local_path: str, fallback_url: str):
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        pass
    try:
        r = requests.get(fallback_url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

lottie_json = _load_lottie(
    _lottie_path,
    "https://lottie.host/ec84bdca-8c08-41de-90cc-9bd58157f679/ooMiQcJ1eO.json"
)

_local_ip = get_local_ip()

# 결제 결과 토스트
if st.session_state.payment_msg:
    if st.session_state.payment_msg == "success":
        st.toast("💎 프리미엄 결제가 완료되었습니다! 모든 기능이 활성화되었습니다.", icon="✅")
    else:
        st.toast(st.session_state.payment_msg, icon="⚠️")
    st.session_state.payment_msg = None

# 메인 타이틀
col_logo, col_title = st.columns([0.08, 0.92])
with col_logo:
    if lottie_json:
        st_lottie(lottie_json, speed=2, loop=True, width=80, height=80)
with col_title:
    st.markdown("# 📈 주식 분석 통합 플랫폼")
    st.caption("🇰🇷 국내 3개 마켓 · 🇺🇸🇯🇵🇨🇳🇻🇳 해외 5개 마켓 | RSI · MACD · 볼린저밴드 | 종목 비교 · 포트폴리오 시뮬레이션")

h1, h2, h3, h4 = st.columns(4)
h1.metric("지원 마켓", "국내 3 + 해외 5개")
h2.metric("기술 지표", "RSI · MACD · 볼린저밴드")
h3.metric("종목 비교", "최대 3개 동시 비교")
h4.metric("핵심 차별화", "💰 포트폴리오 시뮬레이터")
st.markdown("---")


# ── 데이터 함수 ──────────────────────────
@st.cache_data(ttl=300)
def getData(code, datestart, dateend):
    try:
        df = fdr.DataReader(code, datestart, dateend)
        if 'Change' in df.columns:
            df = df.drop(columns='Change')
        return df
    except Exception:
        return pd.DataFrame()

_LISTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "listings")

def _load_static_listing(market: str) -> pd.DataFrame:
    path = os.path.join(_LISTINGS_DIR, f"{market}.csv")
    if os.path.exists(path):
        return pd.read_csv(path, dtype={'Code': str})
    return pd.DataFrame(columns=['Code', 'Name', 'Market'])

def _normalize_listing(df: pd.DataFrame, market: str) -> pd.DataFrame:
    if market in ('KOSPI', 'KOSDAQ', 'KONEX'):
        return df[['Code', 'Name', 'Market']].copy()
    df = df.copy()
    if df.index.name:
        df = df.reset_index()
    rename = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl in ('symbol', 'ticker', 'code', '코드') and 'Code' not in rename.values():
            rename[col] = 'Code'
        elif cl in ('name', '종목명', '이름', 'company') and 'Name' not in rename.values():
            rename[col] = 'Name'
    df = df.rename(columns=rename)
    if 'Code' not in df.columns and len(df.columns) >= 1:
        df = df.rename(columns={df.columns[0]: 'Code'})
    if 'Name' not in df.columns and len(df.columns) >= 2:
        df = df.rename(columns={df.columns[1]: 'Name'})
    if 'Code' not in df.columns or 'Name' not in df.columns:
        return pd.DataFrame(columns=['Code', 'Name', 'Market'])
    df['Market'] = market
    result = df[['Code', 'Name', 'Market']].dropna(subset=['Code', 'Name'])
    return result[result['Code'].astype(str).str.strip() != ''].head(2000)

@st.cache_data(ttl=86400)
def getSymbols(market='KOSPI', sort='Marcap'):
    try:
        df = fdr.StockListing(market)
        result = _normalize_listing(df, market)
        if not result.empty:
            if market in ('KOSPI', 'KOSDAQ', 'KONEX') and sort in result.columns:
                result.sort_values(by=[sort], ascending=(sort != 'Marcap'), inplace=True)
            return result
    except Exception:
        pass
    return _load_static_listing(market)

@st.cache_data(ttl=1800)
def get_google_news(stock_name, max_news=3):
    query = stock_name.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}+주식&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=5)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "xml")
    items = soup.find_all("item")[:max_news]
    return [{"title": i.title.text, "link": i.link.text, "date": i.pubDate.text} for i in items]


# ── Plotly 차트 헬퍼 ─────────────────────
_PLOTLY_TEMPLATES = {"default": "plotly_white", "dark": "plotly_dark", "simple": "simple_white"}

def _candlestick_fig(df, chart_type, template, show_bollinger):
    fig = go.Figure()

    if chart_type == "candle":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            increasing_line_color='#FF4444', decreasing_line_color='#4444FF',
            name='가격', showlegend=False
        ))
    elif chart_type == "ohlc":
        fig.add_trace(go.Ohlc(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            increasing_line_color='#FF4444', decreasing_line_color='#4444FF',
            name='가격', showlegend=False
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            line=dict(color='#1a1a2e', width=2), name='종가'
        ))

    for period, color, name in [(5, '#FF6B6B', 'MA5'), (10, '#2ECC71', 'MA10'), (30, '#3498DB', 'MA30')]:
        ma = df['Close'].rolling(period).mean()
        fig.add_trace(go.Scatter(
            x=df.index, y=ma,
            line=dict(color=color, width=1, dash='dot'),
            name=name, opacity=0.9
        ))

    if show_bollinger and len(df) >= 20:
        ma20 = df['Close'].rolling(20).mean()
        std20 = df['Close'].rolling(20).std()
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        fig.add_trace(go.Scatter(
            x=df.index, y=lower,
            line=dict(color='rgba(68,68,255,0.5)', width=1, dash='dash'),
            name='Lower BB', showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=upper,
            line=dict(color='rgba(255,68,68,0.5)', width=1, dash='dash'),
            fill='tonexty', fillcolor='rgba(128,128,128,0.12)',
            name='볼린저밴드'
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=ma20,
            line=dict(color='#00CED1', width=1.5, dash='dot'),
            name='MA20'
        ))

    fig.update_layout(
        height=520,
        xaxis_rangeslider_visible=False,
        template=template,
        legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1),
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode='x unified'
    )
    return fig


# ── 사이드바 ─────────────────────────────
with st.sidebar:
    st.header("⚙️ 차트 설정")
    st.caption("종목과 기간을 선택하면 차트가 자동으로 업데이트됩니다.")
    ''

    # 플랜 표시
    if st.session_state.is_premium:
        st.success("💎 **프리미엄 플랜** 이용 중")
        if st.button("🔄 무료 플랜으로 전환 (데모)", width='stretch'):
            st.session_state.is_premium = False
            st.rerun()
    else:
        st.info("🆓 **무료 플랜** 이용 중")
        _kakao_pay_button(_local_ip, 8501, key="sidebar")
    st.markdown("---")

    # 관심종목 섹션
    favorites = load_favorites()
    if favorites:
        st.markdown("#### ⭐ 관심 종목")
        _market_icons = {
            'KOSPI': '🇰🇷', 'KOSDAQ': '🇰🇷', 'KONEX': '🇰🇷',
            'NYSE': '🇺🇸', 'NASDAQ': '🇺🇸', 'TSE': '🇯🇵', 'HKEX': '🇨🇳', 'HOSE': '🇻🇳',
        }
        for fav in favorites:
            icon = _market_icons.get(fav.get('market', ''), "⬜")
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(f"{icon} {fav['name'].split('(')[0].strip()}", key=f"fav_{fav['code']}"):
                    st.session_state.fav_code = fav['code']
                    st.session_state.fav_market = fav.get('market', 'KOSPI')
                    st.rerun()
            with c2:
                if st.button("✕", key=f"del_{fav['code']}"):
                    favorites = [f for f in favorites if f['code'] != fav['code']]
                    save_favorites(favorites)
                    if st.session_state.fav_code == fav['code']:
                        st.session_state.fav_code = None
                        st.session_state.fav_market = None
                    st.rerun()
        st.markdown("---")

    # URL 파라미터로 초기 종목/마켓 설정
    _qp = st.query_params
    _init_market = _qp.get("market", "KOSPI")
    if _init_market not in ALL_MARKETS:
        _init_market = "KOSPI"
    _init_code = _qp.get("code", "")

    # 마켓 선택
    _market_idx = ALL_MARKETS.index(st.session_state.fav_market) \
        if st.session_state.fav_market in ALL_MARKETS \
        else (ALL_MARKETS.index(_init_market) if _init_market in ALL_MARKETS else 0)
    selected_market_display = st.selectbox('마켓 선택', MARKET_DISPLAYS, index=_market_idx)
    z = ALL_MARKETS[MARKET_DISPLAYS.index(selected_market_display)]
    currency = MARKET_INFO[z]['currency']

    symbols = getSymbols(z)
    if symbols.empty:
        st.error(f"⚠️ {z} 종목 목록을 불러올 수 없습니다. 잠시 후 새로고침 해주세요.")
        st.stop()
    symbols['Display'] = symbols['Name'] + " (" + symbols['Code'] + ")"
    stock_list = list(symbols['Display'])

    # 종목 기본 인덱스 결정 (관심종목 클릭 > URL 파라미터 > 기본값 순)
    default_idx = 0
    if st.session_state.fav_code:
        m = symbols[symbols['Code'] == st.session_state.fav_code]
        if not m.empty:
            d = m.iloc[0]['Name'] + " (" + m.iloc[0]['Code'] + ")"
            if d in stock_list:
                default_idx = stock_list.index(d)
    elif _init_code:
        m = symbols[symbols['Code'] == _init_code]
        if not m.empty:
            d = m.iloc[0]['Name'] + " (" + m.iloc[0]['Code'] + ")"
            if d in stock_list:
                default_idx = stock_list.index(d)

    selected_name = st.selectbox("종목 선택", stock_list, index=default_idx)
    selected_code = selected_name.split("(")[-1].replace(")", "")

    date_start = st.date_input("시작일 입력", (datetime.today() - timedelta(days=365)).date())
    date_end = st.date_input("종료일 입력", datetime.today().date())

    _date_error = date_start > date_end
    if _date_error:
        st.error("시작일이 종료일보다 늦습니다.")

    chart_type = st.selectbox("차트 유형", ["candle", "ohlc", "line"])
    chart_style = st.selectbox("차트 스타일", list(_PLOTLY_TEMPLATES.keys()))
    _template = _PLOTLY_TEMPLATES[chart_style]

    show_bollinger = st.checkbox(
        "볼린저밴드 표시", value=True,
        help="20일 이동평균(MA20) ±2σ 구간을 표시합니다. 가격이 하단 밴드에 닿으면 반등 가능성이 높아집니다.")

    other_symbols = [s for s in stock_list if s != selected_name]
    compare_names = st.multiselect("비교 종목 선택 (최대 2개)", other_symbols, max_selections=2)

    st.markdown("---")

    # 관심종목 추가
    if st.button("⭐ 현재 종목 관심목록에 추가"):
        favorites = load_favorites()
        if any(f['code'] == selected_code for f in favorites):
            st.info("이미 추가된 종목입니다.")
        elif not st.session_state.is_premium and len(favorites) >= 3:
            st.warning("💎 무료 플랜은 관심종목을 최대 3개까지 저장할 수 있습니다.")
        else:
            favorites.append({"code": selected_code, "name": selected_name, "market": z})
            save_favorites(favorites)
            st.success(f"'{selected_name.split('(')[0].strip()}' 추가됨!")
            st.rerun()

    # 링크 공유
    with st.expander("🔗 현재 종목 링크 공유"):
        st.code(f"?market={z}&code={selected_code}")
        st.caption("브라우저 주소창 끝에 위 파라미터를 붙여서 공유하세요.")


# ── 메인 차트 (자동 갱신) ─────────────────
df = getData(selected_code, date_start, date_end)

st.subheader(f"▪️ 선택 종목 : :blue[{selected_name} (**{z}**)]")

if _date_error:
    st.warning("날짜 범위를 다시 선택해주세요.")
elif df.empty:
    st.error("데이터를 불러올 수 없습니다. 종목 코드나 날짜 범위를 확인해 주세요.")
else:
    st.plotly_chart(_candlestick_fig(df, chart_type, _template, show_bollinger),
                    width='stretch')

''
''


# ── 탭 ──────────────────────────────────
_lock = "" if st.session_state.is_premium else " 🔒"
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    '**요약** :speech_balloon:', '**기간별 통계분석** :speech_balloon:',
    '**뉴스** :speech_balloon:', '**거래량** :speech_balloon:',
    f'**투자 지표**{_lock}', f'**종목 비교**{_lock}',
    f'**포트폴리오 시뮬레이터**{_lock}', '**💎 요금제**'])


with tab1:  # 요약
    if not df.empty:
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        return_pct = (end_price - start_price) / start_price * 100
        ''
        st.markdown(f"- **종목명:** {selected_name.split(' ')[0]}")
        st.markdown(f"- **종목 코드:** {selected_code}")
        st.markdown(f"- **최신 종가:** {fmt_price(end_price, currency)}")
        st.markdown(f"- **기간 내 최고가:** {fmt_price(df['Close'].max(), currency)}")
        st.markdown(f"- **기간 내 최저가:** {fmt_price(df['Close'].min(), currency)}")
        if return_pct > 0:
            st.markdown(f"- **선택 기간 수익률:** :red[{return_pct:.2f}%] 📈")
        elif return_pct < 0:
            st.markdown(f"- **선택 기간 수익률:** :blue[{return_pct:.2f}%] 📉")
        else:
            st.markdown(f"- **선택 기간 수익률:** {return_pct:.2f}%")

        if len(df) >= 20:
            _d = df['Close'].diff()
            _g = _d.where(_d > 0, 0.0)
            _l = -_d.where(_d < 0, 0.0)
            _rsi_val = (100 - (100 / (1 + _g.rolling(14).mean() / _l.rolling(14).mean()))).iloc[-1]
            st.markdown("---")
            st.markdown("**📊 현재 RSI 신호**")
            if _math.isnan(_rsi_val):
                st.info("RSI — 계산 불가 (변동 없음)")
            elif _rsi_val >= 70:
                st.warning(f"⚠️ RSI {_rsi_val:.1f} — **과매수** 구간 (단기 조정 가능성)")
            elif _rsi_val <= 30:
                st.info(f"💡 RSI {_rsi_val:.1f} — **과매도** 구간 (반등 가능성)")
            else:
                st.success(f"✅ RSI {_rsi_val:.1f} — **중립** 구간")
    else:
        st.info("데이터가 없어 요약 정보를 표시할 수 없습니다.")


with tab2:  # 기간별 통계분석
    ''
    st.markdown(f"#### '{selected_name}' 기간 통계 분석 :smile:")
    if not df.empty and len(df) >= 2:
        latest_close = df['Close'].iloc[-1]
        period_mean = df['Close'].mean()
        period_max = df['Close'].max()
        period_min = df['Close'].min()
        price_range = period_max - period_min

        st.markdown("---")
        st.markdown("##### **1. 현재 주가 위치**")
        if latest_close > period_mean:
            st.markdown(f"📈 **현재 종가** ({fmt_price(latest_close, currency)})는 기간 평균 ({fmt_price(period_mean, currency)})보다 **높습니다.**")
        elif latest_close < period_mean:
            st.markdown(f"📉 **현재 종가** ({fmt_price(latest_close, currency)})는 기간 평균 ({fmt_price(period_mean, currency)})보다 **낮습니다.**")
        else:
            st.info("현재 종가가 기간 평균과 거의 같습니다.")

        st.markdown("---")
        st.markdown("##### **2. 기간 내 가격 분포**")
        st.markdown(f"- **최고가**: :red[{fmt_price(period_max, currency)}]")
        st.markdown(f"- **최저가**: :blue[{fmt_price(period_min, currency)}]")
        st.markdown(f"- **차이**: {fmt_price(price_range, currency)}")
        if price_range > 0:
            st.markdown(f"현재 종가는 최저가 대비 **{(latest_close - period_min) / price_range * 100:.1f}%** 지점에 있습니다.")
        else:
            st.markdown("현재 종가는 기간 내 최고가·최저가와 동일합니다.")
    else:
        st.info("기간 통계를 계산하기 위한 데이터가 부족합니다.")


with tab3:  # 뉴스
    inner_tab1, inner_tab2 = st.tabs(["국내", "국외"])
    with inner_tab1:
        st.subheader("국내 증시 뉴스")
        naver_url = f'https://finance.naver.com/item/main.naver?code={selected_code}'
        st.markdown(f"#### ***✅ N Pay 증권 '{selected_name.split('(')[0]}' 검색결과***")
        st.markdown(f"[N pay증권 {selected_name} 바로가기]({naver_url})")
        st.markdown("---")
        st.markdown("#### 📰 ***관련 최신 뉴스 (Google)***")
        try:
            news_list = get_google_news(selected_name.split("(")[0], max_news=3)
            if news_list:
                for news in news_list:
                    st.markdown(
                        f"- **[{news['title']}]({news['link']})**  \n"
                        f"  <span style='color:gray'>{news['date']}</span>",
                        unsafe_allow_html=True)
            else:
                st.info("관련 뉴스가 없습니다.")
        except Exception:
            st.error("뉴스를 불러오는 중 오류가 발생했습니다.")

    with inner_tab2:
        st.subheader("국외 증시 뉴스")
        st.markdown("#### :newspaper: :gray[The Wall Street Journal]")
        _wsj_code = WSJ_EXCHANGE.get(z, 'KR/XKRX')
        WSJ_url = f"https://www.wsj.com/market-data/quotes/{_wsj_code}/{selected_code}?mod=searchresults_companyquotes"
        st.markdown(f"[월스트리트 저널에서 '{selected_name.split('(')[0]}' 검색결과 바로가기]({WSJ_url})")
        st.warning("⚠️ 종목에 따라 뉴스 정보가 존재하지 않을 수도 있습니다.")
        st.markdown("---")
        st.markdown("#### :newspaper: :gray[Bloomberg Markets]")
        st.markdown(" - [블룸버그 마켓 섹션 구경하기](https://www.bloomberg.com/markets)")
        st.markdown("#### :newspaper: :gray[Reuters News]")
        st.markdown(" - [로이터 뉴스 속보 둘러보기](https://www.reuters.com/markets/)")


with tab4:  # 거래량
    if df.empty:
        st.info("종목을 선택하고 사이드바 설정을 완료해주세요.")
    elif 'Volume' not in df.columns:
        st.warning("이 종목은 거래량 데이터를 제공하지 않습니다.")
    else:
        ''
        # 양봉/음봉 색상 구분
        if 'Open' in df.columns:
            vol_colors = ['#FF4444' if c >= o else '#4444FF'
                          for c, o in zip(df['Close'], df['Open'])]
        else:
            vol_colors = '#4169E1'

        avg_vol = df['Volume'].mean()
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(x=df.index, y=df['Volume'],
                                  marker_color=vol_colors, opacity=0.8, name='거래량'))
        fig_vol.add_hline(y=avg_vol, line_dash='dash', line_color='orange',
                           annotation_text=f'평균 {int(avg_vol):,}', annotation_position='right')
        fig_vol.update_layout(
            height=350, template=_template,
            xaxis_title='날짜', yaxis_title='거래량',
            margin=dict(l=10, r=10, t=20, b=10), hovermode='x unified'
        )
        st.plotly_chart(fig_vol, width='stretch')

        st.markdown("---")
        st.markdown("#### 📊 거래량 주요 통계")
        ''
        col1, col2, col3 = st.columns(3)
        col1.metric("평균 거래량", f"{int(avg_vol):,}")
        col2.metric("최대 거래량", f"{int(df['Volume'].max()):,}")
        with col3:
            st.markdown("**최대 거래량 날짜**")
            st.write(f"**{df['Volume'].idxmax().strftime('%Y년 %m월 %d일')}**")

        if df['Volume'].iloc[-1] > avg_vol * 1.5:
            st.warning("최근 거래량이 평균 대비 크게 증가했습니다.")
        else:
            st.info("거래량은 평균 수준입니다.")


with tab5:  # 투자 지표
    if not st.session_state.is_premium:
        st.markdown("### 🔒 프리미엄 전용 기능")
        st.warning("RSI · MACD · 연환산 변동성 지표는 **프리미엄 플랜**에서만 이용하실 수 있습니다.")
        ''
        col_lock1, col_lock2 = st.columns(2)
        with col_lock1:
            st.markdown("""
**이 탭에서 제공하는 기능:**
- 📊 RSI (상대강도지수) 차트 & 신호
- 📈 MACD 차트 & 매수/매도 신호
- ⚠️ 연환산 변동성 분석
- 📆 기간/단기 수익률 분석
""")
        with col_lock2:
            st.markdown("""
**프리미엄 플랜 혜택:**
- ✅ 고급 기술 지표 전체 이용
- ✅ 종목 비교 (최대 3개)
- ✅ 포트폴리오 시뮬레이터
- ✅ 관심종목 무제한 저장
""")
        ''
        _kakao_pay_button(_local_ip, 8501, key="tab5")
    elif not df.empty and len(df) >= 20:
        ''
        close = df['Close']
        returns = close.pct_change().dropna()
        period_return = (close.iloc[-1] / close.iloc[0] - 1) * 100
        volatility = returns.std() * (252 ** 0.5) * 100

        col1, col2 = st.columns(2)
        col1.metric("📆 기간 수익률", f"{period_return:.2f} %")
        col2.metric("⚠️ 연환산 변동성", f"{volatility:.2f} %",
                    help="20% 이하 안정적 | 20~40% 보통 | 40% 이상 고변동성")
        st.caption("💡 변동성이 높을수록 가격 등락이 크고 위험도가 높습니다.")
        st.markdown("---")

        # RSI
        st.markdown("#### ▪️ RSI (상대강도지수)")
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        rsi = 100 - (100 / (1 + gain.rolling(14).mean() / loss.rolling(14).mean()))
        rsi_latest = rsi.iloc[-1]

        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=close.index, y=rsi,
                                      line=dict(color='#9B59B6', width=1.5), name='RSI',
                                      fill='tozeroy', fillcolor='rgba(155,89,182,0.08)'))
        fig_rsi.add_hline(y=70, line_dash='dash', line_color='red',
                           annotation_text='과매수(70)', annotation_position='right')
        fig_rsi.add_hline(y=30, line_dash='dash', line_color='blue',
                           annotation_text='과매도(30)', annotation_position='right')
        fig_rsi.update_layout(height=250, template=_template,
                               yaxis=dict(range=[0, 100]), yaxis_title='RSI',
                               margin=dict(l=10, r=10, t=20, b=10),
                               hovermode='x unified', showlegend=False)
        st.plotly_chart(fig_rsi, width='stretch')

        if _math.isnan(rsi_latest):
            st.info("RSI — 계산 불가 (변동 없음)")
        elif rsi_latest >= 70:
            st.error(f"RSI {rsi_latest:.1f} → 과매수 구간 (단기 조정 가능성)")
        elif rsi_latest <= 30:
            st.info(f"RSI {rsi_latest:.1f} → 과매도 구간 (반등 가능성)")
        else:
            st.success(f"RSI {rsi_latest:.1f} → 중립 구간")

        with st.expander("💡 RSI(상대강도지수)란?"):
            st.markdown("""
**RSI**는 최근 14일간의 주가 상승폭 대 하락폭의 비율로, 현재 주가가 얼마나 과열되었는지를 0~100으로 나타냅니다.

| 구간 | 신호 | 해석 |
|------|------|------|
| 70 이상 | 🔴 과매수 | 단기 조정 가능성 → 매도 고려 |
| 30 이하 | 🔵 과매도 | 반등 가능성 → 매수 고려 |
| 30 ~ 70 | 🟢 중립 | 추세 유지 |

> ⚠️ RSI는 보조 지표이므로 단독으로 매매 결정에 사용하지 마세요.
""")
        st.markdown("---")

        # MACD
        st.markdown("#### ▪️ MACD (이동평균 수렴·발산)")
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        bar_colors = ['#FF6B6B' if v >= 0 else '#4169E1' for v in macd_hist]

        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=close.index, y=macd_line,
                                       line=dict(color='#4ECDC4', width=1.5), name='MACD'))
        fig_macd.add_trace(go.Scatter(x=close.index, y=signal_line,
                                       line=dict(color='#FF6B6B', width=1.5), name='Signal'))
        fig_macd.add_trace(go.Bar(x=close.index, y=macd_hist,
                                   marker_color=bar_colors, opacity=0.6, name='Histogram'))
        fig_macd.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5)
        fig_macd.update_layout(height=280, template=_template,
                                margin=dict(l=10, r=10, t=20, b=10),
                                hovermode='x unified',
                                legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1))
        st.plotly_chart(fig_macd, width='stretch')

        macd_now, signal_now = macd_line.iloc[-1], signal_line.iloc[-1]
        if macd_now > signal_now:
            st.success(f"MACD({macd_now:.2f}) > Signal({signal_now:.2f}) → 상승 신호")
        else:
            st.error(f"MACD({macd_now:.2f}) < Signal({signal_now:.2f}) → 하락 신호")

        with st.expander("💡 MACD(이동평균 수렴·발산)란?"):
            st.markdown("""
**MACD**는 단기(12일) 지수이동평균과 장기(26일) 지수이동평균의 차이로, 추세 전환 시점을 포착합니다.

- **MACD선 > Signal선**: 상승 모멘텀 → 매수 신호 🟢
- **MACD선 < Signal선**: 하락 모멘텀 → 매도 신호 🔴
- **히스토그램**: 막대가 0선 위로 올라오면 상승 전환, 아래로 내려가면 하락 전환
""")
        st.markdown("---")

        # 최근 수익률
        st.markdown("#### ▪️ 최근 수익률")
        col1, col2, col3 = st.columns(3)
        for col, n in zip([col1, col2, col3], [1, 5, 20]):
            with col:
                if len(close) > n:
                    recent_return = (close.iloc[-1] / close.iloc[-n-1] - 1) * 100
                    st.metric(f"{n}일 수익률", f"{recent_return:.2f} %")
                else:
                    st.metric(f"{n}일 수익률", "데이터 부족")
    else:
        st.info("지표 계산을 위한 데이터가 부족합니다. (최소 20일 이상 필요)")


with tab6:  # 종목 비교
    if not st.session_state.is_premium:
        st.markdown("### 🔒 프리미엄 전용 기능")
        st.warning("종목 비교는 **프리미엄 플랜**에서만 이용하실 수 있습니다.")
        ''
        st.markdown("""
**이 탭에서 제공하는 기능:**
- 최대 3개 종목 누적 수익률 동시 비교
- 종목별 시작가 · 현재가 · 수익률 요약표
- 같은 기간, 같은 출발선(0%)으로 공정 비교
""")
        _kakao_pay_button(_local_ip, 8501, key="tab6")
    else:
        st.markdown("#### 📊 종목 비교 (누적 수익률 기준)")
        st.caption("선택한 기간 동안 여러 종목의 수익률을 같은 출발선(0%)에서 비교합니다. 사이드바에서 최대 2개 종목을 추가로 선택하세요.")

        all_compare = [selected_name] + compare_names
        if len(all_compare) < 2:
            st.info("👈 사이드바 '비교 종목 선택'에서 종목을 1개 이상 추가한 뒤 선택해주세요.")
        else:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
            fig_comp = go.Figure()
            summary_rows = []

            for i, name in enumerate(all_compare):
                code = name.split("(")[-1].replace(")", "")
                try:
                    d = getData(code, date_start, date_end)
                    if not d.empty:
                        normalized = (d['Close'] / d['Close'].iloc[0] - 1) * 100
                        label = name.split("(")[0].strip()
                        fig_comp.add_trace(go.Scatter(
                            x=d.index, y=normalized, name=label,
                            line=dict(color=colors[i % len(colors)], width=2)
                        ))
                        ret = float(normalized.iloc[-1])
                        summary_rows.append({
                            "종목": label,
                            f"시작가 ({currency})": fmt_price(d['Close'].iloc[0], currency),
                            f"현재가 ({currency})": fmt_price(d['Close'].iloc[-1], currency),
                            "수익률": f"{ret:+.2f}%",
                            f"최고가 ({currency})": fmt_price(d['Close'].max(), currency),
                            f"최저가 ({currency})": fmt_price(d['Close'].min(), currency),
                        })
                except Exception:
                    st.warning(f"{name} 데이터를 불러오지 못했습니다.")

            fig_comp.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5)
            fig_comp.update_layout(
                height=420, template=_template,
                yaxis_title='누적 수익률 (%)', xaxis_title='날짜',
                legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1),
                margin=dict(l=10, r=10, t=40, b=10), hovermode='x unified'
            )
            st.plotly_chart(fig_comp, width='stretch')

            if summary_rows:
                st.markdown("#### 요약 비교표")
                st.dataframe(pd.DataFrame(summary_rows), width='stretch', hide_index=True)


with tab7:  # 포트폴리오 시뮬레이터
    if not st.session_state.is_premium:
        st.markdown("### 🔒 프리미엄 전용 기능")
        st.warning("포트폴리오 시뮬레이터는 **프리미엄 플랜**에서만 이용하실 수 있습니다.")
        ''
        st.markdown("""
**이 탭에서 제공하는 기능:**
- 📅 특정 날짜에 투자했다면 지금 얼마?
- 💰 투자 원금 대비 현재 평가액 & 손익 계산
- 📊 투자 기간 내 평가액 변화 그래프
- 🎯 수익률 구간별 코멘트
""")
        _kakao_pay_button(_local_ip, 8501, key="tab7")
    else:
        st.markdown("#### 💰 포트폴리오 시뮬레이터")
        st.markdown(f"**{selected_name.split('(')[0].strip()}** 에 특정 날짜에 투자했다면 지금 얼마일지 계산합니다.")
        ''
        col_a, col_b = st.columns(2)
        with col_a:
            invest_date = st.date_input(
                "투자 날짜", (datetime.today() - timedelta(days=365)).date(),
                min_value=date(2000, 1, 1), max_value=datetime.today().date(),
                key="invest_date")
        with col_b:
            invest_amount = st.number_input(
                f"투자 금액 ({currency})", min_value=1, max_value=10_000_000_000,
                value=1_000_000 if currency == '원' else (10_000 if currency == 'USD' else 100_000),
                step=100_000 if currency == '원' else (1_000 if currency == 'USD' else 10_000),
                key="invest_amount")

        if st.button("계산하기", key="calc_portfolio"):
            try:
                hist_df = getData(selected_code, invest_date, datetime.today().date())
                if hist_df.empty:
                    st.error("해당 날짜의 데이터가 없습니다. 거래일을 확인해주세요.")
                else:
                    buy_price = hist_df['Close'].iloc[0]
                    current_price = hist_df['Close'].iloc[-1]
                    shares = invest_amount / buy_price
                    current_value = shares * current_price
                    profit = current_value - invest_amount
                    return_pct = (current_value / invest_amount - 1) * 100

                    st.markdown("---")
                    st.markdown(f"**실제 매수일:** {hist_df.index[0].strftime('%Y년 %m월 %d일')} (가장 가까운 거래일)")
                    st.markdown(f"**매수 가격:** {fmt_price(buy_price, currency)} / 주")
                    st.markdown(f"**매수 수량:** {shares:.4f} 주")
                    ''
                    c1, c2, c3 = st.columns(3)
                    c1.metric("투자 원금", fmt_price(invest_amount, currency))
                    c2.metric("현재 평가액", fmt_price(current_value, currency))
                    prefix = "+" if profit >= 0 else ""
                    c3.metric("손익", f"{prefix}{fmt_price(abs(profit), currency)}", delta=f"{return_pct:.2f}%")

                    invest_values = (hist_df['Close'] / buy_price) * invest_amount
                    line_color = '#2ECC71' if return_pct >= 0 else '#E74C3C'
                    fill_color = 'rgba(46,204,113,0.12)' if return_pct >= 0 else 'rgba(231,76,60,0.12)'

                    fig_port = go.Figure()
                    fig_port.add_hline(y=invest_amount, line_dash='dash', line_color='gray',
                                        annotation_text=f'원금 {fmt_price(invest_amount, currency)}',
                                        annotation_position='right')
                    fig_port.add_trace(go.Scatter(
                        x=hist_df.index, y=invest_values,
                        line=dict(color=line_color, width=2),
                        fill='tozeroy', fillcolor=fill_color, name='평가액'
                    ))
                    fig_port.update_layout(height=360, template=_template,
                                           yaxis_title=f'평가액 ({currency})', xaxis_title='날짜',
                                           margin=dict(l=10, r=10, t=20, b=10),
                                           hovermode='x unified', showlegend=False)
                    st.plotly_chart(fig_port, width='stretch')
                    ''
                    if return_pct >= 20:
                        st.success(f"🎉 {return_pct:.2f}% 수익! 훌륭한 투자입니다.")
                    elif return_pct > 0:
                        st.success(f"📈 {return_pct:.2f}% 수익 중입니다.")
                    elif return_pct > -10:
                        st.warning(f"📊 {abs(return_pct):.2f}% 손실 중입니다.")
                    else:
                        st.error(f"📉 {abs(return_pct):.2f}% 손실 중입니다.")
            except Exception as e:
                st.error(f"계산 중 오류가 발생했습니다: {str(e)}")


with tab8:  # 요금제
    st.markdown("## 💎 요금제 안내")
    st.caption("모든 기능을 체험해보고 나에게 맞는 플랜을 선택하세요.")
    ''
    col_free, col_premium = st.columns(2, gap="large")

    with col_free:
        st.markdown("""
<div style="border:2px solid #ddd;border-radius:12px;padding:24px;text-align:center;">
<h2>🆓 무료 플랜</h2><h1 style="color:#666;">₩0</h1>
<p style="color:gray;">영구 무료</p><hr></div>
""", unsafe_allow_html=True)
        st.markdown("""
**포함 기능:**
- ✅ 국내 3개 + 해외 5개 마켓 전 종목 조회
- ✅ 캔들 · OHLC · 라인 차트 (인터랙티브)
- ✅ 볼린저밴드 · 이동평균선 표시
- ✅ 기간별 통계 분석
- ✅ 국내 · 국외 관련 뉴스
- ✅ 거래량 분석
- ✅ 관심종목 저장 (최대 3개)
- ❌ RSI · MACD 지표
- ❌ 종목 비교
- ❌ 포트폴리오 시뮬레이터
- ❌ 관심종목 무제한
""")
        if not st.session_state.is_premium:
            st.success("현재 이용 중인 플랜입니다.")

    with col_premium:
        st.markdown("""
<div style="border:3px solid #FFD700;border-radius:12px;padding:24px;text-align:center;background:linear-gradient(135deg,#fff9e6,#fffdf5);">
<h2>💎 프리미엄 플랜</h2><h1 style="color:#E6A817;">₩9,900</h1>
<p style="color:gray;">월 구독 · 언제든 해지 가능</p><hr></div>
""", unsafe_allow_html=True)
        st.markdown("""
**포함 기능:**
- ✅ 무료 플랜의 모든 기능
- ✅ RSI 차트 & 과매수/과매도 신호
- ✅ MACD 차트 & 매수/매도 신호
- ✅ 연환산 변동성 분석
- ✅ 종목 비교 (최대 3개 동시)
- ✅ 포트폴리오 시뮬레이터
- ✅ 평가액 변화 그래프
- ✅ 관심종목 무제한 저장
""")
        if st.session_state.is_premium:
            st.success("✅ 현재 이용 중인 플랜입니다.")
            if st.button("무료 플랜으로 전환 (데모)", width='stretch'):
                st.session_state.is_premium = False
                st.rerun()
        else:
            _kakao_pay_button(_local_ip, 8501, key="tab8_main")
            st.caption("카카오페이를 통한 안전한 결제 · 언제든 해지 가능")

    st.markdown("---")
    st.markdown("### ❓ 자주 묻는 질문")
    with st.expander("프리미엄은 언제 해지할 수 있나요?"):
        st.markdown("언제든지 해지 가능하며, 다음 결제일 전까지 프리미엄 기능을 계속 이용하실 수 있습니다.")
    with st.expander("무료 플랜에서도 차트를 볼 수 있나요?"):
        st.markdown("네, 무료 플랜에서도 KOSPI·KOSDAQ·KONEX 전 종목의 캔들/라인/OHLC 차트와 뉴스, 거래량 분석을 이용하실 수 있습니다.")
    with st.expander("RSI, MACD가 처음인데 어렵지 않나요?"):
        st.markdown("각 지표 아래에 **초보자용 해설**이 포함되어 있어 투자 지식 없이도 신호를 쉽게 해석할 수 있습니다.")
