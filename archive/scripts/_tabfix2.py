import re

path = 'main.tex'
content = open(path, encoding='utf-8').read()
orig = content

def fix_table(content, label, old_env, new_env, old_tab, new_tab):
    """Convert table -> table* for a specific label."""
    # Find the table block containing this label
    # Replace \begin{table}[...] -> \begin{table*}[...]
    # Replace \begin{tabular}{spec} -> \begin{tabular*}{\textwidth}{...}
    # Replace \end{tabular} -> \end{tabular*}
    # Replace \end{table} -> \end{table*}
    
    # Find position of label
    pos = content.find(label)
    if pos < 0:
        print(f"  LABEL NOT FOUND: {label}")
        return content
    
    # Find the \begin{table opening before this label
    start = content.rfind(r'\begin{table}', 0, pos)
    if start < 0:
        print(f"  TABLE BEGIN NOT FOUND for {label}")
        return content
    
    # Find the \end{table} after the label
    end = content.find(r'\end{table}', pos)
    if end < 0:
        print(f"  TABLE END NOT FOUND for {label}")
        return content
    end += len(r'\end{table}')
    
    block = content[start:end]
    new_block = block.replace(r'\begin{table}', r'\begin{table*}', 1)
    new_block = new_block.replace(old_tab, new_tab, 1)
    new_block = new_block.replace(r'\end{tabular}', r'\end{tabular*}', 1)
    new_block = new_block.replace(r'\end{table}', r'\end{table*}', 1)
    
    if new_block == block:
        print(f"  NO CHANGE for {label} (col spec not found?)")
    else:
        print(f"  OK: {label}")
    
    return content[:start] + new_block + content[end:]

# tab:tvorder L1901 {lcccc}
content = fix_table(content, r'\label{tab:tvorder}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{lcccc}',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccc}')

# tab:effects L1973 {p{5cm}rc}
content = fix_table(content, r'\label{tab:effects}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{>{\raggedright\arraybackslash}p{5cm}rc}',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{7.5cm}rc}')

# tab:assembly L2034 {llrc}
content = fix_table(content, r'\label{tab:assembly}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{llrc}',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llrc}')

# tab:coding2x2 L2128 {llcc}
content = fix_table(content, r'\label{tab:coding2x2}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{llcc}',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llcc}')

# tab:e1 L2283 {lccccc}
content = fix_table(content, r'\label{tab:e1}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{lccccc}',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccccc}')

# tab:e6summary L2383 {lrr}
content = fix_table(content, r'\label{tab:e6summary}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{lrr}',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lrr}')

# tab:amprefset L2173 {llcc}
content = fix_table(content, r'\label{tab:amprefset}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{llcc}',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llcc}')

# tab:factorial L1948 if it has overflow
content = fix_table(content, r'\label{tab:factorial}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}')

# tab:exponent L1447
content = fix_table(content, r'\label{tab:exponent}',
    r'\begin{table}', r'\begin{table*}',
    r'\begin{tabular}{',
    r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

changed = content.count(r'\begin{table*}') - orig.count(r'\begin{table*}')
print(f"\nTotal table* conversions: {changed}")
print("Done.")
