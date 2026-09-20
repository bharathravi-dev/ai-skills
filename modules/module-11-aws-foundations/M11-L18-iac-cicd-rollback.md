# M11-L18 — Infrastructure as Code, CI/CD and Rollback

| | |
|---|---|
| **Lesson ID** | M11-L18 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M11-L12](M11-L12-containers-ecr-ecs-fargate.md), [M2-L17](../module-02-python-foundations/M2-L17-git-dependencies.md), [M10-L14](../module-10-governance-security/M10-L14-incident-response-rollback.md) |

---

## 1. Learning objectives

1. **Remove the source of drift** rather than detecting and repairing it forever.
2. **Read a plan** for the difference between an update and a destroy-and-create.
3. **Move defects earlier**, knowing that each stage costs roughly ten times the previous one.
4. **Separate** what a pipeline can revert from what it cannot, and prepare for the latter.
5. **Give the pipeline short-lived, narrowly-conditioned credentials** instead of stored keys.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Infrastructure as code (IaC)** | Defining infrastructure in files that are reviewed, versioned and applied. |
| **Plan / change set** | The preview of what an apply would do, including replacements. |
| **Replacement** | A change that destroys and recreates a resource rather than modifying it. |
| **Drift** | Live infrastructure differing from the code that is supposed to define it. |
| **Policy as code** | Automated checks that reject a change violating a rule (no public buckets, tags required). |
| **OIDC federation** | Exchanging the CI system's own identity token for a short-lived AWS role session. |
| **Deletion protection** | A resource flag preventing deletion until explicitly removed. |
| **Progressive delivery** | Canary or staged rollout with automatic rollback (M13-L14). |

---

## 3. Plain-language explanation

### 3.1 Drift is a source problem, not a detection problem

§7.1, over a year with 180 resources: with console changes normal and no detection, **81 resources (45%)** drift.
Discouraging them without enforcement: **32 (18%)**. Monthly detection with manual repair: **3 (2%)** — and a recurring
afternoon of someone's time. A read-only console: **1 (1%)**.

Every drifted resource is one where the next apply either reverts someone's fix or fails outright.

### 3.2 A plan is where "update" and "destroy" become visible

§7.2: **5 of 9** example changes **replace** the resource rather than updating it. Renaming an RDS identifier creates a
**new empty database and deletes the old one**. Changing a DynamoDB partition key creates a new empty table. Changing a
subnet's CIDR or AZ recreates it and orphans everything inside.

None of that is visible in the diff of the source file. It is visible in the plan.

### 3.3 Each stage costs about ten times the last

§7.3: the expected cost per defect is **71.2 minutes**, and the **1% that reaches production contributes 54 of those
minutes**. Moving the defects that currently escape to canary and production into a four-minute CI policy check takes the
expected cost to **10.1 minutes — 86% lower**.

### 3.4 Code rolls back configuration, not state or effects

§7.4: **4 of 9** changes revert by re-applying the previous code. Schema migrations, deleted buckets and databases,
re-indexed vector stores and emails the agent already sent do not. This is M10-L14 §5.4 again, in the pipeline's
vocabulary.

### 3.5 The pipeline's credentials are the pipeline's blast radius

§7.5: stored IAM user keys last until someone rotates them and work from any job on any branch forever. OIDC federation
gives a session lasting minutes, scoped to one repository — and, with the right condition, to one branch and after an
approval.

---

## 4. Analogy

**Architectural drawings for a building in use.** If tradespeople may move a wall without updating the drawings, within a
year the drawings describe a building that does not exist — and the next contractor works from them. A survey each month
catches most of it and costs a surveyor. Not letting anyone move a wall without a drawing change is what actually works.
And "the drawings show the old layout" is discovered at the worst moment: when someone drills through a pipe.

### Where the analogy breaks

- **Walls move slowly; cloud resources are created by a script in seconds**, by anyone with permission, which is why the
  permission is the control (§5.1).
- **A drawing cannot delete a building; an apply can** — which is what makes the plan step non-negotiable (§5.2).

