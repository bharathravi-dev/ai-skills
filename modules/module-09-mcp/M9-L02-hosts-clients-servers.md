# M9-L02 — Hosts, Clients and Servers

| | |
|---|---|
| **Lesson ID** | M9-L02 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M9-L01](M9-L01-what-mcp-standardizes.md) |

---

## 1. Learning objectives

1. **Define** the three architectural roles MCP names: host, client, and server.
2. **Demonstrate** that a client holds a dedicated, one-to-one connection to exactly one server.
3. **Demonstrate** that a host owns multiple clients (one per connected server) and aggregates their tools
   into a single combined view.
4. **Diagnose** a real bug naive aggregation produces — two servers exposing an identically-named tool
   silently colliding — and apply the standard fix.
5. **Distinguish** this lesson's host/client/server structure from M8-L09's single-agent/multi-agent
   distinction, a different axis of "multiple."

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Host** | The application that owns one or more MCP clients and makes the final decision of which tool to call. |
| **Client** | A dedicated, stateful connection to exactly one MCP server, owned by a host. |
| **Server** | A process exposing tools (and other primitives) through the MCP calling convention (M9-L01). |
| **Aggregation** | A host's own act of combining multiple clients' tool catalogs into one view for its decision logic. |
| **Namespacing** | Qualifying a tool's name with its owning server's identity to prevent collisions during aggregation. |

---

## 3. Plain-language explanation

### 3.1 Three roles, cleanly separated

M9-L01 showed the *shape* of the messages traveling between a host application and a tool server. This
lesson names who is on each end of that shape, precisely: a **server** exposes tools; a **client** is one
dedicated connection to exactly one server; a **host** is the application that owns one or more clients (one
per server it connects to) and combines their tools for its own decision-making.

### 3.2 One client, one server — structurally, not just by convention

§7.2 builds a `Client` class that is constructed against exactly one `Server` and literally cannot reach any
other. This mirrors MCP's own defined relationship: a client's connection is to a single server, for the
lifetime of that connection.

### 3.3 One host, many clients — and a real collision that follows from it

§7.3 builds a `Host`-like class holding two clients, one per server, and aggregating their tools into a
single catalog. Because both servers happen to expose a tool named `get_status` (for entirely different
purposes — refund status versus shipping status), naive aggregation genuinely loses one of them. §7.4 fixes
this the standard way: namespacing every tool by the server it came from.

### 3.4 A different "multiple" than M8-L09's

M8-L09 (Single-Agent vs Multi-Agent Designs) asked when to split *decision-making* across multiple
cooperating agents. This lesson's "multiple" is different: one host, one decision-maker, connecting to
multiple *tool servers*. A single-agent design (per M8-L09) can still, and typically does, connect to many
MCP servers — the two axes are independent.

---

## 4. Analogy

**A phone with several dedicated lines, and a single receptionist who answers all of them.** Each phone line
(client) connects to exactly one outside party (server) — line 1 always rings through to the pharmacy, line
2 always to the dentist's office, permanently wired that way. The receptionist (host) is the one person
deciding, across all the lines, who to call and when — the lines themselves make no such decisions. If two
outside parties both happen to have a service called "front desk," the receptionist needs their own system
(writing down which line each "front desk" belongs to) to avoid confusing the two — the phone system itself
doesn't prevent two different businesses from choosing the same name for a department.

### Where the analogy breaks

- **A phone line is typically bidirectional and continuously open.** An MCP client's connection to a server
  has more structure to it (initialization, capability negotiation — M9-L05) than a phone line's simple
  always-on connection.
- **A receptionist would likely notice a naming collision immediately, by ear.** §7.3's `NaiveHost` shows a
  collision that is completely silent in code — nothing raises an error or a warning when one dict key
  overwrites another; it requires deliberately inspecting the aggregated catalog to notice at all.

---

## 5. Detailed technical explanation

### 5.1 A server has no awareness of clients or hosts

`[REAL, measured]` §7.1's `refund_server` and `shipping_server` are constructed and queried completely
independently. **Both happen to expose a tool literally named `get_status`**, with entirely different
meanings — an ordinary, unremarkable occurrence, since neither server was designed with the other in mind.

### 5.2 A client is structurally bound to one server

`[REAL, measured]` §7.2's `Client` class takes exactly one `Server` at construction and exposes no way to
reach any other. **`refund_client.call_tool()` only ever reaches `refund_server`**; the identical call
pattern against `shipping_client` only ever reaches `shipping_server`. This is MCP's own defined host-client
relationship made concrete: not a convention a developer might follow, but a structural property this class
enforces.

