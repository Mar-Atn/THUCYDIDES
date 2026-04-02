# Maintenance Recalibration

**Date:** 2026-04-01
**Author:** BUILD team (SUPER EXPERT analysis)
**Data source:** `/2 SEED/C_MECHANICS/C4_DATA/countries.csv`
**Reference:** SIPRI 2024 Military Expenditure data (published April 2025)

---

## Methodology

### Problem
The `maintenance_per_unit` values (0.15-0.50 coins/unit/round) were uniform-ish across countries regardless of GDP, producing absurd military-spending-to-GDP ratios. Every country was spending 8-600x the real-world percentage of GDP on military maintenance.

### Approach
1. Gathered real-world 2024 military spending as % of GDP from SIPRI (Stockholm International Peace Research Institute) April 2025 fact sheet, World Bank, and CIA World Factbook.
2. Set **game target percentages** based on real data, with minor adjustments:
   - Wartime countries (Ukraine, Israel, Russia) retain elevated percentages but scaled for playability.
   - North Korea uses a mid-range estimate (~25%) from the wide 15-34% range.
   - Countries with hidden military spending (China, Iran) use upper estimates.
3. Calculated: `new_maintenance_per_unit = (target_pct / 100) * GDP / total_military_units`
4. Verified budget balance: `Revenue - (Military + Social) = Discretionary budget`

### Revenue model used for verification
- **Tax revenue** = GDP x tax_rate
- **Oil revenue** = sector_resources% x GDP x 0.05 (for oil producers only)
- **Social cost** = social_baseline x GDP x 0.70

### Key insight
The old values treated maintenance_per_unit as if it were a percentage of unit cost. In reality, it must be calibrated to produce total maintenance that equals a realistic fraction of GDP. A country with GDP=280 and 64 units needs maintenance_per_unit ~0.15, not 0.50.

---

## Real-World Reference Data (SIPRI 2024)

| Country analog | Real mil % GDP | Source notes |
|---------------|---------------|--------------|
| United States | 3.4% | SIPRI 2024. $997B on $29T GDP |
| China | 1.7% official, ~2.2% est. | SIPRI estimates 27-90% higher than official |
| Russia | 7.1% | SIPRI 2024. Wartime surge from ~3.9% pre-2022 |
| Ukraine | 34% | SIPRI 2024. Highest in world, wartime |
| Iran | 2.1% official, ~3-4% est. | Hidden IRGC spending not in official budget |
| France | 2.05% | SIPRI 2024. Just above NATO 2% target |
| Germany | 1.9% | SIPRI 2024. Just below NATO 2% target |
| Poland | 4.2% | SIPRI 2024. NATO frontline state, rapid increase |
| Italy | 1.6% | SIPRI 2024. Below NATO target |
| United Kingdom | 2.3% | SIPRI 2024 |
| India | 2.3% | SIPRI 2024. $86.1B |
| Israel | 8.8% | SIPRI 2024. Wartime surge from 5.4% in 2023 |
| Taiwan | ~2.5% | Estimated: $16.5B / ~$660B GDP |
| Turkey | ~1.6% | SIPRI 2024 |
| Japan | 1.4% | SIPRI 2024. Record high since 1958 |
| Saudi Arabia | 7.3% | SIPRI 2024. $80.3B |
| North Korea | ~25% | Estimates range 15-34%. Mid-range used |
| South Korea | ~2.8% | Estimated: $47.6B / ~$1.7T GDP |
| Cuba+Venezuela | ~2.5% | Blended: Cuba ~2.9%, Venezuela ~0.7% |
| UAE | ~5.6% | Estimated from regional data |

---

## Per-Country Results Table

