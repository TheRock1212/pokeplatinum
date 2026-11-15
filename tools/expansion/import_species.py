"""Importa in pokeplatinum le specie 494..1025 da hg-engine (dati) con sprite di hg-engine o, se mancano, del Gen 9 Pack.

Rieseguibile: rigenera le cartelle delle specie nuove e l'elenco in generated/species.txt; filtra mosse, abilità,
strumenti ed evoluzioni su ciò che esiste in pokeplatinum in quel momento.
Uso: python3 -I import_species.py [--only NOME,...]
"""
import collections, hashlib, json, os, pickle, re, shutil, sys

sys.path.insert(0, os.path.dirname(__file__))
import hg_parse, pngpix, sprite_convert

PP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HG = os.environ.get("HG_ENGINE", os.path.expanduser("~/hg-engine"))
PACK = os.environ.get("GEN9_PACK", "/mnt/d/Pokemon/Generation 9 Pack v3.3.6") + "/Graphics/Pokemon"
LAST_NAT = 1025
HG_OFFSET = 50                       # in hg-engine le specie dopo la 493 hanno indice = nazionale + 50
KEY = bytes.fromhex('8064be03')      # seme di cifratura degli sprite (qualsiasi valore va bene)

log = collections.defaultdict(list)


def lines(path):
    return open(os.path.join(PP, path)).read().split()


# ---------- nomi validi in pokeplatinum ----------
PT_MOVES = lines('generated/moves.txt')           # indice = ID
PT_ABILITIES = lines('generated/abilities.txt')
PT_ITEMS = lines('generated/items.txt')
PT_MOVE_SET, PT_ABIL_SET, PT_ITEM_SET = set(PT_MOVES), set(PT_ABILITIES), set(PT_ITEMS)
TM_OF_MOVE = {}
for f in sorted(os.listdir(os.path.join(PP, 'res/items/data'))):
    m = re.fullmatch(r'(tm|hm)(\d+)\.json', f)
    if m:
        mv = json.load(open(os.path.join(PP, 'res/items/data', f)))['teachesMove']
        TM_OF_MOVE[mv] = f'{m.group(1).upper()}{int(m.group(2)):02d}'
TUTOR_MOVES = set(re.findall(r'"(MOVE_\w+)"', open(os.path.join(PP, 'res/pokemon/move_tutors.json')).read()))
SHAPES = {'QUADRUPED': 'SHAPE_QUADRUPED', 'BIPEDAL_TAILLESS': 'SHAPE_BIPEDAL_TAILLESS', 'BIPEDAL_TAIL': 'SHAPE_BIPEDAL_TAILED',
          'SERPENTINE': 'SHAPE_SERPENTINE', 'MULTIWING': 'SHAPE_MULTI_WINGED', 'BIWING': 'SHAPE_WINGED', 'INSECTOID': 'SHAPE_INSECTOID',
          'HEAD_TORSO': 'SHAPE_HEAD_BASE', 'HEAD_ARMS': 'SHAPE_HEAD_ARMS', 'HEAD_LEGS': 'SHAPE_HEAD_LEGS', 'TENTACLES': 'SHAPE_TENTACLES',
          'FINS': 'SHAPE_FINS', 'HEAD_ONLY': 'SHAPE_HEAD', 'MULTIBODY': 'SHAPE_MULTI_BODY'}
GENDER = {0: 'GENDER_RATIO_MALE_ONLY', 31: 'GENDER_RATIO_FEMALE_12_5', 63: 'GENDER_RATIO_FEMALE_25', 127: 'GENDER_RATIO_FEMALE_50',
          191: 'GENDER_RATIO_FEMALE_75', 223: 'GENDER_RATIO_FEMALE_87_5', 254: 'GENDER_RATIO_FEMALE_ONLY', 255: 'GENDER_RATIO_NO_GENDER'}
SHADOWS = ['SHADOW_SIZE_NONE', 'SHADOW_SIZE_SMALL', 'SHADOW_SIZE_MEDIUM', 'SHADOW_SIZE_LARGE']
LANGS = ['en', 'fr', 'de', 'it', 'es', 'jp']

# ---------- dati hg-engine ----------
H = hg_parse.load_all()
HG_MOVE_BY_ID = {v: k for k, v in H['move_ids'].items()}
HG_ABIL_BY_ID = {v: k for k, v in H['ability_ids'].items()}
HG_ITEM_BY_ID = {v: k for k, v in H['item_ids'].items()}
HG_SPECIES_BY_ID = {v: k for k, v in H['species_ids'].items() if not k.startswith('SPECIES_MEGA') and v <= LAST_NAT + HG_OFFSET}