---

## 5. Detailed technical explanation

### 5.1 Making code the only path

`[REAL, simulated]` §7.1 — 45% / 18% / 2% / 1% drift.

```text
[ ] humans get a read-only console role by default
[ ] a break-glass role grants write access, alerts on use, and is time-limited (L03 §5.6)
[ ] the pipeline's role is the only principal with routine write permissions
[ ] drift detection runs anyway, and a finding is a question ("why did someone need to?")
```

That last line matters: drift is usually a symptom of the pipeline being too slow or too restrictive. Fix the cause.

What belongs in code: accounts and their baselines (L03), networks (L07, L08), IAM roles and policies (L04), buckets and
their settings (L10), compute and services (L11–L15), alarms and dashboards (L16), keys and secret *definitions* (L17) —
and the pipeline itself.

### 5.2 Reading a plan

`[REAL, classified]` §7.2 — 5 of 9 replacements.

| In the plan | Means |
|---|---|
| Update in place | A property changes; the resource survives |
| **Replace** | Destroy and create; **anything the resource held is gone** |
| Destroy | Removal, whether intended or because it left the code |
| Move / import | Bookkeeping only, no infrastructure change |

Controls to put around it:

- **Post the plan in the pull request**, and require a reviewer to acknowledge every replacement and destroy.
- **Deletion protection** on stateful resources — databases, buckets, tables — so an unreviewed apply cannot execute.
- **`prevent_destroy`-style lifecycle rules** in the code for resources that must never be recreated.
- **Separate stacks** for stateful and stateless resources, so routine deploys cannot touch the database.
- **Apply from CI only**, against the reviewed plan, never from a laptop.

### 5.3 The pipeline

`[REAL, computed]` §7.3 — 71.2 → 10.1 minutes.

A pipeline that earns its cost:

```text
1. pre-commit     format, lint, secret scan
2. CI checks      validate, unit tests, POLICY AS CODE, image scan (L12 §5.6)
3. plan           posted to the PR; replacements acknowledged by a reviewer
4. apply: staging automatic
5. verify         smoke tests, evaluation gates for AI changes (M10-L12)
6. apply: prod    approved, and a canary first for risky changes (M13-L14)
7. verify         canary metrics; automatic rollback on failure (M10-L14)
```

The policy-as-code stage (step 2) is the cheapest place to enforce everything Module 10 and this module have asked for:
no public buckets, no `0.0.0.0/0` inbound except on load balancers, all four BPA settings, encryption with a
customer-managed key, required tags, no IAM user keys, IMDSv2 required, CloudTrail not disabled.

For an AI system, step 5 is where the L12 evaluation gates run: a prompt or retrieval change is a release like any other
and should not reach production without passing them.

### 5.4 Rollback

`[REAL, classified]` §7.4 — 4 of 9 revertible.

| Revertible by re-applying | Not revertible |
|---|---|
| Container image, function code | Schema migrations |
| Security group rules, most configuration | Deleted buckets, tables, databases |
| Alarms, dashboards, tags | Re-indexed vector stores |
| IAM policies (though issued sessions persist — L05) | Effects the system had on the outside world |

Preparation, all of it done **before** the change: reverse migrations written with the forward one; deletion protection;
previous images and indexes kept through a soak period; and a pipeline that can deploy the **previous commit** without a
rebuild, because rebuilding during an incident is slow and may not even reproduce (M10-L13).

### 5.5 Pipeline credentials

`[REAL, compared]` §7.5.

```json
// the trust policy condition that matters
"Condition": {
  "StringEquals":  {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
  "StringLike":    {"token.actions.githubusercontent.com:sub": "repo:acme/assistant:ref:refs/heads/main"}
}
```

The subtlety specific to CI: a condition that checks only the **repository** lets any branch — including one from a
fork's pull request — assume the deployment role. Condition on repository **and** branch or environment, require an
approval for production, and use a **different role per environment** (L04 §5.7).

Plus the basics: no long-lived keys anywhere (L05), a role with least privilege for what the pipeline actually deploys,
and secret scanning in pre-commit and CI.

