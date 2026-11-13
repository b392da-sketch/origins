"""Tunable starting values (M0, with M1 additions at the end). None of these are measurements.

Units: one food unit = one adult's food needs for one day.
Time: one tick = one season = 91.25 days; four ticks per year.
"""

SEASON_DAYS = 91.25
TICKS_PER_YEAR = 4
START_YEARS_BP = 50_000
FOUNDING_BAND = 30
FOUNDING_BANDS = 3            # number of founding bands (each of FOUNDING_BAND people) in neighbouring land; decided by Ben, 6 Nov 2026

# --- Food and foraging
STOCK_MULTIPLIER = 1.6        # standing wild food = capacity * daily need * season days * this
REGROWTH = 0.55               # fraction of the gap to the seasonal maximum regrown each season
FORAGE_RATE = 2.4             # food units a full worker can gather per day when food is plentiful
STORE_DAYS = 45               # perishable store a band can carry, in days of its needs
STORE_SPOIL = 0.3             # fraction of carried store lost each season

# --- Climate variability (per region, per year)
CLIMATE_AR = 0.5
CLIMATE_SIGMA = 0.20
CLIMATE_MIN, CLIMATE_MAX = 0.45, 1.5
BAD_YEAR = 0.80               # yearly factor below this is recorded as a bad year

# --- Body condition (0 = starving, 1 = well fed)
CONDITION_LOSS = 0.9          # per season, times the shortfall fraction
CONDITION_GAIN = 0.35         # per season when fully fed

# --- Mortality: Siler-type annual hazard plus hunger
SILER_A1, SILER_B1 = 0.33, 1.0     # infant and early-childhood risk, falling with age
SILER_A2 = 0.012                   # age-independent accident and illness
SILER_A3, SILER_B3 = 0.00015, 0.085  # senescence, rising with age
HUNGER_HAZARD = 2.0                # annual hazard at condition 0
HUNGER_ONSET = 0.6                 # hunger becomes a death risk only below this body condition
HUNGER_POWER = 2.0
HUNGER_VULNERABLE = 2.5            # multiplier under 5 and over 60
ORPHAN_INFANT_HAZARD = 1.5         # annual, infant under 1 whose mother has died
MATERNAL_DEATH = 0.01              # per birth

# --- Fertility and partnership
FEMALE_MIN_AGE, FEMALE_MAX_AGE = 15, 49
MALE_MIN_AGE, MALE_MAX_AGE = 17, 60
CONCEPTION = 0.085                  # per season at peak fecundity, well fed, not nursing
NURSING_SUPPRESS_1 = 0.10          # youngest child under 2
NURSING_SUPPRESS_2 = 0.5           # youngest child 2-3
PREGNANCY_TICKS = 3
PAIRING = 0.6                      # per season, chance an unpartnered woman finds a partner
PARTNER_RINGS = 2                  # partners are sought within two rings of land (a regional marriage network)
SEPARATION = 0.005                 # per season
RESIDENCE_WITH_HUSBAND = 0.5       # M0 only; from M1 set by each band's marriage-residence custom (sim/customs.py)
FERTILE_CONDITION = (0.5, 0.4)     # conception zero below body condition 0.5, full above 0.9
FERTILE_MARGIN = (1.0, 0.5, 0.15)  # food gathered/needed (recent seasons): full fertility above 1.5, falling to 15% at 1.0 or less
MARGIN_MEMORY = 0.5                # weight of the previous seasons in the band's food margin

# --- Bands
FISSION_SIZE = 50
VILLAGE_FISSION_SIZE = 150        # farming villages hold more people before a daughter village is founded
GROUP_FISSION_SIZE = 200          # groups are local populations, not single bands
STRESS_FISSION_MIN = 24
STRESS_FISSION_RATIO = 0.85
GROUP_HUNGER_EVENT = 0.03         # log group hunger deaths only above this share of the group in a season
MERGE_SIZE = 10
MOVE_THRESHOLD = 1.15             # move if a neighbouring cell offers this much more food per person
INDIVIDUAL_THRESHOLD = 20_000      # above this many individuals, distant bands fold into groups
FOLD_TARGET = 0.9                  # fold down to this share of the threshold


