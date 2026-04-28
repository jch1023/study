# MBTI Biz Navigator (Vercel + Supabase)

요청하신 대로 **Vercel + Supabase** 구조로 바꾼 MVP입니다.

- 프론트엔드: 정적 페이지 (`index.html`, `styles.css`, `app.js`)
- 백엔드: Vercel Serverless Function (`api/analyze.js`)
- 데이터 저장: Supabase Postgres (REST API 사용)

---

## 1) 기능

- MBTI/업종/목표 입력
- 무료 사업 방향 분석 결과 출력
- 유료 심층 보고서 1,000자 미리보기 출력
- 분석 결과를 Supabase 테이블에 저장

---

## 2) Supabase 설정

### SQL 실행 (테이블 생성)

```sql
create extension if not exists "pgcrypto";

create table if not exists public.mbti_reports (
  id uuid primary key default gen_random_uuid(),
  mbti text not null,
  industry text not null,
  goal text not null,
  free_report text not null,
  premium_preview text not null,
  scores jsonb not null,
  created_at timestamptz not null default now()
);
```

> 서버 함수에서 Service Role Key로 저장하므로, 우선 MVP 단계에서는 별도 RLS 정책 없이 시작 가능.

---

## 3) Vercel 환경변수

Vercel 프로젝트 Settings → Environment Variables에 아래 추가:

- `SUPABASE_URL` (예: `https://xxxxx.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY`

---

## 4) 로컬 실행

```bash
cd mbti-biz-platform
python3 -m http.server 8000
# 브라우저: http://localhost:8000
```

> 참고: 로컬에서 `/api/analyze`까지 테스트하려면 `vercel dev` 사용 권장.

```bash
cd mbti-biz-platform
vercel dev
# 브라우저: http://localhost:3000
```

---

## 5) 배포

1. GitHub에 푸시
2. Vercel에서 저장소 Import
3. Root Directory를 `mbti-biz-platform`로 지정
4. 환경변수 2개 등록 후 Deploy

---

## 6) 다음 단계

- MBTI 16유형별 정밀 데이터셋 고도화
- 유료 결제(Stripe/토스) 연결
- PDF 사업계획서 내보내기
- 사용자 로그인 + 보고서 히스토리 조회
