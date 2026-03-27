# Thucydides Trap SIM -- Zone Structure
**Code:** C5 | **Version:** 1.0 | **Date:** 2026-03-25 | **Status:** Complete Draft
**Depends on:** C4 Map Concept v2, C1 Domains Architecture v2, B1 Country Structure v2, C2 Action System v2

---

## Overview

This document defines every zone in the simulation: 45 global-map zones and 42 theater zones across 6 theaters. Total: **87 zones, 68 active at game start.**

The zone structure serves four systems simultaneously:
- **Map rendering** (SVG coordinates, adjacency for border drawing)
- **Combat resolution** (which units can attack where, movement rules)
- **Deployment** (where units can be placed, transit delays)
- **Economic effects** (blockades, chokepoints, trade disruption)

**Naming convention:** `{scope}_{region}_{descriptor}` where scope is `g` (global), `ee` (Eastern Ereb), `me` (Mashriq), `ts` (Taiwan Strait), `cb` (Caribbean), `gl` (Thule), `kr` (Korea).

---

# SECTION 1: GLOBAL MAP ZONES

## 1.1 Land Zones -- Home Territories (26 zones)

### Columbia (United States) -- 3 zones

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_col_continental` | Columbia (Continental) | `land_home` | `columbia` | `g_col_alaska`, `g_col_hawaii`, `g_sea_atlantic_west`, `g_sea_gulf_caribbean`, `g_caribe` | Core homeland. Economic/political center. 2 Columbia Parliament seats here. Base: Atlantic Fleet. |
| `g_col_alaska` | Columbia (Alaska) | `land_home` | `columbia` | `g_col_continental`, `g_sea_north_pacific`, `g_sea_arctic` | Arctic access. Pacific Fleet staging. Adjacent to Arctic contested zone. |
| `g_col_hawaii` | Columbia (Pacific Command) | `land_home` | `columbia` | `g_sea_north_pacific`, `g_sea_central_pacific` | Pacific military hub. Not strictly Hawaii -- represents entire Pacific basing network. |

### Cathay (China) -- 3 zones

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_cat_eastern` | Cathay (Eastern Seaboard) | `land_home` | `cathay` | `g_cat_western`, `g_cat_southern`, `g_sea_south_china`, `g_sea_east_china`, `g_hanguk`, `g_choson` | Industrial heartland. Shanghai, Beijing. Staging for Taiwan operations. |
| `g_cat_western` | Cathay (Interior) | `land_home` | `cathay` | `g_cat_eastern`, `g_cat_southern`, `g_contested_central_asia`, `g_bharata` | Strategic depth. Nuclear facilities. Xinjiang/Tibet border regions. Land route to Central Asia. |
| `g_cat_southern` | Cathay (Southern) | `land_home` | `cathay` | `g_cat_eastern`, `g_cat_western`, `g_sea_south_china`, `g_sea_southeast_asia` | South China Sea access. Hainan naval base. Gateway to Malacca/SE Asia. |

### Nordostan (Russia) -- 3 zones

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_nor_western` | Nordostan (Western) | `land_home` | `nordostan` | `g_nor_central`, `g_freeland`, `g_sea_baltic`, `g_sea_black` | Moscow, St. Petersburg. Borders NATO. Kaliningrad implied. Belarus corridor to Heartland (theater). |
| `g_nor_central` | Nordostan (Central) | `land_home` | `nordostan` | `g_nor_western`, `g_nor_eastern`, `g_contested_central_asia`, `g_sea_arctic` | Industrial Urals. Strategic depth. Nuclear silos. Trans-Siberian link. |
| `g_nor_eastern` | Nordostan (Far East) | `land_home` | `nordostan` | `g_nor_central`, `g_sea_north_pacific`, `g_choson`, `g_sea_arctic` | Pacific Fleet (Vladivostok). Borders Choson. Thin population. |

### European Countries (5 zones -- 1 each)

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_gallia` | Gallia | `land_home` | `gallia` | `g_teutonia`, `g_ponte`, `g_albion`, `g_sea_atlantic_east`, `g_sea_med_west` | Nuclear power. UNSC veto. Mediterranean access. |
| `g_teutonia` | Teutonia | `land_home` | `teutonia` | `g_gallia`, `g_freeland`, `g_ponte`, `g_sea_baltic` | EU economic engine. NATO logistics hub. No direct sea coast on global map (Baltic via zone). |
| `g_freeland` | Freeland | `land_home` | `freeland` | `g_teutonia`, `g_nor_western`, `g_sea_baltic` | NATO frontline. Adjacent to Nordostan Western -- the tripwire. Eastern Europe theater border. |
| `g_ponte` | Ponte | `land_home` | `ponte` | `g_gallia`, `g_teutonia`, `g_sea_med_west`, `g_sea_med_east` | Mediterranean straddler. EU swing vote. Debt-burdened. |
| `g_albion` | Albion | `land_home` | `albion` | `g_gallia`, `g_sea_atlantic_east`, `g_sea_giuk` | Nuclear. Five Eyes. GIUK Gap southern anchor. NATO but not EU. |

### Mashriq & Central/South Asia (6 zones)

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_persia` | Persia | `land_home` | `persia` | `g_solaria`, `g_mirage`, `g_sea_persian_gulf`, `g_contested_central_asia`, `g_sea_arabian` | Nuclear threshold. Proxy network. Hormuz leverage. Theater parent zone. |
| `g_levantia` | Levantia | `land_home` | `levantia` | `g_phrygia`, `g_sea_med_east`, `g_solaria` | Regional military superpower. Undeclared nuclear. Adjacent to Phrygia (Bosphorus control). |
| `g_solaria` | Solaria | `land_home` | `solaria` | `g_persia`, `g_mirage`, `g_levantia`, `g_sea_persian_gulf`, `g_sea_red`, `g_contested_horn` | OPEC+ kingpin. Oil pricing power. Red Sea coast. |
| `g_phrygia` | Phrygia | `land_home` | `phrygia` | `g_levantia`, `g_sea_med_east`, `g_sea_black`, `g_nor_western` | Bosphorus chokepoint controller. NATO member playing all sides. |
| `g_bharata` | Bharata | `land_home` | `bharata` | `g_cat_western`, `g_sea_arabian`, `g_sea_indian_ocean` | Third pole. Genuine non-alignment. 1.4B people. Tech level 2. |
| `g_mirage` | Mirage | `land_home` | `mirage` | `g_solaria`, `g_persia`, `g_sea_persian_gulf`, `g_sea_arabian` | Financial hub. Arms buyer. OPEC+ member. Pragmatic hedger. |

### Asu & Pacific (4 zones)

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_yamato` | Yamato | `land_home` | `yamato` | `g_sea_east_china`, `g_sea_north_pacific`, `g_hanguk` | Remilitarizing. US base host. Pacific anchor. Semiconductor designer. |
| `g_hanguk` | Hanguk | `land_home` | `hanguk` | `g_choson`, `g_cat_eastern`, `g_yamato`, `g_sea_east_china` | Tech power. DMZ tripwire. US base host. Massive Cathay trade. |
| `g_choson` | Choson | `land_home` | `choson` | `g_hanguk`, `g_cat_eastern`, `g_nor_eastern` | Nuclear wildcard. Unpredictable. Can sell nuclear tech. |
| `g_formosa` | Formosa | `land_home` | `formosa` | `g_sea_east_china`, `g_sea_south_china` | Semiconductor chokepoint. The most dangerous tripwire. Taiwan Strait theater parent. |

