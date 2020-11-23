import time
import numpy as np

def compute_clustering_coefficient(a):
	(n, m) = a.shape

	Ci = np.empty(n)

	Div = np.sqrt(1-np.multiply(a, a))
	Ridx1, Ridx2 = np.triu_indices(n, 1)
	mymask = np.ones((n, n), dtype=bool)

	for i in range(n):
		M = np.outer(a[i,:], a[i,:])
		D = np.outer(Div[i,:],Div[i,:])
		mymask[Ridx1, Ridx2] = False
		mymask[i, :] = True
		mymask[:,i] = True
		M1 = np.ma.array(np.fabs(M),mask=mymask)
		r1 = np.ma.array(a,mask=mymask)
		up1 = np.ma.subtract(r1, M)
		ro = np.ma.divide(up1, D)
		up2 = np.ma.multiply(M, ro)
		up2abs = np.ma.fabs(up2)
		sumUp = np.ma.sum(up2abs)
		sumDown = np.ma.sum(M1)
		Ci[i] = sumUp / sumDown

	Cglob = np.average(Ci)
	return Ci, Cglob

