#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  2 18:51:46 2017

@author: Matteo
"""

from sklearn.kernel_approximation import RBFSampler
from sklearn.linear_model import LogisticRegression, SGDClassifier, Lasso, RidgeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, AdaBoostClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB


import json, time
import pandas as pd
import numpy as np
from predict import GetCLF, PredictWinner, CleanData
from data import ImportData
    
    



# Get the ratings for a class in a mode
def GetRatings(mode,hero):
    path = '/Users/macbook/Dropbox/Code/Python/HS/'
    with open(path+'skillDB.json') as infile:
        db = pd.read_json(json.load(infile)).sort_index()
    db = db[db['mode']==mode]
    db = db[db['class_self']==hero]
    print(db[db['player_me']==1][['card_name','copies','mean','stdev']].sort_values('mean', ascending=False))
   






# Update winning probabilities with new clf
def UpdateWinProb():
    
    path = '/Users/macbook/Dropbox/Code/Python/HS/'
    with open(path+'gameDB.json') as infile:
        db = pd.read_json(json.load(infile)).sort_index()


    clfs = {'DRAFT':GetCLF('DRAFT'), 
        'TOURNAMENT':GetCLF('TOURNAMENT')}    

    gameID = ''  
    winprob = {1: 0.5, 2: 0.5}  
    for i in range(len(db)): 
        if i%10==0:
            print(i)
        current_gameID = db[db.index==i]['game_id'].as_matrix()[0]
        mode = db[db.index==i]['mode'].as_matrix()[0]
        curr_player = db[db.index==i]['player'].as_matrix()[0]
        if current_gameID != gameID:
            winprob = {1: 0.5, 2: 0.5}  
            gameID = current_gameID
        db.loc[i,'last_winprob_self'] = winprob[curr_player]
        db.loc[i,'last_winprob_oppo'] = winprob[3-curr_player]
        temp_db = db[db.index==i]
        clf = clfs[mode][0]
        cols= clfs[mode][1]
        win_prob = PredictWinner(temp_db, clf, cols)
        db.loc[i,'win_hat'] = win_prob
        winprob[curr_player] = win_prob
        
    '''
    with open(path+'gameDB.json', 'w') as outfile:    
        json.dump(db.to_json(), outfile)
    '''
        



# Test CLF
def TestCLF(mode, reps=1):
    start_time = time.time()
    scores = []
    for i in range(reps):
        training_data = ImportData(mode)
    
        X_train, X_test, y_train, y_test = CleanData(training_data, split=True)
    
        print('Fitting %s obs with %s predictors' % (len(X_train),len(X_train.columns)))
        #      WEIGHTED KNN: 0.56 (+/- 0.06) in 16.70s
        #clf = KNeighborsClassifier(n_neighbors=10, weights='distance').fit(X_train, y_train)
        #      BOOSTING: 0.59 (+/- 0.11) in 298.21s
        clf = GradientBoostingClassifier(max_features='auto', n_estimators=100, max_depth=8).fit(X_train, y_train)
        #      LOGISTIC REGRESSION: Accuracy: 0.58 (+/- 0.11) in 23.32s
        #clf = LogisticRegression(C=0.1, n_jobs=-1).fit(X_train, y_train)
        #      RIDGE REGRESSION: 0.60 (+/- 0.11) in 49.34s
        #clf = RidgeClassifier(tol=1e-2, solver="lsqr").fit(X_train, y_train)
        #      SUPPORT VECTOR MACHINE: 0.56 (+/- 0.06) in 199.77s
        #clf = SVC(C=1).fit(X_train, y_train)
        #      NAIVE BAYES: 0.56 (+/- 0.11) in 14.74s
        #clf = GaussianNB().fit(X_train, y_train)
        #      RANDOM FOREST: 0.61 (+/- 0.11)
        #clf = RandomForestClassifier(n_estimators=100, criterion='entropy', max_depth=20, n_jobs=-1)
        #      EXTRA TREES: 0.56 (+/- 0.10) in 127.97s
        #clf = ExtraTreesClassifier(max_features='auto', n_estimators=500, max_depth=3).fit(X_train, y_train)
        scores += cross_val_score(clf, X_test, y_test, scoring='accuracy', cv=10, n_jobs=-1).tolist()
    print("Accuracy: %0.2f (+/- %0.2f) in %0.2fs" % (np.mean(scores), np.std(scores), time.time() - start_time))






###################### FUNCTIONS ######################

if __name__ != '__main__':

    # Get ratings
    GetRatings('DRAFT', 'DRUID')
    
    # Testing clf: best result RandomForestClassifier = 0.69
    TestCLF('TOURNAMENT', reps = 10)




