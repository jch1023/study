"""토스증권 Open API 클라이언트.

⚠️ 엔드포인트 경로와 요청/응답 스키마는 developers.tossinvest.com 문서가
로그인 뒤에서만 열려 있어 일반적인 REST 관례 기준의 추정값이다.
API 키를 발급받은 뒤 공식 문서와 대조해 아래 ``_ENDPOINTS`` 상수와
각 메서드의 파싱 부분만 수정하면 된다 — 다른 모듈은 이 클래스의
메서드 시그니처에만 의존한다.

MockTossClient 는 동일한 인터페이스의 오프라인 구현으로, 키 발급 전에
전체 흐름(파싱 → 계획 → dry-run)을 테스트할 때 사용한다.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

_BASE_URL = "https://openapi.tossinvest.com"  # TODO: 공식 문서로 확인

_ENDPOINTS = {
    "token": "/oauth2/token",
    "accounts": "/v1/accounts",
    "holdings": "/v1/accounts/{account_no}/positions",
    "balance": "/v1/accounts/{account_no}/balance",
    "quote": "/v1/market/quotes/{ticker}",
    "exchange_rate": "/v1/market/exchange-rate",
    "market_hours": "/v1/market/hours",
    "order": "/v1/orders",
    "order_status": "/v1/orders/{order_id}",
}

_TOKEN_CACHE = Path(__file__).resolve().parent.parent / ".token_cache.json"


class TossApiError(RuntimeError):
    pass


class TossClient:
    """토스증권 Open API REST 클라이언트 (OAuth 2.0 client credentials)."""

    def __init__(self, app_key: str, app_secret: str, base_url: str = _BASE_URL):
        if not app_key or not app_secret:
            raise TossApiError(
                "TOSS_APP_KEY / TOSS_APP_SECRET 이 설정되지 않았습니다. "
                ".env 파일을 확인하세요. (키 발급 전에는 --mock 모드를 사용)"
            )
        self._app_key = app_key
        self._app_secret = app_secret
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._token: str | None = None
        self._token_expiry: float = 0.0

    # ── 인증 ──────────────────────────────────────────────

    def _access_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        cached = self._load_cached_token()
        if cached:
            return cached
        resp = self._session.post(
            self._base_url + _ENDPOINTS["token"],
            data={
                "grant_type": "client_credentials",
                "client_id": self._app_key,
                "client_secret": self._app_secret,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            raise TossApiError(f"토큰 발급 실패 ({resp.status_code}): {resp.text[:200]}")
        body = resp.json()
        self._token = body["access_token"]
        self._token_expiry = time.time() + int(body.get("expires_in", 3600))
        _TOKEN_CACHE.write_text(
            json.dumps({"token": self._token, "expiry": self._token_expiry})
        )
        return self._token

    def _load_cached_token(self) -> str | None:
        try:
            cache = json.loads(_TOKEN_CACHE.read_text())
            if time.time() < cache["expiry"] - 60:
                self._token = cache["token"]
                self._token_expiry = cache["expiry"]
                return self._token
        except (OSError, ValueError, KeyError):
            pass
        return None

    # ── HTTP 공통 ─────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        url = self._base_url + path
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        for attempt in range(4):
            resp = self._session.request(method, url, headers=headers, timeout=15, **kwargs)
            if resp.status_code == 429:  # rate limit → 지수 백오프
                time.sleep(2 ** attempt)
                continue
            if resp.status_code >= 400:
                raise TossApiError(f"{method} {path} 실패 ({resp.status_code}): {resp.text[:300]}")
            return resp.json()
        raise TossApiError(f"{method} {path}: 레이트리밋 재시도 초과")

    # ── 조회 ──────────────────────────────────────────────

    def get_accounts(self) -> list[dict]:
        return self._request("GET", _ENDPOINTS["accounts"]).get("accounts", [])

    def get_holdings(self, account_no: str) -> dict[str, int]:
        """보유 미국 주식 {티커: 수량}."""
        body = self._request("GET", _ENDPOINTS["holdings"].format(account_no=account_no))
        return {
            p["symbol"]: int(p["quantity"])
            for p in body.get("positions", [])
            if p.get("market", "US") == "US"
        }

    def get_cash_balance_usd(self, account_no: str) -> float:
        """가용 현금 (USD 환산)."""
        body = self._request("GET", _ENDPOINTS["balance"].format(account_no=account_no))
        usd = float(body.get("usd_cash", 0))
        krw = float(body.get("krw_cash", 0))
        if krw > 0:
            usd += krw / self.get_usd_krw_rate()
        return usd

    def get_quote(self, ticker: str) -> float:
        """현재가 (USD). 조회 실패 시 TossApiError."""
        body = self._request("GET", _ENDPOINTS["quote"].format(ticker=ticker))
        return float(body["price"])

    def get_usd_krw_rate(self) -> float:
        body = self._request("GET", _ENDPOINTS["exchange_rate"], params={"pair": "USDKRW"})
        return float(body["rate"])

    def is_us_market_open(self) -> bool:
        """미국 시장(정규장 또는 토스 주간거래)이 주문 가능한 상태인지."""
        body = self._request("GET", _ENDPOINTS["market_hours"], params={"market": "US"})
        return bool(body.get("is_open", False))

    # ── 주문 ──────────────────────────────────────────────

    def place_order(
        self, account_no: str, ticker: str, side: str, quantity: int,
        order_type: str = "market", limit_price: float | None = None,
    ) -> str:
        """주문 제출 후 주문 ID 반환. side: BUY|SELL, order_type: market|limit."""
        payload = {
            "account_no": account_no,
            "symbol": ticker,
            "side": side.lower(),
            "quantity": quantity,
            "order_type": order_type,
        }
        if order_type == "limit":
            if limit_price is None:
                raise TossApiError("지정가 주문에는 limit_price 가 필요합니다.")
            payload["price"] = limit_price
        body = self._request("POST", _ENDPOINTS["order"], json=payload)
        return str(body["order_id"])

    def get_order_status(self, order_id: str) -> str:
        """주문 상태: FILLED | PARTIAL | OPEN | CANCELLED | REJECTED."""
        body = self._request("GET", _ENDPOINTS["order_status"].format(order_id=order_id))
        return str(body.get("status", "OPEN")).upper()

    def cancel_order(self, order_id: str) -> None:
        self._request("DELETE", _ENDPOINTS["order_status"].format(order_id=order_id))


class MockTossClient:
    """키 발급 전 오프라인 테스트용 가짜 클라이언트 (TossClient 와 동일 인터페이스)."""

    #: 모의 보유: INTC 는 리스트 제외 매도, AAPL 은 비중 조정 시나리오를 만들기 위한 값
    _HOLDINGS = {"INTC": 12, "AAPL": 5, "MOH": 2}
    _PRICES = {
        "AAPL": 232.50, "MSFT": 512.10, "NVDA": 178.30, "INTC": 23.40,
        "ONTO": 220.15, "MOH": 291.80, "ASAN": 14.25, "ALGM": 32.60,
        "GOOG": 196.40, "META": 745.20, "AMZN": 228.90, "TSLA": 315.60,
    }
    _DEFAULT_PRICE = 100.0

    def __init__(self) -> None:
        self._order_seq = 0
        self.placed_orders: list[dict] = []

    def get_accounts(self) -> list[dict]:
        return [{"account_no": "MOCK-0001", "name": "모의 계좌"}]

    def get_holdings(self, account_no: str) -> dict[str, int]:
        return dict(self._HOLDINGS)

    def get_cash_balance_usd(self, account_no: str) -> float:
        return 8_000.0

    def get_quote(self, ticker: str) -> float:
        return self._PRICES.get(ticker, self._DEFAULT_PRICE)

    def get_usd_krw_rate(self) -> float:
        return 1_380.0

    def is_us_market_open(self) -> bool:
        return True

    def place_order(
        self, account_no: str, ticker: str, side: str, quantity: int,
        order_type: str = "market", limit_price: float | None = None,
    ) -> str:
        self._order_seq += 1
        order_id = f"MOCK-ORDER-{self._order_seq:04d}"
        self.placed_orders.append(
            {"order_id": order_id, "ticker": ticker, "side": side, "quantity": quantity}
        )
        return order_id

    def get_order_status(self, order_id: str) -> str:
        return "FILLED"

    def cancel_order(self, order_id: str) -> None:
        pass
