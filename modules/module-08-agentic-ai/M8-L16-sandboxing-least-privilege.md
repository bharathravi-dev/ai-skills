# M8-L16 — Sandboxing and Least Privilege for Tools

| | |
|---|---|
| **Lesson ID** | M8-L16 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M8-L11](M8-L11-read-only-vs-state-changing.md) |

---

## 1. Learning objectives

1. **Demonstrate** that a narrowly-scoped tool cannot leak data it was never given access to, structurally,
   not merely through a value check.
2. **Demonstrate** that a restricted code-execution environment cannot reach capabilities it was never
   granted, even when an expression explicitly asks for them.
3. **Explain** why removing a capability is a stronger defense than checking whether that capability was
   misused.
4. **Apply** a checkable framework (a set difference between needed and granted capability) to assess
   whether a tool is over-privileged.
5. **Identify**, from a described incident, whether the actual defect was a missing value check or an
   unnecessarily broad grant of capability.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Least privilege** | Granting a tool only the minimum capability it needs to perform its intended job. |
| **Sandboxing** | Restricting an execution environment so it cannot reach capabilities beyond an intended scope. |
| **Over-privileged** | Having access to capability beyond what any legitimate use of a tool actually requires. |
| **Blast radius** | The worst outcome of one call, however it was triggered (M5-L08). |
| **Capability** | A specific thing a tool or execution environment is actually able to do. |

---

## 3. Plain-language explanation

### 3.1 M5-L08's absent-parameter defense and M8-L11's classification both point here

M5-L08 established that a field that doesn't exist can't be set, however persuasive the request. M8-L11
classified tools by what they actually do once called. This lesson asks the question those two ideas
converge on: what is a tool actually *capable* of, structurally — not what it was designed for, but what it
could be made to do?

### 3.2 A narrow tool cannot leak a field it was never given

§7.1 doesn't just check whether a broad tool happens to refuse a sensitive request — it shows that a
narrowly-scoped version of the identical tool has no way to return a field it was never handed in the first
place, regardless of what's asked of it.

### 3.3 A sandbox cannot reach outside its own namespace

§7.2 makes the identical point about code execution: a restricted `eval()` doesn't refuse a suspicious-
looking expression through pattern matching — it simply has no `__import__` to name at all, because its
available names were never populated with it.

### 3.4 A checkable question settles it: what's granted beyond what's needed?

§7.3 turns "is this over-privileged" from a judgment call into a set difference — comparing what a tool
actually needs against what it was actually granted, applied identically to both this lesson's tools.

---

## 4. Analogy

**A hotel keycard programmed for one floor, versus a master key handed out "just in case."** A keycard
programmed only to open a guest's own floor and room cannot open the manager's office, no matter who holds
it or what they claim — not because a rule stops them, but because the key was never cut to fit that lock.
A master key, by contrast, opens everything, and if it falls into the wrong hands (lost, copied, used by a
confused staff member for the wrong room), the consequence is bounded only by what the master key can reach
— which is everything. Handing out master keys "for convenience" trades a real, structural safety property
for a marginal reduction in how often someone has to request a specific key.

### Where the analogy breaks

- **A keycard system can revoke or reprogram a key after the fact.** §7.1's narrow tool has its scope fixed
  in its own code — changing what it can access requires changing the tool itself, not flipping a remote
  permission.
- **A hotel's master key is a single, identifiable physical object.** §7.2's "master key" equivalent
  (unrestricted `eval()`) is a property of how code is *written*, not a discrete object that can be tracked,
  audited, or physically secured the way a real master key can.

---

## 5. Detailed technical explanation

### 5.1 A narrow scope structurally cannot leak what it never has

`[REAL, measured]` §7.1 ran identical requests against a broad customer-info tool (full record access) and
a narrow one (only `name` and `order_history`). **Both returned the same result for a legitimate request.
For a request asking for `ssn`, the broad tool genuinely returned the real value; the narrow tool returned
"no such field" — not because it checked the request and refused it, but because `ssn` was never part of
its own data at all.** This is M5-L08's absent-parameter defense, applied to read scope rather than write
parameters.

