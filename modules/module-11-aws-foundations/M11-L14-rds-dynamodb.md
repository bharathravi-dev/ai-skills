# M11-L14 — RDS and DynamoDB

| | |
|---|---|
| **Lesson ID** | M11-L14 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M2-L16](../module-02-python-foundations/M2-L16-sql-databases.md), [M11-L13](M11-L13-lambda-api-gateway.md) |

---

## 1. Learning objectives

1. **Choose** between relational and key-value from the *access patterns you can and cannot anticipate*.
2. **Compute** connection demand from compute scaling, and recognise the limit before it is hit.
3. **Size** DynamoDB capacity in RCU and WCU, and check the **per-partition** ceiling, not just the total.
4. **Explain** why a filter expression does not reduce cost, and when a scan means a design error.
5. **Separate** availability, read scaling and recoverability — three different purchases.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **RDS** | Managed relational database (PostgreSQL, MySQL and others). |
| **DynamoDB** | Managed key-value and document store with per-partition throughput limits. |
| **Partition key** | The attribute DynamoDB hashes to place an item; it decides distribution. |
| **Sort key** | The second key attribute, giving ordered access within a partition. |
| **RCU / WCU** | Read and write capacity units: 1 RCU = one strongly consistent read of up to 4 KB per second (or two eventually consistent); 1 WCU = one write of up to 1 KB per second. |
| **GSI** | Global secondary index — an alternative key structure over the same items. |
| **Scan** | Reading every item in a table; filters apply *after* reading and billing. |
| **Hot partition** | A partition receiving disproportionate traffic and hitting its own ceiling. |
| **RDS Proxy** | A managed connection pool between many clients and one database. |
| **Read replica** | An asynchronously replicated copy that serves reads; **not a backup**. |

---

## 3. Plain-language explanation

### 3.1 The decision is about the queries you have not thought of yet

§7.1 runs five queries against both models. Two are trivial in either. The other **3 of 5** — grouped counts, text search,
joins — are cheap in SQL and require a scan, a maintained counter, an external index or denormalisation in DynamoDB.

DynamoDB is extremely fast and cheap for access patterns you designed the **keys** around, and poor at everything else. A
relational database is adequate at everything and lets you ask a question you did not anticipate. For a system whose
requirements are still moving, that flexibility usually beats the performance ceiling.

### 3.2 Connection limits are set by memory; scaling is set by traffic

§7.2: 40 container tasks with pools of 10 need **400 connections** — more than a `db.m6g.large` allows. 800 concurrent
Lambdas need **800**. The database's limit scales with its **memory**; your compute scales with **traffic**. The two are
unrelated, which is why the failure arrives as "too many connections" during a spike rather than as slow queries.

### 3.3 Total capacity is never the problem; distribution is

§7.3: 900 reads/s and 400 writes/s of 6 KB items need **1,800 RCU** (or **900** eventually consistent) and **2,400 WCU**.
Against a per-partition ceiling of **3,000 RCU / 1,000 WCU**, a key of `tenant_id` with three large tenants puts
**1,680 WCU** on one partition — **throttled**, while the table as a whole is almost idle. Adding the day to the key
spreads it to **24**.

### 3.4 A filter does not reduce what you pay

§7.4: finding 120 matching items among 4 million costs **3,000,000 RCU** by scan and **90 RCU** by query — **33,333×**.
The filter reduces what you *receive*, never what you are *billed*.

### 3.5 Availability, read scaling and backup are three different things

§7.5: a Multi-AZ standby exists to fail over and (for the instance deployment) serves no traffic — it is not a read
replica. A read replica faithfully copies the `DELETE` you regret — it is not a backup.

---

## 4. Analogy

**A filing system versus a card index.** A card index sorted by customer number finds a customer instantly and is useless
for "which customers ordered in March" unless you built a second index at the time. A general filing room is slower for
everything and can answer a question nobody anticipated. The room also has a fixed number of desks (connections): however
many clerks you hire, only so many can work at once. And a duplicate copy of the index kept in the next room protects you
from a fire, not from someone correctly copying an erroneous card.

### Where the analogy breaks

