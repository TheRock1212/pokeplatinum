#include "macros/btlcmd.inc"


@ Expansion: snowy maps start the battle with snow instead of hail (Gen 9)
_000:
    // there is no snow animation: reuse the hail one
    PlayBattleAnimation BTLSCR_PLAYER, BATTLE_ANIMATION_WEATHER_HAIL
    Wait 
    // It started to snow!
    PrintMessage BattleStrings_Text_HgEngine1439, TAG_NONE
    Wait 
    WaitButtonABTime 30
    UpdateVar OPCODE_FLAG_ON, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_SNOW_PERM
    End 
