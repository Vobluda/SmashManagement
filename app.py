import math
import pickle
import random  # for assigning seeds to random players

from flask import Flask, request, render_template, redirect

app = Flask(__name__, static_url_path='/static')
app.config.from_object('config')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


class Player:
    def __init__(self, ID, IGN, main, school, seed):
        self.ID = ID
        self.IGN = IGN
        self.main = main
        self.school = school
        self.seed = seed
        self.currentChar = None


class Game:
    def __init__(self, seedindex1, seedindex2):  # initialize an "empty" game without players
        self.ID = 0
        self.seedindex1 = seedindex1  # seed *index*, not the actual seed
        self.seedindex2 = seedindex2
        self.player1 = None
        self.player2 = None
        self.player1Char = None
        self.player2Char = None
        self.winner = None
        self.score = [0, 0]
        self.BO = 5

    def players(self, player1, player2, player1Char, player2Char, BO, name):
        self.player1 = player1
        self.player2 = player2
        self.player1Char = player1Char
        self.player2Char = player2Char
        self.BO = BO
        self.name = name


class Tournament:
    def __init__(self):
        self.rounds = []
        self.currentGame = None
        self.type = 'se'  # NEEDS TO BE CHANGED WHEN DOUBLE ELIM IS IMPLMENTED


class PlayerManager:
    def __init__(self):
        self.playerList = []
        self.ID = len(self.playerList) + 1
        self.currentGame = None
        self.tournament = None


manager = PlayerManager()


def backup(object, fileName):
    with open(fileName, 'wb') as openedFile:
        pickle.dump(object, openedFile)
        print('Backup succesful')


def readBackupPlayers(objectFile):
    with open(objectFile, 'rb') as openedFile:
        manager.playerList = pickle.load(openedFile)
    print('Backup of players retrieved')


def readBackupTournament(objectFile):
    with open(objectFile, 'rb') as openedFile:
        manager.tournament = pickle.load(openedFile)
    print('Backup of tournament retrieved')


def createSeeding(playerList):  # Find players whose seeds are missing and assign them free seeds randomly.
    seeds = [i.seed if (type(i.seed) == int) else 0 for i in
             playerList]  # iterate over the playerList and get the player seeds into one handy list. Non-ints are converted to 0.
    valid_seeds = [i for i in seeds if i > 0]  # make a list with only the valid seeds, a seed is valid if > 0
    missing_seed_indices = [i for i in range(len(seeds)) if
                            not seeds[i] > 0]  # make a list with the indices of players that have missing seeds
    current_seed_value = 1  # set the loop counter to 1, because it's the lowest valid seed
    while missing_seed_indices:  # loop while there are still some missing seeds (list is True unless empty)
        if current_seed_value not in valid_seeds:  # if the current seed value has not yet been used
            selected_player_index = random.choice(
                missing_seed_indices)  # pick a random player index with a missing seed
            playerList[selected_player_index].seed = current_seed_value  # assign the player the current seed value
            missing_seed_indices.remove(selected_player_index)  # remove the player's index from the list
        current_seed_value += 1  # increment the counter
    return playerList  # return the modified playerList


def areSeedsValid(
        playerList):  # Returns True if all seeds are valid but not unique (i.e. between 1 and the number of players)
    seeds = [i.seed if (type(i.seed) == int) else 0 for i in
             playerList]  # iterate over the playerList and get the player seeds into one handy list. Non-ints are converted to 0.
    return min(seeds) > 0 and max(seeds) <= len(
        playerList)  # returns True if the lowest and highest seed are between 1 and the number of players.


def areSeedsUnique(playerList):  # Returns True if players have unique seeds.
    seeds = [i.seed if (type(i.seed) == int) else 0 for i in
             playerList]  # iterate over the playerList and get the player seeds into one handy list. Non-ints are converted to 0.
    while 0 in seeds:
        seeds.remove(0)
    seedsUnique = seeds == list(set(
        seeds))  # compares the seeds list to a set of the seeds - converting to a set removes duplicates - True if unique
    return seedsUnique


