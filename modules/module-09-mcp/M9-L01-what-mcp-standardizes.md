# M9-L01 — What MCP Standardizes — and Explicitly What It Does Not

| | |
|---|---|
| **Lesson ID** | M9-L01 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M8-L05](../module-08-agentic-ai/M8-L05-tool-schemas-argument-validation.md) |

---

## 1. Learning objectives

1. **Explain** what the Model Context Protocol (MCP) standardizes: the calling convention between a host
   application and a tool/data server.
2. **Demonstrate** that two servers in entirely unrelated domains produce identically-shaped `tools/list`
   and `tools/call` messages.
3. **Distinguish** what MCP standardizes (the envelope) from what it explicitly leaves to the host (which
   tool to call and when) and to the server (what a tool actually does).
4. **Apply** M8-L03's own tool-execution loop, unmodified, to show the decision step is entirely outside
   MCP's own specification.
5. **Diagnose**, from a described integration problem, whether it is actually a protocol-shape issue or one
   of the things MCP was never meant to standardize.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **MCP (Model Context Protocol)** | A standardized calling convention connecting a host application to external tool and data servers. |
| **Host** | The application (e.g., an agent) that connects to one or more MCP servers as a client. |
| **Server** | A process exposing tools, resources, or prompts through the MCP calling convention. |
| **Envelope** | The standardized message shape (request/response structure) a call travels in, independent of the tool it targets. |
| **Calling convention** | The fixed rules for how a call is described and invoked, as distinct from what the call actually does. |

---

## 3. Plain-language explanation

### 3.1 A protocol standardizes the shape of the conversation, not its content

MCP defines how a host discovers and calls tools — a fixed shape for listing what's available (`tools/list`)
and a fixed shape for invoking one (`tools/call`). It does not define what a specific tool does, or how a
host decides which tool to call next. Those are exactly the two things this lesson's lab isolates and shows
are left entirely outside the protocol.

### 3.2 Same shape, any domain

§7.1 shows a refund server and a weather server — two servers with nothing in common — producing structurally
identical `tools/list` responses. §7.2 shows the identical `dispatch()` function correctly invoking a tool on
either server, never needing to know anything about refunds or weather. This is the concrete meaning of
"MCP standardizes the calling convention": a client (or dispatcher) written once works against any compliant
server.

### 3.3 What is explicitly left out: the decision, and the implementation

§7.3 reuses M8-L03's own `run_tool_loop()`, completely unmodified, to show that WHICH tool gets called and
WHEN is decided by the host's own logic — a hand-written function, a full agent loop, or a fixed workflow —
none of which MCP has any opinion about. §7.4 shows two different implementations behind the identical tool
name and schema, producing two different real outcomes for the identical request — MCP standardizes the
description a client sees, not the behavior behind it.

---

## 4. Analogy

**A universal power outlet standard, not a promise about what's plugged into it.** A standardized electrical
outlet guarantees a fixed plug shape and voltage — any device built to that standard can be plugged in and
will receive power the same way, whether it's a lamp, a toaster, or a laptop charger. The standard says
nothing about what the appliance does with that power once it's on, and nothing about who in the house
decides when to plug something in and turn it on.

### Where the analogy breaks

- **An outlet does not "answer back" with a description of itself.** MCP's `tools/list` is closer to a
  labeled outlet that describes, in a fixed format, exactly what it's rated for and what plugging into it
  requires — a real difference from a bare physical socket.
- **A household appliance's behavior is usually predictable from its type.** §7.4's two `issue_refund`
  implementations show that even the identical tool *name* and *schema* can hide meaningfully different real
  behavior — a distinction with no clean electrical parallel.

---

## 5. Detailed technical explanation

### 5.1 The standardized shape of `tools/list`

`[REAL, measured]` §7.1 built `make_tools_list_response()` and called it for two unrelated tool sets — a
refund server's and a weather server's. **Both responses shared the identical envelope**: a `jsonrpc` field,
an `id`, and a `result.tools` array where every entry has exactly `name`, `description`, and `inputSchema`.
Nothing about the two servers' actual subject matter appears in the *shape* of the response — only in its
content.

