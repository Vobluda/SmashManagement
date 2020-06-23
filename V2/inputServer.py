from flask import Flask, url_for, send_from_directory, request, render_template
import re
import pickle
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

#def createSeeding(playerList):

#def createBracket(bracketStyle, playerList):

#def updateBracket(GameID, score1, score2):

#def updateOverlayVals(GameID):

#def manualOverwrite(GameID, IGN1, Character1, Score1, IGN2, Character2, Score2, BO, gameName):

#def readBackup(objectFile):

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
            manager.playerList[int(request.form['ID'])-1] = Player(request.form['ID'], request.form['IGN'], request.form['main'], request.form['school'], request.form['seed'])
        except:
            print("ID input is out of range")
        return render_template('EditPlayersTemplate.html', playerList = manager.playerList)

@app.route('/backupPlayers', methods = ['POST'])
def createBackup():
    backup(manager.playerList, 'Backups/playerBackup')
    return render_template('AddPlayersTemplate.html', playerList = manager.playerList)

if __name__ == '__main__':
    app.run()