- **A card index's cost is uniform; DynamoDB's is per partition**, so one very busy customer can throttle while the
  system is idle (§5.4).
- **Clerks queue politely; connection exhaustion fails immediately**, and usually at the worst moment (§5.3).

---

## 5. Detailed technical explanation

### 5.1 Choosing

| Choose relational (RDS/Aurora) when | Choose DynamoDB when |
|---|---|
| Access patterns are still changing | Access patterns are known and few |
| You need joins, aggregates, ad-hoc queries | You need single-digit-millisecond key lookups at any scale |
| Transactions across several entities are natural | Items are self-contained |
| The team already knows SQL | Operational simplicity and automatic scaling matter more |
| You want `pgvector` beside your data (M6-L08, M12-L10) | Traffic is spiky and you want per-request billing |

For most AI applications the state is small and the queries are unpredictable: **start relational**. Reach for DynamoDB
for the specific things it is excellent at — session state, idempotency keys (M8-L12), rate-limit counters, job status,
event deduplication.

### 5.2 Modelling

`[REAL, compared]` §7.1 — 3 of 5 queries awkward in DynamoDB.

In DynamoDB, **design the keys from the access patterns**, in writing, before the table exists:

```text
PK = TENANT#t_14              SK = DOC#2026-09-17#d_991     -> a tenant's docs, newest first
PK = DOC#d_991                SK = META                     -> one document by id
PK = TENANT#t_14              SK = RUN#2026-09-17#r_22      -> ingestion runs in the same partition
GSI1PK = STATUS#failed        GSI1SK = 2026-09-17T10:22Z    -> failed items across tenants
```

If a required pattern has no key that serves it, you have found either a GSI to add or a query that belongs in SQL.

### 5.3 Connections

`[REAL, computed — ILLUSTRATIVE limits]` §7.2.

```text
connections ≈ concurrent_compute_units × pool_size_per_unit
```

Remedies, in order of preference:

1. **RDS Proxy** (or an equivalent pooler): many clients share few database connections, and it survives failover more
   gracefully than raw clients.
2. **Smaller pools per task**, sized from measured concurrency per task rather than a library default.
3. **Fewer, larger compute units** — a container holding a pool beats 200 Lambdas holding one each.
4. **A different store** for the high-fan-out path: DynamoDB has no connection limit in this sense.

Alarm on connection count as a percentage of the limit, not on errors — by the time it errors, users are affected (L16).

### 5.4 DynamoDB capacity

`[REAL, computed]` §7.3.

```text
RCU (strong)   = ceil(item_KB / 4)  × reads_per_second
RCU (eventual) = that / 2
WCU            = ceil(item_KB / 1)  × writes_per_second
per partition  ≤ 3,000 RCU and 1,000 WCU
```

Two design consequences. **Item size is multiplied by every read**, so storing a large blob in an item is expensive —
put it in S3 and keep a pointer (L10). And the **partition key must spread traffic**: add a dimension (date, shard
number) when one key value dominates, and remember that adaptive capacity helps but does not remove the ceiling.

On-demand capacity removes the sizing exercise and costs more per request; provisioned with autoscaling is cheaper for
steady load. The partition ceiling applies either way.

### 5.5 Scan versus query

`[REAL, computed]` §7.4 — 33,333×.

A `Scan` reads every item and bills for every item; the `FilterExpression` is applied afterwards. A `Query` reads only the
items under a key. If you are scanning in a request path, the design missed a pattern: add a GSI, maintain a
denormalised item, or move that query to SQL.

The same logic is why **counting** is awkward: there is no cheap `COUNT(*)`. Maintain a counter item as you write, and
accept the extra write.

### 5.6 Availability, replicas and backups

`[REAL, compared — ILLUSTRATIVE timings]` §7.5.

| Purpose | Mechanism | Not to be confused with |
|---|---|---|
| Survive an AZ failure | Multi-AZ deployment | Read scaling |
| Scale reads | Read replicas | Availability or backup |
| Recover from a mistake | Backups, snapshots, point-in-time restore | Replication |
| Recover from region loss | Cross-region replica or copied snapshots | Multi-AZ |