### 5.2 The standardized shape of `tools/call`, and one dispatcher for both domains

`[REAL, measured]` §7.2's `dispatch()` function accepts a standardized request (`{jsonrpc, id, method:
"tools/call", params: {name, arguments}}`) and a server's own call function, and returns a standardized
response. **The identical `dispatch()` correctly handled both the refund request and the weather request**,
never once branching on which domain it was talking to. This is the operational meaning of "a client written
once works against any compliant server."

### 5.3 The decision of which tool to call is the host's, not the protocol's

`[REAL, measured]` §7.3 reused **M8-L03's own `run_tool_loop()`, completely unmodified**, feeding it tool
calls that traveled only through the standardized `tools/call` envelope built in §7.2. The loop correctly
executed `search_orders` then `issue_refund` in sequence. **The decision of which action to take next came
entirely from `decide_next_for_refund_request()`** — a plain Python function the lesson wrote, with nothing
in MCP's own specification constraining or even describing it. A host could equally have used a full
model-driven agent loop or a fixed workflow: MCP has no opinion on that choice.

### 5.4 The tool's own behavior is the server's, not the protocol's

`[REAL, measured]` §7.4 sent the identical request, `{"order_id": "O-1001", "amount": 999.0}`, to two
different implementations behind the **identical tool name and identical inputSchema**: `issue_refund_v1`
(accepts any amount unconditionally) and `issue_refund_v2` (caps the amount to the order's real total).
**The two servers returned genuinely different results** — `{"amount": 999.0}` versus `{"amount": 40.0}` —
for the exact same standardized call. MCP standardizes what a client *sees described*, not what a server
*actually does* once a call is validated and dispatched.

### 5.5 Assumptions and limitations

- This lab's JSON-RPC envelope is simplified for this lesson's specific purpose. The real JSON-RPC 2.0
  structure MCP actually uses — including error objects and notification messages — is this module's own
  M9-L04 topic, covered directly there.
- Real network transport (M9-L08), capability negotiation during initialization (M9-L05), the other two MCP
  primitives beyond tools — resources and prompts (M9-L03) — and authorization over who may call a tool at
  all (M9-L10 through M9-L13) are not shown here.

---

## 6. Worked example — the integration that "broke MCP compliance" without actually breaking anything

**The situation.** A team integrated a new MCP-compliant expense-approval server into their existing agent
host. During review, someone flagged that the server's `approve_expense` tool sometimes auto-approved
requests and sometimes required a human step, depending on the amount — and argued this was "not MCP
compliant," since the protocol documentation didn't describe any approval-tier logic.

**Why the concern was misplaced.** MCP's `tools/list` response for `approve_expense` correctly described its
`name`, `description`, and `inputSchema` — nothing about the tool's *internal* decision to sometimes require
approval is part of that description, and nothing in the protocol requires it to be. **This is precisely
§5.4's finding**: the protocol standardizes the calling convention, not the tool's own business logic. A
server is free to implement any internal behavior behind a compliant call, exactly as `issue_refund_v1` and
`issue_refund_v2` differ behind an identical schema.

**The actual, valid concern buried underneath.** The real question worth asking was different: did the
server's `inputSchema` and `description` accurately and sufficiently describe what calling `approve_expense`
could result in, so that a host integrating it could build appropriate handling (e.g., recognizing a
pending-approval response and routing it correctly)? That is a documentation-and-schema-design question,
distinct from a protocol-compliance question.

**Two things the team correctly separated once the actual issue was named:**

| # | Concern | Resolution |
|---|---|---|
| 1 | Is the server's message shape MCP-compliant? | Yes — verified directly against the standardized `tools/list` and `tools/call` envelope, per §5.1–§5.2 |
| 2 | Is the tool's own internal approval logic adequately described so a host can handle its range of possible results? | A separate, valid concern — addressed by improving the tool's description and result shape, not by relitigating protocol compliance |

### The fix

**Separate "is this MCP-compliant" from "does this tool's description tell me enough to integrate it well,"**
per §5.4 and this worked example — the first question is answered by checking the envelope shape; the second
is a design question about a specific tool's own documentation, entirely the server author's responsibility.

**The general rule.** **MCP compliance is a claim about message shape, not about what a tool does internally
or how well its behavior is documented** — two teams can build fully compliant, well-behaved servers with
completely different internal designs behind the identical protocol surface.

---

## 7. Practical activity

**File:** [`labs/m9/l01_what_mcp_standardizes.py`](../../labs/m9/l01_what_mcp_standardizes.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l01_what_mcp_standardizes.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THE STANDARDIZED SHAPE: A 'tools/list' RESPONSE
============================================================================
  A refund server's tools/list response:
    {'jsonrpc': '2.0', 'id': 1, 'result': {'tools': [{'name': 'search_orders', 'description': 'Find an order id by customer name.', 'inputSchema': {'type': 'object', 'properties': {'name': {'type': 'string'}}, 'required': ['name']}}, {'name': 'issue_refund', 'description': 'Issue a refund for an order.', 'inputSchema': {'type': 'object', 'properties': {'order_id': {'type': 'string'}, 'amount': {'type': 'number'}}, 'required': ['order_id', 'amount']}}]}}

  A completely unrelated weather server's tools/list response:
    {'jsonrpc': '2.0', 'id': 1, 'result': {'tools': [{'name': 'get_forecast', 'description': 'Get a weather forecast for a city.', 'inputSchema': {'type': 'object', 'properties': {'city': {'type': 'string'}}, 'required': ['city']}}]}}

  Both responses share the IDENTICAL envelope shape -- 'jsonrpc',
  'id', and a 'result.tools' array of {name, description, inputSchema}
  entries -- despite the two servers having nothing in common beyond
  both speaking MCP. This shared shape is exactly what the protocol
  standardizes: not what a tool does, but how any tool is DESCRIBED.

============================================================================
2. THE STANDARDIZED SHAPE: A 'tools/call' REQUEST AND RESPONSE
============================================================================
  A refund tools/call request and response:
    request:  {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'issue_refund', 'arguments': {'order_id': 'O-1001', 'amount': 40.0}}}
    response: {'jsonrpc': '2.0', 'id': 2, 'result': {'content': {'status': 'refunded', 'order_id': 'O-1001', 'amount': 40.0}}}

  A weather tools/call request and response, through the SAME dispatch():
    request:  {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'get_forecast', 'arguments': {'city': 'Austin'}}}
    response: {'jsonrpc': '2.0', 'id': 2, 'result': {'content': {'forecast': '72F, clear'}}}

  The identical dispatch() function handled both -- it never once
  needed to know anything about refunds or weather. This is the
  concrete meaning of 'MCP standardizes the calling convention': one
  generic caller works against any server that speaks the same shape.

============================================================================
3. WHAT MCP DOES NOT STANDARDIZE: WHICH TOOL TO CALL, AND WHEN
============================================================================
  Running M8-L03's own run_tool_loop(), completely unmodified, against
  tools reached only through the standardized MCP-style envelope:

    [search_orders] args={'name': 'Priya Nair'} -> result={'order_id': 'O-1001'}
    [issue_refund] args={'order_id': 'O-1001', 'amount': 40.0} -> result={'status': 'refunded', 'order_id': 'O-1001', 'amount': 40.0}

  Every call above passed through the identical standardized
  envelope from section 2 -- but WHICH tool to call, and in what
  order, came entirely from decide_next_for_refund_request(), a
  function MCP's own specification says nothing about. A host could
  have used a hand-written decision function like this one, a full
  model-driven agent loop, or a fixed workflow -- MCP standardizes
  none of that choice.

============================================================================
4. WHAT MCP DOES NOT STANDARDIZE: A TOOL'S OWN BUSINESS LOGIC
============================================================================
  A single request, {'order_id': 'O-1001', 'amount': 999.0}, sent to two different servers
  both exposing a tool literally named 'issue_refund' with the
  identical inputSchema from section 1:

    server using issue_refund_v1 -> {'status': 'refunded', 'order_id': 'O-1001', 'amount': 999.0}
    server using issue_refund_v2 -> {'status': 'refunded', 'order_id': 'O-1001', 'amount': 40.0}

  Both servers are equally valid MCP servers -- the protocol
  standardizes the NAME, the DESCRIPTION, and the INPUT SCHEMA a
  client sees, and the envelope a call travels in. It says nothing
  about what the tool actually DOES with a validated request, which
  is why the identical request produced two entirely different real
  outcomes here.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every tools/list and tools/call message above is a genuinely
  constructed dict matching the envelope MCP defines; dispatch() and
  run_tool_loop() are genuinely, identically reused across both
  domains and both refund implementations; every printed trace is a
  measured result of actually running this code.

  ILLUSTRATIVE: this lab's JSON-RPC envelope is simplified for this
  lesson's purpose -- the real JSON-RPC 2.0 structure MCP actually
  uses (including error objects and notification messages) is this
  module's own M9-L04 topic.

  NOT SHOWN: real network transport (M9-L08), capability negotiation
  during initialization (M9-L05), resources and prompts -- the other
  two MCP primitives beyond tools (M9-L03) -- and authorization over
  who may call a tool at all (M9-L10 through M9-L13).

Done.
```

