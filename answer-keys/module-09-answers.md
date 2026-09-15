# Module 9 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> Module 9 quiz options are uniform in length with a balanced answer distribution, and carry no inline
> explanation of the correct choice. All rationale lives here.

| Lesson | Jump to |
|---|---|
| M9-L01 What MCP Standardizes — and Explicitly What It Does Not | [↓](#m9-l01) |
| M9-L02 Hosts, Clients and Servers | [↓](#m9-l02) |

---

<a id="m9-l01"></a>
## M9-L01 — What MCP Standardizes — and Explicitly What It Does Not

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: both servers' tools/list responses shared the identical `jsonrpc`/`id`/`result.tools` envelope. **B**, **C** and **D** contradict the lab's own printed output. |
| 2 | **D** | The lab's own measured result: the identical `dispatch()` correctly handled both the refund and weather requests with no domain-specific branch. **A**, **B** and **C** contradict this measured, printed result. |
| 3 | **B** | The lab's own measured result: `decide_next_for_refund_request()`, a plain host-side function, determined the call order. **A**, **C** and **D** contradict the lab's own printed trace and code. |
| 4 | **C** | This is the lesson's own stated conclusion: MCP has no opinion on the host's choice of decision logic. **A**, **B** and **D** contradict this stated conclusion. |
| 5 | **A** | The lab's own measured result: the identical request produced $999.00 from v1 and $40.00 (capped) from v2. **B**, **C** and **D** contradict this measured, printed result. |
| 6 | **D** | The lesson states this directly: the schema describes the calling interface, not the tool's internal behavior. **A**, **B** and **C** contradict this stated distinction. |
| 7 | **B** | The worked example states this directly as the resolution of the compliance dispute. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as the actual, valid concern once compliance was confirmed. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | Section 7.5 names these specifically as not shown, deferring to later lessons in this module. **A**, **B** and **C** name things this lesson does cover directly. |
| 11 | **B** | This is the lesson's own stated point in §5.1: the two servers' differing subject matter is content, not part of the shared envelope shape. **A**, **C** and **D** name parts of the shared shape itself. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming what MCP actually standardizes**, per §5.1-§5.2 — the
calling convention (message shape for listing and invoking tools), not the logic that decides which tool to
call; **naming the decision step as the host's own responsibility**, per §5.3 and §7.3 — M8-L03's own
`run_tool_loop()` worked unmodified against MCP-style calls specifically because the decision of which tool
to call, and when, was never part of the protocol layer; **giving a concrete consequence of the
misconception**, per §5.3 — a team that skips reviewing its own tool-selection logic because "MCP handles
it" would ship an agent whose actual behavior (what it decides to call, and in what order) was never actually
checked by anyone; **connecting this to tool behavior as a second, separate gap**, per §5.4 — even a
correctly-selected tool call can produce different real outcomes depending on the server's own
implementation, a second area MCP does not cover; and **stating the corrected expectation**, per §5.1 — MCP
reduces integration friction (one calling convention for any compliant server) but does not remove the need
to design, write, and review the host's own decision logic. An answer that only says "that's wrong" without
naming the specific layer (decision logic) MCP leaves to the host scores 2.

---

<a id="m9-l02"></a>
## M9-L02 — Hosts, Clients and Servers

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lesson states this directly: two independently-developed servers sharing a tool name is ordinary, not a bug. **B**, **C** and **D** contradict the lab's own printed setup. |
| 2 | **D** | The lab's own measured result: `refund_client` is structurally bound to `refund_server` alone. **A**, **B** and **C** contradict the lab's own code and printed output. |
| 3 | **B** | The lab's own measured result: `refund_server`'s `get_status` entry vanished, silently overwritten by `shipping_server`'s. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | The lesson states this directly: each server's own tests passed, since the collision existed only at the aggregation layer neither server's team owned. **A**, **B** and **D** contradict this stated reasoning. |
| 5 | **A** | The lab's own measured result: `NamespacedHost` keys its catalog by `"{server_name}.{tool_name}"`. **B**, **C** and **D** contradict the lab's own printed code and output. |
| 6 | **D** | The lesson states this directly, per M9-L01's own finding that MCP does not mandate host-side design choices. **A**, **B** and **C** contradict this stated conclusion. |
| 7 | **B** | The worked example states this directly as the root cause, mirroring §7.3's own demonstrated collision. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly: no test exercised the host with two servers sharing a tool name. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or invent an unsupported absolute. |
| 10 | **D** | This is the lesson's own stated distinction in §3.4. **A**, **B** and **C** contradict this stated distinction. |
| 11 | **B** | Section 5.5 names these specifically as not covered, left to later lessons in this module. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **checking for tool-name collisions across the two servers
before deployment**, per §5.3-§5.4 and §6 — listing every tool each server exposes and comparing the two
lists directly, since MCP guarantees uniqueness only within one server's own catalog; **checking how the
host currently aggregates tools**, per §5.3 — specifically whether it keys by bare tool name (vulnerable, per
`NaiveHost`) or already namespaces by server (safe, per `NamespacedHost`); **testing the host with both
servers connected simultaneously, not just each individually**, per §6 — since this class of bug is invisible
to any test using only a single connected server; **proposing namespacing as the fix if bare-name aggregation
is found**, per §5.4 — qualifying every tool by its owning server before the change ships; and **explaining
why this matters even if no collision is found today**, per §5.3 — a future third server could still
introduce one, so the aggregation scheme itself, not just today's specific tool names, is what should be
made safe. An answer that only says "check for naming conflicts" without addressing the aggregation
mechanism itself scores 2.

---

*Further lessons are added to this key as Module 9 is written.*
