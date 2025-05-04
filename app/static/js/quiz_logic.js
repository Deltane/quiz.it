document.addEventListener('DOMContentLoaded', function () {
    let currentQuestionIndex = 0;
    let score = 0;
    let timerInterval;
    const questionTimeLimit = 30; // 30 seconds per question

    function resetQuiz() {
        currentQuestionIndex = 0;
        score = 0;
        document.getElementById('next-question').style.display = 'none';
        document.getElementById('timer-container').style.display = 'block';
        document.getElementById('question-container').innerHTML = '';
    }

    function startTimer() {
        const timerProgress = document.getElementById('timer-progress');
        let timeLeft = questionTimeLimit * 1000;
        const interval = 100;
        const decrement = 100 / (timeLeft / interval);

        timerProgress.style.width = '100%';

        timerInterval = setInterval(() => {
            timeLeft -= interval;
            const percentage = (timeLeft / (questionTimeLimit * 1000)) * 100;
            timerProgress.style.width = `${percentage}%`;

            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                alert('Time is up for this question! Moving to the next question.');
                submitAnswer(null);
            }
        }, interval);
    }

    function stopTimer() {
        clearInterval(timerInterval);
    }

    function loadQuestion() {
        if (currentQuestionIndex === 0) resetQuiz();
        fetch(`/get_question/${currentQuestionIndex}`)
            .then(response => response.json())
            .then(data => {
                if (data.question) {
                    const questionContainer = document.getElementById('question-container');
                    questionContainer.innerHTML = '';

                    questionContainer.innerHTML += `<p><strong>Q${currentQuestionIndex + 1}:</strong> ${data.question}</p>`;

                    if (data.type === 'multiple-choice' && data.options) {
                        data.options.forEach((option, index) => {
                            const optionId = `option${index}`;
                            questionContainer.innerHTML += `
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="answer" id="${optionId}" value="${option}">
                                    <label class="form-check-label" for="${optionId}">${option}</label>
                                </div>
                            `;
                        });
                    } else {
                        questionContainer.innerHTML += `
                            <div class="form-group">
                                <input type="text" class="form-control" name="answer" placeholder="Type your answer here" required>
                            </div>
                        `;
                    }

                    document.getElementById('next-question').style.display = 'block';
                    startTimer();
                } else {
                    document.getElementById('question-container').innerHTML = `<p>Quiz completed! Your score is: ${score}</p>`;
                    document.getElementById('next-question').style.display = 'none';
                    document.getElementById('timer-container').style.display = 'none';
                }
            })
            .catch(err => {
                document.getElementById('question-container').innerHTML = `<p>Error loading question: ${err.message}</p>`;
            });
    }

    document.getElementById('next-question').addEventListener('click', function () {
        let answer;
        if (document.querySelectorAll('input[type="radio"]').length > 0) {
            answer = document.querySelector('input[name="answer"]:checked')?.value;
            if (!answer) {
                alert('Please select an answer before proceeding.');
                return;
            }
        } else {
            answer = document.querySelector('input[name="answer"]').value.trim();
            if (!answer) {
                alert('Please enter your answer before proceeding.');
                return;
            }
        }
        submitAnswer(answer);
    });

    function submitAnswer(selectedAnswer) {
        stopTimer();

        fetch('/submit_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ questionIndex: currentQuestionIndex, answer: selectedAnswer })
        })
        .then(response => response.json())
        .then(data => {
            if (data.completed) {
                document.getElementById('question-container').innerHTML = `
                    <div class="result">
                        <p>Quiz completed! Your score is: ${data.score}</p>
                        <div class="button-group" style="margin-top: 20px; display: flex; justify-content: center; gap: 15px;">
                            <a href="/create_quiz" class="btn">Redo</a>
                            <a href="/" class="btn">Home</a>
                            <a href="/dashboard" class="btn">Quiz Dashboard</a>
                        </div>
                    </div>
                `;
                document.getElementById('next-question').style.display = 'none';
                document.getElementById('timer-container').style.display = 'none';
            } else {
                currentQuestionIndex++;
                loadQuestion();
            }
        })
        .catch(err => {
            alert('Error submitting answer: ' + err.message);
        });
    }

    loadQuestion();
});