Failover is not free at the application layer: connections drop, and code that does not **retry idempotently** turns a
40-second failover into a 40-second outage plus a consistency puzzle (M8-L12, M8-L13). Test failover deliberately
(M10-L14).

For DynamoDB, point-in-time recovery is a switch and should be on for anything that matters; deletion protection likewise.

### 5.7 What AI systems actually need this for

| Data | Store | Why |
|---|---|---|
| Documents and chunks | S3 + a vector index | Large, immutable, retrieved by similarity (M12-L10) |
| Chunk metadata, tenancy, permissions | Relational | Joins, filters, ad-hoc questions (M7-L15) |
| Conversation state | DynamoDB or relational | Key lookup by session; small items (M8-L06) |
| Idempotency keys, job status | DynamoDB | Exactly the pattern it is best at (M8-L12) |
| Evaluation results and run records | Relational | You will ask unanticipated questions of these (M10-L13) |

### 5.8 Assumptions and limitations

- Connection limits per instance class, traffic figures, tenant distributions and failover times are approximations.
- Capacity-unit definitions and per-partition ceilings are as documented; verify current values.
- Aurora, global tables, transactions, on-demand pricing detail and vector search are out of scope (M12-L10).

---

## 6. Worked example — the table that throttled while the graph showed 6% utilisation

**The situation.** A document-processing pipeline wrote status items to DynamoDB, keyed by `tenant_id`. Provisioned
capacity was set from total throughput with generous headroom. Utilisation graphs showed about 6%.

**What happened.**

1. The three largest tenants generated roughly **70%** of writes. Each tenant was one partition key, so one partition
   received 70% of a 2,400 WCU workload — **1,680 WCU against a 1,000 ceiling** (§7.3).
2. Writes to those tenants were **throttled**; writes for everyone else succeeded. The table-level graph, averaging across
   partitions, showed 6% (§5.4).
3. The pipeline retried on throttling without backoff, amplifying the load (M8-L13).
4. The affected tenants were the largest customers — the L08 slice problem in a different layer (M10-L08).
5. The fix was a key of `tenant_id#date`, spreading each tenant across days, plus exponential backoff.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Capacity sized from totals | Size per partition; model the busiest key |
| 2 | Table-level metrics hid it | Alarm on `ThrottledRequests`, not utilisation |
| 3 | Retries without backoff | Exponential backoff with jitter (M8-L13) |
| 4 | Largest tenants worst affected | Treat tenant skew as a slice (M10-L08) |
| 5 | Key chosen from the entity, not the traffic | Design keys from access patterns and volume |

**The general rule.** **In DynamoDB, average utilisation tells you nothing. Model the busiest partition.**

---

## 7. Practical activity