### 5.2 A sandbox structurally cannot reach outside its granted namespace

`[REAL, measured]` §7.2 ran the identical arithmetic expression through an unrestricted `eval()` and a
sandboxed one (empty builtins, an explicit allow-list of math functions) — both produced the same correct
result. Given an expression naming `__import__('os').getcwd()`, **the unsafe version genuinely executed a
real operating-system call, returning the actual working directory. The sandboxed version raised a
`NameError` — `__import__` was never in its available names at all**, deliberately chosen as a harmless
call standing in for what could equally have been a file read or a system command.

### 5.3 Removing a capability beats checking for its misuse

`[REAL reasoning]` Both §5.1 and §5.2 demonstrate the identical structural principle stated explicitly:
**a capability that was never granted cannot be misused, by definition, regardless of how the request that
would have misused it was phrased, whether by mistake, by a bug, or by deliberate manipulation.** A value
check or pattern match, by contrast, only catches the specific misuse patterns its author anticipated.

### 5.4 A checkable framework replaces judgment with a set difference

`[REAL, measured]` §7.3's `assess_privilege()` compares a tool's actually-needed capability set against
what it was actually granted. **Applied to this lesson's own four functions, it correctly identifies the
narrow customer-info tool and the sandboxed calculator as matching their needs exactly, and flags the broad
tool and the unsafe calculator as over-privileged, naming precisely which extra capabilities they hold**
(`ssn`, `payment_method`; `filesystem`, `imports`, `network`, `os`).

### 5.5 Assumptions and limitations

- `CUSTOMER_RECORD` is a small, hand-built example, not a claim about how real customer data models are
  structured.
- The sandboxed `eval()` in §7.2 blocks one real class of escape (builtin access) — a production-grade
  sandbox for arbitrary code execution needs substantially more (resource limits, real process isolation),
  which this lab does not attempt to build.
- This lesson does not cover how a real system enforces least privilege at the infrastructure level
  (database row-level security, IAM roles, OS-level containers) rather than inside a single function.

---

## 6. Worked example — the analytics tool with a database admin connection

**The system.** An internal analytics tool lets an agent run read-only reporting queries against a
production database. For convenience during initial development, the tool was connected using the database's
admin credentials, with the plan to "restrict it later" once reporting needs stabilized.

