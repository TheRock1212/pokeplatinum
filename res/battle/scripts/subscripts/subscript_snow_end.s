#include "macros/btlcmd.inc"

@ Expansion: written by hand (hg-engine's version also re-runs its switch-in ability check)
_000:
    UpdateVar OPCODE_FLAG_OFF, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_SNOW_TEMP
    // The snow stopped.
    PrintMessage BattleStrings_Text_HgEngine1440, TAG_NONE
    Wait
    WaitButtonABTime 30
    End
