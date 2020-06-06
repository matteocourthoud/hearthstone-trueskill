#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 10:44:29 2017

@author: Matteo
"""


import time, re, sys, os
from game import NewGame
from data import GetCardDatabase
from predict import GetCLF
from logreader import ReadEvent




# Continuous reader
def follow(thefile):
    while True:
        line = thefile.readline()
        if not line:
            thefile.seek(0,2)
            time.sleep(0.1)
            continue
        yield line
        
        


# Main part of the script: reading the log file
def ReadGame(file):
    # Setup
    gameStart = re.compile("^D ([\\S]+) .* - CREATE_GAME")
    cardDB = GetCardDatabase()
    game = NewGame()

    # Read logfile
    loglines = follow(file)
    for event in loglines:
        
        if game.over:
            # Get new game
            gameInfo = gameStart.findall(event)
            if len(gameInfo):
                game = NewGame()
                game.ID = gameInfo[0]
                game.mode = game.GetGameMode()
                game.over = False
                game.clf, game.clf_vars = GetCLF(game.mode)
                print('\nNEW GAME: %s, %s MODE' % (game.ID, game.mode))
        
        else:
            # Read lines
            ReadEvent(event, game, cardDB)
        







# Main
if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(path)
    logfile = open("/Applications/Hearthstone/Logs/Power.log","r",encoding='utf-8')
    ReadGame(logfile)
