#!/usr/bin/env python3
"""Turns an unzipped atlas bundle into the data files the atlas page loads.

    python3 build_site.py <bundle_dir> <out_dir>

Writes atlas.json (index), locus-<GENE>.json (one per locus, loaded on demand),
variants.json, clock.json and rearr.json. Only the bundle is read; nothing is fetched.
"""
import base64, csv, gzip, json, math, sys
from fractions import Fraction
from pathlib import Path
import numpy as np

B, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()


def rows(path):
    p = B / path
    if not p.exists(): return []
    with gzip.open(p, 'rt') as f: return list(csv.DictReader(f))


def num(x, nd=5):
    if x is None or x == '': return None
    try: v = float(x)
    except (TypeError, ValueError): return None
    if not math.isfinite(v): return None
    return round(v, nd)


def dump(obj, name):
    (OUT / name).write_text(json.dumps(obj, separators=(',', ':'), allow_nan=False))
    return (OUT / name).stat().st_size


def mode_label(m):
    """One evidence level from whatever the bundle recorded for a layer."""
    if isinstance(m, str) and m.startswith('{'):
        try: m = json.loads(m)
        except ValueError: pass
    if isinstance(m, dict):
        vals = [mode_label(v) for v in m.values()]
        for k in ('observed', 'supported', 'exploratory', 'cells'):
            if k in vals: return k
        return 'unknown'
    return {'observed': 'observed', 'imputed_supported': 'supported', 'imputed_exploratory': 'exploratory',
            '': 'cells', 'none': 'unknown'}.get(str(m), 'unknown')


man = json.loads((B / 'manifest.json').read_text())
trust = json.loads((B / 'trust/trust.json').read_text())
probe = json.loads((B / 'probe_report.json').read_text()) if (B / 'probe_report.json').exists() else {}
fails = json.loads((B / 'failures.json').read_text()) if (B / 'failures.json').exists() else []
labels = [c['label'] for c in man['conditions']]
S = len(labels)
H = 524288


def signed_kb(pos, tss, strand):
    d = (pos - tss) * (1 if strand == '+' else -1)
    return d / 1000.0


def kb_text(d):
    return f'{"+" if d >= 0 else "−"}{abs(d):.1f} kb'


