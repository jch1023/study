"""붙여넣은 ProPicks 텍스트에서 미국 주식 티커를 추출한다.

ProPicks 화면을 복사하면 UI 언어(영/한), 표 형태(탭 구분), 티커 표기
(``NYSE:ONTO`` / ``NASDAQ:AAPL`` / 순수 ``ONTO``)가 뒤섞여 들어오므로
두 단계로 파싱한다:

1. 거래소 접두사가 붙은 티커(``NYSE:ONTO``)가 하나라도 있으면 그것만 사용
   — 가장 신뢰도가 높은 형태.
2. 없으면 독립된 1~5자 대문자 토큰을 티커 후보로 수집하되,
   화면에 흔히 섞이는 잡음 단어(컬럼 헤더, 지표 약어 등)는 제외.

파싱 결과는 반드시 사용자 확인을 거친 뒤 사용해야 한다. ``AI``(C3.ai)처럼
잡음 목록과 실제 티커가 겹치는 경우 거래소 접두사 형태로 붙여넣거나
확인 단계에서 수동 보정한다.
"""

from __future__ import annotations

import re

_EXCHANGE_TICKER = re.compile(
    r"\b(?:NYSE|NASDAQ|Nasdaq|AMEX|CBOE)\s*[:：]\s*([A-Z]{1,5}(?:\.[A-Z])?)\b"
)

_BARE_TICKER = re.compile(r"(?<![A-Za-z.$%])([A-Z]{1,5}(?:\.[A-Z])?)(?![A-Za-z.])")

# ProPicks/InvestingPro 화면 복사 시 흔히 섞이는 대문자 잡음 토큰.
# 실제 티커와 겹칠 수 있는 단어(AI 등)도 포함되어 있으므로, 이런 종목은
# 거래소 접두사 형태(NYSE:AI)로 입력하거나 확인 단계에서 수동 추가한다.
_NOISE_TOKENS = frozenset({
    "A", "I", "AI", "PRO", "USD", "KRW", "ETF", "IPO", "CEO", "CFO",
    "NYSE", "AMEX", "CBOE", "PER", "PBR", "ROE", "ROA", "EPS", "P", "E",
    "PICKS", "TOP", "BUY", "SELL", "HOLD", "NEW", "YTD", "MTD", "Q",
    "S", "US", "USA", "GAAP", "FY", "TTM", "AM", "PM", "EST", "EDT",
    "VS", "OK", "NO", "ID", "IT", "TV", "UP", "ALL", "FAIR", "VALUE",
    "SP", "DOW", "JONES", "MID", "CAP", "LOW", "HIGH", "AVG", "MAX", "MIN",
})


def parse_tickers(text: str) -> list[str]:
    """붙여넣은 텍스트에서 티커 리스트를 추출한다 (순서 유지, 중복 제거)."""
    prefixed = _EXCHANGE_TICKER.findall(text)
    if prefixed:
        return _dedupe(prefixed)

    candidates = [
        token
        for token in _BARE_TICKER.findall(text)
        if token not in _NOISE_TOKENS
    ]
    return _dedupe(candidates)


def _dedupe(tickers: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for ticker in tickers:
        if ticker not in seen:
            seen.add(ticker)
            result.append(ticker)
    return result
