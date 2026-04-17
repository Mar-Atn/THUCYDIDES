# CONTRACT: Exchange Transaction v2.0

**Date:** 2026-04-17 | **Status:** ACTIVE
**Replaces:** transaction_validator.py personal scope logic

---

## 1. Scope

Country-to-country transactions only. No personal scope.

## 2. Tradeable Assets

| Asset | Offer (what you give) | Request (what you ask for) |
|-------|----------------------|---------------------------|
| **Coins** | Specific amount from treasury | Specific amount |
| **Military Units** | Specific unit_ids (RESERVE only) | Type + count (system auto-selects) |
| **Technology** | Nuclear or AI level (your level or lower) | Nuclear or AI level |
| **Basing Rights** | Grant: other country can place units on your territory | Request: access to their territory |

## 3. Rules

- **Units offered:** must be in RESERVE status, specified by unit_id
- **Units requested:** specified by type + count only (proposer doesn't know counterpart's specific units)
- **Tech transfer:** sets recipient to that level. Nuclear still requires test/confirmation for military use.
- **Basing rights:** blanket access to place units on any hex of the granting country's territory
- **Unilateral:** one side of offer/request can be empty (gifts, aid requests)
- **Visibility:** public by default, toggle for secret deal
- **Comments:** free text field on proposal and response

## 4. Flow

1. **Propose:** Proposer fills form → system validates proposer's assets → creates PENDING record
2. **Notify:** Counterpart's HoS + Diplomat see proposal in "Actions Expected Now"
3. **Accept:** Counterpart clicks Accept → system checks counterpart has requested assets:
   - Coins: treasury >= requested amount
   - Units: enough reserve units of requested type
   - Tech: has the requested level
   - Basing: owns territory
   - If ANY missing → system shows what's missing, blocks accept
   - If all available → transaction executes atomically
4. **Reject:** Counterpart declines. Proposer notified.
5. **Counter-offer:** Counterpart modifies terms → new proposal (original cancelled)

## 5. Execution (on Accept)

Atomic — all or nothing:
- Coins: debit proposer treasury, credit counterpart (and vice versa)
- Units offered: change `country_id` on those specific deployment rows
- Units requested: system picks N reserve units of requested type from counterpart, changes `country_id`
- Tech: set recipient's nuclear_level or ai_level (nuclear: nuclear_confirmed = false)
- Basing rights: update relationships table basing_rights_a_to_b / b_to_a

## 6. Authorization

- **Propose:** HoS, Diplomat, Economy Officer (any with `propose_transaction` in role_actions)
- **Accept/Reject:** HoS, Diplomat of counterpart country (first responder wins)

## 7. Deprecated

- Personal scope removed (no personal coins in game)
- Personal role-to-role transactions removed
