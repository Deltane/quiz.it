let answers = [];
$(document).ready(function () {
    // Add pause state
    let isPaused = false;
    // Get the total quiz time from a data attribute, fallback to 5 minutes (300s)
    const totalQuizTime = parseInt($('#timer-container').data('total-time')) || 300; // fallback: 5 minutes
    let remainingTime = totalQuizTime;
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
        const $timerDisplay = $('#countdown-timer');
        const totalDuration = totalQuizTime;

        let warned60 = false, warned30 = false, warned10 = false;

        $timerProgress.css('width', '100%');
        $timerDisplay.text(formatTime(remainingTime));

        timerInterval = setInterval(() => {
            if (!isPaused) {
                remainingTime--;
                $timerDisplay.text(formatTime(remainingTime));
                const progressPercent = (remainingTime / totalQuizTime) * 100;
                $timerProgress.css('width', `${progressPercent}%`);

                if (remainingTime === 60 && !warned60) {
                    $timerProgress.removeClass().addClass('warning-1min');
                    alert('⚠️ You have 1 minute left!');
                    warned60 = true;
                } else if (remainingTime === 30 && !warned30) {
                    $timerProgress.removeClass().addClass('warning-30s');
                    alert('⚠️ Only 30 seconds remaining!');
                    warned30 = true;
                } else if (remainingTime === 10 && !warned10) {
                    $timerProgress.removeClass().addClass('warning-10s');
                    alert('⏰ 10 seconds left!');
                    warned10 = true;
                }

                if (remainingTime <= 0) {
                    clearInterval(timerInterval);
                    submitAnswer(null);
                }
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

        // Store answer in the answers array
        answers[currentQuestionIndex] = selectedAnswer;

        $.ajax({
            url: '/submit_answer',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ questionIndex: currentQuestionIndex, answer: selectedAnswer }),
            success: function (data) {
                if (data.completed) {
                    stopTimer();
                    $('#timer-container').hide();
                    $('#countdown-timer').hide();
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

    // Pause/resume button logic
    $('#pause-resume-btn').on('click', function () {
        isPaused = !isPaused;
        if (isPaused) {
            $(this).text('Resume');
            $('#pause-message').show();
            $('input[name="answer"]').prop('disabled', true);
            $('#next-question').prop('disabled', true);
            $('#prev-question').prop('disabled', true);
        } else {
            $(this).text('Pause');
            $('#pause-message').hide();
            $('input[name="answer"]').prop('disabled', false);
            $('#next-question').prop('disabled', false);
            $('#prev-question').prop('disabled', false);
        }
    });

    loadQuestion();
    startTimer();
});