def hg_index(nat):
    return nat if nat <= 493 else nat + HG_OFFSET


def nat_of(hg_species):
    v = H['species_ids'].get(hg_species)
    if v is None:
        return None
    if v <= 493:
        return v
    if 494 + HG_OFFSET <= v <= LAST_NAT + HG_OFFSET:
        return v - HG_OFFSET
    return None


def pt_move(hg_name):
    """Mossa hg-engine -> nome pokeplatinum, tramite l'ID (uguale fino alla 467), o None."""
    v = H['move_ids'].get(hg_name)
    if v is not None and v < len(PT_MOVES) and v > 0:
        return PT_MOVES[v]
    return hg_name if hg_name in PT_MOVE_SET else None


def pt_ability(hg_name):
    v = H['ability_ids'].get(hg_name)
    if v is not None and 0 < v < len(PT_ABILITIES) - 1:
        return PT_ABILITIES[v]
    return hg_name if hg_name in PT_ABIL_SET else None


def pt_item(hg_name):
    """Strumento hg-engine -> nome pokeplatinum: stesso ID e stesso nome a meno dei trattini bassi."""
    if hg_name in (None, 'ITEM_NONE'):
        return 'ITEM_NONE'
    if hg_name in PT_ITEM_SET:
        return hg_name
    v = H['item_ids'].get(hg_name)
    if v is not None and 0 < v < len(PT_ITEMS) and PT_ITEMS[v].replace('_', '') == hg_name.replace('_', ''):
        return PT_ITEMS[v]
    return None


def pt_move_type(move):
    p = os.path.join(PP, 'res/moves', move[len('MOVE_'):].lower(), 'data.json')
    return json.load(open(p))['type'] if os.path.exists(p) else None


def hg_int(param):
    """Parametro numerico di hg-engine, anche se scritto come costante (es. SPECIES_NIDORAN_M = 32)."""
    try:
        return int(param, 0)
    except ValueError:
        for table in ('species_ids', 'move_ids', 'item_ids', 'ability_ids'):
            if param in H[table]:
                return H[table][param]
    return None


LEVEL_METHODS = {'EVO_LEVEL_DAY', 'EVO_LEVEL_NIGHT', 'EVO_LEVEL_DUSK', 'EVO_LEVEL_RAIN', 'EVO_LEVEL_DARK_TYPE_MON_IN_PARTY',
                 'EVO_LEVEL_NATURE_AMPED', 'EVO_LEVEL_NATURE_LOW_KEY'}


def prevo_level(sp):
    """Livello a cui la specie si evolve dallo stadio precedente (per stimare quello successivo)."""
    for pre, evos in H['evolutions'].items():
        for method, param, target in evos:
            if target == sp and method in ({'EVO_LEVEL'} | LEVEL_METHODS):
                v = hg_int(param)
                if v and v <= 100:
                    return v
    return None


def fallback_level(sp):
    lvl = prevo_level(sp)
    return min(lvl + 10, 100) if lvl else 30


def folder(species):
    return species[len('SPECIES_'):].lower()


# ---------- elenco delle specie ----------
def species_list():
    out = []
    for nat in range(494, LAST_NAT + 1):
        sp = HG_SPECIES_BY_ID.get(hg_index(nat))
        if sp is None:
            raise SystemExit(f'nessuna specie hg-engine per il nazionale {nat}')
        out.append((nat, sp))
    return out


