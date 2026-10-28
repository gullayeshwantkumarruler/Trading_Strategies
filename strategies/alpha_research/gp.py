"""Genetic-programming alpha miner (the automated proposer).

Population of expression trees over the DSL; fitness = Referee.fitness (TRAIN months only: |IC t| minus depth and
redundancy penalties). After every generation the best not-yet-judged trees are submitted to the frozen Referee
(which alone looks at VALID). Mining data are truncated at 2021-12-31, so the sealed test cannot leak.
"""
from __future__ import annotations

import random

import dsl

GP_FIELDS = ["close", "ret", "volume", "dvol", "resid", "beta", "gpa", "asset_growth", "accruals", "issuance", "ey",
             "bm", "roe", "cfoa", "sue", "insider_opp", "lp_jac", "lp_cos", "wiki", "k8", "k8_502", "k8_202",
             "k8_101", "filing_delay"]


def rand_tree(rng: random.Random, d: int):
    if d <= 0 or rng.random() < 0.25:
        return rng.choice(GP_FIELDS)
    r = rng.random()
    if r < 0.40:
        return (rng.choice(dsl.TS), rand_tree(rng, d - 1), rng.choice(dsl.WINDOWS))
    if r < 0.60:
        return (rng.choice(dsl.UNARY), rand_tree(rng, d - 1))
    if r < 0.90:
        return (rng.choice(dsl.BINARY), rand_tree(rng, d - 1), rand_tree(rng, d - 1))
    return (rng.choice(dsl.TS2), rand_tree(rng, d - 1), rand_tree(rng, d - 1), rng.choice([21, 63, 126]))


def subtrees(e, path=()):
    yield path, e
    if isinstance(e, tuple):
        for i, a in enumerate(e[1:], start=1):
            if isinstance(a, (tuple, str)):
                yield from subtrees(a, path + (i,))


def replace(e, path, new):
    if not path:
        return new
    lst = list(e)
    lst[path[0]] = replace(e[path[0]], path[1:], new)
    return tuple(lst)


def crossover(rng, a, b):
    pa, _ = rng.choice(list(subtrees(a)))
    _, sb = rng.choice(list(subtrees(b)))
    return replace(a, pa, sb)


def mutate(rng, a):
    p, _ = rng.choice(list(subtrees(a)))
    return replace(a, p, rand_tree(rng, 2))


def run(ev: dsl.Evaluator, ref: dsl.Referee, pop_size=150, gens=20, seed=0, submit_per_gen=5, log=print):
    rng = random.Random(seed)
    pop = [rand_tree(rng, 3) for _ in range(pop_size)]
    cache: dict[str, float] = {}
    judged = set()

    def fit(e):
        k = dsl.to_str(e)
        if k not in cache:
            cache[k] = -9.0 if dsl.depth(e) > dsl.MAX_DEPTH or dsl.depth(e) == 0 else ref.fitness(e, ev)
        return cache[k]

    for g in range(gens):
        scored = sorted(((fit(e), e) for e in pop), key=lambda x: -x[0])
        sub = 0
        for f, e in scored:
            k = dsl.to_str(e)
            if k in judged or f < dsl.T_TRAIN - 0.6:
                continue
            judged.add(k)
            ref.judge(e, ev, source=f"gp(seed={seed},gen={g})")
            sub += 1
            if sub >= submit_per_gen:
                break
        n_adm = sum(r["source"].startswith("gp") for r in ref.admitted)
        log(f"  gen {g + 1}/{gens}: best fitness {scored[0][0]:.2f} {dsl.to_str(scored[0][1])[:90]} | admitted {n_adm}")
        elite = [e for _, e in scored[:10]]
        nxt = elite[:]
        while len(nxt) < pop_size:
            a = max(rng.sample(scored, 4), key=lambda x: x[0])[1]
            r = rng.random()
            if r < 0.6:
                b = max(rng.sample(scored, 4), key=lambda x: x[0])[1]
                c = crossover(rng, a, b)
            elif r < 0.9:
                c = mutate(rng, a)
            else:
                c = rand_tree(rng, 3)
            if dsl.depth(c) <= dsl.MAX_DEPTH:
                nxt.append(c)
        pop = nxt
    return cache
