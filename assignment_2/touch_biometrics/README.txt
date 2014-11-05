How to run code:
    There are a few components to the code for this problem. Features are
    extracted by using the modified file extractFeatures.m. Information about
    the features including the information gain relative to the UserID and the
    covariance of all features with each other (except for those for which the
    data is all zeros, as in the change of finger orientation) can be computed
    by running the script bio_entropy.R via
        ~ R
        > source("bio_entropy.R")
    which outputs the vector of information gains for each feature and the
    covariances to the screen and writes them to CSV, included in this solution
    already computed. This script requires the packages infotheo and FSelector,
    both available on CRAN.

    The classifier that we trained can be run by running touch_biometrics.py.
    This script requires scikit-learn (package sklearn) which provides the kNN
    implementation as well as a useful utility for cross-validation.


Answers to the problem are available in analysis.txt.
