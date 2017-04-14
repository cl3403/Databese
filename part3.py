#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Chang Liu, Meiyao Li
Project 1 Part 3
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, session, url_for, flash, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
SECRET_KEY = "my secret keyyek terces ym"
app = Flask(__name__, template_folder=tmpl_dir)
app.config.from_object(__name__)

DATABASEURI = "postgresql://cl3403:buyaochidao@104.196.135.151/proj1part2"
engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():
  cur = g.conn.execute('select name, COUNT(*) as freq from play group by name order by freq desc limit 10')
  entries = [dict(name=row[0]) for row in cur.fetchall()]
  return render_template('index.html', entries=entries)


@app.route('/signup', methods=['GET','POST'])
def sign_up():
    error = None
    cur = g.conn.execute('select uid from player order by CAST(uid as int) DESC limit 1')
    newId = str(int(cur.fetchone()[0]) + 1)

    cur = g.conn.execute('select email from player')
    players = []
    for row in cur.fetchall():
        players.append(row[0]) 

    if request.method == 'POST':
      gameName = request.form['gamename']
      if (request.form['fullname'] == '') or (request.form['phone'] == '') or (request.form['email'] == ''):
        error = 'Incomplete Information'
        
      elif '@' not in request.form['email']:
        error = 'Email not in the right format'
        
      elif request.form['email'] in players:
        error = 'Email already registered'

      else:
        g.conn.execute('insert into player  values (%s, %s, %s, %s)', newId, request.form['fullname'], request.form['phone'], request.form['email'])
        cur = g.conn.execute('select rank from play where name=%s order by rank DESC',gameName)
        newRank = cur.fetchone()[0] + 1
        g.conn.execute('insert into play values (%s, %s, %s)', gameName, newId, newRank)
        
        flash('Successfully signed up!')
        return redirect(url_for('index'))
    return render_template('signup.html', error=error)

@app.route('/data', methods=['GET','POST'])
def data():
    uid = session['uid']
    cur = g.conn.execute('select plname from player where uid=%s',uid)
    userN = cur.fetchone()[0]
    cur = g.conn.execute('select name, rank from play where uid=%s',uid)
    entries = [dict(name=row[0], rank=row[1]) for row in cur.fetchall()]
    return render_template('data.html', entries=entries, userN=userN)

