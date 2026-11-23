(() => {
  "use strict";

  const form = document.querySelector("[data-capstone]");
  const actions = document.querySelector("[data-capstone-actions]");
  const result = document.querySelector("[data-capstone-result]");
  const questions = [...form.querySelectorAll("[data-question]")];
  let scored = false;

  function clearFeedback() {
    if (!scored) return;
    for (const question of questions) {
      question.querySelector("[data-feedback]").hidden = true;
      question.querySelector("details").open = false;
    }
    result.hidden = true;
    scored = false;
  }

  for (const question of questions) question.querySelector("fieldset").disabled = false;
  actions.hidden = false;

  form.addEventListener("submit", event => {
    event.preventDefault();
    const answers = new FormData(form);
    let correct = 0;
    for (const question of questions) {
      const matches = answers.get(question.dataset.question) === question.dataset.correct;
      const feedback = question.querySelector("[data-feedback]");
      feedback.textContent = matches ? "Correct" : "Review this question";
      feedback.dataset.outcome = matches ? "correct" : "review";
      feedback.hidden = false;
      question.querySelector("details").open = true;
      if (matches) correct += 1;
    }
    result.textContent = `${correct} of ${questions.length} correct. Read the explanations above to review your choices.`;
    result.hidden = false;
    result.focus();
    scored = true;
  });

  form.addEventListener("change", clearFeedback);
  form.addEventListener("reset", () => {
    clearFeedback();
    questions[0].querySelector("input").focus();
  });
})();
