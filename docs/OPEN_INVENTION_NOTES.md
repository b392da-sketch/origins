# Open-ended invention: literature check and feasibility notes

Claude, 27 November 2026. **Status: research only.** Ben asked for this on 27 November 2026, after approving "open-ended invention after M6" in the weaknesses proposal (`docs/WEAKNESSES_PROPOSAL.md`, decision 6). No code and no design change until Ben decides.

**The independent check:** the question is posted to the Notion database "Origins — Research questions" for ChatGPT, without these findings: "Open-ended invention: how do new techniques arise from existing ones, and how could a simulator generate techniques no one wrote down in advance?". When its answer is in, the two are compared here, and the verified sources go into "Origins — Sources".

## Claude's literature check (first pass)

Each source was opened and checked as noted. "Full text" means the paper itself was read, not only an abstract.

| Source | How read | What it says that bears on this |
|---|---|---|
| Arthur & Polak, "The evolution of technology within a simple computer model", Santa Fe Institute Working Paper 2004-12-042 (2004); published in *Complexity* (2006); volume and pages not yet confirmed. [PDF](https://sites.santafe.edu/~wbarthur/Papers/AP-Complexity.pdf) | Full text (working paper) | Technologies are logic circuits built by wiring together 2 to 12 existing circuits, starting from NAND gates. A new circuit is kept if it meets one of a **fixed list of needs** (adders, comparators and so on) better or more cheaply than the current best. Better ones replace older ones wherever they are used, which sets off avalanches of obsolescence of every size, roughly a power law. Usage is heavily skewed. Most important here: "The algorithm does not produce complex circuits without intermediate needs present". Without the full-adder need, not even a 2-bit adder appeared in a million steps. |
| Youn, Strumsky, Bettencourt & Lobo 2015, "Invention as a combinatorial process: evidence from US patents", *J. R. Soc. Interface* 12(106): 20150272, [doi:10.1098/rsif.2015.0272](https://doi.org/10.1098/rsif.2015.0272) | Full text (PMC) | 77% of US patents from 1790 to 2010 combine at least two technology codes. About 60% of new patents bring a new combination, and the ratio is "arguably invariant" over 220 years. New codes slow down after about 1870, while combinations go on unabated. Reuse is far from random: heavy-tailed, roughly a power law. Older codes are not favoured. |
| Kolodny, Creanza & Feldman 2015, "Evolution in leaps: the punctuated accumulation and loss of cultural innovations", *PNAS* 112(49): E6762–E6769, [doi:10.1073/pnas.1520492112](https://doi.org/10.1073/pnas.1520492112) | Full text (PMC) | Three paths to new tools: rare "lucky leap" inventions; a toolkit of tools that one such invention makes useful (1 to 20 each); and combinations of existing tools. Leaps alone give linear growth. Adding toolkits gives long stasis broken by bursts, like the archaeological record. Adding combination gives faster than linear growth. Losing a key tool loses its whole toolkit and its combinations. Population size sets a "cultural carrying capacity", and a subdivided population behaves like a smaller one. |
| Lewis & Laland 2012, "Transmission fidelity is the key to the build-up of cumulative culture", *Phil. Trans. R. Soc. B* 367(1599): 2171–2180, [doi:10.1098/rstb.2012.0119](https://doi.org/10.1098/rstb.2012.0119) | Full text (PMC) | A model with novel invention, modification and combination. Low loss (faithful transmission) matters most for building up culture, combination next, and novel invention least. It is a simulation result; the authors note there are no data on fidelity rates. |
| Derex & Boyd 2016, "Partial connectivity increases cultural accumulation within groups", *PNAS* 113(11): 2982–2987, [doi:10.1073/pnas.1518798113](https://doi.org/10.1073/pnas.1518798113) | Full text (PMC) | A laboratory experiment with 144 people in groups of six, combining ingredients along two paths. Fully connected groups converged on one path and never combined both; partially connected groups did so in 58% of cases. The authors caution that fragmentation also raises loss, so there is probably an optimal level of connectedness. |
| Muthukrishna & Henrich 2016, "Innovation in the collective brain", *Phil. Trans. R. Soc. B* 371(1690), [doi:10.1098/rstb.2015.0192](https://doi.org/10.1098/rstb.2015.0192) | Full text (LSE repository copy) | A review. Innovation comes from serendipity, recombination ("new ideas are born at the social nexus where previously isolated ideas meet") and incremental improvement, not lone geniuses. Larger and more connected populations innovate more, but too much connection reduces variance. The authors say much of the evidence is case studies. |
| Ogburn & Thomas, "Are inventions inevitable? A note on social evolution", *Political Science Quarterly* 37(1): 83–98 (1922). [archive.org text](https://archive.org/stream/jstor-2142320/2142320_djvu.txt) | Full text (scan); the year and last page are from the catalogue | Lists 148 inventions and discoveries made independently by more than one person. Invention needs its cultural elements to exist first: "Necessity will not produce an invention without the existence of the essential elements." |
| Arthur 2009, *The Nature of Technology: What It Is and How It Evolves*, Free Press, ISBN 978-1-4165-4405-0 | Through reviews: Publishers Weekly (29 June 2009); Dan Gordon, *Issues in Science and Technology* 26(3), Spring 2010 | New technologies are combinations of existing ones, and every technology harnesses natural phenomena. Gordon's criticisms: the theory makes few testable predictions; it neglects social relations of production; and the circuit simulation shows little beyond its assumptions. **The book itself is still to be read.** |

## What this means for Origins (Claude's interpretation, for Ben)

1. **The evidence supports combination as the main engine of invention**, gated by what already exists. That fits Origins' existing technology system, where techniques need others and invention needs skill, need and connection.
2. **No published model found so far invents its own goals.** Arthur and Polak's open-endedness is in the means: new designs meet a fixed list of needs. That suggests a feasible version for Origins:
   - a fixed set of human needs and effect channels (food got, food kept, carrying, shelter, warmth, fighting, record-keeping, and so on), already the channels the simulation uses;
   - open-ended combinations of materials, processes and earlier techniques to meet them;
   - effects judged by measured performance against those needs.

   Fully open-ended ends would be a research problem, not an engineering one.
3. **Intermediate steps are essential** (Arthur & Polak). Complex techniques appear only if simpler ones meeting simpler needs come first. The needs list must have a ladder.
4. **Loss matters as much as invention** (Lewis & Laland; Kolodny et al.): faithful transmission, connected populations, and loss cascades when a key technique is lost. Origins already models transmission and loss; it would need to carry dependants down with a lost technique.
5. **Partial connection helps combination** (Derex & Boyd; Muthukrishna & Henrich). Separate peoples develop different paths, and contact combines them. This is a behaviour a gate could test.
6. **Testable patterns:**
   - long stasis broken by bursts;
   - heavy-tailed reuse of a few key techniques;
   - avalanches of obsolescence;
   - independent reinvention where the parts exist;
   - growth with population and connection.
7. **The open problem:** judging a new design's usefulness without hand-writing it. Arthur and Polak could compute a circuit's function exactly; Origins would need a small physics of materials and processes, each property with a source. That is the part to prototype first, outside the simulation.

## Next

- Compare with ChatGPT's independent check when it is in.
- Read Arthur 2009 itself; confirm the *Complexity* volume and pages.
- Look further for archaeological evidence on how prehistoric techniques combined, and for any model that judges designs by simulated physics.
- Then a short feasibility note for Ben, with a stand-alone prototype plan.
