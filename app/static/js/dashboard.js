document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.create-folder form');
    if (form) { // Ensure the form exists before adding event listeners
        const folderNameInput = document.getElementById('folder-name');
        const checkboxes = document.querySelectorAll('.quiz-checkboxes input[type="checkbox"]');

        form.addEventListener('submit', function(event) {
            // Form validation
            if (!folderNameInput || !folderNameInput.value.trim()) {
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
    }

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

    // Handle AJAX for sharing quizzes
    document.querySelectorAll('.share-quiz-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const quizId = form.dataset.quizId;
            const recipientEmailInput = form.querySelector('input[name="recipient_email"]');
            const recipientEmail = recipientEmailInput.value;
            const messageDiv = form.querySelector('.share-message');

            if (!recipientEmail) {
                messageDiv.textContent = 'Recipient email is required.';
                messageDiv.className = 'share-message error';
                return;
            }

            fetch('/share_quiz', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Include CSRF token if your app uses them for AJAX POSTs
                    // 'X-CSRFToken': getCsrfToken() 
                },
                body: JSON.stringify({ 
                    quiz_id: quizId, 
                    recipient_email: recipientEmail 
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    messageDiv.textContent = data.success;
                    messageDiv.className = 'share-message success';
                    recipientEmailInput.value = ''; // Clear input
                } else {
                    messageDiv.textContent = data.error || 'Failed to share quiz.';
                    messageDiv.className = 'share-message error';
                }
            })
            .catch(error => {
                console.error('Error sharing quiz:', error);
                messageDiv.textContent = 'An unexpected error occurred.';
                messageDiv.className = 'share-message error';
            });
        });
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

