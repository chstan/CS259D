library("FSelector")
library("entropy")
library("infotheo")

features_frame <- read.csv("features/new_features.csv")
print("Here.")
features_frame[,36] <- discretize(features_frame[,36])
print("And Here.")
weights <- information.gain(features_frame)


is.na(features_frame) <- sapply(features_frame, is.infinite)
safe_features_frame <- features_frame[complete.cases(features_frame),]
feature_covariance <- cor(safe_features_frame)

write.csv(weights, "results/weights.csv")
write.csv(feature_covariance, "results/cor.csv")

print(weights)
print(feature_covariance)

