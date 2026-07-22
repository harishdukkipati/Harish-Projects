# 2026 World Cup — Group stage simulation

Monte Carlo simulation of the **group stage only** (round-robin: each team plays
the other three in its group). **Not** knockout/bracket prediction.

## Method

- **Simulations:** 10,000 independent group-stage draws
- **Random seed:** 42
- **Feature set:** same `FEATURE_COLS` as the champion Random Forest
  (Elo, FIFA rank score, last-12mo form, SofaScore advanced stats, confederation)
- **Feature weights:** fifa_rank_score ×4, host ×0.25, advanced ×0.5
- **Match model:** logistic regression on weighted feature diffs (team A − team B)
  trained on international results since 2010; Poisson goals calibrated from
  the same features (goals for/against per match + win probability)
- **Points:** 3 win / 1 draw / 0 loss
- **Group winner tiebreak:** points → goal difference → goals scored → head-to-head
  among tied teams
- **Advancement:** top 2 per group (`p_top2`) — 48-team format (2026)

Groups defined in `data/inputs/wc_2026_groups.json`.

> **Disclaimer:** Statistical model, not betting advice.

---

## Group A

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Czech Republic | 34.6% | 62.4% |
| South Africa | 28.6% | 56.9% |
| Mexico | 28.1% | 56.9% |
| South Korea | 8.6% | 23.9% |

**Favorite to win group A:** Czech Republic (34.6%)

## Group B

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Switzerland | 46.6% | 76.1% |
| Bosnia and Herzegovina | 29.0% | 62.0% |
| Canada | 23.4% | 56.5% |
| Qatar | 1.1% | 5.4% |

**Favorite to win group B:** Switzerland (46.6%)

## Group C

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Morocco | 42.7% | 74.8% |
| Brazil | 38.3% | 70.8% |
| Scotland | 15.5% | 40.6% |
| Haiti | 3.5% | 13.8% |

**Favorite to win group C:** Morocco (42.7%)

## Group D

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Turkey | 42.5% | 69.4% |
| United States | 26.4% | 54.5% |
| Australia | 17.9% | 41.6% |
| Paraguay | 13.2% | 34.5% |

**Favorite to win group D:** Turkey (42.5%)

## Group E

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Germany | 49.7% | 78.8% |
| Ivory Coast | 33.4% | 67.7% |
| Ecuador | 12.4% | 36.6% |
| Curaçao | 4.5% | 16.8% |

**Favorite to win group E:** Germany (49.7%)

## Group F

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Netherlands | 57.8% | 83.8% |
| Japan | 19.9% | 52.1% |
| Tunisia | 19.3% | 51.7% |
| Sweden | 2.9% | 12.3% |

**Favorite to win group F:** Netherlands (57.8%)

## Group G

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Belgium | 81.0% | 95.4% |
| Iran | 11.6% | 55.1% |
| Egypt | 6.5% | 40.2% |
| New Zealand | 1.0% | 9.3% |

**Favorite to win group G:** Belgium (81.0%)

## Group H

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Spain | 86.6% | 97.0% |
| Cape Verde | 5.4% | 39.2% |
| Uruguay | 5.1% | 40.2% |
| Saudi Arabia | 2.9% | 23.6% |

**Favorite to win group H:** Spain (86.6%)

## Group I

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Norway | 45.4% | 76.3% |
| France | 33.1% | 67.2% |
| Senegal | 19.8% | 48.4% |
| Iraq | 1.7% | 8.2% |

**Favorite to win group I:** Norway (45.4%)

## Group J

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Argentina | 55.8% | 83.4% |
| Austria | 28.3% | 65.5% |
| Algeria | 13.1% | 39.1% |
| Jordan | 2.9% | 12.0% |

**Favorite to win group J:** Argentina (55.8%)

## Group K

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| Portugal | 43.0% | 72.8% |
| Colombia | 37.7% | 69.8% |
| DR Congo | 12.0% | 33.9% |
| Uzbekistan | 7.3% | 23.5% |

**Favorite to win group K:** Portugal (43.0%)

## Group L

| Team | P(win group) | P(finish top 2) |
|------|-------------:|----------------:|
| England | 63.9% | 88.1% |
| Croatia | 22.5% | 62.4% |
| Panama | 11.2% | 37.9% |
| Ghana | 2.3% | 11.6% |

**Favorite to win group L:** England (63.9%)

---

## Group C snapshot (Brazil · Morocco · Haiti · Scotland)

- **Morocco:** 42.7% win group, 74.8% top 2
- **Brazil:** 38.3% win group, 70.8% top 2
- **Scotland:** 15.5% win group, 40.6% top 2
- **Haiti:** 3.5% win group, 13.8% top 2
