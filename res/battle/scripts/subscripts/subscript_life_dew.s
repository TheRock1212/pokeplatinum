#include "macros/btlcmd.inc"

@ Expansion: written by hand from hg-engine LIFE_DEW. hg-engine passes BMON_DATA_MAXHP to
@ CompareMonDataToVar, which takes a script variable: copy the max HP to a variable first.
_000:
    UpdateMonDataFromVar OPCODE_GET, BTLSCR_MSG_BATTLER_TEMP, BATTLEMON_MAX_HP, BTLVAR_CALC_TEMP
    CompareMonDataToVar OPCODE_EQU, BTLSCR_MSG_BATTLER_TEMP, BATTLEMON_CUR_HP, BTLVAR_CALC_TEMP, _end
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    UpdateMonDataFromVar OPCODE_GET, BTLSCR_MSG_BATTLER_TEMP, BATTLEMON_MAX_HP, BTLVAR_HP_CALC_TEMP
    DivideVarByValueRoundUp BTLVAR_HP_CALC_TEMP, 4
    Call BATTLE_SUBSCRIPT_UPDATE_HP
    // {0} had its HP restored.
    PrintMessage BattleStrings_Text_HgEngine1396, TAG_NICKNAME, BTLSCR_MSG_BATTLER_TEMP, 0, 0, 0, 0, 0
    Wait
    WaitButtonABTime 30
_end:
    End
