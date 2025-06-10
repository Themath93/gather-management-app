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
  export function renderLogoutButton() {
    const logoutBtn = document.createElement("button");
    logoutBtn.textContent = "로그아웃";
  
    // 스타일 추가
    logoutBtn.style.position = "fixed";
    logoutBtn.style.top = "1.5rem";
    logoutBtn.style.right = "1.5rem";
    logoutBtn.style.padding = "0.5rem 1rem";
    logoutBtn.style.fontSize = "0.95rem";
    logoutBtn.style.border = "none";
    logoutBtn.style.borderRadius = "8px";
    logoutBtn.style.backgroundColor = "#2b6cb0";
    logoutBtn.style.color = "white";
    logoutBtn.style.cursor = "pointer";
    logoutBtn.style.boxShadow = "0 2px 6px rgba(0, 0, 0, 0.1)";
    logoutBtn.style.transition = "background-color 0.2s ease";
  
    logoutBtn.onmouseenter = () => logoutBtn.style.backgroundColor = "#2c5282";
    logoutBtn.onmouseleave = () => logoutBtn.style.backgroundColor = "#2b6cb0";
  
    logoutBtn.onclick = () => {
      localStorage.removeItem("currentUser");
      window.location.href = "/login";
    };
  
    document.body.appendChild(logoutBtn);
  }