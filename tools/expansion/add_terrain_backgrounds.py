"""Aggiunge a res/prebuilt/battle/graphic/pl_batt_bg.narc gli sfondi di lotta dei terreni di hg-engine.

Platinum e HGSS usano lo stesso formato per gli sfondi di lotta (tile 8 bpp compressi LZ, palette da
256 colori, stessa mappa dei tile all'indice 2): i PNG di hg-engine (rawdata/battle_sprite/7_354..360)
si convertono con nitrogfx come fa il suo narcs.mk e si accodano dopo i 342 file vanilla:
  342 + 2 * (terrain - 1)      tile (NCGR, LZ)   terrain = GRASSY_TERRAIN, MISTY_TERRAIN, ...
  342 + 2 * (terrain - 1) + 1  palette (NCLR)
(vedi BATTLE_BG_NARC_TERRAIN_FIRST in include/battle/battle_system.h)
Rieseguibile: riparte sempre dai 342 file vanilla. Uso: python3 -I add_terrain_backgrounds.py
(dopo aver compilato almeno una volta, servono build/tools/nitroarc e build/tools/nitrogfx)
"""
import os, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(__file__))
import hg_parse

PP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NARC = f'{PP}/res/prebuilt/battle/graphic/pl_batt_bg.narc'
NITROARC = f'{PP}/build/tools/nitroarc/nitroarc'
NITROGFX = f'{PP}/build/tools/nitrogfx/nitrogfx'
VANILLA_FILES = 342

# ordine dei valori di BattleContext.terrain (GRASSY_TERRAIN = 1, ...) -> PNG di hg-engine
HG_PNGS = ['7_358.png', '7_356.png', '7_354.png', '7_360.png']  # grassy, misty, electric, psychic


def run(*args, cwd=None):
    subprocess.run(args, check=True, cwd=cwd, stdout=subprocess.DEVNULL)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(NARC, f'{tmp}/in.narc')
        run(NITROARC, '-xf', 'in.narc', cwd=tmp)
        files = f'{tmp}/in.narc.d'
        names = sorted(os.listdir(files))
        for name in names[VANILLA_FILES:]:
            os.remove(f'{files}/{name}')

        n = VANILLA_FILES
        for png in HG_PNGS:
            src = f'{hg_parse.HG}/rawdata/battle_sprite/{png}'
            run(NITROGFX, src, f'{tmp}/tiles.NCGR', '-bitdepth', '8')
            # l'estensione .lz dice a nitrogfx di comprimere: rinomina dopo
            run(NITROGFX, f'{tmp}/tiles.NCGR', f'{tmp}/tiles.NCGR.lz')
            shutil.move(f'{tmp}/tiles.NCGR.lz', f'{files}/{n:05d}.NCGR')
            run(NITROGFX, src, f'{files}/{n + 1:05d}.NCLR', '-bitdepth', '8')
            n += 2

        run(NITROARC, '-cf', 'out.narc', 'in.narc.d', cwd=tmp)
        shutil.copy(f'{tmp}/out.narc', NARC)
    print(f'pl_batt_bg.narc: {VANILLA_FILES} file vanilla + {n - VANILLA_FILES} dei terreni')


main()