# ---------- dati ----------
def convert_evolutions(sp, evos):
    out = []
    for method, param, target in evos:
        tnat = nat_of(target)
        if tnat is None or tnat > LAST_NAT:
            log['evo_target_skipped'].append(f'{sp}->{target}')
            continue
        try:
            p = int(param, 0)
        except ValueError:
            p = param
        if p == 'ITEM_LINKING_CORD':
            method = 'EVO_TRADE'           # il Cavo Link sostituisce lo scambio delle generazioni successive
        if method in LEVEL_METHODS:
            lvl = hg_int(param)
            lvl = lvl if lvl and 1 <= lvl <= 100 else fallback_level(sp)
            out.append(['EVO_LEVEL', lvl, target])
            log['evo_level_variant'].append(f'{sp}->{target} {method}({param}) -> livello {lvl}')
            continue
        if method == 'EVO_HAS_MOVE_TYPE':
            ls = H['learnsets'].get(sp, {})
            cands = [pt_move(e['Move']) for e in ls.get('LevelMoves', [])] + [pt_move(m) for m in ls.get('EggMoves', [])]
            cands = [m for m in cands if m and pt_move_type(m) == param]
            if cands:
                out.append(['EVO_LEVEL_KNOW_MOVE', cands[0], target])
                log['evo_move_type'].append(f'{sp}->{target} {param} -> conosce {cands[0]}')
                continue
        if method in ('EVO_FRIENDSHIP', 'EVO_FRIENDSHIP_DAY', 'EVO_FRIENDSHIP_NIGHT', 'EVO_TRADE', 'EVO_MAGNETIC_FIELD', 'EVO_MOSSY_ROCK', 'EVO_ICY_ROCK'):
            pt = {'EVO_FRIENDSHIP': 'EVO_LEVEL_HAPPINESS', 'EVO_FRIENDSHIP_DAY': 'EVO_LEVEL_HAPPINESS_DAY', 'EVO_FRIENDSHIP_NIGHT': 'EVO_LEVEL_HAPPINESS_NIGHT',
                  'EVO_TRADE': 'EVO_TRADE', 'EVO_MAGNETIC_FIELD': 'EVO_LEVEL_MAGNETIC_FIELD', 'EVO_MOSSY_ROCK': 'EVO_LEVEL_MOSS_ROCK', 'EVO_ICY_ROCK': 'EVO_LEVEL_ICE_ROCK'}[method]
            out.append([pt, target])
        elif method in ('EVO_LEVEL', 'EVO_LEVEL_ATK_GT_DEF', 'EVO_LEVEL_ATK_EQ_DEF', 'EVO_LEVEL_ATK_LT_DEF', 'EVO_LEVEL_PID_LO', 'EVO_LEVEL_PID_HI',
                        'EVO_LEVEL_NINJASK', 'EVO_LEVEL_SHEDINJA', 'EVO_BEAUTY', 'EVO_LEVEL_MALE', 'EVO_LEVEL_FEMALE'):
            pt = {'EVO_LEVEL_PID_LO': 'EVO_LEVEL_PID_LOW', 'EVO_LEVEL_PID_HI': 'EVO_LEVEL_PID_HIGH', 'EVO_BEAUTY': 'EVO_LEVEL_BEAUTY'}.get(method, method)
            out.append([pt, p, target])
        elif method in ('EVO_TRADE_ITEM', 'EVO_STONE', 'EVO_STONE_MALE', 'EVO_STONE_FEMALE', 'EVO_ITEM_DAY', 'EVO_ITEM_NIGHT'):
            pt = {'EVO_TRADE_ITEM': 'EVO_TRADE_WITH_HELD_ITEM', 'EVO_STONE': 'EVO_USE_ITEM', 'EVO_STONE_MALE': 'EVO_USE_ITEM_MALE',
                  'EVO_STONE_FEMALE': 'EVO_USE_ITEM_FEMALE', 'EVO_ITEM_DAY': 'EVO_LEVEL_WITH_HELD_ITEM_DAY', 'EVO_ITEM_NIGHT': 'EVO_LEVEL_WITH_HELD_ITEM_NIGHT'}[method]
            item = pt_item(p if isinstance(p, str) else HG_ITEM_BY_ID.get(p))
            if item and item != 'ITEM_NONE':
                out.append([pt, item, target])
            else:
                lvl = fallback_level(sp)
                out.append(['EVO_LEVEL', lvl, target])
                log['evo_item_to_level'].append(f'{sp}->{target} ({p}) -> livello {lvl}')
        elif method == 'EVO_HAS_MOVE':
            mv = pt_move(p if isinstance(p, str) else HG_MOVE_BY_ID.get(p))
            if mv:
                out.append(['EVO_LEVEL_KNOW_MOVE', mv, target])
            else:
                lvl = fallback_level(sp)
                out.append(['EVO_LEVEL', lvl, target])
                log['evo_move_to_level'].append(f'{sp}->{target} ({p}) -> livello {lvl}')
        elif method == 'EVO_OTHER_PARTY_MON':
            other = p if isinstance(p, str) else HG_SPECIES_BY_ID.get(p)
            if other and nat_of(other):
                out.append(['EVO_LEVEL_SPECIES_IN_PARTY', other, target])
        elif method == 'EVO_TRADE_SPECIFIC_MON':
            out.append(['EVO_TRADE', target])
        elif method == 'EVO_DUMMY':
            log['evo_dummy_skipped'].append(f'{sp}->{target}')
        else:
            lvl = fallback_level(sp)
            out.append(['EVO_LEVEL', lvl, target])
            log['evo_new_method_to_level'].append(f'{sp}->{target} {method}({param}) -> livello {lvl}')
    return out[:8]


