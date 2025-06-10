// admin.js (유저 추가/수정 + 목록 토글 + 페이지네이션 포함)

const PART_ENUM_TO_LABEL = { first: "1부", second: "2부" };
const USERS_PER_PAGE = 20;
let currentPage = 1;

// ✅ DOM 로드 시 실행

document.addEventListener("DOMContentLoaded", () => {
  const currentUser = JSON.parse(localStorage.getItem("currentUser"));

  const showMessage = (id, msg, ok = true) => {
    const el = document.getElementById(id);
    el.textContent = `${ok ? "✅" : "❌"} ${msg}`;
  };

  const bindUserForm = () => {
    const toggleBtn = document.getElementById("toggle-user-form");
    const container = document.getElementById("user-form-container");

    // 초기 상태는 닫힌 상태로 설정
    container.style.display = "none";

    toggleBtn.onclick = () => {
      const isHidden = container.style.display === "none";
      container.style.display = isHidden ? "block" : "none";
      toggleBtn.textContent = isHidden ? "접기" : "열기";
    };

    const form = document.getElementById("user-form");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!confirm("이 유저를 추가하시겠습니까?")) return;
      const formData = new FormData(form);
      try {
        const res = await fetch("/api/v1/users/register_user", {
          method: "POST",
          body: formData
        });
        if (res.ok) {
          showMessage("user-add-result", "유저가 추가되었습니다.");
          form.reset();
        } else {
          const err = await res.json();
          showMessage("user-add-result", err.detail || "에러 발생", false);
        }
      } catch (err) {
        showMessage("user-add-result", "네트워크 오류", false);
      }
    });
  };

  const bindUserListToggle = () => {
    const toggleBtn = document.getElementById("toggle-user-list");
    const listContainer = document.getElementById("user-list");

    toggleBtn.onclick = () => {
      const isHidden = listContainer.style.display === "none";
      listContainer.style.display = isHidden ? "block" : "none";
      toggleBtn.textContent = isHidden ? "접기" : "불러오기";
      if (isHidden) loadUsers();
    };
  };

  async function loadUsers(page = 1) {
    try {
      const res = await fetch("/api/v1/users/get_users_detail");
      const users = await res.json();
      const start = (page - 1) * USERS_PER_PAGE;
      const paginated = users.slice(start, start + USERS_PER_PAGE);
      currentPage = page;

      const container = document.getElementById("user-list");
      container.innerHTML = "";
      const table = document.createElement("table");
      table.className = "user-table";
      table.innerHTML = `
        <thead>
          <tr><th>이름</th><th>성별</th><th>이메일</th><th>권한</th><th>관심사</th><th>참석횟수</th><th>최근참석</th><th>가입일</th><th>수정</th></tr>
        </thead>
        <tbody></tbody>
      `;
      const tbody = table.querySelector("tbody");

      paginated.forEach(user => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${user.username}</td>
          <td>${user.gender}</td>
          <td>${user.email}</td>
          <td>${user.role}</td>
          <td>${user.interests || "-"}</td>
          <td>${user.attendance_count}</td>
          <td>${user.last_attended || "-"}</td>
          <td>${user.created_at.slice(0, 10)}</td>
          <td><button class="edit-user-btn" data-user-id="${user.id}">수정</button></td>
        `;
        tbody.appendChild(tr);
      });

      container.appendChild(table);
      renderPagination(users.length, page);
      bindEditButtons(users);
    } catch (err) {
      console.error("유저 목록 불러오기 실패:", err);
    }
  }

  function renderPagination(total, current) {
    const container = document.getElementById("user-list");
    const totalPages = Math.ceil(total / USERS_PER_PAGE);
    if (totalPages <= 1) return;
    const nav = document.createElement("div");
    for (let i = 1; i <= totalPages; i++) {
      const btn = document.createElement("button");
      btn.textContent = i;
      btn.disabled = i === current;
      btn.onclick = () => loadUsers(i);
      nav.appendChild(btn);
    }
    container.appendChild(nav);
  }

  function bindEditButtons(users) {
    document.querySelectorAll(".edit-user-btn").forEach(btn => {
      btn.onclick = () => {
        const user = users.find(u => u.id == btn.dataset.userId);
        if (user) showEditPopup(user);
      };
    });
  }

  function showEditPopup(user) {
    const popup = document.createElement("div");
    popup.className = "popup-overlay";
    popup.innerHTML = `
      <div class="popup">
        <h3>👤 유저 수정 (${user.username})</h3>
        <form id="edit-user-form">
          <input type="hidden" name="user_id" value="${user.id}" />
          <label>이메일 <input name="email" value="${user.email}" /></label>
          <label>관심사 <input name="interests" value="${user.interests || ""}" /></label>
          <label>성별
            <select name="gender">
              <option value="남" ${user.gender === "남" ? "selected" : ""}>남</option>
              <option value="여" ${user.gender === "여" ? "selected" : ""}>여</option>
            </select>
          </label>
          <label>권한
            <select name="role">
              <option value="회원" ${user.role === "회원" ? "selected" : ""}>회원</option>
              <option value="운영진" ${user.role === "운영진" ? "selected" : ""}>운영진</option>
              <option value="모임장" ${user.role === "모임장" ? "selected" : ""}>모임장</option>
            </select>
          </label>
          <button type="submit">저장</button>
          <button type="button" id="cancel-edit">취소</button>
        </form>
      </div>
    `;
    document.body.appendChild(popup);
    popup.querySelector("#edit-user-form").onsubmit = async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const res = await fetch("/api/v1/users/update_user", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        alert("수정 완료");
        popup.remove();
        loadUsers(currentPage);
      } else {
        const err = await res.json();
        alert("실패: " + (err.detail || "오류"));
      }
    };
    popup.querySelector("#cancel-edit").onclick = () => popup.remove();
  }

  // 초기 실행
  bindUserForm();
  bindUserListToggle();
  window.loadUsers = loadUsers;
});