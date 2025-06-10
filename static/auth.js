// static/auth.js

export function requireLogin() {
    const user = JSON.parse(localStorage.getItem("currentUser"));
    if (!user) {
      window.location.href = "/login";
    }
    return user;
  }
  
  export function requireRole(allowedRoles = []) {
    const user = requireLogin();
    if (!allowedRoles.includes(user.role)) {
      alert("접근 권한이 없습니다.");
      window.location.href = "/";
    }
  }
  
  // 로그아웃 버튼 삽입 및 동작 바인딩
export function renderLogoutButton(includeHome = false) {
  const container = document.createElement("div");
  container.style.position = "fixed";
  container.style.top = "1.5rem";
  container.style.right = "1.5rem";
  container.style.display = "flex";
  container.style.gap = "0.5rem";
  
  const baseBtnStyle = (btn) => {
    btn.style.padding = "0.5rem 1rem";
    btn.style.fontSize = "0.95rem";
    btn.style.border = "none";
    btn.style.borderRadius = "8px";
    btn.style.backgroundColor = "#2b6cb0";
    btn.style.color = "white";
    btn.style.cursor = "pointer";
    btn.style.boxShadow = "0 2px 6px rgba(0, 0, 0, 0.1)";
    btn.style.transition = "background-color 0.2s ease";
    btn.onmouseenter = () => btn.style.backgroundColor = "#2c5282";
    btn.onmouseleave = () => btn.style.backgroundColor = "#2b6cb0";
  };

  if (includeHome) {
    const homeBtn = document.createElement("button");
    homeBtn.textContent = "메인 화면";
    baseBtnStyle(homeBtn);
    homeBtn.onclick = () => {
      window.location.href = "/";
    };
    container.appendChild(homeBtn);
  }

  const logoutBtn = document.createElement("button");
  logoutBtn.textContent = "로그아웃";
  baseBtnStyle(logoutBtn);
  logoutBtn.onclick = () => {
    localStorage.removeItem("currentUser");
    window.location.href = "/login";
  };

  container.appendChild(logoutBtn);
  document.body.appendChild(container);
}