### 7.3 Reading the result

**Sections 1 and 2 are the "yes, standardized" half of this lesson.** Two servers with nothing in common
produce identically-shaped messages, and one dispatcher, written without any domain knowledge, correctly
routes calls to both — the concrete, measured meaning of "a calling convention."

**Sections 3 and 4 are the "no, not standardized" half.** Reusing M8-L03's own loop *unmodified* is the
point: the loop's decision logic never had to change to work with MCP-style calls, because MCP was never the
layer responsible for that decision in the first place. Section 4's two differing `issue_refund` results from
an identical request make the same point about implementation: the schema describes the call, not the
behavior behind it.

---

## 8. Common mistakes and troubleshooting

1. **Assuming MCP compliance implies consistent or "correct" tool behavior.** §5.4, §6 — two fully compliant
   servers can implement the identical tool name and schema completely differently.
2. **Assuming MCP dictates or constrains how a host decides which tool to call.** §5.3 — that decision is
   entirely the host's own logic, unconstrained by the protocol.
3. **Treating a tool's `description` and `inputSchema` as documentation of its internal behavior.** §5.4 —
   they describe the calling interface, not what happens once a call is dispatched.
4. **Confusing a documentation gap with a protocol-compliance issue.** §6 — a tool that behaves in an
   under-described way is a design/documentation problem, not evidence of a non-compliant server.
