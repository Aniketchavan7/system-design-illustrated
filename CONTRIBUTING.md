# Contributing to System Design Illustrated 🤝

> **"This is an open source project for everyone. We learn together, build together, and accept mistakes together. Whether you're fixing a typo, updating a latency figure, or sharing your company's production architecture—your knowledge belongs here."**

First off, thank you for considering contributing to **System Design Illustrated**! 

System design is not a static, dogmatic textbook. Real-world distributed systems are messy, evolving, and full of subtle tradeoffs. No single person knows everything about how planetary systems are built. This project thrives because engineers, students, and practitioners from around the world share their knowledge, catch mistakes, and develop it collaboratively.

---

## 🌟 Our Guiding Principles

1. **Mistakes are Welcomed & Expected**: Found a technical inaccuracy, an outdated latency number, a broken link, or a confusing explanation? Please tell us or submit a fix! Nobody writes bug-free documentation or flawless architectures on their first pass. We treat every bug report and correction as an act of generosity.
2. **Share Your Own Knowledge**: Have you worked on high-scale systems at your job or in an open source project? Have you debugged a cascading failure or a subtle race condition? Your real-world war stories and architectural dissections are pure gold for someone preparing for an interview or building their first production system.
3. **No Contribution Is Too Small**: Fixing a comma, correcting an equation, improving a diagram, adding a comment to a Python simulation, or suggesting a clearer analogy is just as valuable as writing a brand-new 5,000-word case study.
4. **Clarity Over Jargon**: We explain things from first principles using everyday physical analogies, visual diagrams, and real numbers before diving into kernel internals. If an explanation feels like "academic soup", help us simplify it!

---

## 🧭 Ways You Can Contribute

There are many ways to contribute to the project:

### 1. 🐛 Fix Mistakes & Inaccuracies
- Fix typos, grammatical errors, or awkward phrasing.
- Correct outdated hardware numbers (e.g., modern NVMe SSD vs. HDD latency).
- Clarify misleading or incomplete distributed systems explanations (e.g., nuances in Paxos vs. Raft, CAP theorem subtleties, ACID vs. BASE).
- Fix broken markdown links or table formatting.

### 2. 🏢 Share Real-World Production Knowledge
- Add a **Real-World Production Deep Dive** to any module's `REAL_WORLD_EXAMPLES.md`:
  - How did your company (or a company you admire like Stripe, Uber, Netflix, Shopify, Discord, Cloudflare) solve rate limiting, feed generation, distributed locks, or database sharding?
  - What were the post-mortem lessons and failure modes?
- Add new architectural decision tradeoffs to `DECISION_FLOWCHARTS.md`.

### 3. 🎨 Visuals & Architectural Diagrams
- Add or improve ASCII, SVG, or Mermaid diagrams in any module.
- Create step-by-step visual request flows (e.g., DNS resolution, 2PC transaction flow, consistent hashing ring rebalance).

### 4. 🧮 Back-of-the-Envelope Math & Cheat Sheets
- Expand `CHEATSHEET.md` with new rules of thumb, SLA conversions, and capacity formulas.
- Add new presets or formulas to `calculate.py` (the interactive CLI estimation calculator).

### 5. 🧠 Interactive Flashcards & Interview Q&A
- Contribute new high-yield interview questions and senior-level answers to `README.md` and `cards-data.js`.
- Improve the ELI5 explanations or physical analogies on the flashcards.

### 6. 💻 Runnable Python Simulations & Labs
- Improve existing `demo.py` scripts to make simulations clearer or more interactive.
- Contribute new hands-on labs in `labs/` (e.g., simulating a distributed lock with Redis lease TTLs, an event-driven saga orchestrator, or a token bucket rate limiter).

### 7. 🌐 Translations & Accessibility
- Help translate modules or flashcards to other languages so developers worldwide can learn system design in their native tongue.

