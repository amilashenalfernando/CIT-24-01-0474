// CloudTask Frontend Application Logic

let currentFilter = 'all';
let searchQuery = '';

document.addEventListener('DOMContentLoaded', () => {
    fetchTasks();
    fetchStats();
    setupEventListeners();
});

function setupEventListeners() {
    // Form submission
    const form = document.getElementById('add-task-form');
    form.addEventListener('submit', handleAddTask);

    // Filter tabs
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            tabs.forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.getAttribute('data-filter');
            fetchTasks();
        });
    });

    // Search bar with debounce
    const searchInput = document.getElementById('search-input');
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchQuery = e.target.value;
            fetchTasks();
        }, 300);
    });
}

async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (data.success) {
            document.getElementById('stat-total').textContent = data.stats.total;
            document.getElementById('stat-pending').textContent = data.stats.pending;
            document.getElementById('stat-completed').textContent = data.stats.completed;
            if (data.stats.views !== undefined) {
                document.getElementById('stat-views').textContent = data.stats.views;
            }
        }
    } catch (err) {
        console.error('Failed to fetch stats:', err);
    }
}

async function fetchTasks() {
    const listContainer = document.getElementById('task-list');
    
    let url = '/api/tasks?';
    if (currentFilter !== 'all') {
        url += `status=${currentFilter}&`;
    }
    if (searchQuery.trim() !== '') {
        url += `q=${encodeURIComponent(searchQuery.trim())}`;
    }

    try {
        const res = await fetch(url);
        const data = await res.json();

        if (!data.success) {
            listContainer.innerHTML = `<div class="empty-state"><p>⚠️ ${data.error || 'Failed to load tasks.'}</p></div>`;
            return;
        }

        if (data.tasks.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <p>✨ No tasks found. Create a new task on the left!</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = data.tasks.map(task => createTaskCard(task)).join('');
    } catch (err) {
        console.error('Failed to fetch tasks:', err);
        listContainer.innerHTML = `<div class="empty-state"><p>⚠️ Network or Server Error.</p></div>`;
    }
}

function createTaskCard(task) {
    const formattedDate = task.created_at ? new Date(task.created_at).toLocaleString() : '';
    const isChecked = task.completed ? 'checked' : '';
    const itemClass = task.completed ? 'task-item completed' : 'task-item';

    return `
        <div class="${itemClass}" id="task-${task.id}">
            <div class="task-left">
                <div class="custom-checkbox ${isChecked}" onclick="toggleTask(${task.id})">
                    ${task.completed ? '✓' : ''}
                </div>
                <div class="task-text">
                    <h3>${escapeHtml(task.title)}</h3>
                    ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
                    <div class="task-meta">
                        <span class="badge badge-priority-${task.priority}">${task.priority}</span>
                        <span class="badge badge-category">${task.category}</span>
                        <span class="task-time">${formattedDate}</span>
                    </div>
                </div>
            </div>
            <button class="btn-delete" onclick="deleteTask(${task.id})" title="Delete Task">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"/>
                </svg>
            </button>
        </div>
    `;
}

async function handleAddTask(e) {
    e.preventDefault();
    const titleInput = document.getElementById('task-title');
    const descInput = document.getElementById('task-desc');
    const priorityInput = document.getElementById('task-priority');
    const categoryInput = document.getElementById('task-category');
    const submitBtn = document.getElementById('btn-submit');

    const title = titleInput.value.trim();
    if (!title) return;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    try {
        const res = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                description: descInput.value.trim(),
                priority: priorityInput.value,
                category: categoryInput.value
            })
        });

        const data = await res.json();
        if (data.success) {
            titleInput.value = '';
            descInput.value = '';
            fetchTasks();
            fetchStats();
        } else {
            alert('Error adding task: ' + data.error);
        }
    } catch (err) {
        console.error('Error adding task:', err);
        alert('Network error while adding task.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Add Task to Database';
    }
}

async function toggleTask(id) {
    try {
        const res = await fetch(`/api/tasks/${id}/toggle`, { method: 'PUT' });
        const data = await res.json();
        if (data.success) {
            fetchTasks();
            fetchStats();
        }
    } catch (err) {
        console.error('Failed to toggle task:', err);
    }
}

async function deleteTask(id) {
    if (!confirm('Are you sure you want to delete this task from persistent storage?')) {
        return;
    }

    try {
        const res = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            fetchTasks();
            fetchStats();
        }
    } catch (err) {
        console.error('Failed to delete task:', err);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