def convert_learnset(sp):
    ls = H['learnsets'].get(sp, {})
    by_level = []
    for e in ls.get('LevelMoves', []):
        mv = pt_move(e['Move'])
        if mv:
            by_level.append([e['Level'], mv])
        else:
            log['level_moves_missing'].append(e['Move'])
    by_level.sort(key=lambda e: e[0])
    if len(by_level) > 20:
        later = [e for e in by_level if e[0] > 1]
        lvl1 = [e for e in by_level if e[0] <= 1]
        by_level = (lvl1[:max(0, 20 - len(later))] + later)[-20:]
    if not by_level:
        by_level = [[1, 'MOVE_TACKLE']]
        log['no_level_moves'].append(sp)
    teach = set(ls.get('MachineMoves', [])) | set(ls.get('TutorMoves', []))
    pt_teach = {pt_move(m) for m in teach} - {None}
    by_tm = sorted({TM_OF_MOVE[m] for m in pt_teach if m in TM_OF_MOVE}, key=lambda s: (s[:2] == 'HM', s))
    by_tutor = sorted(m for m in pt_teach if m in TUTOR_MOVES)
    egg = []
    for m in ls.get('EggMoves', []):
        mv = pt_move(m)
        if mv and mv not in egg:
            egg.append(mv)
    return {'by_level': by_level, 'by_tm': by_tm, 'by_tutor': by_tutor, 'egg_moves': egg[:16]}


def convert_abilities(sp, d):
    want = [a for a in d['abilities'] if a != 'ABILITY_NONE']
    have = [pt_ability(a) for a in want]
    out = [a for a in have if a]
    if not out:
        hidden = pt_ability(H['hidden_ability'].get(sp, 'ABILITY_NONE').strip())
        if hidden:
            out = [hidden]
            log['ability_from_hidden'].append(f'{sp}: {want} -> {hidden}')
        else:
            log['ability_none'].append(f'{sp}: {want}')
    elif len(out) < len(want):
        log['ability_partial'].append(f'{sp}: {want} -> {out}')
    out = (out + ['ABILITY_NONE', 'ABILITY_NONE'])[:2]
    if out[1] == out[0]:
        out[1] = 'ABILITY_NONE'
    return out


CHARMAP = set()
for _l in open(os.path.join(PP, 'build/tools/msgenc/charmap.txt'), encoding='utf-8'):
    if '=' in _l:
        CHARMAP.add(_l.rstrip('\n').split('=', 1)[1])


def clean(text, where):
    """Converte ASCII ' e " nei caratteri del gioco e segnala quelli che la tabella non conosce."""
    text = text.replace("'", '’').replace('—', '-').replace('–', '-')
    out, quote = [], False
    for ch in text:
        if ch == '"':
            ch = '”' if quote else '“'
            quote = not quote
        if ch not in CHARMAP and ch != '\n':
            log['char_replaced'].append(f'{where}: {ch!r}')
            ch = '?'
        out.append(ch)
    return ''.join(out)


def dex_text(d, name, sp):
    parts = [clean(p, sp) for p in re.split(r'\\+n', d['pokedexEntry'] or '')]
    text = [p + '\n' for p in parts[:-1]] + [parts[-1]]
    cat = clean(d['classification'] or 'Unknown Pokémon', sp)
    return {lang: {'name': name, 'category': cat, 'entry_text': text} for lang in LANGS}


def mon_name(sp, d):
    name = clean((d['name'] or folder(sp)).upper(), sp)
    if len(name) > 10:
        log['name_truncated'].append(f'{name} -> {name[:10]}')
        name = name[:10]
    return name


