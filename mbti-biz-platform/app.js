const mbtiProfiles = {
  ENTJ: {
    direction: "고성장 B2B, 운영 효율, 확장형 모델에 강합니다.",
    industries: ["B2B SaaS", "컨설팅", "프랜차이즈", "교육 플랫폼"],
    scores: { 리더십: 92, 실행력: 90, 관계관리: 67, 분석력: 85 }
  },
  ENTP: {
    direction: "신규 시장 개척, 실험형 비즈니스, 콘텐츠/브랜드 확장에 강합니다.",
    industries: ["크리에이터 이코노미", "마케팅 에이전시", "AI 도구"],
    scores: { 리더십: 84, 실행력: 76, 관계관리: 73, 분석력: 88 }
  },
  INTJ: {
    direction: "장기 전략, 데이터 기반 최적화, 지식형/기술형 사업에 강합니다.",
    industries: ["리서치 SaaS", "에듀테크", "핀테크 백오피스"],
    scores: { 리더십: 78, 실행력: 82, 관계관리: 60, 분석력: 94 }
  },
  ENFP: {
    direction: "브랜드 스토리텔링, 커뮤니티 성장, 고객 경험 중심 사업에 강합니다.",
    industries: ["커뮤니티 앱", "코칭", "라이프스타일 커머스"],
    scores: { 리더십: 80, 실행력: 70, 관계관리: 89, 분석력: 68 }
  }
};

function normalizeMbti(input) {
  return (input || "").trim().toUpperCase();
}

function getProfile(mbti) {
  return mbtiProfiles[mbti] || {
    direction: "표준형 전략: 작은 실험을 빠르게 반복하며 데이터로 확장하세요.",
    industries: ["니치 커머스", "전문 서비스", "디지털 제품"],
    scores: { 리더십: 75, 실행력: 75, 관계관리: 75, 분석력: 75 }
  };
}

function renderBars(scores) {
  const chartArea = document.getElementById("chartArea");
  chartArea.innerHTML = "";

  Object.entries(scores).forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <span>${label}</span>
      <div class="bar"><span style="width:${value}%"></span></div>
      <strong>${value}</strong>
    `;
    chartArea.appendChild(row);
  });
}

function buildPremiumText(mbti, industry, goal, profile) {
  return `[심층 보고서 미리보기]
MBTI: ${mbti}
관심 업종: ${industry}
6개월 목표: ${goal}

1) 마케팅 전략
- 1단계(0~4주): ICP(이상 고객) 1개 세그먼트 정의 및 오퍼 테스트
- 2단계(5~8주): 채널 2개 집중(콘텐츠+퍼포먼스)으로 CAC 측정
- 3단계(9~12주): 고전환 페이지, 이메일 시퀀스, 리타겟팅 자동화

2) 직원/조직 관리 전략
- 창업자 업무를 영업/운영/제품으로 분리하고 KPI 3개만 추적
- 채용은 '실행형 1명 + 운영형 1명' 우선
- 주간 운영 리듬: 월(목표), 수(문제해결), 금(리뷰)

3) 자동화 연동
- 리드 수집 → CRM 저장 → 맞춤 이메일 발송 → 상담 예약 자동화
- 광고 리포트/매출 대시보드 자동 집계

4) 예상 리스크
- ${mbti} 성향은 ${profile.direction}
- 강점 과몰입으로 인한 리스크를 줄이기 위해 '반대 성향 체크리스트' 운영 권장

※ 전체 보고서는 사업계획서 형태(PDF+시각화)로 제공됩니다.`;
}

document.getElementById("analysisForm").addEventListener("submit", (e) => {
  e.preventDefault();

  const mbti = normalizeMbti(document.getElementById("mbti").value);
  const industry = document.getElementById("industry").value.trim();
  const goal = document.getElementById("goal").value.trim();

  const profile = getProfile(mbti);

  const freeText = `✅ ${mbti} 성향 무료 분석\n\n` +
    `- 사업 방향: ${profile.direction}\n` +
    `- 추천 업종: ${profile.industries.join(", ")}\n` +
    `- 실행 제안: '${industry}' 분야에서 2주 단위 MVP 실험 후, 목표(${goal})를 기준으로 전환율/재구매율을 추적하세요.`;

  document.getElementById("freeResult").textContent = freeText;
  renderBars(profile.scores);

  const premiumText = buildPremiumText(mbti, industry, goal, profile);
  document.getElementById("premiumPreview").textContent = premiumText.slice(0, 1000) + "\n\n...이후 내용은 유료 플랜에서 확인 가능합니다.";
});

document.getElementById("unlockBtn").addEventListener("click", () => {
  alert("결제/구독 플로우는 MVP 이후 Stripe·토스페이먼츠 연동 단계에서 구현하세요.");
});
