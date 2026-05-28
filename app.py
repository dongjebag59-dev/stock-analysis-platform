
# 필요한 라이브러리
import streamlit as st
import FinanceDataReader as fdr
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta, date
from streamlit_lottie import st_lottie
import requests
from bs4 import BeautifulSoup
import json
import os
import pandas as pd
import socket
import streamlit.components.v1 as components
from io import BytesIO
try:
    import qrcode
    _HAS_QR = True
except ImportError:
    _HAS_QR = False


# 한글 폰트 설정 (matplotlib 차트용)
_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "NanumSquareR.ttf")
if os.path.exists(_font_path):
    fm.fontManager.addfont(_font_path)
    plt.rcParams['font.family'] = 'NanumSquareR'
plt.rcParams['axes.unicode_minus'] = False


# 관심종목 저장 파일
FAVORITES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")

# 지원 마켓 정보 (한국 + 해외)
MARKET_INFO = {
    'KOSPI':  {'display': 'KOSPI 🇰🇷',           'currency': '원',  'decimal': 0},
    'KOSDAQ': {'display': 'KOSDAQ 🇰🇷',          'currency': '원',  'decimal': 0},
    'KONEX':  {'display': 'KONEX 🇰🇷',           'currency': '원',  'decimal': 0},
    'NYSE':   {'display': 'NYSE 🇺🇸 (뉴욕)',       'currency': 'USD', 'decimal': 2},
    'NASDAQ': {'display': 'NASDAQ 🇺🇸 (나스닥)',   'currency': 'USD', 'decimal': 2},
    'TSE':    {'display': 'TSE 🇯🇵 (도쿄)',        'currency': 'JPY', 'decimal': 0},
    'HKEX':   {'display': 'HKEX 🇨🇳 (홍콩)',      'currency': 'HKD', 'decimal': 2},
    'HOSE':   {'display': 'HOSE 🇻🇳 (베트남)',     'currency': 'VND', 'decimal': 0},
}
ALL_MARKETS = list(MARKET_INFO.keys())
MARKET_DISPLAYS = [MARKET_INFO[m]['display'] for m in ALL_MARKETS]
MARKET_FLAGS = {
    'KOSPI': '🇰🇷', 'KOSDAQ': '🇰🇷', 'KONEX': '🇰🇷',
    'NYSE': '🇺🇸', 'NASDAQ': '🇺🇸', 'TSE': '🇯🇵', 'HKEX': '🇨🇳', 'HOSE': '🇻🇳',
}

def fmt_price(value, currency, decimal=None):
    d = decimal if decimal is not None else (0 if currency in ('원', 'JPY', 'VND') else 2)
    return f"{value:,.{d}f} {currency}"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# ── 카카오페이 설정 ──
try:
    _KAKAO_KEY = st.secrets.get("KAKAO_ADMIN_KEY", "")
except Exception:
    _KAKAO_KEY = ""
_KAKAO_KEY = _KAKAO_KEY or os.environ.get("KAKAO_ADMIN_KEY", "")
_KAKAO_CID = "TC0ONETIME"  # 카카오페이 단건결제 테스트 CID

def _kakao_ready(local_ip: str, port: int = 8501) -> dict:
    order_id = f"premium_{int(datetime.now().timestamp())}"
    base = f"http://{local_ip}:{port}"
    resp = requests.post(
        "https://kapi.kakao.com/v1/payment/ready",
        headers={"Authorization": f"KakaoAK {_KAKAO_KEY}"},
        data={
            "cid": _KAKAO_CID,
            "partner_order_id": order_id,
            "partner_user_id": "stock_user",
            "item_name": "주식분석플랫폼 프리미엄",
            "quantity": 1,
            "total_amount": 9900,
            "vat_amount": 900,
            "tax_free_amount": 0,
            "approval_url": f"{base}?payment=approve",
            "fail_url":     f"{base}?payment=fail",
            "cancel_url":   f"{base}?payment=cancel",
        },
        timeout=10,
    )
    result = resp.json()
    result["_order_id"] = order_id
    return result

def _kakao_approve(tid: str, pg_token: str, order_id: str) -> dict:
    resp = requests.post(
        "https://kapi.kakao.com/v1/payment/approve",
        headers={"Authorization": f"KakaoAK {_KAKAO_KEY}"},
        data={
            "cid": _KAKAO_CID,
            "tid": tid,
            "partner_order_id": order_id,
            "partner_user_id": "stock_user",
            "pg_token": pg_token,
        },
        timeout=10,
    )
    return resp.json()