**File:** [`labs/m11/l14_rds_dynamodb.py`](../../labs/m11/l14_rds_dynamodb.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic.

```bash
source .venv/bin/activate
python labs/m11/l14_rds_dynamodb.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. FIVE QUERIES, TWO DATA MODELS
============================================================================
  query                                       relational      DynamoDB                          
  get one document by id                      index seek      GetItem on the key                
  list a tenant's documents, newest first     index seek      Query on PK=tenant, SK=date       
  count documents per tenant per month        GROUP BY        SCAN, or a maintained counter     
  find documents whose title contains a word  LIKE / FTS      SCAN, or an external index        
  join documents to their ingestion runs      JOIN            denormalise at write time         

  queries that are cheap in SQL and expensive or awkward in DynamoDB: 3/5
  This is the whole decision. DynamoDB is extremely fast and cheap for access
  patterns you designed the KEYS around, and bad at everything else. A
  relational database is adequate at everything and lets you ask a question
  you did not anticipate -- which, for a system whose requirements are still
  moving, is usually worth more than the performance ceiling (M14-L06).

============================================================================
2. CONNECTIONS: WHAT SERVERLESS SCALING DOES TO A DATABASE
============================================================================
  compute shape                           connections    t4g.medium     m6g.large   m6g.2xlarge
  8 container tasks, pool of 10 each               80          fits          fits          fits
  40 container tasks, pool of 10 each             400     EXHAUSTED     EXHAUSTED          fits
  200 concurrent Lambdas, 1 each                  200     EXHAUSTED          fits          fits
  800 concurrent Lambdas, 1 each                  800     EXHAUSTED     EXHAUSTED          fits

  A database's connection limit scales with its MEMORY, and serverless compute
  scales with TRAFFIC. Those two numbers are unrelated, which is why the
  failure arrives as 'too many connections' during a traffic spike rather
  than as slow queries. Fixes, in order: a connection proxy (RDS Proxy) so
  many clients share few connections; smaller pools per task; and, for
  Lambda specifically, a data API or a key-value store instead (M11-L13).

============================================================================
3. DYNAMODB CAPACITY, AND THE PARTITION CEILING
============================================================================
  900 reads/s and 400 writes/s of 6 KB items

  strongly consistent reads :   1,800 RCU  (ceil(6/4) x 900)
  eventually consistent     :     900 RCU  (half price, and usually fine)
  writes                    :   2,400 WCU  (ceil(6/1) x 400)

  per-partition ceiling: 3,000 RCU and 1,000 WCU
  key design                                    partitions  busiest share   its WCU   verdict
  partition key = tenant_id, 3 big tenants               3            70%     1,680   THROTTLES
  partition key = tenant_id, 400 tenants               400             8%       192   fits
  partition key = tenant_id#day, 400 tenants        12,000             1%        24   fits

  Total capacity is never the problem; DISTRIBUTION is. One large tenant on
  its own partition key hits the per-partition ceiling while the table as a
  whole is almost idle. Design the key so traffic spreads, and remember that
  the tenant with the most data is usually the one whose complaints matter
  most (M10-L07).

============================================================================
4. SCAN VERSUS QUERY
============================================================================
  table of 4,000,000 items of 6 KB; 120 of them match

  operation                                   items read   RCU consumed
  Scan with a filter expression                4,000,000      3,000,000
  Query on a well-chosen key                         120             90
  Query on a GSI                                     120             90

  ratio: 33,333x more capacity for the same 120 results
  A filter expression is applied AFTER the items are read and paid for. The
  filter reduces what you receive, never what you are billed. If you find
  yourself scanning, the access pattern was not in the key design -- add a
  global secondary index, or accept that this query belongs in SQL.

============================================================================
5. WHAT 'HIGHLY AVAILABLE' ACTUALLY COSTS
============================================================================
  option                      failover        behaviour                                   cost
  RDS single-AZ               none            restore from backup: 30-120 min               1x
  RDS Multi-AZ instance       60-120 s        automatic failover to the standby             2x
  RDS Multi-AZ cluster        under 35 s      failover to a readable standby             ~2.5x
  RDS + read replicas         manual          replicas serve reads, lag in seconds    +1x each
  DynamoDB (standard)         none needed     replicated across AZs by design               1x

  Two points people get wrong. A Multi-AZ standby is NOT a read replica: it
  exists to fail over, and (for the instance deployment) serves no traffic.
  And a read replica is NOT a backup: replication faithfully copies the
  DELETE you regret. Availability, read scaling and recoverability are three
  separate purchases (M10-L14, M11-L17).
  Failover is also not free at the application layer: connections drop, and
  code that does not retry idempotently turns a 40-second failover into a
  40-second outage plus a data-consistency puzzle (M8-L12).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every capacity calculation, connection count, RCU figure and ratio
  above is computed from the values and the documented capacity units.

  DOCUMENTED BEHAVIOUR: 1 RCU = one strongly consistent read of up to 4 KB per
  second (or two eventually consistent); 1 WCU = one write of up to 1 KB per
  second; per-partition ceilings of 3,000 RCU and 1,000 WCU; filter
  expressions are applied after items are read and billed.

  ILLUSTRATIVE: connection limits per instance class, traffic figures, tenant
  distributions and failover times are approximations -- check current
  documentation and measure your own.

  NOT SHOWN: Aurora, DynamoDB on-demand pricing, global tables, transactions,
  and vector search in either engine (M12-L10).

Done.
```

### 7.3 Reading the result

**Section 1's count** — 3 of 5 — is the design decision in one number.

**Section 2's bottom row** is what serverless does to a database that was fine last month.

**Section 3's first key design** throttles at 70% share while the table is idle. That is the hot-partition failure.

**Section 4's ratio** is why "just add a filter" is not an optimisation.

---

## 8. Common mistakes and troubleshooting

1. **Choosing DynamoDB for a system whose queries are still changing.** §5.1.
2. **Sizing capacity from totals.** §5.4 — model the busiest partition.
3. **A partition key with a dominant value.** §7.3 — add a dimension.
4. **Scanning with a filter in a request path.** §7.4 — 33,333×.
5. **Large blobs in items.** Item size multiplies every read; use S3 with a pointer.
6. **Default connection pools with serverless compute.** §7.2 — compute the product.
7. **Treating a read replica as a backup.** §5.6 — it replicates your mistakes.
8. **Treating a Multi-AZ standby as a read replica.** §5.6.
9. **No idempotent retry across failover.** §5.6 — a 40-second failover becomes an outage.

| Symptom | Likely cause | Fix |
|---|---|---|
| "Too many connections" during spikes | Compute scaled past the connection limit | RDS Proxy; smaller pools; fewer units |
| Throttling with low reported utilisation | Hot partition | Re-key to spread; alarm on throttles |
| DynamoDB costs far above the estimate | Scans, or large items | Add a GSI; move blobs to S3 |
| Reads fail during maintenance | Single-AZ, or replicas not used for reads | Multi-AZ; route reads deliberately |
| Data deleted in error is gone from the replica too | Replica used as a backup | Point-in-time restore; snapshots (L17) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Databases live in private subnets, reachable only from the application's security group (L07); IAM
  authentication removes a password to manage (L17).
- **Privacy.** Encrypt at rest with a customer-managed key; deletion must reach replicas, snapshots and backups
  (M10-L06, L10).
- **Reliability.** Multi-AZ plus idempotent retries; test failover rather than assuming it (M10-L14).
- **Cost.** DynamoDB cost is dominated by item size and access pattern; RDS by instance size and Multi-AZ. Both reward
  measuring before scaling up (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which of the five queries in §7.1 require a scan or denormalisation?
2. How many connections do 40 tasks with pools of 10 need?
3. Compute the WCU for 400 writes/s of 6 KB items.
4. Why did the `tenant_id` key design throttle?
5. What is the RCU ratio between the scan and the query in §7.4?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the item size to 1 KB and recompute the capacity.
2. Add a fourth key design to §7.3 that shards a large tenant across ten suffixes.
3. Add your own compute shape to §7.2 and check it against each instance class.
4. Write the DynamoDB key design for conversation state with per-tenant listing.
5. Decide, with reasons, which of your system's data belongs in each store (§5.7).

### Exercise 3 — Challenge (~60 min)

1. Write the access-pattern document for one service, then the key design that serves every pattern.
2. Compute your real connection demand at peak and design the pooling to match.
3. Add throttle and connection-utilisation alarms with thresholds from your own maths (L16).
4. Test a Multi-AZ failover in a non-production environment and measure the application-visible impact.
5. Write the idempotent retry wrapper your data layer needs to survive a failover (M8-L12, M8-L13).

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l14).)*

