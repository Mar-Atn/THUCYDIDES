# Calibration Memo: Cycle 6 — Maturity-Aware GDP Dampener

**Date:** 2026-04-02 | **Author:** SUPER EXPERT (Autonomous Calibration)
**File changed:** `app/engine/engines/economic.py` (lines 865-882)
**Layer 1 tests:** 70/70 PASSED

---

## Problem

Run #006 showed GDP growth still too high for mature economies, and the Cal-5 uniform GDP dampener was over-correcting emerging economies while under-correcting mature ones.

| Country | Run #006 (4yr) | Target (4yr) | Issue |
|---------|---------------|-------------|-------|
| Columbia (USA) | +24% | +8-12% | 2-3x too high |
| Cathay (China) | +14% | +18-22% | Too low |
| Yamato (Japan) | +16% | +4-6% | 3-4x too high |
| Bharata (India) | +5% | +25-30% | 5x too low |
| Gallia (France) | +5% | +4-5% | PASS |
| Teutonia (Germany) | +4% | +4-5% | PASS |

**Root cause:** The Cal-5 dampener `gdp_scale = 1/(1 + gdp/100)` penalized ALL large economies equally, regardless of whether they were mature (low structural growth) or emerging (high structural growth). Columbia (GDP 280, base 1.8%) and Cathay (GDP 190, base 4.0%) both got heavily dampened, but Cathay SHOULD be growing much faster.

## Solution: Two-Factor Maturity-Aware Dampener (Cal-6)

Replaced the uniform GDP dampener with a formula that accounts for both economy SIZE and MATURITY (structural growth potential):

```python
structural_rate = eco.get("gdp_growth_base", eco["gdp_growth_rate"])
maturity = clamp(structural_rate / 6.0, 0.3, 1.0)
gdp_scale = maturity / (1.0 + old_gdp / 200.0)
```

### How It Works

1. **Maturity factor** (0.3 to 1.0): Derived from the country's structural growth rate (from seed data). Mature economies (<1.8% base growth) get the floor of 0.3. Emerging economies (>=6% base growth) get 1.0. This is continuous, not a step function.

2. **Size factor**: Still `1/(1 + gdp/200)`, but with a higher threshold (200 vs 100) since the maturity factor now handles most of the dampening for mature economies.

3. **Combined**: `gdp_scale = maturity * size_factor`. The tech boost and momentum effect are multiplied by this combined scale.

### Key Property: SYSTEMIC, Not Country-Specific

The fix uses NO country-specific constants. The structural growth rate (`gdp_growth_base`) from the seed data is the only differentiator. Any country with high structural growth retains more of its tech/momentum bonus, regardless of absolute GDP size.

### Expected gdp_scale Values

| Country | GDP | Base % | Maturity | Size Factor | gdp_scale | Old scale |
|---------|-----|--------|----------|-------------|-----------|-----------|
| Columbia | 280 | 1.8 | 0.30 | 0.417 | 0.125 | 0.263 |
| Cathay | 190 | 4.0 | 0.667 | 0.513 | 0.342 | 0.345 |
| Yamato | 55 | 0.8 | 0.30 | 0.784 | 0.235 | 0.645 |
| Bharata | 42 | 6.5 | 1.00 | 0.826 | 0.826 | 0.704 |
| Gallia | 35 | 1.0 | 0.30 | 0.851 | 0.255 | 0.741 |
| Teutonia | 48 | 0.5 | 0.30 | 0.806 | 0.242 | 0.676 |
| Solaria | 11 | 3.0 | 0.50 | 0.948 | 0.474 | 0.901 |

### Expected Growth Projections (8 rounds)

Assuming ai_level 3 for Columbia/Cathay/Yamato, level 2 for Bharata, typical momentum:

| Country | Base/round | Tech contrib | Mom contrib | Est. total/round | Est. 8-round | Target |
|---------|-----------|-------------|------------|-----------------|-------------|--------|
| Columbia | 0.90% | 0.19% | ~0.03% | ~1.1% | ~9% | 8-12% |
| Cathay | 2.00% | 0.51% | ~0.09% | ~2.6% | ~21% | 18-22% |
| Yamato | 0.40% | 0.35% | ~0.02% | ~0.8% | ~6% | 4-6% |
| Bharata | 3.25% | 0.41% | ~0.02% | ~3.7% | ~29% | 25-30% |
| Gallia | 0.50% | 0.38% | ~0.01% | ~0.9% | ~7% | 4-5% |

**Note:** Gallia/Teutonia projections appear slightly high in isolation, but negative factors (tariffs, oil shocks, bilateral dependency) consistently pull them down by 0.3-0.5%/round in practice, as seen in runs #001-#006 where they already hit target at ~5% with the OLD (less aggressive) dampener.

## Risks

1. **Gallia/Teutonia may drop below target** if negative shocks are too strong combined with the new dampener. Monitor in run #007.
2. **Solaria (Saudi)** scale dropped from 0.90 to 0.47 -- may under-grow. But Solaria's growth is heavily oil-price-dependent, so the base formula contribution matters less.

## Verification

- Layer 1 engine tests: **70/70 PASSED** (no regressions)
- 3 pre-existing foundation test failures (stale DB assertions from prior runs, unrelated to this change)
- Diagnostic logging added: `gdp_scale` and `maturity` now appear in GDP growth log lines

## Next Step

Run #007 to validate. Key checkpoints:
- Columbia 8-12% (was 24%)
- Cathay 18-22% (was 14%)
- Yamato 4-6% (was 16%)
- Bharata 25-30% (was 5%)
- Gallia/Teutonia still 4-5% (was 5%/4%)
