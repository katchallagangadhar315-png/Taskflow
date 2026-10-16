/**
 * TaskFlow - Personal Dashboard & Task Management Client Logic
 * Handles real-time metrics, task CRUD, search/filtering, modals, sidebar navigation, and ownership isolation.
 * Monochromatic Design: Only black, white, and gray tones.
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Guard check: Ensure user is authenticated
    if (!Auth.isAuthenticated()) {
        window.location.href = "login.html";
        return;
    }

    // DOM Elements - Navigation & User Info
    const navAvatar = document.getElementById("navAvatar");
    const navUserName = document.getElementById("navUserName");
    const navUserEmail = document.getElementById("navUserEmail");
    const welcomeTitle = document.getElementById("welcomeTitle");
    const signOutBtn = document.getElementById("signOutBtn");

    // DOM Elements - Sidebar & Responsive Drawer
    const dashboardSidebar = document.getElementById("dashboardSidebar");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");
    const quickCreateTaskBtn = document.getElementById("quickCreateTaskBtn");

    // DOM Elements - Sidebar Filter Buttons
    const navFilterAll = document.getElementById("navFilterAll");
    const navFilterPending = document.getElementById("navFilterPending");
    const navFilterInProgress = document.getElementById("navFilterInProgress");
    const navFilterCompleted = document.getElementById("navFilterCompleted");
    const navFilterHigh = document.getElementById("navFilterHigh");
    const sidebarNavItems = [navFilterAll, navFilterPending, navFilterInProgress, navFilterCompleted, navFilterHigh].filter(Boolean);

    // DOM Elements - Metrics
    const metricTotal = document.getElementById("metricTotal");
    const metricPending = document.getElementById("metricPending");
    const metricCompleted = document.getElementById("metricCompleted");
    const metricOverdue = document.getElementById("metricOverdue");

    // DOM Elements - Toolbar & Search
    const searchInput = document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const priorityFilter = document.getElementById("priorityFilter");
    const openCreateModalBtn = document.getElementById("openCreateModalBtn");
    const tasksGrid = document.getElementById("tasksGrid");

    // DOM Elements - Task Modal (Create & Edit)
    const taskModal = document.getElementById("taskModal");
    const taskForm = document.getElementById("taskForm");
    const modalTitle = document.getElementById("modalTitle");
    const taskIdInput = document.getElementById("taskIdInput");
    const taskTitleInput = document.getElementById("taskTitleInput");
    const taskDescInput = document.getElementById("taskDescInput");
    const taskPriorityInput = document.getElementById("taskPriorityInput");
    const taskStatusInput = document.getElementById("taskStatusInput");
    const taskDueDateInput = document.getElementById("taskDueDateInput");
    const closeTaskModalBtn = document.getElementById("closeTaskModalBtn");
    const cancelTaskModalBtn = document.getElementById("cancelTaskModalBtn");
    const saveTaskBtn = document.getElementById("saveTaskBtn");
    const saveTaskBtnText = document.getElementById("saveTaskBtnText");
    const saveTaskSpinner = document.getElementById("saveTaskSpinner");
    const modalAlert = document.getElementById("modalAlert");
    const modalAlertMessage = document.getElementById("modalAlertMessage");

    // DOM Elements - Delete Confirmation Modal
    const deleteModal = document.getElementById("deleteModal");
    const deleteTaskTitleDisplay = document.getElementById("deleteTaskTitleDisplay");
    const closeDeleteModalBtn = document.getElementById("closeDeleteModalBtn");
    const cancelDeleteModalBtn = document.getElementById("cancelDeleteModalBtn");
    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
    const confirmDeleteBtnText = document.getElementById("confirmDeleteBtnText");
    const deleteSpinner = document.getElementById("deleteSpinner");

    let taskToDeleteId = null;
    let searchDebounceTimer = null;

    // Initialize User Interface
    initUserProfile();
    loadDashboardData();

    // --------------------------------------------------------------------------
    // User Profile Initialization
    // --------------------------------------------------------------------------
    async function initUserProfile() {
        const cachedUser = Auth.getUser();
        if (cachedUser) {
            updateUserUI(cachedUser);
        }

        try {
            const res = await Auth.authFetch("/api/v1/auth/me");
            if (res.ok) {
                const user = await res.json();
                Auth.saveSession(Auth.getToken(), user);
                updateUserUI(user);
            }
        } catch (err) {
            console.error("Failed to load user profile:", err);
        }
    }

    function updateUserUI(user) {
        if (!user) return;
        if (navUserName) navUserName.textContent = user.name;
        if (navUserEmail) navUserEmail.textContent = user.email;
        if (welcomeTitle) welcomeTitle.textContent = `Welcome back, ${user.name.split(" ")[0]}!`;
        if (navAvatar) navAvatar.textContent = user.name ? user.name.charAt(0).toUpperCase() : "U";
    }

    // Sign Out
    if (signOutBtn) {
        signOutBtn.addEventListener("click", () => {
            Auth.logout();
        });
    }

    // --------------------------------------------------------------------------
    // Responsive Mobile Sidebar Toggle
    // --------------------------------------------------------------------------
    function toggleMobileSidebar(open) {
        if (!dashboardSidebar) return;
        if (open) {
            dashboardSidebar.classList.add("mobile-open");
            if (sidebarBackdrop) sidebarBackdrop.style.display = "block";
        } else {
            dashboardSidebar.classList.remove("mobile-open");
            if (sidebarBackdrop) sidebarBackdrop.style.display = "none";
        }
    }

    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener("click", () => {
            const isOpen = dashboardSidebar.classList.contains("mobile-open");
            toggleMobileSidebar(!isOpen);
        });
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener("click", () => {
            toggleMobileSidebar(false);
        });
    }

    // --------------------------------------------------------------------------
    // Sidebar Quick Navigation Filter Links
    // --------------------------------------------------------------------------
    sidebarNavItems.forEach(item => {
        item.addEventListener("click", () => {
            sidebarNavItems.forEach(el => el.classList.remove("active"));
            item.classList.add("active");

            const status = item.getAttribute("data-status");
            const priority = item.getAttribute("data-priority");

            if (status !== null) {
                statusFilter.value = status;
                priorityFilter.value = "";
            } else if (priority !== null) {
                priorityFilter.value = priority;
                statusFilter.value = "";
            }

            toggleMobileSidebar(false);
            loadTasks();
        });
    });

    // --------------------------------------------------------------------------
    // Dashboard Data Loading (Metrics + Tasks)
    // --------------------------------------------------------------------------
    async function loadDashboardData() {
        await Promise.all([loadMetrics(), loadTasks()]);
    }

    // 1. Fetch Task Metrics
    async function loadMetrics() {
        try {
            const res = await Auth.authFetch("/api/v1/tasks/metrics");
            if (res.ok) {
                const data = await res.json();
                if (metricTotal) metricTotal.textContent = data.total;
                if (metricPending) metricPending.textContent = data.pending + data.in_progress;
                if (metricCompleted) metricCompleted.textContent = data.completed;
                if (metricOverdue) metricOverdue.textContent = data.overdue;
            }
        } catch (err) {
            console.error("Failed to load metrics:", err);
        }
    }

    // 2. Fetch Tasks with Search and Filter Query Params
    async function loadTasks() {
        const params = new URLSearchParams();
        const search = searchInput ? searchInput.value.trim() : "";
        const status = statusFilter ? statusFilter.value : "";
        const priority = priorityFilter ? priorityFilter.value : "";

        if (search) params.append("search", search);
        if (status) params.append("status", status);
        if (priority) params.append("priority", priority);

        const url = `/api/v1/tasks/?${params.toString()}`;

        try {
            const res = await Auth.authFetch(url);
            if (res.ok) {
                const tasks = await res.json();
                renderTasks(tasks);
            } else {
                tasksGrid.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                            </svg>
                        </div>
                        <h3 class="empty-title">Error Loading Tasks</h3>
                        <p class="empty-subtext">Could not retrieve tasks from server. Please try refreshing.</p>
                    </div>`;
            }
        } catch (err) {
            console.error("Failed to fetch tasks:", err);
            tasksGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                    </div>
                    <h3 class="empty-title">Connection Error</h3>
                    <p class="empty-subtext">Unable to reach the backend server.</p>
                </div>`;
        }
    }

    // --------------------------------------------------------------------------
    // Render Task Cards
    // --------------------------------------------------------------------------
    function renderTasks(tasks) {
        if (!tasks || tasks.length === 0) {
            tasksGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                        </svg>
                    </div>
                    <h3 class="empty-title">No tasks found</h3>
                    <p class="empty-subtext">
                        ${(searchInput && searchInput.value) || (statusFilter && statusFilter.value) || (priorityFilter && priorityFilter.value)
                            ? "Try adjusting your search query or filters."
                            : "Your task list is empty. Create your first task to start organizing!"}
                    </p>
                    <button id="emptyCreateBtn" class="btn-new-task">
                        + Create Your First Task
                    </button>
                </div>`;
            
            const emptyBtn = document.getElementById("emptyCreateBtn");
            if (emptyBtn) {
                emptyBtn.addEventListener("click", () => openTaskModal());
            }
            return;
        }

        tasksGrid.innerHTML = tasks.map(task => {
            const isCompleted = task.status === "completed";
            const isOverdue = Boolean(task.is_overdue);

            // Format Due Date
            let dueDateFormatted = "No due date";
            if (task.due_date) {
                const d = new Date(task.due_date);
                dueDateFormatted = d.toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit"
                });
            }

            // Status Badge Text
            const statusLabelMap = {
                pending: "Pending",
                in_progress: "In Progress",
                completed: "Completed"
            };

            return `
                <article class="task-card ${isCompleted ? 'is-completed' : ''} ${isOverdue ? 'is-overdue' : ''}" data-task-id="${task.id}">
                    <div>
                        <div class="task-badges">
                            <span class="badge badge-${task.status}">
                                ${statusLabelMap[task.status] || task.status}
                            </span>
                            <span class="badge badge-priority-${task.priority}">
                                ${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)} Priority
                            </span>
                            ${isOverdue ? '<span class="badge badge-overdue">Overdue</span>' : ''}
                        </div>

                        <h3 class="task-title">${escapeHTML(task.title)}</h3>
                        <p class="task-description">${escapeHTML(task.description || "No description provided.")}</p>
                    </div>

                    <div class="task-meta">
                        <div class="task-due" title="Due Date">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                            <span>${dueDateFormatted}</span>
                        </div>

                        <div class="task-actions">
                            <!-- Toggle Complete -->
                            <button
                                class="btn-card-action btn-toggle-complete"
                                onclick="window.TaskActions.toggleStatus(${task.id}, '${task.status}')"
                                title="${isCompleted ? 'Mark Pending' : 'Mark Completed'}"
                            >
                                ${isCompleted
                                    ? `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"></path><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg> Reopen`
                                    : `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Done`
                                }
                            </button>

                            <!-- Edit Task -->
                            <button
                                class="btn-card-action"
                                onclick="window.TaskActions.openEdit(${task.id})"
                                title="Edit Task"
                            >
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
                                </svg>
                                Edit
                            </button>

                            <!-- Delete Task -->
                            <button
                                class="btn-card-action btn-delete"
                                onclick="window.TaskActions.openDelete(${task.id}, '${escapeQuote(task.title)}')"
                                title="Delete Task"
                            >
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </article>
            `;
        }).join("");
    }

    // --------------------------------------------------------------------------
    // Search & Filter Listeners
    // --------------------------------------------------------------------------
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                loadTasks();
            }, 280);
        });
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", () => {
            // Update active state in sidebar
            sidebarNavItems.forEach(el => el.classList.remove("active"));
            const match = sidebarNavItems.find(el => el.getAttribute("data-status") === statusFilter.value);
            if (match) match.classList.add("active");
            loadTasks();
        });
    }

    if (priorityFilter) {
        priorityFilter.addEventListener("change", () => {
            sidebarNavItems.forEach(el => el.classList.remove("active"));
            const match = sidebarNavItems.find(el => el.getAttribute("data-priority") === priorityFilter.value);
            if (match) match.classList.add("active");
            loadTasks();
        });
    }

    // --------------------------------------------------------------------------
    // Task Create & Edit Modal Operations
    // --------------------------------------------------------------------------
    if (openCreateModalBtn) openCreateModalBtn.addEventListener("click", () => openTaskModal());
    if (quickCreateTaskBtn) quickCreateTaskBtn.addEventListener("click", () => openTaskModal());
    if (closeTaskModalBtn) closeTaskModalBtn.addEventListener("click", () => closeTaskModal());
    if (cancelTaskModalBtn) cancelTaskModalBtn.addEventListener("click", () => closeTaskModal());

    function openTaskModal(task = null) {
        hideModalAlert();
        taskForm.reset();

        if (task) {
            // Edit Mode
            modalTitle.textContent = "Edit Task";
            taskIdInput.value = task.id;
            taskTitleInput.value = task.title;
            taskDescInput.value = task.description || "";
            taskPriorityInput.value = task.priority;
            taskStatusInput.value = task.status;

            if (task.due_date) {
                // Format for datetime-local (YYYY-MM-DDTHH:mm)
                const d = new Date(task.due_date);
                const isoStr = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                taskDueDateInput.value = isoStr;
            } else {
                taskDueDateInput.value = "";
            }

            saveTaskBtnText.textContent = "Update Task";
        } else {
            // Create Mode
            modalTitle.textContent = "Create New Task";
            taskIdInput.value = "";
            taskPriorityInput.value = "medium";
            taskStatusInput.value = "pending";
            taskDueDateInput.value = "";
            saveTaskBtnText.textContent = "Create Task";
        }

        taskModal.style.display = "flex";
        setTimeout(() => taskTitleInput.focus(), 50);
    }

    function closeTaskModal() {
        taskModal.style.display = "none";
    }

    function showModalAlert(message) {
        modalAlertMessage.textContent = message;
        modalAlert.style.display = "flex";
    }

    function hideModalAlert() {
        modalAlert.style.display = "none";
    }

    // Submit Task Form (Create or Update)
    taskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideModalAlert();

        const title = taskTitleInput.value.trim();
        const description = taskDescInput.value.trim();
        const priority = taskPriorityInput.value;
        const status = taskStatusInput.value;
        const dueVal = taskDueDateInput.value;
        const taskId = taskIdInput.value;

        if (!title) {
            showModalAlert("Please enter a task title.");
            taskTitleInput.focus();
            return;
        }

        const payload = {
            title: title,
            description: description || null,
            priority: priority,
            status: status,
            due_date: dueVal ? new Date(dueVal).toISOString() : null
        };

        saveTaskBtn.disabled = true;
        saveTaskSpinner.style.display = "inline-block";
        saveTaskBtnText.textContent = taskId ? "Saving..." : "Creating...";

        try {
            const isEdit = Boolean(taskId);
            const url = isEdit ? `/api/v1/tasks/${taskId}` : "/api/v1/tasks/";
            const method = isEdit ? "PUT" : "POST";

            const res = await Auth.authFetch(url, {
                method: method,
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                closeTaskModal();
                await loadDashboardData();
            } else {
                const errData = await res.json();
                showModalAlert(errData.detail || "Failed to save task. Please try again.");
            }
        } catch (err) {
            console.error("Save task error:", err);
            showModalAlert("Network error occurred while connecting to the server.");
        } finally {
            saveTaskBtn.disabled = false;
            saveTaskSpinner.style.display = "none";
            saveTaskBtnText.textContent = taskId ? "Update Task" : "Create Task";
        }
    });

    // --------------------------------------------------------------------------
    // Delete Confirmation Modal Operations
    // --------------------------------------------------------------------------
    if (closeDeleteModalBtn) closeDeleteModalBtn.addEventListener("click", () => closeDeleteModal());
    if (cancelDeleteModalBtn) cancelDeleteModalBtn.addEventListener("click", () => closeDeleteModal());

    function openDeleteModal(taskId, title) {
        taskToDeleteId = taskId;
        deleteTaskTitleDisplay.textContent = `"${title}"`;
        deleteModal.style.display = "flex";
    }

    function closeDeleteModal() {
        deleteModal.style.display = "none";
        taskToDeleteId = null;
    }

    confirmDeleteBtn.addEventListener("click", async () => {
        if (!taskToDeleteId) return;

        confirmDeleteBtn.disabled = true;
        deleteSpinner.style.display = "inline-block";
        confirmDeleteBtnText.textContent = "Deleting...";

        try {
            const res = await Auth.authFetch(`/api/v1/tasks/${taskToDeleteId}`, {
                method: "DELETE"
            });

            if (res.ok) {
                closeDeleteModal();
                await loadDashboardData();
            } else {
                const errData = await res.json();
                alert(errData.detail || "Failed to delete task.");
            }
        } catch (err) {
            console.error("Delete task error:", err);
            alert("Network error occurred while deleting task.");
        } finally {
            confirmDeleteBtn.disabled = false;
            deleteSpinner.style.display = "none";
            confirmDeleteBtnText.textContent = "Delete Task";
        }
    });

    // --------------------------------------------------------------------------
    // Global Task Actions (invoked from card buttons)
    // --------------------------------------------------------------------------
    window.TaskActions = {
        async toggleStatus(taskId, currentStatus) {
            const newStatus = currentStatus === "completed" ? "pending" : "completed";
            try {
                const res = await Auth.authFetch(`/api/v1/tasks/${taskId}`, {
                    method: "PUT",
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    await loadDashboardData();
                }
            } catch (err) {
                console.error("Toggle task error:", err);
            }
        },

        async openEdit(taskId) {
            try {
                const res = await Auth.authFetch(`/api/v1/tasks/${taskId}`);
                if (res.ok) {
                    const task = await res.json();
                    openTaskModal(task);
                } else {
                    const err = await res.json();
                    alert(err.detail || "Could not fetch task details.");
                }
            } catch (err) {
                console.error("Fetch task details error:", err);
            }
        },

        openDelete(taskId, title) {
            openDeleteModal(taskId, title);
        }
    };

    // Helper: Escape HTML to prevent XSS
    function escapeHTML(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function escapeQuote(str) {
        if (!str) return "";
        return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    }
});
