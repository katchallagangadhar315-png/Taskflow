/**
 * TaskFlow — User Login Logic
 * Handles client validation, API authentication, session storage, and dashboard redirection.
 */

const form = document.getElementById("loginForm");
const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");
const togglePasswordBtn = document.getElementById("togglePasswordBtn");
const submitBtn = document.getElementById("submitBtn");
const btnText = document.getElementById("btnText");
const spinner = document.getElementById("spinner");
const alertBanner = document.getElementById("alertBanner");
const alertMessage = document.getElementById("alertMessage");

// Check if user was redirected due to an expired session
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get("expired") === "true") {
    showAlert("Your session has expired. Please sign in again.", "error");
}

// 1. Toggle Show / Hide Password
togglePasswordBtn.addEventListener("click", () => {
    const isPassword = passwordInput.getAttribute("type") === "password";
    passwordInput.setAttribute("type", isPassword ? "text" : "password");
    
    togglePasswordBtn.innerHTML = isPassword
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
});

// Helper: Show Alert Banner
function showAlert(message, type = "error") {
    alertBanner.className = `alert-banner ${type}`;
    alertMessage.textContent = message;
    alertBanner.style.display = "flex";
}

// Helper: Hide Alert Banner
function hideAlert() {
    alertBanner.style.display = "none";
}

// Helper: Toggle Button Loading State
function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        btnText.textContent = "Authenticating...";
        spinner.style.display = "inline-block";
    } else {
        submitBtn.disabled = false;
        btnText.textContent = "Sign In";
        spinner.style.display = "none";
    }
}

// 2. Handle Login Form Submit
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert();

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email) {
        showAlert("Please enter your registered email address.");
        emailInput.focus();
        return;
    }

    if (!password) {
        showAlert("Please enter your password.");
        passwordInput.focus();
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.status === 200) {
            // Authentication Succeeded
            // Save JWT access token & user profile in localStorage
            Auth.saveSession(data.access_token, data.user);

            showAlert(`Authentication successful! Welcome, ${data.user.name}. Redirecting...`, "success");

            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 600);
        } else if (response.status === 401) {
            // Invalid credentials
            showAlert(data.detail || "Invalid email or password. Please try again.");
            passwordInput.focus();
        } else if (response.status === 422) {
            // Validation error
            const errorMsg = data.detail && Array.isArray(data.detail)
                ? data.detail.map(err => err.msg).join(", ")
                : "Invalid input. Please check your email format.";
            showAlert(errorMsg);
        } else {
            showAlert(data.detail || "Server error occurred. Please try again later.");
        }
    } catch (err) {
        console.error("Login network error:", err);
        showAlert(`Unable to connect to backend at ${API_BASE}. Please ensure FastAPI is running.`);
    } finally {
        setLoading(false);
    }
});
