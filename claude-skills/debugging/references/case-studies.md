# Bug Fix Case Studies

> This file is a living document. After every non-trivial bug fix, append a new case study.
> AI agents read this file before debugging to learn from past mistakes.
> Format: newest cases at the top.

---

## Case 006: Code Review Catches 3 Classes of Issues in Perp/Referral PR

**Date**: 2026-02-09 | **Project**: OneKey app-monorepo | **Platforms**: all (mobile, desktop, web, ext)

### Context
PR with 4 files: ServiceHyperliquid atom fix, two token selector tab simplifications, and a PerpsRecordTable compact layout refactor with fixed-column + horizontal scroll.

### Issues Found During Review

| # | Category | Issue | Severity |
|---|---|---|---|
| 1 | **No-op useMemo** | `visibleDynamicTabs = useMemo(() => dynamicTabs, [dynamicTabs])` — wrapping an already-memoized value in another useMemo that just returns its only dependency. Zero benefit, extra closure allocation per render. | Warning |
| 2 | **Unused import** | Removing the useMemo left `IPerpDynamicTab` type import with 0 usages. Dead import. | Warning |
| 3 | **Inline style objects in render** | `hoverStyle={{ opacity: 0.7 }}`, `hoverStyle={{ bg: '$bgHover' }}`, `formatterOptions={{ showPlusMinusSigns: true }}` — create new object references every render. | Warning |
| 4 | **Import order** | `FixedColumnShadowOverlay` imported before `Currency` (not alphabetical within `@onekeyhq/kit` group). | Style |
| 5 | **Fixed vs scrollable column row height drift** (caught by Devin bot) | Compact mode splits the table into two independent YStacks: fixed address column and scrollable rest. The scrollable column has a `Badge` component (with padding/border) that's taller than the fixed column's `SizableText`. Heights accumulate independently, causing rows to misalign after many rows. | Critical |

### Fixes Applied

1. **No-op useMemo** → `const visibleDynamicTabs = dynamicTabs;` (direct assignment)
2. **Unused import** → Removed `import type { IPerpDynamicTab }`
3. **Inline style objects** → Extracted to module-level constants: `HOVER_OPACITY_STYLE`, `HOVER_BG_STYLE`, `REWARD_FORMATTER_OPTIONS`
4. **Import order** → Alphabetical: `Currency` → `FixedColumnShadowOverlay` → `useFixedColumnShadow` → `useThemeVariant`
5. **Row height drift** → Added `minHeight={COMPACT_ROW_MIN_HEIGHT}` (`'$10'`) to all rows in both columns, following the existing `InviteCodeListTable` pattern

### Lessons

- **useMemo is not free** — don't wrap values that are already memoized or referentially stable. `useMemo(() => x, [x])` is strictly worse than `const y = x`.
- **After removing code, trace all side effects** — removing a `useMemo<TypeAnnotation>` can orphan the type import. Always check remaining usage count.
- **Inline object literals in JSX** (`style={{}}`, `hoverStyle={{}}`, `formatterOptions={{}}`) create new references every render. Extract to module-level constants, even for simple objects. This is enforced by project rules and prevents subtle re-render bugs downstream.
- **When splitting a table into fixed + scrollable columns, row heights MUST be synchronized** — two independent layout containers will produce independently-sized rows if their content differs (e.g., Badge vs plain text). Always add explicit `minHeight` to both sides. The existing codebase already has this pattern in `InviteCodeListTable` (`rowProps={{ minHeight: '$10' }}`).
- **Search for existing patterns before inventing** — the `InviteCodeListTable` already solved the fixed-column height issue. A 30-second search would have prevented the bug.
- **PR bots can catch real bugs** — the Devin bot spotted the row height drift that manual review missed. Don't dismiss automated review comments.

### Anti-Pattern Catalog (add to checklist)

```
[ ] No useMemo wrapping a single already-memoized dependency
[ ] No orphaned type imports after refactoring
[ ] No inline object literals in JSX props (extract to module-level const)
[ ] Fixed-column tables: both columns have explicit minHeight on rows
[ ] Import order: alphabetical within each package group
```

### Tags
`code-review` `useMemo-anti-pattern` `inline-object-literal` `fixed-column-table` `row-height-drift` `reference-stability` `import-hygiene`

---

## Case 005: PR #10051 Merged But Dynamic Tabs Never Appear (Atom Stuck at null)

