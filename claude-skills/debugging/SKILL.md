---
name: debugging
description: Systematic debugging methodology for any codebase. Use when investigating bugs, test failures, or unexpected behavior before proposing fixes.
allowed-tools: Read, Grep, Glob, SemanticSearch, Shell, Write, Edit
---

# Systematic Bug Debugging (Enhanced)

A structured methodology for diagnosing and fixing bugs. Enforces root-cause analysis over trial-and-error. Works across any tech stack and any project.

Merges the best of case-study-driven debugging + superpowers systematic-debugging techniques.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1-3, you CANNOT propose fixes.
Violating the letter of this process is violating the spirit of debugging.

## When to Use

- Investigating any bug report or unexpected behavior
- Fixing test failures
- Debugging platform-specific issues
- Performance problems, build failures, integration issues
- Any time you're about to write a "fix:" commit

**Use ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- You don't fully understand the issue

## FIRST: Read Past Case Studies

**Before starting ANY debugging work**, read the case study log:
→ [references/case-studies.md](references/case-studies.md)

Search for cases matching the current bug by:
- **Symptom similarity** (e.g., "tabs disappear", "data not showing on mobile")
- **Tags** (e.g., `ui-overflow`, `state-misdiagnosis`, `cross-platform`)
- **Project / Component area**

If a similar case exists, learn from it to avoid repeating the same wrong hypotheses.

---

## The 6-Phase Process

### Phase 1: Reproduce & Classify

**Step 1 — Reproduce the bug**
- Understand the exact symptoms: what is visible? What should be visible?
- Can you trigger it reliably? What are the exact steps?
- If not reproducible → gather more data, don't guess
- Identify affected platform(s): all platforms, or specific ones?

**Step 2 — Classify the bug layer**

```
Data/API ──→ State ──→ Logic/Filter ──→ UI/Layout ──→ User sees bug
```

Work backwards from the symptom to find which layer is broken:

| Layer | How to Check |
|-------|-------------|
| Data/API | `console.log` the raw API response |
| State | Log the state/store/atom value at the read point |
| Logic | Log the output of filter/map/sort chains |
| UI | Add visible border/background to confirm element exists and its dimensions |

**Step 3 — Check recent changes**
- What changed that could cause this? `git diff`, recent commits
- New dependencies, config changes, environmental differences

### Phase 2: Instrument & Gather Evidence

> **Core upgrade from superpowers:** Don't guess which layer — instrument all boundaries, run once, then analyze.

**Step 4 — Component boundary diagnostics**

For multi-component systems (CI → build → signing, API → service → database, atom → hook → component):

```
For EACH component boundary:
  - Log what data ENTERS the component
  - Log what data EXITS the component
  - Verify environment/config propagation
  - Check state at each layer

Run ONCE to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify failing component.
THEN investigate that specific component.
```

Example (multi-layer system):
```bash
# Layer 1: API response
echo "=== API response: ===" && curl -s "$URL" | jq '.data'

# Layer 2: State after parsing
console.log('[DEBUG L2] atom value:', JSON.stringify(atomValue));

# Layer 3: Logic output
console.log('[DEBUG L3] filtered result:', result.length, result);

# Layer 4: UI render
<div style={{ border: '2px solid red' }}>{children}</div>
```

**Step 5 — Search for context**

Before writing any fix, search for:
1. Similar components that already solve this problem
2. How the same pattern is implemented elsewhere (other pages, other platforms)
3. Git history for related fixes: `git log --all --oneline | grep "keyword"`

**Step 6 — Understand platform differences (if cross-platform)**

| Aspect | Desktop/Web | Mobile |
|--------|-------------|--------|
| Screen width | Wide, content fits | Narrow, may need scroll |
| Interaction | Mouse hover + click | Touch press |
| Navigation | Usually inline | Modal / Page push |
| State context | Single JS context | May have background/UI split |

### Phase 3: Root Cause Tracing

> **Core technique from superpowers:** Trace bugs backward through call stack to find original trigger. NEVER fix where the error appears — find the source.

**Step 7 — Backward tracing**

```
1. Observe the Symptom
   Error: git init failed in /Users/project/packages/core

2. Find Immediate Cause
   await execFileAsync('git', ['init'], { cwd: projectDir });

3. Ask: What Called This?
   WorktreeManager.createSessionWorktree(projectDir)
     → called by Session.initializeWorkspace()
     → called by Session.create()
     → called by test at Project.create()

4. Keep Tracing Up — What value was passed?
   projectDir = '' (empty string!)

5. Find Original Trigger
   const context = setupCoreTest(); // Returns { tempDir: '' }
   Project.create('name', context.tempDir); // Accessed before beforeEach!
```

