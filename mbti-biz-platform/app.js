const form = document.getElementById("analysisForm");
const submitBtn = document.getElementById("submitBtn");
const freeResult = document.getElementById("freeResult");
const premiumPreview = document.getElementById("premiumPreview");
const saveInfo = document.getElementById("saveInfo");
const chartArea = document.getElementById("chartArea");

function renderBars(scores) {
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

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const mbti = document.getElementById("mbti").value.trim().toUpperCase();
  const industry = document.getElementById("industry").value.trim();
  const goal = document.getElementById("goal").value.trim();

  submitBtn.disabled = true;
  submitBtn.textContent = "분석 중...";
  saveInfo.textContent = "";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mbti, industry, goal })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ message: "서버 오류" }));
      throw new Error(err.message || "분석 실패");
    }

    const data = await response.json();

    freeResult.textContent = data.freeReport;
    premiumPreview.textContent = data.premiumPreview;
    renderBars(data.scores);

    saveInfo.textContent = data.saved
      ? `분석 결과가 Supabase에 저장되었습니다. (report_id: ${data.reportId})`
      : "분석 결과는 생성되었지만 저장에는 실패했습니다.";
  } catch (error) {
    freeResult.textContent = `오류: ${error.message}`;
    premiumPreview.textContent = "";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "무료 분석 시작";
  }
});

document.getElementById("unlockBtn").addEventListener("click", () => {
  alert("다음 단계: Vercel 결제 페이지 + Stripe/토스페이먼츠 연동");
});
