# Study Schedule

A realistic plan for working through this course at **10–12 hours a week**, the pace stated in the
course brief. It assumes you are doing this alongside a full-time job.

> **Read this before you start Module 1.** The most common way people fail a self-directed course
> is not difficulty — it is losing the thread after a break. This schedule is built to survive
> interruptions.

---

## 1. The headline numbers

| | |
|---|---|
| Total study hours | **492** |
| At 10 h/week | **49 weeks** (~11 months) |
| At 12 h/week | **41 weeks** (~9 months) |
| At 15 h/week | 33 weeks (~8 months) |
| At 6 h/week | 82 weeks (~19 months) |

**Be honest with yourself about the number in that table.** Roughly ten months at a sustainable
pace is the realistic answer for someone in full-time work. A plan that assumes 20 hours a week
will be abandoned in week five, and an abandoned plan teaches nothing.

**These hours are for the material as written** — reading, running every lab, attempting all three
exercises, and taking the assessments. If you skip the exercises the hours drop by roughly a third
and so does what you retain, because the exercises are where the material stops being something you
have read and starts being something you can do.

---

## 2. Module-by-module plan at 11 h/week

| Module | Topic | Hours | Weeks | Cumulative | Project |
|---|---|---|---|---|---|
| **M1** | [AI Foundations](../modules/module-01-ai-foundations/) | 12.0 | 1.1 | 1w | — |
| **M2** | [Python and Software Foundations](../modules/module-02-python-foundations/) | 36.2 | 3.3 | 4w | Project 2 — Ticket API |
| **M3** | [Mathematics and ML Essentials](../modules/module-03-math-ml-essentials/) | 27.8 | 2.5 | 7w | Project 3 — Churn classifier |
| **M4** | [Generative AI and LLM Internals](../modules/module-04-genai-llm-internals/) | 32.2 | 2.9 | 10w | Project 4 — Model comparison |
| **M5** | [Prompting and LLM Applications](../modules/module-05-prompting-llm-apps/) | 33.8 | 3.1 | 13w | Project 5 — Prompt system |
| **M6** | [Embeddings and Search](../modules/module-06-embeddings-search/) | 24.5 | 2.2 | 15w | Project 6 — Search service |
| **M7** | [Retrieval-Augmented Generation](../modules/module-07-rag/) | 40.5 | 3.7 | 19w | Project 7 — RAG system |
| **M8** | [Agentic AI](../modules/module-08-agentic-ai/) | 34.5 | 3.1 | 22w | Project 8 — Agent |
| **M9** | [Model Context Protocol](../modules/module-09-mcp/) | 30.8 | 2.8 | 25w | Project 9 — MCP server |
| **M10** | [AI Governance and Security](../modules/module-10-governance-security/) | 29.5 | 2.7 | 27w | Project 10 — Governance pack |
| **M11** | [AWS Foundations](../modules/module-11-aws-foundations/) | 36.2 | 3.3 | 31w | Project 11 — AWS deployment |
| **M12** | [AI on AWS](../modules/module-12-ai-on-aws/) | 27.8 | 2.5 | 33w | Project 12 — Bedrock service |
| **M13** | [Fine-Tuning and Production](../modules/module-13-finetuning-production/) | 27.2 | 2.5 | 36w | Project 13 — Production LLM app |
| **M14** | [FDE and Delivery Skills](../modules/module-14-fde-delivery/) | 20.5 | 1.9 | 38w | Exercise — Delivery pack |
| **M15** | [Capstone](../modules/module-15-capstone/) | 78.0 | 7.1 | 45w | Capstone build |
| | **Total** | **492** | | **45 weeks** | |

---

## 3. A weekly rhythm that works

Eleven hours split into five sessions. **The split matters more than the total** — three hours on a
Tuesday evening after work will teach you less than three separate hours on three different days,
because spacing is what moves material into long-term memory.

| Day | Time | What |
|---|---|---|
| Mon | 1.5 h | Read the next lesson's §1–§5. Do not run anything yet. |
| Tue | 1.5 h | Work §6 by hand — pencil, not keyboard. Then run the lab. |
| Wed | — | **Rest.** This is part of the schedule, not a gap in it. |
| Thu | 2 h | Exercises 1 and 2. |
| Fri | — | **Rest.** |
| Sat | 3 h | Exercise 3, then the next lesson's §1–§6. |
| Sun | 3 h | Finish the lesson, take the quiz, update the progress tracker. |

**Two rules that matter more than the timetable:**

1. **Work §6 with a pencil before running the lab.** Every worked example in this course is
   designed to be done by hand in ten to twenty minutes. Reading the answer feels like learning and
   is not; deriving it is.
