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

if __name__ == "__main__":
    num_users = 50
    sequence_length = 100

    users_and_files = userFilesMap(num_users)

    command_dict = buildCommandDictionary(users_and_files.values())

    # still need to split the data into training sets and test sets
    users_and_files = {u: splitSequence(users_and_files[u], sequence_length) for \
                       u in users_and_files }

    print list(users_and_files['User1'])[0]