def _kakao_pay_button(local_ip: str, port: int = 8501, key: str = "pay"):
    """카카오페이 결제 버튼 공통 컴포넌트"""
    if not _KAKAO_KEY:
        if st.button("💎 프리미엄 시작하기 (데모)", type="primary", use_container_width=True, key=f"demo_{key}"):
            st.session_state.is_premium = True
            st.rerun()
        st.caption("ℹ️ KAKAO_ADMIN_KEY 미설정 상태입니다. 데모 모드로 즉시 활성화됩니다.")
        return
    if st.button("💛 카카오페이로 결제 (월 ₩9,900)", type="primary", use_container_width=True, key=f"kakao_{key}"):
        try:
            res = _kakao_ready(local_ip, port)
            if "tid" in res:
                st.session_state.kakao_tid = res["tid"]
                st.session_state.kakao_order_id = res["_order_id"]
                redirect_url = res.get("next_redirect_pc_url", "")
                components.html(
                    f"<script>window.top.location.href='{redirect_url}';</script>",
                    height=0,
                )
            else:
                st.error(f"결제 준비 실패: {res.get('msg', '알 수 없는 오류')}")
        except Exception as e:
            st.error(f"카카오페이 연결 오류: {e}")

@st.cache_data
def make_qr(url):
    if not _HAS_QR:
        return None
    qr = qrcode.QRCode(version=1, box_size=6, border=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_favorites(favs):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)


# 페이지 설정
st.set_page_config(
    page_title="주식 분석 통합 플랫폼",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "fav_code" not in st.session_state:
    st.session_state.fav_code = None
if "fav_market" not in st.session_state:
    st.session_state.fav_market = None
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "kakao_tid" not in st.session_state:
    st.session_state.kakao_tid = None
if "kakao_order_id" not in st.session_state:
    st.session_state.kakao_order_id = None
if "payment_msg" not in st.session_state:
    st.session_state.payment_msg = None

# ── 카카오페이 콜백 처리 ──
_qp = st.query_params
_payment_status = _qp.get("payment", "")
if _payment_status == "approve" and st.session_state.kakao_tid:
    _pg_token = _qp.get("pg_token", "")
    try:
        _res = _kakao_approve(
            st.session_state.kakao_tid,
            _pg_token,
            st.session_state.kakao_order_id or "premium",
        )
        if "aid" in _res:
            st.session_state.is_premium = True
            st.session_state.payment_msg = "success"
        else:
            st.session_state.payment_msg = f"오류: {_res.get('msg', '결제 승인 실패')}"
    except Exception as _e:
        st.session_state.payment_msg = f"오류: {_e}"
    finally:
        st.session_state.kakao_tid = None
    st.query_params.clear()
    st.rerun()
elif _payment_status in ("fail", "cancel"):
    st.session_state.payment_msg = "결제가 취소되었습니다."
    st.query_params.clear()
    st.rerun()


# 로티 붙이기
@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_url = "https://lottie.host/ec84bdca-8c08-41de-90cc-9bd58157f679/ooMiQcJ1eO.json"
lottie_json = load_lottieurl(lottie_url)


# 로컬 IP (결제 콜백 URL에 재사용)
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


# 강사님이 지정해주신 함수(시장 데이터 읽어오는 함수) + 캐시 추가로 최적화
@st.cache_data
def getData(code, datestart, dateend):
    try:
        df = fdr.DataReader(code, datestart, dateend)
        if 'Change' in df.columns:
            df = df.drop(columns='Change')
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data
def getSymbols(market='KOSPI', sort='Marcap'):
    df = fdr.StockListing(market)
    if market in ('KOSPI', 'KOSDAQ', 'KONEX'):
        ascending = False if sort == 'Marcap' else True
        df.sort_values(by=[sort], ascending=ascending, inplace=True)
        return df[['Code', 'Name', 'Market']]
    # 해외 마켓: 컬럼 이름 정규화
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
    if 'Code' not in df.columns:
        df = df.rename(columns={df.columns[0]: 'Code'})
    if 'Name' not in df.columns:
        df = df.rename(columns={df.columns[1]: 'Name'})
    df['Market'] = market
    result = df[['Code', 'Name', 'Market']].dropna(subset=['Code', 'Name'])
    return result[result['Code'].astype(str).str.strip() != ''].head(2000)

@st.cache_data(ttl=1800)
def get_google_news(stock_name, max_news=3):
    query = stock_name.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}+주식&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "xml")
    items = soup.find_all("item")[:max_news]
    news_list = []
    for item in items:
        news_list.append({
            "title": item.title.text,
            "link": item.link.text,
            "date": item.pubDate.text
        })
    return news_list

