with open('refs.bib','r',encoding='utf-8') as f: text=f.read()
old = r"Watr\'{o}bski"
new = r"W{\k{a}}tr\'obski"
n = text.count(old)
text = text.replace(old, new)
with open('refs.bib','w',encoding='utf-8') as f: f.write(text)
print(f'{n} replacements in refs.bib')
