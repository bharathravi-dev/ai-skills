"""M11-L07 lab -- a working subnet planner, route matcher and firewall evaluator.
This lab computes:

  1. a CIDR plan: subnets per AZ, usable addresses after AWS's 5 reserved per subnet,
  2. why two VPCs with overlapping CIDRs cannot be peered, and what it costs to fix,
  3. route-table resolution by longest prefix match, over six destinations,
  4. security groups (stateful) vs network ACLs (stateless) on request AND response,
  5. security-group referencing vs CIDR rules, measured as reachable instances.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l07_vpc_subnets_security_groups.py
"""

from __future__ import annotations

import ipaddress
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


RESERVED_PER_SUBNET = 5     # AWS reserves the first four addresses and the last one

# ============================================================ 1
rule("1. A CIDR PLAN, WITH AWS'S RESERVED ADDRESSES COUNTED")

VPC = ipaddress.ip_network("10.20.0.0/16")
LAYOUT = [("public",  24), ("private-app", 22), ("private-data", 24)]
AZS = ["a", "b", "c"]
print(f"  VPC {VPC} -> {VPC.num_addresses:,} addresses\n")
print(f"  {'subnet':<26}{'CIDR':<20}{'total':>8}{'usable':>9}")
subnets, cursor = [], int(VPC.network_address)
total_usable = wasted = 0
for tier, prefix in LAYOUT:
    for az in AZS:
        size = 2 ** (32 - prefix)
        aligned = (cursor + size - 1) // size * size      # a subnet must start on its own boundary
        wasted += aligned - cursor
        net = ipaddress.ip_network((aligned, prefix))
        cursor = aligned + size
        usable = net.num_addresses - RESERVED_PER_SUBNET
        total_usable += usable
        subnets.append((f"{tier}-{az}", net))
        print(f"  {tier + '-' + az:<26}{str(net):<20}{net.num_addresses:>8,}{usable:>9,}")
used = cursor - int(VPC.network_address)
print(f"\n  allocated {used:,}/{VPC.num_addresses:,} addresses ({used / VPC.num_addresses:.0%}), "
      f"{total_usable:,} usable after reservations")
print(f"  lost to ALIGNMENT (a /22 must start on a /22 boundary): {wasted:,} addresses")
print(f"  AWS reserves {RESERVED_PER_SUBNET} addresses in EVERY subnet, so {len(subnets)} subnets lose "
      f"{len(subnets) * RESERVED_PER_SUBNET} addresses")
print("  before you launch anything. A /28 has 11 usable addresses, which is why /28")
print("  subnets run out during a rolling deployment rather than at steady state.")


# ============================================================ 2
rule("2. WHY THESE TWO VPCs CANNOT BE PEERED")

OURS = ipaddress.ip_network("10.20.0.0/16")
OTHERS = {
    "partner A (default template)": ipaddress.ip_network("10.0.0.0/16"),
    "acquired company":             ipaddress.ip_network("10.20.0.0/16"),
    "our own second region":        ipaddress.ip_network("10.20.128.0/17"),
    "well-planned partner B":       ipaddress.ip_network("10.60.0.0/16"),
}
print(f"  our VPC: {OURS}\n")
print(f"  {'the other side':<32}{'their CIDR':<18}{'overlaps?':>11}   consequence")
for name, net in OTHERS.items():
    ov = OURS.overlaps(net)
    consequence = "peering impossible without re-addressing" if ov else "peering fine"
    print(f"  {name:<32}{str(net):<18}{('YES' if ov else 'no'):>11}   {consequence}")
print("\n  Row 3 is the one teams inflict on themselves: a second environment carved")
print("  from inside the first VPC's range. Address space is the one decision you")
print("  cannot change without rebuilding, so allocate from a central plan with room")
print("  for regions, environments and companies you have not acquired yet.")


# ============================================================ 3
rule("3. ROUTE TABLES RESOLVE BY LONGEST PREFIX MATCH")

ROUTES = [
    ("10.20.0.0/16",   "local"),
    ("10.20.16.0/22",  "vpc-endpoint (S3 gateway)"),
    ("10.60.0.0/16",   "pcx-partner-b (peering)"),
    ("0.0.0.0/0",      "nat-gateway"),
]
DESTS = ["10.20.3.14", "10.20.17.9", "10.60.2.200", "52.95.110.1", "10.99.0.5", "169.254.169.254"]
print(f"  {'route':<18}target")
for cidr, target in ROUTES:
    print(f"  {cidr:<18}{target}")
print()
print(f"  {'destination':<20}{'matched route':<18}{'target':<34}prefix")
for d in DESTS:
    ip = ipaddress.ip_address(d)
    best, best_len = None, -1
    for cidr, target in ROUTES:
        net = ipaddress.ip_network(cidr)
        if ip in net and net.prefixlen > best_len:
            best, best_len = (cidr, target), net.prefixlen
    if d == "169.254.169.254":
        print(f"  {d:<20}{'(link-local)':<18}{'instance metadata, never routed':<34}--")
    else:
        print(f"  {d:<20}{best[0]:<18}{best[1]:<34}/{best_len}")
