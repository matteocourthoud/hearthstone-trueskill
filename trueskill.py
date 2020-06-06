# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.

"""

import json, os, sys
import numpy as np
import pandas as pd
from scipy.stats import norm
from data import ImportData




# V: mean multiplicative factor
def VExceedsMargin(teamPerformanceDifference, draw_margin):
    denominator = norm.cdf(teamPerformanceDifference - draw_margin)
    if (denominator < 1e-162):
        return -teamPerformanceDifference + draw_margin
    return norm.pdf(teamPerformanceDifference - draw_margin)/denominator




# W: variance multiplicative factor
def WExceedsMargin(teamPerformanceDifference, draw_margin):
    denominator = norm.cdf(teamPerformanceDifference - draw_margin)
    if (denominator < 1e-162):
        if (teamPerformanceDifference < 0.0):
            return 1
        return 0
    vWin = VExceedsMargin(teamPerformanceDifference, draw_margin)
    return vWin*(vWin + teamPerformanceDifference - draw_margin)






# Update player ratings
def UpdatePLayerRatings(new_ratings, self_team, oppo_team):
    
    draw_margin = 0
    beta_squared = np.square(25/6)
    tau_squared = np.square(25/300)
    
    n_players = len(self_team) + len(oppo_team)

    c = np.sqrt(np.square(self_team['stdev'].mean()) + np.square(oppo_team['mean'].mean()) + n_players*beta_squared)
    
    if self_team['winner'].mean()==1:
        delta = self_team['mean'].mean() - oppo_team['mean'].mean()
        rank_multiplier = +1
    else:
        delta = oppo_team['mean'].mean() - self_team['mean'].mean()
        rank_multiplier = -1
    
    v = VExceedsMargin(delta, draw_margin)
    w = WExceedsMargin(delta, draw_margin)
    
    
    # Update rating of each member of the team
    for index, row in self_team.iterrows():
        
        previous_player_mean = row['mean']
        previous_player_stdev = row['stdev']
        
        mean_multiplier = (np.square(previous_player_stdev) + tau_squared)/c
        stdev_multiplier = (np.square(previous_player_stdev) + tau_squared)/np.square(c)
        
        player_mean_delta = rank_multiplier*mean_multiplier*v
        new_mean = previous_player_mean + player_mean_delta
        
        new_stdev = np.sqrt((np.square(previous_player_stdev) + tau_squared)*(1 - w*stdev_multiplier))
        
        new_player_ratings = pd.DataFrame({
                'card_name': [row['card_name']],
                'player_me': [row['player_me']],
                'class_self': [row['class_self']],
                'mode': [row['mode']],
                'copies': [1],
                'mean': [new_mean],
                'stdev': [new_stdev]})
        if len(new_ratings)>1:
            if row['card_name'] in new_ratings['card_name'].unique():
                new_player_ratings['copies']=[2]
        new_ratings = new_ratings.append(new_player_ratings)    
    
    return new_ratings
    

    
    
    
    
# Calculate the skills of the players of two teams after a game (win/loss, no draw)
# Teams are pandas-dataframes
def TwoTeamTrueSkillCalculator(game):
    
    # Check copies
    game.DB = game.DB.reset_index(drop=True)
    game.DB['copies'] = 1
    for player in [1,2]:
        for i in range(1,len(game.DB)):
            card = game.DB['card_name'].as_matrix()[i]
            sub_df = game.DB[:i-1]
            if ((sub_df['card_name'] == card) & (sub_df['player'] == player)).any():
                game.DB = game.DB.set_value(i,'copies',2)
    
    
    # Add ratings
    try:
        df_skills = ImportData(game.mode, dataset='skill')
        df_skills_merge = df_skills.set_index(['card_name','player_me','class_self','copies','mode'])
        del df_skills_merge['game_id']
        game.DB = game.DB.join(df_skills_merge, on=['card_name','player_me','class_self','copies','mode'])
    except:
        df_skills = pd.DataFrame({'card_name':[], 'copies':[], 'player_me':[], 'class_self':[], 'mode':[], 'mean':[], 'stdev':[], 'game_id':[]})
        game.DB['mean'] = np.nan
        game.DB['stdev'] = np.nan
        print('ERROR! No skill dataset found. Generating one...')
    game.DB['mean'] = game.DB['mean'].fillna(value=25)
    game.DB['stdev'] = game.DB['stdev'].fillna(value=25/3)
    
    
    # Prepare data
    team1 = game.DB[(game.DB['player_me']==True) & (game.DB['card_name']!='Hero Power')]
    team2 = game.DB[(game.DB['player_me']==False) & (game.DB['card_name']!='Hero Power')]
    
    
    # Update data
    results = pd.DataFrame({'card_name':[], 'copies':[], 'player_me':[], 'class_self':[], 'mode':[], 'mean':[], 'stdev':[], 'game_id':[]})
    results = UpdatePLayerRatings(results, team1, team2)
    results = UpdatePLayerRatings(results, team2, team1)
    results['game_id'] = game.ID

    
    # Save data
    if game.ID not in df_skills['game_id'].unique():
        print(results[results['player_me']==1][['card_name','copies','mean','stdev']].sort_values('mean', ascending=False))
        df_skills = df_skills.append(results)
        df_skills = df_skills.drop_duplicates(subset = ['card_name','copies','player_me','class_self','mode'], keep='last')
        df_skills = df_skills.reset_index(drop=True)
        path = os.path.dirname(os.path.abspath(sys.argv[0]))
        with open(path+'/skillDB.json', 'w') as outfile:    
            json.dump(df_skills.to_json(), outfile)
    else:
        print("SKILLS ALREADY RECORDED! Skipping...")
    
    
    
    
    
    
