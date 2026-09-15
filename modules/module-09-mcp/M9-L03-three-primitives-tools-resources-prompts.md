# M9-L03 — The Three Primitives: Tools, Resources, Prompts

| | |
|---|---|
| **Lesson ID** | M9-L03 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M9-L02](M9-L02-hosts-clients-servers.md) |

---

## 1. Learning objectives

1. **Define** MCP's three primitives — tools, resources, and prompts — and what distinguishes each.
2. **Demonstrate** that a tool requires an explicit, argument-bearing decision to call, while a resource is
   read by fixed identifier with no such decision.
3. **Demonstrate** that a prompt is server-maintained, reusable text, distinct from both an action and raw
   data.
4. **Diagnose** a real design mistake — modeling pure lookup data as a tool — and measure the unnecessary
   decision step it forces.
5. **Apply** the distinction to choose the right primitive for a new piece of server functionality.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Tool** | A model-invoked action, called explicitly with specific arguments at a specific moment. |
| **Resource** | Host-readable data addressed by a fixed identifier (URI), read without a model deciding arguments. |
| **Prompt** | A reusable, server-maintained text template, explicitly invoked and filled with named fields. |
| **Decision step** | A point where something (a model or decision function) must choose to call a tool, at some real cost. |

---

## 3. Plain-language explanation

### 3.1 One protocol, three different kinds of thing a server can offer

M9-L01 and M9-L02 both used tools as their only example. MCP actually names three distinct primitives: a
**tool** is something you *do* (an action, with arguments to decide); a **resource** is something you *read*
(data at a fixed address, no arguments to decide); a **prompt** is reusable *text* a server maintains so
every client invoking it gets the same well-crafted wording.

### 3.2 The test that actually distinguishes them

§7.1–§7.3 build one instance of each against the identical small dataset. The tool (`issue_refund`) needed an
explicit call with explicit arguments. The resource (`orders://O-1001`) needed only a fixed URI — there was
never an argument to reason about, only an address to read. The prompt (`refund_explanation`) needed a
name and some fields to fill in a template the server itself owns and maintains.

### 3.3 A real cost to getting this wrong

§7.4 takes something that is obviously a resource — a customer's own order history, pure lookup data — and
deliberately builds it as a tool instead. **The measured result: the tool-based design required one explicit
decision step just to retrieve data that was never actually a decision**, while the resource-based design,
reading the identical data, required none. This is not a stylistic preference; it is a measurable planning
cost paid for no reason.

---

## 4. Analogy

**A vending machine, a public bulletin board, and a form letter template.** A vending machine (a tool)
requires you to choose a specific selection and pay a specific amount — an explicit decision every time, with
consequences (a real transaction). A public bulletin board (a resource) just sits there with information
posted on it — you walk up and read whatever's pinned at a specific spot, no decision beyond which spot to
look at. A form letter template (a prompt) is pre-written by someone else specifically so that anyone filling
in the blanks gets consistent, well-crafted wording, rather than composing a new letter from scratch each
time.

### Where the analogy breaks

