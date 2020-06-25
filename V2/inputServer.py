from flask import Flask, url_for, send_from_directory, request, render_template, redirect
import re
import pickle
import random  # for assigning seeds to random players
import math
from datetime import datetime

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
        self.seedindex1 = seedindex1  # seed *index*, not the actual seed
        self.seedindex2 = seedindex2
        self.player1 = None
        self.player2 = None
        self.player1Char = None
        self.player2Char = None
        self.winner = None
        self.score = [0,0]
        self.BO = None
        self.name = None

    def players(self, player1, player2, player1Char, player2Char, BO, name):
        self.player1 = player1
        self.player2 = player2
        self.player1Char = player1Char
        self.player2Char = player2Char
        self.winner = None
        self.score = [0,0]
        self.BO = BO
        self.name = name


class Tournament:
    def __init__(self):
        self.rounds = []
        self.currentGame = None
        self.type = 'se' #NEEDS TO BE CHANGED WHEN DOUBLE ELIM IS IMPLMENTED


class PlayerManager:
    def __init__(self):
        self.playerList = []
        self.ID = len(self.playerList) + 1
        self.currentGame = None
        self.tournament = None


manager = PlayerManager()
basicP1 = Player(1, 'Vobluda', 'Daisy', 'STA', 1)
basicP2 = Player(2, 'Flux', 'Daisy', 'STA', 2)
manager.currentGame = Game(1,2)
manager.currentGame.players(basicP1, basicP2, 'Samus', 'Daisy', 5, 'Winner\'s Final')

def backup(object, fileName):
    with open(fileName, 'wb') as openedFile:
        pickle.dump(object, openedFile)


def readBackupPlayers(objectFile):
    with open(objectFile, 'rb') as openedFile:
        manager.playerList = pickle.load(openedFile)
    print('Backup of players retrieved')


def createSeeding(playerList):  # Find players whose seeds are missing and assign them free seeds randomly.
    seeds = [i.seed if (type(i.seed) == int) else 0 for i in playerList]  # iterate over the playerList and get the player seeds into one handy list. Non-ints are converted to 0.
    valid_seeds = [i for i in seeds if i > 0]  # make a list with only the valid seeds, a seed is valid if > 0
    missing_seed_indices = [i for i in range(len(seeds)) if not seeds[i] > 0]  # make a list with the indices of players that have missing seeds
    current_seed_value = 1  # set the loop counter to 1, because it's the lowest valid seed
    while missing_seed_indices:  # loop while there are still some missing seeds (list is True unless empty)
        if current_seed_value not in valid_seeds:  # if the current seed value has not yet been used
            selected_player_index = random.choice(missing_seed_indices)  # pick a random player index with a missing seed
            playerList[selected_player_index].seed = current_seed_value  # assign the player the current seed value
            missing_seed_indices.remove(selected_player_index)  # remove the player's index from the list
        current_seed_value += 1  # increment the counter
    return playerList  # return the modified playerList


def areSeedsValid(playerList):  # Returns True if all seeds are valid but not unique (i.e. between 1 and the number of players)
    seeds = [i.seed if (type(i.seed) == int) else 0 for i in playerList]  # iterate over the playerList and get the player seeds into one handy list. Non-ints are converted to 0.
    return min(seeds) > 0 and max(seeds) <= len(playerList)  # returns True if the lowest and highest seed are between 1 and the number of players.


def areSeedsUnique(playerList):  # Returns True if players have unique seeds.
    seeds = [i.seed if (type(i.seed) == int) else 0 for i in playerList]  # iterate over the playerList and get the player seeds into one handy list. Non-ints are converted to 0.
    while 0 in seeds:
        seeds.remove(0)
    seedsUnique = seeds == list(set(seeds))  # compares the seeds list to a set of the seeds - converting to a set removes duplicates - True if unique
    return seedsUnique


def createSingleElimTemplate(playerNumber):
    roundNumber = int(math.ceil(math.log(playerNumber, 2)))  # find the lowest possible game number
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
    return template


def createSingleElimTournament(playerList):
    print("Standard print")
    print("Standard debug",out=sys.stderr)
    playerList = createSeeding(playerList)
    roundNumber = int(math.ceil(math.log(len(playerList), 2)))  # find the lowest possible game number
    playerNumber = int(2 ** roundNumber)  # find the player number (including voids)
    while len(playerList) < playerNumber:
        playerList.append(Player(len(playerList) + 1, "Nic", "Nic", "Nic", 0))
        print("Null player with id",len(playerList),"and name Nic was added.")
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


# def updateBracket(GameID, score1, score2):

# def updateOverlayVals(GameID):

# def manualOverwrite(GameID, IGN1, Character1, Score1, IGN2, Character2, Score2, BO, gameName):


manager = PlayerManager()


@app.route('/')
def default():
    return redirect('/controlPanel')

@app.route('/<path:path>')
def getImage(path):
    return app.send_static_file(path)

@app.route('/overlay', methods = ['GET'])
def overlayPage():
    return render_template('OverlayTemplate.html', game=manager.currentGame)

@app.route('/bracket', methods = ['GET'])
def bracketPage():
    if manager.tournament.type == 'se':
        print(manager.tournament.rounds)
        return render_template('SingleElimTemplate.html', tournament=manager.tournament)

@app.route('/controlPanel', methods = ['GET', 'POST'])
def controlPanel():
    return render_template('ControlPanelTemplate.html', playerList = manager.playerList)

@app.route('/setup', methods = ['GET', 'POST'])
def setup():
    if request.method == 'GET':
        return render_template('SetupTemplate.html', playerList = manager.playerList)
    if request.method == 'POST':

        if request.form['formIdentifier'] == 'addForm':
            if request.form['seed'] == '':
                player = Player(manager.ID, request.form['IGN'], request.form['main'], request.form['school'], '')
            else:
                player = Player(manager.ID, request.form['IGN'], request.form['main'], request.form['school'], request.form['seed'])
            manager.ID = manager.ID + 1
            manager.playerList.append(player)

        elif request.form['formIdentifier'] == 'editForm':
            try:
                tempList = manager.playerList
                manager.playerList[int(request.form['ID'])-1] = Player(request.form['ID'], request.form['IGN'], request.form['main'], request.form['school'], request.form['seed'])
                print(request.json)
                if areSeedsUnique(manager.playerList) == True:
                    print('Seeding finalised succesfully')
                else:
                    raise Exception('An error has occurred, as seeding is not unique. Try again') #NEED TO IMPLEMENT PROPER WARNING ON SITE
                    manager.playerList = tempList
            except IndexError:
                print("ID input is out of range")

        elif request.form['formIdentifier'] == 'deleteForm':
            index = 0
            IDList = []
            for player in manager.playerList:
                IDList.append(player.ID)
            print(IDList)
            for ID in IDList:
                if ID == int(request.form['ID']):
                    delete = manager.playerList.pop(index)
                    print(manager.playerList)
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
            manager.ID = len(manager.playerList)+1

        elif request.form['formIdentifier'] == 'makeBracketForm':
            manager.playerList = createSeeding(manager.playerList)
            i = 1
            for player in manager.playerList:
                player.ID = i
                i = i + 1
            manager.tournament = createSingleElimTournament(manager.playerList)

        else:
            print('This king of request is not valid: ' + request.form['formIdentifier'])
            raise Exception

        return render_template('SetupTemplate.html', playerList = manager.playerList)

if __name__ == '__main__':
    app.run()
