import numpy as np
from collections import OrderedDict
from itertools import chain

def userNames(n):
    return ["User" + str(i) for i in range(1, n+1)]

def getFileFromName(name):
    with open ('hw1/' + name) as user_file:
        return [command.strip() for command in user_file.readlines()]

def userFilesMap(n):
    return { name: getFileFromName(name) for name in userNames(n) }

def buildCommandDictionary(command_lists):
    ks = OrderedDict.fromkeys(chain(*command_lists)).keys()
    return {k: i for k, i in zip(ks, range(len(ks)))}

def splitSequence(s, k):
    for i in xrange(0, len(s), k):
        yield s[i:i+k]

def buildCooccurrence(seq, d, dictionary):
    """ Seq is the input sequence of words to parse into the co occurence
        matrix. The maximum distance of interaction is d, and the dictionary
        is used to translate words to indices."""

    k = len(dictionary) # much bigger than I would like. :(
    m = np.zeros((k, k))
    for idx_max in range(len(seq)):
        for idx in range(max(0, idx_max - d), idx_max):
            x = dictionary[seq[idx]]
            y = dictionary[seq[idx_max]]
            m[x, y] += 1
    #print "done"
    return m

def meanMatrices1(matrices):
    return np.mean(matrices, axis=0)

def meanMatrices2(matrices):
    return np.mean(matrices)
    #TODO

def normalizeMatrices(matrices):
    mean = meanMatrices1(matrices)
    print mean
    return [matrix - mean for matrix in matrices]

if __name__ == "__main__":
    num_users = 50
    train_length = 5000
    test_length = 10000
    sequence_length = 100
    num_train_seq = train_length/sequence_length
    window_len = 6

    users_and_files = userFilesMap(num_users)

    command_dict = buildCommandDictionary(users_and_files.values())

    # still need to split the data into training sets and test sets
    users_and_files = {u: list(splitSequence(users_and_files[u], sequence_length)) for \
                       u in users_and_files }

    # syphon off the training data and concatenate in one list
    train_seq = []
    for user in users_and_files:
        train_seq.extend(users_and_files[user][:num_train_seq])

    train_cooccurs = [buildCooccurrence(seq, window_len, command_dict) for seq in train_seq]
    #norm_train_cooccurs = normalizeMatrices(train_cooccurs)
    #print buildCooccurrence(users_and_files['User1'][0], 3, command_dict)