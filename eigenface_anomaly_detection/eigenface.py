import matplotlib.pyplot as plt
import scipy.linalg as scl
import numpy as np
#import mdp
import random
import math
import time

from itertools import permutations
from sklearn.decomposition import PCA

#from scipy.sparse.linalg.eigen.arpack import eigsh
from collections import OrderedDict, Counter
from itertools import chain

def userNames(n):
    return ["User" + str(i) for i in range(1, n+1)]

def getFileFromName(name):
    with open ('hw1/' + name) as user_file:
        return [command.strip() for command in user_file.readlines()]

def userFilesMap(n):
    return { int(name[4:]): getFileFromName(name) for name in userNames(n) }

def buildSmallCommandDictionary(command_lists, n_most_common, n_random):
    """ Build a command dictionary (command -> index) with the n_most_common
        most common found commands along with an additional n_random randomly
        selected ones."""
    c = Counter(chain(*command_lists))
    print "There are ", str(len(c)), " total commands."
    filtered_commands = [k for k, v in c.most_common(n_most_common)]
    rest = list(set(c.keys()).difference(set(filtered_commands)))
    random.shuffle(rest)
    selected_commands = filtered_commands + rest[:n_random]
    return {k: i for k, i in zip(selected_commands, range(len(selected_commands)))}


def buildCommandDictionary(command_lists):
    ks = OrderedDict.fromkeys(chain(*command_lists)).keys()
    return {k: i for k, i in zip(ks, range(len(ks)))}

def splitSequence(s, k):
    for i in xrange(0, len(s), k):
        yield s[i:i+k]

def totalExpectedPairs(k, d):
    """ Computes the number of expected co-occurrence pairs in a sequence of
        length k with interaction distance d. Used to compute a normalization
        factor in buildCooccurrence"""
    return d * (k - d) + d * (d-1) / 2

def buildCooccurrence(seq, d, dictionary):
    """ Seq is the input sequence of words to parse into the co occurence
        matrix. The maximum distance of interaction is d, and the dictionary
        is used to translate words to indices. This function does not assume
        that all the encountered words are in the dictionary."""

    k = len(dictionary)
    m = np.zeros((k, k))
    for idx_max in range(len(seq)):
        for idx in range(max(0, idx_max - d), idx_max):
            if seq[idx] not in dictionary or seq[idx_max] not in dictionary:
                continue
            x = dictionary[seq[idx]]
            y = dictionary[seq[idx_max]]
            m[x, y] += 1

    # Compute the appropriate normalization
    t = np.sum(m)
    t0 = totalExpectedPairs(len(seq), d)
    if t/t0 < 0.1:
        print "OH GOD"
    tf = t0/t
    if t == 0:
        tf = 0
    return m * tf

def calculateCovariance(vecs):
    vec_mat = np.matrix(vecs)
    return vec_mat.T * vec_mat

def minRep(t):
    i = t.index(min(t))
    return t[i:] + t[:i]

def loadReference():
    with open("hw1/reference.txt", "r") as f:
        lines = f.readlines()
        integers = [[int(token) for token in line.split()] for line in lines]
        return zip(*integers)

def pathInGraph(g,p):
    if len(p) == 1:
        return True
    else:
        return p[1] in g[p[0]] and pathInGraph(g,p[1:])

def cycleInGraph(g,t):
    return pathInGraph(g,t + (t[0],))

def buildTuplesFromGraph(g, r):
    """ Finds all the r-cycles in the directed graph g by brute force."""
    s = set()
    for t in permutations(g.keys(), r):
        if cycleInGraph(g, t):
            s.add(minRep(t))
    return s

def buildNetworkLayer(mat, cut, r):
    k = int(math.sqrt(mat.shape[0]))
    ind = np.argpartition(mat.ravel(), -r)[-r:]
    g = {}
    for i in range(r):
        idx = ind[i]
        idx_y = idx % k
        idx_x = (idx - idx_y) / k
        if idx_x in g:
            g[idx_x].append(idx_y)
        else:
            g[idx_x] = [idx_y]

    return buildTuplesFromGraph(g, 3)

