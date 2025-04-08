document.getElementById('task-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const taskName = document.getElementById('task-name').value;

    // Send task to the backend API
    const response = await fetch('/api/tasks/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: taskName }),
    });

    if (response.ok) {
        const task = await response.json();
        addTaskToList(task);
        document.getElementById('task-form').reset();
    } else {
        alert('Failed to add task');
    }
});

async function fetchTasks() {
    const response = await fetch('/api/tasks/');
    if (response.ok) {
        const data = await response.json();
        data.tasks.forEach(addTaskToList);
    } else {
        alert('Failed to fetch tasks');
    }
}

function addTaskToList(task) {
    const taskList = document.getElementById('task-list');
    const listItem = document.createElement('li');
    listItem.textContent = task.name;
    taskList.appendChild(listItem);
}

// Fetch tasks on page load
fetchTasks();

async function fetchAnalytics() {
    const response = await fetch('/api/analytics/');
    if (response.ok) {
        const data = await response.json();
        document.getElementById('completed-tasks').textContent = data.completed;
        document.getElementById('pending-tasks').textContent = data.pending;
    } else {
        alert('Failed to fetch analytics');
    }
}

// Fetch analytics on page load
fetchAnalytics();