# --- Languages (M1). Retention target: about 80% of core words per 1,000 years (Lees 1953), a plausibility range.
LANGUAGE_CHECK_YEARS = 25
SOUND_CHANGE_YEARS = 450           # mean years between regular sound changes in one language
WORD_REPLACEMENT_RATE = 0.0002     # per meaning per year
BORROWING_RATE = 0.004             # words borrowed per year by a language in contact with others
LANGUAGE_SPLIT_CHECKS = 6          # checks in a row with separated speakers before a split (about 150 years, several generations)
LANGUAGE_SPLIT_PEOPLE = 250        # a separated community must have at least this many people to become its own language
LANGUAGE_SHIFT = 0.8              # chance per check (25 years, about a generation) that a band surrounded by another language takes it up
LANGUAGE_SHIFT_MAJORITY = 0.5      # ... when this share of the people within two rings speak it
LANGUAGE_MAX_CELLS = 40            # a language spread over more land than this splits in two

# --- Customs (M1)
CUSTOM_INVENTION = 0.0002          # per custom per band per year
CUSTOM_COPYING = 0.05              # per band per year, copy one custom from a band in contact
NEUTRAL_DRIFT = 0.007               # yearly random drift of each neutral trait (standard deviation)
NEUTRAL_COPY = 0.3                 # share of the difference closed when copying from a band in contact
NEUTRAL_SCALE = 0.5                # neutral distance at which cultural distance saturates

# --- Hazards (M1). Yearly chances per land cell unless stated.
HAZARD_RECOVERY = 0.35             # share of lost wild food recovered each year
FLOOD_RATE = 0.015                 # river cells, scaled by the year's wetness
FLOOD_FOOD, FLOOD_DEATHS = 0.75, 0.01
FIRE_RATE = 0.001                  # burnable vegetation, scaled by dryness
FIRE_FOOD, FIRE_DEATHS = 0.6, 0.003
ERUPTION_RATE = 1 / 4000           # volcanic cells
LARGE_ERUPTION = 0.08              # share of eruptions that are large (wide ash, regional cooling)
ERUPTION_FOOD, ASH_FOOD, ERUPTION_DEATHS = 0.05, 0.6, 0.25
ERUPTION_COOLING = 1.5             # climate anomaly (standard deviations) after a large eruption, fading over years
QUAKE_RATE = 1 / 600               # plate-boundary cells
QUAKE_DEATHS = 0.02                # foragers in light shelters: few deaths
OUTBREAK_RATE = 0.0002             # per 100 people per year, rising with crowding
OUTBREAK_SPREAD = 0.3             # yearly chance to reach each peopled cell in contact
OUTBREAK_DEATHS = 0.15             # deaths among the non-immune at full severity
OUTBREAK_IMMUNITY, IMMUNITY_LOSS = 0.8, 0.05
CROSSING_HUNGER = 0.9              # a band receiving less than this share of its needs may cross the sea
CROSSING_RATE = 0.2                # yearly chance such a band crosses, when land is visible across one ocean cell

