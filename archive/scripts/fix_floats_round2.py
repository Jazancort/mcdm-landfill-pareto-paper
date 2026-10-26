"""fix_floats_round2.py
1. Converte figure* → figure para Fig 2 (F5) e Fig 5 (F2) — gráficos de meia largura
2. Converte table* → table para Tab 3-7 (as que cabem em coluna simples)
3. Remove hack @currlist
"""

with open('main.tex', 'r', encoding='utf-8') as f:
    text = f.read()

n = 0

# ── Fig 2 (F5 binary amplitude) — figure* → figure, 0.5textwidth → 0.92columnwidth
old = r"""\begin{figure*}[!t]
\centering
\includegraphics[width=0.5\textwidth]{figures/fig_F5_binary_amplitude.pdf}"""
new = r"""\begin{figure}[!t]
\centering
\includegraphics[width=0.92\columnwidth]{figures/fig_F5_binary_amplitude.pdf}"""
if old in text:
    text = text.replace(old, new, 1)
    n += 1
    print("Converted fig_F5 figure* -> figure")

old_end_f5 = r"""\label{fig:binary_amplitude}
\end{figure*}"""
new_end_f5 = r"""\label{fig:binary_amplitude}
\end{figure}"""
if old_end_f5 in text:
    text = text.replace(old_end_f5, new_end_f5, 1)

# ── Fig 5 (F2 interaction) — figure* → figure, 0.5textwidth → 0.92columnwidth
old = r"""\begin{figure*}[!t]
\centering
\includegraphics[width=0.5\textwidth]{figures/fig_F2_interaction.pdf}"""
new = r"""\begin{figure}[!t]
\centering
\includegraphics[width=0.92\columnwidth]{figures/fig_F2_interaction.pdf}"""
if old in text:
    text = text.replace(old, new, 1)
    n += 1
    print("Converted fig_F2 figure* -> figure")

old_end_f2 = r"""\label{fig:interaction}
\end{figure*}"""
new_end_f2 = r"""\label{fig:interaction}
\end{figure}"""
if old_end_f2 in text:
    text = text.replace(old_end_f2, new_end_f2, 1)

# ── Tables 3-7: table* → table
# Tab 3: tab:canonical
for label in ['tab:canonical', 'tab:tvorder', 'tab:factorial', 'tab:effects',
              'tab:amprefset', 'tab:fourthcell']:
    # find begin{table*} that contains this label
    import re
    # replace begin{table*}[!t] → begin{table}[!t] only for tables that have these labels
    # and their matching end{table*}
    # Strategy: find the label position, then scan backwards for begin{table*} and forwards for end{table*}
    idx = text.find(fr'\label{{{label}}}')
    if idx < 0:
        print(f"Label {label} not found")
        continue
    # scan back for \begin{table*}
    start = text.rfind(r'\begin{table*}', 0, idx)
    if start < 0:
        print(f"No begin{{table*}} before {label}")
        continue
    # scan forward for \end{table*}
    end = text.find(r'\end{table*}', idx)
    if end < 0:
        print(f"No end{{table*}} after {label}")
        continue
    end_end = end + len(r'\end{table*}')
    chunk = text[start:end_end]
    new_chunk = chunk.replace(r'\begin{table*}', r'\begin{table}', 1)
    new_chunk = new_chunk.replace(r'\end{table*}', r'\end{table}', 1)
    text = text[:start] + new_chunk + text[end_end:]
    n += 1
    print(f"Converted {label} table* -> table")

# ── Remove @currlist hack
hack = r'\makeatletter\global\let\@currlist\@empty\makeatother'
if hack in text:
    text = text.replace(hack, '', 1)
    n += 1
    print("Removed @currlist hack")

with open('main.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print(f'\nTotal changes: {n}')
