"""M11-L14 lab -- relational or key-value, and the limits that decide.
This lab computes:

  1. the same five queries against a relational schema and a DynamoDB table design,
  2. connection arithmetic: what serverless scaling does to a database's limit,
  3. DynamoDB capacity: RCU/WCU for a real workload, and the hot-partition ceiling,
  4. scan versus query: the cost of the wrong access pattern,
  5. failover and replica lag: what "highly available" actually costs you.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l14_rds_dynamodb.py
"""

from __future__ import annotations

import math
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. FIVE QUERIES, TWO DATA MODELS")

QUERIES = [
    ("get one document by id",                      "index seek",  "GetItem on the key"),
    ("list a tenant's documents, newest first",     "index seek",  "Query on PK=tenant, SK=date"),
    ("count documents per tenant per month",        "GROUP BY",    "SCAN, or a maintained counter"),
    ("find documents whose title contains a word",  "LIKE / FTS",  "SCAN, or an external index"),
    ("join documents to their ingestion runs",      "JOIN",        "denormalise at write time"),
]
print(f"  {'query':<44}{'relational':<16}{'DynamoDB':<34}")
for q, rel, dyn in QUERIES:
    print(f"  {q:<44}{rel:<16}{dyn:<34}")
hard = sum(1 for _, _, d in QUERIES if "SCAN" in d or "denormalise" in d)
print(f"\n  queries that are cheap in SQL and expensive or awkward in DynamoDB: {hard}/{len(QUERIES)}")
print("  This is the whole decision. DynamoDB is extremely fast and cheap for access")
print("  patterns you designed the KEYS around, and bad at everything else. A")
print("  relational database is adequate at everything and lets you ask a question")
print("  you did not anticipate -- which, for a system whose requirements are still")
print("  moving, is usually worth more than the performance ceiling (M14-L06).")


# ============================================================ 2
rule("2. CONNECTIONS: WHAT SERVERLESS SCALING DOES TO A DATABASE")

DB_MAX_CONNECTIONS = {"db.t4g.medium (4 GiB)": 170, "db.m6g.large (8 GiB)": 340,
                      "db.m6g.2xlarge (32 GiB)": 1365}
COMPUTE = [
    ("8 container tasks, pool of 10 each",   8, 10),
    ("40 container tasks, pool of 10 each", 40, 10),
    ("200 concurrent Lambdas, 1 each",     200,  1),
    ("800 concurrent Lambdas, 1 each",     800,  1),
]
print(f"  {'compute shape':<38}{'connections':>13}" +
      "".join(f"{k.split(' ')[0][3:]:>14}" for k in DB_MAX_CONNECTIONS))
for label, n, pool in COMPUTE:
    conns = n * pool
    row = "".join(f"{('fits' if conns <= m else 'EXHAUSTED'):>14}" for m in DB_MAX_CONNECTIONS.values())
    print(f"  {label:<38}{conns:>13}{row}")
print("\n  A database's connection limit scales with its MEMORY, and serverless compute")
print("  scales with TRAFFIC. Those two numbers are unrelated, which is why the")
print("  failure arrives as 'too many connections' during a traffic spike rather")
print("  than as slow queries. Fixes, in order: a connection proxy (RDS Proxy) so")
print("  many clients share few connections; smaller pools per task; and, for")
print("  Lambda specifically, a data API or a key-value store instead (M11-L13).")


# ============================================================ 3
rule("3. DYNAMODB CAPACITY, AND THE PARTITION CEILING")

READS_PER_S, WRITES_PER_S = 900, 400
ITEM_KB = 6
RCU_READ_KB, WCU_WRITE_KB = 4, 1
strong_rcu = math.ceil(ITEM_KB / RCU_READ_KB) * READS_PER_S
eventual_rcu = math.ceil(math.ceil(ITEM_KB / RCU_READ_KB) * READS_PER_S / 2)
wcu = math.ceil(ITEM_KB / WCU_WRITE_KB) * WRITES_PER_S
print(f"  {READS_PER_S} reads/s and {WRITES_PER_S} writes/s of {ITEM_KB} KB items\n")
print(f"  strongly consistent reads : {strong_rcu:>7,} RCU  "
      f"(ceil({ITEM_KB}/{RCU_READ_KB}) x {READS_PER_S})")
print(f"  eventually consistent     : {eventual_rcu:>7,} RCU  (half price, and usually fine)")
print(f"  writes                    : {wcu:>7,} WCU  "
      f"(ceil({ITEM_KB}/{WCU_WRITE_KB}) x {WRITES_PER_S})")
