#ifndef POKEPLATINUM_CONSTANTS_SPECIES_H
#define POKEPLATINUM_CONSTANTS_SPECIES_H

#include "generated/species.h"

#define MAX_SPECIES        SPECIES_BAD_EGG
#define NATIONAL_DEX_COUNT (MAX_SPECIES - 2)

// The sound archive has cry banks/wave archives indexed by species only up to
// here; later species fall back to the default cry until theirs are added.
#define LAST_SPECIES_WITH_CRY SPECIES_ARCEUS

#endif // POKEPLATINUM_CONSTANTS_SPECIES_H