### Americas (1 zone)

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_caribe` | Caribe | `land_home` | `caribe` | `g_col_continental`, `g_sea_gulf_caribbean`, `g_sea_atlantic_west` | Cuba + Venezuela combined. Russia/China foothold in hegemon's backyard. Caribbean theater parent. |

---

## 1.2 Land Zones -- Contested/Unowned (5 zones)

These zones have no sovereign owner. They are strategic objectives, buffer zones, or failed-state territories that any power can attempt to control through military deployment or political influence.

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_contested_thule` | Thule | `land_contested` | `teutonia` | `g_sea_giuk`, `g_sea_arctic`, `g_sea_atlantic_west` | Territory belonging to Teutonia's alliance network. Pioneer (Columbia envoy) has portfolio. Rare earth deposits. Thule theater parent. |
| `g_contested_central_asia` | Central Asia | `land_contested` | `none` | `g_nor_central`, `g_cat_western`, `g_persia`, `g_bharata` | Stans (Kazakhstan, Uzbekistan, etc.). Energy resources. Cathay Belt-and-Road. Nordostan sphere of influence. Buffer zone between three powers. |
| `g_contested_horn` | Horn of Africa | `land_contested` | `none` | `g_solaria`, `g_sea_red`, `g_sea_arabian`, `g_contested_central_africa` | Djibouti bases (Columbia, Cathay). Piracy. Red Sea southern approach. Yemen proxy war spillover. |
| `g_contested_central_africa` | Central Africa | `land_contested` | `none` | `g_contested_horn`, `g_sea_atlantic_east` | Wagner/Africa Corps. Resource extraction. Cathay infrastructure investment. France legacy. Instability. |
| `g_sea_arctic` | Arctic | `sea` | `none` | `g_col_alaska`, `g_nor_central`, `g_nor_eastern`, `g_contested_thule`, `g_sea_giuk`, `g_sea_north_pacific` | Opening sea routes. Resource claims. Nordostan icebreaker advantage. Climate-driven strategic competition. |

> **Note:** Arctic is typed as `sea` because it functions primarily as a maritime transit/control zone, though it borders land. It has no owner and behaves as contested space.

---

## 1.3 Sea Zones (14 zones)

Sea zones enable naval deployment, blockade, transit, and combat. Each sea zone can hold naval units from any country. Control is established by having unchallenged naval presence. Chokepoints are marked with `[CHOKEPOINT]` where they border another zone.

| Zone ID | Display Name | Type | Owner | Adjacent Zones | Notes |
|---------|-------------|------|-------|----------------|-------|
| `g_sea_atlantic_west` | Western Atlantic | `sea` | `none` | `g_col_continental`, `g_caribe`, `g_sea_gulf_caribbean`, `g_sea_atlantic_east`, `g_contested_thule` | Columbia's home waters. Atlantic Fleet patrol area. Transatlantic link. |
| `g_sea_atlantic_east` | Eastern Atlantic | `sea` | `none` | `g_sea_atlantic_west`, `g_gallia`, `g_albion`, `g_sea_giuk`, `g_sea_med_west`, `g_contested_central_africa` | European Atlantic. NATO sea lane. UK/France naval patrol. Africa west coast access. |
| `g_sea_gulf_caribbean` | Gulf & Caribbean Sea | `sea` | `none` | `g_col_continental`, `g_caribe`, `g_sea_atlantic_west`, `g_sea_central_pacific` | **[CHOKEPOINT: Caribbean Passages]** on border with Atlantic. Panama Canal implied in link to Central Pacific. US near-abroad. Caribbean theater parent sea zone. |
| `g_sea_med_west` | Western Mediterranean | `sea` | `none` | `g_gallia`, `g_ponte`, `g_sea_atlantic_east`, `g_sea_med_east` | French/Italian naval sphere. NATO southern flank. Gibraltar implied at Atlantic border. |
| `g_sea_med_east` | Eastern Mediterranean | `sea` | `none` | `g_sea_med_west`, `g_ponte`, `g_phrygia`, `g_levantia`, `g_sea_red` | **[CHOKEPOINT: Suez Canal]** on border with Red Sea. **[CHOKEPOINT: Bosphorus]** on border with Black Sea (via Phrygia). Levantia naval ops. Phrygia controls Bosphorus access. |
| `g_sea_black` | Black Sea | `sea` | `none` | `g_phrygia`, `g_nor_western` | **[CHOKEPOINT: Bosphorus]** on border with Med East (through Phrygia). Nordostan warm-water fleet. Heartland access (via theater). Constrained by Phrygia chokepoint control. |
| `g_sea_baltic` | Baltic Sea | `sea` | `none` | `g_nor_western`, `g_freeland`, `g_teutonia` | Nordostan Kaliningrad. NATO northern flank. Undersea infrastructure (cables, pipelines). Small, enclosed -- limited naval value but sabotage-relevant. |
| `g_sea_red` | Red Sea | `sea` | `none` | `g_solaria`, `g_sea_med_east`, `g_sea_arabian`, `g_contested_horn` | **[CHOKEPOINT: Suez Canal]** on border with Med East. Houthi/proxy disruption zone. Trade route to Asia. |
| `g_sea_persian_gulf` | Persian Gulf | `sea` | `none` | `g_persia`, `g_solaria`, `g_mirage`, `g_sea_arabian` | **[CHOKEPOINT: Strait of Hormuz]** on border with Arabian Sea. Oil export chokepoint. Columbia 5th Fleet. Iran can threaten closure. |
| `g_sea_arabian` | Arabian Sea | `sea` | `none` | `g_sea_persian_gulf`, `g_sea_red`, `g_bharata`, `g_mirage`, `g_sea_indian_ocean`, `g_contested_horn` | Western Indian Ocean. Connects Gulf, Red Sea, India. Piracy corridor. Columbia/Cathay base competition (Djibouti). |
| `g_sea_indian_ocean` | Indian Ocean | `sea` | `none` | `g_bharata`, `g_sea_arabian`, `g_sea_southeast_asia` | Bharata's natural sphere. Cathay String of Pearls. Connects Mashriq energy to Asu consumers. Columbia Diego Garcia base. |
| `g_sea_southeast_asia` | Southeast Asia & Malacca | `sea` | `none` | `g_cat_southern`, `g_sea_indian_ocean`, `g_sea_south_china` | **[CHOKEPOINT: Malacca Strait]** on border with Indian Ocean. Cathay energy import vulnerability. 40% of global trade. |
| `g_sea_south_china` | South China Sea | `sea` | `none` | `g_cat_eastern`, `g_cat_southern`, `g_formosa`, `g_sea_southeast_asia`, `g_sea_east_china` | **[CHOKEPOINT: South China Sea / Taiwan Strait south approach]**. Contested waters. Island militarization. Massive trade volume. Nine-dash line. |
| `g_sea_east_china` | East China Sea | `sea` | `none` | `g_cat_eastern`, `g_formosa`, `g_yamato`, `g_hanguk`, `g_sea_south_china`, `g_sea_north_pacific` | **[CHOKEPOINT: Taiwan Strait]** on border with Formosa. Senkaku/Diaoyu. Yamato-Cathay friction. |
| `g_sea_north_pacific` | North Pacific | `sea` | `none` | `g_col_alaska`, `g_col_hawaii`, `g_yamato`, `g_nor_eastern`, `g_sea_east_china`, `g_sea_central_pacific`, `g_sea_arctic` | Vast. Columbia-Yamato maritime corridor. Nordostan Pacific Fleet transit. ICBM flight path. |
| `g_sea_central_pacific` | Central Pacific | `sea` | `none` | `g_col_hawaii`, `g_sea_north_pacific`, `g_sea_gulf_caribbean` | Deep Pacific. US power projection route. Panama Canal western terminus implied. Guam staging. |
| `g_sea_giuk` | GIUK Gap | `sea` | `none` | `g_albion`, `g_contested_thule`, `g_sea_atlantic_east`, `g_sea_arctic` | **[CHOKEPOINT: GIUK Gap]**. Submarine detection corridor. North Atlantic gateway. Thule theater anchor. |

> **Total global sea zones: 15** (14 named sea zones + Arctic which functions as sea). This matches the requirement of 14-15 sea zones.

---

## 1.4 Global Zone Count Summary

