# util.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

def as_dec(x):
    return float(x.strip().replace('%', '').replace(',', '.'))

def is_number(x):
    try:
        as_dec(x)
    except ValueError:
        return False
    return True

def merge(ret):
    return {k: v for d in ret for k, v in d.items()}

def generate_pairs(texts):
    pairs = []
    for _, v in texts.items():
        v = [x for x in v if x]
        if len(v) < 2:
            continue

        it = iter(v)
        groups = zip(it, it)
        groups = [sorted(x) for x in groups]
        groups = [x for x in groups if not is_number(x[1])]

        candidates = [x[1] for x in groups]
        numbers = [as_dec(x[0]) for x in groups]
        
        if len(candidates) != len(numbers):
            raise Exception('evil!')
        
        pairs.append(dict(zip(candidates, numbers)))

    return merge(pairs)