### 8. 💬 Discuss Ideas & Share Feedback on Reddit
- Before opening a large PR or proposing an extensive new module, feel free to bounce ideas off the community in **[r/systemdesign](https://www.reddit.com/r/systemdesign/)** or other subreddits.
- See our **[Community & Reddit Guide](./COMMUNITY.md)** for discussion prompts, post templates, and how community feedback gets turned into repository updates.

---

## 🛠️ Step-by-Step Contribution Workflow

We use the standard GitHub fork-and-pull-request model:

### Step 1: Fork and Clone the Repository
```bash
# 1. Fork the repo on GitHub via the 'Fork' button
# 2. Clone your personal fork locally
git clone https://github.com/<your-username>/system-design-illustrated.git
cd system-design-illustrated

# 3. Add upstream remote to stay synchronized with main
git remote add upstream https://github.com/Aniketchavan7/system-design-illustrated.git
```

### Step 2: Create a Feature Branch
Create a descriptive branch for your work:
```bash
git checkout -b fix/module-05-rate-limiting-typo
# or
git checkout -b feat/add-shopify-flash-sale-case-study
```

### Step 3: Make Your Changes
- Follow the existing module structure (see [TEMPLATE.md](./TEMPLATE.md) for module conventions).
- Keep language direct, clear, and non-dogmatic.
- If you're adding or editing flashcard data, remember that `cards-data.js` and `docs/cards-data.js` should remain in sync (or run `python build_rich_flashcards.py`).

### Step 4: Run the Test Suite Locally
Before submitting a PR, verify that all automated checks and links pass:
```bash
# Run the test suite via the CLI runner:
python run_tests.py

# Or run pytest directly:
pytest tests/
```
All 105+ tests (including relative link validity, demo execution, calculator presets, and flashcard data integrity) should pass with 0 errors.

### Step 5: Commit and Push
Write a clear, concise commit message following conventional commits format:
```bash
git add .
git commit -m "fix(05-rate-limiting): correct token bucket refill math"
git push origin feat/your-feature-name
```

### Step 6: Open a Pull Request
- Go to the original repository on GitHub and click **"Compare & pull request"**.
- Fill out the provided Pull Request template.
- Explain what you changed, why it helps, and any references or links.
- Don't worry if CI catches an issue—maintainers will gladly help guide you through it!

### Step 7: Review & Merge Policy (Maintainer Review Required)
To ensure technical accuracy, consistency, and educational rigor, **all pull requests require explicit review and approval from maintainer [@Aniketchavan7](https://github.com/Aniketchavan7) before merging into `main`**:
1. **Branch Protection Enforced**: The `main` branch is protected. Direct commits are disallowed, and pull requests cannot be merged without review.
2. **Code Owner Approval**: Every PR automatically assigns [@Aniketchavan7](https://github.com/Aniketchavan7) as the designated code owner (defined in [`.github/CODEOWNERS`](./.github/CODEOWNERS)). Approval from the code owner is mandatory to unlock merging.
3. **Automated CI Checks**: All automated test checks (`Test (Python 3.12)` and `Asset & Link Integrity`) must pass.
4. **Stale Review Dismissal**: If you push new commits after receiving approval, GitHub resets the approval status to ensure all final changes are re-reviewed before merge.
5. **Constructive Collaboration**: Reviews are supportive and focused on clarity, real numbers, and accurate system tradeoffs. We will gladly help you get your PR across the finish line!

---

## 📐 Content Style Guide

To maintain high educational quality across all 45 modules, please keep these guidelines in mind:

| Section | Target Style |
| :--- | :--- |
| **🧒 The 30-Second Version (ELI5)** | Direct, accessible, zero buzzwords. Explain it so a freshman or curious high school student understands the core problem and solution. |
| **🍕 Everyday Analogy** | Intuitive, tangible real-world physical metaphor (kitchens, post offices, traffic intersections, library catalogs). |
| **🔢 Real Numbers Math** | Grounded in hardware physics: L1 cache (~1ns) vs. RAM (~100ns) vs. NVMe SSD (~100μs) vs. Network RTT (~40–150ms). |
| **⚖️ Tradeoffs Matrix** | Balanced and honest. Every architecture is a tradeoff—highlight when *not* to use a pattern as clearly as when to use it. |
| **🏢 Real-World Examples** | Citable engineering architecture papers, tech blogs (Netflix TechBlog, Uber Engineering, Stripe Blog, AWS Architecture), or public post-mortems. |

---

## 💡 Good First Issues & Ideas to Explore

Looking for an idea to contribute? Here are some fantastic topics currently open for community contributions:

1. **New FAANG Case Studies**:
   - How **Discord** migrated from MongoDB to Cassandra to ScyllaDB for billions of messages.
   - How **Shopify** handles Black Friday / Cyber Monday flash sale surges.
   - How **Figma** built their real-time multiplayer multiplayer CRDT / operational transform engine.
   - How **Airbnb** designed their distributed search and pricing indexing engine.
2. **Interactive Labs**:
   - Add a runnable simulation of **Consistent Hashing with Virtual Nodes** visualizing node addition/removal load distribution.
   - Build a mini simulation of **Bloom Filter false positive rates** with varying bit-array sizes.
3. **Cheat Sheet Additions**:
   - Add cloud egress cost rules of thumb (AWS / GCP / Cloudflare bandwidth pricing comparison).
   - Add database connection pool sizing formulas ($	ext{Connections} = 2 	imes 	ext{CPU cores} + 	ext{disk count}$).

---

## 🤝 Code of Conduct

We are committed to making participation in **System Design Illustrated** a welcoming, respectful, and harassment-free experience for everyone. Please review our [Code of Conduct](./CODE_OF_CONDUCT.md).

---

## 🏆 Contributor Recognition

Every single contributor—whether you fix a typo, suggest a diagram, or write an entire case study—will be recognized and credited in our README and documentation. You are helping thousands of engineers around the world learn system design.

Thank you for being part of this open community! Let's build and learn together. 🚀