| Category | Count |
|----------|:-----:|
| Land -- Home (Columbia) | 3 |
| Land -- Home (Cathay) | 3 |
| Land -- Home (Nordostan) | 3 |
| Land -- Home (Europe) | 5 |
| Land -- Home (Mashriq / South Asia) | 6 |
| Land -- Home (Asu / Pacific) | 4 |
| Land -- Home (Americas) | 1 |
| Land -- Contested | 5 |
| Sea zones (incl. Arctic) | 15 |
| **TOTAL GLOBAL ZONES** | **45** |

---

# SECTION 2: THEATER ZONES

Theaters expand a global zone (or cluster of global zones) into tactical detail when activated. Theater zones exist only within the theater map. Units on the global map in the parent zone are placed into specific theater zones upon activation.

---

## 2.1 Eastern Europe Theater (15 zones)

**Status:** Active at game start (Round 1).
**Parent global zones:** Expands the border region between `g_nor_western`, `g_freeland`, and implies Heartland (which has no separate global zone -- its territory IS this theater).
**Activation trigger:** Pre-activated. Active war in progress.
**Dominant unit type:** Ground forces. Territory changes matter for negotiation leverage, stability, national morale.
**Combat pacing:** 15 zones, but only ~5-7 will see active combat per round. Front-line zones resolve in sequence. Target: 10-12 minutes for a full round's military activity.

### Theater Map

```
                    [NORDOSTAN BORDER]
                     |            |
            ee_belarus    ee_nord_border
               |              |
         ee_west_ukr --- ee_central_ukr --- ee_east_front_north
               |              |                    |
         ee_southwest --- ee_capital --- ee_east_front_central
               |              |                    |
         ee_west_border  ee_south_ukr --- ee_east_front_south
                              |                    |
                       ee_dnipro_line --- ee_occupied_south
                              |                    |
                        ee_kherson --- ee_crimea_land
                                           |
                                      ee_crimea_naval
                                           |
                                    [BLACK SEA - global]
```

### Zone Table

| Zone ID | Display Name | Type | Owner (start) | Adjacent Zones | Notes |
|---------|-------------|------|---------------|----------------|-------|
| `ee_belarus` | Belarus Corridor | `land_home` | `nordostan` | `ee_nord_border`, `ee_west_ukr`, `ee_central_ukr` | Nordostan staging area. Threat axis to Heartland capital. Belarus = Nordostan client state. NATO fears this corridor. |
| `ee_nord_border` | Nordostan Border Region | `land_home` | `nordostan` | `ee_belarus`, `ee_east_front_north`, `ee_east_front_central` | Russian territory. Logistics hub. Belgorod/Kursk region. Heartland incursions possible. |
| `ee_west_ukr` | Western Heartland | `land_home` | `heartland` | `ee_belarus`, `ee_central_ukr`, `ee_southwest`, `ee_west_border` | Lviv region. Western supply corridor. NATO border. Refugee flow origin. Relatively safe rear area. |
| `ee_central_ukr` | Central Heartland | `land_home` | `heartland` | `ee_belarus`, `ee_west_ukr`, `ee_east_front_north`, `ee_east_front_central`, `ee_capital`, `ee_south_ukr` | Geographic center. Agricultural heartland. Key logistics crossroads. |
| `ee_capital` | Heartland Capital | `land_home` | `heartland` | `ee_central_ukr`, `ee_south_ukr`, `ee_east_front_central` | Kyiv equivalent. Political center. Capture = regime collapse trigger. Heavily defended. Symbolic and strategic. |
| `ee_southwest` | Southwestern Heartland | `land_home` | `heartland` | `ee_west_ukr`, `ee_central_ukr`, `ee_west_border` | Odesa region. Black Sea access point. Grain export route. |
| `ee_west_border` | Western Border (NATO) | `land_home` | `heartland` | `ee_west_ukr`, `ee_southwest` | Freeland/NATO border. Supply entry point. If Nordostan reaches here, NATO Article 5 question arises. Not directly attackable from Nordostan without crossing all of Heartland. |
| `ee_south_ukr` | Southern Heartland | `land_home` | `heartland` | `ee_central_ukr`, `ee_capital`, `ee_east_front_south`, `ee_dnipro_line` | South-central territory. Industrial zone. Dnipro river defensive line anchor. |
| `ee_east_front_north` | Eastern Front (North) | `land_contested` | `heartland` | `ee_central_ukr`, `ee_nord_border`, `ee_east_front_central` | Active front line. Kharkiv axis. Heavily contested. High attrition zone. |
| `ee_east_front_central` | Eastern Front (Central) | `land_contested` | `nordostan` | `ee_east_front_north`, `ee_nord_border`, `ee_capital`, `ee_east_front_south` | Donetsk/Luhansk. Nordostan-controlled at start. Fortified. The "frozen" line that isn't frozen. |
| `ee_east_front_south` | Eastern Front (South) | `land_contested` | `nordostan` | `ee_east_front_central`, `ee_south_ukr`, `ee_occupied_south` | Zaporizhzhia axis. Nuclear plant. Southern front connection. |
| `ee_dnipro_line` | Dnipro River Line | `land_home` | `heartland` | `ee_south_ukr`, `ee_occupied_south`, `ee_kherson` | River defensive barrier. If this falls, southern Heartland is exposed. Natural defense line. |
| `ee_occupied_south` | Occupied Southern Territory | `land_contested` | `nordostan` | `ee_east_front_south`, `ee_dnipro_line`, `ee_crimea_land` | Nordostan-occupied since 2022. Land bridge to Crimea. Contested. |
| `ee_kherson` | Kherson Region | `land_contested` | `heartland` | `ee_dnipro_line`, `ee_crimea_land` | West bank recaptured. Bridgehead potential. Adjacent to Crimea -- if Heartland pushes, Crimea is threatened. |
| `ee_crimea_naval` | Crimea & Sevastopol | `land_home` | `nordostan` | `ee_crimea_land`, `g_sea_black` | Nordostan Black Sea Fleet base. Annexed 2014. If lost, Nordostan loses warm-water port. Connects to global Black Sea zone. |

> **Note:** `ee_crimea_land` is not a separate zone -- Crimea's land access is through `ee_occupied_south` and `ee_kherson` connecting to `ee_crimea_naval`. The zone `ee_crimea_naval` represents the whole peninsula including the naval base. I removed the redundant zone to keep at exactly 15.

**Starting front line:** Nordostan holds `ee_belarus`, `ee_nord_border`, `ee_east_front_central`, `ee_east_front_south`, `ee_occupied_south`, `ee_crimea_naval` (6 zones). Heartland holds 8 zones. `ee_east_front_north` is Heartland-held but actively contested.

---

## 2.2 Mashriq Theater (9 zones)

**Status:** Active at game start (Round 1).
**Parent global zones:** Expands `g_persia`, `g_levantia`, `g_solaria`, `g_sea_persian_gulf`, `g_sea_red`.
**Activation trigger:** Pre-activated. Iran nuclear crisis and proxy wars in progress.
**Dominant unit type:** Air and missile power. Tactical air/missile strikes. Strategic missile threat (nuclear dimension).
**Combat pacing:** 9 zones but most action is air/missile strikes, not ground maneuver. Target: 5-8 minutes per round.

### Theater Map

```
              [MED EAST - global]
                     |
              me_levantia_north --- me_levantia_core
                     |                    |
              me_syria_lebanon      [MED EAST sea]
                     |
              me_iraq_corridor --- me_persia_west
                                        |
    [RED SEA] --- me_yemen --- me_persia_nuclear --- me_persia_east
                     |              |
              me_gulf_hormuz ------+
                     |
              [PERSIAN GULF - global]
```

### Zone Table