**The incident.** A prompt-injection attempt (M5-L13's own territory) embedded in a document the agent had
retrieved attempted to get the agent to run a query that would modify data rather than merely report on it.
The query itself was almost blocked by the application's own intent — reporting queries shouldn't need write
access — but nothing in the actual database connection *prevented* the write from executing, because the
admin credentials the tool held could do it regardless of what the tool's authors intended it to be used
for.

**Why this matches §5.3 exactly.** The tool's *intended* use was read-only reporting — but its *actual*
capability, via the admin connection, included every write operation the database supported. **The gap
between intended use and granted capability is exactly what this lesson's own tools demonstrate: the broad
customer-info tool's intended use was probably also narrow, but its actual data access was not restricted
to match.**

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The tool's database connection used admin credentials rather than a read-only role | A successful injection could reach far beyond what any legitimate reporting query needed |
| 2 | "Restrict it later" was never revisited once the tool reached production | The temporary, convenient choice became the permanent, actual security posture |
| 3 | No check compared the tool's granted database permissions against what its queries actually required | The over-privileged connection was invisible until an attempted misuse revealed it |

### The fix

**Connect the tool with a read-only database role from the start**, per §5.1 and §5.2 — matching M8-L11's
own read-only classification of the tool's intended function to its actual granted capability.

**Apply §5.4's framework before shipping any tool** — comparing needed capability against granted
capability explicitly, rather than deferring the restriction to "later."

**The general rule.** **A tool's actual capability is not defined by what it is intended to do — it is
defined by what its underlying connection, credentials, or execution environment can actually reach, and
"restrict it later" is a plan that, in practice, competes with every other priority until an incident forces
the question.**

---

## 7. Practical activity

**File:** [`labs/m8/l16_sandboxing_least_privilege.py`](../../labs/m8/l16_sandboxing_least_privilege.py)

**No API key, no network, no third-party dependencies.** Section 2's "escape" demonstration only calls a
harmless, read-only function (`os.getcwd()`) to illustrate the concept safely — it does not execute,
modify, or read anything sensitive.

```bash
source .venv/bin/activate
python labs/m8/l16_sandboxing_least_privilege.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. LEAST PRIVILEGE: A NARROW-SCOPE TOOL CANNOT LEAK WHAT IT NEVER HAS
============================================================================
  A request that only needs the customer's name behaves identically
  on both versions:
    broad:  get_customer_info_broad('name') -> 'Dana Kim'
    narrow: get_customer_info_narrow('name') -> 'Dana Kim'

  A request -- crafted, mistaken, or from a manipulated agent step --
  asking for a field no legitimate support task ever needs:
    broad:  get_customer_info_broad('ssn') -> '123-45-6789'
    narrow: get_customer_info_narrow('ssn') -> "no such field: 'ssn'"

  The broad tool genuinely returns the SSN -- it has that data and no
  scope restriction stops it. The narrow tool cannot leak it, not
  because of a value check that happened to catch this specific
  field name, but because the SSN was never part of its own data at
  all. Removing a capability is a stronger defense than checking
  whether a capability was misused.

============================================================================
2. SANDBOXING: A RESTRICTED EXECUTION ENVIRONMENT CANNOT REACH OUTSIDE ITSELF
============================================================================
  A genuine arithmetic request behaves identically on both versions:
    unsafe:     calculate_unsafe('2 + 2 * 3') -> 8
    sandboxed:  calculate_sandboxed('2 + 2 * 3') -> 8

  An expression reaching for something no calculator needs:
    "__import__('os').getcwd()"
    unsafe:     calculate_unsafe(...) -> 'D:\\Learning\\notes\\ai-skills'
    sandboxed:  calculate_sandboxed(...) -> "BLOCKED: name '__import__' is not defined"

  The unsafe version genuinely executed a real OS call -- reading the
  current directory, deliberately chosen here because it is harmless
  to actually run, standing in for what could just as easily have
  been a file read or a system command. The sandboxed version could
  not even NAME __import__, because its builtins were never made
  available in the first place -- the same removal-over-restriction
  principle as section 1, applied to code execution instead of data.

============================================================================
3. A FRAMEWORK: DOES THIS TOOL'S ACTUAL SCOPE MATCH WHAT IT NEEDS
============================================================================
  Applying a real set-difference check to both this lab's tools:

    get_customer_info_narrow: LEAST PRIVILEGE: granted scope matches what is actually needed
    get_customer_info_broad:  OVER-PRIVILEGED: granted access to ['payment_method', 'ssn'] beyond what any legitimate call needs
    calculate_sandboxed:      LEAST PRIVILEGE: granted scope matches what is actually needed
    calculate_unsafe:         OVER-PRIVILEGED: granted access to ['filesystem', 'imports', 'network', 'os'] beyond what any legitimate call needs

  This connects directly to M8-L11's own classification and M5-L08's
  blast-radius principle: a state-changing, over-privileged tool is
  the highest-risk combination this course has built toward -- not
  because it is more LIKELY to be misused than a narrowly-scoped
  one, but because the CONSEQUENCE of any misuse, accidental or
  adversarial, is structurally larger.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: both customer-info functions genuinely differ in what data
  they can return, verified directly above; both calculate functions
  genuinely differ in what they can execute, including a real,
  harmless OS call the sandboxed version genuinely cannot reach.

  ILLUSTRATIVE: CUSTOMER_RECORD is a small, hand-built example, not a
  claim about real customer data models. The sandboxed eval() shown
  here blocks ONE real class of escape (builtin access) -- a
  production-grade sandbox for arbitrary code execution needs much
  more (resource limits, real process isolation), which this lab
  does not attempt to build.

  NOT SHOWN: how a real system enforces least privilege at the
  infrastructure level (database row-level security, IAM roles, OS
  containers) rather than inside a single Python function; and a
  complete, hardened code-execution sandbox, which is a substantial
  engineering effort beyond this lesson's own scope.

Done.
```

### 7.3 Reading the result

**Section 1 and section 2 are the identical argument, made twice, in two different domains — data access
and code execution.** Reading them side by side reinforces that "least privilege" and "sandboxing" are not
two unrelated topics bundled into one lesson; they are the same structural principle (remove the capability
rather than police its use) applied to two different kinds of resource.

**Section 2's harmless `getcwd()` call is doing real work, not just illustrating a point safely.** It
demonstrates a genuine reach beyond the calculator's intended scope — an actual, real operating-system call
— while remaining completely safe to run, which is exactly the balance a responsible demonstration of this
risk needs to strike.

**Section 3's set-difference framework is what makes "over-privileged" a checkable fact rather than a
vague concern.** Applied identically to both of this lesson's tool pairs, it names the exact extra
capabilities each over-privileged version holds — not a general sense that something feels risky.

---

## 8. Common mistakes and troubleshooting

1. **Granting a tool broad access "for flexibility" rather than the specific access its actual job
   requires.** §5.1, §6 — this trades a real, structural safety property for a marginal convenience.
2. **Relying on a value check or pattern match to prevent misuse, when removing the capability entirely is
   possible.** §5.3 — a check only catches the misuse patterns its author anticipated; an absent capability
   catches all of them, by construction.
3. **Treating "restrict it later" as an acceptable temporary state for a tool already in production.** §6 —
   the temporary choice tends to become the permanent security posture in practice.
4. **Assuming a code-execution tool is safe because its typical use cases are benign.** §5.2 — what matters
   is what the execution environment can actually reach, not what it's usually asked to do.
5. **Treating "is this tool over-privileged" as a subjective judgment rather than a checkable comparison.**
   §5.4 — a set difference between needed and granted capability settles it directly.

| Symptom | Likely cause | Fix |
|---|---|---|
| A tool can return or affect data far beyond what its actual stated purpose requires | The tool was granted broader access than its intended use needs, "for flexibility" | Restrict the tool's actual data or capability access to match its real job, per §5.1, §5.4 |
| A code-execution tool can reach the filesystem, network, or OS despite only being meant for a narrow computation | The execution environment was not sandboxed at all, or insufficiently | Restrict the execution environment's available names/capabilities explicitly, per §5.2 |
| A tool's underlying connection or credentials are broader than its application-level logic implies | Convenience during development ("restrict it later") became the permanent production configuration | Apply §5.4's needed-vs-granted comparison and correct the underlying connection or credentials directly |
| Uncertainty about whether a specific tool is over-privileged | No systematic comparison exists between what the tool needs and what it was actually granted | Apply the set-difference framework in §5.4 explicitly, rather than relying on a general impression |

---

## 9. Security, privacy, reliability, cost

- **Security.** Grant a tool only the minimum capability its actual job requires — a capability that was
  never granted cannot be misused, regardless of how the request that would misuse it is phrased (§5.1,
  §5.3).
- **Security.** Sandbox any code-execution tool so its available names and reachable resources are an
  explicit, minimal allow-list, not the full standard environment (§5.2).
- **Security.** Never treat "restrict it later" as an acceptable state for a tool already reachable in
  production — the worked example's incident is exactly what "later" becoming "never" produces (§6).
- **Reliability.** Apply a checkable, set-difference comparison between needed and granted capability for
  every tool before shipping it, rather than relying on subjective judgment (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why couldn't the narrow customer-info tool return the SSN field, even when explicitly asked for it?
2. Why couldn't the sandboxed calculator execute `__import__('os').getcwd()`?
3. Why is removing a capability described as a stronger defense than checking for its misuse?
4. What are the two inputs to the `assess_privilege()` framework, and what does it output?
5. In your own words, what was the actual defect in §6's worked example — the query attempt, or something
   else?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the SSN leak/no-leak contrast in §7.1 and the sandbox escape/block contrast in
   §7.2 on your own machine.
2. Add a third field to `CUSTOMER_RECORD` (e.g., a home address) and confirm the narrow tool correctly
   cannot return it, matching the SSN case.
3. Add a second, different escape attempt to §7.2 (e.g., an expression trying to reach `open`) and confirm
   the sandboxed version blocks it the same way.
4. Using §5.4's `assess_privilege()` function, evaluate a tool of your own design (real or hypothetical)
   and identify any excess capability it holds.
5. Extend `calculate_sandboxed()`'s allow-list with one additional safe math function, and confirm it works
   correctly while the sandbox still blocks the same escape attempt as before.

### Exercise 3 — Challenge (~50 min)

1. Design a least-privilege scope for a hypothetical tool that needs to both read and write a narrow slice
   of data (not purely read-only), and specify exactly what capability it should and should not have.
2. Research (conceptually) what additional protections a production-grade code-execution sandbox needs
   beyond restricting builtins (e.g., resource/time limits, process isolation), and explain why each is
   necessary.
3. Using M5-L13's own prompt-injection coverage, design a scenario where an over-privileged tool's excess
   capability is specifically what makes an injection attempt dangerous, and show how least privilege would
   have prevented the consequence even if the injection itself succeeded.
4. Propose a code-review checklist item that would have caught §6's worked example's admin-credentialed
   tool before it reached production.
5. Using §5.4's framework, design an automated check that could run in CI to flag any newly-added tool
   whose granted capability set is broader than a declared "needed capability" annotation.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l16).)*