# --- Farming (M2)
FARMING = True                     # False: no tending, cultivation or domestication (for regression checks of M0/M1)
FARM_RATE = 3.0                    # food units per worker-day farming a fully domesticated species on ideal land
FARM_CAPACITY = 1200               # people a cell (about 3,100 km2) of ideal farmland can feed; foraging feeds 10-200
FARM_RISK = 0.8                    # farmers discount a harvest's promise for its risk
FARM_INERTIA = 0.15                # yearly share of the gap between current and preferred work split that is closed
HARVEST_QUARTER = 2                # crops come in once a year (third season)
PRESSURE_MARGIN = 1.6              # food gathered / needed below this presses a people towards new food
TEND_STILL_YEARS = 5               # years in one area before a people begins to tend a wild plant or herd
TEND_START = 5e-6                  # yearly chance a pressed band first begins to tend a wild species (per unit pressure and land quality)
CULTIVATE_START = 1e-6             # yearly chance a band that tends a species first sows it deliberately (per unit pressure and land quality)
TEND_RATE = 1 / 200                # yearly progress of tending at full pressure on ideal land
CULTIVATE_RATE = 1 / 400           # yearly progress from tending to cultivation
DOMESTICATE_RATE = 1 / 600         # yearly progress from cultivation to domestication (when farming fully, or fully pressed)
LEARN_CHANCE = 0.1                 # yearly chance a band compares notes with a neighbour
LEARN_SHARE = 0.3                  # share of a neighbour's lead in a skill learned at once
FIRST_VILLAGE_YEARS = 75           # years mainly farming before a village counts as a lasting farming village
STORAGE = True                     # gate G2 knock-out: False keeps every store at the foragers' size and spoilage
GRANARY_DAYS = 400                 # days of needs a farming household can store (grain in pits, baskets, pots)
GRAIN_SPOIL = 0.05                 # share of stored grain lost each season
FARMER_NURSING_1 = 0.25            # settled mothers with weaning foods: conception multiplier with a child under 2
SURPLUS_RESERVE = 0.75            # share of a year's needs kept back after harvest before anything counts as surplus
SPECIALIST_MAX = 0.3               # at most this share of a band can be specialists
PROPERTY_SHARE = 0.5               # bands farming at least this share of their work hold fields and stores by household
WEALTH_LUCK = 0.1                  # yearly spread of households' harvest luck (log scale) at full surplus (0.25 until 12 Nov 2026: inequality hit its ceiling within a few centuries, leaving nothing to compound)
DOWRY_SHARE = 0.3                  # share of a mother's household holdings a daughter's new household takes
NEW_HOUSEHOLD_START = 0.5          # a new household with no mother to endow it starts with this share of the village mean (1.0 until 11 Nov 2026; 0.1 on 11-12 Nov gave a Gini of 0.62-0.73; 0.5 gives about 0.40, between Kohler et al. 2017 house sizes and Borgerhoff Mulder et al. 2009 agriculturalists)
SURPLUS_FOR_FULL_LUCK = 150.0      # surplus per person (food units) at which luck has its full effect
FORAGER_OUTBREAK = 0.3             # outbreak start rate multiplier for foragers (scattered, mobile)
VILLAGE_OUTBREAK = 2.0             # ... for villages (crowded, settled, near animals)
INHERITANCE_BY_CUSTOM = True         # M3 (Ben, 11 Nov 2026, check 9 option a): holdings pass by the succession custom (one heir), not always in equal shares
LAND_ADVANTAGE = 0.03              # M3: yearly growth of a household's holdings per unit of its size above the village mean, in full villages
LAND_SCARCE = 0.5                  # M3: a village's land counts as scarce from this share of what its farmland can feed
HERD_GROWTH = 0.005                 # (0.02 until 14 Nov 2026; with common pasture, herding societies' Gini 0.49-0.50 against 0.42 for pastoralists in Borgerhoff Mulder et al. 2009) M3: yearly growth of holdings in animals (herds breed), before losses
LAND_HERDS = 0.0                   # M4a (Ben, 14 Nov 2026): pasture is held in common, herds privately (Fratkin & Mearns 2003): crowding gives the richer no extra pasture
HERD_THRESHOLD = 0.5               # M3 (12 Nov 2026): below this share of the village mean, a household's herd shrinks instead of breeding (Lybbert et al. 2004)
HERD_RISK = 1.0                    # M3: herds' extra spread of luck (disease, drought, raids), as a share of the harvest's


# --- Polities and institutions (M3)
POLITIES = True                    # False: villages never come under one another's leaders
INSTITUTIONS = True                # gate G3 knock-out: False means polities can never build institutions
ALLIANCE_RATE = 0.05               # yearly chance an autonomous village considers a leader of greater standing nearby
TRIBUTE_SHARE = 0.3                # share of a member's surplus sent each year towards the seat
SUB_LEADER_KEEP = 0.3              # share of passing tribute a sub-leader keeps
POLITY_CAPACITY = 3.0              # load (about three nearby villages of 150) a leader can hold without institutions
INSTITUTION_GAIN = [1.0, 2.0, 1.0, 1.0, 0.0]   # added capacity (as multiples of the base) for each institution
COUNCIL_LOAD = 0.8                 # a council of village heads lightens each member's load to this share
OFFICIALS_MULTIPLIER = 3.0         # officials over districts multiply what a polity can hold
INSTITUTION_INVENT = 0.01          # yearly chance a pressed polity finds its next institution on its own
INSTITUTION_COPY = 20.0            # ... multiplied by this where a polity within three rings already has it
INSTITUTION_STAFF = [0.5, 1.0, 0.7, 1.5, 1.5]  # specialists each institution needs, per square root of settlements
INSTITUTION_PRESSURE = 0.8         # a polity looks for an institution when load passes this share of capacity
LOAD_DISTANCE = 4.0                # cells at which distance doubles a settlement's load
LOAD_CULTURE = 2.0                 # how much cultural difference adds to a settlement's load (at full difference)
DELEGATED_LOAD = 0.5               # a settlement ruled through a district head weighs this much on the seat (check 5 option b, 12 Nov 2026: hierarchy relieves scalar stress)
SECESSION_BASE = 0.001             # yearly chance a member leaves when all is well (0.002 in G3 run 1; halved 12 Nov 2026, check 5 option c)
SECESSION_OVERLOAD = 0.05          # ... added per unit of overload (load / capacity above 1)
SECESSION_STRESS = 0.01            # (0.02 in G3 run 1; halved 12 Nov 2026, check 5 option c) ... added per unit of stress (failed harvest at the seat, contested succession, hunger)
LAW_CALM = 0.3                     # law and judges cut the chance of secession by this share
CONTESTED_SUCCESSION = [0.25, 0.2, 0.1, 0.25]   # chance a succession is contested, by custom (son, sister's son, council, daughter)
CONTEST_YEARS = 5                  # years a contested succession weakens a polity
PASTORALISM = True                 # M4a (13 Nov 2026): herding peoples move their herds to better pasture
PASTORAL_SHARE = 0.7               # a band farming mainly by herds: at least this share of its farming value in animals
PASTORAL_MOVE = 1.25               # it moves when a neighbouring area offers this many times the pasture per person
FLIGHT_RATE = 0.01                 # M4a (13 Nov 2026): yearly chance a member village under a polity takes flight to open land, x (1 + hunger + overload) (Carneiro 1970); 0 turns it off
FLIGHT_LAND = 0.7                  # open land must offer at least this share of the farming value of home
FLIGHT_OPEN = 0.25                 # ... and be farmed below this share of its capacity, outside every polity
NOTABLE_MEMORY = 100               # years a seat stays individual after its polity was last a chiefdom or state (12 Nov 2026: seats were folding and unfolding as polities crossed the chiefdom line)
NOTABLE_SEATS = 200                # the seats of at most this many chiefdoms and states are kept person by person

