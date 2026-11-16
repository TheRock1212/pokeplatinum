#include "macros/btlcmd.inc"

@ Expansion: written by hand (Grassy/Misty/Electric/Psychic Terrain)
_000:
    UpdateTerrainOverlay FALSE, _failed
    Call BATTLE_SUBSCRIPT_ATTACK_MESSAGE_AND_ANIMATION
    Call BATTLE_SUBSCRIPT_CREATE_TERRAIN_OVERLAY
    End

_failed:
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_FAILED
    End