def addBollingerBand(data, ax):
    df = data.reset_index(drop=True)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['StDev'] = df['Close'].rolling(window=20).std()
    df['Upper'] = df['MA20'] + (df['StDev'] * 2)
    df['Lower'] = df['MA20'] - (df['StDev'] * 2)
    df = df[19:]
    ax.plot(df.index, df['Upper'], color='red', linestyle='--', linewidth=1.5, label='Upper')
    ax.plot(df.index, df['MA20'], color='aqua', linestyle=':', linewidth=2, label='MA20')
    ax.plot(df.index, df['Lower'], color='blue', linestyle='--', linewidth=1.5, label='Lower')
    ax.fill_between(df.index, df['Upper'], df['Lower'], color='grey', alpha=0.3)
    ax.legend(loc='best')


# 사이드바 (Sidebar)
with st.sidebar:
    st.header("⚙️ 차트 설정")
    st.caption("종목과 기간을 선택한 뒤 '확인'을 누르세요.")
    ''

    # 플랜 표시
    if st.session_state.is_premium:
        st.success("💎 **프리미엄 플랜** 이용 중")
        if st.button("🔄 무료 플랜으로 전환 (데모)", use_container_width=True):
            st.session_state.is_premium = False
            st.rerun()
    else:
        st.info("🆓 **무료 플랜** 이용 중")
        _kakao_pay_button(_local_ip, 8501, key="sidebar")
    st.markdown("---")

    # 관심종목 즐겨찾기 섹션
    favorites = load_favorites()
    if favorites:
        st.markdown("#### ⭐ 관심 종목")
        market_icons = {
            'KOSPI': '🇰🇷', 'KOSDAQ': '🇰🇷', 'KONEX': '🇰🇷',
            'NYSE': '🇺🇸', 'NASDAQ': '🇺🇸', 'TSE': '🇯🇵', 'HKEX': '🇨🇳', 'HOSE': '🇻🇳',
        }
        for fav in favorites:
            icon = market_icons.get(fav.get('market', ''), "⬜")
            c1, c2 = st.columns([4, 1])
            with c1:
                name_short = fav['name'].split('(')[0].strip()
                if st.button(f"{icon} {name_short}", key=f"fav_{fav['code']}"):
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

    # 마켓 선택 (관심종목 클릭 시 자동 설정)
    market_idx = ALL_MARKETS.index(st.session_state.fav_market) \
        if st.session_state.fav_market in ALL_MARKETS else 0
    selected_market_display = st.selectbox('마켓 선택', MARKET_DISPLAYS, index=market_idx)
    z = ALL_MARKETS[MARKET_DISPLAYS.index(selected_market_display)]
    currency = MARKET_INFO[z]['currency']

    symbols = getSymbols(z)
    symbols['Display'] = symbols['Name'] + " (" + symbols['Code'] + ")"
    e2 = st.empty()

    # 관심종목 클릭 시 해당 종목 자동 선택
    stock_list = list(symbols['Display'])
    default_stock_idx = 0
    if st.session_state.fav_code:
        matching = symbols[symbols['Code'] == st.session_state.fav_code]
        if not matching.empty:
            fav_display = matching.iloc[0]['Name'] + " (" + matching.iloc[0]['Code'] + ")"
            if fav_display in stock_list:
                default_stock_idx = stock_list.index(fav_display)

    with st.form(key='myForm1', clear_on_submit=False):
        selected_name = st.selectbox("종목 선택", symbols['Display'], index=default_stock_idx)
        selected_code = selected_name.split("(")[-1].replace(")", "")

        # 날짜 입력(시작일/종료일 설정)
        date_start = st.date_input("시작일 입력",
            (datetime.today() - timedelta(days=365)).date())
        date_end = st.date_input("종료일 입력", datetime.today().date())

        # 차트 유형 선택
        chart_type = st.selectbox("차트 유형(type)", ["candle", "ohlc", "line"])
        chart_style = st.selectbox("차트 스타일(style)", ["default", "binance", "yahoo"])

        # 볼린저 밴드 표시 체크박스
        show_bollinger = st.checkbox(
            "볼린저밴드 표시", value=True,
            help="20일 이동평균(MA20) ±2σ 구간을 표시합니다. 가격이 하단 밴드에 닿으면 반등 가능성이 높아집니다.")

        # 비교 종목 선택 (최대 2개)
        other_symbols = [s for s in symbols['Display'] if s != selected_name]
        compare_names = st.multiselect("비교 종목 선택 (최대 2개)", other_symbols, max_selections=2)

        ''
        if date_start > date_end:
            st.error("시작일이 종료일보다 늦습니다. 다시 선택해주세요!")
        submitted = st.form_submit_button('확인')

    # QR 코드 — 모바일 버전 바로가기
    st.markdown("---")
    _ip = get_local_ip()
    _mobile_url = f"http://{_ip}:8502"
    st.markdown("#### 📱 모바일 버전 바로가기")
    if _HAS_QR:
        _qr = make_qr(_mobile_url)
        if _qr:
            st.image(_qr, width=170)
    st.caption(_mobile_url)
    st.markdown("---")

    # 관심종목 추가 버튼 (폼 밖)
    if st.button("⭐ 현재 종목 관심목록에 추가"):
        favorites = load_favorites()
        if any(f['code'] == selected_code for f in favorites):
            st.info("이미 추가된 종목입니다.")
        else:
            favorites.append({"code": selected_code, "name": selected_name, "market": z})
            save_favorites(favorites)
            st.success(f"'{selected_name.split('(')[0].strip()}' 추가됨!")
            st.rerun()


