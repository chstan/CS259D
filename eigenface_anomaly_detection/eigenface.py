import scipy.linalg as scl
import numpy as np
import random
import math
from itertools import permutations

from scipy.sparse.linalg.eigen.arpack import eigsh
from collections import OrderedDict, Counter
from itertools import chain

def userNames(n):
    return ["User" + str(i) for i in range(1, n+1)]

def getFileFromName(name):
    with open ('hw1/' + name) as user_file:
        return [command.strip() for command in user_file.readlines()]

def userFilesMap(n):
    return { name: getFileFromName(name) for name in userNames(n) }

def buildSmallCommandDictionary(command_lists, n_most_common, n_random):
    """ Build a command dictionary (command -> index) with the n_most_common
        most common found commands along with an additional n_random randomly
        selected ones."""
    c = Counter(chain(*command_lists))

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

def calculateNetworks(cooccurs, m_cooccurs, eigen_mats):
    norm_cooccurs = cooccurs - m_cooccurs
    n_layers = eigen_mats.shape[0]
    fis = eigen_mats.dot(norm_cooccurs.ravel())
    for i in range(n_layers - 1, -1, -1):
        print buildNetworkLayer(fis[i]*eigen_mats[i], 0, 50)

if __name__ == "__main__":
    num_eigen = 20
    num_users = 50
    train_length = 5000
    test_length = 10000
    sequence_length = 100
    keep_most_common = 130  #this seems to be minimal to
                           #prevent losing "too much" info
    keep_random = 0
    num_train_seq = train_length/sequence_length
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

    P = calculateCovariance(norm_vec_cooccurs)
    Pk = P.shape[0]

    print "Calculating eigenvectors"
    #eig_vals, eig_vecs = scl.eigh(P, eigvals = (Pk - num_eigen, Pk - 1))
    eig_vals, eig_vecs = eigsh(P, num_eigen, which="LM")
    print eig_vecs.shape;
    calculateNetworks(train_cooccurs[0], mean, np.transpose(eig_vecs))
