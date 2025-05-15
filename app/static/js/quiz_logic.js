let answers = [];
let questionTimestamps = [];

$(document).ready(function () {
    // Remove any localStorage keys containing "None"
    Object.keys(localStorage).forEach(key => {
        if (key.includes("None")) {
            localStorage.removeItem(key);
        }
    });
    // Initialize unique quiz session ID if not already set
    if (!sessionStorage.getItem("quiz_session_id")) {
        const timestamp = Date.now();
        sessionStorage.setItem("quiz_session_id", `session_${timestamp}`);
    }
    // Ensure quiz_id is set early
    if (!sessionStorage.getItem("quiz_id")) {
        const quizIdMatch = window.location.href.match(/take_quiz\/(\d+)/);
        const quizId = quizIdMatch ? quizIdMatch[1] : "default";
        sessionStorage.setItem("quiz_id", quizId);
    }
    // Ensure attempt_id is set early and stored consistently
    const quizId = sessionStorage.getItem("quiz_id") || "default";
    const attemptIndexKey = `quiz_attempt_index_${quizId}`;
    let attemptIds = JSON.parse(localStorage.getItem(attemptIndexKey) || "[]");

    // Validate and assign attemptId early
    if (!sessionStorage.getItem("attempt_id")) {
        const newAttemptId = attemptIds.length + 1;
        sessionStorage.setItem("attempt_id", newAttemptId);

        // Add to attempt index immediately to lock it in
        if (!attemptIds.includes(newAttemptId)) {
            attemptIds.push(newAttemptId);
            localStorage.setItem(attemptIndexKey, JSON.stringify(attemptIds));
        }
    }
    // Add pause state
    let isPaused = false;
    // Get the full quiz time and remaining time from data attributes, fallback to 5 minutes (300s)
    const fullQuizTime = parseInt($('#timer-container').data('full-time')) || 300;
    let remainingTime = parseInt($('#timer-container').data('total-time')) || fullQuizTime;
    let currentQuestionIndex = typeof INITIAL_QUESTION_INDEX !== 'undefined' ? INITIAL_QUESTION_INDEX : 0;
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
        const totalDuration = fullQuizTime;

        let warned60 = false, warned30 = false, warned10 = false;

        const initialProgress = (remainingTime / totalDuration) * 100;
        $timerProgress.css('width', `${initialProgress}%`);
        $timerDisplay.text(formatTime(remainingTime));

        timerInterval = setInterval(() => {
            if (!isPaused) {
                remainingTime--;
                $timerDisplay.text(formatTime(remainingTime));
                const progressPercent = (remainingTime / totalDuration) * 100;
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

                const quizId = sessionStorage.getItem("quiz_id") || "default";
                const attemptId = sessionStorage.getItem("attempt_id") || Date.now();
                const currentQuizKey = `current_quiz_${quizId}_${attemptId}`;
                let quizData = JSON.parse(localStorage.getItem(currentQuizKey) || "[]");
                quizData[currentQuestionIndex] = {
                    question: data.question,
                    answer: data.answer,
                    options: data.options || [],
                    type: data.type || 'text'
                };
                localStorage.setItem(currentQuizKey, JSON.stringify(quizData));

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
        // Add timestamp for this answer
        questionTimestamps.push(Date.now());
        // Store answer in the answers array
        answers[currentQuestionIndex] = selectedAnswer;

        // Strictly get quizId and attemptId from sessionStorage, enforce presence
        const quizId = parseInt(sessionStorage.getItem("quiz_id"));
        const attemptId = parseInt(sessionStorage.getItem("attempt_id"));
        console.log("SUBMITTING: quizId =", quizId, "attemptId =", attemptId);
        // Fallback safety net
        if (!quizId || !attemptId) {
            alert("Error: quizId or attemptId is missing from sessionStorage.");
            return;
        }

        $.ajax({
            url: '/submit_answer',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ questionIndex: currentQuestionIndex, answer: selectedAnswer }),
            success: function (data) {
                if (data.completed) {
                    // Use strictly correct quizId and attemptId
                    const durationsKey = `quiz_durations_${quizId}_${attemptId}`;
                    const reviewKey = `quiz_review_${quizId}_${attemptId}`;
                    const scoresKey = `quiz_attempts_${quizId}_${attemptId}`;
                    const attemptIndexKey = `quiz_attempt_index_${quizId}`;

                    // Save current attemptId to the quiz's attempt index
                    let attemptIndex = JSON.parse(localStorage.getItem(attemptIndexKey) || "[]");
                    if (!attemptIndex.includes(attemptId)) {
                        attemptIndex.push(attemptId);
                        localStorage.setItem(attemptIndexKey, JSON.stringify(attemptIndex));
                    }

                    stopTimer();
                    $('#timer-container').hide();

                    // Save durations
                    questionTimestamps.push(Date.now());  // Add end timestamp for final question

                    // Remove all previous quiz_durations keys for this quizId except current attempt
                    Object.keys(localStorage).forEach((key) => {
                        if (key.startsWith(`quiz_durations_${quizId}_`) && key !== durationsKey) {
                            localStorage.removeItem(key);
                        }
                    });
                    const durations = [];
                    for (let i = 1; i < questionTimestamps.length; i++) {
                        durations.push((questionTimestamps[i] - questionTimestamps[i - 1]) / 1000);
                    }
                    localStorage.removeItem(durationsKey);
                    localStorage.setItem(durationsKey, JSON.stringify(durations));

                    // Always overwrite with latest score (one entry only per attempt)
                    localStorage.setItem(scoresKey, JSON.stringify([data.score]));

                    // Clean up any duplicated or incorrect score keys
                    Object.keys(localStorage).forEach(key => {
                        if (
                            key.startsWith(`quiz_attempts_${quizId}_`) &&
                            key !== scoresKey &&
                            key !== `quiz_attempts_${quizId}_1` &&
                            key !== `quiz_attempts_${quizId}_2` &&
                            key !== `quiz_attempts_${quizId}_${attemptId}`
                        ) {
                            localStorage.removeItem(key);
                        }
                    });

                    // Save latest keys
                    localStorage.setItem("latest_quiz_durations_key", durationsKey);
                    localStorage.setItem("latest_quiz_review_key", reviewKey);
                    localStorage.setItem("latest_quiz_attempts_key", scoresKey);

                    // Save quiz review data from local copy with logging and guard
                    const currentQuizKey = `current_quiz_${quizId}_${attemptId}`;
                    const quizData = JSON.parse(localStorage.getItem(currentQuizKey) || "[]");
                    localStorage.removeItem("current_quiz"); // clear any legacy data
                    console.log("Generating quiz review...");
                    console.log("Quiz Data:", quizData);
                    console.log("Answers:", answers);

                    // Remove all previous quiz_review keys for this quizId except current attempt
                    Object.keys(localStorage).forEach((key) => {
                        if (key.startsWith(`quiz_review_${quizId}_`) && key !== reviewKey) {
                            localStorage.removeItem(key);
                        }
                    });

                    let quizReview = [];

                    if (quizData.length === answers.length) {
                        quizReview = quizData.map((q, i) => {
                            const userAnswer = answers[i] || "";
                            const correctAnswer = q.answer || "";
                            return {
                                question: q.question,
                                userAnswer: userAnswer,
                                correctAnswer: correctAnswer,
                                isCorrect: userAnswer.trim().toLowerCase() === correctAnswer.trim().toLowerCase()
                            };
                        });
                    } else {
                        console.warn("Mismatch in quizData and answers length. Skipping review.");
                    }

                    localStorage.removeItem(reviewKey);
                    localStorage.setItem(reviewKey, JSON.stringify(quizReview));

                    // Then show result after storing review
                    const redirectURL = data.redirect_url || '/';
                    $('#question-container').html(`
                        <div class="result">
                            <p><b>Quiz completed! Your score is: ${data.score}</b></p>
                            <div class="button-group" style="margin-top: 20px; display: flex; justify-content: center; gap: 15px;">
                                <a href="/create_quiz" class="btn">Redo</a>
                                <a href="/" class="btn">Home</a>
                                <a href="/dashboard" class="btn">Quiz Dashboard</a>
                                <a href="${redirectURL}" class="btn">Quiz Summary</a>
                            </div>
                        </div>
                    `);

                    $('#countdown-timer').hide();
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

    // Exit quiz button logic
    $('#exit-quiz-btn').on('click', function () {
        const confirmExit = confirm("Are you sure you want to exit the quiz? Your progress will be saved and you can resume it later.");
        if (confirmExit) {
            $('#time_left_input').val(remainingTime);
            $('#exit-form').submit();
        }
    });
});