# 메인 주식 그래프 (확인 버튼 누르면 활성화)
df = getData(selected_code, date_start, date_end)
if submitted:
    st.subheader(f"▪️선택 종목  : :blue[{selected_name} (**{z}**) ]")
    marketcolors = mpf.make_marketcolors(up='red', down='blue', ohlc={'up': 'red', 'down': 'blue'})
    mpf_style = mpf.make_mpf_style(base_mpf_style=chart_style, marketcolors=marketcolors)

    fig, ax = mpf.plot(
        data=df,
        volume=False,
        type=chart_type,
        style=mpf_style,
        figsize=(10, 7),
        fontscale=1.1,
        mav=(5, 10, 30),
        mavcolors=('red', 'green', 'blue'),
        returnfig=True)

    if show_bollinger:
        addBollingerBand(df, ax[0])
    st.pyplot(fig)

''
''
''


# 탭 (프리미엄 여부에 따라 잠금 아이콘 표시)
_lock = "" if st.session_state.is_premium else " 🔒"
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    '**요약** :speech_balloon:', '**기간별 통계분석** :speech_balloon:',
    '**뉴스** :speech_balloon:', '**거래량** :speech_balloon:',
    f'**투자 지표**{_lock}', f'**종목 비교**{_lock}',
    f'**포트폴리오 시뮬레이터**{_lock}', '**💎 요금제**'])


