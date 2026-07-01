# LAUNCH.md - cc-bench

A prioritized, evidence-cited checklist for presenting and launching cc-bench.
Every item links to its source. Rule of the house: **be honest** - no fake
stars, no asking people to upvote, no buzzwords. Anything that violates a
platform's rules is excluded on purpose.

---

## 1. README & presentation

- [ ] Open with a **one-line elevator pitch (~10 words or fewer)** placed immediately after the title/logo - say what it does, not how. ([dev.to - README template that gets stars](https://dev.to/belal_zahran/the-github-readme-template-that-gets-stars-used-by-top-repos-4hi7))
- [ ] Put a **trimmed demo GIF or screenshot (15-30s max, under ~5MB)** right after the title - a visual proves the tool faster than a paragraph. ([dev.to - README best practices](https://dev.to/iris1031/github-readme-best-practices-how-to-write-a-readme-that-gets-stars-2gb2))
- [ ] Keep **3-5 badges** (build status, version, license, downloads); more than ~8 starts looking cluttered. ([dev.to - README template that gets stars](https://dev.to/belal_zahran/the-github-readme-template-that-gets-stars-used-by-top-repos-4hi7))
- [ ] Provide a **copy-paste Quick Start of ≤5 steps** that goes zero-to-working in under 2 minutes, and **test it on a fresh machine**. ([dev.to - README template that gets stars](https://dev.to/belal_zahran/the-github-readme-template-that-gets-stars-used-by-top-repos-4hi7))
- [ ] Make sure the README covers the **five common README contents**: what it does, why it's useful, how to get started, where to get help, who maintains/contributes. ([GitHub Docs - About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes))
- [ ] Add **social proof + project hygiene** (a specified license and a contributing guide); per the article citing GitHub research, repos with detailed READMEs get ~50% more contributions. ([dev.to - README template that gets stars](https://dev.to/belal_zahran/the-github-readme-template-that-gets-stars-used-by-top-repos-4hi7))

## 2. Repo settings & discoverability

- [ ] Upload a **custom social preview image** (PNG/JPG/GIF under 1MB; **1280x640 px, 2:1 ratio** displays best) so shared links render a rich card. ([GitHub Docs - Social media preview](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview))
- [ ] Add **up to 20 relevant topics** (lowercase letters, numbers, hyphens; ≤50 chars each) so the repo surfaces in topic browsing and search. ([GitHub Docs - Classifying with topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics))
- [ ] Keep a **clear README for the repository** - GitHub explicitly recommends one to make work easy to understand and navigate. ([GitHub Docs - Best practices for repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories))
- [ ] **Pin cc-bench** (and up to six best repos/gists combined) to your GitHub profile so visitors see your best work first. ([GitHub Docs - Pinning items to your profile](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/pinning-items-to-your-profile))
- [ ] Publish **tagged Releases with auto-generated notes** (merged PRs, contributors, full-changelog link); GitHub auto-assigns the "latest" label by semantic version if you don't set it. ([GitHub Docs - Automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes))

## 3. Launch channels & timing

- [ ] Post **Show HN on Tuesday-Thursday, 9am-12pm ET**, aiming for **30-50 upvotes in the first hour** - early momentum determines ranking and only a small fraction reach the front page. ([daily.dev - Hacker News marketing for dev tools](https://business.daily.dev/resources/hacker-news-marketing-developer-tools-show-hn-launch-day-sustained-coverage/))
- [ ] Title it **`Show HN: [Name] - [one-sentence technical description]`**, **8-12 words, under 80 chars**, **no buzzwords** ("revolutionary", "game-changing"), and **link to the live repo/demo** - never a waitlist page. ([daily.dev - Hacker News marketing for dev tools](https://business.daily.dev/resources/hacker-news-marketing-developer-tools-show-hn-launch-day-sustained-coverage/))
- [ ] Within **5 minutes**, post a **maker first comment** explaining what you built plus **one honest limitation**, then **reply to every meaningful comment within ~15 minutes** - active presence sustains a front-page post 18-24h; silence kills it in 4-6h. ([daily.dev - Hacker News marketing for dev tools](https://business.daily.dev/resources/hacker-news-marketing-developer-tools-show-hn-launch-day-sustained-coverage/))
- [ ] **Do not ask Slack/Twitter followers to upvote**, and use a **personal account, not a brand account** - coordinated voting triggers HN's anti-abuse penalties; authentic participation earns 2-3x more engagement. ([daily.dev - Hacker News marketing for dev tools](https://business.daily.dev/resources/hacker-news-marketing-developer-tools-show-hn-launch-day-sustained-coverage/))

## 4. Credibility signals

- [ ] Keep a **permissive license (MIT/Apache 2.0)** - MIT appears in 92% of OSS projects per the 2025 OSSRA report - to remove the compliance friction that makes adopters hesitate. ([daily.dev - How licenses shape developer choices](https://business.daily.dev/resources/how-open-source-licenses-shape-developer-choices/))
- [ ] Structure the README to answer **"What does it do? Why is it useful? How do I start? Where do I get help?"** - better docs mean more users, fewer support requests, more contributors. ([Open Source Guides - Starting a project](https://opensource.guide/starting-a-project/))
- [ ] Adopt the **Contributor Covenant** for CODE_OF_CONDUCT (40,000+ projects incl. Kubernetes, Rails) to signal a welcoming, well-governed community. ([Open Source Guides - Starting a project](https://opensource.guide/starting-a-project/))
- [ ] Display a **CI build-status badge and a code-coverage badge**, aim for ~5-10 accurate badges (not bloat), and **keep them current** - stale badges erode trust. ([daily.dev - Readme badges](https://daily.dev/blog/readme-badges-github-workflow-status-indicators/))
- [ ] Tap **awesome-lists as a discovery channel** (sindresorhus/awesome ~450k stars) by contributing a high-quality, well-categorized list per its CONTRIBUTING guidelines. ([sampaio.cloud - GitHub's Awesome List](https://sampaio.cloud/en/posts/awesome-list-github/))

## 5. After launch / growth

- [ ] Label beginner-friendly issues **`good first issue`** so GitHub surfaces them to potential new contributors. ([Open Source Guides - Best practices for maintainers](https://opensource.guide/best-practices/))
- [ ] **Keep issues and PRs moving** and publish an explicit **response-time expectation** (e.g., 10up replies to every issue/PR within five business days). ([10up - Open Source Best Practices: Maintaining](https://10up.github.io/Open-Source-Best-Practices/maintaining/))
- [ ] On a newcomer's first issue, prioritize **active maintainer participation** - the factor most robustly linked to long-term retention (E-value up to ~2.24); moderate discussion (~5-15 comments) helps weakly. ([arXiv - The First Issue Matters](https://arxiv.org/html/2603.27136v1))
- [ ] Don't rely on a fast or upbeat first reply alone - a 2.7M-PR study found no link between speedy/positive first responses and future contributions; invest in **substantive review** instead. ([arXiv - Does the First Response Matter](https://arxiv.org/html/2104.02933v3))
- [ ] Ship **semantic-versioned releases with a hand-curated, latest-first changelog** in Keep a Changelog format (Added/Changed/Deprecated/Removed/Fixed/Security + an Unreleased section); changelogs are for humans, so curate rather than fully automate. ([Keep a Changelog](https://keepachangelog.com/en/1.0.0/))

---

## Ready to execute (prepared, needs the maintainer)

### Publish to PyPI (one-time, ~5 min)

Both names verified free (2026-07-01): `cc-bench` and `ccbench`. Artifacts build
clean and the wheel passed a pristine-venv test (version, doctor, selftest).

```bash
uv build                                    # dist/ already verified
uv publish --token pypi-XXXX                # or: twine upload dist/*
# then flip the README one-liner to: uvx cc-bench doctor
```

### awesome-claude-code submission (paste into their issue form)

> **cc-bench** - Does your CLAUDE.md actually help? Audits your Claude Code /
> Codex setup against cited evidence (`ccbench doctor`, score /100), then
> A/B-tests config changes on your own repo with honest statistics (permutation
> tests, confidence intervals, placebo control, "not proven" by default).
> Zero-install: `uvx --from git+https://github.com/Galou3/cc-bench ccbench doctor`.
> MIT. https://github.com/Galou3/cc-bench

### GitHub Marketplace listing (Action)

`action.yml` ships in the repo (pin `Galou3/cc-bench@v0.3.0`). To list it:
repo page -> Releases -> draft release -> tick "Publish this Action to the
GitHub Marketplace" -> category: Continuous integration.

### Launch posts

Show HN / Reddit / X drafts live in the session notes; the HN title:
`Show HN: cc-bench - measure if your CLAUDE.md actually helps (CIs, not vibes)`.
Post Tue-Thu 9am-12pm ET, maker comment within 5 minutes including one honest
limitation (alpha; mock demo uses injected probabilities; real runs cost quota).

### First content post (pre-registered)

`experiments/001-superclaude-token-claim/PROTOCOL.md` is committed before any
data: measuring SuperClaude's "30-50% fewer tokens" claim with held-out tasks
and a success-rate guard. Running it needs maintainer quota (~$10-25).
