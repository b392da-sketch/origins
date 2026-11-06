# Gate G1 report — 'spreading and drifting apart'

Histories found: 4 of 300 years on 2 planets (target 75 = 5 × 15; minimum 50).

Environment: Python 3.13.18, NumPy 2.5.4

All rates are tunable starting values (origins/params.py), not measurements.

| Check | Result | Evidence |
|---|---|---|
| 1. M0 still holds | FAIL | survival 4 of 4; highest population ÷ capacity 0.142 (≤ 1.0); life expectancy 32.0–33.3, births per woman 4.72–5.04, median band 27–31 (4 of 4 in all ranges); 0 accounting failures; exact replay 0 of 0; cause chains complete for 648 of 648 sampled deaths and events |
| 2. Spread | FAIL | at year 300, occupied land holds 1%–2% of the starting land mass's food capacity (median 1%; at least 80% in 0 of 4 histories, pass mark 90%), on 0%–1% of its cells (the rest is mostly ice, desert and high mountains); 0 of 4 histories made at least one sea crossing (median 0), and 0 have people on more than one land mass at the end (every planet has islands within one sea cell) |
| 3. Drift with distance | FAIL | rank correlation between distance apart and cultural distance (400 random band pairs per history, final year): -0.03–0.57 (median 0.34); clearly positive (above 0.2) in 3 of 4 histories (pass mark 90%). Parts on their own: customs median 0.34, language median nan |
| 4. Drift with time | FAIL | no retention measurements |
| 5. Languages multiply | — | living languages at year 300: 1–1 (median 1); ever spoken 1–1; families (languages sharing an ancestor less than 2,500 years back): 1–1 (median 1); speakers per language median 534; no languages across the sea to compare. The pass count is for Ben to set from these runs. |
| 6. Regular sound change | PASS | 372 of 372 words rebuilt exactly from the proto-language by replaying every recorded change (each rule is applied to the whole vocabulary at once); 796 of 796 living people's names rebuilt from their language's words; sound changes per history 0–1 |
| 7. Hazards in the right places | PASS | hazards logged in impossible places: 0; frequencies (all land, peopled or not): flood once per 58 years per affected cell; wildfire once per 347 years per affected cell; eruption once per 3,841 years per affected cell; earthquake once per 593 years per affected cell; plausibility ranges: flood 1/15–1/200; wildfire 1/50–1/2,000; eruption 1/1,000–1/20,000; earthquake 1/100–1/3,000 |
| 8. Hazard responses | FAIL | flood: 20 with deaths (mean 2.8% of the area's people); local population lower a year later in 30%, back to 90% within 20 years in 50%; wildfire: 1 with deaths (mean 4.0% of the area's people); local population lower a year later in 0%, back to 90% within 20 years in 100%; eruption: none with deaths among people; earthquake: 2 with deaths (mean 2.2% of the area's people); local population lower a year later in 50%, back to 90% within 20 years in 50%; outbreak: none with deaths among people. Every hazard death names its hazard in its cause chain (check 1). |
| 9. Outbreaks spread by contact | FAIL | yearly chance a peopled area falls ill: 0.0% when in contact with an outbreak (0 of 0 area-years) vs 0.000% otherwise (0 new outbreaks in 8,599 area-years): 0 times higher (pass mark 10×) |
| 10. Groups match individuals at the food limit | FAIL | not run |
| 11. Speed | — | 300 years took 4–6 s (median 4 s) of computing per history; median by planet: 1: 4 s, 2: 5 s |

Final populations at year 300: 194–631 (median 516).
Deaths by cause, all histories: accident or illness 41.3%, infancy and early childhood 29.0%, old age 27.2%, childbirth 1.2%, orphaned infant 0.9%, flood 0.4%, earthquake 0.0%, wildfire 0.0%.
