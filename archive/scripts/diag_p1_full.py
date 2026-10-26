import pandas as pd, numpy as np, sys, os; sys.path.insert(0,'.')
from mcdm_experiment import (
    load_data,impute_nan,COL,AHP_WEIGHTS,_build_decision_matrix,
    haversine_km,optimal_trio_enumerate,MIN_DIST_KM,INV,COST,F1_CRIT,F2_CRIT,F3_CRIT
)

df_all,par,bcs=load_data()
df_imp=impute_nan(df_all)
via_mask=df_imp[COL['protected']]>0
df_via=df_imp[via_mask].copy()
w=np.array(list(AHP_WEIGHTS.values()),dtype=np.float32)
col_names=list(AHP_WEIGHTS.keys())
X_via,benefit=_build_decision_matrix(df_via)
D=haversine_km(df_via['latitude (degrees)'].values,df_via['longitude (degrees)'].values)
via_idx=df_via.index.values
N=len(df_via)

front_ap=pd.read_csv('results/pareto_front_Aprime.csv')
s = frozenset([184,430,460])
in_ap=any(frozenset([int(r.idx1),int(r.idx2),int(r.idx3)])==s for _,r in front_ap.iterrows())
print('{184,430,460} in pareto_front_Aprime.csv:', in_ap)
print('Front colunas:', list(front_ap.columns))
print('Front F1P range:', round(front_ap.F1P.min(),4), round(front_ap.F1P.max(),4))
print('Front F2P range:', round(front_ap.F2P.min(),4), round(front_ap.F2P.max(),4))
print('Front F3P range:', round(front_ap.F3P.min(),4), round(front_ap.F3P.max(),4))

# Calcular objetivos do trio {184,430,460}
def _norm(x,ref):
    lo,hi=ref.min(),ref.max(); return (x-lo)/(hi-lo) if hi>lo else np.zeros_like(x)
f1v=np.zeros(N,dtype=np.float32); f2v=np.zeros(N,dtype=np.float32); f3v=np.zeros(N,dtype=np.float32)
for j,k in enumerate(col_names):
    col=COL[k]; x=df_via[col].values.astype(float); ref=df_via[col].values.astype(float)
    if k=='aspect': c=np.where((x>=90)&(x<=180),0.,1.)
    elif k in INV:  c=1.-_norm(x,ref)
    elif k in COST: c=_norm(x,ref)
    else:           c=_norm(x,ref)
    c=(c*w[j]).astype(np.float32)
    if k in F1_CRIT: f1v+=c
    elif k in F2_CRIT: f2v+=c
    else: f3v+=c

# Localizar índices locais de {184,430,460}
local_ids = [int(np.where(via_idx==g)[0][0]) for g in [184,430,460]]
print('IDs locais de {184,430,460}:', local_ids)
f1t=float(f1v[local_ids[0]]+f1v[local_ids[1]]+f1v[local_ids[2]])
f2t=float(f2v[local_ids[0]]+f2v[local_ids[1]]+f2v[local_ids[2]])
f3t=float(f3v[local_ids[0]]+f3v[local_ids[1]]+f3v[local_ids[2]])
print('Objetivos {184,430,460}: f1=',round(f1t,4),'f2=',round(f2t,4),'f3=',round(f3t,4))

# Verificar dominância
F1f=front_ap.F1P.values; F2f=front_ap.F2P.values; F3f=front_ap.F3P.values
le=(F1f<=f1t+1e-7)&(F2f<=f2t+1e-7)&(F3f>=f3t-1e-7)
lt=(F1f<f1t-1e-7)|(F2f<f2t-1e-7)|(F3f>f3t+1e-7)
dom=(le&lt)
print('Num trios que dominam {184,430,460}:', dom.sum())
if dom.any():
    print('Primeiro dominador:', front_ap[dom].iloc[0].to_dict())

# O trio pode nao estar na fronteira A' porque usa referencia 473 para o score
# mas A' foi calculada com ref 389 -- verificar
# A' = trios calculados com compute_objs(w, df_via) -- referencia df_via (389)
# SAW score com ref=389 maximiza sum(c_ij) com c normalizado em df_via
# P1: SAW[ref=389] optimal DEVE estar em A' (fronteira com ref=389)
# Verificar: pareto_front_Aprime foi calculado com ref df_via (389)?
# Ver o script space_aprime.py
print()
print('Verificando: a fronteira A prime usa ref=df_via ou ref=df_imp?')
sc_can=pd.read_csv('results/space_aprime_canonical.csv')
print('space_aprime_canonical colunas:', list(sc_can.columns))
print(sc_can.head(5).to_string(index=False))