def userSimilarity(user, seq):
    return max([sequenceSimilarity(user_seq, seq) for user_seq in user])

def sequenceSimilarity(seqA, seqB):
    acc = 0
    for i in range(len(seqA)):
        acc += netSimilarity(seqA[i], seqB[i])
    return acc

def netSimilarity(netA, netB):
    if len(netA) <= len(netB):
        little, big = netA, netB
    else:
        little, big = netB, netA
    acc = 0
    for elem in little:
        if elem in big:
            acc += 1
    return acc

def calculateNetworks(cooccurs, m_cooccurs, eigen_mats):
    norm_cooccurs = cooccurs - m_cooccurs
    n_layers = eigen_mats.shape[0]
    fis = norm_cooccurs.ravel().dot(np.transpose(eigen_mats))
    return [buildNetworkLayer(fis[j]*eigen_mats[j],0,30) for j in range(n_layers)]

def rmLsCooccurrence(d, m):
    k = int(math.sqrt(m.shape[0]))
    idx_rm = d["rm"]
    idx_ls = d["ls"]
    return m[idx_ls + idx_rm*k]

def calculateUserNetworks(user_num, train_cooccurs, eigen_mats, mean, n_train):
    return [calculateNetworks(train_cooccurs[i + user_num*n_train], mean,
                              eigen_mats) for i in range(50)]

def calculateTestNetworks(user_num, test_cooccurs, eigen_mats, mean, n_test):
    return [calculateNetworks(test_cooccurs[user_num][i], mean, eigen_mats) for i in range(n_test)]

def calculateBeta(l):
    idx = int(len(l)*0.1)
    return sorted(l)[idx] - 10

def analyzeTestScore(guessed, actual):
    """Guessed and actual are bitlists with 0s for
       the actual use and 1s for masqueraders. This function
       returns a tuple: (true positive rate, true negative rate,
                         false positive rate, false negative rate)
                      :  identified real user, identified masquerader,
                         misidentified as user, misidentified as masquerader"""
    num_masquerader = sum(actual)
    if actual[0] == -1:
        return (0,0,0,0,) # THIS WAS THE UNLABELED SEQUENCE

    total = len(actual)
    num_user = total - num_masquerader
    tpr = float(sum([((1-g)*(1-a)) for g,a in zip(guessed, actual)])) / num_user
    fnr = float(sum([((g)*(1-a)) for g,a in zip(guessed, actual)])) / num_user
    if num_masquerader != 0:
        tnr = float(sum([((g)*(a)) for g,a in zip(guessed, actual)])) / num_masquerader
        fpr = float(sum([((1-g)*(a)) for g,a in zip(guessed, actual)])) / num_masquerader
    else:
        tnr = 0
        fpr = 0
    return (tpr, tnr, fpr, fnr,)