### 5.6 Multi-account topology

The pipeline runs in a shared-services account and assumes a deployment role in each target account (L03 §5.4). That gives
you one place to audit deployments, per-environment roles with different permissions, and a production role that a
developer cannot assume directly.

### 5.7 Assumptions and limitations

- Drift rates, defect distribution, stage costs and repair effectiveness are invented; the **ordering** of stage costs is
  the durable part.
- The lab is tool-agnostic: "plan", "apply" and "replace" describe CloudFormation, Terraform and CDK with different names.
- State-file management and locking, module design and progressive-delivery tooling are out of scope (M13-L14).

---

## 6. Worked example — the rename that emptied the database

**The situation.** A team tidied their Terraform, renaming resources for consistency. One change altered an RDS
instance's identifier from `app-db-prod` to `prod-app-db`.

**What happened.**

1. The plan showed a **replacement**: destroy `app-db-prod`, create `prod-app-db` (§7.2). The plan was 400 lines and was
   approved with "tidy-up, no functional change".
2. The apply ran in the production pipeline. Deletion protection was **not** enabled (§5.2).
3. The new database came up empty. The application connected successfully — to nothing.
4. The final snapshot existed, but the restore needed a KMS key policy change first, which nobody could make quickly
   (L17 §6).
5. Total: **five hours**, and a day of writes lost to the snapshot's age.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Replacement not noticed in a long plan | Require explicit acknowledgement of every replacement (§5.2) |
| 2 | No deletion protection | Enable on all stateful resources |
| 3 | Stateful and stateless in one stack | Separate stacks; routine deploys cannot touch the database |
| 4 | No policy check for destroys in production | Policy as code: fail on destroy of protected types (§5.3) |
| 5 | Restore path untested | Timed restore test (L17 §5.6) |

**The general rule.** **Read the plan for verbs, not for names. "Replace" is a destroy that has been made to sound
routine.**

---

## 7. Practical activity

**File:** [`labs/m11/l18_iac_cicd_rollback.py`](../../labs/m11/l18_iac_cicd_rollback.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l18_iac_cicd_rollback.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1118)`; run twice, output
identical.

```text

============================================================================
1. DRIFT: WHAT HAPPENS WHEN THE CONSOLE IS ALLOWED
============================================================================
  180 resources, 52 weeks

  policy                                        drifted at year end   share
  console changes normal, no detection                           81     45%
  console changes discouraged, no detection                      32     18%
  drift detection monthly, fixed by hand                          3      2%
  read-only console; changes only via code                        1      1%

  Every drifted resource is one where the code no longer describes reality,
  so the next apply either reverts someone's fix or fails outright.
  Detection plus repair keeps the number small but never reaches zero, and it
  costs someone a recurring afternoon. Removing WRITE access to the console
  removes the source. The console stays useful for reading, which is most of
  what it is good for -- and a break-glass role covers the rest (M11-L03).

============================================================================
2. READING A PLAN: WHICH CHANGES DESTROY SOMETHING?
============================================================================
  change                                    effect             data loss?   note
  security group rule added                 update in place            no   
  instance type changed                     update in place            no   brief restart
  subnet CIDR changed                       REPLACE                   YES   new subnet; anything in it is orphaned
  RDS instance identifier renamed           REPLACE                   YES   NEW EMPTY DATABASE; the old one is deleted
  S3 bucket name changed                    REPLACE                   YES   new empty bucket; data not migrated
  Lambda memory increased                   update in place            no   
  DynamoDB partition key changed            REPLACE                   YES   new empty table
  tags changed                              update in place            no   
  availability zone of a subnet changed     REPLACE                   YES   everything in it is recreated

  changes that REPLACE a resource: 5/9
  A plan is not a formality; it is the only place the difference between
  'update' and 'destroy and create' is visible before it happens. Require the
  plan output in the pull request, make a reviewer acknowledge every
  replacement, and put deletion protection on stateful resources so that an
  unreviewed plan cannot execute (M10-L14 -- these are one-way doors).

