# CONTRACT: Assassination

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §6.2

---

## 1. PURPOSE

Targeted killing of a specific role. Card-based (consumable).
Moderator-confirmed. Always detected (100%), attribution 50%.

---

## 2. PROBABILITY

| Scenario | Success |
|---|---|
| Domestic | **30%** |
| International | **20%** |
| Involving Levantia | **50%** |

On success: **50/50** kill vs survive-injured.

---

## 3. EFFECTS

| Outcome | Target | Target country |
|---|---|---|
| **Kill** | `run_roles.status = 'killed'` | `political_support +15` (martyr) |
| **Survive** | stays active (injured) | `political_support +10` (sympathy) |
| **Failure** | untouched | no effect |

Detection: **100%** — always public, everyone knows an attempt was made.
Attribution: **50%** — who ordered it.

---

## 4. LOCKED INVARIANTS

1. Card-based: `assassination_cards` (consumable)
2. Moderator-confirmed (auto in unmanned)
3. 100% detection (always public)
4. 50% attribution
5. Kill/survive is 50/50 (on success)
6. Uses `run_roles` for status change
7. `precomputed_rolls` hook for all 3 rolls (success, kill, attribution)