if __name__ == "__main__":
    num_eigen = 200
    num_users = 50
    train_length = 5000
    test_length = 10000
    sequence_length = 100
    keep_most_common = 200  #this seems to be minimal to
                           #prevent losing "too much" info
    keep_random = 0
    num_train_seq = train_length/sequence_length
    num_test_seq = test_length/sequence_length
    window_len = 6

    users_and_files = userFilesMap(num_users)

    command_dict = buildSmallCommandDictionary(users_and_files.values(),
                                               keep_most_common, keep_random)

    # still need to split the data into training sets and test sets
    users_and_files = {u: list(splitSequence(users_and_files[u], sequence_length)) for \
                       u in users_and_files }

    # siphon off the training data and concatenate in one list
    train_seq = []
    for user in users_and_files:
        train_seq.extend(users_and_files[user][:num_train_seq])

    train_cooccurs = [buildCooccurrence(seq, window_len, command_dict) for seq in train_seq]
    mean = np.mean(train_cooccurs, axis=0)

    norm_train_cooccurs = [t - mean for t in train_cooccurs]
    norm_vec_cooccurs = [n.ravel() for n in norm_train_cooccurs]

    # print cooccurrence of rm and ls for Users 1 and 2.
    # Use the first five sequences for each
    for i in range(0, 5):
        print "User 1 Set", str(i+1), "rm-ls cooccurrence: ", \
            rmLsCooccurrence(command_dict, train_cooccurs[i].ravel())

    for i in range(num_train_seq, 5+num_train_seq):
        print "User 2 Set", str(i-num_train_seq+1), "rm-ls cooccurrence: ", \
            rmLsCooccurrence(command_dict, train_cooccurs[i].ravel())

    # AND NORMALIZED
    print "NORMALIZED"
    for i in range(0, 5):
        print "User 1 Set", str(i+1), "rm-ls cooccurrence: ", \
            rmLsCooccurrence(command_dict, norm_vec_cooccurs[i])

    for i in range(num_train_seq, 5+num_train_seq):
        print "User 2 Set", str(i-num_train_seq+1), "rm-ls cooccurrence: ", \
            rmLsCooccurrence(command_dict, norm_vec_cooccurs[i])

    #P = calculateCovariance(norm_vec_cooccurs)
    #Pk = P.shape[0]

    start = time.clock()
    print "Calculating eigenvectors"
<<<<<<< HEAD
    #eig_vals, eig_vecs = scl.eigh(P, eigvals = (Pk - num_eigen, Pk - 1))
    eig_vals, eig_vecs = eigsh(P, num_eigen, which="LM")
    print eig_vecs.shape;
    calculateNetworks(train_cooccurs[0], mean, np.transpose(eig_vecs))
