import warnings
from sklearn import preprocessing
import numpy as np
from sklearn import cross_validation
import sklearn.neighbors as neighbors

warnings.simplefilter("ignore")

paper_top_ten = (30,13,29,11,6,4,24,5,27,7,)
paper_top_ten_plus_two = (30,13,29,11,6,4,24,5,27,7,34,35,)
top_ten = (29, 30, 11, 5, 24, 6, 4, 14, 31, 3,)
top_ten_plus_two = (29, 30, 11, 5, 24, 6, 4, 14, 31, 3, 34, 35,)
all_thirty = (2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,)
all_thirty_plus_two = (2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,34,35)


def get_data_columns(arr):
    return (arr[:,paper_top_ten], arr[:,paper_top_ten_plus_two],
            arr[:,top_ten], arr[:, top_ten_plus_two],
            arr[:,all_thirty], arr[:, all_thirty_plus_two])

data = np.loadtxt(open("features/new_features.csv","rb"),delimiter=",",skiprows=1)

data = data[~np.isnan(data).any(axis=1)]
data = data[~np.isinf(data).any(axis=1)]

labels = [int(label) for label in data[:,0]]
data_scaled = preprocessing.scale(data)

datasets = get_data_columns(data_scaled)
dataset_names = ["paper_top_ten", "paper_top_ten_plus_two", "top_ten", "top_ten_plus_two", "all_thirty", "all_thirty_plus_two"]

unique_labels = sorted(list(set(labels)))

final_data = []

for dataset, dataset_name in zip(datasets, dataset_names):
    print "Training", dataset_name
    f1s = []
    precs = []
    recalls = []
    for current_user in unique_labels:
        c_labels = [int(label == current_user) for label in labels]
        print "Training classifiers for", current_user, " +Samples: ", sum(c_labels)

        seen_scores_precision = []
        seen_scores_recall = []
        seen_scores_f1 = []
        for current_k in range(1, 12):
            cv = cross_validation.StratifiedKFold(c_labels, 10)
            clf = neighbors.KNeighborsClassifier(current_k)
            scores_f1 = cross_validation.cross_val_score(clf, dataset, c_labels,
                                                         cv=cv, scoring='f1')
            scores_precision = cross_validation.cross_val_score(clf, dataset, c_labels,
                                                         cv=cv, scoring='precision')
            scores_recall = cross_validation.cross_val_score(clf, dataset, c_labels,
                                                         cv=cv, scoring='recall')
            score_f1 = np.mean(scores_f1)
            score_precision = np.mean(scores_precision)
            score_recall = np.mean(scores_recall)
            seen_scores_f1.append([score_f1, current_k])
            seen_scores_precision.append([score_precision, current_k])
            seen_scores_recall.append([score_recall, current_k])

        best_idx = -1
        best_f1 = -1
        for idx in range(len(seen_scores_f1)):
            if seen_scores_f1[idx][0] > best_f1:
                best_f1 = seen_scores_f1[idx][0]
                best_idx = idx

        best_precision = seen_scores_precision[best_idx][0]
        best_recall = seen_scores_recall[best_idx][0]
        best_k = seen_scores_precision[best_idx][1]

        precs.append(best_precision*sum(c_labels))
        recalls.append(best_recall*sum(c_labels))
        f1s.append(best_f1*sum(c_labels))

        final_data.append((current_user, dataset_name, best_f1, best_precision, best_recall, best_k))
        print (best_f1, best_precision, best_recall, best_k)
    print "f1", (sum(f1s)/len(labels))
    print "precision", (sum(precs)/len(labels))
    print "recall", (sum(recalls)/len(labels))


with open("results/results.txt", "w+") as f:
    lines = [", ".join([str(attr) for attr in line]) for line in final_data]
    f.write("UserID, Features, F1, Precision, Recall, k (kNN hyperparameter)\n")
    f.write("\n".join(lines))