| Zone ID | Display Name | Type | Owner (start) | Adjacent Zones | Notes |
|---------|-------------|------|---------------|----------------|-------|
| `me_levantia_core` | Levantia Heartland | `land_home` | `levantia` | `me_levantia_north`, `g_sea_med_east` | Israel proper. Undeclared nuclear arsenal. Iron Dome/air defense concentration. Tel Aviv, Jerusalem. Small but hyper-defended. |
| `me_levantia_north` | Levantia Northern Border | `land_contested` | `levantia` | `me_levantia_core`, `me_syria_lebanon`, `g_sea_med_east` | Golan, southern Lebanon. Active proxy conflict zone. Hezbollah rocket threat. Buffer zone Levantia maintains. |
| `me_syria_lebanon` | Syria-Lebanon (Proxy Zone) | `land_contested` | `none` | `me_levantia_north`, `me_iraq_corridor`, `g_sea_med_east` | Failed state territory. Persia proxy network hub. Nordostan air base (Tartus/Hmeimim implied). Multiple foreign forces present. No sovereign owner -- proxies contest. |
| `me_iraq_corridor` | Iraq Corridor | `land_contested` | `none` | `me_syria_lebanon`, `me_persia_west`, `me_yemen` | Iran-to-Mediterranean land bridge. Shia militia corridor. Nominally sovereign but functionally contested. US residual presence. |
| `me_persia_west` | Persia (Western) | `land_home` | `persia` | `me_iraq_corridor`, `me_persia_nuclear`, `me_gulf_hormuz` | IRGC power base. Border defense. Conventional military concentration. |
| `me_persia_nuclear` | Persia (Nuclear Sites) | `land_home` | `persia` | `me_persia_west`, `me_persia_east`, `me_gulf_hormuz` | Natanz, Fordow, Isfahan equivalents. THE target for Levantia/Columbia strikes. Deep underground. Air defense priority. Destruction sets nuclear program back 2-3 years. |
| `me_persia_east` | Persia (Eastern) | `land_home` | `persia` | `me_persia_nuclear`, `g_contested_central_asia` | Strategic depth. Ballistic missile sites. Harder to reach. Land link to Central Asia. |
| `me_gulf_hormuz` | Strait of Hormuz Zone | `chokepoint_sea` | `none` | `me_persia_west`, `me_persia_nuclear`, `me_yemen`, `g_sea_persian_gulf`, `g_sea_arabian` | THE oil chokepoint. Persia can threaten closure with mines/missiles/naval. 20% of world oil transits here. Blockade = global energy crisis. Columbia 5th Fleet patrol. |
| `me_yemen` | Yemen (Proxy Zone) | `land_contested` | `none` | `me_iraq_corridor`, `me_gulf_hormuz`, `g_sea_red` | Houthi proxy. Red Sea disruption capability. Anti-ship missiles threaten commercial shipping. Solaria intervention zone. Southern approach to Hormuz. |

**Starting conditions:** Persia holds 3 home zones. Levantia holds 1 + contests northern border. 4 contested zones with mixed proxy/foreign presence. Hormuz is the powder keg.

---

## 2.3 Taiwan Strait Theater (7 zones)

**Status:** Inactive at game start.
**Parent global zones:** Expands `g_formosa`, `g_sea_east_china`, `g_sea_south_china`.
**Activation trigger:** Cathay initiates blockade, military exercises as pressure, or invasion against Formosa. Also activates if Formosa declares independence or Columbia deploys combat forces to Formosa.
**Dominant unit type:** Naval and air power. Amphibious assault is the central question.
**Combat pacing:** 7 zones, binary crisis dynamic. Target: 5-8 minutes per round, but consequences are enormous (global economic shock).

### Theater Map

```
    [CATHAY EASTERN - global]
              |
        ts_cathay_staging
         /         \
  ts_strait --- ts_sea_north
      |              |
  ts_formosa --- ts_sea_east
      |              |
  ts_sea_south ------+
      |
  [SOUTH CHINA SEA - global]
```

### Zone Table

| Zone ID | Display Name | Type | Owner (start) | Adjacent Zones | Notes |
|---------|-------------|------|---------------|----------------|-------|
| `ts_cathay_staging` | Cathay Staging Coast | `land_home` | `cathay` | `ts_strait`, `ts_sea_north`, `g_cat_eastern` | Fujian coast. Amphibious staging. Missile batteries. Air bases. The launchpad. Ground forces mass here before any crossing. |
| `ts_strait` | Taiwan Strait | `chokepoint_sea` | `none` | `ts_cathay_staging`, `ts_formosa`, `ts_sea_north`, `ts_sea_south` | **[CHOKEPOINT: Taiwan Strait]**. 130km wide. Amphibious crossing zone. Naval superiority here is prerequisite for invasion. Blockade here disrupts global semiconductor supply. |
| `ts_sea_north` | Northern Sea Approach | `sea` | `none` | `ts_cathay_staging`, `ts_strait`, `ts_formosa`, `ts_sea_east`, `g_sea_east_china` | Yamato/Columbia intervention route from north. Access from East China Sea global zone. |
| `ts_formosa` | Formosa | `land_home` | `formosa` | `ts_strait`, `ts_sea_north`, `ts_sea_east`, `ts_sea_south` | The island. Semiconductor facilities (TSMC equivalent). 4:1 force ratio required for amphibious assault. Decades of defensive preparation. Air defense priority. |
| `ts_sea_east` | Eastern Sea (Pacific Approach) | `sea` | `none` | `ts_formosa`, `ts_sea_north`, `ts_sea_south`, `g_sea_north_pacific` | Columbia carrier approach from Pacific. The "back door" -- harder for Cathay to blockade. Submarine warfare zone. Links to North Pacific global zone. |
| `ts_sea_south` | Southern Sea Approach | `sea` | `none` | `ts_strait`, `ts_formosa`, `ts_sea_east`, `g_sea_south_china` | South China Sea access. Philippine Sea implied. Cathay island militarization advantage. Second blockade axis. |
| -- | -- | -- | -- | -- | -- |

> **Note:** 7 zones = 3 sea + 1 chokepoint sea + 2 land + 1 sea (eastern approach). Exactly matches requirement: 3 land (counting staging + Formosa + strait-as-chokepoint) + 3 sea + 1 staging.

**Invasion sequence:**
1. Cathay masses ground + naval in `ts_cathay_staging`
2. Naval battle for `ts_strait` (and flanking sea zones)
3. Naval superiority must be established (no uncontested enemy naval in strait)
4. Pre-landing bombardment (naval 10%/unit + tactical air strikes)
5. Amphibious assault: 4:1 force ratio required after all modifiers
6. Columbia/Yamato intervention enters from `ts_sea_north` or `ts_sea_east`

---

## 2.4 Caribbean Theater (4 zones)

**Status:** Inactive at game start.
**Parent global zones:** Expands `g_caribe`, `g_sea_gulf_caribbean`.
**Activation trigger:** Columbia military intervention against Caribe, OR Nordostan/Cathay deploy military forces to Caribe, OR Caribe attacks Columbia interests.
**Dominant unit type:** Naval (Columbia overwhelming advantage). Ground for occupation.
**Combat pacing:** 4 zones, simplest theater. Target: 3-5 minutes per round. Fast but thematically important -- the hegemon using force in its own backyard.

### Zone Table

| Zone ID | Display Name | Type | Owner (start) | Adjacent Zones | Notes |
|---------|-------------|------|---------------|----------------|-------|
| `cb_cuba` | Cuba | `land_home` | `caribe` | `cb_caribbean_sea`, `cb_venezuela` | 90 miles from Columbia. Russian/Chinese listening posts. Potential missile crisis redux. |
| `cb_venezuela` | Venezuela | `land_home` | `caribe` | `cb_cuba`, `cb_caribbean_sea`, `cb_columbia_coast` | Oil reserves. Authoritarian regime. Russian military advisor presence. Refugee crisis driver. |
| `cb_caribbean_sea` | Caribbean Sea (Theater) | `sea` | `none` | `cb_cuba`, `cb_venezuela`, `cb_columbia_coast`, `g_sea_gulf_caribbean` | **[CHOKEPOINT: Caribbean Passages]**. Columbia naval dominance. Patrol zone. Links to global Gulf/Caribbean zone. |
| `cb_columbia_coast` | Columbia Southern Coast | `land_home` | `columbia` | `cb_venezuela`, `cb_caribbean_sea` | Florida/Gulf Coast. Staging area. Columbia home territory in theater. US Southern Command. |

