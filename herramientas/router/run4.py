from core import *
import time, pickle, json, os
t=time.time()
R=setup(); B=R.B
order=default_order(B)
af=route_all(R,order); af.update(R.pre_fail)
print('initial',count(af),af,f'{time.time()-t:.0f}s',flush=True)
pickle.dump((B.segs,B.vias,R.viol,af),open('init4.pkl','wb'))
af=repair(R,af,rounds=int(os.environ.get('ROUNDS','2')))
print('FINAL',count(af),af,f'{time.time()-t:.0f}s')
print('viol',len(R.viol),R.viol[:10])
pickle.dump((B.segs,B.vias,R.viol,af),open('final4_%s_%s.pkl'%(os.environ.get('VIACOST'),os.environ.get('ROUNDS')),'wb'))
