# Proposal: how farming starts (M2's trigger, revisited in M4a)

**Status:** PROPOSED for Ben, 14 November 2026. Changes M2's model, so gate G4a must recheck M2's checks.

## 1. The problem

In M2, a band begins to tend a wild plant or herd only when it is **pressed**: its food margin (food gathered and stored against need) falls below `PRESSURE_MARGIN`. The same pressure drives sowing and domestication.

M4a's technique effects showed this trigger is fragile. Anything that makes foragers' food go further keeps margins above the line, and farming never starts. On planet 3, history 1, from the first people (all values are tunable starting values):

| Run | Bands farming by year 6,000 | First village |
|---|---|---|
| technology off | 12 | year 6,794 |
| technology on, all effects off | 12 (identical history) | year 6,794 |
| all effects on | 0 | none by year 10,000 |
| foraging gear off (broad-spectrum food at zero) | 0 | none by year 10,000 |
| foraging gear off, storage effects off | 12 (as technology off) | year 6,744 |
| foraging gear off, canoe crossings off, storage on | 0 | none by year 10,000 |
| broad-spectrum food as good as wild food | 0 | none by year 10,000 |
| broad-spectrum food at 0.3 of the return | 0 | none by year 10,000 |

Two effects each stop farming: foraging gear (more food for foragers) and storage (food that lasts longer). Canoe crossings do not. Real foragers had both nets and baskets, and still came to farm.

## 2. What the literature says

- **Pressure, as population against wild food.** In eastern North America, population nearly doubled between about 6,900 and 5,200 years ago, just before plants were domesticated around 5,000 years ago (Weitzel & Codding 2016). The pressure is long-term crowding against wild food and falling returns, not running short in a bad season.
- **Abundance and niche construction.** The rival view: domestication came from experiment in times of plenty, by settled people enhancing rich local resources (Zeder 2012). Debated; Weitzel and Codding argue it does not fit eastern North America.
- **Climate.** Agriculture was nearly impossible in the last ice age (dry, variable over millennia, low CO₂: about 190 ppm against about 250 ppm early in the Holocene) and became close to mandatory in the stable Holocene through a "competitive ratchet": intensive users of land grow and displace others (Richerson, Boyd & Bettinger 2001).
- **Not a better technology.** Early cereal farming yielded about three fifths of what foraging did (Bowles 2011); it spread with property that could be marked out and defended (Bowles & Choi 2013).
- **Slow.** Domesticated wheat emerged over roughly 3,000 years, with wild wheat still harvested meanwhile (Tanno & Willcox 2006).

## 3. Proposed trigger

Pressure is measured as people against the **wild food their land gives without help** (the cell's ordinary wild food capacity, before gear or stores), not as food in hand. Gear and storage then feed people and buffer bad years without hiding the crowding beneath.

1. **Route A, crowding (behavioural ecology).** `pressure = clip((people on the cell and its neighbours / their wild-food capacity − CROWD_START) / CROWD_RANGE, 0, 1)`, combined with the existing hunger pressure as the larger of the two. A band settled for `TEND_STILL_YEARS` with wild species on its land begins to tend with chance `TEND_START x pressure x land quality`, as now.
2. **Route B, abundance (niche construction).** A band settled for `ABUNDANCE_YEARS` (proposed 20, as for building) on land rich in wild domesticable species may begin to tend without pressure, at a much lower rate: `ABUNDANCE_START x land quality`. Proposed `ABUNDANCE_START` = one tenth of `TEND_START`.
3. **Sowing and domestication** keep M2's rates, driven by the larger of farming share and pressure (Route A) or by a small floor for settled bands in rich places (Route B). Together they take well over a thousand years at full pressure, longer otherwise. That fits the slow transition (Tanno & Willcox 2006); the gate measures it.
4. **Wild gathering continues** alongside farming, as it already does (farming takes a share of work).

**Not proposed now:** an ice age and a Holocene. The planets have no glacial climate, so farming can begin tens of thousands of years earlier than on Earth. Richerson et al. suggest this matters. It would be a climate change to the planets, for a later milestone if wanted.

## 4. How it would be checked

- Farming must start with **all technique effects on**, foraging gear included, and at about the old time without technology (planet 3: around year 6,800 as a reference, not a target).
- A trial on several planets, then gate G4a, which includes M2's checks (farming is an option, not a destiny: some regions stay foraging; farming arises in more than one place; etc.).
- Both routes recorded in the cause of each first tending: "began to tend wild grain: 1.4 people per unit of wild food within reach" or "began to tend wild grain, settled 35 years on rich land".

## Sources

- Bowles, S. (2011). Cultivation of cereals by the first farmers was not more productive than foraging. *PNAS*, 108(12), 4760–4765.
- Bowles, S., & Choi, J.-K. (2013). Coevolution of farming and private property during the early Holocene. *PNAS*, doi:10.1073/pnas.1212149110.
- Richerson, P. J., Boyd, R., & Bettinger, R. L. (2001). Was agriculture impossible during the Pleistocene but mandatory during the Holocene? A climate change hypothesis. *American Antiquity*, 66(3), 387–411.
- Tanno, K., & Willcox, G. (2006). How fast was wild wheat domesticated? *Science*, 311, 1886.
- Weitzel, E. M., & Codding, B. F. (2016). Population growth as a driver of initial domestication in Eastern North America. *Royal Society Open Science*, doi:10.1098/rsos.160319.
- Zeder, M. A. (2012). The Broad Spectrum Revolution at 40: Resource diversity, intensification, and an alternative to optimal foraging explanations. *Journal of Anthropological Archaeology*, 31, 241–264.