============================================================================
3. WHERE IS THE DEFECT CAUGHT, AND WHAT DOES THAT COST?
============================================================================
  caught at                             cost (minutes)   share of defects   weighted
  editor / pre-commit hook                           1                55%        0.6
  CI: lint, validate, policy check                   4                25%        1.0
  CI: plan reviewed by a human                      30                10%        3.0
  deploy to staging                                 90                 6%        5.4
  canary in production                             240                 3%        7.2
  full production incident                       5,400                 1%       54.0
  EXPECTED COST PER DEFECT                                                      71.2 min

  counterfactual: a policy check that catches the 3% reaching canary and the
  1% reaching production -- open security groups, public buckets, missing
  encryption -- moves them to the 4-minute stage:
    expected cost per defect 71.2 min -> 10.1 min (86% lower)
  Each stage is roughly an order of magnitude more expensive than the one
  before, so moving ONE class of defect one stage earlier pays for a lot of
  automation -- and the 1% that reaches production dominates the average.
  Policy-as-code checks (no public buckets, no 0.0.0.0/0, tags required,
  encryption required) are the cheapest stage to add (M10-L12, M11-L10).

============================================================================
4. WHAT CAN THE PIPELINE ACTUALLY ROLL BACK?
============================================================================
  change                                revertible by re-apply?   how
  application container image                               yes   redeploy the previous tag
  Lambda function code                                      yes   alias points to the previous version
  security group rules                                      yes   re-apply the previous code
  IAM policy change                                         yes   re-apply, but sessions already issued persist
  a database schema migration                                NO   needs the reverse migration, written in advance
  a deleted S3 bucket                                        NO   the name may be gone; the data certainly is
  a deleted RDS instance                                     NO   restore from snapshot, if one exists and is current
  a re-indexed vector store                                  NO   rebuild, if you kept the previous index (M10-L14)
  emails the deployed agent sent                             NO   cannot be unsent

  revertible: 4/9
  'Infrastructure as code means we can always roll back' is true of
  CONFIGURATION and false of STATE and EFFECTS -- the same split as M10-L14.
  So: deletion protection on stateful resources, reverse migrations written
  with the forward one, previous artefacts kept through a soak period, and a
  pipeline that can deploy the previous commit without a rebuild.

============================================================================
5. PIPELINE CREDENTIALS
============================================================================
  option                                      credential lifetime           
  long-lived IAM user keys in CI secrets      until someone rotates them    
      scope: any job, any branch, forever
      if it leaks: a leaked log line is a permanent breach
  OIDC federation, role per repository        the job's duration (minutes)  
      scope: that repo, that workflow
      if it leaks: a leaked token expires in minutes
  OIDC + branch condition + environment approvalthe job's duration            
      scope: that repo, that BRANCH, after approval
      if it leaks: a fork's pull request cannot deploy

  This is M11-L05's arithmetic applied to CI. The subtlety specific to
  pipelines is the CONDITION: an OIDC trust policy that checks only the
  repository lets any branch -- including one from a fork's pull request --
  assume the deployment role. Condition on the repo AND the branch or
  environment, and require an approval for production (M11-L04 section 5.7).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every drift count, replacement classification, weighted cost and
  rollback verdict above is computed from the values in this script.

  ILLUSTRATIVE: drift rates, defect distribution, stage costs and repair
  effectiveness are invented. The ORDERING of stage costs -- each roughly an
  order of magnitude above the last -- is the durable part.

  TOOL-AGNOSTIC: 'plan', 'apply' and 'replace' describe CloudFormation,
  Terraform and CDK alike, with different names.

  NOT SHOWN: state-file management and locking, module design, multi-account
  pipeline topologies, and progressive delivery tooling (M13-L14).

