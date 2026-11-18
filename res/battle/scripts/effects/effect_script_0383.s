@ BATTLE_EFFECT_LIFE_DEW: MOVE_LIFE_DEW
#include "macros/btlcmd.inc"

@ Expansion: written by hand from hg-engine LIFE_DEW, which only printed the attack message:
@ subscript_life_dew shows message and animation, like the vanilla stat moves.
_000:
    UpdateVarFromVar OPCODE_SET, BTLVAR_MSG_BATTLER_TEMP, BTLVAR_ATTACKER
    UpdateVar OPCODE_SET, BTLVAR_SIDE_EFFECT_FLAGS_DIRECT, MOVE_SIDE_EFFECT_TO_ATTACKER|MOVE_SUBSCRIPT_PTR_LIFE_DEW
    End
