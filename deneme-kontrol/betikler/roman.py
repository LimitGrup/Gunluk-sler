# -*- coding: utf-8 -*-
import json, re
Q=json.load(open('questions.json'))
order=[]
for t,n in [('T1',40),('T2',46),('T3',40),('T4',40)]: order+=[f'{t}-{i}' for i in range(1,n+1)]
I=[];L=[]
for k in order:
    t=Q[k]['text']
    if re.search(r'(?<![A-Za-zÇĞİÖŞÜçğıöşü])I{1,3}\.\s', t): I.append((k,Q[k]['page']))
    if re.search(r'(?<![A-Za-zÇĞİÖŞÜçğıöşü])l{1,3}\.\s', t): L.append((k,Q[k]['page']))
print('BÜYÜK I ile (doğru):',len(I))
for k,p in I: print('   ',k,'s.'+str(p))
print('KÜÇÜK l ile (tutarsız):',len(L))
for k,p in L: print('   ',k,'s.'+str(p), repr(Q[k]['text'][:110]))