### 5.3 Naive aggregation silently loses a colliding tool

`[REAL, measured]` §7.3's `NaiveHost.aggregated_tools()` iterates every client and stores each tool under its
bare name in one flat dict. **The measured result: `{"get_status": "shipping_server", "issue_refund":
"refund_server"}`** — `refund_server`'s own `get_status` entry is gone entirely, silently overwritten because
`shipping_server` happened to be processed second. Nothing in this code raised an error; the loss is only
visible by inspecting the resulting catalog directly, exactly the discipline this course has applied
throughout.

### 5.4 Namespacing by server restores both tools

`[REAL, measured]` §7.4's `NamespacedHost` keys its aggregated catalog by `"{server_name}.{tool_name}"`
instead of the bare name. **The measured result:** both `"refund_server.get_status"` and
`"shipping_server.get_status"` appear as distinct, independently callable entries, and `fixed_host.call()`
correctly routes each to its actual owning server. Per M9-L01's own finding, this namespacing scheme is
entirely the host's own design choice — MCP's specification does not mandate any one particular scheme, only
that the host is the one responsible for making this choice at all.

### 5.5 Assumptions and limitations

- Real MCP hosts manage client connections with considerably more machinery than this lab's minimal classes
  show — connection lifecycle and capability negotiation are this module's own M9-L05 topic.
- This lesson does not cover the two MCP primitives beyond tools (resources and prompts, M9-L03), real
  transport connecting a client to a remote server (M9-L08), or authorization over which client may reach
  which server (M9-L10 through M9-L13).

---

## 6. Worked example — the support agent that lost half its refund tools

**The situation.** A team's support agent connected to two internal MCP servers: an order-management server
and a newly-added loyalty-program server. Both servers, developed by different teams, happened to expose a
tool named `get_details` — one returning order details, the other returning loyalty-account details. After
the loyalty server was added, the agent started failing to look up order details correctly on a noticeable
fraction of requests.

**Diagnosis, applying this lesson directly.** The team's host aggregated tools from all connected clients
into a single flat dict keyed by bare tool name — **exactly `NaiveHost`'s own design from §7.3**. Whichever
server's client happened to be registered last silently won the `get_details` key, and the agent's decision
step, consulting only the aggregated catalog, had no way to know the *other* server's `get_details` tool
still existed or that it was even being shadowed.

**Why this was easy to miss.** Each server's own tests passed — `order_server.get_details` worked correctly
in isolation, and so did `loyalty_server.get_details`. **The bug only existed at the aggregation layer**, a
component neither server's own team owned or tested, exactly the gap §5.3 demonstrates directly.

**Three things the team found once they inspected the aggregated catalog directly, per §5.3's own
diagnostic:**

| # | Finding | Consequence |
|---|---|---|
| 1 | The aggregation used bare tool names as dict keys | Any two connected servers sharing a tool name would silently collide |
| 2 | No test exercised the host with more than one connected server | The collision was invisible to every existing test, each of which used a single-server setup |
| 3 | The order in which servers were registered determined which tool silently won | The failure was intermittent-looking in practice, since deployment order wasn't always identical |

### The fix

**Namespace every tool by its owning server at aggregation time**, per §5.4 — exactly `NamespacedHost`'s
approach, converting a silent, order-dependent collision into two permanently distinct, correctly-routed
entries.

**Add a test that connects a host to two servers sharing a tool name deliberately**, per §5.3 — since this
class of bug is invisible to any test using only a single connected server, regardless of how well each
server is tested individually.

**The general rule.** **Aggregating multiple servers' tools under a host is the host's own responsibility,
not something either server can be blamed for or expected to prevent** — a collision is a property of the
combination, not of any one server in isolation.

---

## 7. Practical activity