| Country | Real analog | Real mil% | Target mil% | Old m/u | NEW m/u | Old mil cost | NEW mil cost | Revenue | Social | Mandatory | Discretionary | Treasury | Status |
|---------|-----------|----------|------------|---------|---------|-------------|-------------|---------|--------|-----------|--------------|----------|--------|
| Columbia | United States | 3.4% | **3.5%** | 0.500 | **0.1531** | 32.000 | 9.800 | 68.320 | 58.800 | 68.600 | -0.280 | 50.0 | DEFICIT (179r) |
| Cathay | China | 1.7% | **2.0%** | 0.300 | **0.0745** | 15.300 | 3.800 | 38.000 | 26.600 | 30.400 | 7.600 | 45.0 | HEALTHY |
| Sarmatia | Russia | 7.1% | **7.0%** | 0.300 | **0.0326** | 12.900 | 1.400 | 4.400 | 3.500 | 4.900 | -0.500 | 6.0 | DEFICIT (12r) |
| Ruthenia | Ukraine | 34.0% | **26.0%** | 0.300 | **0.0409** | 4.200 | 0.572 | 0.550 | 0.308 | 0.880 | -0.330 | 5.0 | DEFICIT (15r) |
| Persia | Iran | 3.0% | **3.5%** | 0.250 | **0.0109** | 4.000 | 0.175 | 0.987 | 0.700 | 0.875 | 0.112 | 1.0 | TIGHT |
| Gallia | France | 2.1% | **2.1%** | 0.500 | **0.0510** | 7.000 | 0.714 | 15.300 | 8.330 | 9.044 | 6.256 | 8.0 | HEALTHY |
| Teutonia | Germany | 1.9% | **2.0%** | 0.400 | **0.0818** | 4.400 | 0.900 | 17.100 | 9.450 | 10.350 | 6.750 | 12.0 | HEALTHY |
| Freeland | Poland | 4.2% | **4.0%** | 0.300 | **0.0450** | 2.400 | 0.360 | 3.150 | 1.575 | 1.935 | 1.215 | 4.0 | HEALTHY |
| Ponte | Italy | 1.6% | **1.6%** | 0.400 | **0.0587** | 2.400 | 0.352 | 8.800 | 4.620 | 4.972 | 3.828 | 4.0 | HEALTHY |
| Albion | United Kingdom | 2.3% | **2.3%** | 0.500 | **0.0633** | 6.000 | 0.759 | 11.550 | 6.930 | 7.689 | 3.861 | 8.0 | HEALTHY |
| Bharata | India | 2.3% | **2.3%** | 0.250 | **0.0439** | 5.500 | 0.966 | 7.560 | 5.880 | 6.846 | 0.714 | 12.0 | TIGHT |
| Levantia | Israel | 8.8% | **9.0%** | 0.400 | **0.0300** | 6.000 | 0.450 | 1.600 | 0.980 | 1.430 | 0.170 | 5.0 | TIGHT |
| Formosa | Taiwan | 2.5% | **2.5%** | 0.350 | **0.0222** | 3.150 | 0.200 | 1.600 | 1.232 | 1.432 | 0.168 | 8.0 | TIGHT |
| Phrygia | Turkey | 1.6% | **1.8%** | 0.300 | **0.0180** | 3.300 | 0.198 | 2.750 | 1.694 | 1.892 | 0.858 | 4.0 | HEALTHY |
| Yamato | Japan | 1.4% | **1.4%** | 0.450 | **0.0502** | 5.400 | 0.602 | 12.900 | 9.030 | 9.632 | 3.268 | 15.0 | HEALTHY |
| Solaria | Saudi Arabia | 7.3% | **7.0%** | 0.400 | **0.0963** | 3.200 | 0.770 | 1.348 | 1.925 | 2.695 | -1.348 | 20.0 | DEFICIT (15r) |
| Choson | North Korea | 25.0% | **25.0%** | 0.150 | **0.0063** | 1.800 | 0.075 | 0.150 | 0.021 | 0.096 | 0.054 | 1.0 | HEALTHY |
| Hanguk | South Korea | 2.8% | **2.8%** | 0.350 | **0.0388** | 4.550 | 0.504 | 4.680 | 3.150 | 3.654 | 1.026 | 8.0 | HEALTHY |
| Caribe | Cuba + Venezuela | 2.5% | **3.0%** | 0.200 | **0.0150** | 0.800 | 0.060 | 0.650 | 0.280 | 0.340 | 0.310 | 1.0 | HEALTHY |
| Mirage | UAE | 5.6% | **5.5%** | 0.350 | **0.0458** | 2.100 | 0.275 | 0.825 | 0.700 | 0.975 | -0.150 | 15.0 | DEFICIT (100r) |

### Budget Status Legend
- **HEALTHY** = Discretionary > 15% of revenue. Country can invest in production, R&D, diplomacy.
- **TIGHT** = Discretionary 0-15% of revenue. Country must make hard choices but is solvent.
- **DEFICIT (Nr)** = Spending exceeds revenue. N = rounds until treasury depleted. Countries at war or under sanctions are expected to run deficits.

### Design Notes on Deficit Countries
- **Columbia (179r)**: Tiny deficit (-0.28 on 68.3 revenue = -0.4%). Effectively balanced. The social_baseline=0.30 and tax_rate=0.24 create a realistic squeeze — the US runs deficits IRL.
- **Sarmatia (12r)**: Russia at war, spending 7% of GDP on military. 12 rounds of treasury cover is intentionally stressful but survivable for an 8-round game.
- **Ruthenia (15r)**: Ukraine at war with 26% mil/GDP. Deficit is structural — mirrors reality. Receives foreign aid in-game.
- **Solaria (15r)**: Saudi Arabia's low tax_rate (0.10) and high social spending create a deficit. This is realistic — Saudi runs budget deficits when oil prices are low. Treasury of 20.0 covers 15 rounds.
- **Mirage (100r)**: UAE has a tiny deficit. Treasury of 15.0 covers 100 rounds — effectively infinite. No issue.