def build_data(nat, sp):
    d = H['species'][sp]
    name = mon_name(sp, d)
    abilities = convert_abilities(sp, d)
    held = []
    for it in d['wildHeldItems']:
        p = pt_item(it)
        if p is None:
            log['held_item_missing'].append(f'{sp}: {it}')
            p = 'ITEM_NONE'
        held.append(p)
    base_exp = int(str(H['base_exp'].get(sp, '64')).strip())
    baby = H['baby'].get(sp, sp).strip()
    if nat_of(baby) is None:
        baby = sp
    ev = d['evYields']
    bs = d['baseStats']
    metrics = {'height_inches': round(d['heightDecimetres'] * 3.937), 'weight_pounds': round(d['weightHectograms'] * 0.220462, 1),
               'body_shape': SHAPES[d['bodyType'].replace('DEX_SEARCH_BODYTYPE_', '')],
               'trainer_scale_f': d['femaleTrainerScale'], 'pokemon_scale_f': d['femalePokemonScale'],
               'trainer_scale_m': d['maleTrainerScale'], 'pokemon_scale_m': d['malePokemonScale'],
               'trainer_pos_f': d['femaleTrainerYOffset'] & 0xFFFF, 'pokemon_pos_f': d['femalePokemonYOffset'] & 0xFFFF,
               'trainer_pos_m': d['maleTrainerYOffset'] & 0xFFFF, 'pokemon_pos_m': d['malePokemonYOffset'] & 0xFFFF}
    metrics.update(dex_text(d, name, sp))
    return {
        'base_stats': {'hp': bs['hp'], 'attack': bs['attack'], 'defense': bs['defense'], 'speed': bs['speed'],
                       'special_attack': bs['spAttack'], 'special_defense': bs['spDefense']},
        'types': d['types'],
        'catch_rate': d['catchRate'],
        'base_exp_reward': min(base_exp, 255),
        'ev_yields': {'hp': ev['hp'], 'attack': ev['attack'], 'defense': ev['defense'], 'speed': ev['speed'],
                      'special_attack': ev['spAttack'], 'special_defense': ev['spDefense']},
        'held_items': {'common': held[0], 'rare': held[1]},
        'gender_ratio': GENDER[min(GENDER, key=lambda k: abs(k - d['genderRatio']))],
        'hatch_cycles': d['hatchCycles'],
        'base_friendship': d['baseFriendship'],
        'exp_rate': d['expRate'].replace('GROWTH_', 'EXP_RATE_'),
        'egg_groups': d['eggGroups'],
        'abilities': abilities,
        'safari_flee_rate': d['safariFleeRate'],
        'body_color': d['bodyColor'].replace('BODY_COLOR_', 'MON_COLOR_'),
        'flip_sprite': bool(d['flipSprite']),
        'icon_palette': int(str(H['icon_palette'].get(sp, '0')).strip()),
        'learnset': convert_learnset(sp),
        'evolutions': convert_evolutions(sp, H['evolutions'].get(sp, [])),
        'offspring': baby,
        'footprint': {'has': False, 'size': 'FOOTPRINT_SMALL', 'type': 'FOOTPRINT_TYPE_CUTE'},
        'pokedex_data': metrics,
        'catching_show': {'pal_park_land_area': 'PAL_PARK_AREA_LAND_NONE', 'pal_park_water_area': 'PAL_PARK_AREA_WATER_NONE',
                          'catching_points': 0, 'rarity': 0, 'unused': 0},
    }


def build_sprite_data(sp):
    o = H['sprite_offsets'][sp]
    ht = [int(x) for x in H['height'][sp].strip('{} ').split(',')]
    def frames(fr):
        fr = list(fr) + [(-1, 0, 0, 0)] * (10 - len(fr))
        return [{'sprite_frame': a, 'frame_delay': b, 'x_shift': c, 'y_shift': d} for a, b, c, d in fr[:10]]
    z = lambda v: 0 if v == -1 else v
    return {
        'front': {'y_offset': {'female': z(ht[2]), 'male': z(ht[3])}, 'addl_y_offset': o['spriteYOffset'],
                  'animation': o['front']['animation'], 'cry_delay': o['front']['cryDelay'], 'start_delay': o['front']['animationDelay'],
                  'frames': frames(o['frontFrames'])},
        'back': {'y_offset': {'female': z(ht[0]), 'male': z(ht[1])}, 'animation': o['back']['animation'],
                 'cry_delay': o['back']['cryDelay'], 'start_delay': o['back']['animationDelay'], 'frames': frames(o['backFrames'])},
        'shadow': {'x_offset': o['shadowXOffset'], 'size': SHADOWS[o['shadowSize']]},
    }


# ---------- sprite ----------
def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else None


