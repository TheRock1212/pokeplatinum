#include "macros/btlcmd.inc"

@ Expansion: written by hand. Clears the terrain (end of turn countdown, Defog)
_000:
    GotoIfTerrainOverlayIsType GRASSY_TERRAIN, _grassy
    GotoIfTerrainOverlayIsType MISTY_TERRAIN, _misty
    GotoIfTerrainOverlayIsType ELECTRIC_TERRAIN, _electric
    GotoIfTerrainOverlayIsType PSYCHIC_TERRAIN, _psychic
    End

_grassy:
    // The grass disappeared from the battlefield.
    PrintMessage BattleStrings_Text_HgEngine1389, TAG_NONE
    GoTo _clear

_misty:
    // The mist disappeared from the battlefield.
    PrintMessage BattleStrings_Text_HgEngine1391, TAG_NONE
    GoTo _clear

_electric:
    // The electricity disappeared from the battlefield.
    PrintMessage BattleStrings_Text_HgEngine1393, TAG_NONE
    GoTo _clear

_psychic:
    // The weirdness disappeared from the battlefield.
    PrintMessage BattleStrings_Text_HgEngine1395, TAG_NONE

_clear:
    Wait
    WaitButtonABTime 30
    UpdateTerrainOverlay TRUE, _end
    RefreshTerrainBackground

_end:
    End