@app.route('/add', methods=['GET','POST'])
def add():
    uid = session['uid']
    error = None
    gameList = []
    cur = g.conn.execute('select name from play where uid=%s',uid)
    for row in cur.fetchall():
      gameList.append(row[0])
    
    if request.method == 'POST':
      gameName = request.form['gamename']
      if gameName in gameList:
        error = " we know you are already playing this game!"
      else:
        cur = g.conn.execute('select rank from play where name=%s order by rank DESC',gameName)
        newRank = cur.fetchone()[0] + 1
        g.conn.execute('insert into play values (%s, %s, %s)', gameName, uid, newRank)
        flash('Successfully added another game!')
    return render_template('add.html', error=error)

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    cur = g.conn.execute('select plname, email, uid from player')
    users = {}
    uid = {}
    for row in cur.fetchall():
        users[row[0]] = row[1]
        uid[row[0]] = row[2]
      
    if request.method == 'POST':
        if request.form['username'] not in users:
            error = 'Invalid username'
        elif request.form['email'] != users[request.form['username']]:
            error = 'Invalid email'
        else:
            session['logged_in'] = True
            session['uid'] = uid[request.form['username']]
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('uid', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/recommendation', methods=['GET','POST'])
def recom():
    error = None
    entries = None

    genreKeys = []
    modeKeys = []
    cnyKeys = []
    pfKeys = []
    ctyKeys = []

    genreError = "the available genres:  "
    modeError = "the available modes:  "
    cnyError = "the available companies:  "
    pfError = "the available platforms:  "
    ctyError = "the available countries:  "
      
    if request.method == 'POST':
        if request.form['condition'] == "genre":
          cur = g.conn.execute('select distinct genre from game')
          for row in cur.fetchall():
            genreKeys.append(row[0])
            genreError += row[0] + ","
          if request.form['key'] not in genreKeys:
            error = genreError[:-1]
          else:
            cur = g.conn.execute('select name from game where genre=%s', request.form['key'])
            entries = [dict(name=row[0]) for row in cur.fetchall()]

        elif request.form['condition'] == "mode":
          cur = g.conn.execute('select distinct mode from game')
          for row in cur.fetchall():
            modeKeys.append(row[0])
            modeError += row[0] + ","
          if request.form['key'] not in modeKeys:
            error = modeError[:-1]
          else:
            cur = g.conn.execute('select name from game where mode=%s', request.form['key'])
            entries = [dict(name=row[0]) for row in cur.fetchall()]

        elif request.form['condition'] == "company":
          cur = g.conn.execute('select distinct cname from publish')
          for row in cur.fetchall():
            cnyKeys.append(row[0])
            cnyError += row[0] + ","
          if request.form['key'] not in cnyKeys:
            error = cnyError[:-1]
          else:
            cur = g.conn.execute('select name from publish where cname=%s', request.form['key'])
            entries = [dict(name=row[0]) for row in cur.fetchall()]

        elif request.form['condition'] == "platform":
          cur = g.conn.execute('select distinct pname from publish_on')
          for row in cur.fetchall():
            pfKeys.append(row[0])
            pfError += row[0] + ","
          if request.form['key'] not in pfKeys:
            error = pfError[:-1]
          else:
            cur = g.conn.execute('select name from publish_on where pname=%s', request.form['key'])
            entries = [dict(name=row[0]) for row in cur.fetchall()]

        elif request.form['condition'] == "country":
          cur = g.conn.execute('select distinct country from company')
          for row in cur.fetchall():
            ctyKeys.append(row[0])
            ctyError += row[0] + ","
          if request.form['key'] not in ctyKeys:
            error = ctyError[:-1]
          else:
            cur = g.conn.execute('select p.name from publish p, company c where c.country=%s and c.cname = p.cname', request.form['key'])
            entries = [dict(name=row[0]) for row in cur.fetchall()]

        else:
            error = "Invalid input value for recommendation"
    return render_template('recom.html', error=error, entries=entries)

@app.route('/chart', methods=['GET','POST'])
def chart():
    
    error = None
    entries = None
    maxV = avgV = salesV = timeV = False
   
    if request.method == 'POST':
        limit = request.form['number']
        if request.form['criteria'] == "max":
          maxV = True
          cur = g.conn.execute('select r.name, MAX(r.score) as maxS from review_on r group by r.name order by maxS DESC limit %s', limit)
          entries = [dict(name=row[0], number=row[1]) for row in cur.fetchall()]

        elif request.form['criteria'] == "sales":
          salesV = True
          cur = g.conn.execute('select name, sales from game order by sales DESC limit %s', limit)
          entries = [dict(name=row[0], number=row[1]) for row in cur.fetchall()]

        elif request.form['criteria'] == "avg":
          avgV = True
          cur = g.conn.execute('select r.name, AVG(r.score) as avgS from review_on r group by r.name order by avgS DESC limit %s', limit)
          entries = [dict(name=row[0], number=row[1]) for row in cur.fetchall()]

        else:
          timeV = True
          cur = g.conn.execute('select name, year from publish order by year DESC limit %s', limit)
          entries = [dict(name=row[0], number=row[1]) for row in cur.fetchall()]    
    return render_template('chart.html', error=error, entries=entries, maxV=maxV, avgV=avgV, salesV=salesV, timeV=timeV)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/otherweb')
def other():
    cur = g.conn.execute('select website_name from game_website')
    entries = [dict(name=row[0]) for row in cur.fetchall()]
    return render_template('otherweb.html', entries=entries)

@app.route('/info', methods=['GET','POST'])
def info():
    error = None
    entry = None
    result = {}
    gameKeys = []
    gameError = "the available games:  "
      
    if request.method == 'POST':
      gameName = request.form['gamename']
      cur = g.conn.execute('select name from game')
      for row in cur.fetchall():
        gameKeys.append(row[0])
        gameError += row[0] + ","
      if gameName not in gameKeys:
        error = gameError[:-1]
      else:
        cur = g.conn.execute('select sales from game where name=%s', gameName)
        result['sales'] = cur.fetchone()[0]
        cur = g.conn.execute('select genre from game where name=%s', gameName)
        result['genre'] = cur.fetchone()[0]
        cur = g.conn.execute('select mode from game where name=%s', gameName)
        result['mode'] = cur.fetchone()[0]
        cur = g.conn.execute('select cname from publish where name=%s', gameName)
        result['company'] = cur.fetchone()[0]
        cur = g.conn.execute('select year from publish where name=%s', gameName)
        result['year'] = cur.fetchone()[0]
        cur = g.conn.execute('select pname from publish_on where name=%s', gameName)
        result['platform'] = cur.fetchone()[0]
        result['name'] = gameName
        entry = result
  
    return render_template('info.html', entry=entry, error=error)

@app.route('/player', methods=['GET','POST'])
def player():
    error = None
    entries = None
    result = {}
    gameKeys = []
    gameError = "the available games:  "
  
    if request.method == 'POST':
      gameName = request.form['gamename']
      cur = g.conn.execute('select name from game')
      for row in cur.fetchall():
        gameKeys.append(row[0])
        gameError += row[0] + ","
      if gameName not in gameKeys:
        error = gameError[:-1]
      else:
        limit = request.form['number']
        cur = g.conn.execute('select P.plname, P.phone, P.email, p1.rank from player p, play p1 where p1.name = %s and p.uid = p1.uid order by p1.rank limit %s', gameName, limit)
        entries = [dict(name=row[0], phone=row[1], email=row[2]) for row in cur.fetchall()]
        result['gamename'] = gameName

    return render_template('player.html', error=error, entries=entries, result=result)
  
if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=False)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