print("\n  The most specific route wins, always. Adding a /22 for an endpoint silently")
print("  changes where a subset of traffic goes -- which is how a 'no change to the")
print("  network' deploy stops reaching a service (M11-L08).")


# ============================================================ 4
rule("4. STATEFUL SECURITY GROUP VS STATELESS NETWORK ACL")

SG_INBOUND = [("tcp", 443, "10.20.0.0/16")]
SG_OUTBOUND = [("tcp", 0, "0.0.0.0/0")]          # 0 = any port
NACL_INBOUND = [(100, "allow", "tcp", (443, 443), "10.20.0.0/16"),
                (32767, "deny", "all", (0, 65535), "0.0.0.0/0")]
NACL_OUTBOUND_BROKEN = [(100, "allow", "tcp", (443, 443), "0.0.0.0/0"),
                        (32767, "deny", "all", (0, 65535), "0.0.0.0/0")]
NACL_OUTBOUND_FIXED = [(100, "allow", "tcp", (443, 443), "0.0.0.0/0"),
                       (110, "allow", "tcp", (1024, 65535), "0.0.0.0/0"),
                       (32767, "deny", "all", (0, 65535), "0.0.0.0/0")]


def nacl_allows(rules, port: int) -> bool:
    for _, effect, _proto, (lo, hi), _cidr in sorted(rules):
        if lo <= port <= hi:
            return effect == "allow"
    return False


FLOWS = [("inbound request", 443), ("outbound response", 49512)]
print("  a client at 10.20.3.14 calls an instance on tcp/443; the response returns")
print("  from the instance to the client's EPHEMERAL port 49512\n")
print(f"  {'flow':<24}{'port':>7}{'security group':>21}{'NACL (broken)':>16}{'NACL (fixed)':>15}")
for label, port in FLOWS:
    inbound = port == 443
    sg = "allowed" if inbound else "allowed (stateful)"
    broken_rules = NACL_INBOUND if inbound else NACL_OUTBOUND_BROKEN
    fixed_rules = NACL_INBOUND if inbound else NACL_OUTBOUND_FIXED
    nb = "allowed" if nacl_allows(broken_rules, port) else "DROPPED"
    nf = "allowed" if nacl_allows(fixed_rules, port) else "DROPPED"
    print(f"  {label:<24}{port:>7}{sg:>21}{nb:>16}{nf:>15}")
print("\n  The security group remembers the request, so the response is allowed without")
print("  any outbound rule matching port 49512. A network ACL remembers NOTHING, so")
print("  the response needs its OWN rule for the ephemeral range 1024-65535.")
print("  This is the single most common NACL bug: connections that open and hang.")
print("  Security groups also have NO deny rules -- everything not allowed is denied.")


# ============================================================ 5
rule("5. SG-REFERENCING VS CIDR RULES: WHAT CAN REACH THE DATABASE?")

FLEET = {"app servers (sg-app)": 12, "batch workers (sg-batch)": 6, "bastion (sg-bastion)": 1,
         "analytics (sg-analytics)": 4, "anything else in 10.20.0.0/16": 240}
RULES = {
    "source = 10.20.0.0/16 (the whole VPC)": list(FLEET),
    "source = 10.20.16.0/22 (the app subnet)": ["app servers (sg-app)", "batch workers (sg-batch)",
                                                "anything else in 10.20.0.0/16"],
    "source = sg-app (security group reference)": ["app servers (sg-app)"],
}
print(f"  {'database inbound rule':<44}{'reachable hosts':>17}   who")
for label, groups in RULES.items():
    n = sum(FLEET[g] for g in groups)
    who = ", ".join(g.split(' (')[0] for g in groups)
    print(f"  {label:<44}{n:>17}   {who[:34]}")
print("\n  A CIDR rule grants access to an ADDRESS RANGE, which means to anything that")
print("  ever gets an address in it -- including the instance someone launches next")
print("  month. A security-group reference grants access to a ROLE, and the set")
print("  updates itself. Prefer SG references inside the VPC (M10-L07).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every subnet calculation, overlap test, longest-prefix match, firewall")
print("  verdict and host count above is computed by this script, using Python's")
print("  ipaddress module for the addressing arithmetic.")
print("\n  VERIFIED BEHAVIOUR: AWS reserves 5 addresses per subnet; routes resolve by")
print("  longest prefix match; security groups are stateful and allow-only; network")
print("  ACLs are stateless, numbered, and evaluated in order with allow and deny.")
print("\n  ILLUSTRATIVE: the CIDR plan, fleet sizes and rule sets are invented.")
print("\n  NOT SHOWN: Transit Gateway, IPv6, PrivateLink, Network Firewall and")
print("  flow-log analysis (M11-L08, M11-L16).")
print("\nDone.")