**File:** [`labs/m9/l02_hosts_clients_servers.py`](../../labs/m9/l02_hosts_clients_servers.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l02_hosts_clients_servers.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A SERVER: TOOLS PLUS A HANDLER, NOTHING ELSE
============================================================================
  refund_server.list_tools()   -> [{'name': 'get_status', 'description': "Get an order's refund status."}, {'name': 'issue_refund', 'description': 'Issue a refund for an order.'}]
  shipping_server.list_tools() -> [{'name': 'get_status', 'description': "Get an order's shipping status."}]

  Two independent servers, each with its own tool catalog and its
  own handler logic -- neither aware the other exists. Notice both
  happen to expose a tool named 'get_status', with entirely
  different meanings -- ordinary, since neither server designed
  itself around the other.

============================================================================
2. A CLIENT: ONE DEDICATED CONNECTION TO EXACTLY ONE SERVER
============================================================================
  refund_client (bound to 'refund_server'):
    call_tool('get_status', {'order_id': 'O-1'}) -> {'order_id': 'O-1', 'refund_status': 'none'}
  shipping_client (bound to 'shipping_server'):
    call_tool('get_status', {'order_id': 'O-1'}) -> {'order_id': 'O-1', 'shipping_status': 'in_transit'}

  Each client is structurally bound to exactly one server at
  construction time -- refund_client has no way to reach
  shipping_server, and vice versa. This is what 'one client per
  server connection' means concretely: not a preference, a
  structural property of this class.

============================================================================
3. A HOST: OWNS MULTIPLE CLIENTS, AGGREGATES THEIR TOOLS
============================================================================
  NaiveHost owns clients for: ['refund_server', 'shipping_server']
  Naively aggregated catalog (tool name -> owning server): {'get_status': 'shipping_server', 'issue_refund': 'refund_server'}

  Only ONE 'get_status' entry survived -- shipping_server's,
  because it was processed last and silently overwrote
  refund_server's identically-named entry in the same dict key.
  A host decision step consulting this catalog has now lost all
  ability to reach refund_server's own get_status tool at all.

============================================================================
4. THE FIX: NAMESPACE EVERY TOOL BY ITS OWNING SERVER
============================================================================
  Namespaced catalog: ['refund_server.get_status', 'refund_server.issue_refund', 'shipping_server.get_status']

  fixed_host.call('refund_server.get_status', ...)   -> {'order_id': 'O-1', 'refund_status': 'none'}
  fixed_host.call('shipping_server.get_status', ...) -> {'order_id': 'O-1', 'shipping_status': 'in_transit'}

  Both servers' identically-named tools are now independently
  reachable and correctly routed -- the collision from section 3 is
  gone, not because either server changed anything, but because
  the HOST's own aggregation now preserves which server each tool
  actually came from. Per M9-L01, this aggregation and namespacing
  scheme is entirely the host's own design choice -- MCP's
  specification does not mandate any particular one.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: Server, Client, NaiveHost and NamespacedHost are genuinely
  exercised above; the collision in section 3 and its fix in
  section 4 are both measured, not asserted -- the naive catalog
  really did lose an entry, and the namespaced one really did
  preserve both.

  ILLUSTRATIVE: real MCP hosts (e.g., an IDE or chat application)
  manage client connections with considerably more machinery
  (lifecycle, capability negotiation -- M9-L05) than this lab's
  minimal classes show.

  NOT SHOWN: the three MCP primitives beyond tools -- resources and
  prompts (M9-L03); real transport connecting a client to a remote
  server (M9-L08); and any authorization over which client may
  reach which server (M9-L10 through M9-L13).

Done.
```

### 7.3 Reading the result

**Section 2's `Client` class is doing real structural work, not just naming a role.** It cannot reach any
server besides the one it was constructed with — this is the concrete difference between "a client usually
connects to one server" and "a client's connection object structurally can't reach a second one."

**Section 3's collision is the payoff of setting up two servers with an intentionally shared tool name in
section 1.** Nothing about either server is wrong; the loss happens entirely inside the host's own naive
aggregation, exactly the layer this lesson is about.

**Section 4 fixes the problem without touching either server.** This is deliberate: the collision was never
a property of `refund_server` or `shipping_server` individually, so the fix correctly lives entirely in the
host's own aggregation logic.

---

## 8. Common mistakes and troubleshooting

1. **Assuming a host only ever connects to one server.** §5.2-§5.3 — a host commonly owns many clients, one
   per connected server, and must aggregate across all of them.
2. **Assuming tool names are unique across all connected servers.** §5.3, §6 — MCP guarantees uniqueness only
   within one server's own catalog, never across independently-developed servers.
3. **Aggregating multiple servers' tools by bare name into one flat structure.** §5.3 — this is exactly the
   naive design that silently loses a colliding entry.
4. **Blaming an individual server for a collision that only exists at the aggregation layer.** §6 — the
   collision is a property of the combination, not of either server alone.
5. **Confusing this lesson's host/client/server "multiple" with M8-L09's single-agent/multi-agent
   "multiple."** §3.4 — a single decision-making agent can still connect to many MCP servers; these are
   independent design axes.

| Symptom | Likely cause | Fix |
|---|---|---|
| A tool that used to work stops being reachable after a new server is connected | Bare-name aggregation across servers silently lost it to a same-named tool on the new server | Namespace every tool by its owning server at aggregation time, per §5.4 |
| A bug only appears once a second MCP server is added to a host | The host's aggregation was never tested with more than one connected server | Add a test connecting the host to two servers with a deliberately shared tool name, per §6 |
| A team disputes which server "owns" a tool name during an integration review | Tool names are not guaranteed unique across independently-developed servers | Confirm namespacing is applied at the host's own aggregation layer, not assumed away, per §5.3-§5.4 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never aggregate multiple servers' tools by bare name alone — a same-named tool on a newly
  connected server can silently shadow an existing one (§5.3, §6).
- **Reliability.** Test a host's aggregation logic with more than one connected server sharing a tool name
  deliberately — single-server tests cannot expose this class of bug (§6).
- **Cost/predictability.** Namespacing tool names by server is inexpensive to add up front and prevents a
  class of failure that is otherwise invisible until two specific servers happen to collide (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In your own words, define host, client, and server as this lesson uses them.
2. What did §7.2 demonstrate about the relationship between a client and a server?
3. What caused the collision in §7.3?
4. How did §7.4 fix the collision without modifying either server?
5. How does this lesson's "multiple" (hosts and servers) differ from M8-L09's "multiple" (agents)?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the collision in §7.3 and its fix in §7.4 on your own machine.
2. Add a third server with a tool name that collides with one of the first two, and confirm `NaiveHost`
   loses it the same way.
3. Modify `NamespacedHost` to use a different separator (e.g., `":"` instead of `"."`), and confirm the fix
   still works.
4. Write a test that would have caught the collision in §7.3 before it reached a real aggregated catalog.
5. Explain, using this lesson's own terms, why a single-agent system (M8-L09) can still need this lesson's
   host/client/server design if it connects to more than one MCP server.

### Exercise 3 — Challenge (~50 min)

1. Design an aggregation scheme that lets a host prefer one server's tool over another's for a specific
   colliding name (rather than always namespacing), and explain the tradeoff versus always namespacing.
2. Using M8-L05's schema-validation approach, add validation to `NamespacedHost.call()` so an unknown
   namespaced name produces a clear error rather than a raw `KeyError`.
3. Research (conceptually) how a real MCP host might present an aggregated, namespaced tool catalog to a
   model for tool selection, and discuss any new risks that introduces.
4. Extend the lab with a third client whose server disconnects mid-session, and design how `NamespacedHost`
   should handle a call to a tool whose owning server is no longer reachable.
5. Using §6's worked example as a template, describe a plausible real collision between two other domains
   (not order/shipping) and walk through diagnosing and fixing it using this lesson's own method.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l02).)*

**Q1.** Per §7.1's measured result, why did both servers expose a tool named `get_status`?

- A. This was an ordinary, unremarkable occurrence — neither server was designed with the other in mind.
- B. One server copied its tool list from the other.
- C. MCP requires every server to expose a tool with this exact name.
- D. The lab's code contained a naming bug that was later fixed.

**Q2.** Per §7.2's measured result, what happens when `refund_client` attempts to reach `shipping_server`?

- A. It succeeds, since clients can reach any registered server.
- B. It requires an explicit reconfiguration step, but is otherwise possible.
- C. It raises a permission error specific to unauthorized servers.
- D. It cannot — the client is structurally bound to exactly the one server it was constructed with.

**Q3.** Per §7.3's measured result, what happened to `refund_server`'s own `get_status` entry in the
naively aggregated catalog?

- A. It was preserved under a namespaced key.
- B. It was silently lost, overwritten by `shipping_server`'s identically-named entry.
- C. It raised an error during aggregation.
- D. It was merged with `shipping_server`'s entry into a single combined tool.

**Q4.** Per §5.3, what made this collision hard to notice by looking at either server alone?

- A. Both servers actually failed their own individual tests.
- B. The collision only affected tools neither server actually used.
- C. Each server's own tests passed; the collision existed only at the aggregation layer, which neither server's team owned or tested.
- D. The lab deliberately hid the collision using randomization.

**Q5.** Per §7.4's measured result, how did `NamespacedHost` resolve the collision?

- A. By keying the aggregated catalog with `"{server_name}.{tool_name}"` instead of the bare tool name.
- B. By renaming one of the two servers' tools.
- C. By removing one of the two colliding tools entirely.
- D. By requiring the two servers to negotiate a shared name.

**Q6.** Per §5.4, who is responsible for choosing a specific namespacing or aggregation scheme, according to
MCP's own specification?

- A. MCP mandates a single specific namespacing scheme for all hosts.
- B. Each server must independently avoid all possible name collisions with any other server.
- C. The end user must manually resolve every collision at query time.
- D. The host — MCP's specification does not mandate any one particular scheme.

**Q7.** Per §6's worked example, what was the actual root cause of the support agent's intermittent failure?

- A. The order-management server had a genuine bug in its own get_details implementation.
- B. The host's aggregation used bare tool names as dict keys, so a same-named tool on the newly connected loyalty server silently won the collision.
- C. The loyalty server was never actually MCP-compliant.
- D. The agent's decision logic was rewritten incorrectly.

**Q8.** Per §6, why was this bug invisible to each server's own existing tests?

- A. The tests were run in the wrong order.
- B. The bug only appeared when the servers were tested together with real network calls.
- C. No test connected the host to more than one server with a shared tool name — the bug existed only at the aggregation layer.
- D. The existing tests were not automated.

**Q9.** Per §6's general rule, whose responsibility is a tool-name collision across servers?

- A. It's the host's own responsibility — a property of the combination, not of either server in isolation.
- B. It's always the fault of whichever server was registered second.
- C. It's always the fault of whichever server was registered first.
- D. It's unavoidable and cannot be meaningfully assigned to any party.

**Q10.** Per §3.4, how does this lesson's "multiple" (hosts and connected servers) differ from M8-L09's
"multiple" (single-agent vs multi-agent)?

- A. They are the same distinction described with different words.
- B. M8-L09's multiple agents can never connect to more than one MCP server.
- C. This lesson's host/client/server design replaces the need for M8-L09's distinction entirely.
- D. A single decision-making agent (M8-L09's single-agent design) can still connect to many MCP servers — the two are independent axes.

**Q11.** Per §5.5, what does this lesson explicitly NOT cover?

- A. The relationship between a client and a server.
- B. Resources and prompts, real network transport, and authorization over which client may reach which server — left to later lessons.
- C. The relationship between a host and multiple clients.
- D. The collision demonstrated in section 3.

**Q12.** What is the general lesson of this lesson's own worked example and lab?

- A. Servers should always avoid choosing common tool names, and hosts need not aggregate carefully.
- B. A host should never connect to more than one MCP server at a time.
- C. Tool-name uniqueness is guaranteed only within a single server's own catalog, not across independently-developed servers — a host must aggregate accordingly, typically by namespacing.
- D. Collisions between servers are a rare, purely theoretical concern not worth designing against.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is about to connect a second MCP server
to an existing host that previously talked to only one. What should you check before deploying this change,
and why?

---

## 12. Revision notes

- **A server exposes tools with no awareness of any client or host** — measured directly: two independent
  servers happened to share a tool name with no coordination between them.
- **A client is structurally bound to exactly one server** — measured directly: neither client could reach
  the other's server.
- **A host owns multiple clients and aggregates their tools for its own decision logic** — the host, not MCP
  itself, decides how that aggregation works.
- **Naive bare-name aggregation silently loses a colliding tool** — measured directly: one of two
  identically-named tools vanished from the aggregated catalog with no error raised.
- **Namespacing by owning server is the standard fix, applied entirely at the host's own aggregation layer**
  — measured directly: both colliding tools became independently reachable again.
- **This lesson's host/client/server "multiple" is a different axis than M8-L09's single-agent/multi-agent
  "multiple"** — a single agent can still connect to many servers.

---

## 13. Completion checklist

- [ ] I can define host, client, and server precisely.
- [ ] I can explain why a client is structurally bound to exactly one server.
- [ ] I can explain why a host must aggregate multiple clients' tools for its own decision logic.
- [ ] I can diagnose a bare-name aggregation collision and apply the namespacing fix.
- [ ] I can distinguish this lesson's "multiple" from M8-L09's single-agent/multi-agent distinction.
- [ ] I never assume tool names are unique across independently-developed servers.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M9-L01's own finding that MCP standardizes the calling convention, not host-side design choices like
  aggregation. `[STABLE]`
- M8-L09's single-agent vs multi-agent distinction, contrasted explicitly with this lesson's host/client/
  server structure. `[STABLE]`

---

## 15. Next lesson

→ [M9-L03 — The Three Primitives: Tools, Resources, Prompts](M9-L03-three-primitives-tools-resources-prompts.md)
names the two primitives this lesson's lab deliberately left out — resources and prompts — alongside tools,
and examines what each is actually for.
