"""주문 계획 실행: 계획표 출력 → 확인 → 매도 → 체결 대기 → 매수 → 로그 기록."""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .planner import Order, RebalancePlan
from .toss_client import TossApiError

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

console = Console()


def print_plan(plan: RebalancePlan, holdings: dict[str, int], budget: float) -> None:
    table = Table(title=f"주문 계획 (예산 ${budget:,.0f})")
    table.add_column("방향", style="bold")
    table.add_column("종목")
    table.add_column("수량", justify="right")
    table.add_column("현재가", justify="right")
    table.add_column("예상금액", justify="right")
    table.add_column("현재보유", justify="right")
    table.add_column("사유")

    for order in plan.orders:
        style = "red" if order.side == "SELL" else "green"
        table.add_row(
            f"[{style}]{'매도' if order.side == 'SELL' else '매수'}[/{style}]",
            order.ticker,
            str(order.quantity),
            f"${order.est_price:,.2f}",
            f"${order.est_amount:,.2f}",
            str(holdings.get(order.ticker, 0)),
            order.reason,
        )
    console.print(table)
    console.print(
        f"매도 예상 합계: [red]${plan.total_sell_amount:,.2f}[/red] · "
        f"매수 예상 합계: [green]${plan.total_buy_amount:,.2f}[/green]"
    )
    for warning in plan.warnings:
        console.print(f"[yellow]⚠ {warning}[/yellow]")


def execute_plan(
    client,
    account_no: str,
    plan: RebalancePlan,
    order_type: str = "market",
    fill_poll_interval: float = 3,
    fill_poll_timeout: float = 300,
) -> None:
    """매도 먼저 제출·체결 대기 후 매수를 제출한다. 전 과정을 JSONL 로 기록."""
    if not client.is_us_market_open():
        raise TossApiError("미국 시장이 주문 가능한 시간이 아닙니다. 장 운영 시간에 다시 실행하세요.")

    _LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = _LOG_DIR / f"orders-{stamp}.jsonl"

    with log_path.open("a", encoding="utf-8") as log:
        sell_ids = _submit_batch(client, account_no, plan.sells, order_type, log)
        if sell_ids:
            console.print("매도 주문 체결 대기 중...")
            _wait_for_fills(client, sell_ids, fill_poll_interval, fill_poll_timeout, log)
        _submit_batch(client, account_no, plan.buys, order_type, log)

    console.print(f"[bold]완료.[/bold] 주문 기록: {log_path}")


def _submit_batch(client, account_no: str, orders: list[Order], order_type: str, log) -> list[str]:
    order_ids: list[str] = []
    for order in orders:
        entry = {
            "ts": datetime.datetime.now().isoformat(),
            "ticker": order.ticker,
            "side": order.side,
            "quantity": order.quantity,
            "est_price": order.est_price,
            "order_type": order_type,
        }
        try:
            limit_price = order.est_price if order_type == "limit" else None
            order_id = client.place_order(
                account_no, order.ticker, order.side, order.quantity,
                order_type=order_type, limit_price=limit_price,
            )
            entry["order_id"] = order_id
            order_ids.append(order_id)
            console.print(f"  {order.side} {order.ticker} × {order.quantity} → 주문 {order_id}")
        except TossApiError as exc:
            # 부분 실패 시 즉시 중단: 이미 제출된 주문은 로그에 남아 있어 수동 확인 가능
            entry["error"] = str(exc)
            log.write(json.dumps(entry, ensure_ascii=False) + "\n")
            raise TossApiError(
                f"{order.ticker} {order.side} 주문 실패로 중단합니다. "
                f"이미 제출된 주문은 로그를 확인하세요: {exc}"
            ) from exc
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
        log.flush()
    return order_ids


def _wait_for_fills(client, order_ids: list[str], interval: float, timeout: float, log) -> None:
    deadline = time.monotonic() + timeout
    pending = set(order_ids)
    while pending and time.monotonic() < deadline:
        for order_id in sorted(pending):
            status = client.get_order_status(order_id)
            if status in ("FILLED", "CANCELLED", "REJECTED"):
                pending.discard(order_id)
                log.write(json.dumps({
                    "ts": datetime.datetime.now().isoformat(),
                    "order_id": order_id,
                    "status": status,
                }, ensure_ascii=False) + "\n")
                if status in ("CANCELLED", "REJECTED"):
                    raise TossApiError(f"매도 주문 {order_id} 이(가) {status} 상태입니다. 중단합니다.")
        if pending:
            time.sleep(interval)
    if pending:
        raise TossApiError(
            f"매도 체결 대기 시간 초과 ({timeout}초). 미체결 주문: {', '.join(sorted(pending))}. "
            "체결 확인 후 다시 실행하면 남은 매수가 계산됩니다."
        )