PARTITION_RCU, PARTITION_WCU = 3000, 1000
print(f"\n  per-partition ceiling: {PARTITION_RCU:,} RCU and {PARTITION_WCU:,} WCU")
KEYS = [("partition key = tenant_id, 3 big tenants", 3, 0.7),
        ("partition key = tenant_id, 400 tenants", 400, 0.08),
        ("partition key = tenant_id#day, 400 tenants", 12_000, 0.01)]
print(f"  {'key design':<44}{'partitions':>12}{'busiest share':>15}{'its WCU':>10}   verdict")
for label, parts, busiest in KEYS:
    hot_wcu = wcu * busiest
    verdict = "THROTTLES" if hot_wcu > PARTITION_WCU else "fits"
    print(f"  {label:<44}{parts:>12,}{busiest:>15.0%}{hot_wcu:>10,.0f}   {verdict}")
print("\n  Total capacity is never the problem; DISTRIBUTION is. One large tenant on")
print("  its own partition key hits the per-partition ceiling while the table as a")
print("  whole is almost idle. Design the key so traffic spreads, and remember that")
print("  the tenant with the most data is usually the one whose complaints matter")
print("  most (M10-L07).")


# ============================================================ 4
rule("4. SCAN VERSUS QUERY")

TABLE_ITEMS = 4_000_000
MATCHING = 120
print(f"  table of {TABLE_ITEMS:,} items of {ITEM_KB} KB; {MATCHING} of them match\n")
scan_rcu = math.ceil(TABLE_ITEMS * ITEM_KB / 2 / RCU_READ_KB)      # eventually consistent
query_rcu = math.ceil(MATCHING * ITEM_KB / 2 / RCU_READ_KB)
print(f"  {'operation':<40}{'items read':>14}{'RCU consumed':>15}")
print(f"  {'Scan with a filter expression':<40}{TABLE_ITEMS:>14,}{scan_rcu:>15,}")
print(f"  {'Query on a well-chosen key':<40}{MATCHING:>14,}{query_rcu:>15,}")
print(f"  {'Query on a GSI':<40}{MATCHING:>14,}{query_rcu:>15,}")
print(f"\n  ratio: {scan_rcu / query_rcu:,.0f}x more capacity for the same {MATCHING} results")
print("  A filter expression is applied AFTER the items are read and paid for. The")
print("  filter reduces what you receive, never what you are billed. If you find")
print("  yourself scanning, the access pattern was not in the key design -- add a")
print("  global secondary index, or accept that this query belongs in SQL.")


# ============================================================ 5
rule("5. WHAT 'HIGHLY AVAILABLE' ACTUALLY COSTS")

OPTIONS = [
    ("RDS single-AZ",            "none",         "restore from backup: 30-120 min", "1x"),
    ("RDS Multi-AZ instance",    "60-120 s",     "automatic failover to the standby", "2x"),
    ("RDS Multi-AZ cluster",     "under 35 s",   "failover to a readable standby",   "~2.5x"),
    ("RDS + read replicas",      "manual",       "replicas serve reads, lag in seconds", "+1x each"),
    ("DynamoDB (standard)",      "none needed",  "replicated across AZs by design",   "1x"),
]
print(f"  {'option':<28}{'failover':<16}{'behaviour':<40}{'cost':>8}")
for name, fo, behaviour, cost in OPTIONS:
    print(f"  {name:<28}{fo:<16}{behaviour:<40}{cost:>8}")
print("\n  Two points people get wrong. A Multi-AZ standby is NOT a read replica: it")
print("  exists to fail over, and (for the instance deployment) serves no traffic.")
print("  And a read replica is NOT a backup: replication faithfully copies the")
print("  DELETE you regret. Availability, read scaling and recoverability are three")
print("  separate purchases (M10-L14, M11-L17).")
print("  Failover is also not free at the application layer: connections drop, and")
print("  code that does not retry idempotently turns a 40-second failover into a")
print("  40-second outage plus a data-consistency puzzle (M8-L12).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every capacity calculation, connection count, RCU figure and ratio")
print("  above is computed from the values and the documented capacity units.")
print("\n  DOCUMENTED BEHAVIOUR: 1 RCU = one strongly consistent read of up to 4 KB per")
print("  second (or two eventually consistent); 1 WCU = one write of up to 1 KB per")
print("  second; per-partition ceilings of 3,000 RCU and 1,000 WCU; filter")
print("  expressions are applied after items are read and billed.")
print("\n  ILLUSTRATIVE: connection limits per instance class, traffic figures, tenant")
print("  distributions and failover times are approximations -- check current")
print("  documentation and measure your own.")
print("\n  NOT SHOWN: Aurora, DynamoDB on-demand pricing, global tables, transactions,")
print("  and vector search in either engine (M12-L10).")
print("\nDone.")
