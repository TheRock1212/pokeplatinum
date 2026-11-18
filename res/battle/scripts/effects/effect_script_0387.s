#include "macros/btlcmd.inc"

@ Expansion: written by hand. BATTLE_EFFECT_END_TERRAIN: MOVE_STEEL_ROLLER, MOVE_ICE_SPINNER
@ Both remove the terrain after hitting; Steel Roller fails without a terrain.
_000:
    GotoIfTerrainOverlayIsType TERRAIN_NONE, _no_terrain
    GoTo _hit

_no_terrain:
    CompareVarToValue OPCODE_EQU, BTLVAR_CURRENT_MOVE, MOVE_STEEL_ROLLER, _failed

_hit:
    UpdateVar OPCODE_SET, BTLVAR_SIDE_EFFECT_FLAGS_INDIRECT, MOVE_SIDE_EFFECT_ON_HIT|MOVE_SUBSCRIPT_PTR_END_TERRAIN
    CalcCrit
    CalcDamage
    End

_failed:
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_FAILED
    End
