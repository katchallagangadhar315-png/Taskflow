/**
 * TaskFlow - User Registration Logic
 * Handles client validation, password strength scoring, API calls, and UI states.
 * Monochromatic Design: Only black, white, and gray tones.
 */

// Determine API Base URL dynamically
const API_BASE = window.location.origin.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";

// DOM Elements
const form = document.getElementById("registerForm");
const nameInput = document.getElementById("nameInput");
const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");
const togglePasswordBtn = document.getElementById("togglePasswordBtn");
const submitBtn = document.getElementById("submitBtn");
const btnText = document.getElementById("btnText");
const spinner = document.getElementById("spinner");
const alertBanner = document.getElementById("alertBanner");
const alertMessage = document.getElementById("alertMessage");

// Password Strength Elements
const strengthMeter = document.getElementById("strengthMeter");
const strengthBarFill = document.getElementById("strengthBarFill");
const strengthLabel = document.getElementById("strengthLabel");

// 1. Toggle Show / Hide Password
togglePasswordBtn.addEventListener("click", () => {
    const isPassword = passwordInput.getAttribute("type") === "password";
    passwordInput.setAttribute("type", isPassword ? "text" : "password");
    
    // Toggle eye icon SVG
    togglePasswordBtn.innerHTML = isPassword
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
});

// 2. Real-Time Password Strength Checker (Monochrome)
passwordInput.addEventListener("input", () => {
    const pwd = passwordInput.value;
    if (!pwd) {
        strengthBarFill.style.width = "0%";
        strengthLabel.textContent = "Enter password";
        strengthLabel.style.color = "var(--text-dim)";
        return;
    }

    let score = 0;
    if (pwd.length >= 6) score += 1;
    if (pwd.length >= 10) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    let fillPct = "20%";
    let text = "Very Weak";
    let color = "#525252"; // Dark Gray

    if (score === 2) {
        fillPct = "40%";
        text = "Weak";
        color = "#737373"; // Medium Dark Gray
    } else if (score === 3) {
        fillPct = "65%";
        text = "Fair";
        color = "#A3A3A3"; // Neutral Secondary Gray
    } else if (score === 4) {
        fillPct = "85%";
        text = "Good";
        color = "#D4D4D4"; // Light Gray
    } else if (score >= 5) {
        fillPct = "100%";
        text = "Strong";
        color = "#FFFFFF"; // Pure White
    }

    strengthBarFill.style.width = fillPct;
    strengthBarFill.style.backgroundColor = color;
    strengthLabel.textContent = text;
    strengthLabel.style.color = color;
});

// Helper: Show Alert
function showAlert(message, type = "error") {
    alertBanner.className = `alert-banner ${type}`;
    alertMessage.textContent = message;
    alertBanner.style.display = "flex";
}

// Helper: Hide Alert
function hideAlert() {
    alertBanner.style.display = "none";
}

// Helper: Toggle Button Loading State
function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        btnText.textContent = "Creating Account...";
        spinner.style.display = "inline-block";
    } else {
        submitBtn.disabled = false;
        btnText.textContent = "Create Account";
        spinner.style.display = "none";
    }
}

// 3. Handle Registration Form Submit
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert();

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // Client-side Validation Checks
    if (!name || name.length < 2) {
        showAlert("Please enter your full name (minimum 2 characters).");
        nameInput.focus();
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
        showAlert("Please enter a valid email address (e.g., name@example.com).");
        emailInput.focus();
        return;
    }

    if (!password || password.length < 6) {
        showAlert("Password must be at least 6 characters long.");
        passwordInput.focus();
        return;
    }

    // Prepare Request Payload
    const payload = {
        name: name,
        email: email,
        password: password
    };

    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.status === 201) {
            // Registration Succeeded
            showAlert(
                `Welcome aboard, ${data.user.name}! Your account was created successfully.`,
                "success"
            );
            form.reset();
            strengthBarFill.style.width = "0%";
            strengthLabel.textContent = "Enter password";
            strengthLabel.style.color = "var(--text-dim)";
        } else if (response.status === 400) {
            // Business logic rejection (e.g., duplicate email)
            showAlert(data.detail || "An account with this email already exists.");
        } else if (response.status === 422) {
            // Pydantic Schema Validation Error
            const errorMsg = data.detail && Array.isArray(data.detail)
                ? data.detail.map(err => err.msg).join(", ")
                : "Invalid registration data. Please check your inputs.";
            showAlert(errorMsg);
        } else {
            // Other server error
            showAlert(data.detail || "Server error occurred. Please try again.");
        }
    } catch (err) {
        console.error("Network or connection error:", err);
        showAlert(
            `Unable to connect to the server at ${API_BASE}. Please ensure the FastAPI backend is running.`
        );
    } finally {
        setLoading(false);
    }
});
