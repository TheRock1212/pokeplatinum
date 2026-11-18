#include "macros/btlcmd.inc"

@ Expansion: written by hand from hg-engine LIFE_DEW. hg-engine passes BMON_DATA_MAXHP to
@ CompareMonDataToVar, which takes a script variable: copy the max HP to a variable first.
@ Message and animation are here (the effect script only sets this subscript); full HP: the move fails.
_000:
    UpdateMonDataFromVar OPCODE_GET, BTLSCR_MSG_BATTLER_TEMP, BATTLEMON_MAX_HP, BTLVAR_CALC_TEMP
    CompareMonDataToVar OPCODE_EQU, BTLSCR_MSG_BATTLER_TEMP, BATTLEMON_CUR_HP, BTLVAR_CALC_TEMP, _failed
    Call BATTLE_SUBSCRIPT_ATTACK_MESSAGE_AND_ANIMATION
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    UpdateMonDataFromVar OPCODE_GET, BTLSCR_MSG_BATTLER_TEMP, BATTLEMON_MAX_HP, BTLVAR_HP_CALC_TEMP
    DivideVarByValueRoundUp BTLVAR_HP_CALC_TEMP, 4
    Call BATTLE_SUBSCRIPT_UPDATE_HP
    // {0} had its HP restored.
    PrintMessage BattleStrings_Text_HgEngine1396, TAG_NICKNAME, BTLSCR_MSG_BATTLER_TEMP, 0, 0, 0, 0, 0
    Wait
    WaitButtonABTime 30
    End

_failed:
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_FAILED
    End