**Date**: 2026-02-09 | **Project**: OneKey (app-monorepo) | **Platforms**: All

### Symptom
PR #10051 (ScrollableFilterBar + dynamic tabs) merged to main branch, but the dynamic tabs feature had no visible effect — atom stayed at initial `null` and never transitioned to a loaded state.

### Wrong Hypotheses (if any)
| # | Hypothesis | Why Wrong |
|---|-----------|-----------|
| — | First hypothesis was correct: atom write guard blocking the transition | — |

### Root Cause
**State layer** — PR changed `perpTokenSelectorTabsAtom` initial value from `[]` to `null` (to distinguish "not loaded" from "loaded but empty"), but did NOT update the corresponding write logic in `ServiceHyperliquid.updatePerpConfig()`. The pre-existing guard `if (tokenSelectorTabs) { atom.set(tokenSelectorTabs) }` only writes when the server returns a truthy value. When the server doesn't return `tokenSelectorTabs` (optional field, `undefined`), the guard blocks the write, and the atom stays at `null` forever. This means:
1. `dynamicTabsLoaded = (dynamicTabs !== null)` is always `false`
2. `usePerpActiveTabValidation` never runs validation
3. Dynamic tabs are never displayed even when data exists

### Fix
Changed `if (tokenSelectorTabs) { atom.set(tokenSelectorTabs) }` to `atom.set(tokenSelectorTabs ?? [])` — always write to the atom after config fetch, using `[]` as fallback when server doesn't return the field.

### Lessons
- **When changing an atom's type/initial value, trace ALL write points**: Changing `initialValue: []` to `initialValue: null` is a semantic change that requires updating every writer that previously relied on the old "always loaded" assumption
- **The `null` vs `[]` pattern has TWO halves**: (1) Read side correctly distinguishes loading states, (2) Write side must always transition from `null` to a valid state. PR only did half (1) but missed (2)
- **Optional server fields + truthy guards = silent failure**: `if (optionalField)` silently skips when the field is `undefined`, which is fine for "add if present" but catastrophic for "must always set to unblock downstream logic"
- **This is a direct follow-up to Case 002**: Case 002 introduced the `null` initial value pattern, but the write-side fix was incomplete — the `ServiceHyperliquid.ts` guard was not updated

### Tags
`state-layer` `atom-write-guard` `null-vs-empty` `async-loading` `incomplete-refactor` `cross-platform`

---

## Case 002: PR #10051 Post-Submit Fix Chain (6 fixes after feature commit)

**Date**: 2026-02-07 | **Project**: OneKey (app-monorepo) | **Platforms**: All

### Symptom
After submitting the ScrollableFilterBar feature PR, Devin Review identified 3 bugs that required 6 incremental fix commits — each fix partially correct but introducing or missing new issues.

### Wrong Hypotheses (if any)
| # | Hypothesis | Why Wrong |
|---|-----------|-----------|
| 1 | Only need to gate validation on `hasAssetsLoaded` | `dynamicTabs` loads independently from assets — a separate race condition |
| 2 | `dynamicTabs.length > 0` = "tabs have loaded" | Can't distinguish "not loaded yet" (`[]` initial) from "server returned empty" (`[]` valid) |
| 3 | `dynamicTabsRaw ?? []` is a safe fallback | Creates a new array reference every render, breaking downstream `useMemo` |

### Root Cause
**Multiple layers**: (1) Async state loading — didn't trace temporal order of two independent data sources, (2) React reference stability — inline `?? []` and `{}` defaults, (3) Cross-platform consistency — desktop and mobile had different filtering logic for the same feature, (4) TypeScript — didn't run `tsc` before push.

### Fix
1. Changed atom initial from `[]` to `null` to distinguish "not loaded" from "empty"
2. Wrapped `?? []` fallbacks in `useMemo` for reference stability
3. Aligned desktop filtering logic to match mobile (filter tabs by matching tokens)
4. Extracted module-level `EMPTY_STYLE` constant with correct type

### Lessons
- **Trace async loading sequences BEFORE writing code**: List all data sources, their loading order, and initial values. Map every combination.
- **`array.length > 0` is NOT a loading indicator**: Use `null` for "not loaded", `[]` for "loaded but empty"
- **ALWAYS diff desktop vs mobile implementations side by side** before committing
- **ALWAYS run `yarn tsc:staged` and `yarn lint:staged`** before pushing — type errors should never be caught by CI
- **Stop the fix-on-fix chain**: After 2 stacked fixes on the same code, revert and redesign holistically instead of incrementally patching
- **Inline `?? []` and `?? {}` in render paths are reference stability traps**: Use module-level constants or `useMemo`

