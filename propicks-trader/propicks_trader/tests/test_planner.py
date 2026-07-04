import math

import pytest

from propicks_trader.planner import build_rebalance_plan


PRICES = {"ONTO": 200.0, "MOH": 300.0, "ASAN": 15.0, "INTC": 25.0, "AAPL": 250.0}


def test_removed_holding_is_fully_sold():
    plan = build_rebalance_plan(
        target_tickers=["ONTO", "MOH"],
        holdings={"INTC": 12},
        prices=PRICES,
        budget=6000,
        available_cash=6000,
    )
    sells = {o.ticker: o for o in plan.sells}
    assert sells["INTC"].quantity == 12
    assert sells["INTC"].side == "SELL"


def test_equal_weight_buy_quantities():
    plan = build_rebalance_plan(
        target_tickers=["ONTO", "MOH", "ASAN"],
        holdings={},
        prices=PRICES,
        budget=9000,  # 종목당 $3,000
        available_cash=9000,
    )
    buys = {o.ticker: o for o in plan.buys}
    assert buys["ONTO"].quantity == math.floor(3000 / 200.0)  # 15
    assert buys["MOH"].quantity == math.floor(3000 / 300.0)   # 10
    assert buys["ASAN"].quantity == math.floor(3000 / 15.0)   # 200


def test_existing_holding_only_buys_delta():
    plan = build_rebalance_plan(
        target_tickers=["ONTO"],
        holdings={"ONTO": 5},
        prices=PRICES,
        budget=3000,  # 목표 15주, 보유 5주 → 10주만 매수
        available_cash=3000,
    )
    assert len(plan.buys) == 1
    assert plan.buys[0].quantity == 10


def test_overweight_holding_is_trimmed():
    plan = build_rebalance_plan(
        target_tickers=["ONTO"],
        holdings={"ONTO": 20},
        prices=PRICES,
        budget=3000,  # 목표 15주, 보유 20주 → 5주 매도
        available_cash=0,
    )
    assert len(plan.sells) == 1
    assert plan.sells[0].ticker == "ONTO"
    assert plan.sells[0].quantity == 5
    assert not plan.buys


def test_insufficient_cash_trims_buys():
    plan = build_rebalance_plan(
        target_tickers=["ONTO", "MOH"],
        holdings={},
        prices=PRICES,
        budget=6000,          # 매수 필요 ~$6,000
        available_cash=1000,  # 현금은 $1,000 뿐, 매도도 없음
    )
    assert any("자동 축소" in w for w in plan.warnings)
    assert plan.total_buy_amount <= 1000


def test_sell_proceeds_count_toward_buying_power():
    plan = build_rebalance_plan(
        target_tickers=["ONTO"],
        holdings={"INTC": 100},  # 매도 대금 $2,500 확보
        prices=PRICES,
        budget=2500,
        available_cash=0,
        cash_safety_factor=1.0,
    )
    assert plan.buys and plan.buys[0].quantity == 12  # floor(2500/200)
    assert not any("자동 축소" in w for w in plan.warnings)


def test_stock_too_expensive_for_allocation_warns():
    plan = build_rebalance_plan(
        target_tickers=["ONTO", "MOH"],
        holdings={},
        prices=PRICES,
        budget=500,  # 종목당 $250 < ONTO $200? no, MOH $300 은 1주도 못 삼
        available_cash=500,
    )
    assert any("MOH" in w and "매수 불가" in w for w in plan.warnings)


def test_missing_price_raises():
    with pytest.raises(ValueError, match="UNKNOWN"):
        build_rebalance_plan(
            target_tickers=["UNKNOWN"],
            holdings={},
            prices=PRICES,
            budget=1000,
            available_cash=1000,
        )


def test_empty_target_list_raises():
    with pytest.raises(ValueError):
        build_rebalance_plan([], {}, PRICES, 1000, 1000)


def test_sells_come_before_buys_in_order_list():
    plan = build_rebalance_plan(
        target_tickers=["ONTO"],
        holdings={"INTC": 1},
        prices=PRICES,
        budget=1000,
        available_cash=1000,
    )
    sides = [o.side for o in plan.orders]
    assert sides == sorted(sides, key=lambda s: 0 if s == "SELL" else 1)
