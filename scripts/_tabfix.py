import re

path = 'main.tex'
content = open(path, encoding='utf-8').read()
orig = content

replacements = [
    # L1901: table -> table*
    (r'\\begin\{table\}\[!t\]\n(.*?)\\begin\{tabular\}\{lcccc\}\n(.*?)\\end\{tabular\}\n(.*?)\\end\{table\}',
     lambda m: m.group(0).replace(r'\begin{table}[!t]', r'\begin{table*}[!t]')
                          .replace(r'\begin{tabular}{lcccc}', r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccc}')
                          .replace(r'\end{tabular}', r'\end{tabular*}')
                          .replace(r'\end{table}', r'\end{table*}')),
]

# Simpler approach: direct string replacements per table
fixes = [
    # Table at L1901 (lcccc, 4 numeric cols)
    (r'\begin{table}[!t]' + '\n' + r'\centering' + '\n',
     r'\begin{table*}[!t]' + '\n' + r'\centering' + '\n',
     1908),  # approximate search window
]

# Do targeted replacements by finding unique anchor strings
patches = [
    # L1909 table: {lcccc}
    (r'\begin{tabular}{lcccc}',
     r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccc}'),
    (r'\end{tabular}' + '\n' + r'\end{table}' + '\n' + r'\label{tab:aggregation_results}',
     r'\end{tabular*}' + '\n' + r'\end{table*}' + '\n' + r'\label{tab:aggregation_results}'),

    # L1978 table: p{5cm}rc  
    (r'\begin{tabular}{>{\raggedright\arraybackslash}p{5cm}rc}',
     r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{7cm}rc}'),
]

# Find the label names for each table
lines = content.splitlines()
table_info = {}
for i, l in enumerate(lines):
    if r'\label{tab:' in l:
        lbl = l.strip()
        # find enclosing \begin{table}
        for j in range(i, max(0,i-50), -1):
            if r'\begin{table' in lines[j]:
                table_info[lbl] = (j+1, lines[j].strip())
                break

print("Table labels found:")
for k, v in sorted(table_info.items()):
    print(f"  L{v[0]}: {v[1]} -> {k[:60]}")
