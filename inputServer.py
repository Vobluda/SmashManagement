from flask import Flask, url_for, send_from_directory, request, render_template
import re
import os
app = Flask(__name__, static_url_path='/static')
app.config.from_object('config')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

class Player:
    def __init__(self, IGN, score, character):
        self.IGN = IGN
        self.score = score
        self.character = character

class Game:
    def __init__(self, player1, player2, status):
        self.player1 = player1
        self.player2 = player2
        self.status = status
#class Match:

#class Tournament:

player1 = Player('', 0, 'boomer')
player2 = Player('', 0, 'boomer')
game = Game(player1, player2, "")

def printVals(player1, player2):
    print(player1.IGN)
    print(player1.score)
    print(player1.character)
    print(player2.IGN)
    print(player2.score)
    print(player2.character)

def setDefaultValues(player1, player2):
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
        pass

@app.route('/')
def mainPage():
    printVals(player1, player2)
    return render_template('AtomTestingTemplate.html', player1=player1, player2=player2, game=game)

@app.route('/<path:path>')
def getImage(path):
    return app.send_static_file(path)

@app.route('/input')
def inputPage():
    setDefaultValues(player1, player2)
    return render_template('InputSiteTemplate.html', player1=player1, player2=player2, game=game)

@app.route('/saveVals', methods = ['POST'])
def saveVals():
    player1.IGN = request.form['p1']
    player1.score = request.form['p1s']
    player1.character = request.form['character1']
    player2.IGN = request.form['p2']
    player2.score = request.form['p2s']
    player2.character = request.form['character2']
    game.status = request.form['status']
    setDefaultValues(player1, player2)
    return render_template('InputSiteTemplate.html', player1=player1, player2=player2, game=game)