# ----------------------------------------------------------------------------- loci
loci_index, gene_coords, sizes = [], {}, {}
for L in man['loci']:
    g = L['gene']
    j = json.loads((B / f'loci/{g}.json').read_text())
    a = np.load(B / f'loci/{g}.npz')
    conds = j['conditions']                                   # all atlas states, in manifest order
    for x in j['genes']: gene_coords[x['name']] = dict(x, chrom=j['chrom'])
    pc = j['per_condition']
    # methylation: binned for the 1 Mb view, per CpG inside the zoom window
    cpg, mq = a['cpg_pos'].astype(np.int64), a['meth_q']
    nb, wb = man['bins']['n_wide'], man['bins']['wide']
    bins = np.clip((cpg - j['start']) // wb, 0, nb - 1)
    mw = np.full((len(conds), nb), 255, dtype=np.uint8)
    for ci in range(len(conds)):
        ok = mq[ci] < 255
        if ok.any():
            s = np.bincount(bins[ok], weights=mq[ci][ok].astype(float), minlength=nb)
            n = np.bincount(bins[ok], minlength=nb)
            has = n > 0
            mw[ci, has] = np.round(s[has] / n[has]).astype(np.uint8)
    density = np.bincount(bins, minlength=nb).astype(np.uint16)
    z0 = j['zoom_start']; z1 = z0 + man['bins']['n_zoom'] * man['bins']['zoom']
    inz = (cpg >= z0) & (cpg < z1)
    # consensus enhancers for the locus gene: merge calls that overlap or sit within 250 bp
    gid = j['gene_id']
    calls = []
    for ci, lab in enumerate(conds):
        for e in (pc.get(lab) or {}).get('enhancers') or []:
            if str(e.get('gene_id', '')).split('.')[0] == gid:
                calls.append((int(e['start']), int(e['end']), ci, float(e['gradient_score']), e.get('atac_score')))
    calls.sort()
    clusters = []
    for s_, e_, ci, gs, at in calls:
        if clusters and s_ <= clusters[-1]['end'] + 250:
            c = clusters[-1]; c['end'] = max(c['end'], e_)
        else:
            c = dict(start=s_, end=e_, grad=[None] * len(conds), atac=[None] * len(conds)); clusters.append(c)
        if c['grad'][ci] is None or gs > c['grad'][ci]:
            c['grad'][ci] = round(gs, 5); c['atac'][ci] = num(at, 3)
    for c in clusters:
        c['kb'] = round(signed_kb((c['start'] + c['end']) // 2, j['tss'], j['strand']), 2)
        c['max'] = max(v for v in c['grad'] if v is not None)
        c['n_states'] = sum(v is not None for v in c['grad'])
    clusters.sort(key=lambda c: -c['max'])
    # gene-level expression for every gene in the window
    expr = {}
    for x in j['genes']:
        expr[x['id']] = dict(name=x['name'],
                             sc=[num(((pc.get(l) or {}).get('expr_sc') or {}).get(x['id']), 3) for l in conds],
                             rna=[num(((pc.get(l) or {}).get('expr_rna') or {}).get(x['id']), 5) for l in conds])
    by_state = []
    for l in conds:
        p = pc.get(l)
        if not p: by_state.append(None); continue
        by_state.append(dict(expr=num((p.get('expr_sc') or {}).get(gid), 3), rna=num((p.get('expr_rna') or {}).get(gid), 5),
                             pacc=num(p.get('promoter_acc'), 4), pmeth=num(p.get('promoter_meth'), 4),
                             bmeth=num(p.get('body_meth'), 4),
                             n_enh=sum(1 for e in p.get('enhancers') or [] if str(e.get('gene_id', '')).split('.')[0] == gid),
                             grad_ok=bool(p.get('grad_ok')), method=p.get('enhancer_method')))
    # a plain-language reading of the locus, built only from the numbers above
    kinds = {c['label']: c['kind'] for c in man['conditions']}
    ex_all = [(labels[i], b['expr']) for i, b in enumerate(by_state) if b and b['expr'] is not None]
    ex = [t for t in ex_all if kinds.get(t[0]) == 'reference'] or ex_all       # headline within reference states
    reading = dict(headline='', body='', evidence=[])
    if ex:
        hi, lo = max(ex, key=lambda t: t[1]), min(ex, key=lambda t: t[1])
        top = clusters[0] if clusters else None
        distal = next((c for c in clusters if abs(c['kb']) >= 5), None)
        head = f'{g} is predicted highest in {hi[0]} ({hi[1]:.1f} CPM) and lowest in {lo[0]} ({lo[1]:.2g} CPM)'
        if distal:
            side = 'upstream' if distal['kb'] < 0 else 'downstream'
            head += f'; its strongest distal linked element sits {abs(distal["kb"]):.1f} kb {side} of the promoter.'
        else:
            head += '.'
        reading['headline'] = head
        body = []
        if lo[1] > 0: body.append(f'Predicted expression spans a {hi[1] / lo[1]:,.0f}-fold range across the {len(ex)} reference states.')
        ne = [(labels[i], b['n_enh']) for i, b in enumerate(by_state) if b]
        if ne:
            body.append(f'The model links between {min(n for _, n in ne)} and {max(n for _, n in ne)} elements to {g} per state '
                        f'({len(clusters)} distinct elements overall).')
        if distal:
            tops = [labels[i] for i, v in enumerate(distal['grad']) if v is not None and clusters and v == max(
                (c['grad'][i] for c in clusters if c['grad'][i] is not None and abs(c['kb']) >= 5), default=None)]
            body.append(f'The {kb_text(distal["kb"])} element (chr{j["chrom"][3:]}:{distal["start"]:,}–{distal["end"]:,}) is called in '
                        f'{distal["n_states"]} of {len(ne)} states'
                        + ('.' if not tops else f' and is the top distal link in {", ".join(tops)}.' if len(tops) <= 4 else f' and is the top distal link in {len(tops)} of them.'))
        pm = [b['pmeth'] for b in by_state if b and b['pmeth'] is not None]
        bm = [b['bmeth'] for b in by_state if b and b['bmeth'] is not None]
        if pm:
            rng = lambda v: f'about {min(v):.0%}' if round(min(v), 2) == round(max(v), 2) else f'{min(v):.0%} to {max(v):.0%}'
            body.append(f'Promoter CpGs are predicted {rng(pm)} methylated across states'
                        + (f', against {rng(bm)} across the gene body.' if bm else '.'))
        reading['body'] = ' '.join(body)
        ev = [f'{l}: {v:.1f} CPM' if v >= 1 else f'{l}: {v:.2g} CPM' for l, v in sorted(ex, key=lambda t: -t[1])[:4]]
        for c in clusters[:3]:
            ev.append(f'Element {kb_text(c["kb"])}: gradient score up to {c["max"]:.4f}, called in {c["n_states"]} states')
        aml = {l[4:].replace('-like', ''): by_state[i] for i, l in enumerate(labels) if l.startswith('AML ') and by_state[i]}
        ctl = {l.replace('SeqWell normal ', ''): by_state[i] for i, l in enumerate(labels) if l.startswith('SeqWell normal ') and by_state[i]}
        for k in aml:
            if k in ctl and aml[k]['expr'] and ctl[k]['expr']:
                ev.append(f'AML {k}-like vs matched normal {k}: {aml[k]["expr"] / ctl[k]["expr"]:.2f}× expression')
        reading['evidence'] = ev
    data = dict(gene=g, tier=j['tier'], gene_id=gid, chrom=j['chrom'], start=j['start'], end=j['end'], tss=j['tss'], strand=j['strand'],
                states=conds, present=[l in pc for l in conds],
                wide=dict(bin=wb, tracks=j['wide_tracks'], scale=[float(x) for x in a['wide_scale']], q=b64(a['wide_q'])),
                zoom=dict(start=z0, bin=man['bins']['zoom'], tracks=j['zoom_tracks'], scale=[float(x) for x in a['zoom_scale']], q=b64(a['zoom_q'])),
                meth_wide=b64(mw), cpg_density=b64(density),
                meth_zoom=dict(n=int(inz.sum()), pos=b64(cpg[inz].astype(np.int32)), q=b64(mq[:, inz])),
                genes=[dict(name=x['name'], id=x['id'], strand=x['strand'], start=x['start'], end=x['end'], tss=x['tss'], exons=x['exons']) for x in j['genes']],
                enhancers=clusters, expr=expr)
    sizes[g] = dump(data, f'locus-{g}.json')
    loci_index.append(dict(gene=g, tier=j['tier'], gene_id=gid, chrom=j['chrom'], start=j['start'], end=j['end'], tss=j['tss'],
                           strand=j['strand'], window_source=j.get('window_source'), n_cpg=int(len(cpg)), by_state=by_state,
                           reading=reading, top=[dict(kb=c['kb'], start=c['start'], end=c['end'], max=c['max'], n_states=c['n_states'],
                                                      best=labels[int(np.argmax([v or 0 for v in c['grad']]))]) for c in clusters[:3]]))

# ----------------------------------------------------------------------------- states
states = []
for ci, c in enumerate(man['conditions']):
    modes = {}
    for L in man['loci']:
        p = json.loads((B / f'loci/{L["gene"]}.json').read_text())['per_condition'].get(c['label'])
        if p:
            m = p.get('modes') or {}
            modes = dict(rna=mode_label(m.get('rna')), acc=mode_label(m.get('acc')), meth=mode_label(m.get('meth')),
                         expr=mode_label(m.get('expr_sc')),
                         hist=mode_label({k: v for k, v in m.items() if k.startswith('H3')}))
            break
    info = c.get('info') or {}
    states.append(dict(label=c['label'], kind=c['kind'], group=c.get('group') or '', name=c.get('name') or '', curie=c.get('curie'),
                       n_cells=info.get('n_cells'), donors=info.get('donors'), modes=modes))

# ----------------------------------------------------------------------------- variants
regions = json.loads((B / 'variants/regions.json').read_text()) if (B / 'variants/regions.json').exists() else []
ism, clinvar, gnomad, indels = rows('variants/ism.csv.gz'), rows('variants/clinvar.csv.gz'), rows('variants/gnomad.csv.gz'), rows('variants/clinvar_indels_scored.csv.gz')
READOUTS = [('expr', 'expr_target'), ('acc', 'acc'), ('h3k27ac', 'h3k27ac'), ('meth', 'meth_mean'), ('meth_max', 'meth_maxabs')]
BASES = 'ACGT'
vregions, region_index = [], []
for r in regions:
    n = r['end'] - r['start']
    rr = [x for x in ism if x['region'] == r['id']]
    conds = [l for l in labels if any(x['condition'] == l for x in rr)]
    data = {}
    for l in conds:
        d = {k: [[None] * 4 for _ in range(n)] for k, _ in READOUTS}
        other = [[None] * 4 for _ in range(n)]
        for x in rr:
            if x['condition'] != l: continue
            i = int(x['pos']) - 1 - r['start']
            if not (0 <= i < n) or x['alt'] not in BASES: continue
            bi = BASES.index(x['alt'])
            for k, col in READOUTS: d[k][i][bi] = num(x.get(col), 4)
            if x.get('expr_other_gene'): other[i][bi] = [x['expr_other_gene'], num(x.get('expr_other'), 4)]
        d['other'] = other
        data[l] = d
    g = gene_coords.get(r['gene'])
    kb = round(signed_kb((r['start'] + r['end']) // 2, g['tss'], g['strand']), 1) if g else None
    best = None
    for x in rr:
        v = num(x.get('expr_target'))
        if v is not None and (best is None or abs(v) > abs(best[0])): best = (v, x)
    vr = dict(id=r['id'], name=r['name'], gene=r['gene'], chrom=r['chrom'], start=r['start'], end=r['end'], seq=r.get('sequence', ''),
              auto=bool(r.get('auto')), kb=kb, conds=conds, data=data,
              clinvar=[dict(id=x['clinvar_id'], title=x['title'], pos=int(x['pos']), ref=x['ref'], alt=x['alt'], cls=x['germline'] or x.get('oncogenicity') or 'Not classified',
                            review=x.get('review', ''), consequence=x.get('consequence', '')) for x in clinvar if x['region'] == r['id']],
              gnomad=[dict(pos=int(x['pos']), ref=x['ref'], alt=x['alt'], ac=int(float(x['ac'])), an=int(float(x['an'])), af=num(x['af'], 9)) for x in gnomad if x['region'] == r['id']],
              indels=[dict(id=x['clinvar_id'], title=x['title'], cls=x['germline'], cond=x['condition'], pos=int(x['pos']), ref=x['ref'], alt=x['alt'],
                           expr=num(x.get('expr_target'), 4), acc=num(x.get('acc'), 4), h3k27ac=num(x.get('h3k27ac'), 4), meth=num(x.get('meth_mean'), 4))
                      for x in indels if x['region'] == r['id']])
    vregions.append(vr)
    region_index.append(dict(id=r['id'], name=r['name'], gene=r['gene'], chrom=r['chrom'], start=r['start'], end=r['end'], auto=bool(r.get('auto')), kb=kb,
                             n_clinvar=len(vr['clinvar']), conds=conds,
                             best=None if best is None else dict(v=best[0], pos=int(best[1]['pos']), ref=best[1]['ref'], alt=best[1]['alt'], cond=best[1]['condition'])))
sizes['variants'] = dump(vregions, 'variants.json')

# ----------------------------------------------------------------------------- clock
clock_rows = rows('clock/clock_cpgs.csv.gz')
clock_meta = json.loads((B / 'clock/clock_meta.json').read_text()) if (B / 'clock/clock_meta.json').exists() else {}
cpgs, cstates, measured_types = [], [], []
if clock_rows:
    z = np.load(B / 'clock/predicted_beta.npz')
    cstates = [str(x) for x in z['conditions']]
    arr = {x['probe']: i for i, x in enumerate(rows('clock/array_cpgs.csv.gz'))}
    meas = {}
    mp = B / 'clock/measured_blood_450k.csv.gz'
    if mp.exists():
        with gzip.open(mp, 'rt') as f:
            rd = csv.reader(f); head = next(rd); measured_types = head[1:]
            for line in rd: meas[line[0]] = [num(v, 3) for v in line[1:]]
    beta, prof, flank = z['beta'].astype(float), z['ism_profile'].astype(float), int(z['ism_flank'])
    for i, x in enumerate(clock_rows):
        k = arr.get(x['probe'])
        cpgs.append(dict(probe=x['probe'], chrom=x['chrom'], pos=int(x['pos']),
                         coefs={c[5:]: num(x[c], 4) for c in x if c.startswith('coef_') and x[c] != ''},
                         beta=[num(v, 3) for v in beta[k]] if k is not None else [None] * len(cstates),
                         sd=num(x.get('state_sens_sd'), 4), range=num(x.get('state_sens_range'), 4), mean=num(x.get('beta_mean_normal'), 3),
                         seq=num(x.get('seq_sens_mean'), 4), seq_max=num(x.get('seq_sens_max'), 4), aml=num(x.get('aml_minus_control'), 4),
                         prof=[num(v, 3) for v in prof[i]], measured=meas.get(x['probe'])))
    prof_cov = float(np.isfinite(np.delete(prof, [flank, flank + 1], axis=1)).mean()) if len(prof) else 0.0
else:
    flank, prof_cov = 10, 0.0
sizes['clock'] = dump(dict(states=cstates, clocks=clock_meta.get('clocks', {}), flank=flank, ism_state=clock_meta.get('ism_condition'),
                           profile_coverage=round(prof_cov, 3), measured_types=measured_types, cpgs=cpgs), 'clock.json')

# ----------------------------------------------------------------------------- rearrangements
rj = json.loads((B / 'rearrangements/rearrangements.json').read_text()) if (B / 'rearrangements/rearrangements.json').exists() else []
rexpr = rows('rearrangements/gene_expression.csv.gz')
rearr, rearr_index = [], []


def arm_iv(side, spec):
    c, bp, s = spec
    if side == 'left': return (c, bp - H, bp) if s == '+' else (c, bp, bp + H)
    return (c, bp, bp + H) if s == '+' else (c, bp - H, bp)


def to_derived(side, spec, g):
    _, s, e = arm_iv(side, spec)
    return (g - s if spec[2] == '+' else e - 1 - g) + (0 if side == 'left' else H)


for R in rj:
    ex = R.get('_export')
    if not ex: continue
    a = np.load(B / f'rearrangements/{R["name"]}.npz')
    V = ex['variants']; nb = a[f'q_{ex["tracks"][0]}'].shape[-1]; half = nb // 2
    lanes = ['native'] + [v for v in V if not v.startswith('native')]
    q, scales = {}, {}
    for t in ex['tracks']:
        src = a[f'q_{t}']                                      # (cond, variant, bins)
        out = np.zeros((src.shape[0], len(lanes), nb), dtype=np.uint8)
        for li, lane in enumerate(lanes):
            if lane != 'native':
                out[:, li] = src[:, V.index(lane)]; continue
            # each arm as it looks in its normal genomic context, laid out in rearranged coordinates
            for side, sl in (('left', slice(0, half)), ('right', slice(half, nb))):
                flip = R[side][2] == '-'
                tt = t
                if flip and t in ('rna_plus', 'rna_minus'): tt = 'rna_minus' if t == 'rna_plus' else 'rna_plus'
                nat = a[f'q_{tt}'][:, V.index(f'native_{side}')] if f'q_{tt}' in a.files else src[:, V.index(f'native_{side}')]
                if side == 'left': seg = nat[:, half:][:, ::-1] if flip else nat[:, :half]
                else:              seg = nat[:, :half][:, ::-1] if flip else nat[:, half:]
                out[:, li, sl] = seg
        q[t] = b64(out); scales[t] = float(a[f'scale_{t}'])
    marks = []
    for gname in R['genes']:
        g = gene_coords.get(gname)
        if not g: continue
        for side in ('left', 'right'):
            c, s, e = arm_iv(side, R[side])
            if g['chrom'] == c and g['end'] > s and g['start'] < e:
                lo, hi = sorted((to_derived(side, R[side], max(g['start'], s)), to_derived(side, R[side], min(g['end'], e) - 1)))
                strand = g['strand'] if R[side][2] == '+' else ('-' if g['strand'] == '+' else '+')
                tss = to_derived(side, R[side], g['tss']) if s <= g['tss'] < e else None
                marks.append(dict(kind='gene', name=gname, lo=lo, hi=hi, strand=strand, tss=tss))
    if R.get('scramble'):
        c, s, e = R['scramble']
        for side in ('left', 'right'):
            ac, a_s, a_e = arm_iv(side, R[side])
            if ac == c and a_s <= s and e <= a_e:
                lo, hi = sorted((to_derived(side, R[side], s), to_derived(side, R[side], e - 1)))
                marks.append(dict(kind='enhancer', name='GATA2 distal enhancer', lo=lo, hi=hi))
    er = [dict(cond=x['condition'], gene=x['gene'], arm=x['arm'], focus=x['focus'] == 'True', native=num(x['native'], 5),
               rearranged=num(x['rearranged'], 5), scrambled=num(x.get('enhancer_scrambled'), 5)) for x in rexpr if x['rearrangement'] == R['name']]
    rearr.append(dict(name=R['name'], label=R['label'], genes=R['genes'], left=R['left'], right=R['right'], scramble=R.get('scramble'),
                      arms={s: dict(interval=list(arm_iv(s, R[s])), strand=R[s][2]) for s in ('left', 'right')},
                      conds=ex['conditions'], lanes=lanes, tracks=ex['tracks'], scales=scales, q=q, bin=2 * H // nb, marks=marks, expr=er))
    foc = [x for x in er if x['focus'] and x['native'] and x['rearranged']]
    rearr_index.append(dict(name=R['name'], label=R['label'], genes=R['genes'], conds=ex['conditions'],
                            focus=[dict(gene=x['gene'], cond=x['cond'], fold=round(x['rearranged'] / x['native'], 3),
                                        fold_scrambled=round(x['scrambled'] / x['native'], 3) if x['scrambled'] else None) for x in foc]))
sizes['rearr'] = dump(rearr, 'rearr.json')

# ----------------------------------------------------------------------------- trust
tm = []
sc = np.load(B / 'trust/methylation_scatter.npz') if (B / 'trust/methylation_scatter.npz').exists() else None
for lab, r in (trust.get('methylation') or {}).items():
    key = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in lab)
    pts = []
    if sc is not None and key in sc.files:
        p = sc[key].astype(float); p = p[np.isfinite(p).all(axis=1)]
        p = p[np.random.default_rng(1).choice(len(p), size=min(700, len(p)), replace=False)]
        pts = [[round(float(a_), 3), round(float(b_), 3)] for a_, b_ in p]
    tm.append(dict(label=lab, measured=r.get('measured_cell_type'), n=r.get('n'), pearson=num(r.get('pearson'), 3), spearman=num(r.get('spearman'), 3),
                   mae=num(r.get('mae'), 3), mode=mode_label(r.get('imputation_mode')), calibration=r.get('calibration'), points=pts))
cert = trust.get('conditioning_certificate')
cert_out = None
if cert:
    def pf(x):
        try: return float(Fraction(x))
        except (ValueError, ZeroDivisionError, TypeError): return None
    cert_out = dict(M=cert.get('M'), K=cert.get('K'), n=cert.get('n_elements'),
                    tests={k: dict(K=v.get('K'), M=v.get('M'), p=pf(v.get('p')), passed=bool(v.get('pass_')))
                           for k, v in cert.items() if isinstance(v, dict) and 'p' in v})
outs = {}
for kind, d in (probe.get('outputs') or {}).items():
    outs[kind] = {n: dict(ok=bool(x.get('ok')), tracks=x.get('n_tracks'), resolution=x.get('resolution'), modes=x.get('imputation_modes')) for n, x in d.items()}

# ----------------------------------------------------------------------------- places to start
findings = []
def distal_top(L):
    return next((c for c in L['top'] if abs(c['kb']) >= 5), None)
ranked = sorted((L for L in loci_index if distal_top(L)), key=lambda L: -distal_top(L)['max'])
for L in ranked[:4]:
    t = distal_top(L)
    findings.append(dict(title=L['gene'], tag='Linked element', sub=f'{kb_text(t["kb"])} element, strongest in {t["best"]}', href=f'locus-{L["gene"]}'))
# largest AML-versus-matched-control differences in predicted expression
pairs = [(i, labels.index('SeqWell normal ' + l[4:].replace('-like', ''))) for i, l in enumerate(labels)
         if l.startswith('AML ') and ('SeqWell normal ' + l[4:].replace('-like', '')) in labels]
diffs = []
for L in loci_index:
    for ai, ci in pairs:
        a_, c_ = L['by_state'][ai], L['by_state'][ci]
        if a_ and c_ and a_['expr'] is not None and c_['expr'] is not None and max(a_['expr'], c_['expr']) >= 5:
            diffs.append((math.log2((a_['expr'] + 1) / (c_['expr'] + 1)), L['gene'], labels[ai], labels[ci]))
seen = set()
for d_, g_, la, lc in sorted(diffs, key=lambda t: -abs(t[0])):
    if g_ in seen: continue
    seen.add(g_)
    findings.append(dict(title=g_, tag='AML vs control', sub=f'{2 ** d_:.1f}× in {la} against {lc.replace("SeqWell ", "")}', href=f'locus-{g_}'))
    if len(seen) == 2: break
if cpgs:
    c = max((x for x in cpgs if x['sd'] is not None), key=lambda x: x['sd'], default=None)
    if c: findings.append(dict(title=c['probe'], tag='Clock CpG', sub=f'most state-dependent site: SD {c["sd"]:.2f} across normal states', href='clock'))
for i, r in enumerate(rearr_index):
    f = max(r['focus'], key=lambda x: abs(math.log2(x['fold'])), default=None)
    if f: findings.append(dict(title=f['gene'], tag='Rearrangement', sub=f'{f["fold"]:.2f}× native expression after inv(3) in {f["cond"]}', href=f'rearr-{i}'))
if tm:
    t = max(tm, key=lambda x: x['pearson'] or 0)
    findings.append(dict(title='Methylation', tag='Check', sub=f'r = {t["pearson"]:.2f} against measured {t["measured"]} (n = {t["n"]:,})', href='trust'))

atlas = dict(
    meta=dict(run_mode=man['run_mode'], created=man['created'], sdk=man['sdk'], n_failures=man['n_failures'], calls=man.get('model_calls_this_session'),
              caveats=man.get('caveats', []), bins=man['bins'], planned_loci=49),
    states=states, bench=[dict(label=c['label'], name=c.get('name'), curie=c.get('curie')) for c in man.get('benchmark_conditions', [])],
    loci=loci_index, regions=region_index, rearr=rearr_index,
    clock=dict(n=len(cpgs), clocks=clock_meta.get('clocks', {}), profile_coverage=round(prof_cov, 3)),
    findings=findings[:10],
    trust=dict(methylation=tm, contrasts=trust.get('methylation_contrasts') or [], expression=trust.get('expression') or {},
               embeddings=trust.get('cell_embeddings') or {}, certificate=cert_out, e2g=trust.get('e2g_gata2_enhancer') or {},
               outputs=outs, failures=fails[:50]))
sizes['atlas'] = dump(atlas, 'atlas.json')
print({k: f'{v / 1e3:.0f} KB' for k, v in sizes.items()})
print('findings:'); [print('  ', f['title'], '|', f['tag'], '|', f['sub']) for f in atlas['findings']]
for L in loci_index: print(L['gene'], '->', L['reading']['headline']); print('    ', L['reading']['body']); print('    ', L['reading']['evidence'])
