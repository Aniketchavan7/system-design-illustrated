/**
 * System Design Illustrated - Interactive Flashcard Web App Engine
 * Zero dependencies, vanilla JS, fully responsive, keyboard accessible.
 */

(function () {
  'use strict';

  // 1. Data Initialization
  const rawCards = window.SYSTEM_DESIGN_FLASHCARDS || [];
  let cards = [...rawCards];
  let filteredCards = [...cards];
  let currentIndex = 0;
  let isFlipped = false;
  let isShuffled = false;

  // Review status storage
  const STORAGE_KEY = 'sys_design_flashcards_state_v1';
  let cardStates = {};
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) cardStates = JSON.parse(saved);
  } catch (e) {
    console.warn('LocalStorage unavailable:', e);
  }

  // Active Filters
  let activeCategory = 'all';
  let activeStatus = 'all';
  let searchQuery = '';

  // DOM Elements
  const dom = {
    card: document.getElementById('flashcard'),
    cardContainer: document.getElementById('flashcard-container'),
    cardNum: document.getElementById('card-number'),
    cardCategory: document.getElementById('card-category'),
    cardStatus: document.getElementById('card-status'),
    cardTitleFront: document.getElementById('card-title-front'),
    cardTitleBack: document.getElementById('card-title-back'),
    cardEli5: document.getElementById('card-eli5'),
    cardAnalogy: document.getElementById('card-analogy'),
    cardNumbers: document.getElementById('card-numbers'),
    primaryCaseLabel: document.getElementById('primary-case-label'),
    secondaryCaseLabel: document.getElementById('secondary-case-label'),
    googleDesc: document.getElementById('google-desc'),
    netflixDesc: document.getElementById('netflix-desc'),
    interviewQ: document.getElementById('interview-q'),
    interviewA: document.getElementById('interview-a'),
    linkReadme: document.getElementById('link-readme'),
    linkExamples: document.getElementById('link-examples'),
    linkDemo: document.getElementById('link-demo'),
    linkReadmeBack: document.getElementById('link-readme-back'),
    linkExamplesBack: document.getElementById('link-examples-back'),
    linkDemoBack: document.getElementById('link-demo-back'),
    
    // Progress
    progressText: document.getElementById('progress-text'),
    progressPercentage: document.getElementById('progress-percentage'),
    progressFill: document.getElementById('progress-fill'),

    // Controls
    btnPrev: document.getElementById('btn-prev'),
    btnNext: document.getElementById('btn-next'),
    btnFlip: document.getElementById('btn-flip'),
    btnMaster: document.getElementById('btn-master'),
    btnReview: document.getElementById('btn-review'),
    btnShuffle: document.getElementById('btn-shuffle'),
    btnReset: document.getElementById('btn-reset'),
    searchInput: document.getElementById('search-input'),
    categoryChips: document.getElementById('category-chips'),
    statusFilters: document.getElementById('status-filters')
  };

  // 2. Storage Helpers
  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cardStates));
    } catch (e) {}
    updateProgress();
  }

  function getCardStatus(cardId) {
    return cardStates[cardId] || 'unseen';
  }

  function setCardStatus(cardId, status) {
    cardStates[cardId] = status;
    saveState();
  }

  // 3. Filtering & Searching
  function applyFilters() {
    filteredCards = cards.filter(card => {
      // Category filter
      if (activeCategory !== 'all' && card.category_id !== activeCategory) {
        return false;
      }
      // Status filter
      const st = getCardStatus(card.id);
      if (activeStatus !== 'all' && st !== activeStatus) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const searchable = (
          card.title + ' ' + 
          card.eli5 + ' ' + 
          card.category + ' ' + 
          card.google_example + ' ' + 
          card.netflix_example + ' ' + 
          card.interview_question
        ).toLowerCase();
        if (!searchable.includes(q)) return false;
      }
      return true;
    });

    currentIndex = 0;
    isFlipped = false;
    renderCard();
    updateProgress();
  }

  // 4. Rendering
  function renderCard() {
    if (dom.card.classList.contains('flipped')) {
      dom.card.classList.remove('flipped');
      isFlipped = false;
    }

    if (filteredCards.length === 0) {
      dom.cardTitleFront.textContent = 'No matching cards found';
      dom.cardEli5.textContent = 'Try adjusting your search query or switching filters.';
      dom.cardAnalogy.textContent = 'Use the category pills or clear search to explore all 45 topics.';
      dom.cardNumbers.textContent = '0 / 0 Results';
      dom.cardNum.textContent = '--';
      dom.cardCategory.textContent = 'Empty';
      dom.cardStatus.textContent = 'No Match';
      dom.cardStatus.className = 'card-status-badge status-unseen';
      dom.btnPrev.disabled = true;
      dom.btnNext.disabled = true;
      dom.btnMaster.disabled = true;
      dom.btnReview.disabled = true;
      dom.btnFlip.disabled = true;
      return;
    }

    dom.btnPrev.disabled = (currentIndex === 0);
    dom.btnNext.disabled = (currentIndex === filteredCards.length - 1);
    dom.btnMaster.disabled = false;
    dom.btnReview.disabled = false;
    dom.btnFlip.disabled = false;

    const card = filteredCards[currentIndex];
    const status = getCardStatus(card.id);

    // Front Face
    dom.cardNum.textContent = `Module ${card.number}`;
    dom.cardCategory.textContent = card.category;
    dom.cardTitleFront.textContent = card.title;
    dom.cardTitleBack.textContent = card.title;
    dom.cardEli5.textContent = card.eli5;
    dom.cardAnalogy.textContent = card.analogy;
    dom.cardNumbers.textContent = card.key_numbers;

    // Status Badge
    dom.cardStatus.textContent = status === 'mastered' ? 'Mastered' : status === 'review' ? 'Review Later' : 'Unseen';
    dom.cardStatus.className = `card-status-badge status-${status}`;

    // Back Face
    dom.primaryCaseLabel.textContent = card.primary_case_label || 'Google';
    dom.secondaryCaseLabel.textContent = card.secondary_case_label || 'Netflix';
    dom.googleDesc.textContent = card.google_example || 'Employed in Google planetary datacenters.';
    dom.netflixDesc.textContent = card.netflix_example || 'Core component of Netflix global streaming architecture.';
    dom.interviewQ.textContent = card.interview_question || 'Interview Question';
    dom.interviewA.textContent = card.interview_answer || 'Detailed answer in module README.';

    // Deep Links
    const isFile = window.location.protocol === 'file:';
    const isDocs = window.location.pathname.replace(/\\/g, '/').toLowerCase().includes('/docs');
    const localBase = isDocs ? '../' : './';
    const repoBase = 'https://github.com/Aniketchavan7/system-design-illustrated/blob/main/';

    const readmeUrl = isFile ? `${localBase}${card.folder}/README.md` : `${repoBase}${card.folder}/README.md`;
    const examplesUrl = isFile ? `${localBase}${card.folder}/REAL_WORLD_EXAMPLES.md` : `${repoBase}${card.folder}/REAL_WORLD_EXAMPLES.md`;
    const demoUrl = isFile ? `${localBase}${card.folder}/demo.py` : `${repoBase}${card.folder}/demo.py`;

    dom.linkReadme.href = readmeUrl;
    dom.linkExamples.href = examplesUrl;
    dom.linkDemo.href = demoUrl;

    dom.linkReadmeBack.href = readmeUrl;
    dom.linkExamplesBack.href = examplesUrl;
    dom.linkDemoBack.href = demoUrl;

    // Counter
    dom.progressText.textContent = `Card ${currentIndex + 1} of ${filteredCards.length}`;
  }

  function flipCard() {
    if (filteredCards.length === 0) return;
    isFlipped = !isFlipped;
    dom.card.classList.toggle('flipped', isFlipped);
  }

  function nextCard() {
    if (currentIndex < filteredCards.length - 1) {
      currentIndex++;
      renderCard();
    }
  }

  function prevCard() {
    if (currentIndex > 0) {
      currentIndex--;
      renderCard();
    }
  }

  function markMastered() {
    if (filteredCards.length === 0) return;
    const card = filteredCards[currentIndex];
    setCardStatus(card.id, 'mastered');
    renderCard();
    // Auto-advance
    if (currentIndex < filteredCards.length - 1) {
      setTimeout(nextCard, 200);
    }
  }

  function markReview() {
    if (filteredCards.length === 0) return;
    const card = filteredCards[currentIndex];
    setCardStatus(card.id, 'review');
    renderCard();
    // Auto-advance
    if (currentIndex < filteredCards.length - 1) {
      setTimeout(nextCard, 200);
    }
  }

  function shuffleDeck() {
    isShuffled = !isShuffled;
    if (isShuffled) {
      for (let i = cards.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [cards[i], cards[j]] = [cards[j], cards[i]];
      }
      dom.btnShuffle.style.background = 'rgba(99, 102, 241, 0.3)';
      dom.btnShuffle.style.borderColor = 'var(--primary)';
    } else {
      cards = [...rawCards];
      dom.btnShuffle.style.background = '';
      dom.btnShuffle.style.borderColor = '';
    }
    applyFilters();
  }

  function resetProgress() {
    if (confirm('Are you sure you want to reset all mastery and review progress?')) {
      cardStates = {};
      saveState();
      renderCard();
    }
  }

  function updateProgress() {
    const total = cards.length;
    let masteredCount = 0;
    let reviewCount = 0;

    cards.forEach(c => {
      const s = getCardStatus(c.id);
      if (s === 'mastered') masteredCount++;
      else if (s === 'review') reviewCount++;
    });

    const percent = Math.round((masteredCount / total) * 100);
    dom.progressPercentage.textContent = `${masteredCount}/${total} Mastered (${percent}%)`;
    dom.progressFill.style.width = `${percent}%`;
  }

  // 5. Event Listeners
  dom.cardContainer.addEventListener('click', (e) => {
    // Avoid flipping when clicking on actual outbound links
    if (e.target.closest('a')) return;
    flipCard();
  });

  dom.btnFlip.addEventListener('click', (e) => {
    e.stopPropagation();
    flipCard();
  });

  dom.btnNext.addEventListener('click', (e) => {
    e.stopPropagation();
    nextCard();
  });

  dom.btnPrev.addEventListener('click', (e) => {
    e.stopPropagation();
    prevCard();
  });

  dom.btnMaster.addEventListener('click', (e) => {
    e.stopPropagation();
    markMastered();
  });

  dom.btnReview.addEventListener('click', (e) => {
    e.stopPropagation();
    markReview();
  });

  dom.btnShuffle.addEventListener('click', shuffleDeck);
  dom.btnReset.addEventListener('click', resetProgress);

  dom.searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value;
    applyFilters();
  });

  // Category filter chips
  dom.categoryChips.addEventListener('click', (e) => {
    const chip = e.target.closest('.category-chip');
    if (!chip) return;
    dom.categoryChips.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeCategory = chip.dataset.cat;
    applyFilters();
  });

  // Status filters
  dom.statusFilters.addEventListener('click', (e) => {
    const pill = e.target.closest('.status-pill');
    if (!pill) return;
    dom.statusFilters.querySelectorAll('.status-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeStatus = pill.dataset.status;
    applyFilters();
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    // Ignore keystrokes when typing in search input
    if (document.activeElement === dom.searchInput) return;

    if (e.code === 'Space' || e.code === 'ArrowUp' || e.code === 'ArrowDown') {
      e.preventDefault();
      flipCard();
    } else if (e.code === 'ArrowRight') {
      e.preventDefault();
      nextCard();
    } else if (e.code === 'ArrowLeft') {
      e.preventDefault();
      prevCard();
    } else if (e.code === 'Digit1' || e.code === 'KeyM') {
      e.preventDefault();
      markMastered();
    } else if (e.code === 'Digit2' || e.code === 'KeyR') {
      e.preventDefault();
      markReview();
    } else if (e.code === 'KeyS') {
      e.preventDefault();
      shuffleDeck();
    }
  });

  // Touch swipe support for mobile
  let touchStartX = 0;
  let touchEndX = 0;

  dom.cardContainer.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });

  dom.cardContainer.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  }, { passive: true });

  function handleSwipe() {
    const diff = touchEndX - touchStartX;
    if (Math.abs(diff) > 50) {
      if (diff < 0) nextCard();
      else prevCard();
    }
  }

  // Set header link destinations for web vs local
  const isFileProto = window.location.protocol === 'file:';
  const isDocsDir = window.location.pathname.replace(/\\/g, '/').toLowerCase().includes('/docs');
  const guideLink = document.getElementById('link-study-guide');
  if (isFileProto) {
    guideLink.href = isDocsDir ? '../STUDY_GUIDE.md' : './STUDY_GUIDE.md';
  }
  const csEl = document.getElementById('link-cheatsheet');
  const fcEl = document.getElementById('link-flowcharts');
  if (csEl) {
    csEl.href = isFileProto ? (isDocsDir ? '../CHEATSHEET.md' : './CHEATSHEET.md') : 'https://github.com/Aniketchavan7/system-design-illustrated/blob/main/CHEATSHEET.md';
  }
  if (fcEl) {
    fcEl.href = isFileProto ? (isDocsDir ? '../DECISION_FLOWCHARTS.md' : './DECISION_FLOWCHARTS.md') : 'https://github.com/Aniketchavan7/system-design-illustrated/blob/main/DECISION_FLOWCHARTS.md';
  }

  // Initial Run
  applyFilters();
})();
