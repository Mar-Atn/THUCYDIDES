# DET A2 — Data Calibration

**Version:** 1.0 | **Date:** 2026-04-01 | **Status:** Active
**Depends on:** SEED C4_DATA/countries.csv | CONTEXT/RESEARCH_* files
**Owner:** LEAD + BACKEND

---

## 1. Methodology

All starting data derives from real-world Q1 2026 values, abstracted into game units suitable for a 6-8 round simulation with 10+ countries. Primary sources:

- **GDP / Trade:** IMF World Economic Outlook (Jan 2026), World Bank
- **Military forces:** IISS Military Balance 2026, SIPRI databases
- **Nuclear:** FAS Nuclear Notebook, SIPRI Yearbook
- **Trade / sanctions:** WTO trade statistics, UNCTAD
- **Country research:** Six dedicated CONTEXT/RESEARCH_* briefs (Columbia, Cathay, Nordostan, Heartland, Persia, Europe)

**Scaling principle:** Real values are compressed into small integers (typically 0-280) so that players/AI can reason about them without calculators. Precision is sacrificed for playability; relative ratios matter more than absolute accuracy.

---

## 2. GDP Calibration

**Scaling factor: 1 coin ~ $10B real GDP (nominal, USD).**

| Country | Game GDP | Real Equivalent | Notes |
|---------|----------|----------------|-------|
| Columbia | 280 | US ~$28T | Largest economy, reference anchor |
| Cathay | 190 | China ~$19T | PPP would be higher; nominal used for trade realism |
| Teutonia | 45 | Germany ~$4.5T | Largest European economy |
| Yamato | 43 | Japan ~$4.3T | |
| Bharata | 42 | India ~$4.2T | High growth (6.5%) compensates for lower base |
| Gallia | 34 | France ~$3.4T | |
| Albion | 33 | UK ~$3.3T | |
| Ponte | 22 | Italy ~$2.2T | |
| Sarmatia | 20 | Russia ~$2.0T | Nominal GDP; PPP ~$5T not used |
| Hanguk | 18 | South Korea ~$1.8T | |

Minor economies (Persia 5, Levantia 5, Mirage 5, Phrygia 11, etc.) are rounded to nearest integer. Sub-$100B economies (Choson 0.3, Ruthenia 2.2, Caribe 2) keep one decimal for differentiation.

**Growth rates** reflect real IMF projections: Bharata 6.5%, Cathay 4.0%, Freeland 3.7%. Negative growth for sanctioned states: Persia -3.0%, Caribe -1.0%.

---

## 3. Military Calibration

**Ground units:** 1 unit ~ 1 division-equivalent (~10,000-15,000 troops with equipment). Reserves and mobilization pools are separate.

| Country | Ground | Real Basis |
|---------|--------|-----------|
| Cathay | 25 | PLA ~2M active, largest standing army, but limited expeditionary capability |
| Columbia | 22 | ~1.3M active + reserves; higher readiness and global deployment |
| Sarmatia | 18 | ~1M active (post-attrition); large on paper, degraded quality |
| Bharata | 12 | ~1.4M active; large but lower per-unit capability |
| Ruthenia | 10 | ~800K mobilized (wartime footing); high motivation, lower equipment |

**Naval units:** 1 unit ~ carrier group or major surface flotilla. Columbia 11 (11 carrier groups), Cathay 7 (growing blue-water navy), Sarmatia 2 (Black Sea + Northern Fleet remnants).

**Tactical air:** Abstracted similarly. Columbia 15 reflects ~5,000 combat aircraft; Cathay 12 reflects ~3,000.

**Strategic missiles:** Non-nuclear ballistic/cruise missile capability. Added to latent nuclear nations to represent indigenous missile programs: Yamato 2, Bharata 2, Levantia 2, Teutonia 1, Hanguk 1.

---

## 4. Key Calibration Fixes

These corrections were made during design playtest sessions to prevent degenerate game states:

### 4.1 Ruthenia Treasury: 1 -> 5
Ruthenia's per-round maintenance cost is ~4.2 coins (10 ground units + 3 tactical air at 0.3/unit). With treasury=1, Ruthenia would be bankrupt before completing Round 0 orders. Raised to 5 to give ~1 round of operational buffer, reflecting real Western aid flows.

### 4.2 Persia Nuclear R&D Progress: 0.60 -> 0.30
The L0-to-L1 nuclear breakout threshold is 0.60. Starting at 0.60 meant Persia would auto-achieve nuclear weapons at Round 1 with zero investment, eliminating the "will they or won't they" tension that drives Persia's entire storyline. Reduced to 0.30: breakout requires ~2-3 rounds of dedicated R&D, creating a decision window.

### 4.3 Hanguk Naval: 0 -> 2
South Korea operates a substantial navy (~170 vessels including Aegis destroyers). Zero naval was a data entry error. Set to 2 to reflect a credible regional naval force.

### 4.4 Mirage Tax Rate: 0 -> 0.15
UAE collects no income tax in reality, but the game's tax_rate represents total government revenue extraction (including oil revenue, fees, sovereign wealth returns). Zero tax meant zero revenue generation. Set to 0.15 to reflect actual fiscal capacity.

### 4.5 Strategic Missiles for Latent Nuclear Nations
Countries with advanced missile programs but no nuclear weapons received strategic_missiles values to represent delivery-capable conventional systems: Yamato 2 (solid-fuel space launch), Teutonia 1 (European missile participation), Bharata 2 (Agni program), Levantia 2 (Jericho program), Hanguk 1 (Hyunmoo program).

### 4.6 Sanctions Imposer Cost: Full GDP-Weighted Formula
Early formula used a 0.012 multiplier on imposer GDP, making sanctions nearly free for Columbia. Replaced with full GDP-weighted cost reflecting real trade disruption, lost contracts, and enforcement overhead. Sanctioning is now a meaningful economic sacrifice.

### 4.7 Combat: Die Hard + Air Support Non-Stacking
Die Hard (defensive terrain bonus) and air support both grant positional advantage. Allowing both to stack made fortified positions with air cover nearly impregnable. Rule: maximum positional modifier is +1, regardless of source combination.

---

## 5. Balance Targets

The data was calibrated against five simulation-level balance constraints:

| Target | Mechanism | How Data Supports It |
|--------|-----------|---------------------|
| **No elimination before R4** | Minimum treasury buffers, maintenance costs | Even Ruthenia (weakest economy) survives ~3 rounds with aid |
| **Sarmatia economic clock ~R3-4** | GDP 20, growth 1.0%, war maintenance ~6/round | Sarmatia bleeds ~3-4 coins/round net; treasury 6 lasts ~R3 without trade |
| **Columbia election meaningful at R5** | dem_rep_split 48/52, political_support 7 | Tight partisan split means war tiredness or economic cost can flip support |
| **Formosa invasion probability 15-25%** | Cathay ground 25 vs Formosa 4 + naval gap + Columbia response | Cathay CAN invade but faces naval crossing, air defense 2, and likely Columbia intervention |
| **Nuclear proliferation tension** | Persia 0.30 progress, Choson L1, latent nations at 0.0 | 2-3 nations could proliferate by R5-6; none automatically do |

These targets are validated through Layer 3 (full unmanned simulation) testing. If any target is consistently missed across 10+ runs, the underlying data must be recalibrated.

---

*End of DET A2. Source data: `2 SEED/C_MECHANICS/C4_DATA/countries.csv`. Formula specs: `DET_C1_SYSTEM_CONTRACTS.md`.*