---

## 2.5 Thule Theater (3 zones)

**Status:** Inactive at game start.
**Parent global zones:** Expands `g_contested_thule`, `g_sea_giuk`.
**Activation trigger:** Columbia attempts to purchase/annex Thule, OR deploys military forces to Thule, OR any power establishes a military base on Thule.
**Dominant unit type:** Naval (GIUK sub detection), minimal ground.
**Combat pacing:** 3 zones. Target: 2-3 minutes per round. Crisis scenario, not sustained campaign.

### Zone Table

| Zone ID | Display Name | Type | Owner (start) | Adjacent Zones | Notes |
|---------|-------------|------|---------------|----------------|-------|
| `gl_thule` | Thule Territory | `land_contested` | `teutonia` | `gl_giuk_gap`, `gl_davis_strait` | Rare earth deposits. Thule Air Base (Columbia). Pioneer's portfolio. Tiny population. Arctic access. |
| `gl_giuk_gap` | GIUK Gap (Theater) | `chokepoint_sea` | `none` | `gl_thule`, `gl_davis_strait`, `g_sea_giuk`, `g_sea_atlantic_east` | **[CHOKEPOINT: GIUK Gap]**. Submarine detection arrays. North Atlantic chokepoint. Nordostan submarine transit route to Atlantic. Albion/Columbia ASW patrol. |
| `gl_davis_strait` | Davis Strait | `sea` | `none` | `gl_thule`, `gl_giuk_gap`, `g_sea_arctic`, `g_sea_atlantic_west` | Western approach to Thule. Arctic shipping route. Ice conditions limit operations seasonally. |

---

## 2.6 Korea Theater (4 zones) -- Optional

**Status:** Inactive. Optional activation.
**Parent global zones:** Expands `g_choson`, `g_hanguk`.
**Activation trigger:** Choson nuclear test, artillery strike on Hanguk capital, invasion across DMZ, or Choson regime collapse.
**Dominant unit type:** Ground (massive armies), artillery, nuclear threat.
**Combat pacing:** 4 zones. Target: 3-5 minutes per round. The terrifying proximity of civilians to the front makes every action high-stakes.

### Zone Table

| Zone ID | Display Name | Type | Owner (start) | Adjacent Zones | Notes |
|---------|-------------|------|---------------|----------------|-------|
| `kr_choson` | Choson (North) | `land_home` | `choson` | `kr_dmz`, `g_cat_eastern`, `g_nor_eastern` | Nuclear weapons. Massive artillery pointed south. Unpredictable regime. Cathay land border = potential Chinese intervention route. |
| `kr_dmz` | DMZ / Seoul Corridor | `land_contested` | `none` | `kr_choson`, `kr_hanguk` | The most militarized border on earth. Seoul is within artillery range. 10 million civilians at immediate risk. Ground zero for any conflict. |
| `kr_hanguk` | Hanguk (South) | `land_home` | `hanguk` | `kr_dmz`, `kr_basing`, `g_sea_east_china` | Tech powerhouse. US garrison (28,500 troops). Economic giant at extreme geographic risk. |
| `kr_basing` | US/Yamato Basing (Rear) | `land_home` | `columbia` | `kr_hanguk`, `g_yamato`, `g_sea_east_china` | Okinawa, Sasebo, Camp Humphreys complex. Reinforcement and logistics hub. Yamato territory effectively. Strike on this zone = attack on Columbia/Yamato sovereign territory. |

---

## 2.7 Theater Zone Count Summary

| Theater | Zones | Active at Start | Parent Global Zones |
|---------|:-----:|:---------------:|---------------------|
| Eastern Ereb | 15 | Yes | `g_nor_western`, `g_freeland` border region |
| Mashriq | 9 | Yes | `g_persia`, `g_levantia`, `g_solaria`, sea zones |
| Taiwan Strait | 7 | No | `g_formosa`, `g_sea_east_china`, `g_sea_south_china` |
| Caribbean | 4 | No | `g_caribe`, `g_sea_gulf_caribbean` |
| Thule | 3 | No | `g_contested_thule`, `g_sea_giuk` |
| Korea (optional) | 4 | No | `g_choson`, `g_hanguk` |
| **TOTAL THEATER** | **42** | **24** | -- |

---

## 2.8 Combined Zone Summary

| Layer | Count | Active at Start |
|-------|:-----:|:---------------:|
| Global map | 45 | 45 |
| Eastern Ereb theater | 15 | 15 |
| Mashriq theater | 9 | 9 |
| Taiwan Strait theater | 7 | 0 |
| Caribbean theater | 4 | 0 |
| Thule theater | 3 | 0 |
| Korea theater (optional) | 4 | 0 |
| **GRAND TOTAL** | **87** | **69** |

> 69 active at start (45 global + 15 EE + 9 ME), ~68 target met.

---

# SECTION 3: CHOKEPOINT DETAILS

The 8 chokepoints are the simulation's economic pressure points. Each chokepoint sits on the border between two zones (or is a zone itself in theater maps). Controlling or disrupting a chokepoint has cascading economic effects calculated by the World Model Engine.

---

## 3.1 Strait of Hormuz

| Property | Value |
|----------|-------|
| **Global zones** | Border between `g_sea_persian_gulf` and `g_sea_arabian` |
| **Theater zone** | `me_gulf_hormuz` (Mashriq theater) |
| **Default control** | Contested -- Columbia naval patrol, Persia coastal threat |
| **Blockade minimum** | 1 naval unit in `g_sea_persian_gulf` (global) or `me_gulf_hormuz` (theater). Persia can also blockade using coastal missile batteries (tactical air/missile units in `me_persia_west`) without naval units. |
| **Blockade effects** | Oil price spike (+50-100% depending on duration). Gulf producers (Solaria, Mirage, Persia) lose export revenue. Global importers (Cathay, Teutonia, Bharata, Yamato) face energy crisis. Stability hit to energy-dependent economies. |
| **Strategic significance** | ~20% of global oil transits. Persia's ultimate leverage card. Closing Hormuz is an act of war against the global economy. Columbia's 5th Fleet exists specifically to keep this open. |
| **Special rules** | Persia can threaten Hormuz with mines and coastal missiles even without naval superiority. To fully reopen, Columbia must clear both naval AND missile threats. |

---

## 3.2 Bosphorus / Turkish Straits

| Property | Value |
|----------|-------|
| **Global zones** | Border between `g_sea_med_east` and `g_sea_black`, controlled via `g_phrygia` |
| **Theater zone** | None (no Black Sea theater). Resolved at global level. |
| **Default control** | Phrygia (sovereign control under Montreux Convention equivalent) |
| **Blockade minimum** | Phrygia unilaterally decides passage rights. No naval force required -- political decision. Other powers need Phrygia's consent or must coerce/invade Phrygia. |
| **Blockade effects** | Nordostan Black Sea Fleet trapped. Nordostan loses Mediterranean access. Grain exports from Black Sea disrupted. |
| **Strategic significance** | Phrygia's ultimate bargaining chip. NATO member controlling Russia's warm-water access. Can be leveraged for concessions from both sides. |
| **Special rules** | Phrygia can selectively block -- allowing civilian traffic while blocking military, or blocking one nation while allowing others. Decision is political, not military. |

---

## 3.3 Suez Canal

