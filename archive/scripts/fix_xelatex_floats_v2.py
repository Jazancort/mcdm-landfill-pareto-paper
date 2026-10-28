"""
fix_xelatex_floats_v2.py — substituição por número de linha, sem risco de duplicação.
"""

with open('main.tex', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

print(f'Total lines before: {len(lines)}')

# Mapa: número de linha (1-based) -> novo conteúdo
patches = {
    # F4 map: begin + end
    627:  r'\begin{figure*}[t]' + '\r\n',
    628:  r'\centering' + '\r\n',   # já correcto, só por segurança
    631:  r'\includegraphics[width=0.5\textwidth]{figures/fig_F4_map.pdf}' + '\r\n',
    640:  r'\end{figure*}' + '\r\n',

    # F5 binary: begin + end
    940:  r'\begin{figure*}[t]' + '\r\n',
    941:  r'\centering' + '\r\n',
    942:  r'\includegraphics[width=0.5\textwidth]{figures/fig_F5_binary_amplitude.pdf}' + '\r\n',
    953:  r'\end{figure*}' + '\r\n',

    # F2 interaction: begin + end
    1437: r'\begin{figure*}[t]' + '\r\n',
    1438: r'\centering' + '\r\n',
    1439: r'\includegraphics[width=0.5\textwidth]{figures/fig_F2_interaction.pdf}' + '\r\n',
    1455: r'\end{figure*}' + '\r\n',

    # tab:amprefset: begin + end
    1505: r'\begin{table*}[t]' + '\r\n',
    1524: r'\end{table*}' + '\r\n',

    # tab:fourthcell: begin + end
    1530: r'\begin{table*}[t]' + '\r\n',
    1544: r'\end{table*}' + '\r\n',
}

for ln, new in sorted(patches.items()):
    old = lines[ln-1].rstrip('\r\n')
    lines[ln-1] = new
    print(f'L{ln}: {repr(old[:50])} -> {repr(new.rstrip()[:50])}')

with open('main.tex', 'w', encoding='utf-8', newline='') as f:
    f.writelines(lines)

print(f'\nTotal lines after: {len(lines)}')

# Verificar resultado
print('\nFloat inventory:')
for i, l in enumerate(lines, 1):
    if any(x in l for x in [r'\begin{figure', r'\begin{table', r'\end{figure', r'\end{table']):
        print(f'  L{i}: {l.rstrip()[:70]}')
