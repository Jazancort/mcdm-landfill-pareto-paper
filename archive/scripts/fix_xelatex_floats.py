"""
fix_xelatex_floats.py
Converte as figuras single-column e tabelas problemáticas para figure*/table*
para resolver o Float(s) lost com XeLaTeX + stfloats v3.4 + CAS-DC.

O stfloats v3.4 com XeLaTeX rejeita qualquer specifier explícito [t], [tp],
[tbp], [htbp] em begin{figure} (single-column em twocolumn) e usa um
specifier vazio que causa Float(s) lost. A solução é converter para figure*
(double-wide) que stfloats sempre aceita com [t].

Tabelas single-column no final do documento (L1505, L1530) também causam
Float(s) lost porque o scheduler não consegue colocá-las antes das
referências. Convertem-se para table* com [t].
"""

with open('main.tex', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

# ── Figuras single-column → figure* ──────────────────────────────────────
# F4: map (L627)
text = text.replace(
    r'\begin{figure}' + '\n' + r'\centering' + '\n' + r'\includegraphics[width=0.88\columnwidth]{figures/fig_F4_map.pdf}',
    r'\begin{figure*}[t]' + '\n' + r'\centering' + '\n' + r'\includegraphics[width=0.5\textwidth]{figures/fig_F4_map.pdf}'
)
# find and replace the matching \end{figure} for F4 (before \paragraph{Missing values.})
text = text.replace(
    r'\label{fig:map}' + '\n' + r'\end{figure}' + '\n' + '\n' + r'\paragraph{Missing values.}',
    r'\label{fig:map}' + '\n' + r'\end{figure*}' + '\n' + '\n' + r'\paragraph{Missing values.}'
)

# F5: binary amplitude (L940)
text = text.replace(
    r'\begin{figure}' + '\n' + r'\centering' + '\n' + r'\includegraphics[width=0.88\columnwidth]{figures/fig_F5_binary_amplitude.pdf}',
    r'\begin{figure*}[t]' + '\n' + r'\centering' + '\n' + r'\includegraphics[width=0.5\textwidth]{figures/fig_F5_binary_amplitude.pdf}'
)
text = text.replace(
    r'\label{fig:binary_amplitude}' + '\n' + r'\end{figure}',
    r'\label{fig:binary_amplitude}' + '\n' + r'\end{figure*}'
)

# F2: interaction (L1437)
text = text.replace(
    r'\begin{figure}' + '\n' + r'\centering' + '\n' + r'\includegraphics[width=0.85\columnwidth]{figures/fig_F2_interaction.pdf}',
    r'\begin{figure*}[t]' + '\n' + r'\centering' + '\n' + r'\includegraphics[width=0.5\textwidth]{figures/fig_F2_interaction.pdf}'
)
text = text.replace(
    r'\label{fig:interaction}' + '\n' + r'\end{figure}',
    r'\label{fig:interaction}' + '\n' + r'\end{figure*}'
)

# ── Tabelas single-column no final → table* ───────────────────────────────
# tab:amprefset — usar marcador único (a caption)
text = text.replace(
    r'\begin{table}' + '\n' + r'\centering' + '\n' + r'\caption{Amplitude ratio~\eqref{eq:refsetA} by criterion.}' + '\n' + r'\label{tab:amprefset}',
    r'\begin{table*}[t]' + '\n' + r'\centering' + '\n' + r'\caption{Amplitude ratio~\eqref{eq:refsetA} by criterion.}' + '\n' + r'\label{tab:amprefset}'
)
text = text.replace(
    r'\end{tabular}' + '\n' + r'\end{table}' + '\n' + '\n' + r'Both diagonal cells confirm',
    r'\end{tabular}' + '\n' + r'\end{table*}' + '\n' + '\n' + r'Both diagonal cells confirm'
)

# tab:fourthcell — usar marcador único (a caption)
text = text.replace(
    r'\begin{table}' + '\n' + r'\centering' + '\n' + r'\caption{Score--evaluator alignment, $Q_2$, SAW min--max, $\kappa=200$.}' + '\n' + r'\label{tab:fourthcell}',
    r'\begin{table*}[t]' + '\n' + r'\centering' + '\n' + r'\caption{Score--evaluator alignment, $Q_2$, SAW min--max, $\kappa=200$.}' + '\n' + r'\label{tab:fourthcell}'
)
text = text.replace(
    r'\end{tabular}' + '\n' + r'\end{table}' + '\n' + '\n' + r'Both diagonal cells confirm Proposition',
    r'\end{tabular}' + '\n' + r'\end{table*}' + '\n' + '\n' + r'Both diagonal cells confirm Proposition'
)

with open('main.tex', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text)

# Verificar
with open('main.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'Total lines: {len(lines)}')
for i, l in enumerate(lines, 1):
    if any(x in l for x in [r'\begin{figure', r'\begin{table', r'\end{figure', r'\end{table']):
        print(f'  L{i}: {l.rstrip()[:70]}')
