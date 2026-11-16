#include "macros/btlcmd.inc"

@ Expansion: written by hand. Grassy Terrain heals BTLVAR_MSG_BATTLER_TEMP by BTLVAR_HP_CALC_TEMP
_000:
    PlayBattleAnimation BTLSCR_MSG_TEMP, BATTLE_ANIMATION_RESTORE_HP
    Wait
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    Call BATTLE_SUBSCRIPT_UPDATE_HP
    // {0} had its HP restored.
    PrintMessage BattleStrings_Text_HgEngine1396, TAG_NICKNAME, BTLSCR_MSG_TEMP
    Wait
    WaitButtonABTime 30
    End
