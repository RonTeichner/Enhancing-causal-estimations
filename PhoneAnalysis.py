#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 10:22:05 2021

@author: 
"""
import sys
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split, Subset
from torchvision import transforms
import matplotlib.pyplot as plt
import pickle
import os
from sklearn.model_selection import train_test_split
import copy
from PhoneAnalysis_func import *


createPhoneDataset = True
enableTrain = True
enableSparse = True
enableTest = False
enableOverwriteStatistics = False

enableSmoothing = True

enablePlotTimeSeries = False

phoneAnalysisFileNamesTrainData = ['nexus4', 's3', 's3mini']
phoneAnalysisFileNameTestDataFiles = ['s3mini']  #['nexus4', 's3', 's3mini', 'samsungold', 'lgwatch', 'gear']  #['nexus4', 's3', 's3mini', 'samsungold', 'lgwatch', 'gear']  # {'s3', 'train_nexus4', 'lgwatch', 'gear'}
#phoneSavedModelFileNames = ['trainedOns3', 'trainedOns3mini'] # {'trainedOnNexus4', 'trainedOnLgWatch', 'trainedOnsamsungold', 'trainedOns3', 'trainedOns3mini' }
if enableSparse:
    sparseStr = 'sparse_'
else:
    sparseStr = ''


if enableSmoothing:
    phoneSavedModelFileNames = [sparseStr + 'smoother_trainedOn_' + phoneAnalysisFileNameTrainData for phoneAnalysisFileNameTrainData in phoneAnalysisFileNamesTrainData]
else:
    phoneSavedModelFileNames = [sparseStr + 'trainedOn_' + phoneAnalysisFileNameTrainData for phoneAnalysisFileNameTrainData in phoneAnalysisFileNamesTrainData]


fs = 1/0.005


if createPhoneDataset:    
    for phoneAnalysisFileNameTrainData in phoneAnalysisFileNamesTrainData:
        print(f'creating dataset')
        if phoneAnalysisFileNameTrainData == 'lgwatch':
            filePath = './Activity recognition exp/watchData.pt'  # {'./Activity recognition exp/phonesData.pt', './Activity recognition exp/watchData.pt'}
        else:
            filePath = './Activity recognition exp/phonesData.pt'  # {'./Activity recognition exp/phonesData.pt', './Activity recognition exp/watchData.pt'}
            
        modelList = [phoneAnalysisFileNameTrainData]  # ['nexus4', 's3', 'lgwatch', 'gear']
        
        phoneCompleteDataset = PhoneDataset(filePath, modelList)
        pickle.dump(phoneCompleteDataset, open(phoneAnalysisFileNameTrainData + '_dataset.pt', 'wb'))
    
if enablePlotTimeSeries:
    phoneAnalysisFileNameTrainData = phoneAnalysisFileNamesTrainData[-1]
    phoneCompleteDataset = pickle.load(open(phoneAnalysisFileNameTrainData + '_dataset.pt', 'rb'))
    phoneCompleteDataset.plotTimesSeries()
    
if enableTrain:
    for phoneAnalysisFileNameTrainData, phoneSavedModelFileName in zip(phoneAnalysisFileNamesTrainData, phoneSavedModelFileNames):
        enablePlots = False
        phoneCompleteDataset = pickle.load(open(phoneAnalysisFileNameTrainData + '_dataset.pt', 'rb'))
        
        model = phoneCompleteDataset.metaDataDf['Classification'].unique().tolist()[0]
        classes = phoneCompleteDataset.phonesDf['gt']
        values, counts = np.unique(classes, return_counts=True)
        counts = counts/counts.sum()
        values = ['noClass', 'stand', 'sit', 'walk', 'stairsup', 'stairsdown', 'bike']
        #plt.bar(values, counts)
        #plt.title(model)
        #plt.show()
        
        statisticsDict = {'classDistribution': (values, counts), 'mu': phoneCompleteDataset.mu, 'Sigma_minus_half': phoneCompleteDataset.Sigma_minus_half, 'Sigma_half': phoneCompleteDataset.Sigma_half}
        print(f'dataset contains {len(phoneCompleteDataset)} time series')
        
        # training properties:    
        trainOnNormalizedData = True    
        nTrainsForCrossValidation = 1
        nTrainsOnSameSplit = 3   # not more than 1 because train indices will not match
        batchSize = 8*10
        validation_fraction = 0.3
        nValidation = int(validation_fraction*len(phoneCompleteDataset))
        nTrain = len(phoneCompleteDataset) - nValidation
        
        allFeatures = phoneCompleteDataset.phonesDf.columns[3:-1].tolist()
        featuresIncludeInTrainIndices = [0, 1, 2]  
        
        # create the trained model
        print('creating model')
        if enableSparse:
            hidden_dim = 30 
        else:
            hidden_dim = 30 
        num_layers = 1
        nClasses = phoneCompleteDataset.phonesDf['gt'].unique().shape[0]
        useSelectedFeatures = True
        
        enableDataParallel = True
        
        modelDict = {'enableSparse': enableSparse, 'trainedOn': 'labeled data', 'smoother': enableSmoothing, 'nClasses': nClasses, 'hidden_dim': hidden_dim, 'num_layers': num_layers, 'useSelectedFeatures': useSelectedFeatures, 'allFeatures': allFeatures, 'featuresIncludeInTrainIndices': featuresIncludeInTrainIndices, 'nFeatures': phoneCompleteDataset.nFeatures, 'trainOnNormalizedData': trainOnNormalizedData, 'statisticsDict': statisticsDict, 'fs': 1/0.005}
        
        
        model_state_dict_list, validationLoss_list = list(), list()
        
        for trainIdx in range(nTrainsForCrossValidation):
            maxTrain_vs_validation_classDistributionDiff = np.Inf
            while maxTrain_vs_validation_classDistributionDiff > 25:  # a difference of 20% in one of the classes between train and validation
                trainData, validationData = random_split(phoneCompleteDataset,[nTrain, nValidation])
                if validation_fraction == 0: break
                # check if split is balanced:
                trainClasses = phoneCompleteDataset.phonesDf[phoneCompleteDataset.phonesDf['Id'].isin(trainData.indices)]['gt']
                values, counts = np.unique(trainClasses, return_counts=True)
                trainClassesFraction = np.round(100*counts/counts.sum())
                validationClasses = phoneCompleteDataset.phonesDf[phoneCompleteDataset.phonesDf['Id'].isin(validationData.indices)]['gt']
                values, counts = np.unique(validationClasses, return_counts=True)
                validationClassesFraction = np.round(100*counts/counts.sum())
                if not(validationClassesFraction.shape[0] == trainClassesFraction.shape[0]): continue
                validationClassesFraction_vs_trainClassesFraction = np.round(100*np.divide(np.abs(validationClassesFraction-trainClassesFraction), trainClassesFraction))
                maxTrain_vs_validation_classDistributionDiff = validationClassesFraction_vs_trainClassesFraction.max()
                print(f'max diff classes = {maxTrain_vs_validation_classDistributionDiff}')
                
            
            if validation_fraction > 0: 
                print(f'validation classes fraction {validationClassesFraction}')
                print(f'train classes fraction {trainClassesFraction}')
            trainLoader = DataLoader(trainData, batch_size=batchSize, shuffle=True, num_workers=0)        
            validationLoader = DataLoader(validationData, batch_size=batchSize, shuffle=True, num_workers=0)
            
            modelDict['datasetFile'] = phoneAnalysisFileNameTrainData + '_dataset.pt'
            modelDict['trainIndices'], modelDict['validationIndices'] = trainLoader.dataset.indices, validationLoader.dataset.indices
            pickle.dump(modelDict, open(phoneSavedModelFileName +  '_modelDict.pt', 'wb'))
            
            Filter_rnn = RNN_Filter(input_dim = len(modelDict['allFeatures']), hidden_dim=modelDict['hidden_dim'], output_dim=modelDict['nClasses'], num_layers=modelDict['num_layers'], modelDict=modelDict)
            
            # train:  
            validationLoss = np.inf
            for s in range(nTrainsOnSameSplit):
                print(f'starting training, attemp no. {s}')
                Filter_rnn.apply(init_weights)
                model_state_dict_s, validationLoss_s, _ = trainModel(Filter_rnn, trainLoader, validationLoader, phoneCompleteDataset, enableDataParallel, modelDict, enablePlots, 'train')
                if validationLoss_s < validationLoss:
                    validationLoss = validationLoss_s
                    model_state_dict = model_state_dict_s
                
            model_state_dict_list.append(model_state_dict)
            validationLoss_list.append(validationLoss)                
        
        # save the net with median performance:
        validationLoss_array = np.asarray(validationLoss_list)
        Ann_idx = np.argsort(validationLoss_array)[0]    
        torch.save(model_state_dict_list[Ann_idx], phoneSavedModelFileName + '_model.pt')
  