### Tags
`race-condition` `async-loading` `reference-stability` `cross-platform` `fix-on-fix` `type-error` `pre-submit-checklist`

---

## Case 001: Dynamic Tabs Not Showing on Mobile Perps Token Selector

**Date**: 2026-02-06
**Project**: OneKey (app-monorepo)
**Severity**: Medium
**Platforms affected**: Mobile only
**Time to resolve**: ~19 hours (including 4 failed attempts)

### Symptom
Dynamic tabs (e.g., "Precious Metals") appeared on the desktop token selector but were missing on the mobile token selector.

### Wrong Hypotheses (Failed Attempts)
| # | Hypothesis | Fix Attempted | Why It Failed |
|---|-----------|---------------|---------------|
| 1 | Mobile is missing tab rendering code | Added dynamic tab rendering to a non-scrollable container | Tabs rendered but overflowed the narrow mobile screen — not scrollable |
| 2 | State atom not syncing from background to UI | Added `persist: true` to the atom | Atom was syncing fine — misdiagnosis |
| 3 | Global atom unreliable on React Native | Replaced atom read with direct service call | Same misdiagnosis — data layer was never the problem |

### Root Cause
**UI Layout layer issue**: The mobile tab container was a non-scrollable horizontal stack. When dynamic tabs were added, they overflowed the screen width. The state data was correct all along.

### Correct Fix
1. Searched codebase → found another component with a similar scrollable filter pattern
2. Extracted reusable `ScrollableFilterBar` component from it
3. Extracted shared tab validation hook for desktop/mobile
4. Used the state atom directly (no persistence change needed, no service call needed)

### Key Lessons
- **Always classify the bug layer first**: This was a UI overflow issue, not a data sync issue
- **Search for existing patterns**: Another component already had the scrollable solution
- **Desktop ≠ Mobile**: Wide screens mask overflow problems that are critical on narrow screens
- **Two-Strike Rule**: After 2 failed attempts on the same hypothesis, STOP and reclassify

### Tags
`state-misdiagnosis` `ui-overflow` `mobile-only` `cross-platform` `scrollable-container` `reusable-component`

---

## Case 004: Share Dialog Shows Stale Invitation Code on First Open

**Date**: 2026-02-07  |  **Project**: OneKey App Monorepo  |  **Platforms**: All (Web confirmed)

### Symptom
Gift icon share dialog shows a non-primary invitation code ("6S5L36") on first open; second open shows the correct primary code ("VIP999").

### Wrong Hypotheses (if any)
| # | Hypothesis | Why Wrong |
|---|-----------|-----------|
| — | All hypotheses pointed to the same root cause; H1 confirmed on first attempt | — |

### Root Cause
**State layer** — `getMyReferralCode()` uses a stale-while-revalidate pattern: returns cached SimpleDB value immediately, then fires `setTimeout(() => getSummaryInfo())` to update the cache asynchronously (~700ms later). For a one-shot Dialog that renders once and never re-renders, the stale value is displayed before the API response arrives.

Additionally, two different APIs write to the same `myReferralCode` cache field with different values:
- Login API (`serverUserInfo.inviteCode`) → writes the first/default code "6S5L36"
- Summary API (`/rebate/v1/invite/summary`) → writes the primary code "VIP999"

### Fix
Changed `shareReferRewards()` in `useReferFriends.tsx` to call `getSummaryInfo()` directly when logged in (awaiting the API response), with a `catch` fallback to `getMyReferralCode()` on network failure.

### Lessons
- Stale-while-revalidate is inappropriate for one-shot UI (dialogs, toasts, share sheets) that render once and don't observe state changes
- When multiple APIs write to the same cache field, the last writer wins — check which API runs last and whether it writes the correct value
- The codebase already had a correct pattern in `useReferralUrl.ts` (`getPrimaryInviteCode()`) that calls `getSummaryInfo()` directly — always search for existing patterns before implementing

### Tags
`stale-cache` `async-timing` `one-shot-dialog` `multiple-data-sources` `referral-code`

---

<!-- APPEND NEW CASES ABOVE THIS LINE -->