**Q1.** Per §7.1's measured result, why couldn't the narrow customer-info tool return the SSN field?

- A. The SSN field was never part of the narrow tool's own data at all, structurally, regardless of what was asked.
- B. It checked the request and specifically refused any request for "ssn".
- C. The narrow tool crashed when asked for the SSN.
- D. The SSN field was encrypted and could not be decrypted.

**Q2.** Per §7.2's measured result, what happened when the escape-attempt expression was run through the
sandboxed calculator?

- A. It executed successfully and returned the current working directory.
- B. It silently returned zero with no error.
- C. It crashed the entire Python process.
- D. It raised a NameError, because __import__ was never available in the sandboxed namespace.

**Q3.** Per §7.2's measured result, what did the UNSAFE calculator actually do with the identical escape
attempt?

- A. It also raised a NameError, identical to the sandboxed version.
- B. It genuinely executed a real operating-system call and returned the actual current working directory.
- C. It refused to execute the expression at all.
- D. It returned an error message stating the operation was blocked.

**Q4.** Per §5.3, why is removing a capability described as a stronger defense than checking for its
misuse?

- A. Removing a capability is always faster to implement than writing a check.
- B. Checks are always more effective than removing capabilities.
- C. A capability that was never granted cannot be misused at all, regardless of how the request is phrased, while a check only catches patterns its author anticipated.
- D. There is no meaningful difference between the two approaches.

