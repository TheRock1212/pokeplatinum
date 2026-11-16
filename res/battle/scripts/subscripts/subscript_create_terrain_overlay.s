#include "macros/btlcmd.inc"

@ Expansion: written by hand (no terrain animations or backgrounds yet)
_000:
    GotoIfTerrainOverlayIsType GRASSY_TERRAIN, _grassy
    GotoIfTerrainOverlayIsType MISTY_TERRAIN, _misty
    GotoIfTerrainOverlayIsType ELECTRIC_TERRAIN, _electric
    GotoIfTerrainOverlayIsType PSYCHIC_TERRAIN, _psychic
    End

_grassy:
    // Grass grew to cover the battlefield!
    PrintMessage BattleStrings_Text_HgEngine1388, TAG_NONE
    GoTo _wait

_misty:
    // Mist swirled about the battlefield!
    PrintMessage BattleStrings_Text_HgEngine1390, TAG_NONE
    GoTo _wait

_electric:
    // An electric current ran across the battlefield!
    PrintMessage BattleStrings_Text_HgEngine1392, TAG_NONE
    GoTo _wait

_psychic:
    // The battlefield got weird!
    PrintMessage BattleStrings_Text_HgEngine1394, TAG_NONE

_wait:
    Wait
    WaitButtonABTime 30
    End
