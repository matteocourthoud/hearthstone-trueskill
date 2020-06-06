#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 13:45:21 2017

@author: Matteo
"""
import json, os, sys
import pandas as pd


# Get the database with all the cards
def GetCardDatabase():
    path = '/Users/macbook/Dropbox/Code/Python/HS'
    with open(path+"/cardDB.json", encoding='utf-8') as json_data:
        db = json.load(json_data)
    cardDB = {}
    for card in db:
        cardDB[card['id']] = card
    return cardDB





# Function that updates the database
def GenNewLine(game):
    newline = pd.DataFrame()
    newline['game_id'] = [game.ID]
    newline['mode'] = [game.mode]
    newline['player'] = [game.player]
    newline['player_me'] = [(game.players[game.player] == 'MattFTW')]
    newline['turn'] = [game.turn]
    newline['card_name'] = [game.currCard['name']]
    
    newline['cards_drawn_self'] = [game.totCardsDrawn[game.player]]
    newline['cards_played_self'] = [game.totCardsPlayed[game.player]]
    newline['mana_spent_self'] = [game.manaSpent[game.player]]
    newline['class_self'] = [game.classes[game.player]]
    newline['health_self'] = [game.health[game.player]]
    newline['secrets_self'] = [game.secrets[game.player]]
    newline['last_winprob_self'] = [game.winProb[game.player]]
    newline['last_card_self'] = [game.lastCard[game.player]['name']]
    newline['board_n_self'] = [game.boardN[game.player]]
    newline['board_atk_self'] = [game.boardATK[game.player]]
    newline['board_hp_self'] = [game.boardHP[game.player]]
    
    newline['cards_drawn_oppo'] = [game.totCardsDrawn[3-game.player]]
    newline['cards_played_oppo'] = [game.totCardsPlayed[3-game.player]]
    newline['mana_spent_oppo'] = [game.manaSpent[3-game.player]]
    newline['class_oppo'] = [game.classes[3-game.player]]
    newline['health_oppo'] = [game.health[3-game.player]]
    newline['secrets_oppo'] = [game.secrets[3-game.player]]
    newline['last_winprob_oppo'] = [game.winProb[3-game.player]]
    newline['last_card_oppo'] = [game.lastCard[3-game.player]['name']]
    newline['board_n_oppo'] = [game.boardN[3-game.player]]
    newline['board_atk_oppo'] = [game.boardATK[3-game.player]]
    newline['board_hp_oppo'] = [game.boardHP[3-game.player]]
    
    newline['win_hat'] = [0.5]
    newline['winner'] = [-1]
    return newline.reindex_axis(sorted(newline.columns), axis=1)
    
       


# Save database
def SaveDatabase(game):
    path = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Add to other games
    try:
        with open(path+'/gameDB.json') as infile:
            data = json.load(infile)
        main_db = pd.read_json(data)
        
        if game.ID not in main_db['game_id'].unique():
            main_db = main_db.append(game.DB)
        else:
            print("GAME ALREADY RECORDED! Skipping...")
            return
        
    except: 
        main_db = game.DB
        print("Generating new database")
    
    print("ADDING %s GAME %s" % (game.mode, game.ID))
    main_db = main_db.sort_values(['game_id', 'turn'], ascending=[0, 1])
    main_db.index = range(len(main_db))
    with open(path+'/gameDB.json', 'w') as outfile:    
        json.dump(main_db.to_json(), outfile)

    
    
    





# Import the dataset
def ImportData(mode, dataset=None): 
    path = '/Users/macbook/Dropbox/Code/Python/HS'
    if dataset=='skill':
        with open(path+'/skillDB.json') as infile:
            data = json.load(infile)
        return pd.read_json(data).sort_index() 
    with open(path+'/gameDB.json') as infile:
        data = json.load(infile)
    main_db = pd.read_json(data).sort_index()
    if mode!='ALL':
        main_db = main_db[main_db['mode']==mode]
    return main_db
   
    

