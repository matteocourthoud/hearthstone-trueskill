#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 11:07:06 2017

@author: Matteo
"""

from datetime import datetime
import pandas as pd
import re

# Define a game
class NewGame():

    def __init__(self):
        self.ID = ''
        self.over = True
        self.players = {1: '', 2: ''}
        self.classes = {1: '', 2: ''}
        self.health = {1: 30, 2: 30}
        self.manaSpent = {1: 0, 2: 0}
        self.cardsDrawn = {1: 0, 2: 0, 'turn': 0}
        self.totCardsDrawn = {1: 0, 2: 0}
        self.totCardsPlayed = {1: 0, 2: 0}
        self.lastCard = {1: {'name':'None'}, 2: {'name':'None'}}
        self.secrets = {1: 0, 2: 0}
        self.boardN = {1: 0, 2: 0}
        self.boardATK = {1: 0, 2: 0}
        self.boardHP = {1: 0, 2: 0}
        self.boardCards = {1: [], 2: []}
        self.lastCardRevealed = {}
        self.lookingFor = None
        self.addCard = False
        self.newTurn = True
        self.turn = 0
        self.player = 1
        self.currCard = {'player': 0, 'name':'None'}
        self.winner = ''
        self.mode = 'UNKNOWN'
        self.DB = pd.DataFrame()
        self.clf = None
        self.clf_vars = None
        self.winProb = {1: 0.5, 2: 0.5}


    def playerFromName(self,string):
        for n, player in self.players.items():
            if player==string: return n


    # Update the board
    def UpdateBoard(self):
        self.boardN = {1: 0, 2: 0}
        self.boardATK = {1: 0, 2: 0}
        self.boardHP = {1: 0, 2: 0}
        for player in [1,2]:
            for card in self.boardCards[player]:
                self.boardN[player] += 1
                self.boardATK[player] += card['attack']
                self.boardHP[player] += card['health']



    # Update stats of a card on board
    def UpdateStats(self, card_id, player, stat, value):
        for card in self.boardCards[player]:
            if card['id']==card_id:
                if stat=='ATK':
                    card['attack'] = value
                if stat=='HEALTH':
                    card['health'] = value
                if stat=='DAMAGE' and card['health']>value:
                    card['health'] -= value
                    print('    %s takes %s damage' % (card['name'], value) )
                elif stat!='DAMAGE':
                    print('    %s %s changed to %s' % (card['name'], stat.lower(), value) )
                self.UpdateBoard()
                return


    # Remove a card from the board
    def RemoveCard(self, card):
        try:
            self.boardCards[self.player].remove(card)
        except:
            try:
                self.boardCards[3-self.player].remove(card)
            except:
                pass


    # Print the board
    def PrintBoard(self, pl):
        string = ("%s: HP(%s) MS(%s) CD(%s) CP(%s) BRD(%s: %s/%s)" %
              (self.players[pl], self.health[pl], self.manaSpent[pl], self.totCardsDrawn[pl],
               self.totCardsPlayed[pl], self.boardN[pl], self.boardATK[pl], self.boardHP[pl]))
        return string



    # Get game mode
    def GetGameMode(self):
        findMode = re.compile("([0-9\\:]+)\\.[0-9]+ .* prevMode=([\\S]+) nextMode=GAMEPLAY")
        loadScreenLog = open("/Applications/Hearthstone/Logs/LoadingScreen.log","r",encoding='utf-8')
        for line in reversed(list(loadScreenLog)):
            mode = findMode.findall(line)
            if len(mode):
                time = datetime.strptime(mode[0][0], '%H:%M:%S')
                time = time.hour*60+time.minute
                gametime = datetime.strptime(self.ID[0:8], '%H:%M:%S')
                gametime = gametime.hour*60+gametime.minute
                if gametime in range(time,time+2):    
                    return mode[0][1]
        return 'UNKNOWN'
