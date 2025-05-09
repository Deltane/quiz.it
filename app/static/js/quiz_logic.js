let answers = [];
$(document).ready(function () {
    let currentQuestionIndex = 0;
    let score = 0;
    let timerInterval;

    function resetQuiz() {
        currentQuestionIndex = 0;
        score = 0;
        $('#next-question').hide();
        $('#timer-container').show();
        $('#question-container').empty();
    }

    function startTimer() {
        const $timerProgress = $('#timer-progress');
        const $timerDisplay = $('#timer-display');
        const totalDuration = parseInt($timerProgress.data('total-time')) || 60;
        let elapsed = 0;

        $timerProgress.css({
            transition: `width ${totalDuration}s linear`,
            width: '0%'
        });
        $timerDisplay.text(formatTime(totalDuration));

        timerInterval = setInterval(() => {
            elapsed++;
            $timerDisplay.text(formatTime(totalDuration - elapsed));

            if (elapsed >= totalDuration) {
                clearInterval(timerInterval);
                submitAnswer(null);
            }
        }, 1000);
    }

    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
        const secs = (seconds % 60).toString().padStart(2, '0');
        return `${mins}:${secs}`;
    }

    function stopTimer() {
        clearInterval(timerInterval);
    }

    function loadQuestion() {
        if (currentQuestionIndex === 0) resetQuiz();
        $.getJSON(`/get_question/${currentQuestionIndex}`, function (data) {
            const $questionContainer = $('#question-container').empty();

            if (data.question) {
                $questionContainer.append(`<p><strong>Q${currentQuestionIndex + 1}:</strong> ${data.question}</p>`);

                if (data.type === 'multiple-choice' && data.options) {
                    data.options.forEach((option, index) => {
                        const optionId = `option${index}`;
                        $questionContainer.append(`
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="answer" id="${optionId}" value="${option}">
                                <label class="form-check-label" for="${optionId}">${option}</label>
                            </div>
                        `);
                    });
                } else {
                    $questionContainer.append(`
                        <div class="form-group">
                            <input type="text" class="form-control" name="answer" placeholder="Type your answer here" required>
                        </div>
                    `);
                }

                $('#next-question').show();
                // Show/hide previous-question button
                if (currentQuestionIndex > 0) {
                    $('#prev-question').show();
                } else {
                    $('#prev-question').hide();
                }
                // Restore previous answer if it exists
                const prevAnswer = answers[currentQuestionIndex];
                if (prevAnswer) {
                    if (data.type === 'multiple-choice' && data.options) {
                        $(`input[name="answer"][value="${prevAnswer}"]`).prop('checked', true);
                    } else {
                        $('input[name="answer"]').val(prevAnswer);
                    }
                }
                startTimer();
            } else {
                $questionContainer.html(`<p>Quiz completed! Your score is: ${score}</p>`);
                $('#next-question').hide();
                $('#timer-container').hide();
            }
        }).fail(function (jqXHR, textStatus, errorThrown) {
            $('#question-container').html(`<p>Error loading question: ${textStatus}</p>`);
        });
    }

    $('#next-question').on('click', function () {
        let answer;
        if ($('input[type="radio"]').length > 0) {
            answer = $('input[name="answer"]:checked').val();
            if (!answer) {
                alert('Please select an answer before proceeding.');
                return;
            }
        } else {
            answer = $('input[name="answer"]').val().trim();
            if (!answer) {
                alert('Please enter your answer before proceeding.');
                return;
            }
        }
        submitAnswer(answer);
    });

    $('#prev-question').on('click', function () {
        if (currentQuestionIndex > 0) {
            currentQuestionIndex--;
            loadQuestion();
        }
    });

    function submitAnswer(selectedAnswer) {
        stopTimer();

        // Store answer in the answers array
        answers[currentQuestionIndex] = selectedAnswer;

        $.ajax({
            url: '/submit_answer',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ questionIndex: currentQuestionIndex, answer: selectedAnswer }),
            success: function (data) {
                if (data.completed) {
                    $('#question-container').html(`
                        <div class="result">
                            <p>Quiz completed! Your score is: ${data.score}</p>
                            <canvas id="resultChart" width="400" height="200" style="margin-top: 20px;"></canvas>
                            <div class="button-group" style="margin-top: 20px; display: flex; justify-content: center; gap: 15px;">
                                <a href="/create_quiz" class="btn">Redo</a>
                                <a href="/" class="btn">Home</a>
                                <a href="/dashboard" class="btn">Quiz Dashboard</a>
                            </div>
                        </div>
                    `);
                    $('#timer-container').hide();
                    $('#prev-question').hide();
                    $('#next-question').hide();
                    $('#pause-resume-btn').hide();
                    $('#exit-quiz-btn').hide();
                } else {
                    currentQuestionIndex++;
                    loadQuestion();
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert('Error submitting answer: ' + textStatus);
            }
        });
    }

    loadQuestion();
});


