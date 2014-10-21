import numpy as np
import csv
import re
import sys
from itertools import chain

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn import tree

# returns array of vectors extracted from csv file at fname
def getTrainDataFromFile(fname):
	with open(fname, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=',')
		train = []
		dic = {}
		for row in reader:
			# deletes the 2nd and 3rd columns in the file
			del row[1]
			del row[1]

			# extracts user id from first column
			match = re.findall(r'\d+',row[0])
			if len(match) != 0:
				row[0] = int(match[0])
				dic[row[0]] = True
				train.append(row)
		return (train, len(dic))

# returns a matrix of feature vectors and corresponding labels extracted from the array of training vectors trvec
def createFeatureMatrix(trvec):
	# currently uses the training vectors as is
	feat = []
	labels = []
	for row in trvec:
		# remove user ids
		feat.append(row[1:])
		labels.append(row[0])
	return (labels, np.matrix(feat))

# returns a sublist of l containing the first n elements of each modulo chunk
def getSublist(l,n,modulo):
	if n > 0:
		return list(chain(*[x[:n-modulo] for x in list(zip(*[iter(l)] * modulo))]))
	else:
		return list(chain(*[x[-n-modulo:] for x in list(zip(*[iter(l)] * modulo))]))

def createNGrams(s, n):
	arr = []
	for i in range(len(s)-n+2):
		su = 0
		for j in range(n-1):
			su += float(s[i+j])
		arr.append(su)
	return arr

def createNGramsDictR(s):
	dic = {}
	for row in s:
		arr = createNGrams(row[1:][1::3], 2)+createNGrams(row[1:][1::3], 3)
		arr = [(arr[i],i) for i in range(len(arr))]
		arr.sort()
		dic2 = {}
		for i in range(len(arr)):
			dic2[arr[i][1]] = i;

		if row[0] in dic:
			dic[row[0]].append(dic2)
		else:
			dic[row[0]] = [dic2]
	return dic

def createNGramsDictA(s):
	dic = {}
	for row in s:
		arr = createNGrams(row[1:], 2)#+createNGrams(row[1:], 3)
		if row[0] in dic:
			dic[row[0]].append(arr)
		else:
			dic[row[0]] = [arr]
	return dic

def computeNGramDistR(s1, s2):
	su = 0
	for key in s1:
		su += abs(s1[key] - s2[key])
	mx = len(s1)*len(s1)/2
	su /= float(mx)
	return su

def computeNGramDistA(s1, s2, t):
	tot = len(s1)
	su = 0
	for i in range(len(s1)):
		if s1[i]*s2[i] > 0:
			if s1[i] > 0 and max(s1[i],s2[i])/min(s1[i],s2[i]) < t:
				su += 1
			elif s1[i] < 0 and min(s1[i],s2[i])/max(s1[i],s2[i]) < t:
				su += 1
	su /= float(tot)
	return su

def calcMeanDistR(tr):
	dic = {}
	for key in tr:
		ls = tr[key]
		num = 0
		su = 0
		for i in range(len(ls)):
			for j in range(len(ls)):
				if (j > i):
					num += 1
					su += computeNGramDistR(ls[i], ls[j])
		dic[key] = float(su/num)
	return dic

def ngramPredict(dicR, ngramR, dicA, ngramA, x, t):
	md = {}
	for key in dicR:
		su = 0
		tot = 0
		for row in dicR[key]:
			tot += 1
			su += computeNGramDistR(ngramR, row)
		md[key] = float(su/tot)

	for key in dicA:
		su = 0
		tot = 0
		for row in dicA[key]:
			tot += 1
			su += computeNGramDistA(ngramA, row, t)
		md[key] = x*float(md[key]) + (1-x)*(1-float(su)/tot)

	arr = []
	for i in range(5):
		minKey = min(md, key=md.get)
		arr.append(minKey)
		md.pop(minKey, None)
	return arr