**When you can't trace manually, add instrumentation:**
```typescript
async function suspiciousFunction(input: string) {
  const stack = new Error().stack;
  console.error('DEBUG trace:', {
    input,
    cwd: process.cwd(),
    stack,
  });
}
```

**Critical:** Use `console.error()` in tests (not logger — may be suppressed).

### Phase 4: Hypothesis & Test

> **Scientific method from superpowers:** Single hypothesis, minimal test, one variable at a time.

**Step 8 — Form single hypothesis**
- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

**Step 9 — Test minimally**
- Make the SMALLEST possible change to test hypothesis
- One variable at a time
- Don't fix multiple things at once

**Step 10 — Graduated escalation (Strike Rule)**

```
Strike 1: First fix doesn't work
  → Re-examine layer classification (Phase 1 Step 2)
  → Add more logging to narrow down
  → Form NEW hypothesis

Strike 2: Second fix doesn't work
  → STOP. You are likely misdiagnosing the root cause.
  → Go back to Phase 1, start completely over
  → Search git history for similar bugs
  → Consider the problem is in a DIFFERENT layer than you think

Strike 3: Third fix doesn't work
  → STOP. This is NOT a bug problem. This is an ARCHITECTURE problem.
  → Each fix revealing new problems in different places = structural issue
  → Fixes requiring "massive refactoring" = wrong pattern
  → DISCUSS WITH USER before attempting Fix #4
  → Consider: "Are we sticking with this through sheer inertia?"
```

### Phase 5: Fix & Fortify

> **Upgrades from superpowers:** TDD before fixing + Defense-in-Depth after fixing + Verification gate.

**Step 11 — Create failing test FIRST (TDD)**

Before writing any fix code:
1. Write the simplest possible test that reproduces the bug
2. Run it — it MUST fail (red)
3. If it passes, your test doesn't capture the bug — fix the test
4. Use `superpowers:test-driven-development` skill for guidance

**Step 12 — Implement single fix**
1. Fix the root cause, not the symptom
   - Bad: Adding a force-refresh when the real issue is a UI overflow
   - Good: Creating a scrollable container to handle dynamic content
2. Reuse existing patterns — search before creating new solutions
3. ONE change at a time, no "while I'm here" improvements

**Step 13 — Defense-in-Depth (make bug structurally impossible)**

After fixing the root cause, add validation at EVERY layer data passes through:

```
Layer 1: Entry Point Validation
  → Reject obviously invalid input at API boundary
  → Example: if (!directory || directory.trim() === '') throw Error

Layer 2: Business Logic Validation
  → Ensure data makes sense for this operation
  → Example: if (!projectDir) throw Error('projectDir required')

Layer 3: Environment Guards
  → Prevent dangerous operations in specific contexts
  → Example: In test, refuse git init outside tmpdir

Layer 4: Debug Instrumentation
  → Capture context for forensics if it ever happens again
  → Example: Log directory, cwd, stack before dangerous operation
```

Single validation: "We fixed the bug."
Multiple layers: "We made the bug **impossible.**"

**Step 14 — Verification gate (mandatory)**

Before claiming fix works, you MUST:
- [ ] Run the failing test → it passes now (green)
- [ ] Revert the fix → test fails again (confirms test catches the bug)
- [ ] Restore the fix → test passes
- [ ] Run full test suite → no regressions
- [ ] Lint passes
- [ ] Type check passes
- [ ] Bug is fixed on the reported platform
- [ ] No regression on other platforms
- [ ] Removed all debug logging

**NO "should pass now". NO "looks correct". RUN IT.**

Use `superpowers:verification-before-completion` skill for enforcement.

### Phase 6: Learn — Post-Fix Case Study (MANDATORY)

After every non-trivial bug fix, you MUST append a case study to [references/case-studies.md](references/case-studies.md).

**Template:**

```markdown
## Case NNN: [Short Title]

**Date**: YYYY-MM-DD
**Project**: [project name]
**Severity**: Low / Medium / High / Critical
**Platforms affected**: All / Mobile / Desktop / Web / Extension

### Symptom
[What the user saw — one sentence]

### Wrong Hypotheses (if any)
| # | Hypothesis | Fix Attempted | Why It Failed |
|---|-----------|---------------|---------------|
| 1 | ... | ... | ... |

### Root Cause
[The actual root cause — which layer (Data/State/Logic/UI/Platform) and what specifically was wrong]

### Correct Fix
[What was done to fix it — list of changes]

### Defense-in-Depth Added
[What validation layers were added to make it impossible]

### Key Lessons
- [Lesson 1]
- [Lesson 2]

### Tags
`tag1` `tag2` `tag3`
```