Done.
```

### 7.3 Reading the result

**Section 1's first and last rows** — 45% versus 1% — are the difference between discouraging console changes and
removing the permission.

**Section 2's five `REPLACE` rows** are the ones to look for in every plan you approve.

**Section 3's bottom line** — 54 of 71 minutes from the 1% that reaches production — is the case for the policy-check
stage.

**Section 4's split** is M10-L14's one-way doors, restated for a pipeline.

---

## 8. Common mistakes and troubleshooting

1. **Detecting drift instead of preventing it.** §7.1.
2. **Approving a plan without reading the verbs.** §7.2 — five replacements in nine changes.
3. **Stateful and stateless resources in one stack.** §6.
4. **No deletion protection.** §5.2.
5. **No policy-as-code stage.** §7.3 — the cheapest one to add.
6. **Applying from a laptop.** The plan reviewed is not the plan applied.
7. **Assuming code rolls everything back.** §7.4 — 4 of 9.
8. **Long-lived keys in CI.** §7.5.
9. **OIDC conditioned on the repository only.** §5.5 — any branch can deploy.
10. **Rebuilding during a rollback.** Keep the previous artefact deployable.

| Symptom | Likely cause | Fix |
|---|---|---|
| Apply reverts a fix someone made | Drift from console changes | Read-only console; break-glass with alerting |
| A resource was recreated empty | Replacement approved unknowingly | Acknowledge replacements; deletion protection |
| The same misconfiguration recurs | No policy as code | Add the check to CI (§5.3) |
| Rollback took as long as the deploy | Rebuild required | Keep previous images; deploy by tag |
| A fork's pull request could deploy | OIDC condition too broad | Condition on repo **and** branch/environment |

---

## 9. Security, privacy, reliability, cost

- **Security.** The pipeline role is a highly privileged principal: least privilege per environment, OIDC only, and
  CloudTrail on every deployment (L04, L16).
- **Privacy.** Policy as code is where "encrypted with a customer-managed key" and "not public" stop being intentions
  (M10-L06, L10).
- **Reliability.** Small, reviewed, revertible changes are the incident control from M10-L14 §5.6, implemented.
- **Cost.** Infrastructure code is also where budgets, tags and lifecycle rules get enforced consistently (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What share of resources drifted with no detection and a writable console?
2. Which changes in §7.2 replace the resource?
3. What share of the expected defect cost comes from the 1% reaching production?
4. Which five changes in §7.4 cannot be reverted by re-applying?
5. Why is an OIDC condition on the repository alone insufficient?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the drift rate to 0.02 and re-read section 1.
2. Add three changes from your own stack to §7.2 and classify them.
3. Move the staging-caught defects earlier in §7.3 and recompute.
4. Add two of your own resources to §7.4 and decide what preparation each needs.
5. Write the OIDC trust policy for your pipeline, conditioned on repository and branch.

### Exercise 3 — Challenge (~60 min)

1. Write six policy-as-code rules from Module 10 and this module, and run them against your own code.
2. Split one stack into stateful and stateless, and enable deletion protection on everything stateful.
3. Build the pipeline from §5.3 for one service, including an evaluation gate (M10-L12).
4. Prove rollback works: deploy a deliberately broken change to staging and let the pipeline revert it.
5. Remove every long-lived credential from your CI system and replace it with OIDC.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l18).)*

**Q1.** What is the most effective way to eliminate configuration drift?

- A. Running drift detection more frequently
- B. Removing write access to the console so code is the only path
- C. Documenting a policy that discourages console changes
- D. Re-applying the code on a schedule

**Q2.** In §7.1, what share of resources drifted with a writable console and no detection?

- A. 1%
- B. 18%
- C. 45%
- D. 2%

**Q3.** What does "replace" mean in a plan?

- A. The resource is updated with new properties
- B. The resource is renamed in state only
- C. The resource is imported from another stack
- D. The resource is destroyed and a new one created

**Q4.** Renaming an RDS instance identifier in code causes —

- A. a rename with no data impact
- B. an in-place update requiring a restart
- C. a replacement: a new empty database, and the old one deleted
- D. a validation error before apply

**Q5.** In §7.3, what share of the expected defect cost came from defects reaching production?

- A. About three-quarters
- B. About half
- C. About a quarter
- D. About a tenth

**Q6.** Why is the policy-as-code stage high value?

- A. It replaces the need for human plan review
- B. It is required for compliance certification
- C. It runs faster than unit tests
- D. It catches classes of defect that otherwise reach production, at a fraction of the cost

**Q7.** Which change can a pipeline revert by re-applying previous code?

- A. A schema migration
- B. A deleted S3 bucket
- C. A re-indexed vector store
- D. A security group rule

**Q8.** What should be written at the same time as a forward schema migration?

- A. The deployment approval request
- B. The reverse migration
- C. The canary configuration
- D. The updated system card

**Q9.** Why separate stateful and stateless resources into different stacks?

- A. So routine deploys cannot destroy or replace the database
- B. To reduce plan output size
- C. Because they use different IaC tools
- D. To allow different regions per stack

**Q10.** What is the risk of an OIDC trust policy conditioned only on the repository?

- A. Sessions last longer than intended
- B. The role cannot be assumed by scheduled workflows
- C. Any branch, including a fork's pull request, can assume the deployment role
- D. The token cannot be validated across accounts

**Q11.** Why should a rollback not require a rebuild?

- A. Rebuilds are slow and may not reproduce the previous artefact
- B. Build systems are unavailable during incidents
- C. Rebuilding invalidates the image scan
- D. The previous commit may no longer exist

**Q12.** Where should an apply be run from?

- A. A developer's laptop with an assumed admin role
- B. CI, against the reviewed plan
- C. The console, so changes are visible immediately
- D. Any environment, provided the state file is locked

**Q13.** *(Written, rubric-graded.)* In under 150 words: a pull request tidies resource names across your Terraform. What
do you check before approving, and what would make you refuse?

---

## 12. Revision notes

- **Drift is a source problem**: **45%** drift with a writable console and no detection; **2%** with monthly detection and
  manual repair; **1%** with a read-only console.
- **Read plans for verbs**: **5 of 9** lab changes **replace** the resource — renaming an RDS identifier creates an empty
  database.
- **Each stage costs ~10× the last**: expected **71.2 min** per defect, **54 of it** from the 1% reaching production;
  a policy check takes it to **10.1 min (−86%)**.
- **Pipelines revert configuration, not state or effects**: **4 of 9**. Prepare reverse migrations, deletion protection
  and retained artefacts.
- **OIDC, conditioned on repository *and* branch**, with per-environment roles and production approval.
- **Apply from CI only**, against the reviewed plan; keep the previous commit deployable without a rebuild.

---

## 13. Completion checklist

- [ ] Humans have a read-only console; the pipeline is the only routine write path.
- [ ] Plans are posted to pull requests and replacements are explicitly acknowledged.
- [ ] Stateful resources are in separate stacks with deletion protection.
- [ ] Policy-as-code enforces the Module 10 and Module 11 rules in CI.
- [ ] Reverse migrations, retained artefacts and a rebuild-free rollback path exist.
- [ ] CI uses OIDC with repository and branch conditions, and per-environment roles.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS CloudFormation change sets; Terraform plans; AWS CDK — the plan/apply/replace model is common to all `[STABLE]`
- OIDC federation for CI providers into AWS IAM roles; trust-policy conditions on repository and branch `[STABLE]`
- AWS Config for drift detection; Service Control Policies as guardrails (L03, L04) `[STABLE]`
- M10-L13 (run fingerprints and reproducibility) and M10-L14 (rollback, one-way doors, small changes) `[STABLE]`
- M11-L12 (image build and deployment discipline) and M13-L14 (canary releases) `[STABLE]`

---

## 15. Next lesson

→ Module 11 ends here. **Project 11** applies it: an authenticated API with least-privilege roles, private networking,
logging, alarms and a cost estimate, deployed by a pipeline you can revert.

Module 12 puts the AI workload onto this foundation —
[M12-L01 — Amazon Bedrock: concepts, model access, region reality](../module-12-ai-on-aws/M12-L01-bedrock-concepts-model-access.md) —
where the IAM, networking, logging and cost controls you have just built become the way a model is called safely.
