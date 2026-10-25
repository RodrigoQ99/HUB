from core import *
import time, pickle, json, os
t=time.time()
R=setup(verbose=False); B=R.B
order=default_order(B)
front=os.environ.get('FRONT','N08734').split(',')
order=[n for n in front if n in order]+[n for n in order if n not in front]
af=route_all(R,order); af.update(R.pre_fail)
print('initial',count(af),af,f'{time.time()-t:.0f}s',flush=True)
af=repair(R,af,rounds=int(os.environ.get('ROUNDS','3')))
print('FINAL',count(af),af,f'{time.time()-t:.0f}s')
pickle.dump((B.segs,B.vias,R.viol,af),open('final5_%s.pkl'%os.environ.get('TAG','a'),'wb'))
