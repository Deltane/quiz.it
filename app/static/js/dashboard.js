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
});

