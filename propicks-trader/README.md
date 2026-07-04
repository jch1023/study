# ProPicks → 토스증권 자동매매 (propicks-trader)

인베스팅닷컴 InvestingPro **ProPicks AI** 종목 리스트를 복사해서 붙여넣으면,
토스증권 계좌를 그 리스트대로 **리밸런싱**(리스트 제외 종목 전량 매도 → 리스트
종목 균등 비중 매수)하는 CLI 도구입니다.

> ⚠️ **실제 돈이 나가는 프로그램입니다.** dry-run이 기본값이며, 실제 주문은
> `--no-dry-run` + `실행` 타이핑 확인을 모두 거쳐야만 제출됩니다.
> 투자 손실의 책임은 전적으로 사용자에게 있습니다.

## 동작 방식

1. ProPicks 화면에서 종목 리스트를 복사해 터미널에 붙여넣기
2. 티커 파싱 결과를 확인 (`NYSE:ONTO` 접두사 형태가 가장 정확)
3. 토스증권 API로 보유 종목·가용 현금·현재가 조회
4. ProPicks 방법론(균등 비중)대로 주문 계획 계산:
   - 새 리스트에 없는 보유 종목 → 전량 매도
   - 리스트 종목 → `예산 ÷ 종목 수`씩 배분, 보유분과의 차이만 매수/매도
   - 현금 부족 시 매수 수량 자동 축소 (경고 표시)
5. 주문 계획표 출력 → dry-run이면 종료
6. `실행` 입력 시: 매도 제출 → 체결 대기 → 매수 제출, 전 과정 `logs/*.jsonl` 기록

## 설치

```bash
cd propicks-trader
pip install -r requirements.txt
cp .env.example .env   # 발급받은 토스증권 Open API 키 입력
```

### 토스증권 Open API 키 발급

1. 토스증권 앱 → Open API 이용 신청 (2026년 현재 순차 오픈 중)
2. [developers.tossinvest.com](https://developers.tossinvest.com/docs) 에서 App Key / Secret 발급
3. `.env` 파일에 `TOSS_APP_KEY`, `TOSS_APP_SECRET` 입력 (**절대 커밋 금지** — `.gitignore` 처리됨)

## 사용법

```bash
# 1) 키 없이 모의 데이터로 흐름 익히기
python -m propicks_trader --mock --budget 10000

# 2) 실계좌 조회 + 계획표만 (기본값이 dry-run이라 --dry-run 생략 가능)
python -m propicks_trader --budget 10000

# 3) 실제 주문 (계획표 확인 후 '실행' 입력해야 제출됨)
python -m propicks_trader --budget 10000 --no-dry-run

# 붙여넣기 대신 파일 입력
python -m propicks_trader --budget 10000 --input-file picks.txt
```

| 옵션 | 설명 |
|---|---|
| `--budget` (필수) | 이번 리밸런싱 총 목표 투자금액 (USD) |
| `--mock` | API 키 없이 모의 데이터로 전체 흐름 테스트 |
| `--dry-run` / `--no-dry-run` | 계획만 출력 / 실제 주문 (기본: config의 `dry_run: true`) |
| `--input-file` | 붙여넣기 대신 파일에서 리스트 읽기 |
| `--yes` | 파싱 결과 확인 생략 (주문 확인은 생략 불가) |

`config.yaml` 에서 주문 유형(시장가/지정가), 예산 상한, 체결 대기 시간 등을 조정합니다.

## 실전 투입 전 체크리스트

API 스펙은 공식 문서가 로그인 뒤에만 열려 있어 `toss_client.py` 의
엔드포인트 경로/응답 파싱은 **추정값**입니다. 키 발급 후 반드시:

1. `toss_client.py` 상단 `_BASE_URL`, `_ENDPOINTS` 를 [공식 문서](https://developers.tossinvest.com/docs)와 대조해 수정
2. 조회성 API부터 검증: `python -m propicks_trader --budget 100` (dry-run) 으로 잔고·시세 조회 확인
3. 소액 1주 매수/매도로 주문 API 검증
4. 그 다음에 실전 예산으로 사용

## 테스트

```bash
python -m pytest propicks_trader/tests -q
```

## 한계·주의사항

- 토스증권 Open API는 순차 오픈 중 — 키 발급 전에는 `--mock` 만 동작
- 시장가 주문 + 환율 변동으로 실제 체결 금액은 계획표와 다를 수 있음
- 공식 API 기준 정수 수량 주문 가정 (소수점 주문 미지원)
- `AI`(C3.ai)처럼 일반 단어와 겹치는 티커는 잡음 필터에 걸리므로
  `NYSE:AI` 접두사 형태로 입력하세요
- ProPicks 리스트는 InvestingPro 구독자용 콘텐츠입니다 — 본인 계정에서
  열람한 리스트를 본인 투자에만 사용하세요
