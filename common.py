"""공통 상수·유틸·카카오페이 함수 — app.py와 app_mobile.py 양쪽에서 import"""

import os
import json
import socket
from datetime import datetime
from io import BytesIO

import requests
import streamlit as st

# ── 마켓 정보 ──
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

# WSJ 마켓별 거래소 코드
WSJ_EXCHANGE = {
    'KOSPI': 'KR/XKRX', 'KOSDAQ': 'KR/XKOS', 'KONEX': 'KR/XKON',
    'NYSE': 'US/XNYS', 'NASDAQ': 'US/XNAS',
    'TSE': 'JP/XTKS', 'HKEX': 'HK/XHKG', 'HOSE': 'VN/XHOSE',
}

FAVORITES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")

# ── 유틸 함수 ──
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

def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_favorites(favs):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)

# ── QR 코드 ──
try:
    import qrcode as _qrcode
    _HAS_QR = True
except ImportError:
    _HAS_QR = False

@st.cache_data
def make_qr(url: str, color: str = "#1a1a2e"):
    if not _HAS_QR:
        return None
    qr = _qrcode.QRCode(version=1, box_size=6, border=3,
                         error_correction=_qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=color, back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# ── 카카오페이 ──
try:
    _KAKAO_KEY = st.secrets.get("KAKAO_ADMIN_KEY", "")
except Exception:
    _KAKAO_KEY = ""
_KAKAO_KEY = _KAKAO_KEY or os.environ.get("KAKAO_ADMIN_KEY", "")
_KAKAO_CID = "TC0ONETIME"

def _kakao_ready(local_ip: str, port: int) -> dict:
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

def kakao_pay_button(local_ip: str, port: int, key: str = "pay", mobile: bool = False):
    """카카오페이 결제 버튼 공통 컴포넌트"""
    import streamlit.components.v1 as components
    if not _KAKAO_KEY:
        if st.button("💎 프리미엄 시작하기 (데모)", type="primary",
                     use_container_width=True, key=f"demo_{key}"):
            st.session_state.is_premium = True
            st.rerun()
        st.caption("ℹ️ KAKAO_ADMIN_KEY 미설정 — 데모 모드")
        return
    if st.button("💛 카카오페이로 결제 (월 ₩9,900)", type="primary",
                 use_container_width=True, key=f"kakao_{key}"):
        try:
            res = _kakao_ready(local_ip, port)
            if "tid" in res:
                st.session_state.kakao_tid = res["tid"]
                st.session_state.kakao_order_id = res["_order_id"]
                url_key = "next_redirect_mobile_url" if mobile else "next_redirect_pc_url"
                redirect_url = res.get(url_key, res.get("next_redirect_pc_url", ""))
                components.html(
                    f"<script>window.top.location.href='{redirect_url}';</script>",
                    height=0,
                )
            else:
                st.error(f"결제 준비 실패: {res.get('msg', '알 수 없는 오류')}")
        except Exception as e:
            st.error(f"카카오페이 연결 오류: {e}")

def handle_kakao_callback():
    """페이지 최상단에서 카카오페이 콜백 query param을 처리"""
    qp = st.query_params
    status = qp.get("payment", "")
    if status == "approve" and st.session_state.get("kakao_tid"):
        try:
            res = _kakao_approve(
                st.session_state.kakao_tid,
                qp.get("pg_token", ""),
                st.session_state.get("kakao_order_id") or "premium",
            )
            st.session_state.payment_msg = "success" if "aid" in res else f"오류: {res.get('msg', '결제 승인 실패')}"
            if "aid" in res:
                st.session_state.is_premium = True
        except Exception as e:
            st.session_state.payment_msg = f"오류: {e}"
        finally:
            st.session_state.kakao_tid = None
        st.query_params.clear()
        st.rerun()
    elif status in ("fail", "cancel"):
        st.session_state.payment_msg = "결제가 취소되었습니다."
        st.query_params.clear()
        st.rerun()
