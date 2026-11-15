"""Lettura dei dati delle specie di hg-engine (sorgenti C e JSON)."""
import json, os, re

HG = os.environ.get("HG_ENGINE", os.path.expanduser("~/hg-engine"))


def _strip_comments(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)


def constants(path, prefix):
    """#define PREFIX_X <numero o espressione semplice> -> {nome: valore}"""
    out = {}
    text = _strip_comments(open(os.path.join(HG, path)).read())
    for name, expr in re.findall(r'#define\s+(' + prefix + r'\w+)\s+(.+)', text):
        expr = expr.strip()
        expr = re.sub(r'\b(' + prefix + r'\w+)\b', lambda m: str(out.get(m.group(1), m.group(1))), expr)
        try:
            out[name] = int(eval(expr, {}, {}))
        except Exception:
            pass
    return out


def entries(path):
    """[SPECIES_X] = { ... } -> {SPECIES_X: corpo}"""
    text = _strip_comments(open(os.path.join(HG, path)).read())
    out = {}
    for m in re.finditer(r'\[\s*(SPECIES_\w+)\s*\]\s*=\s*', text):
        i = m.end()
        if text[i] == '{':
            depth, j = 0, i
            while True:
                if text[j] == '{': depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0: break
                j += 1
            out[m.group(1)] = text[i + 1:j]
        else:
            j = text.index(',', i) if ',' in text[i:i + 200] else text.index('\n', i)
            out[m.group(1)] = text[i:j].strip()
    return out


def field(body, name, default=None):
    m = re.search(r'\.' + name + r'\s*=\s*("(?:[^"\\]|\\.)*"|\{[^{}]*\}|[^,\n]+)', body)
    if not m:
        return default
    v = m.group(1).strip()
    if v.startswith('"'):
        return v[1:-1]
    if v.startswith('{'):
        return [x.strip() for x in v[1:-1].split(',') if x.strip()]
    try:
        return int(v, 0)
    except ValueError:
        return v


def species_data():
    out = {}
    for sp, body in entries('data/Species.c').items():
        d = {}
        for k in ['name', 'pokedexEntry', 'classification']:
            d[k] = field(body, k)
        bs = re.search(r'\.baseStats\s*=\s*\{([^}]*)\}', body)
        d['baseStats'] = {k: field(bs.group(1), k) for k in ['hp', 'attack', 'defense', 'spAttack', 'spDefense', 'speed']} if bs else None
        ev = re.search(r'\.evYields\s*=\s*\{([^}]*)\}', body)
        d['evYields'] = {k: field(ev.group(1), k) for k in ['hp', 'attack', 'defense', 'spAttack', 'spDefense', 'speed']} if ev else None
        wh = re.search(r'\.wildHeldItems\s*=\s*\{([^}]*)\}', body)
        d['wildHeldItems'] = [field(wh.group(1), 'common'), field(wh.group(1), 'rare')] if wh else ['ITEM_NONE', 'ITEM_NONE']
        for k in ['types', 'eggGroups', 'abilities']:
            d[k] = field(body, k)
        for k in ['catchRate', 'genderRatio', 'hatchCycles', 'baseFriendship', 'expRate', 'safariFleeRate', 'bodyColor', 'flipSprite',
                  'heightDecimetres', 'weightHectograms', 'bodyType', 'femaleTrainerScale', 'femalePokemonScale', 'maleTrainerScale',
                  'malePokemonScale', 'femaleTrainerYOffset', 'femalePokemonYOffset', 'maleTrainerYOffset', 'malePokemonYOffset']:
            d[k] = field(body, k)
        out[sp] = d
    return out


def evolutions():
    out = {}
    for sp, body in entries('data/Evolutions.c').items():
        evos = []
        for method, param, target in re.findall(r'\{\s*(EVO_\w+)\s*,\s*([^,]+?)\s*,\s*(SPECIES_\w+)\s*\}', body):
            if method != 'EVO_NONE':
                evos.append((method, param.strip(), target))
        out[sp] = evos
    return out


def simple_table(path):
    return {k: v for k, v in entries(path).items()}


def sprite_offsets():
    out = {}
    for sp, body in entries('data/SpriteOffsets.c').items():
        d = {}
        for part in ['front', 'back']:
            h = re.search(r'\.' + part + r'Header\s*=\s*\{([^}]*)\}', body)
            d[part] = {k: field(h.group(1), k) for k in ['cryDelay', 'animation', 'animationDelay']} if h else None
            fr = re.search(r'\.' + part + r'Frames\s*=\s*\{(.*?)\}\s*,\s*\n', body, re.S)
            frames = re.findall(r'\.frameNo\s*=\s*(-?\d+)\s*,\s*\.duration\s*=\s*(-?\d+)\s*,\s*\.horizontalShift\s*=\s*(-?\d+)\s*,\s*\.verticalShift\s*=\s*(-?\d+)', body[body.index('.' + part + 'Frames'):] if '.' + part + 'Frames' in body else '')
            d[part + 'Frames'] = [tuple(map(int, f)) for f in frames[:10]]
        for k in ['spriteYOffset', 'shadowXOffset', 'shadowSize']:
            d[k] = field(body, k)
        out[sp] = d
    return out


def learnsets():
    return json.load(open(os.path.join(HG, 'data/learnsets/learnsets.json')))


def load_all():
    return {
        'species_ids': constants('include/constants/species.h', 'SPECIES_'),
        'move_ids': constants('include/constants/moves.h', 'MOVE_'),
        'ability_ids': constants('include/constants/ability.h', 'ABILITY_') or constants('include/constants/abilities.h', 'ABILITY_'),
        'item_ids': constants('include/constants/item.h', 'ITEM_'),
        'species': species_data(),
        'evolutions': evolutions(),
        'icon_palette': simple_table('data/IconPaletteTable.c'),
        'hidden_ability': simple_table('data/HiddenAbilityTable.c'),
        'base_exp': simple_table('data/BaseExperienceTable.c'),
        'height': simple_table('data/HeightTable.c'),
        'baby': simple_table('data/BabyMons.c'),
        'sprite_offsets': sprite_offsets(),
        'learnsets': learnsets(),
    }
