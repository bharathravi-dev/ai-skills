# Zero to Professional AI Engineer

A complete, self-contained course built for **Bharath** — a Technology Lead with frontend and web
application experience, starting from zero in AI, machine learning, mathematics and AWS.

This is not a reading list. It contains the actual teaching material: explanations, worked examples
with real arithmetic, runnable code, exercises, quizzes, separate answer keys, projects with
acceptance criteria, and a capstone.

---

## Start here

1. Read this file (10 minutes).
2. Read [`COURSE_PLAN.md`](COURSE_PLAN.md) — the full lesson inventory, prerequisite map, design
   assumptions and time budget.
3. Open [`modules/module-01-ai-foundations/M1-L01-what-ai-ml-dl-genai-mean.md`](modules/module-01-ai-foundations/M1-L01-what-ai-ml-dl-genai-mean.md)
   and begin.
4. Tick items in [`PROGRESS_TRACKER.md`](PROGRESS_TRACKER.md) as you go.

**Do not skip Module 2** even though you are an experienced engineer. It is short for you, but it
establishes the exact Python idioms, validation library and project layout every later module uses.

---

## Repository map

| Path | What is in it |
|---|---|
| [`README.md`](README.md) | This file |
| [`COURSE_PLAN.md`](COURSE_PLAN.md) | Full lesson inventory, prerequisite map, assumptions, verification policy |
| [`COVERAGE_MATRIX.md`](COVERAGE_MATRIX.md) | Every syllabus item mapped to the lesson that teaches it |
| [`PROGRESS_TRACKER.md`](PROGRESS_TRACKER.md) | Checklist of every lesson, project and assessment |
| [`GLOSSARY.md`](GLOSSARY.md) | Every term and acronym, defined |
| [`GENERATION_STATUS.md`](GENERATION_STATUS.md) | What has been written, what remains, exact next step |
| [`modules/`](modules/) | The lessons, one file per lesson, grouped by module |
| [`labs/`](labs/) | Small runnable scripts belonging to individual lessons |
| [`projects/`](projects/) | Multi-file project applications with their own READMEs |
| [`assessments/`](assessments/) | Module assessments and the final course assessment |
| [`answer-keys/`](answer-keys/) | Answers, reasoning and rubrics — **kept separate on purpose** |
| [`cheatsheets/`](cheatsheets/) | Quick-reference sheets and condensed revision notes |
| [`references/`](references/) | Study schedule, source links, further reading |

---

## How to use a lesson

Every lesson follows the same 21-part structure. Use it in this order:

1. Read the **plain-language explanation** first. Do not fight the technical section yet.
2. Read the **analogy** — and then read **"where the analogy breaks"**, which matters more.
3. Work the **worked example on paper**. Actually write the numbers down. This is the step people
   skip and it is the step that creates real understanding.
4. Run the **code**. Type it rather than pasting it, at least in Modules 2–4.
5. Attempt the **three exercises** before looking at anything.
6. Take the **quiz** with the answer key closed.
7. Only then open [`answer-keys/`](answer-keys/).
8. Tick the **completion checklist**.

If you score below 60% on a lesson quiz, re-read the technical explanation and redo the worked
example before moving on. The prerequisite chains are real; a shaky Module 6 makes Module 7
genuinely confusing.

---

## Environment setup (do this once, in M2-L01)

Verified on this machine on **2026-09-07**: Python 3.12.3, git 2.43.0, Docker 29.2.1, SQLite 3.50.4,
Node 24.13.1.

```bash
# from the course root
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in your own keys
```

`requirements.txt` pins versions that were actually installed and tested in this environment.
Nothing in this course puts a real credential in a file that git tracks — see M2-L19.

---

## Cost policy

- **Modules 1–3** cost nothing. No account, no API key.
- **Modules 4–9** work fully offline with a mock model client that ships with the course. A real
  provider key is optional; every lesson states which parts need one and roughly what they cost.
- **Modules 11–12** use AWS and **can incur real charges**. Every cloud lab begins with a cost
  warning and ends with **teardown instructions**. Set a budget alert first (M11-L06) — and note
  that a budget alert is a *notification*, not a spending cap.
- No infrastructure was provisioned and no money was spent to write this course. Cloud outputs are
  labelled `[NOT EXECUTED]` where that is the case.

---

## Verification labels used throughout

| Label | Meaning |
|---|---|
| `[STABLE]` | Concept unlikely to change |
| `[VERIFIED 2026-09-07]` | Checked against an official source that day |
| `[UNVERIFIED]` | From training knowledge, **not** re-checked — confirm before production use |
| `[EXECUTED]` | Code was actually run here; shown output is real |
| `[NOT EXECUTED]` | Code needs paid/cloud resources; output is illustrative |

Model names, prices, quotas and regional availability change constantly. They are always treated as
`[UNVERIFIED]` and each lesson names the official page to confirm on.

---

## What this course honestly does not do

- It does not make you an ML researcher. You will understand transformers well enough to debug and
  reason about them, not to invent new architectures.
- It does not cover every framework. It teaches mechanics first so that any framework becomes
  readable.
- It does not give legal advice. Governance here is engineering practice (M10-L16 is explicit).
- It cannot be complete. These fields move monthly. `COURSE_PLAN.md` §6 separates required
  professional foundations from optional specializations.

---

## Suggested pace

10–12 hours per week → roughly 32–38 weeks total. Full week-by-week plan:
[`references/STUDY_SCHEDULE.md`](references/STUDY_SCHEDULE.md).

A faster route exists if you only need the AI Engineer core:
M1 → M2 → M4 → M5 → M6 → M7 → M8 → M9 → M15, about 20 weeks.
