"""CLI 진입점: ProPicks 리스트 붙여넣기 → 파싱 확인 → 계획 → (확인 후) 주문.

사용 예:
    python -m propicks_trader --mock --budget 10000          # 모의 흐름 테스트
    python -m propicks_trader --budget 10000 --dry-run       # 실계좌 조회, 계획만 출력
    python -m propicks_trader --budget 10000 --no-dry-run    # 실제 주문 (확인 입력 필요)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from rich.console import Console

from .executor import execute_plan, print_plan
from .parser import parse_tickers
from .planner import build_rebalance_plan
from .toss_client import MockTossClient, TossApiError, TossClient

_ROOT = Path(__file__).resolve().parent.parent

console = Console()

# 붙여넣기를 stdin 파이프로 받은 경우 이후 확인 입력은 stdin 에서 받을 수 없으므로
# (이미 EOF), /dev/tty 로 폴백하기 위해 stdin 소비 여부를 기록한다.
_stdin_consumed = False


def _prompt(message: str) -> str:
    """확인 입력을 받는다. stdin 이 이미 소비된 파이프면 /dev/tty 에서 읽는다."""
    console.print(message)
    if sys.stdin.isatty() or not _stdin_consumed:
        return input("> ").strip()
    try:
        with open("/dev/tty", encoding="utf-8") as tty:
            console.print("> ", end="")
            return tty.readline().strip()
    except OSError as exc:
        raise TossApiError(
            "확인 입력을 받을 수 없습니다. 터미널에서 직접 실행하거나 "
            "--input-file 로 리스트를 전달하세요."
        ) from exc


def main() -> int:
    args = _parse_args()
    config = _load_config(args.config)
    dry_run = _resolve_dry_run(args, config)

    max_budget = float(config.get("max_budget_usd", 50_000))
    if args.budget > max_budget:
        console.print(f"[red]예산 ${args.budget:,.0f} 이 config 상한 ${max_budget:,.0f} 을 넘습니다.[/red]")
        return 1

    # 1) 리스트 붙여넣기 → 파싱 → 사용자 확인
    tickers = _read_and_confirm_tickers(args)
    if not tickers:
        return 1

    # 2) 계좌 조회
    client = _make_client(args.mock)
    account_no = _resolve_account(client)
    console.print(f"계좌: [bold]{account_no}[/bold]{' (mock)' if args.mock else ''}")

    holdings = client.get_holdings(account_no)
    cash = client.get_cash_balance_usd(account_no)
    console.print(f"보유 종목 {len(holdings)}개 · 가용 현금 ${cash:,.2f}")

    # 3) 시세 조회 (조회 실패 티커는 경고 후 제외)
    prices, valid_tickers = _fetch_prices(client, tickers, holdings)
    if not valid_tickers:
        console.print("[red]시세 조회에 성공한 목표 종목이 없습니다.[/red]")
        return 1

    # 4) 리밸런싱 계획
    plan = build_rebalance_plan(
        valid_tickers, holdings, prices, args.budget, cash,
        cash_safety_factor=float(config.get("cash_safety_factor", 0.98)),
    )
    print_plan(plan, holdings, args.budget)

    if not plan.orders:
        console.print("실행할 주문이 없습니다 (이미 목표 상태).")
        return 0

    # 5) dry-run 이면 여기서 종료, 아니면 타이핑 확인 후 실행
    if dry_run:
        console.print("[yellow]dry-run 모드: 실제 주문은 제출하지 않았습니다. "
                      "(실행하려면 --no-dry-run)[/yellow]")
        return 0

    answer = _prompt("[bold red]실제 주문을 제출합니다. 계속하려면 '실행' 을 입력하세요:[/bold red]")
    if answer != "실행":
        console.print("취소했습니다.")
        return 0

    execute_plan(
        client, account_no, plan,
        order_type=str(config.get("order_type", "market")),
        fill_poll_interval=float(config.get("fill_poll_interval", 3)),
        fill_poll_timeout=float(config.get("fill_poll_timeout", 300)),
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="propicks_trader",
        description="ProPicks 리스트를 토스증권 계좌에 리밸런싱합니다.",
    )
    parser.add_argument("--budget", type=float, required=True,
                        help="이번 리밸런싱의 총 목표 투자금액 (USD)")
    parser.add_argument("--mock", action="store_true",
                        help="API 키 없이 모의 데이터로 전체 흐름 테스트")
    parser.add_argument("--input-file", type=Path,
                        help="붙여넣기 대신 파일에서 리스트를 읽음")
    parser.add_argument("--yes", action="store_true",
                        help="파싱 결과 확인을 건너뜀 (주문 확인은 건너뛰지 않음)")
    parser.add_argument("--config", type=Path, default=_ROOT / "config.yaml")
    dry = parser.add_mutually_exclusive_group()
    dry.add_argument("--dry-run", dest="dry_run", action="store_true", default=None)
    dry.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    return parser.parse_args()


def _load_config(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return {}


def _resolve_dry_run(args: argparse.Namespace, config: dict) -> bool:
    if args.dry_run is not None:
        return args.dry_run
    return bool(config.get("dry_run", True))  # 안전 기본값: dry-run


def _read_and_confirm_tickers(args: argparse.Namespace) -> list[str]:
    global _stdin_consumed
    if args.input_file:
        text = args.input_file.read_text(encoding="utf-8")
    else:
        console.print("ProPicks 리스트를 붙여넣은 뒤 Ctrl-D (Windows: Ctrl-Z + Enter) 로 종료하세요:")
        text = sys.stdin.read()
        _stdin_consumed = not sys.stdin.isatty()

    tickers = parse_tickers(text)
    if not tickers:
        console.print("[red]티커를 찾지 못했습니다. NYSE:ONTO 같은 거래소 접두사 형태로 붙여넣어 보세요.[/red]")
        return []

    console.print(f"파싱된 종목 [bold]{len(tickers)}개[/bold]: {', '.join(tickers)}")
    if args.yes:
        return tickers
    answer = _prompt("맞습니까? [y/N]").lower()
    return tickers if answer == "y" else []


def _make_client(mock: bool):
    if mock:
        return MockTossClient()
    load_dotenv(_ROOT / ".env")
    return TossClient(os.getenv("TOSS_APP_KEY", ""), os.getenv("TOSS_APP_SECRET", ""))


def _resolve_account(client) -> str:
    preferred = os.getenv("TOSS_ACCOUNT_NO", "").strip()
    if preferred:
        return preferred
    accounts = client.get_accounts()
    if not accounts:
        raise TossApiError("조회된 계좌가 없습니다.")
    return str(accounts[0]["account_no"])


def _fetch_prices(client, tickers: list[str], holdings: dict[str, int]):
    prices: dict[str, float] = {}
    valid: list[str] = []
    for ticker in tickers:
        try:
            prices[ticker] = client.get_quote(ticker)
            valid.append(ticker)
        except TossApiError as exc:
            console.print(f"[yellow]⚠ {ticker}: 시세 조회 실패 → 제외 ({exc})[/yellow]")
    for ticker in holdings:  # 매도 계산에 보유 종목 시세도 필요
        if ticker not in prices:
            prices[ticker] = client.get_quote(ticker)
    return prices, valid


if __name__ == "__main__":
    try:
        sys.exit(main())
    except TossApiError as exc:
        console.print(f"[red]오류: {exc}[/red]")
        sys.exit(2)
    except KeyboardInterrupt:
        console.print("\n중단했습니다.")
        sys.exit(130)
