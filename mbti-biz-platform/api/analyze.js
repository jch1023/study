function normalizeMbti(input) {
  return (input || "").trim().toUpperCase();
}

function getProfile(mbti) {
  const groups = {
    NT: {
      direction: "전략·혁신 중심. 데이터 기반으로 빠르게 실험하고 스케일하는 모델에 강합니다.",
      industries: ["B2B SaaS", "AI 솔루션", "컨설팅", "자동화 서비스"],
      scores: { 리더십: 86, 실행력: 82, 관계관리: 68, 분석력: 91 }
    },
    NF: {
      direction: "브랜드·커뮤니티 중심. 고객경험과 신뢰를 기반으로 충성도를 높이는 모델에 강합니다.",
      industries: ["코칭", "커뮤니티 플랫폼", "교육", "브랜드 커머스"],
      scores: { 리더십: 78, 실행력: 74, 관계관리: 90, 분석력: 73 }
    },
    SJ: {
      direction: "운영·프로세스 중심. 안정적인 품질과 반복 가능한 서비스에 강합니다.",
      industries: ["프랜차이즈", "로컬 서비스", "BPO", "물류 운영"],
      scores: { 리더십: 81, 실행력: 88, 관계관리: 76, 분석력: 79 }
    },
    SP: {
      direction: "현장·실행 중심. 빠른 반응과 제품/서비스 개선 속도에서 강점을 가집니다.",
      industries: ["커머스", "F&B", "이벤트", "숏폼 콘텐츠 비즈니스"],
      scores: { 리더십: 75, 실행력: 90, 관계관리: 72, 분석력: 70 }
    }
  };

  const key = mbti[1] === "N"
    ? mbti[2] === "T" ? "NT" : "NF"
    : mbti[2] === "T" ? "SP" : "SJ";

  return groups[key] || groups.NT;
}

function buildReports({ mbti, industry, goal, profile }) {
  const freeReport = `✅ ${mbti} 무료 사업 방향 분석\n\n` +
    `- 핵심 방향: ${profile.direction}\n` +
    `- 추천 업종: ${profile.industries.join(", ")}\n` +
    `- 즉시 실행: '${industry}'에서 2주 단위 MVP 테스트를 3회 반복하고, 목표(${goal}) 기준 CAC/LTV/재구매율을 추적하세요.`;

  const premiumFull = `[심층 유료 보고서]\n` +
    `MBTI: ${mbti}\n업종: ${industry}\n목표: ${goal}\n\n` +
    `1) 마케팅 전략\n- ICP 재정의\n- 채널 믹스 최적화\n- 퍼널 자동화\n\n` +
    `2) 조직/채용\n- 역할 분리(영업/운영/제품)\n- KPI 운영 체계\n- 채용 우선순위\n\n` +
    `3) 자동화\n- 리드수집→CRM→이메일→예약\n- 광고/매출 대시보드 자동 리포트\n\n` +
    `4) 리스크\n- ${profile.direction}\n- 성향 편향 보정 체크리스트\n\n` +
    `5) 12주 로드맵\n- 0~4주: 시장 검증\n- 5~8주: 전환 최적화\n- 9~12주: 확장 및 채용`;

  return {
    freeReport,
    premiumPreview: premiumFull.slice(0, 1000) + "\n\n...이후 내용은 유료 플랜에서 확인 가능합니다."
  };
}

async function saveToSupabase(payload) {
  const url = process.env.SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !serviceKey) {
    return { saved: false };
  }

  const response = await fetch(`${url}/rest/v1/mbti_reports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      Prefer: "return=representation"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    return { saved: false };
  }

  const rows = await response.json();
  return { saved: true, reportId: rows?.[0]?.id || null };
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ message: "Method not allowed" });
  }

  try {
    const mbti = normalizeMbti(req.body?.mbti);
    const industry = (req.body?.industry || "").trim();
    const goal = (req.body?.goal || "").trim();

    if (!/^[EI][NS][TF][JP]$/.test(mbti)) {
      return res.status(400).json({ message: "MBTI 형식이 올바르지 않습니다. 예: ENTJ" });
    }

    if (!industry || !goal) {
      return res.status(400).json({ message: "업종과 목표를 입력해주세요." });
    }

    const profile = getProfile(mbti);
    const { freeReport, premiumPreview } = buildReports({ mbti, industry, goal, profile });

    const saveResult = await saveToSupabase({
      mbti,
      industry,
      goal,
      free_report: freeReport,
      premium_preview: premiumPreview,
      scores: profile.scores,
      created_at: new Date().toISOString()
    });

    return res.status(200).json({
      freeReport,
      premiumPreview,
      scores: profile.scores,
      saved: saveResult.saved,
      reportId: saveResult.reportId || null
    });
  } catch (error) {
    return res.status(500).json({ message: "Internal server error", detail: error.message });
  }
}