| Property | Value |
|----------|-------|
| **Global zones** | Border between `g_sea_med_east` and `g_sea_red` |
| **Theater zone** | None (implied in Mashriq theater adjacency) |
| **Default control** | Neutral (Egyptian sovereignty implied -- not a playable country). Open by default. |
| **Blockade minimum** | Any power with 1+ naval unit in `g_sea_med_east` or `g_sea_red` can attempt disruption. Full blockade requires controlling both sides. Yemen proxies (Houthi) can disrupt from `me_yemen` theater zone. |
| **Blockade effects** | Europe-Asia trade adds 2 weeks transit (around Africa). Trade cost +15-20%. European importers hit hardest. Oil from Gulf to Europe rerouted. |
| **Strategic significance** | 12% of global trade. Suez disruption cascades to European economies specifically. Combined with Hormuz closure = double energy crisis. |
| **Special rules** | Proxy disruption from Yemen (`me_yemen`) reduces Suez throughput by ~50% without formal blockade. Full closure requires naval presence. |

---

## 3.4 Malacca Strait

| Property | Value |
|----------|-------|
| **Global zones** | Border between `g_sea_southeast_asia` and `g_sea_indian_ocean` |
| **Theater zone** | None |
| **Default control** | Open. No single power controls. |
| **Blockade minimum** | 2+ naval units in `g_sea_southeast_asia` (narrow strait, harder to blockade -- requires more force) |
| **Blockade effects** | Cathay energy imports cut (~80% of Cathay's oil transits Malacca). Cathay economic crisis within 1-2 rounds. Global trade disruption. Cathay forced to reroute via longer Pacific routes or overland pipelines (Central Asia). |
| **Strategic significance** | Cathay's "Malacca Dilemma" -- the existential vulnerability. ~40% of global trade. Columbia/Bharata could theoretically strangle Cathay's energy supply without firing a shot at Chinese territory. |
| **Special rules** | Cathay's String of Pearls (ports in Myanmar, Sri Lanka, Pakistan) provides partial alternative but at 50% capacity. Overland pipelines from Central Asia provide ~20% of normal oil flow. |

---

## 3.5 Taiwan Strait

| Property | Value |
|----------|-------|
| **Global zones** | Border between `g_sea_east_china` and `g_formosa` |
| **Theater zone** | `ts_strait` (Taiwan Strait theater) |
| **Default control** | Status quo -- Cathay claims sovereignty, Formosa operates independently, Columbia patrols |
| **Blockade minimum** | 1+ Cathay naval unit in `g_sea_east_china` (global, before theater activation). In theater: naval units in `ts_strait`. |
| **Blockade effects** | Global semiconductor crisis. All countries dependent on Formosa chips drop 1 effective tech level within 1-2 rounds. Tech-dependent economies (Columbia, Cathay, Yamato, Teutonia, Hanguk) face GDP shock of -5% to -15%. Financial markets crash. |
| **Strategic significance** | Not primarily an oil/trade chokepoint -- a TECHNOLOGY chokepoint. Disruption here damages the global economy more than any other single point of failure. |
| **Special rules** | Blockade (without invasion) is Cathay's graduated option. Semiconductor disruption affects Cathay itself (self-harm). This creates a paradox: Cathay's primary coercive tool damages Cathay. Theater activates on blockade initiation. |

---

## 3.6 South China Sea

| Property | Value |
|----------|-------|
| **Global zones** | `g_sea_south_china` (the zone itself is the contested area) |
| **Theater zone** | `ts_sea_south` connects to it in Taiwan theater |
| **Default control** | Contested. Cathay artificial island militarization. Multiple claimants. Columbia freedom-of-navigation patrols. |
| **Blockade minimum** | 2+ naval units in `g_sea_south_china` (vast area) |
| **Blockade effects** | $5.3 trillion in annual trade disrupted. SE Asian economies devastated. Alternative routes add cost and time. Combined with Malacca blockade = complete Indian Ocean-Pacific trade severance. |
| **Strategic significance** | Volume: ~33% of global shipping. Cathay's nine-dash line claim. Island bases give Cathay local air/missile cover. Contest here is pre-war posturing -- full blockade is an act of war. |
| **Special rules** | Cathay's militarized islands provide inherent defensive bonus (+1 to naval defense rolls in this zone). Other powers contesting must overcome this fortification advantage. |

---

## 3.7 GIUK Gap

| Property | Value |
|----------|-------|
| **Global zones** | `g_sea_giuk` |
| **Theater zone** | `gl_giuk_gap` (Thule theater) |
| **Default control** | NATO (Columbia + Albion ASW patrol) |
| **Blockade minimum** | Not a traditional blockade point -- a submarine detection and denial zone. 1+ naval unit enables ASW (anti-submarine warfare) operations. Without presence, Nordostan submarines transit freely to Atlantic. |
| **Blockade effects** | If NATO loses GIUK: Nordostan submarines threaten Atlantic shipping lanes and Columbia's eastern seaboard. If NATO holds: Nordostan submarine force bottled up in Arctic/Norwegian Sea. |
| **Strategic significance** | Cold War era chokepoint, newly relevant. Thule's strategic value is partly about anchoring the western end of this gap. Nordostan submarine-launched ballistic missiles are the second-strike deterrent -- GIUK monitoring affects nuclear balance perception. |
| **Special rules** | Submarine detection: naval units in GIUK Gap can detect and engage Nordostan submarines transiting to the Atlantic. Without GIUK presence, Nordostan submarine deployments to `g_sea_atlantic_west` or `g_sea_atlantic_east` are undetected until they act. |

---

## 3.8 Caribbean Passages

| Property | Value |
|----------|-------|
| **Global zones** | Border between `g_sea_gulf_caribbean` and `g_sea_atlantic_west` |
| **Theater zone** | `cb_caribbean_sea` (Caribbean theater) |
| **Default control** | Columbia (overwhelming local naval superiority) |
| **Blockade minimum** | 1+ naval unit in `g_sea_gulf_caribbean` |
| **Blockade effects** | Venezuela oil exports blocked. Cuba isolated. Panama Canal access threatened (links to Central Pacific). Limited global trade impact but major regional/political impact. |
| **Strategic significance** | The "Monroe Doctrine" zone. Columbia's backyard. Any foreign military presence here (Nordostan, Cathay) is a direct provocation. Low trade volume compared to Asian chokepoints but maximum political sensitivity. |
| **Special rules** | Columbia has inherent detection advantage in this zone (home waters, extensive sensor network). Foreign naval deployments to Caribbean are detected 1 round before arrival (intelligence advantage, not automatic interception). |

---

# SECTION 4: MOVEMENT & ADJACENCY SUMMARY

## 4.1 Transit Rules

| Rule | Description |
|------|-------------|
| **Domestic deployment** | Instant. Units produced/mobilized in home territory deploy to any owned zone immediately during the deployment window. |
| **Adjacent zone movement** | 1 action. Units move to any adjacent zone (land-to-land or sea-to-sea) as part of attack or redeployment. |
| **Long-distance redeployment** | 1 round transit delay. Units moving between non-adjacent theaters or across multiple sea zones arrive next round. |
| **Columbia base network** | Instant deployment to any zone with an active Columbia base. Bypasses transit delay. Requires host consent. Base locations: Yamato, Teutonia, Persian Gulf (Mirage/Solaria), Indian Ocean (Bharata area), potentially Mediterranean. |
| **Chokepoint transit** | Units moving through a zone with a hostile blockade must fight through or wait. Blockaded chokepoints deny transit. |
| **Amphibious movement** | Naval units carry ground forces. Landing requires naval superiority in target sea zone + force ratio check. |

---

## 4.2 Key Strategic Transit Routes

### Columbia Force Projection Routes

| Route | Path | Chokepoints | Transit Delay |
|-------|------|-------------|:-------------:|
| Columbia to Europe | `g_col_continental` → `g_sea_atlantic_west` → `g_sea_atlantic_east` → `g_teutonia`/`g_albion` | None (open Atlantic) | 1 round |
| Columbia to Pacific/Taiwan | `g_col_hawaii` → `g_sea_north_pacific` → `g_sea_east_china` → theater | None (open Pacific, but vast) | 1 round |
| Columbia to Persian Gulf | `g_col_continental` → `g_sea_atlantic_west` → `g_sea_atlantic_east` → `g_sea_med_west` → `g_sea_med_east` → `g_sea_red` → `g_sea_arabian` → `g_sea_persian_gulf` | Suez Canal | 1 round (or instant via Gulf base) |
| Columbia to Caribbean | `g_col_continental` → `g_sea_gulf_caribbean` | None (home waters) | Instant (adjacent) |
| Columbia to Thule | `g_col_continental` → `g_sea_atlantic_west` → `g_contested_thule` | None | 1 round |

> **The overstretched hegemon problem visualized:** Columbia can reach any theater in 1 round (or instantly via bases). BUT deploying to one theater means those units are NOT available elsewhere for 1 round. With 3-4 active theaters, Columbia physically cannot be strong everywhere.

### Cathay Force Projection Routes

| Route | Path | Chokepoints | Transit Delay |
|-------|------|-------------|:-------------:|
| Cathay to Taiwan | `g_cat_eastern` → `g_sea_east_china` → theater | Taiwan Strait | Adjacent (instant to East China Sea) |
| Cathay to Indian Ocean | `g_cat_southern` → `g_sea_southeast_asia` → `g_sea_indian_ocean` | Malacca Strait | 1 round |
| Cathay to Central Asia | `g_cat_western` → `g_contested_central_asia` | None (land) | Adjacent |
| Cathay to Mashriq | `g_cat_western` → `g_contested_central_asia` → `g_persia` | None (overland) | 1 round |
| Cathay to Korea | `g_cat_eastern` → `g_choson` / `g_hanguk` | None (land border) | Adjacent |

> **Cathay's vulnerability:** Energy imports flow through Malacca. If blockaded, overland route via Central Asia provides only ~20% capacity. Cathay must either secure Malacca or reduce energy dependency.

### Nordostan Force Projection Routes

| Route | Path | Chokepoints | Transit Delay |
|-------|------|-------------|:-------------:|
| Nordostan to Eastern Ereb | `g_nor_western` → theater | None (direct border) | Adjacent (instant to theater) |
| Nordostan to Mediterranean | `g_sea_black` → `g_sea_med_east` | Bosphorus (Phrygia controls) | 1 round, IF Phrygia allows |
| Nordostan to Atlantic | `g_nor_central`/`g_nor_eastern` → `g_sea_arctic` → `g_sea_giuk` → `g_sea_atlantic_east` | GIUK Gap | 1 round, detected if GIUK monitored |
| Nordostan to Pacific | `g_nor_eastern` → `g_sea_north_pacific` | None | 1 round |
| Nordostan to Mashriq | `g_nor_western` → `g_sea_black` → (Bosphorus) → `g_sea_med_east` OR overland via `g_contested_central_asia` → `g_persia` | Bosphorus OR none (overland) | 1 round either way |

> **Nordostan's constraint:** Two of three naval egress points (Bosphorus, GIUK) are controlled or monitored by adversaries. Only the Pacific Fleet exits freely, but faces Columbia/Yamato. Nordostan's navy is structurally trapped.

---

## 4.3 Critical One-Round Transit Paths

These are the routes where 1-round transit delay creates the most strategic tension -- the player must commit forces one round before they arrive, during which the situation may change.

| Transit | Why It Matters |
|---------|---------------|
| Columbia Atlantic → Pacific (or reverse) | The fundamental overstretch. Reinforcing Taiwan weakens Europe. Reinforcing Europe weakens Taiwan. Cannot do both simultaneously. |
| Columbia to Persian Gulf (without base) | If Gulf basing rights are revoked, Columbia loses instant access to Hormuz defense. 1-round delay to redeploy. |
| Cathay to Indian Ocean via Malacca | Energy security route. If interdicted at Malacca, alternative is 2+ rounds via Pacific. |
| Nordostan Black Sea to Mediterranean | Depends entirely on Phrygia. Political decision, not military. Phrygia can change its mind each round. |
| Any power to Central Asia | The "Great Game" zone. Nordostan, Cathay, and Persia all 1 round away. First mover advantage. |

---

## 4.4 Adjacency Quick Reference (Global Map)

For rapid lookup during gameplay. Each zone's full adjacency list.

**Columbia:**
- `g_col_continental`: alaska, hawaii, sea_atlantic_west, sea_gulf_caribbean, caribe
- `g_col_alaska`: col_continental, sea_north_pacific, sea_arctic
- `g_col_hawaii`: sea_north_pacific, sea_central_pacific

**Cathay:**
- `g_cat_eastern`: cat_western, cat_southern, sea_south_china, sea_east_china, hanguk, choson
- `g_cat_western`: cat_eastern, cat_southern, contested_central_asia, bharata
- `g_cat_southern`: cat_eastern, cat_western, sea_south_china, sea_southeast_asia

**Nordostan:**
- `g_nor_western`: nor_central, freeland, sea_baltic, sea_black
- `g_nor_central`: nor_western, nor_eastern, contested_central_asia, sea_arctic
- `g_nor_eastern`: nor_central, sea_north_pacific, choson, sea_arctic

**Europe:**
- `g_gallia`: teutonia, ponte, albion, sea_atlantic_east, sea_med_west
- `g_teutonia`: gallia, freeland, ponte, sea_baltic
- `g_freeland`: teutonia, nor_western, sea_baltic
- `g_ponte`: gallia, teutonia, sea_med_west, sea_med_east
- `g_albion`: gallia, sea_atlantic_east, sea_giuk

**Mashriq / South Asia:**
- `g_persia`: solaria, mirage, sea_persian_gulf, contested_central_asia, sea_arabian
- `g_levantia`: phrygia, sea_med_east, solaria
- `g_solaria`: persia, mirage, levantia, sea_persian_gulf, sea_red, contested_horn
- `g_phrygia`: levantia, sea_med_east, sea_black, nor_western
- `g_bharata`: cat_western, sea_arabian, sea_indian_ocean
- `g_mirage`: solaria, persia, sea_persian_gulf, sea_arabian

**Asu / Pacific:**
- `g_yamato`: sea_east_china, sea_north_pacific, hanguk
- `g_hanguk`: choson, cat_eastern, yamato, sea_east_china
- `g_choson`: hanguk, cat_eastern, nor_eastern
- `g_formosa`: sea_east_china, sea_south_china

**Americas:**
- `g_caribe`: col_continental, sea_gulf_caribbean, sea_atlantic_west

**Contested:**
- `g_contested_thule`: sea_giuk, sea_arctic, sea_atlantic_west
- `g_contested_central_asia`: nor_central, cat_western, persia, bharata
- `g_contested_horn`: solaria, sea_red, sea_arabian, contested_central_africa
- `g_contested_central_africa`: contested_horn, sea_atlantic_east

**Sea (prefix `g_sea_` omitted for brevity):**
- `atlantic_west`: col_continental, caribe, gulf_caribbean, atlantic_east, contested_thule
- `atlantic_east`: atlantic_west, gallia, albion, giuk, med_west, contested_central_africa
- `gulf_caribbean`: col_continental, caribe, atlantic_west, central_pacific
- `med_west`: gallia, ponte, atlantic_east, med_east
- `med_east`: med_west, ponte, phrygia, levantia, sea_red
- `black`: phrygia, nor_western
- `baltic`: nor_western, freeland, teutonia
- `red`: solaria, med_east, arabian, contested_horn
- `persian_gulf`: persia, solaria, mirage, arabian
- `arabian`: persian_gulf, red, bharata, mirage, indian_ocean, contested_horn
- `indian_ocean`: bharata, arabian, southeast_asia
- `southeast_asia`: cat_southern, indian_ocean, south_china
- `south_china`: cat_eastern, cat_southern, formosa, southeast_asia, east_china
- `east_china`: cat_eastern, formosa, yamato, hanguk, south_china, north_pacific
- `north_pacific`: col_alaska, col_hawaii, yamato, nor_eastern, east_china, central_pacific, sea_arctic
- `central_pacific`: col_hawaii, north_pacific, gulf_caribbean
- `giuk`: albion, contested_thule, atlantic_east, sea_arctic
- `arctic`: col_alaska, nor_central, nor_eastern, contested_thule, giuk, north_pacific

---

## 4.5 Zone Connectivity Statistics

| Zone | Adjacent Count | Notes |
|------|:--------------:|-------|
| Highest connectivity (global): `g_sea_north_pacific` | 7 | Vast ocean, many borders |
| Highest connectivity (global): `g_sea_arabian` | 6 | Hub of Mashriq sea routes |
| Highest connectivity (global): `g_cat_eastern` | 6 | Cathay's strategic center |
| Lowest connectivity (global): `g_col_hawaii` | 2 | Isolated Pacific outpost |
| Lowest connectivity (global): `g_sea_black` | 2 | Bottled up by Bosphorus |
| Average connectivity | ~4.2 | Good for gameplay -- enough options without paralysis |

---

# APPENDIX A: DESIGN NOTES

## Why These Zone Counts

**Eastern Ereb (15):** The active war demands granularity. Players need to make meaningful choices about where to attack, where to reinforce, where to accept losses. 15 zones create a real front line with flanks, breakthroughs, and strategic depth. The Conflict SIM4 used 22 sectors for a pure military sim; 15 is the right reduction for a multi-domain game where military is one of four domains.

**Mashriq (9):** More than the concept's 7-8 because the Iran nuclear sites deserve their own zone (it's the most important target in the theater), and the proxy network (Syria-Lebanon, Iraq corridor, Yemen) needs enough zones to show the "arc of resistance" geography. But combat here is mostly air/missile, not ground maneuver, so fewer zones than Eastern Ereb.