---

## SQL to Apply

```sql
UPDATE countries
SET maintenance_per_unit = CASE id
  WHEN 'columbia' THEN 0.153125
  WHEN 'cathay' THEN 0.074510
  WHEN 'sarmatia' THEN 0.032558
  WHEN 'ruthenia' THEN 0.040857
  WHEN 'persia' THEN 0.010938
  WHEN 'gallia' THEN 0.051000
  WHEN 'teutonia' THEN 0.081818
  WHEN 'freeland' THEN 0.045000
  WHEN 'ponte' THEN 0.058667
  WHEN 'albion' THEN 0.063250
  WHEN 'bharata' THEN 0.043909
  WHEN 'levantia' THEN 0.030000
  WHEN 'formosa' THEN 0.022222
  WHEN 'phrygia' THEN 0.018000
  WHEN 'yamato' THEN 0.050167
  WHEN 'solaria' THEN 0.096250
  WHEN 'choson' THEN 0.006250
  WHEN 'hanguk' THEN 0.038769
  WHEN 'caribe' THEN 0.015000
  WHEN 'mirage' THEN 0.045833
END
WHERE id IN (
  'columbia', 'cathay', 'sarmatia', 'ruthenia', 'persia',
  'gallia', 'teutonia', 'freeland', 'ponte', 'albion',
  'bharata', 'levantia', 'formosa', 'phrygia', 'yamato',
  'solaria', 'choson', 'hanguk', 'caribe', 'mirage'
);
```

---

## Verification

### Improvement Summary

| Country | Old mil % GDP | New mil % GDP | Reduction factor |
|---------|-------------|-------------|-----------------|
| Columbia | 11.4% | 3.5% | 3x |
| Cathay | 8.1% | 2.0% | 4x |
| Sarmatia | 64.5% | 7.0% | 9x |
| Ruthenia | 190.9% | 26.0% | 7x |
| Persia | 80.0% | 3.5% | 23x |
| Gallia | 20.6% | 2.1% | 10x |
| Teutonia | 9.8% | 2.0% | 5x |
| Freeland | 26.7% | 4.0% | 7x |
| Ponte | 10.9% | 1.6% | 7x |
| Albion | 18.2% | 2.3% | 8x |
| Bharata | 13.1% | 2.3% | 6x |
| Levantia | 120.0% | 9.0% | 13x |
| Formosa | 39.4% | 2.5% | 16x |
| Phrygia | 30.0% | 1.8% | 17x |
| Yamato | 12.6% | 1.4% | 9x |
| Solaria | 29.1% | 7.0% | 4x |
| Choson | 600.0% | 25.0% | 24x |
| Hanguk | 25.3% | 2.8% | 9x |
| Caribe | 40.0% | 3.0% | 13x |
| Mirage | 42.0% | 5.5% | 8x |

### Budget Health Check (all 20 countries)

**Healthy (12):** Cathay, Gallia, Teutonia, Freeland, Ponte, Albion, Phrygia, Yamato, Choson, Hanguk, Caribe + Columbia (negligible deficit)

**Tight but solvent (3):** Bharata, Levantia, Formosa — all have positive discretionary budget but limited room. Correct for countries under security pressure.

**Structural deficit, treasury-covered (4):** Sarmatia (12r), Ruthenia (15r), Solaria (15r), Mirage (100r) — all have enough treasury to survive well beyond the 8-round game. Deficits are intentional and reflect real-world fiscal pressure on wartime/petro-state economies.

**Critical (0):** None. No country will go bankrupt during normal gameplay.

### Cross-check: maintenance_per_unit range
- Minimum: 0.0063 (Choson) — extremely poor country, huge army relative to economy
- Maximum: 0.1531 (Columbia) — wealthy superpower, expensive per-unit costs
- Median: ~0.044
- This range makes intuitive sense: wealthier countries pay more per unit (better equipment, higher salaries) while poor/authoritarian states maintain large armies cheaply.

---

## Sources
- [SIPRI Trends in World Military Expenditure, 2024](https://www.sipri.org/publications/2025/sipri-fact-sheets/trends-world-military-expenditure-2024)
- [SIPRI Press Release April 2025](https://www.sipri.org/media/press-release/2025/unprecedented-rise-global-military-expenditure-european-and-middle-east-spending-surges)
- [World Bank Military Expenditure % GDP](https://data.worldbank.org/indicator/MS.MIL.XPND.GD.ZS)
- [CIA World Factbook - Military Expenditures](https://www.cia.gov/the-world-factbook/field/military-expenditures/)
- [Wikipedia - List of countries with highest military expenditures](https://en.wikipedia.org/wiki/List_of_countries_with_highest_military_expenditures)