with tab1:  # 요약
    if not df.empty:
        latest_close = df['Close'].iloc[-1]
        period_high = df['Close'].max()
        period_low = df['Close'].min()
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        return_pct = (end_price - start_price) / start_price * 100

        ''
        st.markdown(f"- **종목명:** {selected_name.split(' ')[0]}")
        st.markdown(f"- **종목 코드:** {selected_code}")
        st.markdown(f"- **최신 종가:** {fmt_price(latest_close, currency)}")
        st.markdown(f"- **기간 내 최고가:** {fmt_price(period_high, currency)}")
        st.markdown(f"- **기간 내 최저가:** {fmt_price(period_low, currency)}")
        if return_pct > 0:
            st.markdown(f"- **선택 기간 수익률:** :red[{return_pct:.2f}%] 📈")
        elif return_pct < 0:
            st.markdown(f"- **선택 기간 수익률:** :blue[{return_pct:.2f}%] 📉")
        else:
            st.markdown(f"- **선택 기간 수익률:** {return_pct:.2f}%")

        # RSI 빠른 신호 요약
        if len(df) >= 20:
            _delta = df['Close'].diff()
            _gain = _delta.where(_delta > 0, 0.0)
            _loss = -_delta.where(_delta < 0, 0.0)
            _rsi = 100 - (100 / (1 + _gain.rolling(14).mean() / _loss.rolling(14).mean()))
            _rsi_val = _rsi.iloc[-1]
            st.markdown("---")
            st.markdown("**📊 현재 RSI 신호**")
            if _rsi_val >= 70:
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

        st.markdown("---")
        st.markdown("##### **1. 현재 주가 위치**")
        if latest_close > period_mean:
            st.markdown(f"📈 **현재 종가** ({fmt_price(latest_close, currency)})는 **선택된 기간 평균** ({fmt_price(period_mean, currency)})보다 **높습니다.**")
        elif latest_close < period_mean:
            st.markdown(f"📉 **현재 종가** ({fmt_price(latest_close, currency)})는 기간 평균 ({fmt_price(period_mean, currency)})보다 **낮습니다.**")
        else:
            st.info("현재 종가가 기간 평균과 거의 같습니다.")

        st.markdown("---")
        st.markdown("##### **2. 기간 내 가격 분포**")
        price_range = period_max - period_min
        st.markdown(f"- **최고가**: :red[{fmt_price(period_max, currency)}]")
        st.markdown(f"- **최저가**: :blue[{fmt_price(period_min, currency)}]")
        st.markdown(f"- **차이**: {fmt_price(price_range, currency)}")
        st.markdown(f"현재 종가는 최저가 대비 **{(latest_close - period_min) / price_range * 100:.1f}%** 지점에 있습니다.")
    else:
        st.info("기간 통계를 계산하기 위한 데이터가 부족합니다.")


with tab3:  # 뉴스
    inner_tab1, inner_tab2 = st.tabs(["국내", "국외"])
    with inner_tab1:
        st.subheader("국내 증시 뉴스")
        naver_url = f'https://finance.naver.com/item/main.naver?code={selected_code}'
        ''
        st.markdown(f"#### ***✅ N Pay 증권 '{selected_name.split('(')[0]}' 검색결과***")
        st.markdown(f"[N pay증권 {selected_name} 바로가기]({naver_url})")
        st.markdown("---")
        st.markdown("#### 📰 ***관련 최신 뉴스 (Google)***")
        try:
            stock_name_only = selected_name.split("(")[0]
            news_list = get_google_news(stock_name_only, max_news=3)
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
        st.markdown("#### :newspaper: :gray[The Wall Street Journel]")
        WSJ_url = f"https://www.wsj.com/market-data/quotes/KR/XKRX/{selected_name.split('(')[-1].replace(')', '')}?mod=searchresults_companyquotes"
        st.markdown(f"[월스트리트 저널에서 '{selected_name.split('(')[0]}' 검색결과 바로가기]({WSJ_url})")
        st.warning("⚠️ 종목에 따라 뉴스 정보가 존재하지 않을 수도 있습니다.")
        st.markdown("---")
        st.markdown("#### :newspaper: :gray[Bloomberg Markets]")
        st.markdown(f" - [블룸버그 마켓 섹션 구경하기](https://www.bloomberg.com/markets)")
        ''
        st.markdown("#### :newspaper: :gray[Reuters News]")
        st.markdown(f" - [로이터 뉴스 속보 둘러보기](https://www.reuters.com/markets/)")


with tab4:  # 거래량
    ''
    volume_addplot = mpf.make_addplot(
        df['Volume'].values, type='bar', panel=0,
        color='blue', alpha=0.7, ylabel='Volume_bar')

    fig_volume, ax_volume = mpf.plot(
        data=df, volume=False, type='line',
        style=chart_style, figsize=(10, 4),
        returnfig=True, addplot=volume_addplot, mav=())
    st.pyplot(fig_volume)

    st.markdown("---")
    st.markdown("#### 📊 거래량 주요 통계")
    ''
    avg_volume = df['Volume'].mean()
    max_volume_date = df['Volume'].idxmax().strftime('%Y년 %m월 %d일')
    max_volume = df['Volume'].max()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="평균 거래량", value=f"{int(avg_volume):,}")
    with col2:
        st.metric(label="최대 거래량", value=f"{int(max_volume):,}")
    with col3:
        st.markdown(f"**최대 거래량 날짜**")
        st.write(f"**{max_volume_date}**")

    if df['Volume'].iloc[-1] > avg_volume * 1.5:
        st.warning("최근 거래량이 평균 대비 크게 증가했습니다.")
    else:
        st.info("거래량은 평균 수준입니다.")