**Q1.** What is the main argument for a relational database in a system whose requirements are still moving?

- A. It scales to higher throughput than key-value stores
- B. It answers questions you did not anticipate when designing the schema
- C. It has no connection limit
- D. It provides stronger encryption options

**Q2.** In §7.1, how many of the five queries were awkward or expensive in DynamoDB?

- A. One
- B. Two
- C. Three
- D. Five

**Q3.** What determines a relational database's connection limit?

- A. The number of client applications registered
- B. The network bandwidth of the instance
- C. The configured maximum concurrency of the VPC
- D. Largely the instance's memory

**Q4.** Why does serverless compute break connection assumptions?

- A. Compute scales with traffic, while the limit scales with database memory
- B. Each invocation opens a TLS session that counts double
- C. Serverless runtimes cannot pool connections at all
- D. Connections from ephemeral addresses are rejected

**Q5.** How many WCU does 400 writes/second of 6 KB items consume?

- A. 400
- B. 600
- C. 1,000
- D. 2,400

**Q6.** What is the per-partition write ceiling in DynamoDB?

- A. 1,000 WCU
- B. 3,000 WCU
- C. 40,000 WCU
- D. There is no per-partition ceiling

**Q7.** A table shows 6% utilisation and requests are throttled. What is the likely cause?

