"""Tunable starting values for M0. None of these are measurements.

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
RESIDENCE_WITH_HUSBAND = 0.5
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
MOVE_THRESHOLD = 1.15
INDIVIDUAL_THRESHOLD = 20_000      # above this many individuals, distant bands fold into groups
FOLD_TARGET = 0.9                   # fold down to this share of the threshold             # move if a neighbouring cell offers this much more food per person


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
