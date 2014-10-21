import numpy as np
import csv
import re
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

if __name__ == "__main__":
	file_test = "hw1/KeyboardTestData.csv"
	file_train = "hw1/KeyboardData.csv"

	(trainVec, numId) = getTrainDataFromFile(file_train)
	(labels, featMat) = createFeatureMatrix(trainVec)

	#Estimate using K-means
	estimator1 = KMeans(init='k-means++', n_clusters=numId, n_init=10)
	clLabels = estimator1.fit_predict(featMat)

	with open("k_output.txt", "w") as fo:
		temp = [str(i)+"\n" for i in clLabels]
		fo.writelines(temp)

	#Estimate using Decision Tree Classification
	trainVec_train = getSublist(trainVec,300,376)
	trainVec_test = getSublist(trainVec,-300,376)
	(labels_train, featMat_train) = createFeatureMatrix(trainVec_train)
	(labels_test, featMat_test) = createFeatureMatrix(trainVec_test)

	estimator2 = tree.DecisionTreeClassifier()
	estimator2.fit(featMat_train, labels_train)

	dlabels = estimator2.predict(featMat_test)
	numIncorrect = 0
	total = len(dlabels)
	for i in range(len(dlabels)):
		if (dlabels[i] != labels_test[i]):
			numIncorrect += 1
	with open("dec_test_output.txt", "w") as fo:
		temp = ["predict: "+str(dlabels[i])+"   actual: "+str(labels_test[i])+"\n" for i in range(len(dlabels))]
		fo.writelines(temp)
		fo.writelines(["numIncorrect: "+str(numIncorrect), "   total: "+str(total), "   percent: "+str(float(numIncorrect)/total)])

	#Estimate using 