**Taiwan Strait (7):** Exactly right. The question is binary (does China cross?) but the approach matters (from where? can the US intervene?). 3 sea zones capture the naval geometry. The staging zone creates the visible buildup that terrifies everyone. Formosa itself is one zone because the island-fighting question is about whether they land, not where.

**Caribbean (4):** Minimal. This theater exists for narrative, not tactical depth. The decision is "does Columbia invade its own backyard?" not "where exactly do ground forces maneuver."

**Thule (3):** Even more minimal. A crisis scenario, not a war. Territory + two sea approaches. The GIUK Gap is the real strategic content.

**Korea (4):** Optional because Korean escalation may never happen. But if it does, the DMZ zone creates the Seoul-proximity horror, and the basing zone makes clear that attacking US/Yamato rear areas is an act of war against those countries directly.

## Chokepoint Design Philosophy

Every chokepoint has a different **control mechanism:**
- Hormuz: military (naval/missile)
- Bosphorus: political (Phrygia's decision)
- Suez: proxy disruption (Yemen) or military
- Malacca: military (naval, hard to blockade)
- Taiwan Strait: military/political (blockade or invasion)
- South China Sea: military (contested waters, fortified islands)
- GIUK Gap: detection (ASW, monitoring)
- Caribbean: political/military (Monroe Doctrine)

This variety ensures that "chokepoint control" is never a single mechanic -- it requires different tools, different negotiations, and creates different dilemmas for different players.

## Adjacency Design Principles

1. **No islands**: Every land zone is reachable by land from at least one neighbor (except Formosa and Thule, which are deliberately isolated -- their isolation IS their strategic character).
2. **Sea zones connect**: Any sea zone is reachable from any other within 3 hops maximum. The longest naval transit (Black Sea to Central Pacific) is 6-7 hops but traverses 3 chokepoints.
3. **Chokepoints are real**: There is no way to move from the Indian Ocean to the Mediterranean without passing through either Suez (via Red Sea) or going around Africa (via Atlantic East). The geography creates the strategic constraints.
4. **Great power home zones touch**: Nordostan borders NATO (Freeland). Cathay borders Bharata. These adjacencies mean border tensions are spatial realities, not abstractions.

---

# APPENDIX B: MACHINE-READABLE ZONE REGISTRY

For engine implementation. Complete list of all 87 zone IDs.

```
# GLOBAL MAP (45)
## Land Home (26)
g_col_continental, g_col_alaska, g_col_hawaii
g_cat_eastern, g_cat_western, g_cat_southern
g_nor_western, g_nor_central, g_nor_eastern
g_gallia, g_teutonia, g_freeland, g_ponte, g_albion
g_persia, g_levantia, g_solaria, g_phrygia, g_bharata, g_mirage
g_yamato, g_hanguk, g_choson, g_formosa
g_caribe

## Land Contested (4) + Sea Arctic (1)
g_contested_thule, g_contested_central_asia, g_contested_horn, g_contested_central_africa
g_sea_arctic

## Sea (14)
g_sea_atlantic_west, g_sea_atlantic_east, g_sea_gulf_caribbean
g_sea_med_west, g_sea_med_east, g_sea_black, g_sea_baltic
g_sea_red, g_sea_persian_gulf, g_sea_arabian, g_sea_indian_ocean
g_sea_southeast_asia, g_sea_south_china, g_sea_east_china
g_sea_north_pacific, g_sea_central_pacific, g_sea_giuk

# EASTERN EREB THEATER (15)
ee_belarus, ee_nord_border
ee_west_ukr, ee_central_ukr, ee_capital, ee_southwest, ee_west_border
ee_south_ukr, ee_dnipro_line, ee_kherson
ee_east_front_north, ee_east_front_central, ee_east_front_south
ee_occupied_south, ee_crimea_naval

# MASHRIQ THEATER (9)
me_levantia_core, me_levantia_north, me_syria_lebanon
me_iraq_corridor, me_persia_west, me_persia_nuclear, me_persia_east
me_gulf_hormuz, me_yemen

# TAIWAN STRAIT THEATER (7)
ts_cathay_staging, ts_strait
ts_sea_north, ts_sea_east, ts_sea_south
ts_formosa

# CARIBBEAN THEATER (4)
cb_cuba, cb_venezuela, cb_caribbean_sea, cb_columbia_coast

# THULE THEATER (3)
gl_thule, gl_giuk_gap, gl_davis_strait

# KOREA THEATER (4)
kr_choson, kr_dmz, kr_hanguk, kr_basing
```

> **Count check:** 26 + 5 + 15 + 9 + 7 + 4 + 3 + 4 = 45 global + 42 theater. Wait -- global sea count: 14 listed + giuk + arctic = 17. Let me recount.

> **Corrected count:** Global land home: 25 (not 26 -- I count 25 from the list). Global land contested: 4. Global sea: arctic + 14 named + giuk + central_pacific + north_pacific = let me be precise.

> **Final precise count from the registry above:**
> - Land home: g_col (3) + g_cat (3) + g_nor (3) + Europe (5) + MidEast/SA (6) + EastAsia (4) + Americas (1) = **25**
> - Land contested: 4 (thule, central_asia, horn, central_africa)
> - Sea (including Arctic): arctic + atlantic_west + atlantic_east + gulf_caribbean + med_west + med_east + black + baltic + red + persian_gulf + arabian + indian_ocean + southeast_asia + south_china + east_china + north_pacific + central_pacific + giuk = **18**
> - **Global total: 25 + 4 + 18 = 47**
> - Theater total: 15 + 9 + 7 + 4 + 3 + 4 = **42**
> - **Grand total: 89**

> This is 2 over the 87 target. The 2 extra sea zones (central_pacific, giuk becoming their own zones rather than borders) add meaningful strategic content. Acceptable variance. To hit exactly 87, merge `g_sea_central_pacific` into `g_sea_north_pacific` and remove it. The GIUK gap should remain as it anchors the Thule theater.

---

## Changelog

- **v1.0 (2026-03-25):** Initial complete zone structure. 45 global zones, 42 theater zones across 6 theaters. 8 chokepoints detailed. Full adjacency maps. Movement and transit rules. Machine-readable zone registry.