**Tag taxonomy** (use existing tags when possible, add new ones as needed):
- Layers: `data-layer` `state-layer` `logic-layer` `ui-layer` `platform-layer`
- Misdiagnosis: `state-misdiagnosis` `data-misdiagnosis` `ui-misdiagnosis`
- Platforms: `mobile-only` `desktop-only` `web-only` `extension-only` `cross-platform`
- UI patterns: `ui-overflow` `scrollable-container` `layout-constraint` `responsive`
- Code quality: `reusable-component` `hook-extraction` `component-refactor`
- Techniques: `defense-in-depth` `backward-tracing` `condition-waiting` `architecture-issue`

---

## Condition-Based Waiting (Flaky Test 专用)

When debugging flaky tests with timing issues, replace arbitrary timeouts with condition polling:

```typescript
// ❌ BEFORE: Guessing at timing
await new Promise(r => setTimeout(r, 50));
const result = getResult();
expect(result).toBeDefined();

// ✅ AFTER: Waiting for condition
await waitFor(() => getResult() !== undefined);
const result = getResult();
expect(result).toBeDefined();
```

**Generic implementation:**
```typescript
async function waitFor<T>(
  condition: () => T | undefined | null | false,
  description: string,
  timeoutMs = 5000
): Promise<T> {
  const startTime = Date.now();
  while (true) {
    const result = condition();
    if (result) return result;
    if (Date.now() - startTime > timeoutMs) {
      throw new Error(`Timeout waiting for ${description} after ${timeoutMs}ms`);
    }
    await new Promise(r => setTimeout(r, 10));
  }
}
```

| Scenario | Pattern |
|----------|---------|
| Wait for event | `waitFor(() => events.find(e => e.type === 'DONE'))` |
| Wait for state | `waitFor(() => machine.state === 'ready')` |
| Wait for count | `waitFor(() => items.length >= 5)` |
| Wait for file | `waitFor(() => fs.existsSync(path))` |

**Arbitrary timeout IS correct ONLY when:**
1. Testing actual timing behavior (debounce, throttle)
2. First wait for triggering condition, THEN wait for timed behavior
3. Comment explaining WHY

---

## Pressure Defense (Anti-Rationalization)

### Red Flags — STOP and Return to Phase 1

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "One more fix attempt" (when already tried 2+)
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow

**ALL of these mean: STOP. Return to Phase 1.**

### Human Signal Detection

Watch for these user redirections — they mean your approach is wrong:
- **"Is that not happening?"** — You assumed without verifying
- **"Will it show us...?"** — You should have added evidence gathering
- **"Stop guessing"** — You're proposing fixes without understanding
- **"Ultrathink this"** — Question fundamentals, not just symptoms
- **"We're stuck?"** (frustrated) — Your approach isn't working

**When you see these:** STOP immediately. Return to Phase 1.

### Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too |
| "Emergency, no time for process" | Systematic is FASTER than guess-and-check |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right. |
| "I'll write test after confirming fix" | Untested fixes don't stick. Test first. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause |
| "One more attempt" (after 2+ failures) | 3+ failures = architectural problem |
| "Reference too long, I'll adapt" | Partial understanding guarantees bugs |

---

## Anti-Patterns Quick Reference

| Anti-Pattern | Why It's Bad | Better Approach |
|-------------|-------------|-----------------|
| Trial-and-error commits | Wastes time, messy git history | Verify root cause with logging first |
| Assuming state sync issues | Often misdiagnosis | Log state values to confirm |
| Copying code across platforms | Different constraints | Adapt for each platform |
| Fixing without reproducing | Might fix symptom, not cause | Always reproduce first |
| 3+ fix attempts same hypothesis | Your hypothesis is wrong | Strike 3 → question architecture |
| Single validation point | Can be bypassed by other code paths | Defense-in-Depth: validate at every layer |
| Arbitrary sleep/timeout in tests | Creates flaky tests | Condition-based waiting |
| Fixing where error appears | Treating symptom | Backward trace to original trigger |

---

## Quick Reference Card

| Phase | Key Activities | Success Criteria | superpowers Integration |
|-------|---------------|------------------|------------------------|
| **1. Reproduce & Classify** | Reproduce, classify layer, check changes | Know WHAT and WHERE | — |
| **2. Instrument & Gather** | Boundary logging, search patterns | Evidence of WHERE it breaks | Component boundary diagnostics |
| **3. Root Cause Tracing** | Backward trace through call chain | Found ORIGINAL trigger | `root-cause-tracing` technique |
| **4. Hypothesis & Test** | Single hypothesis, minimal test | Confirmed or new hypothesis | Strike escalation rule |
| **5. Fix & Fortify** | TDD → Fix → Defense-in-Depth → Verify | Bug fixed AND impossible | `test-driven-development` + `verification-before-completion` |
| **6. Learn** | Write case study | Knowledge preserved | Case study library |

## Case Studies

All past cases are in [references/case-studies.md](references/case-studies.md). Read them before debugging.

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common
