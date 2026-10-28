"""
fix_xelatex_floats_v3.py
Substituição cirúrgica por linha para corrigir floats com XeLaTeX + stfloats v3.4.
Converte figure → figure* e table → table* nas posições correctas.
"""

with open('main.tex', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')

# Verificar que o ficheiro não está duplicado
assert len(lines) < 2000, f'File seems duplicated ({len(lines)} lines)!'

# Mapa: (linha 1-based, expected_content_fragment) -> new_line
patches = [
    # F4 map
    (627,  r'\begin{figure}',              r'\begin{figure*}[t]' + '\r\n'),
    (629,  r'\includegraphics[width=0.88', r'\includegraphics[width=0.5\textwidth]{figures/fig_F4_map.pdf}' + '\r\n'),
    (640,  r'\end{figure}',               r'\end{figure*}' + '\r\n'),

    # F5 binary
    (940,  r'\begin{figure}',              r'\begin{figure*}[t]' + '\r\n'),
    (942,  r'\includegraphics[width=0.88', r'\includegraphics[width=0.5\textwidth]{figures/fig_F5_binary_amplitude.pdf}' + '\r\n'),
    (953,  r'\end{figure}',               r'\end{figure*}' + '\r\n'),

    # F2 interaction
    (1437, r'\begin{figure}',              r'\begin{figure*}[t]' + '\r\n'),
    (1439, r'\includegraphics[width=0.85', r'\includegraphics[width=0.5\textwidth]{figures/fig_F2_interaction.pdf}' + '\r\n'),
    (1455, r'\end{figure}',               r'\end{figure*}' + '\r\n'),

    # tab:amprefset
    (1505, r'\begin{table}',              r'\begin{table*}[t]' + '\r\n'),
    (1524, r'\end{table}',               r'\end{table*}' + '\r\n'),

    # tab:fourthcell
    (1530, r'\begin{table}',              r'\begin{table*}[t]' + '\r\n'),
    (1544, r'\end{table}',               r'\end{table*}' + '\r\n'),
]

errors = 0
for ln, expected, new in patches:
    actual = lines[ln-1]
    if expected in actual:
        old = actual.rstrip('\r\n')
        lines[ln-1] = new
        print(f'  L{ln}: OK  {repr(old[:50])} -> {repr(new.rstrip()[:50])}')
    else:
        print(f'  L{ln}: ERR expected={repr(expected[:40])} got={repr(actual.rstrip()[:40])}')
        errors += 1

if errors:
    print(f'\n{errors} errors — file NOT written.')
else:
    with open('main.tex', 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)
    print(f'\nFile written. Lines: {len(lines)}')

    # Inventário final
    print('\nFloat inventory:')
    for i, l in enumerate(lines, 1):
        if any(x in l for x in [r'\begin{figure', r'\begin{table', r'\end{figure', r'\end{table']):
            print(f'  L{i}: {l.rstrip()[:70]}')