def createSingleElimTemplate(playerNumber):
    roundNumber = int(math.ceil(math.log(playerNumber, 2)))  #find the lowest possible round number
    playerNumber = int(2 ** roundNumber)  # find the player number (including voids)
    template = Tournament()  # create a tournament object
    for currentRound in range(0, roundNumber):  # loop over the round indices
        template.rounds.append([])
        if currentRound == 0:
            template.rounds[currentRound] = [Game(1, 2)]
        else:
            for currentGame in range(int(2 ** currentRound)):
                if currentGame % 2 == 0:
                    seedindex1 = template.rounds[currentRound - 1][currentGame // 2].seedindex1
                else:
                    seedindex1 = template.rounds[currentRound - 1][currentGame // 2].seedindex2
                seedindex2 = int(2 ** (currentRound + 1)) + 1 - seedindex1
                template.rounds[currentRound].append(Game(seedindex1, seedindex2))
    template.rounds = template.rounds[::-1]
    gameIDCounter = 0
    for curr_round in template.rounds:
        for curr_game in curr_round:
            gameIDCounter += 1
            curr_game.ID = gameIDCounter
    return template


def createSingleElimTournament(playerList):
    playerList = createSeeding(playerList)
    roundNumber = int(math.ceil(math.log(len(playerList), 2)))  # find the lowest possible game number
    playerNumber = int(2 ** roundNumber)  # find the player number (including voids)
    while len(playerList) < playerNumber:
        playerList.append(Player(len(playerList) + 1, "Null", "Null", "Null", 0))
    playerList = createSeeding(playerList)
    tournament = createSingleElimTemplate(playerNumber)
    for current_seed in range(1, playerNumber + 1):
        player_with_seed = None
        game_seed_index = None
        seed_1_or_2 = None
        for current_seed_b in range(playerNumber):
            if playerList[current_seed_b].seed == current_seed:
                player_with_seed = playerList[current_seed_b]
            if tournament.rounds[0][current_seed_b // 2].seedindex1 == current_seed:
                game_seed_index = current_seed_b // 2
                seed_1_or_2 = 1
            if tournament.rounds[0][current_seed_b // 2].seedindex2 == current_seed:
                game_seed_index = current_seed_b // 2
                seed_1_or_2 = 2
        if seed_1_or_2 == 1:
            tournament.rounds[0][game_seed_index].player1 = player_with_seed
        elif seed_1_or_2 == 2:
            tournament.rounds[0][game_seed_index].player2 = player_with_seed
    return tournament


def createDoubleElimTemplate(playerNumber):
    # declare variables
    finalTournament = Tournament()

    # create upper bracket
    roundNumber = int(math.ceil(math.log(playerNumber, 2)))  # find the lowest possible round number
    playerNumber = int(2 ** roundNumber)  # find the player number (including voids)
    template = Tournament()  # create a tournament object
    for currentRound in range(0, roundNumber):  # loop over the round indices
        template.rounds.append([])
        if currentRound == 0:
            template.rounds[currentRound] = [Game(1, 2)]
        else:
            for currentGame in range(int(2 ** currentRound)):
                if currentGame % 2 == 0:
                    seedindex1 = template.rounds[currentRound - 1][currentGame // 2].seedindex1
                else:
                    seedindex1 = template.rounds[currentRound - 1][currentGame // 2].seedindex2
                seedindex2 = int(2 ** (currentRound + 1)) + 1 - seedindex1
                template.rounds[currentRound].append(Game(seedindex1, seedindex2))
    template.rounds = template.rounds[::-1]
    gameIDCounter = 0
    for curr_round in template.rounds:
        for curr_game in curr_round:
            gameIDCounter += 1
            curr_game.ID = gameIDCounter
    finalTournament.rounds.append(template)

    # create lower bracket
    roundNumber = int(2 * len(finalTournament.rounds[0].rounds) - 3)  # finds number of rounds
    playerNumber = int(2 ** roundNumber)  # find the player number (including voids)
    template = Tournament()  # create a tournament object
    wbCounter = 0
    for roundCounter in range(0, roundNumber):  # iterates until all rounds are created
        if roundCounter == 0:
            currentRound = []
            gameNumber = int(len(finalTournament.rounds[0].rounds[0]) / 2)
            for gameCounter in range(0, gameNumber):
                currentRound.append(Game(0, 0))
            template.rounds.append(currentRound)
            wbCounter += 1

        elif roundCounter % 2 == 1:
            currentRound = []
            gameNumber = int(len(finalTournament.rounds[0].rounds[wbCounter]) / 2) + int(
                len(template.rounds[roundCounter - 1]) / 2)
            for gameCounter in range(0, gameNumber):
                currentRound.append(Game(0, 0))
            template.rounds.append(currentRound)
            wbCounter += 1

        else:
            currentRound = []
            gameNumber = int(len(template.rounds[roundCounter - 1]) / 2)
            for gameCounter in range(0, gameNumber):
                currentRound.append(Game(0, 0))
            template.rounds.append(currentRound)

        maxGameID = 0
        for round in finalTournament.rounds[0].rounds:
            for game in round:
                maxGameID += 1

        gameIDCounter = 1
        for round in template.rounds:
            for game in round:
                game.ID = maxGameID + gameIDCounter
                gameIDCounter += 1

    finalTournament.rounds.append(template)

    # create finals
    roundNumber = 2  # find the lowest possible round number
    playerNumber = int(2 ** roundNumber)  # find the player number (including voids)
    template = Tournament()  # create a tournament object
    for roundCounter in range(0, roundNumber):  # loop over the round indices
        currentRound = []
        currentRound.append(Game(0, 0))
        template.rounds.append(currentRound)
    for round in template.rounds:
        for game in round:
            game.ID = maxGameID + gameIDCounter
            gameIDCounter += 1
    finalTournament.rounds.append(template)

    return finalTournament


def createDoubleElimTournament(playerList):
    playerList = createSeeding(playerList)
    roundNumber = int(math.ceil(math.log(len(playerList), 2)))  # find the lowest possible game number
    playerNumber = int(2 ** roundNumber)  # find the player number (including voids)
    while len(playerList) < playerNumber:
        playerList.append(Player(len(playerList) + 1, "Null", "Null", "Null", 0))
    playerList = createSeeding(playerList)
    tournament = createDoubleElimTemplate(playerNumber)
    for current_seed in range(1, playerNumber + 1):
        player_with_seed = None
        game_seed_index = None
        seed_1_or_2 = None
        for current_seed_b in range(playerNumber):
            if playerList[current_seed_b].seed == current_seed:
                player_with_seed = playerList[current_seed_b]
            if tournament.rounds[0].rounds[0][current_seed_b // 2].seedindex1 == current_seed:
                game_seed_index = current_seed_b // 2
                seed_1_or_2 = 1
            if tournament.rounds[0].rounds[0][current_seed_b // 2].seedindex2 == current_seed:
                game_seed_index = current_seed_b // 2
                seed_1_or_2 = 2
        if seed_1_or_2 == 1:
            tournament.rounds[0].rounds[0][game_seed_index].player1 = player_with_seed
            tournament.rounds[0].rounds[0][game_seed_index].player1 = player_with_seed
        elif seed_1_or_2 == 2:
            tournament.rounds[0].rounds[0][game_seed_index].player2 = player_with_seed
    return tournament


def formatSingleElimTable(tournament):
    roundNumber = len(tournament.rounds)
    gameNumber = int(2 ** roundNumber) - 1
    tableList = [["" for j in range(roundNumber)] for i in range(gameNumber)]
    prespace = 0
    midspace = 1
    for current_col in range(roundNumber):
        gameCounter = 0
        for current_row in range(gameNumber):
            if current_row == prespace + (gameCounter * (midspace + 1)):
                tableList[current_row][current_col] = tournament.rounds[current_col][gameCounter]
                gameCounter += 1
        prespace = (prespace * 2) + 1
        midspace = (midspace * 2) + 1
    return tableList

def formatDoubleElimTable(tournament):
    winnersTour = tournament.rounds[0]
    losersTour = tournament.rounds[1]
    finalsTour = tournament.rounds[2]
    tableList = formatSingleElimTable(winnersTour)
    initGameNum = len(tableList)
    initRoundNum = len(tableList[0])
    # add 3 cols to all rows
    for current_row in tableList:
        current_row += ["" for j in range(3)]
    rowLen = initRoundNum + 3
    # add the wb header and an empty row before the tableList
    tableList = [["Round" + str(roundnr) for roundnr in range(1, initRoundNum + 1)] + ["","Finals Round 1","Finals Round 2"]] + [["" for j in range(rowLen)]] + tableList
    # add an empty row, the lb header, and an empty row to the end of the tableList
    tableList += [["" for j in range(rowLen)]] + [["Round" + str(roundnr) for roundnr in range(1, initRoundNum + 2)]+["",""]] + [["" for j in range(rowLen)]]
    # add LB rows (1/2 of original WB rows)
    tableList += [["" for j in range(rowLen)] for i in range(initGameNum // 2)]
    lbFirstRow = initGameNum + 5
    prespace = 0
    midspace = 1
    for current_col in range(len(losersTour.rounds)):
        gameCounter = 0
        for current_row in range(initGameNum // 2):
            if current_row == prespace + (gameCounter * (midspace + 1)):
                tableList[current_row+lbFirstRow][current_col] = losersTour.rounds[current_col][gameCounter]
                gameCounter += 1
        if (current_col + 1) % 2 == 0:
            prespace = (prespace * 2) + 1
            midspace = (midspace * 2) + 1
    tableList[3][rowLen-2] = finalsTour.rounds[0][0]
    tableList[2][rowLen-1] = finalsTour.rounds[1][0]
    return tableList


def updateBracket():
    # update Game score for GameID
    if manager.tournament.type == 'se':
        roundCounter = 0
        for round in manager.tournament.rounds:
            for game in round:
                if game.score[0] > int(int(game.BO) / 2):
                    game.winner = game.player1
                elif game.score[1] > int(int(game.BO) / 2):
                    game.winner = game.player2
                else:
                    pass
                # move winners onto next games
                if roundCounter != len(manager.tournament.rounds[0].rounds) - 1:
                    if game.winner != None:
                        if round.index(game) % 2 == 0:
                            manager.tournament.rounds[roundCounter + 1][
                                int(round.index(game) / 2)].player1 = game.winner
                        if round.index(game) % 2 == 1:
                            manager.tournament.rounds[roundCounter + 1][
                                int(round.index(game) / 2)].player2 = game.winner

            roundCounter = roundCounter + 1

    elif manager.tournament.type == 'de':
        roundCounter = 0
        for round in manager.tournament.rounds[0].rounds:
            for game in round:
                if game.score[0] > int(int(game.BO) / 2):
                    game.winner = game.player1
                elif game.score[1] > int(int(game.BO) / 2):
                    game.winner = game.player2
                else:
                    pass
                # move winners onto next games
                if roundCounter != len(manager.tournament.rounds[0].rounds) - 1:
                    if game.winner != None:
                        if round.index(game) % 2 == 0:
                            manager.tournament.rounds[0].rounds[roundCounter + 1][
                                int(round.index(game) / 2)].player1 = game.winner
                        if round.index(game) % 2 == 1:
                            manager.tournament.rounds[0].rounds[roundCounter + 1][
                                int(round.index(game) / 2)].player2 = game.winner

            roundCounter = roundCounter + 1

        roundCounter = 0
        wbRoundCounter = 0
        for round in manager.tournament.rounds[1].rounds:
            if roundCounter == 0:  # populate first round of LB
                for game in manager.tournament.rounds[0].rounds[0]:
                    loser = None
                    if game.winner != None:  # if game has a winner
                        if game.player1.ID == game.winner.ID:
                            loser = game.player2
                        else:
                            loser = game.player1

                    if manager.tournament.rounds[0].rounds[0].index(game) % 2 == 0:
                        manager.tournament.rounds[1].rounds[roundCounter][
                            int(manager.tournament.rounds[0].rounds[0].index(game) / 2)].player1 = loser
                    if manager.tournament.rounds[0].rounds[0].index(game) % 2 == 1:
                        manager.tournament.rounds[1].rounds[roundCounter][
                            int(manager.tournament.rounds[0].rounds[0].index(game) / 2)].player2 = loser

            elif roundCounter % 2 == 1:  # if round takes from upper bracket
                losers = []
                # find corresponding upper bracket round
                # lb-wb: 1-1, 3-2, 5-3, 7-4
                wbRoundCounter += 1
                # create a list of losers in order
                for game in manager.tournament.rounds[0].rounds[wbRoundCounter]:
                    if game.winner != None:  # if game has a winner
                        if game.player1.ID == game.winner.ID:
                            loser = game.player2
                        else:
                            loser = game.player1
                        losers.append(loser)
                    else:
                        losers.append(None)

                # split list as necessary, join list if needed, reverse if needed
                if (roundCounter + 1) % 4 == 0:
                    if (4 * roundLol(roundCounter / 4)) / 4 % 2 == 1:
                        losers.reverse()
                else:
                    length = len(losers)
                    mid = length // 2
                    list1 = []
                    list2 = []
                    for element in losers[:mid]:
                        list1.append(element)
                    for element in losers[mid:]:
                        list2.append(element)
                    losers = []
                    if (4 * roundLol(roundCounter / 4)) / 4 % 2 == 1:
                        list1.reverse()
                        list2.reverse()
                    for element in list1:
                        losers.append(element)
                    for element in list2:
                        losers.append(element)

                # distribute to games
                gameCounter = 0
                for game in manager.tournament.rounds[1].rounds[roundCounter]:
                    game.player1 = losers[gameCounter]
                    gameCounter += 1

            # check for winners
            gameCounter = 0
            for game in manager.tournament.rounds[1].rounds[roundCounter]:
                if game.score[0] > int(int(game.BO) / 2):
                    game.winner = game.player1
                elif game.score[1] > int(int(game.BO) / 2):
                    game.winner = game.player2
                else:
                    pass

                if game.winner != None:
                    if roundCounter == len(manager.tournament.rounds[1].rounds) - 1:  # if last round, do nothing as finals bracket fetches stuff itself
                        pass
                    elif (roundCounter + 1) % 2 == 1:  # if next round takes from UB
                        manager.tournament.rounds[1].rounds[roundCounter + 1][gameCounter].player2 = game.winner
                    elif (roundCounter + 1) % 2 == 0:
                        if round.index(game) % 2 == 0:
                            manager.tournament.rounds[1].rounds[roundCounter + 1][
                                int(round.index(game) / 2)].player1 = game.winner
                        if round.index(game) % 2 == 1:
                            manager.tournament.rounds[1].rounds[roundCounter + 1][
                                int(round.index(game) / 2)].player2 = game.winner

                gameCounter += 1

            roundCounter += 1

        roundCounter = 0
        for round in manager.tournament.rounds[2].rounds:
            for game in round:
                if game.score[0] > int(int(game.BO) / 2):
                    game.winner = game.player1
                elif game.score[1] > int(int(game.BO) / 2):
                    game.winner = game.player2
                else:
                    pass

            if roundCounter == 0:
                if manager.tournament.rounds[0].rounds[-1][0].winner != None:  # finds loser of UB finals
                    if manager.tournament.rounds[0].rounds[-1][0].player1.ID == manager.tournament.rounds[0].rounds[-1][0].winner.ID:
                        loser = manager.tournament.rounds[0].rounds[-1][0].player2
                    else:
                        loser = manager.tournament.rounds[0].rounds[-1][0].player1
                else:
                    loser = None

                round[0].player1 = loser
                round[0].player2 = manager.tournament.rounds[1].rounds[-1][-1].winner  # finds winner of LB finals

            else:
                round[0].player1 = manager.tournament.rounds[0].rounds[-1][0].winner
                if manager.tournament.rounds[2].rounds[0][0].winner != None:
                    round[0].player2 = manager.tournament.rounds[2].rounds[0][0].winner

            roundCounter += 1


    else:
        print("Tournament has no type")


def selectCurrentGame(GameID):  # moves that game object into manager.currentGame
    foundGame = False
    if manager.tournament.type == 'se':
        for round in manager.tournament.rounds:
            for game in round:
                if game.ID == GameID:
                    manager.currentGame = game
                    foundGame = True
                    break
        if foundGame == False:
            print('Failed to find game')

    if manager.tournament.type == 'de':
        for bracket in manager.tournament.rounds:
            for round in bracket.rounds:
                for game in round:
                    if game.ID == GameID:
                        manager.currentGame = game
                        foundGame = True
                        break
            if foundGame == False:
                print('Failed to find game. Was trying to find game ' + str(GameID))
    try:
        manager.currentGame.player1Char = manager.currentGame.player1.main
    except:
        pass
    try:
        manager.currentGame.player2Char = manager.currentGame.player2.main
    except:
        pass


def roundLol(int1):
    return round(int1)


# def manualOverwrite(GameID, IGN1, Character1, Score1, IGN2, Character2, Score2, BO, gameName):

@app.route('/')
def default():
    return redirect('/controlPanel')


@app.route('/<path:path>')
def getImage(path):
    return app.send_static_file(path)


@app.route('/overlay', methods=['GET'])
def overlayPage():
    return render_template('OverlayTemplate.html', game=manager.currentGame)


@app.route('/bracket', methods=['GET'])
def bracketPage():
    #try:
    if manager.tournament.type == 'se':
        print('SE')
        return render_template('SingleElimTemplate.html', tournament=manager.tournament, numRounds=len(manager.tournament.rounds),tournamentTable=formatSingleElimTable(manager.tournament))
    if manager.tournament.type == 'de':
        print('DE')
        return render_template('DoubleElimTemplate.html', tournament=manager.tournament, numRounds=len(manager.tournament.rounds), tournamentTable=formatDoubleElimTable(manager.tournament))
    '''except Exception as e:
        print(e)
        return render_template('Empty.html')'''


@app.route('/controlPanel', methods=['GET', 'POST'])
def controlPanel():
    if request.method == 'GET':
        return render_template('ControlPanelTemplate.html', currentGame=manager.currentGame)
    if request.method == 'POST':

        if request.form['formIdentifier'] == 'changeGame':
            try:
                selectCurrentGame(int(request.form['gameID']))
            except:
                print('Error occured while trying to select game')

        if request.form['formIdentifier'] == 'changeScore':
            try:
                manager.currentGame.score[0] = int(request.form['p1Score'])
                manager.currentGame.score[1] = int(request.form['p2Score'])
            except:
                pass
            updateBracket()

        if request.form['formIdentifier'] == 'changeCharacter':
            try:
                manager.currentGame.player1Char = request.form['p1Char']
                manager.currentGame.player2Char = request.form['p2Char']
            except:
                pass

        if request.form['formIdentifier'] == 'changeScoreCharacter':
            try:
                manager.currentGame.score[0] = int(request.form['p1Score'])
                manager.currentGame.score[1] = int(request.form['p2Score'])
                manager.currentGame.player1Char = request.form['p1Char']
                manager.currentGame.player2Char = request.form['p2Char']
            except:
                pass
            updateBracket()

        if request.form['formIdentifier'] == 'changeBO':
            try:
                manager.currentGame.BO = request.form['BO']
            except:
                pass
            updateBracket()

        if request.form['formIdentifier'] == 'backupTournamentForm':
            backup(manager.tournament, 'Backups/tournamentBackup')

        if request.form['formIdentifier'] == 'retrieveBackupTournamentForm':
            readBackupTournament('Backups/tournamentBackup')

        return render_template('ControlPanelTemplate.html', currentGame=manager.currentGame)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'GET':
        return render_template('SetupTemplate.html', playerList=manager.playerList)
    if request.method == 'POST':

        if request.form['formIdentifier'] == 'addForm':
            if request.form['seed'] == '':
                player = Player(manager.ID, request.form['IGN'], request.form['main'], request.form['school'], '')
            else:
                player = Player(manager.ID, request.form['IGN'], request.form['main'], request.form['school'],
                                request.form['seed'])
            manager.ID = manager.ID + 1
            manager.playerList.append(player)

        elif request.form['formIdentifier'] == 'editForm':
            try:
                tempList = manager.playerList
                if request.form['seed'] == '':
                    manager.playerList[int(request.form['ID']) - 1] = Player(request.form['ID'], request.form['IGN'],
                                                                             request.form['main'],
                                                                             request.form['school'], '')
                else:
                    manager.playerList[int(request.form['ID']) - 1] = Player(request.form['ID'], request.form['IGN'],
                                                                             request.form['main'],
                                                                             request.form['school'],
                                                                             request.form['seed'])
                if areSeedsUnique(manager.playerList) == True:
                    print('Seeding finalised succesfully')
                else:
                    raise Exception(
                        'An error has occurred, as seeding is not unique. Try again')  # NEED TO IMPLEMENT PROPER WARNING ON SITE
                    manager.playerList = tempList
            except IndexError:
                print("ID input is out of range")

        elif request.form['formIdentifier'] == 'deleteForm':
            index = 0
            IDList = []
            for player in manager.playerList:
                IDList.append(player.ID)
            for ID in IDList:
                if ID == int(request.form['ID']):
                    delete = manager.playerList.pop(index)
                    pass
                else:
                    index = index + 1


        elif request.form['formIdentifier'] == 'finaliseForm':
            for player in manager.playerList:
                try:
                    player.seed = int(player.seed)
                except:
                    player.seed = 0
            manager.playerList = createSeeding(manager.playerList)
            i = 1
            for player in manager.playerList:
                player.ID = i
                i = i + 1

        elif request.form['formIdentifier'] == 'backupForm':
            backup(manager.playerList, 'Backups/playerBackup')

        elif request.form['formIdentifier'] == 'retrieveBackupForm':
            readBackupPlayers('Backups/playerBackup')
            manager.ID = len(manager.playerList) + 1

        elif request.form['formIdentifier'] == 'makeSEBracketForm':
            manager.playerList = createSeeding(manager.playerList)
            i = 1
            for player in manager.playerList:
                player.ID = i
                i = i + 1
            manager.tournament = createSingleElimTournament(manager.playerList)
            manager.tournament.type = 'se'

        elif request.form['formIdentifier'] == 'makeDEBracketForm':
            manager.playerList = createSeeding(manager.playerList)
            i = 1
            for player in manager.playerList:
                player.ID = i
                i = i + 1
            manager.tournament = createDoubleElimTournament(manager.playerList)
            manager.tournament.type = 'de'

        else:
            print('This king of request is not valid: ' + request.form['formIdentifier'])
            raise Exception

        return render_template('SetupTemplate.html', playerList=manager.playerList)


if __name__ == '__main__':
    app.run()