5. **Assuming every MCP message in this lesson is the literal, complete JSON-RPC 2.0 structure.** §5.5 — this
   lab's envelope is simplified for illustration; the full structure is M9-L04's own topic.

| Symptom | Likely cause | Fix |
|---|---|---|
| Two "compliant" MCP servers exposing the same tool name behave differently | Both are legitimately compliant — MCP standardizes the call shape, not the implementation | Verify each server's actual behavior independently; don't assume compliance implies consistent behavior, per §5.4, §6 |
| A host's tool-selection logic is described as "part of the MCP integration" and blamed on the protocol | The decision logic is the host's own code, unrelated to protocol compliance | Debug the host's own decision function directly, per §5.3 |
| A team disputes whether a server is "MCP compliant" over a documentation complaint | The actual disagreement is about description quality, not message shape | Separate the two questions explicitly, per §6's worked example |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never assume a tool's behavior from its name or schema alone — verify the actual server
  implementation, since MCP does not standardize or guarantee it (§5.4).
- **Reliability.** A host's own tool-selection logic is exactly as much its own responsibility under MCP as
  it was under M8-L03's loop — MCP changes the calling convention, not who owns that decision (§5.3).
- **Cost/predictability.** Because implementation is unconstrained, integrating a new MCP server still
  requires evaluating its actual behavior, not just its declared schema — the protocol reduces integration
  friction, not verification effort (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What does MCP standardize, in one sentence?
2. Name two things MCP explicitly does not standardize, per this lesson.
3. What did §7.1 show was identical between the refund and weather servers' `tools/list` responses?
4. What in §7.3 stayed completely unmodified from M8-L03?
5. Why did the identical request in §7.4 produce two different results?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the identical envelope shapes in §7.1–§7.2 on your own machine.
2. Add a third, unrelated tool domain (your choice) and confirm `dispatch()` still requires no changes to
   handle it.
3. Write a different `decide_next` function for section 3's loop that calls the tools in a different order,
   and confirm `run_tool_loop()` still requires no changes.
4. Write a third `issue_refund` implementation with different internal behavior than v1 or v2, and confirm
   it can sit behind the identical name and schema.
5. In your own words, explain to a teammate why "the server is MCP-compliant" is not the same claim as "the
   server behaves the way we expect."

### Exercise 3 — Challenge (~50 min)

1. Design a `tools/list` entry for a genuinely different kind of tool (not refunds or weather) and its
   corresponding `tools/call` request/response pair, following this lesson's envelope shape exactly.
2. Using M8-L05's own schema-validation approach, add input validation to `dispatch()` before a call reaches
   either server's own function, and confirm it still works identically across domains.
3. Research (conceptually) how MCP's real specification structures error responses, and compare it to how
   this lab's `dispatch()` would need to change to support them.
4. Explain, using this lesson's own framing, why a security review of an MCP integration needs to examine
   both the protocol-compliance question and the tool-behavior question separately — and what a reviewer
   checking only one would miss.
5. Using §6's worked example as a template, describe a plausible real integration dispute and classify it as
   a protocol-shape question or an implementation-behavior question.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l01).)*