2. **Never skip the quiz because you feel you understood the lesson.** Feeling you understood
   something is uncorrelated with having understood it, which is why the quizzes exist.

---

## 4. Milestones — and what you can actually do at each

| After | Week (at 11 h/wk) | You can |
|---|---|---|
| **M1–M3** | 7 | Read an ML paper's evaluation section and say whether to believe it. Build and honestly evaluate a classifier. |
| **M4–M5** | 13 | Explain what a model is doing internally. Build a reliable prompted application with tests. |
| **M6–M7** | 19 | Build a retrieval system and measure whether it actually helps. |
| **M8–M9** | 25 | Build an agent with tools, and an MCP server other people can use. |
| **M10** | 28 | Run a risk assessment and write the governance documentation for a deployment. |
| **M11–M12** | 34 | Deploy to AWS and run models on Bedrock, with costs you predicted in advance. |
| **M13–M14** | 39 | Take a system to production, and run the client-facing side of the work. |
| **M15** | 45 | Ship a complete capstone you can show someone. |

**The M1–M3 milestone is the one people undervalue.** "Can you tell whether this evaluation is
honest?" separates people who can be trusted with an AI system from people who cannot, and it is
worth more in an interview than any framework you can name.

---

## 5. If you have less time

### 5.1 The 6 h/week route

Same material, **82 weeks**. Halve the weekly rhythm rather than dropping components —
keep the by-hand worked example and the quiz, and spread the exercises across more days.

### 5.2 The fast track, if you have a specific goal

**Do not do this unless you have a deadline.** You will have gaps, and the gaps will be in the
places that cause production incidents.

| Goal | Modules | Hours | Weeks at 11 h/wk |
|---|---|---|---|
| **Build a RAG system** | M1, M3 (L01–L02, L13–L14), M4, M6, M7 | ~110 | 10 |
| **Build agents** | M1, M4, M5, M8, M9 | ~145 | 13 |
| **AI on AWS** | M1, M4, M11, M12 | ~113 | 10 |
| **Governance / assurance role** | M1, M3 (L13–L14), M4, M7, M10 | ~105 | 10 |

**Every fast track includes M1 and M4.** M1 is the vocabulary everything else uses, and M4 is what
lets you reason about a model rather than guess. **Every one that touches evaluation includes
M3-L13 and M3-L14**, because a system you cannot honestly evaluate is not a system you can deploy.

**What the fast tracks skip, and the cost:** Module 2 (you will write worse Python and debug more),
Module 5 (your prompts will be brittle), Module 10 (you will discover governance requirements late,
which is the expensive time to discover them), and Module 14 (you will build the right thing badly
explained). Come back for them.

---

## 6. Getting back on after a break

You will miss a week. Everyone does. The material is built so that this is recoverable:

1. **Do not restart the module.** Open the [progress tracker](../PROGRESS_TRACKER.md) and find the
   last lesson you ticked.
2. **Read that lesson's §12 revision notes only** — about five minutes. They are written to be
   sufficient on their own for recall.
3. **Retake its quiz.** If you score below 70%, reread §5 and §6 of that lesson before moving on.
4. **Then continue.** Do not re-do labs you have already run.

**After a break longer than a month**, work through the module's revision guide in
[`assessments/`](../assessments/) and retake the module assessment. That is what those documents are
for.

---

## 7. Cost planning

**Modules 1 through 10 cost nothing.** Every lab runs locally with no API key, no cloud account and
no network access required. That is a deliberate design constraint of this course, not an accident.

**Modules 11 through 15 involve AWS**, and those lessons:

- state the expected charges **before** any provisioning step,
- give **teardown instructions for every billable resource**,
- prefer free-tier and local alternatives wherever one exists,
- and are explicit that **a billing alert notifies you; it does not cap spending.** Where a hard
  limit is available, the lesson tells you to configure it.

**Budget guidance for M11–M15:** if you tear down promptly and stay in the free tier where the
lesson says you can, the whole course can be completed for a small amount — but *you* are
responsible for what you provision. Set a budget before you start Module 11, check your billing
console at the end of every session, and never leave an endpoint running overnight.

---

## 8. Tracking

- [`PROGRESS_TRACKER.md`](../PROGRESS_TRACKER.md) — tick each lesson, record quiz scores
- [`COVERAGE_MATRIX.md`](../COVERAGE_MATRIX.md) — every syllabus item mapped to where it is taught
- [`GLOSSARY.md`](../GLOSSARY.md) — every term, with the lesson that introduces it
- [`assessments/`](../assessments/) — revision guides and module assessments
- [`answer-keys/`](../answer-keys/) — **do not open before attempting**

---

→ Start at [Module 1, Lesson 1](../modules/module-01-ai-foundations/M1-L01-what-ai-ml-dl-genai-mean.md)
