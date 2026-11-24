/**
 * System Design Illustrated - Interactive Flashcard Web App Engine
 * Zero dependencies, vanilla JS, fully responsive, keyboard accessible,
 * monochrome editorial design with rich reading typography.
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

  // Review status and theme storage
  const STORAGE_KEY = 'sys_design_flashcards_state_v1';
  const THEME_KEY = 'sys_design_flashcards_theme_v1';
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
    btnTheme: document.getElementById('btn-theme'),
    searchInput: document.getElementById('search-input'),
    categoryChips: document.getElementById('category-chips'),
    statusFilters: document.getElementById('status-filters')
  };

  // 2. Markdown Typesetting Helper (handles headings, mixed lists, inline code, links, emphasis)
  function formatInline(text) {
    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    escaped = escaped.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener" class="inline-link">$1</a>'
    );
    return escaped;
  }

  function formatMarkdown(text) {
    if (!text) return '';
    const lines = text.split('\n');
    const out = [];
    let listType = null;
    let listItems = [];
    let paraLines = [];

    function flushList() {
      if (listType && listItems.length > 0) {
        const tag = listType;
        out.push(`<${tag}>${listItems.map(item => `<li>${formatInline(item)}</li>`).join('')}</${tag}>`);
      }
      listType = null;
      listItems = [];
    }

    function flushPara() {
      if (paraLines.length > 0) {
        out.push(`<p>${paraLines.map(formatInline).join('<br>')}</p>`);
        paraLines = [];
      }
    }

    for (const raw of lines) {
      const trimmed = raw.trim();
      if (!trimmed) {
        flushList();
        flushPara();
        continue;
      }

      const headingMatch = trimmed.match(/^#{2,4}\s+(.+)$/);
      if (headingMatch) {
        flushList();
        flushPara();
        out.push(`<h4 class="card-subheading">${formatInline(headingMatch[1])}</h4>`);
        continue;
      }

      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        flushPara();
        if (listType !== 'ul') {
          flushList();
          listType = 'ul';
        }
        listItems.push(trimmed.substring(2).trim());
        continue;
      }

      const numMatch = trimmed.match(/^\d+\.\s+(.+)$/);
      if (numMatch) {
        flushPara();
        if (listType !== 'ol') {
          flushList();
          listType = 'ol';
        }
        listItems.push(numMatch[1].trim());
        continue;
      }

      flushList();
      paraLines.push(trimmed);
    }

    flushList();
    flushPara();
    return out.join('');
  }

  // 3. Storage & Theme Helpers
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

  function applyTheme(theme) {
    if (theme === 'paper') {
      document.documentElement.setAttribute('data-theme', 'paper');
      if (dom.btnTheme) dom.btnTheme.textContent = 'Obsidian Theme';
    } else {
      document.documentElement.removeAttribute('data-theme');
      if (dom.btnTheme) dom.btnTheme.textContent = 'Paper Theme';
    }
  }

  function toggleTheme() {
    const next = document.documentElement.getAttribute('data-theme') === 'paper' ? 'obsidian' : 'paper';
    applyTheme(next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch (e) {}
  }

  function updateCategoryCounts() {
    if (!dom.categoryChips) return;
    const counts = {};
    for (const card of rawCards) {
      counts[card.category_id] = (counts[card.category_id] || 0) + 1;
    }
    dom.categoryChips.querySelectorAll('.category-chip').forEach(chip => {
      const cat = chip.dataset.cat;
      const badge = chip.querySelector('.chip-count');
      if (!badge) return;
      badge.textContent = cat === 'all' ? rawCards.length : (counts[cat] || 0);
    });
  }

  // 4. Environment & Site Path Resolution
  const isFileProto = window.location.protocol === 'file:';
  const pathname = window.location.pathname.replace(/\\/g, '/').toLowerCase();
  const isDocsFile = pathname.includes('/docs/') || pathname.endsWith('/flashcards.html');
  const isGitHubPages = !isFileProto && window.location.hostname.endsWith('.github.io');
  const inDocsSite = isDocsFile || isGitHubPages;
  const coursePrefix = inDocsSite ? './' : './docs/';
  const repoBase = 'https://github.com/Aniketchavan7/system-design-illustrated/blob/main/';

  // 5. Filtering & Searching
  function applyFilters() {
    filteredCards = cards.filter(card => {
      if (activeCategory !== 'all' && card.category_id !== activeCategory) {
        return false;
      }
      const st = getCardStatus(card.id);
      if (activeStatus !== 'all' && st !== activeStatus) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const searchable = (
          card.title + ' ' +
          card.eli5 + ' ' +
          card.analogy + ' ' +
          card.category + ' ' +
          card.google_example + ' ' +
          card.netflix_example + ' ' +
          card.interview_question + ' ' +
          card.interview_answer
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

  // 6. Rendering
  function renderCard() {
    if (dom.card.classList.contains('flipped')) {
      dom.card.classList.remove('flipped');
      isFlipped = false;
    }

    if (filteredCards.length === 0) {
      dom.cardTitleFront.textContent = 'No matching cards found';
      dom.cardEli5.innerHTML = '<p>Try adjusting your search query or switching filters to view all 45 system design modules.</p>';
      dom.cardAnalogy.innerHTML = '<p>Use the category chips above or clear the search input to reset the deck.</p>';
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
    dom.cardEli5.innerHTML = formatMarkdown(card.eli5);
    dom.cardAnalogy.innerHTML = formatMarkdown(card.analogy);
    dom.cardNumbers.textContent = card.key_numbers;

    // Status Badge
    dom.cardStatus.textContent = status === 'mastered' ? '✓ Mastered' : status === 'review' ? 'Review Later' : 'Unseen';
    dom.cardStatus.className = `card-status-badge status-${status}`;

    // Back Face
    dom.primaryCaseLabel.textContent = card.primary_case_label || 'Primary Case Study';
    dom.secondaryCaseLabel.textContent = card.secondary_case_label || 'Secondary Case Study';
    dom.googleDesc.innerHTML = formatMarkdown(card.google_example);
    dom.netflixDesc.innerHTML = formatMarkdown(card.netflix_example);
    dom.interviewQ.textContent = card.interview_question;
    dom.interviewA.innerHTML = formatMarkdown(card.interview_answer);

    // Deep Links: stay inside local rendered chapters when available, fallback smoothly
    const readmeUrl = (inDocsSite || !isFileProto)
      ? `${coursePrefix}chapters/${card.folder}/index.html`
      : `./${card.folder}/README.md`;
    const examplesUrl = (inDocsSite || !isFileProto)
      ? `${coursePrefix}chapters/${card.folder}/examples.html`
      : `./${card.folder}/REAL_WORLD_EXAMPLES.md`;
    const demoUrl = isFileProto
      ? `${isDocsFile ? '../' : './'}${card.folder}/demo.py`
      : `${repoBase}${card.folder}/demo.py`;

    dom.linkReadme.href = readmeUrl;
    dom.linkExamples.href = examplesUrl;
    dom.linkDemo.href = demoUrl;

    dom.linkReadmeBack.href = readmeUrl;
    dom.linkExamplesBack.href = examplesUrl;
    dom.linkDemoBack.href = demoUrl;

    if (inDocsSite || !isFileProto) {
      dom.linkReadme.removeAttribute('target');
      dom.linkExamples.removeAttribute('target');
      dom.linkReadmeBack.removeAttribute('target');
      dom.linkExamplesBack.removeAttribute('target');
    }

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
    if (currentIndex < filteredCards.length - 1) {
      setTimeout(nextCard, 200);
    }
  }

  function markReview() {
    if (filteredCards.length === 0) return;
    const card = filteredCards[currentIndex];
    setCardStatus(card.id, 'review');
    renderCard();
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
      dom.btnShuffle.style.background = 'var(--ink-primary)';
      dom.btnShuffle.style.color = 'var(--ink-inverse)';
      dom.btnShuffle.style.borderColor = 'var(--ink-primary)';
    } else {
      cards = [...rawCards];
      dom.btnShuffle.style.background = '';
      dom.btnShuffle.style.color = '';
      dom.btnShuffle.style.borderColor = '';
    }
    applyFilters();
  }

  function resetProgress() {
    if (confirm('Reset all mastery and review progress?')) {
      cardStates = {};
      saveState();
      renderCard();
    }
  }

  function updateProgress() {
    const total = cards.length;
    let masteredCount = 0;

    cards.forEach(c => {
      if (getCardStatus(c.id) === 'mastered') masteredCount++;
    });

    const percent = total ? Math.round((masteredCount / total) * 100) : 0;
    dom.progressPercentage.textContent = `${masteredCount}/${total} Mastered (${percent}%)`;
    dom.progressFill.style.width = `${percent}%`;
  }

  // 7. Event Listeners
  dom.cardContainer.addEventListener('click', (e) => {
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
  if (dom.btnTheme) dom.btnTheme.addEventListener('click', toggleTheme);

  dom.searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value;
    applyFilters();
  });

  dom.categoryChips.addEventListener('click', (e) => {
    const chip = e.target.closest('.category-chip');
    if (!chip) return;
    dom.categoryChips.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeCategory = chip.dataset.cat;
    applyFilters();
  });

  dom.statusFilters.addEventListener('click', (e) => {
    const pill = e.target.closest('.status-pill');
    if (!pill) return;
    dom.statusFilters.querySelectorAll('.status-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeStatus = pill.dataset.status;
    applyFilters();
  });

  document.addEventListener('keydown', (e) => {
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
    } else if (e.key === '/') {
      e.preventDefault();
      dom.searchInput.focus();
    }
  });

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

  // Set header link destinations across GitHub Pages, local HTTP, and file://
  const guideLink = document.getElementById('link-study-guide');
  const csEl = document.getElementById('link-cheatsheet');
  const fcEl = document.getElementById('link-flowcharts');
  const contribEl = document.getElementById('link-contribute');
  const redditEl = document.getElementById('link-reddit');
  const courseLink = document.getElementById('link-course');
  const libLink = document.getElementById('link-library');

  const mdRoot = isDocsFile ? '../' : './';
  if (inDocsSite || !isFileProto) {
    if (guideLink) guideLink.href = `${coursePrefix}guides/study-guide.html`;
    if (csEl) csEl.href = `${coursePrefix}guides/cheatsheet.html`;
    if (fcEl) fcEl.href = `${coursePrefix}guides/decision-flowcharts.html`;
    if (contribEl) contribEl.href = `${coursePrefix}guides/contributing.html`;
  } else {
    if (guideLink) guideLink.href = `${mdRoot}STUDY_GUIDE.md`;
    if (csEl) csEl.href = `${mdRoot}CHEATSHEET.md`;
    if (fcEl) fcEl.href = `${mdRoot}DECISION_FLOWCHARTS.md`;
    if (contribEl) contribEl.href = `${mdRoot}CONTRIBUTING.md`;
  }
  if (courseLink) courseLink.href = `${coursePrefix}index.html`.replace('./index.html', './');
  if (libLink) libLink.href = `${coursePrefix}library.html`;
  if (redditEl) redditEl.href = 'https://www.reddit.com/r/systemdesign/';

  // Initial Run
  try {
    applyTheme(localStorage.getItem(THEME_KEY) || 'obsidian');
  } catch (e) {
    applyTheme('obsidian');
  }
  updateCategoryCounts();
  applyFilters();
})();