def placeholder_md5s(species):
    seen = collections.defaultdict(set)
    for _, sp in species:
        h = md5(os.path.join(HG, 'data/graphics/sprites', folder(sp), 'male/front.png'))
        if h:
            seen[h].add(sp)
    bad = {h for h, s in seen.items() if len(s) > 1}
    bad.add(hashlib.md5(b'').hexdigest())
    return bad


def icon_palettes():
    lines_ = open(os.path.join(PP, 'res/pokemon/.shared/pl_poke_icon.pal')).read().split('\n')[3:]
    cols = [tuple(int(v) for v in l.split()) for l in lines_ if l.strip()]
    return [cols[p * 16:(p + 1) * 16] for p in range(3)]


ICON_PALS = icon_palettes()


def plte(path):
    return pngpix.read(path)[4]


def with_plte(src, dst, colors):
    w, h, bd, rows, _ = pngpix.read(src)
    pngpix.write(dst, w, h, rows, colors[:16] + [(0, 0, 0)] * (16 - len(colors[:16])), bd=4)


def write_pal(path, colors):
    sprite_convert.write_pal(path, colors[:16])


def pack_name(sp):
    return folder(sp).replace('_', '').upper()


def sprites(nat, sp, out, bad):
    src = os.path.join(HG, 'data/graphics/sprites', folder(sp))
    valid = lambda p: os.path.exists(p) and md5(p) not in bad
    mf, ff = os.path.join(src, 'male/front.png'), os.path.join(src, 'female/front.png')
    genders = []
    if valid(mf):
        genders.append('male')
    if valid(ff) and md5(ff) != md5(mf):
        genders.append('female')
    if genders:
        main = genders[0]
        normal = plte(os.path.join(src, main, 'front.png'))
        shiny = plte(os.path.join(src, main, 'back.png'))
        for g in genders:
            shutil.copy(os.path.join(src, g, 'front.png'), os.path.join(out, f'{g}_front.png'))
            with_plte(os.path.join(src, g, 'back.png'), os.path.join(out, f'{g}_back.png'), normal)
        source = 'hg-engine'
    else:
        n = pack_name(sp)
        paths = [os.path.join(PACK, d, n + '.png') for d in ['Front', 'Back', 'Front shiny', 'Back shiny']]
        missing = [p for p in paths if not os.path.exists(p)]
        if missing:
            raise SystemExit(f'{sp}: sprite mancanti anche nel Gen 9 Pack: {missing}')
        normal, shiny, fi, bi = sprite_convert.convert_mon(*paths)
        g = 'female' if H['species'][sp]['genderRatio'] == 254 else 'male'
        sprite_convert.write_sprite(os.path.join(out, f'{g}_front.png'), fi, normal)
        sprite_convert.write_sprite(os.path.join(out, f'{g}_back.png'), bi, normal)
        genders = [g]
        source = 'Gen 9 Pack'
        log['sprites_from_pack'].append(sp)
    # Il gioco sceglie lo sprite in base al sesso: ogni sesso possibile deve avere i suoi file
    # (come in vanilla, dove le specie senza differenze hanno i file femminili uguali ai maschili).
    ratio = H['species'][sp]['genderRatio']
    needed = [g for g, ok in [('female', ratio not in (0, 255)), ('male', ratio != 254)] if ok]
    for g in needed:
        if g not in genders:
            other = genders[0]
            for face in ['front', 'back']:
                shutil.copy(os.path.join(out, f'{other}_{face}.png'), os.path.join(out, f'{g}_{face}.png'))
    present = [g for g in ['female', 'male'] if g in needed or g in genders]
    files = [f'{g}_back.png' for g in present] + [f'{g}_front.png' for g in present]
    write_pal(os.path.join(out, 'normal.pal'), normal)
    write_pal(os.path.join(out, 'shiny.pal'), shiny)
    for f in files:
        open(os.path.join(out, f + '.key'), 'wb').write(KEY)
    # icona
    icon = os.path.join(src, 'icon.png')
    icon_pal = None
    if os.path.exists(icon) and md5(icon) not in bad_icons:
        pal_idx = int(str(H['icon_palette'].get(sp, '0')).strip())
        with_plte(icon, os.path.join(out, 'icon.png'), ICON_PALS[pal_idx])
    else:
        n = pack_name(sp)
        p = os.path.join(PACK, 'Icons', n + '.png')
        if not os.path.exists(p):
            raise SystemExit(f'{sp}: icona mancante')
        icon_pal, rows = sprite_convert.convert_icon(p, ICON_PALS)
        pngpix.write(os.path.join(out, 'icon.png'), 32, 64, rows, ICON_PALS[icon_pal], bd=4)
        log['icons_from_pack'].append(sp)
    return files, source, icon_pal


