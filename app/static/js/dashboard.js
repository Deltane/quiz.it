document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.create-folder form');
    const folderNameInput = document.getElementById('folder-name');
    const checkboxes = document.querySelectorAll('.quiz-checkboxes input[type="checkbox"]');

    form.addEventListener('submit', function(event) {
        // Form validation
        if (!folderNameInput.value.trim()) {
            alert('Folder name cannot be empty.');
            event.preventDefault();
            return;
        }

        let isChecked = false;
        checkboxes.forEach(function(checkbox) {
            if (checkbox.checked) {
                isChecked = true;
            }
        });

        if (!isChecked) {
            alert('Please select at least one quiz.');
            event.preventDefault();
        }
    });

    // Attach event listeners dynamically for newly added elements
    document.body.addEventListener('click', function(event) {
        if (event.target.matches('form[action^="/delete_quiz"] button')) {
            const confirmDelete = confirm('Are you sure you want to delete this quiz? This action cannot be undone.');
            if (!confirmDelete) event.preventDefault();
        } else if (event.target.matches('form[action^="/unassign_quiz_from_folder"] button')) {
            const confirmUnassign = confirm('Are you sure you want to unassign this quiz from the folder?');
            if (!confirmUnassign) event.preventDefault();
        }
    });

    // Handle AJAX for assigning quizzes to folders
    document.querySelectorAll('[id^="assign-form-"]').forEach(wrapper => {
        const form = wrapper.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(form);

                fetch('/assign_quiz_to_folder', {
                    method: 'POST',
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    if (data.quiz_html && data.folder_id) {
                        const targetList = document.querySelector(`#assign-form-${data.folder_id}`).closest('.folder-entry').querySelector('ul');
                        targetList.insertAdjacentHTML('beforeend', data.quiz_html);
                        form.reset();
                        wrapper.style.display = 'none';
                    } else {
                        alert("Failed to assign quiz to folder.");
                    }
                });
            });
        }
    });

    // AJAX search for users to share quizzes with
    const searchInputs = document.querySelectorAll('.user-search-input');

    searchInputs.forEach(input => {
        input.addEventListener('input', function () {
            const query = input.value;
            const resultsContainer = document.getElementById(`${input.dataset.resultsContainer}`);

            if (query.length > 2) { // Only search if query is longer than 2 characters
                fetch(`/search_users?query=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        resultsContainer.innerHTML = '';
                        data.users.forEach(user => {
                            const userItem = document.createElement('div');
                            userItem.className = 'user-item';
                            userItem.textContent = user.email;
                            userItem.addEventListener('click', () => {
                                input.value = user.email;
                                resultsContainer.innerHTML = '';
                            });
                            resultsContainer.appendChild(userItem);
                        });
                    });
            } else {
                resultsContainer.innerHTML = '';
            }
        });
    });
});

function toggleRenameForm(type, id) {
    const form = document.getElementById(`${type}-rename-form-${id}`);
    if (form) {
        form.style.display = form.style.display === 'none' ? 'inline' : 'none';
    }
}

function toggleAssignForm(folderId) {
    const form = document.getElementById(`assign-form-${folderId}`);
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

function openShareModal(quizId) {
    const modal = document.getElementById(`share-modal-${quizId}`);
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeShareModal(quizId) {
    const modal = document.getElementById(`share-modal-${quizId}`);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Attach modal functions to the global window object
window.openShareModal = openShareModal;
window.closeShareModal = closeShareModal;

// Close modal when clicking outside of it
document.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