**Q5.** Per §5.4, what are the two inputs to the `assess_privilege()` framework?

- A. The capability a tool actually needs and the capability it was actually granted.
- B. The tool's name and its author's identity.
- C. The number of times a tool has been called and its average response time.
- D. The tool's read-only or state-changing classification alone.

**Q6.** Per §7.3's measured result, what specific excess capability did assess_privilege() identify for the
unsafe calculator?

- A. No excess capability was identified.
- B. Only network access was flagged.
- C. The framework could not evaluate the unsafe calculator at all.
- D. filesystem, imports, network, and os access, all beyond what arithmetic actually requires.

**Q7.** Per §6's worked example, what was the actual capability the analytics tool held, versus its
intended use?

- A. Its intended use and actual capability were identical and properly matched.
- B. Its intended use was read-only reporting, but its actual capability, via admin database credentials, included every write operation the database supported.
- C. It had no database connection at all.
- D. Its actual capability was narrower than its intended use required.

**Q8.** Per §6, why did "restrict it later" fail to prevent the incident?

- A. The restriction was applied immediately and worked as intended.
- B. The tool was never actually used in production.
- C. The temporary, convenient choice was never revisited once the tool reached production, becoming the permanent security posture.
- D. The database itself prevented all write operations regardless of credentials.

