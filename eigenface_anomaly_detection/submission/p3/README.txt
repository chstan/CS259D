1. General Approach and Analysis 
Our general approach to the problem was to start with well-known baseline algorithms with the features as the columns of the csv to gauge the difficulty of the problem. For this, we tried to K-means cluster the data and to classify the problem using a multi-class decision tree. 

K-means Analysis
The K-means cluster provided no insight into the groupings of the training data. We saw that different trials from the same user would be classified under several different clusters. This was true even when decreasing the cluster count. In addition, we felt that clustering by itself was not a satisfactory approach for the nature of the problem, since we wanted to be able to classify each of the test trials as a certain user (and for the extra credit, we wanted to be able to have a quantitative measurement as to how "close" each user was to the test data).


Decision Tree Analysis
The multi-class decision tree fared better. Again, we ran the algorithm on a feature vector with the unmodified columns from the original training csv. In order to test the accuracy of the predictions, we used cross-validation, training on ~90% of the training data and testing on the remaining ~10%. This yielded an error rate of 37% (all false negatives, since we didn't have any masqueraders), which is much better than the guessing error rate of ~98%. Again, we were not satisfied with the fact that the decision tree algorithm cannot tell relative closeness of users to test data. Also, we wanted to do better than 37% error rate. 


Modified Approach 1
In this approach, we introduced the concept of "distance" by using what is known as degree of disorder in an array [1]. The overall idea is that the absolute difference between typing speeds between two trials is not indicative of a user (since the user could be typing under various conditions) but that the relative typing speeds moving from key to key is better [3]. Essentially, we measure the DD time between n-grams in the typing sequence (in our case a trigram: the DD time between a key press and the key press two after) and then sort the resulting times. Then the "distance" between trials is measured as the sum of the differences between the relative positioning of the elements in the two arrays, normalized by max distance. 

For each user, we created a "profile" containing all the sorted sequences from the training trials. In order to test/classify a sequence, we calculated the distance between the test sequence and each sequence in a given user profile and computed the average distance. With this, we had a measure for how close a test sequence was to a certain user. We classified each sequence as the user which gave the minimum average distance.

Using cross-validation, this process yielded an ~70% error rate. We believed that this was because we did not have enough features (8 since the password was 9 characters long) to differentiate from the ~50 users.


Modified Approach 2
To modify our approach, we added in other n-grams to increase the number of features [3]. We tested on various combinations of bigrams, trigrams, 4-grams, and 5-grams. We decided to stick with using bigrams and trigrams combined. This lowered the error rate to ~60%. We found that using 4-grams and 5-grams didnt add in too much information in terms of lowering the error rate and only served to increase runtime of the algorithm.


Modified Approach 3
Perplexed that we were not getting error rates comparable or better than the decision tree algorithm, we decided that we still needed to incorporate a sense of the absolute speed (not just relative) of a user's key presses. Thus, we decided to add an additional term to our distance definition. We added an additional term that represented the fraction of times (H, DD, or UD) that were "close" between two sequences. The closeness term was parameterized and was ultimately set at 1.25. This represented what the ratio of the larger time and smaller time needed to be smaller than. We call this the "absolute distance" and the distance from before as "relative distance". We also parameterized the weighting of the two distances. We ultimately decided on 0.4 for "relative distance" and 0.6 for "absolute distance". Using this new distance, we obtained 21% error rate. 


2. Feature Selection
As mentioned above, our features were:
all bigrams (DD between consecutive keys), sorted
all trigrams (DD between first and third keys in all sequences), sorted
all columns (H, DD, UD) from csv

The bigrams and trigrams contributed to our measure of relative distance between two sequences. The regular columns contributed to our measure of absolute distance between two sequences. Overall, this provided a good measure of relative and absolute typing patterns of a user. 


3. Successes and Failures
We believe that feature selection overall was a success. We were able to incorporate the absolute typing speed as well as the relative speed for each key subsequence for each user. As we incrementally improved our algorithm, the error rate was lowered. Also, our error rate for having the right label in the top 5 was only 6%. However, we are still dissatisfied with the error rate. Perhaps there are other features that we could have explored (i.e. right-handedness vs left-handedness...). Also, having a longer password sequence would have helped. The main problem we saw was that our algorithm still had problems differentiating between ~50 users with the number of features we had. Here is a table of our error rates from toggling the closeness and weighting parameters: (unfortunately, we were not able to generate an ROC curve since we had no knowledge of masqueraders and thus false positives)

closeness threshold		weighting (for relative dist term)		error rate
1.15					0.3 									0.228431372549
1.2 					0.3 									0.221568627451
1.25 					0.3  									0.226470588235
1.15					0.35									0.230392156863
1.2 					0.35 									0.223529411765
1.25 					0.35  									0.223529411765
1.15					0.4										0.230392156863
1.2 					0.4 									0.21862745098
1.25 					0.4  									0.21862745098
1.2 					0.5										0.228431372549
1.25 					0.5 									0.222549019608
1.3 					0.5  									0.228431372549
1.2 					0.6										0.25
1.25 					0.6 									0.25
1.3 					0.6  									0.246078431373

4. References
[1] User Authentication through Keystroke Dynamics by Bergadano, Gunetti, and Picardi
[2] Keystroke Analysis of Free Text by Gunetti and Picardi
[3] A k-Nearest Neighbor Approach for User Authentication through Biometric Keystroke Dynamics by Gingrich and Sentosa