def meson(files):
    s = "species_data_files += files('data.json', 'sprite_data.json')\n\npoke_icon_files += files('icon.png')\n\n"
    s += ''.join(f"pokegra_files += files('{f}')\n" for f in files)
    s += "\npokefoot_files += files('footprint.png')\n"
    return s


def main():
    only = None
    if '--only' in sys.argv:
        only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
    species = species_list()
    bad = placeholder_md5s(species)
    global bad_icons
    seen = collections.defaultdict(set)
    for _, sp in species:
        h = md5(os.path.join(HG, 'data/graphics/sprites', folder(sp), 'icon.png'))
        if h:
            seen[h].add(sp)
    bad_icons = {h for h, s in seen.items() if len(s) > 1}

    template = os.path.join(PP, 'res/pokemon/celebi')
    fw, fh, fbd, _, fpal = pngpix.read(os.path.join(template, 'footprint.png'))
    for nat, sp in species:
        if only and folder(sp) not in only:
            continue
        out = os.path.join(PP, 'res/pokemon', folder(sp))
        if os.path.exists(out):
            shutil.rmtree(out)
        os.makedirs(out)
        data = build_data(nat, sp)
        files, source, icon_pal = sprites(nat, sp, out, bad)
        if icon_pal is not None:
            data['icon_palette'] = icon_pal
        json.dump(data, open(os.path.join(out, 'data.json'), 'w'), indent=4, ensure_ascii=False)
        json.dump(build_sprite_data(sp), open(os.path.join(out, 'sprite_data.json'), 'w'), indent=4)
        pngpix.write(os.path.join(out, 'footprint.png'), fw, fh, [[0] * fw for _ in range(fh)], fpal, bd=fbd)
        for f in ['cry.txt', 'cry.wav']:
            shutil.copy(os.path.join(template, f), os.path.join(out, f))
        open(os.path.join(out, 'meson.build'), 'w').write(meson(files))

    # elenco specie: vanilla 1..493, nuove, poi Uovo e Uovo Strano
    names = lines('generated/species.txt')
    head = names[:names.index('SPECIES_ARCEUS') + 1]
    new = [sp for _, sp in species]
    open(os.path.join(PP, 'generated/species.txt'), 'w').write('\n'.join(head + new + ['SPECIES_EGG', 'SPECIES_BAD_EGG']) + '\n')

    # evoluzioni delle specie vanilla verso le nuove
    for nat in range(1, 494):
        sp = names[nat]
        add = [e for e in convert_evolutions(sp, H['evolutions'].get(sp, [])) if (nat_of(e[-1]) or 0) > 493]
        p = os.path.join(PP, 'res/pokemon', folder(sp), 'data.json')
        text = open(p).read()
        d = json.loads(text)
        old = [e for e in d['evolutions'] if (nat_of(e[-1]) or 0) <= 493]
        if old + add == d['evolutions']:
            continue
        d['evolutions'] = old + add
        if len(d['evolutions']) > 8:
            log['vanilla_evo_over_limit'].append(f'{sp}: {[e[-1] for e in d["evolutions"]]}')
        start = text.index('    "evolutions": [')
        i, depth = text.index('[', start), 0
        while True:
            if text[i] == '[': depth += 1
            elif text[i] == ']':
                depth -= 1
                if depth == 0: break
            i += 1
        end = text.index('\n', i) + 1
        rendered = '    "evolutions": [\n' + ',\n'.join('        ' + json.dumps(e, ensure_ascii=False).replace('[', '[ ').replace(']', ' ]') for e in d['evolutions']) + '\n    ],\n'
        open(p, 'w').write(text[:start] + rendered + text[end:])
        log['vanilla_evo_added'].append(f'{sp}: +{[e[-1] for e in add]}')

    report = {k: (sorted(set(v)) if k == 'level_moves_missing' else v) for k, v in log.items()}
    json.dump(report, open(os.path.join(PP, "build", "import_species_log.json"), 'w'), indent=1, ensure_ascii=False)
    for k, v in report.items():
        print(f'{k}: {len(v)}')


if __name__ == '__main__':
    main()
