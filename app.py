
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

_LISTINGS_META: dict = {}
try:
    _meta_path = os.path.join(_LISTINGS_DIR, "meta.json")
    if os.path.exists(_meta_path):
        with open(_meta_path, encoding="utf-8") as _f:
            _LISTINGS_META = _json.load(_f)
except Exception:
    pass

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
_PLOTLY_CONFIG = {'displayModeBar': True, 'displaylogo': False}

try:
    _APP_BASE_URL = st.secrets.get("APP_BASE_URL", "").rstrip("/")
except Exception:
    _APP_BASE_URL = ""

def _candlestick_fig(df, chart_type, template, show_bollinger, show_signals=False, ma_periods=None):
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

    _MA_COLORS = {5: '#FF6B6B', 20: '#F39C12', 60: '#3498DB', 120: '#9B59B6'}
    for _p in (ma_periods or []):
        if len(df) >= _p and not (show_bollinger and _p == 20):
            _ma = df['Close'].rolling(_p).mean()
            fig.add_trace(go.Scatter(
                x=df.index, y=_ma,
                line=dict(color=_MA_COLORS.get(_p, '#888888'), width=1.2, dash='dot'),
                name=f'MA{_p}', opacity=0.9
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

    if show_signals and len(df) >= 30:
        _ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        _ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        _macd = _ema12 - _ema26
        _sig  = _macd.ewm(span=9, adjust=False).mean()
        _diff = _macd - _sig
        _prev = _diff.shift(1)
        _buf  = (df['High'].max() - df['Low'].min()) * 0.025
        buy_x  = df.index[(_prev <= 0) & (_diff > 0)]
        sell_x = df.index[(_prev >= 0) & (_diff < 0)]
        if len(buy_x) > 0:
            fig.add_trace(go.Scatter(
                x=buy_x, y=df.loc[buy_x, 'Low'] - _buf, mode='markers',
                marker=dict(symbol='triangle-up', size=11, color='#00C853',
                            line=dict(color='white', width=0.5)),
                name='매수 신호', hovertemplate='MACD 매수 신호<extra></extra>'
            ))
        if len(sell_x) > 0:
            fig.add_trace(go.Scatter(
                x=sell_x, y=df.loc[sell_x, 'High'] + _buf, mode='markers',
                marker=dict(symbol='triangle-down', size=11, color='#FF1744',
                            line=dict(color='white', width=0.5)),
                name='매도 신호', hovertemplate='MACD 매도 신호<extra></extra>'
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
        st.caption("⚠️ 관심종목은 서버 재시작 시 초기화될 수 있습니다.")
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
    if _LISTINGS_META.get('updated_at'):
        _date_ref = _LISTINGS_META.get('kr_data_date') or _LISTINGS_META['updated_at']
        st.caption(f"📅 종목 목록 기준일: {_date_ref}")

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
    show_signals = st.checkbox(
        "매매 신호 표시", value=False,
        help="MACD 골든크로스(▲매수)·데드크로스(▽매도) 시점을 메인 차트에 표시합니다.")
    ma_periods = st.multiselect(
        "이동평균선 (MA)",
        options=[5, 20, 60, 120],
        default=[5, 20],
        help="메인 차트에 표시할 이동평균선 기간을 선택합니다. MA20은 볼린저밴드 사용 시 자동 포함됩니다.")

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
        _base = _APP_BASE_URL or "https://your-app.streamlit.app"
        st.code(f"{_base}?market={z}&code={selected_code}")
        if not _APP_BASE_URL:
            st.caption("⚙️ secrets에 `APP_BASE_URL` 설정 시 정확한 URL이 표시됩니다.")

    if st.button("🔄 데이터 새로고침", help="캐시를 초기화하고 최신 데이터를 불러옵니다."):
        getData.clear()
        getSymbols.clear()
        st.rerun()


# ── 메인 차트 (자동 갱신) ─────────────────
df = getData(selected_code, date_start, date_end)

st.subheader(f"▪️ 선택 종목 : :blue[{selected_name} (**{z}**)]")

if _date_error:
    st.warning("날짜 범위를 다시 선택해주세요.")
elif df.empty:
    st.error("데이터를 불러올 수 없습니다. 종목 코드나 날짜 범위를 확인해 주세요.")
else:
    st.plotly_chart(
        _candlestick_fig(df, chart_type, _template, show_bollinger, show_signals, ma_periods),
        config=_PLOTLY_CONFIG, width='stretch')

''
''

# ── 기술 지표 사전 계산 (tab1·tab5 공유) ────────
_rsi_series = pd.Series(dtype=float)
_rsi_latest = float('nan')
_macd_line_pre = pd.Series(dtype=float)
_signal_line_pre = pd.Series(dtype=float)
if not df.empty and len(df) >= 20:
    _c = df['Close']
    _d = _c.diff()
    _rsi_series = 100 - (100 / (1 + _d.where(_d > 0, 0.0).rolling(14).mean()
                                   / (-_d.where(_d < 0, 0.0)).rolling(14).mean()))
    _rsi_latest = float(_rsi_series.iloc[-1])
if not df.empty and len(df) >= 26:
    _c = df['Close']
    _macd_line_pre = _c.ewm(span=12, adjust=False).mean() - _c.ewm(span=26, adjust=False).mean()
    _signal_line_pre = _macd_line_pre.ewm(span=9, adjust=False).mean()


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

        # 52주 신고가·신저가
        st.markdown("---")
        _52w_df = getData(selected_code,
                          (datetime.today() - timedelta(days=365)).date(),
                          datetime.today().date())
        if not _52w_df.empty:
            _52h = _52w_df['High'].max()
            _52l = _52w_df['Low'].min()
            _curr = end_price
            col52a, col52b, col52c = st.columns(3)
            col52a.metric(
                "📈 52주 최고가", fmt_price(_52h, currency),
                delta=f"{(_curr / _52h - 1) * 100:+.1f}%",
                help="최근 1년 장중 최고가. 현재 종가 대비 비율.")
            col52b.metric(
                "📉 52주 최저가", fmt_price(_52l, currency),
                delta=f"{(_curr / _52l - 1) * 100:+.1f}%",
                help="최근 1년 장중 최저가. 현재 종가 대비 비율.")
            col52c.metric(
                "↕️ 52주 변동폭", fmt_price(_52h - _52l, currency),
                help="52주 최고가 - 최저가 차이.")

        if len(df) >= 20:
            st.markdown("---")
            st.markdown("**📊 현재 RSI 신호**")
            if not _math.isfinite(_rsi_latest):
                st.info("RSI — 계산 불가 (변동 없음)")
            elif _rsi_latest >= 70:
                st.warning(f"⚠️ RSI {_rsi_latest:.1f} — **과매수** 구간 (단기 조정 가능성)")
            elif _rsi_latest <= 30:
                st.info(f"💡 RSI {_rsi_latest:.1f} — **과매도** 구간 (반등 가능성)")
            else:
                st.success(f"✅ RSI {_rsi_latest:.1f} — **중립** 구간")
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
        st.plotly_chart(fig_vol, config=_PLOTLY_CONFIG, width='stretch')

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

        # RSI (사전 계산값 재사용)
        st.markdown("#### ▪️ RSI (상대강도지수)")
        rsi = _rsi_series
        rsi_latest = _rsi_latest

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
        st.plotly_chart(fig_rsi, config=_PLOTLY_CONFIG, width='stretch')

        if not _math.isfinite(float(rsi_latest)):
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

        # MACD (사전 계산값 재사용 — 최소 26일 필요)
        st.markdown("#### ▪️ MACD (이동평균 수렴·발산)")
        if len(df) >= 26:
            macd_line = _macd_line_pre
            signal_line = _signal_line_pre
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
            st.plotly_chart(fig_macd, config=_PLOTLY_CONFIG, width='stretch')

            macd_now, signal_now = macd_line.iloc[-1], signal_line.iloc[-1]
            if macd_now > signal_now:
                st.success(f"MACD({macd_now:.2f}) > Signal({signal_now:.2f}) → 상승 신호")
            else:
                st.error(f"MACD({macd_now:.2f}) < Signal({signal_now:.2f}) → 하락 신호")
        else:
            st.info(f"MACD 계산을 위한 데이터가 부족합니다. (현재 {len(df)}일, 최소 26일 필요)")

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
            st.plotly_chart(fig_comp, config=_PLOTLY_CONFIG, width='stretch')

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
- 📅 특정 날짜에 최대 3개 종목에 비중 배분 투자했다면 지금 얼마?
- 💰 종목별 평가액 & 포트폴리오 합산 손익 계산
- 📊 포트폴리오 vs 개별 종목 수익률 비교 차트
- 🎯 수익률 구간별 코멘트
""")
        _kakao_pay_button(_local_ip, 8501, key="tab7")
    else:
        st.markdown("#### 💰 포트폴리오 시뮬레이터")
        st.caption("최대 3개 종목에 비중을 배분하여 특정 날짜에 투자했다면 지금 얼마일지 계산합니다.")
        ''

        # 투자 날짜 / 총 금액
        col_a, col_b = st.columns(2)
        with col_a:
            invest_date = st.date_input(
                "투자 날짜", (datetime.today() - timedelta(days=365)).date(),
                min_value=date(2000, 1, 1), max_value=datetime.today().date(),
                key="invest_date")
        with col_b:
            invest_amount = st.number_input(
                f"총 투자 금액 ({currency})", min_value=1, max_value=10_000_000_000,
                value=1_000_000 if currency == '원' else (10_000 if currency == 'USD' else 100_000),
                step=100_000 if currency == '원' else (1_000 if currency == 'USD' else 10_000),
                key="invest_amount")

        # 종목 / 비중 설정
        st.markdown("**종목 및 비중 설정** (합계 = 100%)")
        _port_colors = ['#F39C12', '#3498DB', '#2ECC71']
        _port_stocks = []

        # 종목 1: 현재 선택 종목 고정
        r1c, r1w = st.columns([4, 1])
        r1c.markdown(f"**① {selected_name.split('(')[0].strip()}** ({selected_code})")
        w1 = r1w.number_input("비중%", 1, 100, 60, key="pw1", label_visibility="collapsed")
        _port_stocks.append((selected_code, selected_name.split("(")[0].strip(), w1))

        # 종목 2, 3: 선택 가능
        _avail = ["없음"] + [s for s in stock_list if s != selected_name]
        for _i, (_sk, _wk, _icon, _dw) in enumerate([("ps2","pw2","②",30), ("ps3","pw3","③",10)]):
            r_c, r_w = st.columns([4, 1])
            _choice = r_c.selectbox(f"{_icon} 종목 추가 (선택)", _avail, key=_sk)
            if _choice != "없음":
                _wv = r_w.number_input("비중%", 0, 100, _dw, key=_wk, label_visibility="collapsed")
                _port_stocks.append((_choice.split("(")[-1].replace(")", ""),
                                     _choice.split("(")[0].strip(), _wv))
            else:
                r_w.empty()

        _total_w = sum(s[2] for s in _port_stocks)
        if _total_w == 100:
            st.success(f"비중 합계: **100%** ✅")
        else:
            st.warning(f"비중 합계: **{_total_w}%** — 100%가 되도록 조정하세요.")

        if st.button("계산하기", key="calc_portfolio", disabled=(_total_w != 100)):
            with st.spinner("포트폴리오 계산 중..."):
                _port_data = {}
                for _code, _name, _w in _port_stocks:
                    try:
                        _h = getData(_code, invest_date, datetime.today().date())
                        if not _h.empty:
                            _port_data[_code] = (_name, _w, _h)
                    except Exception:
                        st.warning(f"{_name}: 데이터 로드 실패")

                if not _port_data:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    fig_port = go.Figure()
                    _portfolio_val = None
                    _summary = []

                    for _idx, (_code, (_name, _w, _h)) in enumerate(_port_data.items()):
                        _buy  = _h['Close'].iloc[0]
                        _curr = _h['Close'].iloc[-1]
                        _alloc = invest_amount * _w / 100
                        _vals  = (_h['Close'] / _buy) * _alloc
                        _ret   = (_curr / _buy - 1) * 100

                        fig_port.add_trace(go.Scatter(
                            x=_h.index, y=_vals,
                            name=f"{_name} ({_w}%)",
                            line=dict(color=_port_colors[_idx], width=1.5, dash='dot' if _idx > 0 else 'solid'),
                            opacity=0.75
                        ))

                        _portfolio_val = _vals if _portfolio_val is None else _portfolio_val.add(_vals, fill_value=0)
                        _summary.append({
                            "종목": _name, "비중": f"{_w}%",
                            "실제 매수일": str(_h.index[0].date()),
                            f"매수가": fmt_price(_buy, currency),
                            f"현재가": fmt_price(_curr, currency),
                            "수익률": f"{_ret:+.2f}%",
                            f"배분 원금": fmt_price(_alloc, currency),
                            f"현재 평가액": fmt_price(_vals.iloc[-1], currency),
                        })

                    # 포트폴리오 합계 라인
                    fig_port.add_trace(go.Scatter(
                        x=_portfolio_val.index, y=_portfolio_val,
                        name="포트폴리오 합계",
                        line=dict(color='#ECF0F1', width=3),
                        fill='tozeroy', fillcolor='rgba(236,240,241,0.08)'
                    ))
                    fig_port.add_hline(y=invest_amount, line_dash='dash', line_color='gray', opacity=0.6,
                                       annotation_text=f'원금 {fmt_price(invest_amount, currency)}',
                                       annotation_position='right')
                    fig_port.update_layout(
                        height=400, template=_template,
                        yaxis_title=f'평가액 ({currency})', xaxis_title='날짜',
                        legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1),
                        margin=dict(l=10, r=10, t=40, b=10), hovermode='x unified'
                    )
                    st.plotly_chart(fig_port, config=_PLOTLY_CONFIG, width='stretch')

                    # 요약 지표
                    _total_curr = _portfolio_val.iloc[-1]
                    _total_ret  = (_total_curr / invest_amount - 1) * 100
                    _profit     = _total_curr - invest_amount
                    st.markdown("---")
                    cm1, cm2, cm3 = st.columns(3)
                    cm1.metric("총 투자 원금", fmt_price(invest_amount, currency))
                    cm2.metric("현재 포트폴리오 평가액", fmt_price(_total_curr, currency))
                    _pref = "+" if _profit >= 0 else ""
                    cm3.metric("포트폴리오 손익",
                               f"{_pref}{fmt_price(abs(_profit), currency)}",
                               delta=f"{_total_ret:+.2f}%")

                    st.markdown("#### 종목별 현황")
                    _summary_df = pd.DataFrame(_summary)
                    st.dataframe(_summary_df, hide_index=True, width='stretch')
                    st.download_button(
                        "📥 결과 CSV 다운로드",
                        data=_summary_df.to_csv(index=False).encode('utf-8-sig'),
                        file_name=f"portfolio_{datetime.today().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )

                    if _total_ret >= 20:
                        st.success(f"🎉 {_total_ret:.2f}% 수익! 훌륭한 포트폴리오입니다.")
                    elif _total_ret > 0:
                        st.success(f"📈 {_total_ret:.2f}% 수익 중입니다.")
                    elif _total_ret > -10:
                        st.warning(f"📊 {abs(_total_ret):.2f}% 손실 중입니다.")
                    else:
                        st.error(f"📉 {abs(_total_ret):.2f}% 손실 중입니다.")


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
