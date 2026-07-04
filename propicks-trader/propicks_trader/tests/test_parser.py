from propicks_trader.parser import parse_tickers


def test_exchange_prefixed_tickers_take_priority():
    text = """
    ProPicks AI - Tech Titans
    1. Onto Innovation NYSE:ONTO +12.3% $220.15
    2. Molina Healthcare NYSE:MOH +8.1% $291.80
    3. Asana NYSE: ASAN -2.4% $14.25
    4. Allegro Microsystems NASDAQ:ALGM +5.0%
    ABCD  <- 접두사 형태가 있으면 이런 잡음 토큰은 무시되어야 함
    """
    assert parse_tickers(text) == ["ONTO", "MOH", "ASAN", "ALGM"]


def test_korean_ui_copy_with_prefixed_tickers():
    text = """
    프로픽스 AI  기술 타이탄 전략
    온투 이노베이션 NYSE:ONTO 매수
    몰리나 헬스케어 NYSE:MOH 보유
    엔비디아 NASDAQ:NVDA 신규
    """
    assert parse_tickers(text) == ["ONTO", "MOH", "NVDA"]


def test_bare_tickers_fallback():
    text = "ONTO\nMOH\nASAN\nALGM\nNVDA"
    assert parse_tickers(text) == ["ONTO", "MOH", "ASAN", "ALGM", "NVDA"]


def test_bare_tickers_tab_separated_table():
    text = (
        "종목\t티커\t수익률\n"
        "Onto Innovation\tONTO\t+12.3%\n"
        "Molina Healthcare\tMOH\t+8.1%\n"
    )
    assert parse_tickers(text) == ["ONTO", "MOH"]


def test_noise_tokens_are_filtered():
    text = "TOP PICKS BUY SELL HOLD USD ETF ONTO PER ROE EPS MOH"
    assert parse_tickers(text) == ["ONTO", "MOH"]


def test_dedupe_preserves_order():
    text = "NYSE:MOH NYSE:ONTO NYSE:MOH NASDAQ:ONTO"
    assert parse_tickers(text) == ["MOH", "ONTO"]


def test_class_share_ticker():
    assert parse_tickers("NYSE:BRK.B NYSE:MOH") == ["BRK.B", "MOH"]


def test_empty_input():
    assert parse_tickers("") == []
    assert parse_tickers("아무 티커도 없는 한글 문장입니다.") == []


def test_lowercase_words_not_matched():
    assert parse_tickers("buy onto and moh today") == []