# --- Conflict (M3)
CONFLICT = True                    # False: no raids or wars
WAR_BASE = 0.03                    # yearly chance a side attacks its most tempting neighbour, at even strength
WAR_CONSIDER = 0.25                # share of sides that weigh war each year (the chance of war is capped at this)
WAR_SCARCITY = 3.0                 # ... multiplied by (1 + this x scarcity), scarcity 0-1 from food gathered / needed
WAR_SCARCITY_MARGIN = 1.3          # food gathered / needed below which a side counts as pressed
WAR_CULTURE = 1.0                  # ... and by (1 + this x cultural distance)
WAR_GRIEVANCE = 0.5                # ... and by (1 + this x remembered killings / 10, at most 3)
WAR_NEW_LEADER = 1.5               # a leader in the first three years is more likely to fight
GRIEVANCE_MEMORY = 0.93            # share of a grievance remembered from one year to the next
DEFENDER_ADVANTAGE = 1.5           # defenders fight on their own ground
WARRIOR_STRENGTH = 0.5             # warriors kept by a leader add this share to a side's strength
WAR_DECISIVENESS = 2.0             # how strongly the stronger side wins (1: in proportion to strength)
WAR_LOSS = 0.3                     # share of the fighters on each side who die in a war, before strength
RAID_TAKE = 0.3                    # share of the loser's stores a winner carries off
CAPTIVE_SHARE = 0.05               # share of the loser's young women and children taken into the winner's people
CONQUEST_CHANCE = 0.3              # chance a winning farming side takes the losing farming village
CONQUEST_ROOM = 1.0               # a polity annexes only if its load after the conquest would stay below this share of its capacity (before 12 Nov 2026: its load before)
CONQUEST_LOAD = 1.0                # a newly conquered settlement weighs this much more on its conqueror's load ...
CONQUEST_MEMORY = 100              # ... fading over this many years
DEFEAT_YEARS = 5                   # years a lost war weakens a polity


def need(age, sex, pregnant, nursing):
    """Daily food units needed by one person (vectorised)."""
    import numpy as np
    n = np.select([age < 1, age < 5, age < 10, age < 15, age >= 60],
                  [0.30, 0.45, 0.60, 0.80, 0.85],
                  default=np.where(sex == 1, 1.0, 0.9))
    return n + 0.15 * pregnant + 0.25 * nursing


def work(age, nursing):
    """Worker-equivalents contributed to foraging (vectorised)."""
    import numpy as np
    w = np.select([age < 6, age < 12, age < 16, age < 56, age < 66],
                  [0.0, 0.25, 0.6, 1.0, 0.7], default=0.35)
    return w * np.where(nursing, 0.7, 1.0)

# --- M4a: the technology network (M4 specification section 3; starting values to be tuned) ---
TECHNOLOGY = True
TECH_WORKING = 0.5                 # skill level at which a technique counts as held (prerequisites, diffusion)
TECH_INVENT = 2e-5                 # yearly chance a band invents a technique it could hold, at reference population and no pressure ...
TECH_NEED_FLOOR = 0.2              # ... times (this + the pressure behind it, 0..1) ...
TECH_POP_REF = 1000                # ... times (people within two rings / this) ...
TECH_POP_EXPONENT = 1.0            # ... to this power (0: the knock-out with no population effect, specification check 6)
TECH_INVENT_LEVEL = 0.6            # skill level of a new invention
TECH_STORE_REF = 90                # stores per person (days) below which the need for containers rises