**Q9.** Per §6, what is the stated general rule this incident illustrates?

- A. A tool's actual capability is defined by what its underlying connection or execution environment can actually reach, not by what it is intended to do — and "restrict it later" tends to become "never" in practice.
- B. Database connections should never be used by any automated tool.
- C. Prompt injection attacks are impossible to defend against under any circumstances.
- D. The incident has no generalizable lesson beyond this specific system.

**Q10.** Per §6, what two fixes are proposed together for the kind of gap this incident revealed?

- A. Removing the analytics tool entirely from production.
- B. Disabling all reporting functionality permanently.
- C. Only increasing logging, with no change to the tool's actual database credentials.
- D. Connecting the tool with a read-only database role from the start, and applying the needed-versus-granted capability comparison before shipping any tool.

**Q11.** Per §7.4, what does this lesson explicitly NOT cover?

- A. The least-privilege demonstration in section 1.
- B. How a real system enforces least privilege at the infrastructure level, and a complete, hardened code-execution sandbox — left as substantial engineering efforts beyond this lesson's scope.
- C. The sandboxing demonstration in section 2.
- D. The assess_privilege() framework in section 3.

**Q12.** What is the general lesson this lab demonstrates about sandboxing and least privilege?

- A. A tool's safety depends entirely on how it is intended to be used, regardless of what it is actually capable of.
- B. Sandboxing and least privilege are unrelated concerns that happen to share a lesson.
- C. Removing a capability a tool doesn't need is a structurally stronger defense than checking whether that capability was misused, and this applies identically to data access and code execution.
- D. Value checks and pattern matching are always sufficient to prevent capability misuse.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a new tool your team is building needs to send an
email to a customer. What specific capability would you grant it, and what would you deliberately withhold,
based on this lesson?

---

## 12. Revision notes

- **A narrowly-scoped tool cannot leak a field it was never given access to** — measured directly: a
  narrow customer-info tool correctly could not return an SSN field a broad version genuinely could.
- **A sandboxed execution environment cannot reach a capability it was never granted** — measured directly:
  a sandboxed calculator raised a NameError for `__import__`, while an unsafe version genuinely executed a
  real OS call.
- **Removing a capability is a structurally stronger defense than checking for its misuse** — a check only
  catches anticipated misuse patterns; an absent capability catches all of them, by construction.
- **A checkable set-difference between needed and granted capability replaces subjective judgment about
  over-privilege** — applied identically to this lesson's own four tools, correctly identifying both
  over-privileged ones and naming their specific excess capability.
- **A tool's actual capability is defined by its underlying connection or execution environment, not by its
  intended use** — the general rule §6's worked example illustrates directly, and "restrict it later"
  tends to become the permanent posture in practice.

---

## 13. Completion checklist

- [ ] I can explain why a narrow-scope tool structurally cannot leak data it was never given.
- [ ] I can explain why a sandboxed execution environment structurally cannot reach an ungranted
      capability.
- [ ] I can explain why removing a capability is stronger than checking for its misuse.
- [ ] I can apply a needed-versus-granted capability comparison to assess whether a tool is
      over-privileged.
- [ ] I can identify, from a described incident, whether the defect was a missing check or unnecessarily
      broad capability.
- [ ] I grant tools only the minimum capability their actual job requires, not broad access "for
      flexibility."
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M5-L08's own absent-parameter defense, extended directly to read-scope and execution-scope in this
  lesson. `[STABLE]`
- M8-L11's own read-only vs state-changing classification, connected directly to privilege level in §5.4.
  `[STABLE]`
- OWASP, guidance on least privilege and sandboxing for LLM tool integrations, where available.
  `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L17 — Tracing and Task-Level Evaluation

This lesson bounded what a tool can do. Next: seeing what an agent actually did across an entire task, and
evaluating whether the task itself succeeded, not just whether any single step did.
