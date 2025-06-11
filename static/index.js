// 📦 사용자 정보 로딩
const user = JSON.parse(localStorage.getItem("currentUser"));

// 🎛️ Part enum ↔ label 매핑 (API는 "FIRST", "SECOND" 사용)
const PART_LABEL_TO_ENUM = { "1부": "FIRST", "2부": "SECOND" };
const PART_ENUM_TO_LABEL = { FIRST: "1부", SECOND: "2부" };
const PART_LABELS = Object.keys(PART_LABEL_TO_ENUM);

// 📌 페이지 초기화
window.addEventListener("DOMContentLoaded", () => {
  renderUserInfo();
  renderAdminLink();
  startClock();
  bindGroupListToggle();
  loadGroups();
  const list = document.getElementById("group-list");
  if (list) list.style.display = "block";
  const toggleBtn = document.getElementById("toggle-group-list");
  if (toggleBtn) toggleBtn.textContent = "접기";
});

function renderUserInfo() {
  const userInfo = document.getElementById("user-info");
  if (user?.username) {
    userInfo.textContent = `👤 ${user.username} (${user.role})`;
  }
}

function renderAdminLink() {
  const adminLinkContainer = document.getElementById("admin-link-container");
  if (["운영진", "모임장"].includes(user?.role)) {
    const btn = document.createElement("a");
    btn.href = "/admin";
    btn.textContent = "🔧 관리자 페이지";
    btn.className = "admin-link";
    adminLinkContainer.appendChild(btn);
  }
}

function startClock() {
  const clockEl = document.getElementById("current-datetime");
  setInterval(() => {
    const now = new Date();
    const kstOffset = 9 * 60;
    const localTime = new Date(now.getTime() + kstOffset * 60000);
    const date = localTime.toISOString().slice(0, 10);
    const time = localTime.toTimeString().slice(0, 8);
    clockEl.textContent = `🕒 현재: ${date} ${time}`;
  }, 1000);
}

async function loadGroups() {
  try {
    const res = await fetch("/api/v1/groups/list");
    const groups = await res.json();
    const ul = document.getElementById("group-list");
    ul.innerHTML = "";
    if (groups.length === 0) {
      const li = document.createElement("li");
      li.className = "no-groups";
      li.textContent = "생성된 모임이 없습니다.";
      ul.appendChild(li);
      return;
    }

    const today = new Date().toISOString().slice(0, 10);

    for (const group of groups) {
      const li = document.createElement("li");
      li.className = "group-item";
      const isToday = group.date === today;

      li.innerHTML = `
        <p>📅 ${group.date}</p>
        ${PART_LABELS.map(label => {
            const enumKey = PART_LABEL_TO_ENUM[label];
            const c = group.part_counts?.[enumKey] || { admin: 0, member: 0 };
            return `
          <div class="part-section" data-part-label="${label}">
            <strong>${label} - 운영진 ${c.admin}명 회원 ${c.member}명</strong>
            <span class="attend-msg" data-part-label="${label}">⏳ 상태 확인 중...</span><br/>
            <button class="attend-btn" data-part-label="${label}" ${isToday ? "disabled" : ""}>참석</button>
            <button class="absent-btn" data-part-label="${label}" ${isToday ? "disabled" : ""}>불참</button>
          </div>`;
        }).join("")}
        <div class="team-toggle">
          <button class="toggle-team-btn" data-open="false">🧩 조 편성 보기</button>
          <div class="team-box" style="display:none;"></div>
        </div>
      `;

      li.querySelectorAll(".attend-btn, .absent-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const partLabel = btn.dataset.partLabel;
          const apiPart = PART_LABEL_TO_ENUM[partLabel];
          const status = btn.classList.contains("attend-btn") ? "참석" : "불참";
          const msgElem = li.querySelector(`.attend-msg[data-part-label="${partLabel}"]`);
          await setAttendance(group.id, apiPart, status, msgElem);
        });
      });

      li.querySelector(".toggle-team-btn").onclick = async () => {
        const toggleBtn = li.querySelector(".toggle-team-btn");
        const teamBox = li.querySelector(".team-box");
        const isOpen = toggleBtn.dataset.open === "true";

        if (isOpen) {
          teamBox.style.display = "none";
          toggleBtn.textContent = "🧩 조 편성 보기";
          toggleBtn.dataset.open = "false";
        } else {
          toggleBtn.textContent = "🔽 조 편성 숨기기";
          toggleBtn.dataset.open = "true";
          teamBox.innerHTML = "...로딩중...";
          teamBox.style.display = "block";
          const html = await getTeamHTML(group.id, group.date);
          teamBox.innerHTML = html;
        }
      };

      for (const label of PART_LABELS) {
        const msgElem = li.querySelector(`.attend-msg[data-part-label="${label}"]`);
        const apiPart = PART_LABEL_TO_ENUM[label];

        fetch(`/api/v1/attendance/get?group_id=${group.id}&user_id=${user.id}&part=${encodeURIComponent(apiPart)}`)
          .then(res => res.json())
          .then(data => {
            msgElem.textContent =
              data.status === "참석" ? `✅ 참석 상태입니다.` :
              data.status === "불참" ? `❌ 불참 상태입니다.` :
              `❓ 아직 선택하지 않음`;
          })
          .catch(() => {
            msgElem.textContent = "⚠️ 상태 로딩 실패";
          });
      }

      ul.appendChild(li);
    }
  } catch (e) {
    console.error("모임 목록 로딩 실패", e);
  }
}