- **A vending machine doesn't reason about what you should pick.** A tool's *decision* of which action and
  arguments to use is made by the calling side (the host's decision logic, per M9-L01) — the vending-machine
  analogy captures the "explicit choice with consequences" part, but the choosing itself is external to the
  machine, just as it is external to the tool.
- **A bulletin board doesn't change its own postings on request.** A resource can, in real MCP servers,
  change over time and even notify subscribers of updates — a dimension the static bulletin board doesn't
  capture, and one this lesson's lab does not demonstrate (§5.5).

---

## 5. Detailed technical explanation

### 5.1 A tool always represents an explicit decision to act

`[REAL, measured]` §7.1 called `issue_refund("O-1001", 40.0)` and received `{"order_id": "O-1001",
"refunded": 40.0}`. **Calling it required choosing specific arguments at a specific moment** — exactly
M8-L03's own definition of a tool call, unchanged here. Nothing about a tool is passive.

### 5.2 A resource is read by address, with no arguments to decide

`[REAL, measured]` §7.2 read two resources — `orders://O-1001` and `orders://O-1002` — using only their URIs,
with no other arguments at all. **A host could read every resource it has access to and place the content
directly into context with no model decision step involved**, a structurally different operation from a tool
call.

### 5.3 A prompt is server-maintained reusable text

`[REAL, measured]` §7.3 rendered the `refund_explanation` prompt by name, supplying named fields
(`order_id`, `status`, `amount`), and received back fully-formed text. **The server owns and maintains the
prompt's actual wording** — a client invoking it by name gets that wording filled in, rather than composing
equivalent text itself each time.

### 5.4 Modeling lookup data as a tool forces an unnecessary decision step

`[REAL, measured]` §7.4 built the identical customer-order lookup two ways: as a tool
(`get_customer_orders_as_tool`), requiring a decision function to explicitly plan and call it, and as a
resource, read directly with zero decision steps. **The measured result: 1 explicit decision step for the
tool-based path versus 0 for the resource-based path**, retrieving the exact same underlying data both times.
The tool-based design paid a real planning cost for information that was never actually a decision.

### 5.5 Assumptions and limitations

- This lab's URI scheme (`"orders://..."`) is a small, hand-chosen convention for this lesson — real MCP
  resource URIs follow each server's own scheme design.
- Resource subscriptions and update notifications, prompt arguments with their own schemas, and the full
  initialization/capability-negotiation handshake that tells a client which primitives a specific server
  actually supports (M9-L05) are not shown here.

---

## 6. Worked example — the catalog server that made everything a tool

**The situation.** A team built an MCP server for an internal product catalog, exposing three "tools":
`get_product_details(product_id)`, `get_current_promotions()`, and `apply_discount(order_id, code)`. A
review flagged that the agent connecting to this server was making noticeably more planning steps per
request than a comparable integration with a different catalog server.

**Diagnosis, applying this lesson directly.** Of the three, only `apply_discount` is genuinely a tool — it
performs a real action (a discount applied to a specific order) requiring an explicit decision with
arguments. **`get_product_details` and `get_current_promotions` are both pure lookups**, exactly like §7.4's
customer-order example: `get_product_details` reads by a fixed identifier (a product id), and
`get_current_promotions` reads a value that doesn't even vary by argument at all. Both had been modeled as
tools, forcing the connected agent's decision step to explicitly plan a call for data it could otherwise have
simply read.

**Why this went unnoticed initially.** Every individual tool call worked correctly — the review only
surfaced the issue by comparing planning-step *counts* across two otherwise-comparable integrations, exactly
the measurement discipline §7.4's own step-count comparison applies directly.

**Two things the team found, applying §5.2 and §5.4's own distinction:**

| # | Finding | Consequence |
|---|---|---|
| 1 | `get_product_details` and `get_current_promotions` had no real decision to make — only an identifier (or nothing) to read | Both should have been resources, not tools, per §5.2 and §5.4 |
| 2 | `apply_discount` genuinely needed a decision (which order, which code, whether it should apply at all) | Correctly modeled as a tool, and left unchanged |

### The fix

**Re-model `get_product_details` as a resource, addressed by product id, and `get_current_promotions` as a
resource with a fixed address** — per §5.2 and §5.4, eliminating two pointless decision steps from every
agent run that needed this data.

**Leave `apply_discount` as a tool**, since it is a genuine action requiring an explicit decision, unlike the
other two.

**The general rule.** **If retrieving something never required deciding between multiple possible arguments
or outcomes — only an identifier to look up, or nothing at all — it is very likely a resource being modeled
as a tool**, paying a real, measurable planning cost for no benefit.

---

## 7. Practical activity

**File:** [`labs/m9/l03_three_primitives.py`](../../labs/m9/l03_three_primitives.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l03_three_primitives.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A TOOL: A MODEL-INVOKED ACTION, EXPLICITLY DECIDED AND CALLED
============================================================================
  Calling the 'issue_refund' TOOL: issue_refund('O-1001', 40.0) -> {'order_id': 'O-1001', 'refunded': 40.0}

  A tool requires an explicit call, with explicit arguments, at an
  explicit moment -- exactly M8-L03's own tool-call definition,
  unchanged. Nothing about a tool is passive; it always represents a
  decision to DO something.

============================================================================
2. A RESOURCE: HOST-READABLE DATA, ADDRESSED BY A URI, NOT 'CALLED'
============================================================================
  Reading the RESOURCE 'orders://O-1001': {'customer': 'Priya Nair', 'amount': 40.0, 'status': 'delivered'}
  Reading the RESOURCE 'orders://O-1002': {'customer': 'Priya Nair', 'amount': 15.0, 'status': 'shipped'}

  Reading a resource never required deciding what arguments to
  pass -- only which URI to read. A host can read every resource it
  has access to and place the content directly into context, with
  no model decision step involved at all.

============================================================================
3. A PROMPT: A REUSABLE, SERVER-DEFINED TEMPLATE, EXPLICITLY INVOKED
============================================================================
  Rendering the PROMPT 'refund_explanation':
    'Explain, in plain language a customer would understand, why order O-1001 (status: delivered) is or is not eligible for a refund of $40.00.'

  A prompt is neither an action (a tool) nor raw data to read (a
  resource) -- it is reusable TEXT the server maintains, so that
  many different clients invoking the same prompt name get the
  same well-crafted wording, rather than each re-inventing it.

============================================================================
4. A REAL DESIGN MISTAKE: MODELING A RESOURCE AS A TOOL
============================================================================
  Modeled as a TOOL: retrieving Priya Nair's orders required
  1 explicit decision step(s): ['get_customer_orders']
    result: [{'customer': 'Priya Nair', 'amount': 40.0, 'status': 'delivered', 'order_id': 'O-1001'}, {'customer': 'Priya Nair', 'amount': 15.0, 'status': 'shipped', 'order_id': 'O-1002'}]

  Modeled as a RESOURCE: retrieving the identical data required
  0 decision steps -- a host can read it directly:
    result: [{'customer': 'Priya Nair', 'amount': 40.0, 'status': 'delivered', 'order_id': 'O-1001'}, {'customer': 'Priya Nair', 'amount': 15.0, 'status': 'shipped', 'order_id': 'O-1002'}]

  Both paths returned the SAME underlying data. The tool-based path
  forced something to explicitly plan and decide to call a function
  before the data was available at all -- for information that was
  never actually a decision, only a lookup. Modeling it as a
  resource instead removes that pointless planning step entirely.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every tool call, resource read, and prompt render above is
  genuinely executed; section 4's step-count comparison (1 decision
  step for the tool-based design versus 0 for the resource-based
  one) is a measured result of actually running both paths against
  the identical underlying data.

  ILLUSTRATIVE: this lab's URI scheme ('orders://...') is a small,
  hand-chosen convention for this lesson -- real MCP resource URIs
  follow the server's own scheme design.

  NOT SHOWN: resource subscriptions and update notifications, prompt
  arguments with their own schemas, and the full initialization/
  capability-negotiation handshake that tells a client which of the
  three primitives a specific server actually supports (M9-L05).

Done.
```

### 7.3 Reading the result

**Sections 1 through 3 establish the test, not just the label.** The distinguishing question is never "what
is this called" but "does using it require deciding arguments and a moment to act (tool), only an address to
read (resource), or a name plus fields to fill into maintained text (prompt)."

**Section 4 is where the distinction stops being academic.** The step-count difference (1 versus 0) is a
real, measured cost, not a stylistic argument — the identical data was retrieved either way, and only one of
the two designs paid a planning cost to get it.

---

## 8. Common mistakes and troubleshooting

1. **Modeling pure lookup data as a tool "for consistency" with a server's other genuine tools.** §5.4, §6 —
   this forces a real, measurable, unnecessary decision step for information that was never actually a
   decision.
2. **Treating a resource's URI as if it were an argument to reason about.** §5.2 — a resource address is
   fixed and read directly; it is not a value a decision step chooses among multiple options for.
3. **Confusing a prompt with a tool because both are "invoked by name."** §5.3 — a prompt returns text the
   server maintains; it performs no action and has no side effect of its own.
4. **Assuming every piece of server functionality must be a tool.** §6 — a server offering only lookups and
   reusable text may need no tools at all, per the definitions in §5.1–§5.3.
5. **Not measuring the actual planning-step cost when reviewing a server's primitive choices.** §6 — the
   catalog-server incident was only caught by comparing step counts across integrations, not by inspection
   alone.

| Symptom | Likely cause | Fix |
|---|---|---|
| An agent takes noticeably more planning steps per request than a comparable integration | Pure lookup data was modeled as one or more tools instead of resources | Re-model any lookup with no real decision to make as a resource, per §5.2, §5.4, §6 |
| A team debates whether a piece of server functionality should be a tool, resource, or prompt | The distinguishing question (decision+arguments vs. fixed address vs. maintained text) was never explicitly applied | Apply §5.1–§5.3's test directly to the functionality in question |
| A "tool" call never actually varies its outcome based on its arguments | The tool may actually be a resource in disguise | Check whether the call could instead be a fixed-address resource read, per §5.4 |

---

## 9. Security, privacy, reliability, cost

- **Cost/predictability.** Modeling pure lookup data as a tool forces a measurable, unnecessary planning step
  on every run that needs it — a real, avoidable cost (§5.4, §6).
- **Reliability.** A resource read by fixed address has no arguments for a decision step to get wrong; a tool
  modeling the same data introduces an unnecessary opportunity for an incorrect argument (§5.4).
- **Security.** A prompt's maintained wording is the server's own responsibility, not re-derived by each
  client — reducing the chance of inconsistent or poorly-worded client-side text (§5.3).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Define tool, resource, and prompt in your own words.
2. What distinguishes calling a tool from reading a resource, per §5.1–§5.2?
3. What does a prompt actually return, per §7.3?
4. What did §7.4 measure as the cost of modeling a resource as a tool?
5. What was the actual root cause in §6's worked example?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the step-count difference in §7.4 on your own machine.
2. Add a new resource (your choice of data) and a new prompt (your choice of template) to the lab, following
   the existing patterns.
3. Take one of your own past projects (or a hypothetical one) and classify each piece of server
   functionality it would need as a tool, resource, or prompt.
4. Modify `get_customer_orders_as_tool()` to add a genuine second argument affecting the result (e.g., a
   status filter), and explain whether it is now more correctly a tool or still better as a resource.
5. Explain, using this lesson's own test, why `apply_discount` in §6's worked example was correctly left as
   a tool.

### Exercise 3 — Challenge (~50 min)

1. Design a resource URI scheme for a new domain (your choice) that supports both a specific single record
   and a list of records, and implement both reads.
2. Design a prompt with more than one named field and at least one field that is itself a piece of data
   fetched from a resource, and implement the composition.
3. Using §6's own step-count measurement approach, design a way to detect, in a real system, when a "tool"
   is actually being called with the same effective arguments across many runs — a sign it may really be a
   resource.
4. Research (conceptually) how a real MCP client would decide which of a server's exposed prompts to surface
   to a user, and what information the server would need to provide for that to work well.
5. Using this lesson's own three-part test, audit a hypothetical system you're familiar with and identify
   any functionality that may be modeled as the wrong primitive.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l03).)*

**Q1.** Per §5.1, what does calling `issue_refund("O-1001", 40.0)` in §7.1 require?

- A. An explicit call with explicit arguments, at an explicit moment — a genuine decision to act.
- B. Only a fixed identifier, with no other arguments.
- C. No decision at all — the call happens automatically.
- D. A pre-written template filled in with named fields.

**Q2.** Per §7.2's measured result, what did reading `orders://O-1001` require?

- A. A decision between multiple possible sets of arguments.
- B. An explicit call with a chosen amount and order id.
- C. Rendering a template with named fields.
- D. Nothing but the fixed URI itself — no arguments to reason about.

**Q3.** Per §5.3, what does invoking the `refund_explanation` prompt actually return?

- A. A real refund action performed on a specific order.
- B. Server-maintained text, filled in with the supplied named fields.
- C. A list of all orders belonging to a customer.
- D. A raw data value read from a fixed URI.

**Q4.** Per §7.4's measured result, how many explicit decision steps did the tool-based design require to
retrieve Priya Nair's orders?

- A. Zero.
- B. Two.
- C. One.
- D. A number that varies randomly between runs.

**Q5.** Per §7.4's measured result, how many explicit decision steps did the resource-based design require
to retrieve the identical data?

- A. Zero — a host can read it directly with no decision step.
- B. One, the same as the tool-based design.
- C. Two, more than the tool-based design.
- D. It could not retrieve the identical data at all.

**Q6.** Per §5.4, what is the general finding this comparison demonstrates?

- A. Tools are always more efficient than resources for any kind of data.
- B. Resources and tools always require the identical number of decision steps.
- C. The choice between tool and resource has no measurable effect on planning cost.
- D. Modeling pure lookup data as a tool forces a real, measurable, unnecessary planning step.

**Q7.** Per §6's worked example, which of the catalog server's three "tools" was correctly modeled as a
tool?

- A. get_product_details.
- B. apply_discount, since it performs a genuine action requiring a real decision.
- C. get_current_promotions.
- D. All three were correctly modeled as tools.

**Q8.** Per §6, how was the catalog server's design issue actually discovered?

- A. By reading the server's source code line by line.
- B. By a customer complaint about incorrect refund amounts.
- C. By comparing planning-step counts across two otherwise-comparable integrations.
- D. By a formal MCP compliance audit.

**Q9.** Per §6's general rule, what is a strong signal that something modeled as a tool is actually a
resource?

- A. Retrieving it never required deciding between multiple possible arguments or outcomes — only an identifier to look up, or nothing at all.
- B. It has a long, detailed description.
- C. It is called frequently by the connected host.
- D. It returns a large amount of data.

**Q10.** Per §5.5, what does this lesson's lab explicitly NOT show?

- A. The distinction between a tool and a resource.
- B. The distinction between a resource and a prompt.
- C. The step-count comparison in section 4.
- D. Resource subscriptions and update notifications, prompt argument schemas, and the initialization handshake — left to later lessons.

**Q11.** Per §3.2, what is the actual test that distinguishes the three primitives, according to this
lesson?

- A. What the primitive happens to be named in the server's own code.
- B. Whether using it requires deciding arguments and a moment to act (tool), only an address to read (resource), or a name plus fields for maintained text (prompt).
- C. How many lines of code implement it.
- D. Whether it is documented in the server's README.

**Q12.** What is the general lesson of this lesson's own worked example and lab?

- A. Every piece of server functionality should be modeled as a tool for consistency.
- B. Resources and prompts are legacy concepts no longer relevant to modern MCP servers.
- C. Choosing the right primitive for a piece of functionality — tool, resource, or prompt — has a real, measurable effect on the planning cost a connected host pays to use it.
- D. The choice of primitive is purely stylistic with no practical consequence.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a teammate proposes modeling a server's
"get account balance" functionality (no arguments needed beyond an account id) as a tool. Using this
lesson, what would you recommend, and why?

---

## 12. Revision notes

- **A tool requires an explicit decision with explicit arguments at an explicit moment** — measured directly
  via `issue_refund`.
- **A resource is read by fixed address with no arguments to decide** — measured directly via reading two
  order records by URI.
- **A prompt is server-maintained, reusable text, filled in with named fields on invocation** — measured
  directly via rendering `refund_explanation`.
- **Modeling pure lookup data as a tool forces a real, measurable, unnecessary planning step** — measured
  directly: 1 decision step versus 0 for the identical underlying data.
- **The actual test is what using the primitive requires, not what it happens to be named** — the test this
  lesson's worked example applied to catch two mis-modeled "tools" in a real catalog server.

---

## 13. Completion checklist

- [ ] I can define tool, resource, and prompt precisely.
- [ ] I can explain what distinguishes calling a tool from reading a resource.
- [ ] I can explain what a prompt actually returns.
- [ ] I can identify when pure lookup data has been mis-modeled as a tool.
- [ ] I can measure the planning-step cost of a tool-vs-resource design choice.
- [ ] I can apply the three-part test to a new piece of server functionality.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M8-L03's own tool-call definition, reused unchanged in this lesson's §5.1. `[STABLE]`
- The Model Context Protocol's own definitions of tools, resources, and prompts (conceptual overview; full
  schema and negotiation details in M9-L05 and M9-L07). `[STABLE]`

---

## 15. Next lesson

→ [M9-L04 — JSON-RPC 2.0 Foundations](M9-L04-json-rpc-foundations.md) opens the message-format layer this
module's first three lessons have used in simplified form, building the real envelope MCP's messages
actually use.