**Q1.** Per §7.1's measured result, what was identical between the refund server's and the weather server's
`tools/list` responses?

- A. The envelope shape — `jsonrpc`, `id`, and a `result.tools` array of `{name, description, inputSchema}` entries.
- B. Nothing was identical; the two responses had entirely different structures.
- C. The actual tool names and descriptions.
- D. The specific input values each tool accepted.

**Q2.** Per §5.2, what did `dispatch()` need to know about the domain of the tool it was calling?

- A. It needed a separate branch of logic for each domain.
- B. It needed to know the domain in advance to select the correct server.
- C. It needed to inspect the tool's description text to infer the domain.
- D. Nothing — the identical function correctly handled both the refund and weather requests.

**Q3.** Per §7.3, what determined the order in which `search_orders` and `issue_refund` were called?

- A. The MCP protocol's own specification.
- B. `decide_next_for_refund_request()`, a plain host-side function with no connection to MCP's specification.
- C. The order the tools appeared in the `tools/list` response.
- D. A random selection made by `dispatch()`.

**Q4.** Per §5.3, what does this lesson conclude about a host's choice between a hand-written decision
function, a full model-driven agent loop, or a fixed workflow?

- A. MCP requires a model-driven agent loop specifically.
- B. MCP requires a fixed workflow specifically.
- C. MCP has no opinion on that choice — it standardizes the calling convention, not the decision logic.
- D. MCP forbids using a hand-written decision function.

**Q5.** Per §7.4's measured result, what happened when the identical request was sent to `issue_refund_v1`
and `issue_refund_v2`?

- A. They produced genuinely different results — one refunded the full requested amount, the other capped it to the order's real total.
- B. They produced identical results, since both used the same tool name and schema.
- C. `issue_refund_v2` raised an exception while `issue_refund_v1` succeeded.
- D. Both requests were rejected as non-compliant.

**Q6.** Per §5.4, what does MCP's `inputSchema` actually describe?

- A. The internal business logic a tool will apply once called.
- B. Which of several possible server implementations is currently active.
- C. The order in which arguments must be validated internally.
- D. The calling interface a client sees, not what the tool does with a validated call.

**Q7.** Per §6's worked example, why was the "not MCP compliant" objection to `approve_expense` misplaced?

