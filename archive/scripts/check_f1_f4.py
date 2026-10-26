import csv

rows = list(csv.DictReader(open('scripts/results/mcdm_rankings.csv')))
print('Total rows:', len(rows))
print('First idx:', rows[0][''])
print('Last idx:', rows[-1][''])
print()
lat_col = 'latitude (degrees)'
lon_col = 'longitude (degrees)'
for idx in [183, 184, 429, 430, 459, 460]:
    if idx < len(rows):
        r = rows[idx]
        print(f'row {idx}: lat={float(r[lat_col]):.5f}  lon={float(r[lon_col]):.5f}')

print()
W = dict(perm=0.152,slope=0.113,roads=0.030,rivers=0.091,aspect=0.075,
         coast=0.069,protected=0.066,wells=0.055,urban=0.166,aero=0.102,cult=0.081)
A_rank = dict(perm=0.547,slope=0.995,roads=0.995,rivers=0.995,aspect=0.499,
              coast=0.995,protected=0.995,wells=0.995,urban=0.989,aero=0.995,cult=0.981)
A_vec  = dict(perm=0.583,slope=0.135,roads=0.206,rivers=0.265,aspect=0.103,
              coast=0.126,protected=0.105,wells=0.081,urban=0.107,aero=0.086,cult=0.171)
A_mm   = {c:1.0 for c in W}

for norm, A in [('mm', A_mm), ('vec', A_vec), ('rank', A_rank)]:
    denom = sum(W[c]*A[c] for c in W)
    print(f'\nNorm={norm}  denom={denom:.4f}')
    for c in ['perm','urban','aspect','slope']:
        weff = W[c]*A[c]/denom*100
        print(f'  {c:10s}: w_nom={W[c]*100:.1f}%  w_eff={weff:.2f}%  ratio={weff/(W[c]*100):.3f}x')
    maxw = max(W[c]*A[c]/denom*100 for c in W)
    print(f'  max w_eff = {maxw:.2f}%')
