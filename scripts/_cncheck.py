lines = open(r'figures/src/fig_workflow.html', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'cn-left' in l or 'cn-right' in l or 'border-top: 11px' in l:
        print(f'{i}: {l.rstrip()[:100]}')