- A. The server's tools/list response was itself incorrectly formatted.
- B. MCP standardizes the calling convention, not a tool's own internal decision logic, so varying internal behavior does not violate compliance.
- C. The team had misread the tool's name.
- D. MCP requires every tool to behave identically regardless of input.

**Q8.** Per §6, what was the actual, valid concern once the compliance objection was set aside?

- A. There was no valid concern at all.
- B. Whether the network transport was configured correctly.
- C. Whether the tool's description and result shape adequately conveyed its range of possible outcomes to an integrating host.
- D. Whether the server's JSON-RPC version number was correct.

**Q9.** Per §6's general rule, what is MCP compliance actually a claim about?

- A. Message shape, not what a tool does internally or how well its behavior is documented.
- B. Guaranteed consistent behavior across all compliant servers.
- C. The specific programming language a server is implemented in.
- D. The business correctness of a tool's internal logic.

**Q10.** Per §5.5, what does this lesson's lab explicitly NOT show?

- A. The standardized shape of a tools/list response.
- B. The standardized shape of a tools/call request and response.
- C. That a host's decision logic is unconstrained by MCP.
- D. Real network transport, capability negotiation, resources and prompts, and authorization — left to later lessons in this module.

**Q11.** Per §5.1, what does NOT appear in the shape of a `tools/list` response, only in its content?

- A. The `jsonrpc` field.
- B. The two servers' actual differing subject matter (refunds vs. weather).
- C. The `result.tools` array structure itself.
- D. The `id` field.

**Q12.** What is the general lesson of this opening lesson of Module 9?

- A. MCP standardizes everything about how an agent behaves, including tool selection and tool implementation.
- B. MCP has no practical benefit since so much is left unstandardized.
- C. MCP standardizes only the calling convention — message shape for discovery and invocation — leaving tool-selection logic to the host and tool behavior to the server.
- D. A host's own decision logic must be rewritten specifically to work with MCP-compliant servers.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague says "once we adopt MCP, we won't need
to write or review any tool-selection logic ourselves." Using this lesson, explain what's wrong with that
claim.

---

## 12. Revision notes

- **MCP standardizes the calling convention: a fixed shape for listing tools and a fixed shape for invoking
  them** — measured directly: two unrelated servers produced identically-shaped messages.
- **One dispatcher, written without domain knowledge, correctly routes calls to any compliant server** —
  measured directly via a single `dispatch()` function handling both a refund and a weather request.
- **Which tool to call, and when, is the host's own decision — entirely outside MCP's specification** —
  measured directly: M8-L03's own loop, unmodified, worked identically against MCP-style calls.
- **What a tool actually does once called is the server's own business, not standardized by MCP** — measured
  directly: two implementations behind the identical name and schema produced different real results.
- **"MCP compliant" is a claim about message shape, not about tool behavior or its documentation quality** —
  the distinction this lesson's worked example shows a real team needed to make explicitly.

---

## 13. Completion checklist

- [ ] I can state what MCP standardizes in one sentence.
- [ ] I can name what MCP explicitly does not standardize.
- [ ] I can explain why one dispatcher can serve any compliant server.
- [ ] I can explain why a host's tool-selection logic is unaffected by adopting MCP.
- [ ] I can explain why identical tool names and schemas do not guarantee identical behavior.
- [ ] I can distinguish a protocol-compliance question from a tool-behavior or documentation question.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M8-L03's tool-execution loop, reused unmodified in this lesson's §7.3. `[STABLE]`
- M8-L05's tool schemas and argument validation, the direct prerequisite for this lesson's `inputSchema`
  discussion. `[STABLE]`
- The Model Context Protocol specification (conceptual overview; full JSON-RPC structure covered in M9-L04).
  `[STABLE]`

---

## 15. Next lesson

→ [M9-L02 — Hosts, Clients and Servers](M9-L02-hosts-clients-servers.md) names the three architectural roles
this lesson's lab left implicit — which piece of code was the host, which was acting as a client, and which
was the server — and examines how they relate.
