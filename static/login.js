document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    const result = document.getElementById("result");
  
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
  
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
  
      try {
        const res = await fetch("/api/v1/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ email, password }),
        });
  
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem("currentUser", JSON.stringify(data));
          location.href = "/";
        } else {
          result.textContent = "❌ 로그인 실패: 이메일 또는 비밀번호 오류";
        }
      } catch (err) {
        result.textContent = "🚫 네트워크 오류가 발생했습니다.";
      }
    });
  });