with tab5:  # 투자 지표
    if not st.session_state.is_premium:
        st.markdown("### 🔒 프리미엄 전용 기능")
        st.warning("RSI · MACD · 연환산 변동성 지표는 **프리미엄 플랜**에서만 이용하실 수 있습니다.")
        ''
        col_lock1, col_lock2 = st.columns([1, 1])
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
        st.caption("👈 사이드바의 '프리미엄 무료 체험하기'로 먼저 모든 기능을 체험해 보세요.")
    elif not df.empty and len(df) >= 20:
        ''
        close = df['Close']
        returns = close.pct_change().dropna()

        period_return = (close.iloc[-1] / close.iloc[0] - 1) * 100
        volatility = returns.std() * (252 ** 0.5) * 100

        col1, col2 = st.columns(2)
        with col1:
            st.metric("📆 기간 수익률", f"{period_return:.2f} %")
        with col2:
            st.metric("⚠️ 연환산 변동성", f"{volatility:.2f} %",
                      help="연환산 변동성: 20% 이하 안정적 | 20~40% 보통 | 40% 이상 고변동성")
        st.caption("💡 변동성이 높을수록 가격 등락이 크고 위험도가 높습니다.")
        st.markdown("---")

        # RSI 지표
        st.markdown("#### ▪️ RSI (상대강도지수)")
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_latest = rsi.iloc[-1]

        fig_rsi, ax_rsi = plt.subplots(figsize=(10, 2.5))
        ax_rsi.plot(close.index, rsi, color='#9B59B6', linewidth=1.5)
        ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.7, linewidth=1, label='과매수(70)')
        ax_rsi.axhline(y=30, color='blue', linestyle='--', alpha=0.7, linewidth=1, label='과매도(30)')
        ax_rsi.fill_between(close.index, rsi, 70, where=(rsi >= 70), alpha=0.25, color='red')
        ax_rsi.fill_between(close.index, rsi, 30, where=(rsi <= 30), alpha=0.25, color='blue')
        ax_rsi.set_ylim(0, 100)
        ax_rsi.set_ylabel('RSI')
        ax_rsi.set_title('RSI (14일)')
        ax_rsi.legend(loc='upper left', fontsize=9)
        ax_rsi.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig_rsi)

        if rsi_latest >= 70:
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

        # MACD 지표 (신규)
        st.markdown("#### ▪️ MACD (이동평균 수렴·발산)")
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line

        fig_macd, ax_macd = plt.subplots(figsize=(10, 3))
        ax_macd.plot(close.index, macd_line, color='#4ECDC4', label='MACD', linewidth=1.5)
        ax_macd.plot(close.index, signal_line, color='#FF6B6B', label='Signal', linewidth=1.5)
        bar_colors = ['#FF6B6B' if v >= 0 else '#4169E1' for v in macd_hist]
        ax_macd.bar(close.index, macd_hist, color=bar_colors, alpha=0.5, label='Histogram', width=1)
        ax_macd.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax_macd.legend(loc='best', fontsize=9)
        ax_macd.set_title('MACD (12, 26, 9)')
        ax_macd.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig_macd)

        macd_now = macd_line.iloc[-1]
        signal_now = signal_line.iloc[-1]
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

