# Enhancing Causal Estimation through Unlabeled Offline Data
Code library that regenerates the result in the Example section of the article "Enhancing Causal Estimation through Unlabeled Offline Data".

## Example 4.1, Synthetic example
run RnnEstimator.py to generate data and perform training and testing. Testing results are displayed in console and a figure

## Example 4.2, Enhancing real-time human activity recognition

### Download dataset
First download the human activity recognition dataset from
https://archive.ics.uci.edu/ml/machine-learning-databases/00344/, open the zip file and place it in a sub-library of the project named "Activity recognition exp".
The directory "Activity recognition exp" should contain the files "Phones_gyroscope.csv" and "Phones_accelerometer.csv" which is used to train the estimators.

### Data preprocessing
Run collectData.py to preprocess the CSV file. The data is resampled to a samling rate of 200 Herz. In the CSV file downloaded there is a single time-series for each combination of user and smartphone. We split this single time-series every time there is a gap of over 250ms between sequential data points.

### Train matched filters and smoothers
Run PhoneAnalysis.py to train a dedicated filters and a dedicated smoothers for each smartphone (LG-Nexus4, Samsung-S3, Samsung-S3mini).
The data is split randomly between train and validation sets in a ratio of 70% for train and 30% for validation. 
3 Independent trainings are performed on the same split and the best performing estimator is saved (best with respect to performance on the validation set).

First the single file 'phonesData.pt' that was generated in the previous section is split to separated, per-phone files such as "./nexus4_dataset".
Then the training starts during which the posterior probabilities assigned by the learned filters/smoothers to each category (walking, sitiing,...) 
is displayed to the screen at the end of each epoch. The probabilities are written both for the training set and the validation set.
Dedicated estimators are saved for each smartphone to files such as "sparse_smoother_trainedOn_nexus4_model.pt".
The model saved in sparse_smoother_trainedOn_nexus4_model.pt has two outputs, the first contains the causal estimations and the second the non-causal estimations.

### Train and test improved filters
Run PhoneCrossFilterTrain.py to train improved filters. 
These are train to reproduce the estimations made by the smoothers trained in the previous section. 
At the end of training figure 4 in "Enhancing Causal Estimation through Unlabeled Offline Data" is reproduced.
Dedicated estimators are saved for each smartphone to files such as "".




