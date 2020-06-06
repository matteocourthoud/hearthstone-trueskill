#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  9 15:06:50 2017

@author: Matteo
"""

from sklearn import preprocessing
from sklearn.kernel_approximation import RBFSampler
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, AdaBoostClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB


import random
import pandas as pd
from data import ImportData
 



# Split dataset into X and Y
def CleanData(db, split=False, normalize=False):
    cat_vars = ['class_self','class_oppo','card_name']
    for var in cat_vars:
        dummy_db = pd.get_dummies(pd.Series(db[var]))
        dummy_db.rename(columns=lambda x: var+"_"+x, inplace=True)
        db = pd.concat([db,dummy_db], axis=1)
    
    
    
    # Gen additional variables
    db['win_margin'] = db['last_winprob_self'] - db['last_winprob_oppo']
    db['health_margin'] = db['health_self'] - db['health_oppo']
    db['mana_margin'] = (db['mana_spent_self'] - db['mana_spent_oppo'])/(db['turn']+1)
    db['cardsdrawn_margin'] = (db['cards_drawn_self'] - db['cards_drawn_oppo'])/(db['turn']+1)
    db['cardsplayed_margin'] = (db['cards_played_self'] - db['cards_played_oppo'])/(db['turn']+1)
    db['lethal_self'] = db['board_atk_self']>=db['health_oppo']
    db['lethal_oppo'] = db['board_atk_oppo']>=db['health_self']
    
    vars_todrop = ['game_id','winner','win_hat','mode','last_card_self','last_card_oppo']
    
    if split:
        train_ids = [game_id for game_id in db['game_id'].unique() if random.random()<0.7]
        test_ids = [game_id for game_id in db['game_id'].unique() if game_id not in train_ids]
        
        y_train = db.loc[db['game_id'].isin(train_ids), 'winner']
        y_test = db.loc[db['game_id'].isin(test_ids), 'winner']
        X_train = db[db['game_id'].isin(train_ids)]
        X_test = db[db['game_id'].isin(test_ids)]
        # Delete variables
        for var in cat_vars+vars_todrop:
            del X_train[var], X_test[var]
        return X_train, X_test, y_train, y_test
        
        
    else:
        y = db['winner'].as_matrix()
        X = db
        # Delete variables
        for var in cat_vars+vars_todrop:
            del X[var]
        return X,y




# Get the prediction function at the start of the game
def GetCLF(mode):
    try:
        training_data = ImportData(mode)
        _ = training_data['mode'].as_matrix()[0]
    except Exception as e:
        print("DATA NOT FOUND! Error:", e)
        return None, None

    X, y = CleanData(training_data, normalize=True)
    cols = list(X)

    print('\nFitting %s data on %s obs...' % (mode, len(training_data)))
    clf = ExtraTreesClassifier(max_features='auto', n_estimators=100, max_depth=3).fit(X, y)
    return clf, cols




# Predict the winner after card is played
def PredictWinner(db, clf, cols):
    if not clf or not cols: return 0.5

    X_test, y_test = CleanData(db, normalize=True)
    for col in list(X_test):
        if col not in cols:
            del X_test[col]

    X_test_clean = pd.DataFrame(columns = cols).append(X_test).fillna(value=0)
    y_hat = clf.predict_proba(X_test_clean)[-1][1]
    return round(y_hat, 2)