> 추세가 뚜렷할 때 잘 작동하며, 횡보장에서는 신뢰도가 떨어질 수 있습니다.
""")
        st.markdown("---")

        # 최근 n일 수익률
        st.markdown("#### ▪️ 최근 수익률")
        col1, col2, col3 = st.columns(3)
        for col, n in zip([col1, col2, col3], [1, 5, 20]):
            recent_return = (close.iloc[-1] / close.iloc[-n-1] - 1) * 100
            with col:
                st.metric(f"{n}일 수익률", f"{recent_return:.2f} %")
    else:
        st.info("지표 계산을 위한 데이터가 부족합니다. (최소 20일 이상 필요)")


with tab6:  # 종목 비교 (신규)
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
            st.info("👈 사이드바 '비교 종목 선택'에서 종목을 1개 이상 추가한 뒤 '확인'을 눌러주세요.")
        else:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
            fig_comp, ax_comp = plt.subplots(figsize=(12, 5))
            summary_rows = []

            for i, name in enumerate(all_compare):
                code = name.split("(")[-1].replace(")", "")
                try:
                    d = getData(code, date_start, date_end)
                    if not d.empty:
                        normalized = (d['Close'] / d['Close'].iloc[0] - 1) * 100
                        label = name.split("(")[0].strip()
                        ax_comp.plot(d.index, normalized, label=label,
                                     color=colors[i % len(colors)], linewidth=2)
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

            ax_comp.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            ax_comp.set_ylabel('누적 수익률 (%)')
            ax_comp.set_xlabel('날짜')
            ax_comp.legend(loc='best')
            ax_comp.set_title('누적 수익률 비교 (%)')
            ax_comp.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig_comp)

            if summary_rows:
                st.markdown("#### 요약 비교표")
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


with tab7:  # 포트폴리오 시뮬레이터 (신규)
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
                "투자 날짜",
                (datetime.today() - timedelta(days=365)).date(),
                min_value=date(2000, 1, 1),
                max_value=datetime.today().date(),
                key="invest_date")
        with col_b:
            invest_amount = st.number_input(
                f"투자 금액 ({currency})",
                min_value=1,
                max_value=10_000_000_000,
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
                    actual_buy_date = hist_df.index[0].strftime('%Y년 %m월 %d일')

                    shares = invest_amount / buy_price
                    current_value = shares * current_price
                    profit = current_value - invest_amount
                    return_pct = (current_value / invest_amount - 1) * 100

                    st.markdown("---")
                    st.markdown(f"**실제 매수일:** {actual_buy_date} (가장 가까운 거래일)")
                    st.markdown(f"**매수 가격:** {fmt_price(buy_price, currency)} / 주")
                    st.markdown(f"**매수 수량:** {shares:.4f} 주")
                    ''

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("투자 원금", fmt_price(invest_amount, currency))
                    with c2:
                        st.metric("현재 평가액", fmt_price(current_value, currency))
                    with c3:
                        prefix = "+" if profit >= 0 else ""
                        st.metric("손익", f"{prefix}{fmt_price(abs(profit), currency)}", delta=f"{return_pct:.2f}%")

                    # 투자 기간 내 평가액 변화 차트
                    invest_values = (hist_df['Close'] / buy_price) * invest_amount
                    fig_port, ax_port = plt.subplots(figsize=(10, 3.5))
                    ax_port.plot(hist_df.index, invest_values, color='#2ECC71', linewidth=2, label='평가액')
                    ax_port.axhline(y=invest_amount, color='gray', linestyle='--', linewidth=1.5,
                                    label=f'원금 ({fmt_price(invest_amount, currency)})')
                    ax_port.fill_between(hist_df.index, invest_values, invest_amount,
                                         where=(invest_values >= invest_amount),
                                         alpha=0.25, color='green', label='수익 구간')
                    ax_port.fill_between(hist_df.index, invest_values, invest_amount,
                                         where=(invest_values < invest_amount),
                                         alpha=0.25, color='red', label='손실 구간')
                    ax_port.set_ylabel(f'평가액 ({currency})')
                    ax_port.set_title('투자 기간 내 평가액 변화')
                    ax_port.legend(loc='best', fontsize=9)
                    ax_port.grid(True, alpha=0.3)
                    plt.tight_layout()
                    st.pyplot(fig_port)

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
<div style="border: 2px solid #ddd; border-radius: 12px; padding: 24px; text-align: center;">
<h2>🆓 무료 플랜</h2>
<h1 style="color: #666;">₩0</h1>
<p style="color: gray;">영구 무료</p>
<hr>
</div>
""", unsafe_allow_html=True)
        st.markdown("""
**포함 기능:**
- ✅ 국내 3개 + 해외 5개 마켓 전 종목 조회
- ✅ 캔들 · OHLC · 라인 차트
- ✅ 볼린저밴드 표시
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
<div style="border: 3px solid #FFD700; border-radius: 12px; padding: 24px; text-align: center; background: linear-gradient(135deg, #fff9e6, #fffdf5);">
<h2>💎 프리미엄 플랜</h2>
<h1 style="color: #E6A817;">₩9,900</h1>
<p style="color: gray;">월 구독 · 언제든 해지 가능</p>
<hr>
</div>
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
            if st.button("무료 플랜으로 전환 (데모)", use_container_width=True):
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