if __name__ == "__main__":
	file_test = "hw1/KeyboardTestData.csv"
	file_train = "hw1/KeyboardData.csv"

	(trainVec, numId) = getTrainDataFromFile(file_train)
	(labels, featMat) = createFeatureMatrix(trainVec)

	#Estimate using K-means
	# estimator1 = KMeans(init='k-means++', n_clusters=numId, n_init=10)
	# clLabels = estimator1.fit_predict(featMat)

	# with open("k_output.txt", "w") as fo:
	# 	temp = [str(i)+"\n" for i in clLabels]
	# 	fo.writelines(temp)

	#Estimate using Decision Tree Classification
	# trainVec_train = getSublist(trainVec,300,376)
	# trainVec_test = getSublist(trainVec,-300,376)
	# (labels_train, featMat_train) = createFeatureMatrix(trainVec_train)
	# (labels_test, featMat_test) = createFeatureMatrix(trainVec_test)

	# estimator2 = tree.DecisionTreeClassifier()
	# estimator2.fit(featMat_train, labels_train)

	# dlabels = estimator2.predict(featMat_test)
	# numIncorrect = 0
	# total = len(dlabels)
	# for i in range(len(dlabels)):
	# 	if (dlabels[i] != labels_test[i]):
	# 		numIncorrect += 1
	# with open("dec_test_output.txt", "w") as fo:
	# 	temp = ["predict: "+str(dlabels[i])+"   actual: "+str(labels_test[i])+"\n" for i in range(len(dlabels))]
	# 	fo.writelines(temp)
	# 	fo.writelines(["numIncorrect: "+str(numIncorrect), "   total: "+str(total), "   percent: "+str(float(numIncorrect)/total)])

	#Estimate using Trigrams method
	trainVec_train = getSublist(trainVec,356,376)
	trainVec_test = getSublist(trainVec,-356,376)

	(testVec, numId) = getTrainDataFromFile(file_test)

	trainDictR = createNGramsDictR(trainVec_train)#trainVec)
	#trainMDist = calcMeanDistR(trainDict)
	trainDictA = createNGramsDictA(trainVec_train)#trainVec)

	with open("ngram_test_output_final.txt", "w") as fo, open("answer.csv", "w") as fo2, open("ec.txt", "w") as fo3:
		total = 0
		error = 0
		badError = 0
		for row in trainVec_test:#testVec:
			total += 1
			fo.writelines("test " + str(total) + "\n")
			label = row[0]
			fo.writelines("true label " + str(label) + "\n")

			arr = createNGrams(row[1:][1::3], 2)+createNGrams(row[1:][1::3], 3)
			arr = [(arr[i],i) for i in range(len(arr))]
			arr.sort()
			ngramR = {}
			for i in range(len(arr)):
				ngramR[arr[i][1]] = i;

			ngramA = createNGrams(row[1:], 2)#+createNGrams(row[1:], 3)

			pred = ngramPredict(trainDictR, ngramR, trainDictA, ngramA, 0.4, 1.25)
			fo.writelines("pred label " + str(pred[0]) + "\n")
			if label != pred[0]:
				fo2.writelines("1, ")
				fo3.writelines(str(pred[0]) + ", " + str(pred[1])+ ", " + str(pred[2])+ ", " + str(pred[3])+ ", " + str(pred[4]) + "\n")
				error +=1
				if label not in pred:
					badError += 1
			else:
				fo2.writelines("0, ")
				fo3.writelines("real\n")
			#sys.exit()
		fo.writelines("num bad error " + str(badError) + "\n")
		fo.writelines("num error " + str(error) + "\n")
		fo.writelines("total " + str(total) + "\n")
		fo.writelines("error rate " + str(float(error)/total) + "\n")

	# with open("ngram_test_output_param.txt", "w") as fo:
	# 	for x in [0.3, 0.35, 0.4]:
	# 		for t in [1.15, 1.2, 1.25]:
	# 			fo.writelines("x: " + str(x) + "\n")
	# 			fo.writelines("t: " + str(t) + "\n")
	# 			total = 0
	# 			error = 0
	# 			errorDic = {}
	# 			for row in trainVec_test:
	# 				total += 1
	# 				label = row[0]

	# 				arr = createNGrams(row[1:][1::3], 2)+createNGrams(row[1:][1::3], 3)
	# 				arr = [(arr[i],i) for i in range(len(arr))]
	# 				arr.sort()
	# 				ngramR = {}
	# 				for i in range(len(arr)):
	# 					ngramR[arr[i][1]] = i;

	# 				ngramA = createNGrams(row[1:], 2)#+createNGrams(row[1:], 3)

	# 				pred = ngramPredict(trainDictR, ngramR, trainDictA, ngramA, x, t)
	# 				if (label != pred):
	# 					if label in errorDic:
	# 						errorDic[label] += 1
	# 					else:
	# 						errorDic[label] = 1
	# 					error += 1
	# 			fo.writelines(str(errorDic) + "\n")
	# 			fo.writelines("num error " + str(error) + "\n")
	# 			fo.writelines("total " + str(total) + "\n")
	# 			fo.writelines("error rate " + str(float(error)/total) + "\n")
	# 			fo.writelines("\n\n\n")
	# 			print "done"
	

	







