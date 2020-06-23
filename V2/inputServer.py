from flask import Flask, url_for, send_from_directory, request, render_template
import re
import pickle
import random  # for assigning seeds to random players
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


class Game:
    def __init__(self, player1, player2, BO, name):
        self.player1 = player1
        self.player2 = player2
        self.winner = None
        self.score = []
        self.BO = BO
        self.name = name

class Tournament:
    def __init__(self):
        self.games = []
        self.currentGame = None

class PlayerManager:
    def __init__(self):
        self.ID = 1
        self.playerList = []

manager = PlayerManager()

'''def setDefaultValues(player1, player2):
    f = open('templates\InputSiteTemplate.html', 'r')
    preFile = f.read()
    f.close()
    file = preFile.replace(' selected', '')
    p1Matches = re.finditer(player1.character, file)
    p1List = [match.start() for match in p1Matches]
    try:
        pre = file[0:(p1List[0]-7)]
        post = file[(p1List[0]-7):]
        file = pre + "selected " + post
        p2Matches = re.finditer(player2.character, file)
        p2List = [match.start() for match in p2Matches]
        if player2.character == 'Bowser':
            pre = file[0:(p2List[3]-7)]
            post = file[(p2List[3]-7):]
        else:
            pre = file[0:(p2List[2]-7)]
            post = file[(p2List[2]-7):]
        file = pre + "selected " + post
        os.remove('templates\InputSiteTemplate.html')
        f = open('templates\InputSiteTemplate.html', 'w')
        f.write(file)
        f.close
    except:
        pass'''

def backup(object, fileName):
    dateTimeObj = datetime.now()
    with open(fileName, 'wb') as openedFile:
        pickle.dump(object, openedFile)

def createSeeding(playerList):  # Find players whose seeds are missing and assign them free seeds randomly.
    seeds = [i.seed for i in playerList]  # iterate over the playerList and get the player seeds into one handy list
    valid_seeds = [i for i in seeds if i > 0]  # make a list with only the valid seeds, a seed is valid if > 0
    missing_seed_indices = [i for i in range(len(seeds)) if not seeds[i] > 0]  # make a list with the indices of players that have missing seeds
    current_seed_value = 1  # set the loop counter to 1, because it's the lowest valid seed
    while missing_seed_indices:  # loop while there are still some missing seeds (list is True unless empty)
        if current_seed_value not in valid_seeds:  # if the current seed value has not yet been used
            selected_player_index = random.choice(missing_seed_indices)  # pick a random player index with a missing seed
            playerList[selected_player_index].seed = current_seed_value  # assign the player the current seed value
            missing_seed_indices.remove(selected_player_index)  # remove the player's index from the list
        current_seed_value += 1  # increment the counter
    manager.playerList = playerList  # reassigns to manager playerList used in other parts

def areSeedsUnique(playerList):  # Returns True if players have valid and unique seeds.
    seeds = [i.seed for i in playerList]  # iterate over the playerList and get the player seeds into one handy list
    seedsUnique = seeds == list(set(seeds))  # compares the seeds list to a set of the seeds - converting to a set removes duplicates - True if unique
    seedsValid = min(seeds) > 0  # checks if all seeds are valid - if a seed is invalid it is less than or equal to 0
    return seedsUnique and seedsValid  # True if both conditions are met

#def createBracket(bracketStyle, playerList):

#def updateBracket(GameID, score1, score2):

#def updateOverlayVals(GameID):

#def manualOverwrite(GameID, IGN1, Character1, Score1, IGN2, Character2, Score2, BO, gameName):

@app.route('/<path:path>')
def getImage(path):
    return app.send_static_file(path)

@app.route('/addPlayers', methods = ['GET', 'POST'])
def playerPage():
    if request.method == 'GET':
        return render_template('AddPlayersTemplate.html', playerList = manager.playerList)
    if request.method == 'POST':
        if request.form['seed'] == '':
            player = Player(manager.ID, request.form['IGN'], request.form['main'], request.form['school'], '')
        else:
            player = Player(manager.ID, request.form['IGN'], request.form['main'], request.form['school'], request.form['seed'])
        manager.ID = manager.ID + 1
        manager.playerList.append(player)
        return render_template('AddPlayersTemplate.html', playerList = manager.playerList)

@app.route('/editPlayers', methods = ['GET', 'POST'])
def editPlayerPage():
    if request.method == 'GET':
        return render_template('EditPlayersTemplate.html', playerList = manager.playerList)
    if request.method == 'POST':
        try:
            tempList = manager.playerList
            manager.playerList[int(request.form['ID'])-1] = Player(request.form['ID'], request.form['IGN'], request.form['main'], request.form['school'], request.form['seed'])
            if areSeedsUnique(manager.playerList) == True:
                print('Seeding finalised succesfully')
            else:
                print('An error has occurred, as seeding is not unique. Try again') #NEED TO IMPLEMENT PROPER WARNING ON SITE
                manager.playerList = tempList
        except:
            print("ID input is out of range")
        return render_template('EditPlayersTemplate.html', playerList = manager.playerList)

@app.route('/finishSeeding', methods = ['POST'])
def finishSeeding():
    createSeeding(manager.playerList)
    return render_template('EditPlayersTemplate.html', playerList = manager.playerList)

@app.route('/backupPlayers', methods = ['POST'])
def createBackup():
    backup(manager.playerList, 'Backups/playerBackup')
    return render_template('AddPlayersTemplate.html', playerList = manager.playerList)

if __name__ == '__main__':
    app.run()
