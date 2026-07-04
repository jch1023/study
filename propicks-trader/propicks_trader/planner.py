"""목표 리스트와 현재 보유를 비교해 리밸런싱 주문 계획을 계산한다.

ProPicks 방법론을 따른다: 리스트에서 빠진 보유 종목은 전량 매도,
리스트 종목은 예산을 균등 비중으로 나눠 목표 수량을 맞춘다.
API 호출 없는 순수 계산 모듈이라 단위 테스트로 검증한다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Order:
    ticker: str
    side: str  # "SELL" | "BUY"
    quantity: int
    est_price: float
    reason: str

    @property
    def est_amount(self) -> float:
        return self.quantity * self.est_price


@dataclass
class RebalancePlan:
    sells: list[Order] = field(default_factory=list)
    buys: list[Order] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def orders(self) -> list[Order]:
        # 매도가 먼저 체결되어야 매수 현금이 확보되므로 매도 → 매수 순서 고정
        return self.sells + self.buys

    @property
    def total_sell_amount(self) -> float:
        return sum(o.est_amount for o in self.sells)

    @property
    def total_buy_amount(self) -> float:
        return sum(o.est_amount for o in self.buys)


def build_rebalance_plan(
    target_tickers: list[str],
    holdings: dict[str, int],
    prices: dict[str, float],
    budget: float,
    available_cash: float,
    cash_safety_factor: float = 0.98,
) -> RebalancePlan:
    """리밸런싱 주문 계획을 계산한다.

    Args:
        target_tickers: 새 ProPicks 리스트 (파싱·검증 완료된 티커).
        holdings: 현재 보유 {티커: 수량}.
        prices: 현재가 {티커: USD}. 목표/보유 전 종목 포함이어야 함.
        budget: 이번 리밸런싱의 총 목표 투자금액 (USD).
        available_cash: 계좌 가용 현금 (USD 환산).
        cash_safety_factor: 매도 대금에 적용할 여유 비율 (수수료/슬리피지 대비).
    """
    plan = RebalancePlan()
    if not target_tickers:
        raise ValueError("목표 종목 리스트가 비어 있습니다.")

    missing = [t for t in set(target_tickers) | set(holdings) if t not in prices]
    if missing:
        raise ValueError(f"현재가를 알 수 없는 종목: {', '.join(sorted(missing))}")

    # 1) 리스트에서 빠진 보유 종목 → 전량 매도
    for ticker, qty in sorted(holdings.items()):
        if ticker not in target_tickers and qty > 0:
            plan.sells.append(
                Order(ticker, "SELL", qty, prices[ticker], "리스트 제외 → 전량 매도")
            )

    # 2) 균등 비중 목표 수량과의 차이만큼 매수/매도
    per_stock = budget / len(target_tickers)
    for ticker in target_tickers:
        price = prices[ticker]
        if price <= 0:
            plan.warnings.append(f"{ticker}: 가격이 0 이하라 건너뜀")
            continue
        target_qty = math.floor(per_stock / price)
        held = holdings.get(ticker, 0)
        delta = target_qty - held
        if target_qty == 0:
            plan.warnings.append(
                f"{ticker}: 종목당 배분액 ${per_stock:,.0f} < 1주 가격 ${price:,.2f} → 매수 불가"
            )
        if delta > 0:
            plan.buys.append(Order(ticker, "BUY", delta, price, f"목표 {target_qty}주 (보유 {held}주)"))
        elif delta < 0:
            plan.sells.append(Order(ticker, "SELL", -delta, price, f"목표 {target_qty}주로 축소 (보유 {held}주)"))

    # 3) 현금 검증: 매수 필요액이 (가용현금 + 매도 예상대금×여유율)을 넘으면 축소
    usable = available_cash + plan.total_sell_amount * cash_safety_factor
    if plan.total_buy_amount > usable:
        plan.warnings.append(
            f"매수 필요액 ${plan.total_buy_amount:,.0f} > 가용액 ${usable:,.0f} → 매수 수량 자동 축소"
        )
        _trim_buys(plan, usable)

    return plan


def _trim_buys(plan: RebalancePlan, usable: float) -> None:
    """예상 금액이 큰 매수 주문부터 1주씩 줄여 가용액 안으로 맞춘다."""
    buys = {o.ticker: o for o in plan.buys}
    while sum(o.est_amount for o in buys.values()) > usable:
        reducible = [o for o in buys.values() if o.quantity > 0]
        if not reducible:
            break
        largest = max(reducible, key=lambda o: o.est_amount)
        buys[largest.ticker] = Order(
            largest.ticker, "BUY", largest.quantity - 1, largest.est_price,
            largest.reason + " (현금 부족 축소)",
        )
    plan.buys = [o for t, o in buys.items() if o.quantity > 0]
