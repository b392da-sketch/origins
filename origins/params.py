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
FARM_RATE = 3.0                    # food units per worker-day farming a fully domesticated species on ideal land
FARM_CAPACITY = 1200               # people a cell (about 3,100 km2) of ideal farmland can feed; foraging feeds 10-200
FARM_RISK = 0.8                    # farmers discount a harvest's promise for its risk
FARM_INERTIA = 0.15                # yearly share of the gap between current and preferred work split that is closed
HARVEST_QUARTER = 2                # crops come in once a year (third season)
PRESSURE_MARGIN = 1.6              # food gathered / needed below this presses a people towards new food
TEND_STILL_YEARS = 5               # years in one area before a people begins to tend a wild plant or herd
TEND_RATE = 1 / 200                # yearly progress of tending at full pressure on ideal land
CULTIVATE_RATE = 1 / 400           # yearly progress from tending to cultivation
DOMESTICATE_RATE = 1 / 800         # yearly progress from cultivation to domestication (when farming fully)
LEARN_CHANCE = 0.1                 # yearly chance a band compares notes with a neighbour
LEARN_SHARE = 0.3                  # share of a neighbour's lead in a skill learned at once
FIRST_VILLAGE_YEARS = 75           # years mainly farming before a village counts as a lasting farming village
STORAGE = True                     # gate G2 knock-out: False keeps every store at the foragers' size and spoilage
GRANARY_DAYS = 400                 # days of needs a farming household can store (grain in pits, baskets, pots)
GRAIN_SPOIL = 0.05                 # share of stored grain lost each season
FARMER_NURSING_1 = 0.25            # settled mothers with weaning foods: conception multiplier with a child under 2
FORAGER_OUTBREAK = 0.3             # outbreak start rate multiplier for foragers (scattered, mobile)
VILLAGE_OUTBREAK = 2.0             # ... for villages (crowded, settled, near animals)


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
