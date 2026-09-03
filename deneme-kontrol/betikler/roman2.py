# -*- coding: utf-8 -*-
import json,re
Q=json.load(open('questions.json'))
def cp(s): return ''.join(('[I]' if c=='I' else '[l]' if c=='l' else c) for c in s)
for n in range(30,41):
    k=f'T4-{n}'
    if k not in Q: continue
    t=Q[k]['text']
    seg=re.split(r'(?=\b[A-E]\))',t)
    opts=[s for s in seg if re.match(r'^[A-E]\)',s)]
    pre=t[:t.find(opts[0])] if opts else t
    print(f'--- {k} (s.{Q[k]["page"]}) ---')
    print('  ÖNCÜL:', cp(pre[:150]))
    for o in opts: print('  OPT :', cp(o.strip()[:60]))