async function setAttendance(groupId, apiPart, status, msgElem) {
  const form = new FormData();
  form.append("group_id", groupId);
  form.append("user_id", user.id);
  form.append("part", apiPart);
  form.append("status", status);

  try {
    const res = await fetch("/api/v1/attendance/set", {
      method: "POST",
      body: form,
    });

    if (res.ok) {
      msgElem.textContent = status === "참석" ? "✅ 참석 상태입니다." : "❌ 불참 상태입니다.";
    } else {
      msgElem.textContent = "⚠️ 요청 실패. 다시 시도해주세요.";
    }
  } catch (e) {
    msgElem.textContent = "🚫 네트워크 오류 발생";
  }
}

async function getTeamHTML(groupId, groupDate) {
  const res = await fetch(`/api/v1/groups/${groupId}/teams`);
  const teams = await res.json();
  if (teams.length === 0) return "<p>아직 조가 편성되지 않았습니다.</p>";

  let myTeamId = null;
  try {
    const myRes = await fetch(`/api/v1/groups/${groupId}/my_team?user_id=${user.id}`);
    const myTeam = await myRes.json();
    myTeamId = myTeam.team_id;
  } catch (e) {
    console.warn("내 조 정보 로딩 실패", e);
  }

  const part1 = teams.filter(t => t.part === "FIRST");
  const part2 = teams.filter(t => t.part === "SECOND");

  const renderPart = (titleLabel, list) => {
    let html = `<h4 style="margin-top:2rem;">${titleLabel}</h4><div class="team-grid">`;
    for (let i = 0; i < list.length; i += 2) {
      html += `<div class="team-row">`;
      [list[i], list[i + 1]].forEach((team, j) => {
        if (!team) return;
        const isMine = team.id === myTeamId;
        const teamNumber = i + j + 1;
        const partLabel = PART_ENUM_TO_LABEL[team.part];
        html += `<div class="team-table${isMine ? " highlight" : ""}">`;
        html += `<strong>${partLabel} ${teamNumber}조${isMine ? " ⭐" : ""}</strong>`;
        html += `<div class="seats">`;
        team.members.forEach(m => {
          html += `<div class="bubble${m.is_leader ? " leader" : ""}${m.role === "운영진" ? " admin" : ""}${m.id === user.id ? " me" : ""}">${m.username}</div>`;
        });
        html += `</div></div>`;
      });
      html += `</div>`;
    }
    html += `</div>`;
    return html;
  };

  return `<h4>🧩 ${groupDate} 조 편성 결과</h4>` +
         renderPart("📘 1부 조편성", part1) +
         renderPart("📙 2부 조편성", part2);
}

function bindGroupListToggle() {
  const toggleBtn = document.getElementById("toggle-group-list");
  const list = document.getElementById("group-list");
  if (!toggleBtn || !list) return;
  // 목록을 기본으로 보여주고 필요 시 새로고침용으로 사용
  toggleBtn.onclick = () => {
    const isHidden = list.style.display === "none";
    list.style.display = isHidden ? "block" : "none";
    toggleBtn.textContent = isHidden ? "접기" : "모임 불러오기";
    if (isHidden) loadGroups();
  };
}