=======
    pca = PCA(n_components = num_eigen)
    print "########################"
    print len(norm_vec_cooccurs)
    print len(norm_vec_cooccurs[0])
    pca.fit(norm_vec_cooccurs)
    print "FINISHED: ", (time.clock() - start)
    contributions = np.cumsum(pca.explained_variance_ratio_)
    #plt.plot(range(1,len(contributions) + 1), contributions)
    #plt.title("Variance of first k eigen-matrices")
    #plt.xlabel("# eigen-matrices")
    #plt.ylabel("Explained variance (sum of eigenvalues)")
    #plt.savefig("P2_eigenvalue_contribution.pdf")

    #start = time.clock()
    #print "Calculating eigenvectors"
    #pca = mdp.nodes.NIPALSNode(output_dim = 50)
    #pca.train(np.array(norm_vec_cooccurs))
    #pca.stop_training()
    #print pca.output_dim
    #print pca.explained_variance
    #print "FINISHED: ", (time.clock() - start)

    # first 50 seem to be sufficient
    start = time.clock()
    eigen_mats = np.array(pca.components_[:50])
    #eigen_mats = np.appary(pca.v)
    print "Finding the feature vectors for (e):"
    fVs = []
    for i in range(0, 5):
        fVs.append(np.array(norm_vec_cooccurs[i]).dot(np.transpose(eigen_mats)).tolist())
    with open("csvs/User1FV.csv", "w+") as f:
        f.write("\n".join([", ".join([str(ff) for ff in fi]) for fi in fVs]))

    fVs = []
    for i in range(num_train_seq, 5+num_train_seq):
        fVs.append(np.array(norm_vec_cooccurs[i]).dot(np.transpose(eigen_mats)).tolist())
    with open("csvs/User2FV.csv", "w+") as f:
        f.write("\n".join([", ".join([str(ff) for ff in fi]) for fi in fVs]))

    print "Building networks for each of the original users"
    train_nets = [calculateUserNetworks(user_num, train_cooccurs, eigen_mats,
                                  mean, num_train_seq) for user_num in range(50)]
    print "FINISHED: ", (time.clock() - start)

    print "Preparing test samples."
    test_seqs = [users_and_files[user][num_train_seq:] for user in range(1,50+1)]
    test_cooccurs = [[buildCooccurrence(seq, window_len, command_dict) for seq in u] for u in test_seqs]
    test_nets = [calculateTestNetworks(user_num, test_cooccurs, eigen_mats,
                                       mean, num_test_seq) for user_num in range(50)]
    print "Finished preparing test samples."

    # OH GOD PLEASE GIVE ME MY MAP BACK
    print "Preparing training scores."
    train_scores = []
    for user_num in range(50):
        user_seqs = train_nets[user_num]
        scores = []
        for user_seq in user_seqs:
            scores.append(userSimilarity(user_seqs, user_seq))
        train_scores.append(scores)

    print "Calculating betas."
    betas = [calculateBeta(scores) for scores in train_scores]

    print "Calculating test scores."
    test_scores = []
    test_acceptances = []
    for user_num in range(50):
        test_set_user = test_nets[user_num]
        scores = []
        acceptances = []
        for test_seq in test_set_user:
            # test_seq is the ith test data point for the user given by user_num
            current_score = userSimilarity(train_nets[user_num], test_seq)
            scores.append(current_score)
            if current_score > betas[user_num]:
                # score accepted as legitimate, which is 0
                acceptances.append(0)
            else:
                acceptances.append(1)
        test_scores.append(scores)
        test_acceptances.append(acceptances)

    reference = loadReference()

    # NOTE THAT 21 IS BOGUS
    print "Calculating rates."
    true_pos = [1]
    false_pos = [1]
    all_rates = [analyzeTestScore(g,a) for g,a in zip(test_acceptances, reference)]
    for delta_beta in range(-50, 50):
        ex_acceptances = []
        for user_num in range(50):
            ex_accept = []
            for test_num in range(100):
                if test_scores[user_num][test_num] > (betas[user_num] + delta_beta):
                    ex_accept.append(0)
                else:
                    ex_accept.append(1)
            ex_acceptances.append(ex_accept)

        with open("rates/21_" + str(delta_beta+50) + ".txt", "w+") as f:
            f.write(", ".join([str(r) for r in ex_acceptances[20]]))

        ar = [analyzeTestScore(g,a) for g,a in zip(ex_acceptances, reference)]
        with open("rates/rates_" + str(delta_beta+50) + ".txt", "w+") as f:
            f.write("\n".join([str(f) for f in ar]))

        with open ("rates/pred_" + str(delta_beta+50) + ".txt", "w+")  as f:
            f.write("\n".join([", ".join([str(tt) for tt in u]) for u in ex_acceptances]))

        rc = reference[:]
        del ex_acceptances[20]
        del rc[20]

        ts = analyzeTestScore(list(chain(*ex_acceptances)),
                              list(chain(*rc)))
        true_pos.append(ts[0])
        false_pos.append(ts[2])
        with open("rates/overall_" + str(delta_beta+50) + ".txt", "w+") as f:
            f.write(str(ts))

    true_pos.append(0)
    false_pos.append(0)

    plt.plot(false_pos, true_pos)
    plt.title("ROC Curve for Scheme Described in Paper")
    plt.xlabel("False positive rate (masqueraders identified as user)")
    plt.ylabel("True positive rate (user rightly identified)")
    plt.savefig("ROC_P2.pdf")

    test_acceptances_copy = test_acceptances[:]
    reference_copy = reference[:]

    del test_acceptances_copy[20]
    del reference_copy[20]


    print betas
    print test_acceptances

    print analyzeTestScore(list(chain(*test_acceptances_copy)),
                           list(chain(*reference_copy)))

    print "USER 21 ACCEPTANCES:"
    print test_acceptances[20]

    with open("rates.txt", "w+") as rates_file:
        rates_file.write("\n".join([str(l) for l in all_rates]))
>>>>>>> fecfae17a3cc0a28ec095a81ea32b53c327ed08b
