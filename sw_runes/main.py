from itertools import groupby, combinations, product, chain, combinations_with_replacement

import collections
import heapq
import os
import sys

data = {}
execfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "query.cfg"), data)

OPT_ATTRS = ["atk", "hp", "def", "spd", "rate", "dmg", "acc", "res"]

RUNE_BUILDS = {
    "despair" : (4, {}),
    "focus" : (2, {"acc": 20}),
    "energy" : (2, {"hp": 15}),
    "nemesis" : (2, {}),
    "blade" : (2, {"rate": 12}),
    "fatal" : (4, {"atk": 35}),
    "will" : (2, {}),
    "violent" : (4, {}),
    "guard" : (2, {"def": 20}),
    "endure" : (2, {"res": 20}),
    "vampire" : (4, {}),
    "destroy" : (2, {}),
    "swift" : (4, {"spd": 25}),
    "revenge" : (2, {}),
}

def get_build_total(rune_set):
    sums = collections.defaultdict(int)

    # counters for complete builds..
    req = collections.defaultdict(int)

    for r in rune_set:
        for a in OPT_ATTRS:
            sums[a] += r[a]
            rtype = r['type']
            build_num, add = RUNE_BUILDS[rtype]

            # Count complete builds powerups.
            if a in add:
                req[rtype] += 1
                if req[rtype] == build_num:
                    sums[a] += add[a]
                    req[rtype] = 0  # reset the counter
    return sums

def print_rune_set(rune_set):

    total = get_build_total(rune_set)

    print "POS\tTYPE\tATTR\t" + "\t".join(OPT_ATTRS)

    for r in sorted(rune_set, key=lambda x: x['pos']):
        print str(r['pos']) + ". \t" + r['type'] + "\t" + r['attr'] + "\t" + "\t".join((str(r[k]) for k in OPT_ATTRS))

    print "   \t    \tTOT\t" + "\t".join((str(total[k]) for k in OPT_ATTRS))


def _keyfunc(r):
    return r['type']

def score(rune_set, query):
    sums = get_build_total(rune_set)

    for k in OPT_ATTRS:
        sums[k] *= query['optimize'][k]

    score = sum(sums.itervalues())

    return score

def get_rune_sets(runes, query):
    types = query['types']
    attrs_reqs = query['attrs']

    print "GOT", len(runes), "RUNES TO CHECK"
    type_order = sorted(runes, key=_keyfunc)
    type_grp = groupby(type_order, _keyfunc)

    sort = {}
    for rtype, l in type_grp:
        _l = [k for k in l]
        f = lambda x: x['pos']
        #pos_order = sorted(_l, key=f)
        sort[rtype] = dict((k[0], [v for v in k[1]]) for k in groupby(_l, f))

    #print "Type -> [(position, #runes)]"
    #for rtype, rs in sort.iteritems():
    #    print ">>>", rtype, [(k, len(v)) for k, v in rs.iteritems()]

    # now we got our runes divided by type and then by position.. now
    # let's create sets..

    # Which sets can we combine?
    available_sets = set(r for r in sort)
    for sets in chain(combinations(available_sets, 2),
                      combinations_with_replacement(available_sets, 3)):
        # We need 6 runes, not more, not less!
        if sum(RUNE_BUILDS[rtype][0] for rtype in sets) != 6:
            continue

        # This set does not include the requested runes
        if types and any(k not in sets for k in types):
            continue

        print "GOING FOR SET:", sets

        #############

        all_combs = []
        _types = []
        for rtype in sets:
            positions = sort[rtype]
            build_num = RUNE_BUILDS[rtype][0]

            available_positions = set((p for p in positions))

            got = [g for g in combinations(available_positions, build_num)]

            all_combs.append(got)
            _types.append(rtype)

        valid_combs = []
        for k in product(*all_combs):
            if len(set(c for l in k for c in l)) == 6:
                valid_combs.append(k)

        for comb in valid_combs:
            combined_sets = []

            for idx, pos in enumerate(comb):
                rtype = _types[idx]
                positions = sort[rtype]
                pos_runes = [positions[p] for p in pos]
                combined_sets.extend(pos_runes)

            for k in product(*combined_sets):
                rune_set = sorted(k, key=lambda x: x['pos'])

                # Last check: does this runeset pass the rune main
                # attribute requirements?

                if not attrs_reqs or all(attrs_reqs[p] == rune_set[p - 1]['attr']
                                         for p in attrs_reqs):
                    yield rune_set

        #################
        # OLD SOLUTION< LESS EFFICIENT

        # gen = [_get_type_combinations(_set, sort[_set])
        #        for _set in sets]
        # c = 0
        # for k in product(*gen):
        #     rune_set = [r for t in k for r in t ]

        #     # Discard sets that have duplicate positions. This can be
        #     # improved by not processing the combination in the product
        #     positions = set((r['pos'] for r in rune_set))
        #     if len(positions) != 6:
        #         continue

        #     #print_rune_set(rune_set)
        #     c += 1
        #     yield rune_set

        #print ">> FOUND", c, "SOLUTIONS"


def maximize(runes, query):
    heap = []
    for rune_set in get_rune_sets(runes, query):
        _score = score(rune_set, query)
        heapq.heappush(heap, (1.0 / _score, rune_set))
        pass

    return heap

def _add_to_runes(_input, _type):

    for x in _input:
        x['type'] = _type

        for a in OPT_ATTRS:
            if a not in x: x[a] = 0

    return _input

def _process_query(_input):
    _opt = _input['optimize']

    res = {
        "optimize" : dict((k, _opt[k] if k in _opt else 0.0) for k in OPT_ATTRS),
        "types" : None if not _input['types'] else set(_input['types']),
        "attrs" : None if not _input['attrs'] else _input['attrs'],
    }

    return  res

runes = (_add_to_runes(data['energy'], "energy") +
         _add_to_runes(data['fatal'], "fatal") +
         _add_to_runes(data['blade'], "blade") +
         _add_to_runes(data['rage'], "rage") +
         _add_to_runes(data['will'], "will") +
         _add_to_runes(data['focus'], "focus") +
         _add_to_runes(data['violent'], "violent") +
         _add_to_runes(data['despair'], "despair") +
         _add_to_runes(data['guard'], "guard") +
         _add_to_runes(data['revenge'], "revenge") +
         _add_to_runes(data['endure'], "endure") +
         _add_to_runes(data['swift'], "swift") +
         _add_to_runes(data['vampire'], "vampire") +
         _add_to_runes(data['nemesis'], "nemesis") +
         _add_to_runes(data['destroy'], "destroy"))

query = _process_query(data['query'])

print "********************************************************************************"
print "** ALCUNE NOTE: "

print "** Aggiungete la main stat della runa!!!"
print "** Se avete una runa 6* di atk, mettete ad esempio il suo massimo (63%)"
print ""
print "** Le stats flat (non %) sono state volutamente ignorate "
print "** nella scrittura di questo algoritmo"
print ""
print "** Il bonus spd delle swift viene calcolato come 25 fisso, e non 25%. "
print "** Se swift, togliere 25 dal totale di spd ed aggiungere il 25% della spd del mob"

print "********************************************************************************"


print "QUERY:", query

heap = maximize(runes, query)

print "GOT", len(heap), "SOLUTIONS"

idx = 1
while heap:
    _score, rune_set = heapq.heappop(heap)
    print "#### [", idx, "-", 1.0 / _score, "] ################################################################"

    print_rune_set(rune_set)

    idx += 1

    if idx > int(sys.argv[1] if len(sys.argv) > 1 else 5):
        break