- A. Provisioned capacity was set too low overall
- B. Eventually consistent reads are being used
- C. One partition is receiving a disproportionate share of traffic
- D. The metric is averaged over a five-minute period

**Q8.** What does a `FilterExpression` on a `Scan` reduce?

- A. The capacity consumed
- B. The items returned, not the items read and billed
- C. The number of partitions accessed
- D. Both items read and items returned

**Q9.** In §7.4, how much more capacity did the scan consume than the query?

- A. About 100×
- B. About 1,000×
- C. About 33,000×
- D. About 4,000,000×

**Q10.** What is a read replica *not* suitable for?

- A. Serving read traffic
- B. Reducing load on the primary
- C. Reporting queries that tolerate lag
- D. Recovering from an accidental delete

**Q11.** What does a Multi-AZ instance standby do in normal operation?

- A. Serves read traffic to reduce primary load
- B. Nothing user-visible; it exists to fail over
- C. Stores point-in-time backups
- D. Handles write traffic for the other AZ

**Q12.** What must application code do to survive a failover gracefully?

- A. Retry idempotently, since connections drop
- B. Cache writes locally until the primary returns
- C. Increase connection pool size during failover
- D. Switch to the read replica automatically

**Q13.** *(Written, rubric-graded.)* In under 150 words: a team proposes DynamoDB for the metadata behind a RAG system —
documents, chunks, tenants, permissions and evaluation runs. Give your assessment and what you would put where.

---

## 12. Revision notes

- **Relational for unanticipated questions**; DynamoDB for patterns you designed the keys around. **3 of 5** lab queries
  were awkward in DynamoDB.
- **`connections ≈ compute_units × pool_size`**: 40 tasks × 10 = **400**; 800 Lambdas = **800**. Use RDS Proxy.
- **Capacity**: `ceil(KB/4) × reads` (halved if eventually consistent), `ceil(KB/1) × writes`. 900 r/s + 400 w/s of 6 KB →
  **1,800 RCU / 2,400 WCU**.
- **Per partition: 3,000 RCU, 1,000 WCU.** A 70% key share → **1,680 WCU → throttled** while the table shows 6%.
- **Scan vs query: 33,333×.** Filters reduce what you receive, not what you pay.
- **Three separate purchases**: Multi-AZ (availability), replicas (read scale), backups (recoverability).

---

## 13. Completion checklist

- [ ] I chose the store from the access patterns, including the ones I cannot yet name.
- [ ] I have computed peak connection demand and have pooling that fits it.
- [ ] DynamoDB capacity is modelled per partition, not just in total, and throttles are alarmed.
- [ ] No request path performs a scan.
- [ ] Availability, read scaling and backups are separate, deliberate choices.
- [ ] Data-layer calls retry idempotently across a failover.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon DynamoDB Developer Guide — read/write capacity units, partition throughput limits, scans and filter expressions,
  global secondary indexes, point-in-time recovery `[STABLE — verify current limits]`
- Amazon RDS User Guide — Multi-AZ deployments, read replicas, RDS Proxy, automated backups and point-in-time restore `[STABLE]`
- M2-L16 (SQL and database fundamentals) and M6-L08 (`pgvector` beside your data) `[STABLE]`
- M8-L12 (idempotency) and M8-L13 (retries and backoff) — what makes failover survivable `[STABLE]`
- M12-L10 (vector-store choices on AWS) and M11-L17 (encryption and backups) `[STABLE]`

---

## 15. Next lesson

→ [M11-L15 — SQS, SNS and EventBridge](M11-L15-sqs-sns-eventbridge.md) introduces the component that solves most of the
problems in the last three lessons: a queue between the request and the work, which absorbs spikes, bounds concurrency and
makes retries safe.
