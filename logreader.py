#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  9 14:56:52 2017

@author: Matteo
"""


import re
from data import GenNewLine, SaveDatabase
from predict import PredictWinner
from trueskill import TwoTeamTrueSkillCalculator





def ReadEvent(event, game, cardDB):
    # Setup regular expressions
    playerId= re.compile("id=([12]) Player=([\\S]+).*ChoiceType=MULLIGAN")
    gameEnd = re.compile("TAG_CHANGE Entity=GameEntity tag=STATE value=COMPLETE")
    findWinner = re.compile("TAG_CHANGE Entity=([\\S]+) tag=PLAYSTATE value=WON")
    findClass = re.compile("FULL_ENTITY - Updating \\[.* zone=PLAY zonePos=0 cardId=([\\S]+) player=([12])\\] CardID=HERO")

    keptInMulligan = re.compile("GameState.SendChoices\\(\\).*m_chosenEntities\\[.\\]=\\[.* id=([0-9]+) zone=HAND .* cardId=([\\S]+) player=([12])\\]")
    cardRevealed = re.compile("SHOW_ENTITY - Updating Entity=\\[name=UNKNOWN ENTITY \\[cardType=INVALID\\] id=([0-9]+) zone=([\\S]*).*player=([12])] CardID=([\\S]+)")
    cardMoved = re.compile("TAG_CHANGE Entity=\\[.* id=([0-9]+) zone=([\\S]*) .* cardId=([+\\S]*) player=([12])\\] tag=ZONE value=([\\S]*)")
    cardCreated = re.compile("FULL_ENTITY - Creating ID=([\\S][+\\S]*) CardID=([\\S][+\\S]*)")
    cardsDrawn = re.compile("TAG_CHANGE Entity=([\\S]*) tag=NUM_CARDS_DRAWN_THIS_TURN value=([0-9]+)")

    turn = re.compile("TAG_CHANGE Entity=(\\S[\\S]+) tag=CURRENT_PLAYER value=1")
    manaSpent = re.compile("TAG_CHANGE Entity=([\\S]*) tag=NUM_RESOURCES_SPENT_THIS_GAME value=([0-9]+)")
    heroHealth = re.compile("TAG_CHANGE Entity=\\[.* id=([0-9]+) zone=PLAY .* cardId=([\\S]*) player=([12])\\] tag=DAMAGE value=([0-9]+)")
    heroPower = re.compile("TAG_CHANGE Entity=(\\S[\\S]+) tag=HEROPOWER_ACTIVATIONS_THIS_TURN value=1")
    statsChange = re.compile("(.*) TAG_CHANGE Entity=\\[.* id=([0-9]+) zone=PLAY .* cardId=([\\S]*) player=([12])\\] tag=(ATK|HEALTH|DAMAGE) value=([0-9]+)")
    secretRevealed = re.compile("TAG_CHANGE Entity=\\[.* zone=SECRET .* cardId=([\\S][\\S]*) player=([12])\\] tag=ZONE value=GRAVEYARD")


    # Get player classes
    classInfo = findClass.findall(event)
    if len(classInfo):
        game.classes[int(classInfo[0][1])] = cardDB[classInfo[0][0]]['playerClass']
        print("Class of player %s is %s" % (classInfo[0][1], cardDB[classInfo[0][0]]['playerClass']))


    # Get info on stats changes
    statsInfo = statsChange.findall(event)
    if len(statsInfo):
        card_id = statsInfo[0][1]
        curr_card = cardDB[statsInfo[0][2]]
        card_owner = int(statsInfo[0][3])
        stat = statsInfo[0][4]
        value = int(statsInfo[0][5])
        if 'GameState' not in statsInfo[0][0] and stat=='DAMAGE':
            return
        elif (curr_card['type']=='MINION' or curr_card['type']=='WEAPON') and value>0:
            game.UpdateStats(card_id, card_owner, stat, value)


    # Get info on secrets popped
    secretInfo = secretRevealed.findall(event)
    if len(secretInfo):
        controller = int(secretInfo[0][1])
        game.card = cardDB[secretInfo[0][0]]
        if 'SECRET' in game.card['mechanics']:
            game.secrets[controller] -= 1
            print("    %s secret revealed: it's %s" % (game.players[controller], game.card['name']))



    # Ingore PowerTaskList event
    if re.search("PowerTaskList|PowerProcessor", event):
        return



    # Get turn info
    turnInfo = turn.findall(event)
    if len(turnInfo):
        game.turn += 1
        game.newTurn = True
        if game.turn == 1:
            game.totCardsDrawn = {1: 5, 2: 4}
        else:
            game.totCardsDrawn[1] += game.cardsDrawn[1]
            game.totCardsDrawn[2] += game.cardsDrawn[2]
            game.cardsDrawn = {1: 0, 2: 0, 'turn': game.turn}
        game.player = game.playerFromName((turnInfo[0]))
        print("NEW TURN: %s" % game.PrintBoard(game.player) )



    # Get info on the players
    playerInfo = playerId.findall(event)
    if len(playerInfo):
        game.players[int(playerInfo[0][0])] = playerInfo[0][1]



    # Health info
    healthInfo = heroHealth.findall(event)
    if len(healthInfo):
        if 'HERO' in healthInfo[0][1]:
            game.player = int(healthInfo[0][2])
            health = 30 - int(healthInfo[0][3])
            game.health[game.player] = health
            print("    %s health: %s" % (game.players[game.player], health) )



    # Get cards kept in mulligan
    mulliganKeeps = keptInMulligan.findall(event)
    if len(mulliganKeeps):
        print("    MattFTW keeps: %s" % cardDB[mulliganKeeps[0][1]]['name'])



    # Get cards drawn this turn
    totCardsDrawn = cardsDrawn.findall(event)
    if len(totCardsDrawn) and game.turn:
        game.player = game.playerFromName(totCardsDrawn[0][0])
        game.cardsDrawn[game.player] = int(totCardsDrawn[0][1])



    # Get total mana spent
    manaInfo = manaSpent.findall(event)
    if len(manaInfo):
        game.player = game.playerFromName(manaInfo[0][0])
        game.manaSpent[game.player] = int(manaInfo[0][1])



    # Get info on cards you draw
    drawInfo = cardRevealed.findall(event)
    if len(drawInfo):
        player_name = game.players[int(drawInfo[0][2])]
        if drawInfo[0][1] == "DECK" and player_name == 'MattFTW':
            game.lookingFor = "hand"
            game.card = cardDB[drawInfo[0][3]]
    zoneIsHand = re.search("tag=ZONE value=HAND",event)
    if zoneIsHand and game.lookingFor == "hand":
            game.lookingFor = None
            print("    MattFTW draws %s" % game.card['name'])



    # Get info on hero power
    heropowerInfo = heroPower.findall(event)
    if len(heropowerInfo):
        game.card = {'name': 'Hero Power', 'type': 'HERO_POWER'}
        game.player = game.playerFromName(heropowerInfo[0])
        game.addCard = True



    # Get info on cards generated
    creationInfo = cardCreated.findall(event)
    if len(creationInfo):
        game.card = cardDB[creationInfo[0][1]]
        game.card['id'] = creationInfo[0][0]
        game.lookingFor = "zone"
    zoneIsPlay = re.search("tag=ZONE value=PLAY",event)
    if zoneIsPlay and game.lookingFor == "zone":
        game.lookingFor = "controller"
    controllerInfo = re.findall("tag=CONTROLLER value=([12])",event)
    if len(controllerInfo):
        if game.lookingFor == "controller" and game.card['type']=='MINION':
            controller = int(controllerInfo[0])
            game.card['player'] = controller
            game.boardCards[controller] += [game.card]
            game.UpdateBoard()
            print("    %s enters the battlefield" % game.card['name'])
        game.lookingFor = None



    # Get info on cards revealed by opponent
    cardInfo = cardRevealed.findall(event)
    if len(cardInfo):
        game.player = int(cardInfo[0][2])
        game.card = cardDB[cardInfo[0][3]]
        game.card['id'] = cardInfo[0][0]
        if game.players[game.player]!='MattFTW' and game.card['type']!='ENCHANTMENT':
            game.lastCardRevealed = game.card
            game.lookingFor = "end_zone"
    zoneIsPlay = re.findall("tag=ZONE value=(PLAY|SECRET|DECK)",event)
    if len(zoneIsPlay):
        if game.lookingFor == "end_zone" and zoneIsPlay[0]!='DECK':
            game.addCard = True
        if game.lookingFor == "end_zone" and zoneIsPlay[0]=='DECK' and game.card['type']=='MINION':
            game.card['player'] = game.player
            game.boardCards[game.player] += [game.card]
            game.UpdateBoard()
            print("    %s enters the battlefield" % game.card['name'])
        game.lookingFor == None



    # Get info on the cards moved
    cardInfo = cardMoved.findall(event)
    if len(cardInfo):
        game.player = int(cardInfo[0][3])
        zoneTo = cardInfo[0][4]
        if len(cardInfo[0][2]):
            game.card = cardDB[cardInfo[0][2]]
            game.card['id'] = cardInfo[0][0]
            if zoneTo=='PLAY' and game.card!=game.lastCardRevealed:
                game.addCard = True
            if zoneTo=='GRAVEYARD' and (game.card['type']=='MINION' or game.card['type']=='WEAPON'):
                game.RemoveCard(game.card)
                game.UpdateBoard()
                print("    %s dies" % game.card['name'])
        elif zoneTo=='SECRET' and game.players[game.player]!='MattFTW':
            game.card = {'name': game.classes[game.player]+' Secret', 'type': 'SPELL', 'text': '<b>Secret:</b>'}
            game.addCard = True



    # Add card played to the database
    if game.addCard:
        # Update info
        game.card['player'] = game.player
        game.lastCard[game.currCard['player']] = game.currCard
        game.currCard = game.card
        if game.card['type']=='MINION':
            game.boardCards[game.player] += [game.card]
        if game.card['type']=='WEAPON':
            game.card['health'] = 0
            game.boardCards[game.player] += [game.card]
        if game.card['type']=='SPELL':
            if '<b>Secret:</b>' in game.card['text']:
                game.secrets[game.player] += 1
        game.UpdateBoard()
        game.totCardsPlayed[game.player] += 1
        # Predict outcome
        newline = GenNewLine(game)
        win_prob = PredictWinner(newline, game.clf, game.clf_vars)
        newline['win_hat'] = win_prob
        game.DB = game.DB.append(newline)
        game.winProb[game.player] = win_prob
        game.addCard = False
        print("    %s plays %s: winrate %s" % (game.players[game.player], game.card['name'], win_prob))



    # Get info on the winner
    winnerInfo = findWinner.findall(event)
    if len(winnerInfo):
        game.winner = game.playerFromName(winnerInfo[0])



    # End game
    if gameEnd.search(event):
        game.over = True
        if len(game.DB) and game.mode!='UNKNOWN' and game.winner!='':
            game.DB['winner'] = 1 - abs(game.DB['player'] - game.winner)
            SaveDatabase(game)
            TwoTeamTrueSkillCalculator(game)   # Refers to Microsoft TrueSkill algorithm
            print('GAME OVER!!! %s won \n' % game.players[game.winner])
        elif game.mode=='UNKNOWN':
            print("GAME NOT RECORDED! Game mode unknown...")
        elif game.winner=='':
            print("GAME OVER!!! It's a draw...")
        else:
            print("GAME NOT RECORDED! No cards played...")
        

