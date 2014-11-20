import scipy as sc
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import math

# parses into startDate, startHour, startMin, startSec, durHour, durMin, durSec, serv, srcPort, destPort, srcIP, destIP 
def importLog(log):
	with open (log) as f:
		return [access.replace(":r","**").replace(':',' ').replace("**", ":r").strip().split(' ')[1:] for access in f.readlines()]

# finds anomolies in access frequencies 
def findAccessAnomalies(data):
	# breaks down minute-long intervals from data
	intervalDict = {}
	for access in data:
		# breaks to 10-second intervals
		seconds = int(access[3])
		seconds = seconds - (seconds%10)

		key = (int(access[1]), int(access[2]), seconds)
		if key in intervalDict:
			intervalDict[key].append(access)
		else:
			intervalDict[key] = [access]

	totAccess = [len(intervalDict[key]) for key in intervalDict]
	totAccessMean = sc.mean(totAccess)
	totAccessVar = sc.var(totAccess)
	# print totAccessMean
	# print totAccessVar

	clientAccess = []
	clientDict = {}
	for key in intervalDict:
		count = Counter([access[10] for access in intervalDict[key]])
		for ckey in count:
			clientAccess.append(count[ckey])
			clientDict[(key[0], key[1], key[2], ckey)] = count[ckey]

	clientAccessMean = sc.mean(clientAccess)
	clientAccessVar = sc.var(clientAccess)
	# print clientAccessMean
	# print clientAccessVar

	clientAttackProb = {}
	for key in clientDict:
		totProb = totAccessVar/pow((totAccessMean-len(intervalDict[(key[0],key[1],key[2])])),2)
		clientProb = clientAccessVar/pow((clientAccessMean-clientDict[key]),2)
		prob = (totProb + clientProb)/2
		clientAttackProb[key] = prob

	arr = []
	for i in range(10):
		minKey = min(clientAttackProb, key=clientAttackProb.get)
		arr.append((minKey, clientAttackProb[minKey]))
		clientAttackProb.pop(minKey, None)
	return arr

# calculate the normalized entropy for the given data array
def calcNormEntropy(data):
	count = Counter(data)
	total = len(data)
	h = 0
	for key in count:
		pkey = float(count[key])/total
		h += -pkey*math.log(pkey, 2)
	if h != 0:
		h /= math.log(len(count.keys()),2)
	return h

# returns a dictionary of arrays of intervals of time length n minutes, extracts the entry-th entry from the row
def getIntervals(data, n, entry):
	intervalDict = {}
	for access in data:
		# breaks to 10-second intervals
		minutes = int(access[2])
		minutes = minutes - (minutes%n)

		key = (int(access[1]), minutes)
		if key in intervalDict:
			intervalDict[key].append(access[entry])#.split('.')[0])
		else:
			intervalDict[key] = [access[entry]]#.split('.')[0]]
	return intervalDict

if __name__ == "__main__":
	log_file = "server-log.txt"
	data = importLog(log_file)
	inter = getIntervals(data,5,6) #also want 7; (5,6) find first attack lol...

	entropy = [(key[0], key[1], calcNormEntropy(inter[key])) for key in inter]
	entropy.sort()

	plt.plot([ent[0]*100+ent[1] for ent in entropy], [ent[2] for ent in entropy])
	plt.show()









	