#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort, session, flash, url_for
from datetime import date
from datetime import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jfu2001"
DB_PASSWORD = "joshshimondatabase"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#


######### LOG IN - LOG OUT ###########

'''
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        context = dict(name = session['email'])
        return render_template("posts.html", **context)
'''
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return redirect('/posts')
        
@app.route('/posts')
def posts():
    cmd = 'SELECT * FROM Products_Posted ORDER BY posted_date DESC';
    cursor = g.conn.execute(text(cmd));
    posts = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT * FROM Tags';
    cursor = g.conn.execute(text(cmd));
    tags = cursor.fetchall()
    cursor.close()
    context = dict(posts=posts, tags=tags)
    return render_template("posts.html", **context)

@app.route('/login', methods=['POST'])
def do_admin_login():
    email = request.form['email']
    password = request.form['password']
    cmd = 'SELECT password FROM Users WHERE email = (:email1)';
    cursor = g.conn.execute(text(cmd), email1 = email);
    passes = cursor.fetchall()
    if len(passes) > 0 and request.form['password'] == passes[0][0]:
        session['logged_in'] = True
        session['email'] = email
    else:
        flash('Invalid login credentials!')
    return redirect('/')

@app.route('/logout')
def logout():
    session['logged_in'] = False
    session.pop('email')
    return redirect('/')

@app.route('/newaccount')
def new_account():
    return render_template('newaccount.html')

@app.route('/createnewaccount', methods=['POST'])
def create_new_account():
    values = []
    values.append(request.form['email'])
    values.append(request.form['fullname'])
    values.append(request.form['uni'])
    values.append(request.form['password'])
    values.append(request.form['venmo'])
    values.append(request.form['cashapp'])
    values.append(request.form['image'])
    values = clear_null_entries(values)
    try:
        cmd = 'INSERT INTO Users VALUES (:email1, :password1, :fullname1, :uni1, :venmo1, :cashapp1, :image1)';
        c = g.conn.execute(text(cmd), email1 = values[0], password1 = values[3], fullname1 = values[1], 
                           uni1 = values[2], venmo1 = values[4], cashapp1 = values[5], image1 = values[6]);
        session['logged_in'] = True
        session['email'] = values[0]
        c.close()
        return redirect('/')
    except:
        flash('Error creating account! Ensure all fields are entered correctly.')
        return redirect('/newaccount')

    
############## OPENING POSTS ################
    
@app.route('/openpost', methods=['GET'])
def openpost():
    args = request.args
    pid = args.get("pid")
    cmd = 'SELECT * FROM Products_Posted WHERE product_id = (:pid1)';
    cursor = g.conn.execute(text(cmd), pid1 = pid);
    products = cursor.fetchall()
    
    cmd = 'SELECT * FROM Tags WHERE tag_id in (SELECT tag_id FROM Tagged_Products WHERE product_id = (:pid1))';
    cursor = g.conn.execute(text(cmd), pid1 = pid);
    tags = cursor.fetchall();
    
    cmd = 'SELECT * FROM Reviews WHERE reviewed_email = (:email1)';
    cursor = g.conn.execute(text(cmd), email1 = products[0][0])
    reviews = cursor.fetchall();
    
    context = dict(viewer = session['email'], reviews = reviews, tags = tags, user_email = products[0][0], product_id = products[0][1], title = products[0][2], description = products[0][3], posted_date = products[0][4], product_type = products[0][5], image_url = products[0][6], tutoring_hourly_rate = products[0][7], tutoring_schedule = products[0][8], study_resource_price = products[0][9], study_resource_download_url = products[0][10])
    return render_template("post.html", **context)

########### PROFILE ############

@app.route('/myprofile')
def myprofile():
    return redirect(url_for('.profile', uid=session['email']))

@app.route('/profile', methods=['GET'])
def profile():
    args = request.args
    uid = args.get("uid")
    
    cmd = 'SELECT follower_email FROM Followers WHERE user_email = (:uid1)';
    cursor = g.conn.execute(text(cmd), uid1 = uid);
    followers = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT user_email FROM Followers WHERE follower_email = (:uid1)';
    cursor = g.conn.execute(text(cmd), uid1 = uid);
    followings = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT * FROM Users WHERE email = (:uid1)';
    cursor = g.conn.execute(text(cmd), uid1 = uid);
    info = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT * FROM Followers WHERE user_email = (:uid1) and follower_email = (:uid2)' ;
    cursor = g.conn.execute(text(cmd), uid1 = uid, uid2 = session['email']);
    flwer = cursor.fetchall()
    flw = 0
    if len(flwer) > 0:
        flw = 1
    
    cmd = 'SELECT * FROM Products_Posted WHERE user_email = (:email1)';
    cursor = g.conn.execute(text(cmd), email1 = uid);
    posts = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT * FROM Reviews WHERE reviewed_email = (:email1)';
    cursor = g.conn.execute(text(cmd), email1 = uid);
    reviews = cursor.fetchall()
    cursor.close()
    
    context = dict(followers = followers, followings = followings, info = info, flw = flw, user_id = session['email'], posts=posts, reviews = reviews)
    
    
    return render_template("profile.html", **context)


########### MESSAGING ############


@app.route('/message', methods = ['GET'])
def message():
    args = request.args
    uid = args.get("uid")
    pholder = args.get("pholder")
    if len(pholder) > 0:
        pholder = "Hi, I would like to ask about the following product: " + pholder
    cmd = 'SELECT * FROM Messages_Sent_Received WHERE sender_email = (:sender1) AND receiver_email = (:sender2) OR sender_email = (:sender2) AND receiver_email = (:sender1) ORDER BY date_created, time_created';
    c = g.conn.execute(text(cmd), sender1 = session['email'], sender2 = uid);
    messages = c.fetchall()
    context = dict(useremail=session['email'], messages=messages, receiveremail = uid, pholder = pholder)
    return render_template("messages.html", **context)

@app.route('/createnewmessage', methods = ['POST'])
def createnewmessage():
    message_content = request.form['newmessage']
    args = request.args
    receiver = args.get("receiver")
    cmd = 'SELECT max(message_id) FROM Messages_Sent_Received';
    c = g.conn.execute(text(cmd));
    max_prod = c.fetchall()
    c.close()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
        
    cmd = 'INSERT INTO Messages_Sent_Received VALUES (:id, :content, :date_created, :time_created, :sender_email, :receiver_email, :referred_product)'
    c = g.conn.execute(text(cmd), id = max_prod[0][0] + 1, content = message_content, date_created = date.today(), time_created = current_time, sender_email = session['email'], receiver_email = receiver, referred_product = None)
    return redirect(url_for('.message', uid=receiver, pholder=''))
    
@app.route('/mymessages')
def mymessages():
    cmd = 'SELECT * FROM Users WHERE Users.email IN (SELECT receiver_email FROM Messages_Sent_Received WHERE sender_email = (:email) UNION SELECT sender_email FROM Messages_Sent_Received WHERE receiver_email = (:email))'
    c = g.conn.execute(text(cmd), email = session['email'])
    people = c.fetchall();
    context = dict(people=people)
    return render_template("allmessages.html", **context)
    
############## FOLLOW BUTTON ######


@app.route('/follow', methods=['GET'])
def follow():
    args = request.args
    uid = args.get("uid")
    try:
        cmd = 'INSERT INTO Followers VALUES (:user1, :follower1)';
        c = g.conn.execute(text(cmd), user1 = uid, follower1 = session['email']);
        c.close()
        return redirect(url_for('.profile', uid=uid))
    except:
        return redirect(url_for('.profile', uid=uid))
    

@app.route('/unfollow', methods=['GET'])
def unfollow():
    args = request.args
    uid = args.get("uid")
    try:
        cmd = 'DELETE FROM Followers WHERE follower_email = :user1 and user_email = :follower1';
        c = g.conn.execute(text(cmd), follower1 = uid, user1 = session['email']);
        c.close()
        return redirect(url_for('.profile', uid=uid))
    except:
        return redirect(url_for('.profile', uid=uid))

    
############## SEE ALL COURSES ######


@app.route('/courses')
def course():
    try:
        cmd = 'SELECT * FROM Class_Sections';
        c = g.conn.execute(text(cmd));
        courses = c.fetchall()
        c.close()
        context = dict(courses=courses)
        return render_template("courses.html", **context)
    except:
        return redirect('/')
    
    
@app.route('/selectcourse')
def select_course():
    args = request.args
    cid = args.get("cid")
    pid = args.get("pid")
    #try:
    cmd = 'SELECT * FROM Products_Posted as p WHERE p.product_id IN (SELECT product_id FROM Product_Class_Relation as pcr WHERE professor_id = :pid1 and course_id = :cid1)';
    cursor = g.conn.execute(text(cmd), pid1 = pid, cid1 = cid);
    posts = cursor.fetchall()
    cursor.close()

    cmd = 'SELECT * FROM Tags';
    cursor = g.conn.execute(text(cmd));
    tags = cursor.fetchall()
    cursor.close()
    context = dict(posts=posts, tags=tags)
    return render_template("posts.html", **context)
    #except:
    #    return redirect('/')
    
    

############ ADD POST #############


@app.route('/newpost')
def new_post():
    try:
        cmd = 'SELECT * FROM Tags';
        c = g.conn.execute(text(cmd));
        tags = c.fetchall()
        c.close()
        
        cmd = 'SELECT * FROM Class_Sections';
        c = g.conn.execute(text(cmd));
        classes = c.fetchall()
        c.close()
        
        context = dict(classes = classes, tags = tags)
        return render_template('newpost.html', **context)
    except:
        return redirect('/')
    

@app.route('/createnewpost', methods=['POST'])
def create_new_post():
    #Get all tags, classes, and products
    try:
        cmd = 'SELECT tag_id FROM Tags';
        c = g.conn.execute(text(cmd));
        tags = c.fetchall()
        c.close()

        cmd = 'SELECT course_id, professor_id FROM Class_Sections';
        c = g.conn.execute(text(cmd));
        classes = c.fetchall()
        c.close()

        cmd = 'SELECT max(product_id) FROM Products_Posted';
        c = g.conn.execute(text(cmd));
        max_prod = c.fetchall()
        c.close()

        values = []
        values.append(request.form['title'])
        values.append(request.form['description'])
        values.append(request.form['image'])
        values.append(request.form['tutoring_hourly_rate'])
        values.append(request.form['tutoring_schedule'])
        values.append(request.form['study_resource_price'])
        values.append(request.form['study_resource_download_url'])
        values = clear_null_entries(values)

        my_tags = []
        my_classes = []

        for t in tags:
            if (str(t[0])) in request.form:
                my_tags.append(t[0])
        for p in classes:
            if str(str(p[0]) + '-' + str(p[1])) in request.form:
                my_classes.append(tuple((p[0], p[1])))
        pid = max_prod[0][0]+1
        tutstu = 2
        if 'tutoring' in request.form:
            tutstu = 1

        #Insert product
        cmd = 'INSERT INTO Products_Posted VALUES (:email1, :pid1, :title1, :desc1, :date1, :tut1, :image1, :thr1, :ts1, :srp1, :srd1)';
        c = g.conn.execute(text(cmd), email1 = session['email'], pid1 = pid, title1 = values[0], 
                           desc1 = values[1], date1 = date.today(), tut1 = tutstu, image1 = values[2], 
                           thr1 = values[3], ts1 = values[4], srp1 = values[5], srd1 = values[6]);
        c.close()

        #Insert tags
        for t2 in my_tags:
            cmd = 'INSERT INTO Tagged_Products VALUES (:pid1, :tid1)';
            c = g.conn.execute(text(cmd), pid1 = pid, tid1 = t2)
            c.close()

        #Insert tags
        for c2 in my_classes:
            cmd = 'INSERT INTO Product_Class_Relation VALUES (:pid1, :prof1, :cid1)';
            c = g.conn.execute(text(cmd), pid1 = pid, prof1 = c2[1], cid1 = c2[0])
            c.close()
        return redirect('/')
    except:
        flash('Error creating post! Ensure all fields are entered correctly.')
        return redirect('/newpost')
    
    
    
##################### DELETE POST #######
    
    

@app.route('/deletepost', methods=['GET'])
def delete_post():
    args = request.args
    pid = args.get("pid")
    try:
        #Find whose post it is, make sure this matches with session
        cmd = 'SELECT user_email FROM Products_Posted WHERE product_id = :pid1';
        c = g.conn.execute(text(cmd), pid1 = pid);
        found_user = c.fetchall()
        c.close()
        if found_user[0][0] != session['email']:
            return redirect('/myprofile')

        #Delete post from products_posted
        cmd = 'DELETE FROM Products_Posted WHERE product_id = :pid1';
        c = g.conn.execute(text(cmd), pid1 = pid);
        c.close()
        return redirect('/myprofile')
    except:
        return redirect('/myprofile')
    
    
##################### DELETE REVIEW #######
    
    

@app.route('/deletereview', methods=['GET'])
def delete_review():
    args = request.args
    rid = args.get("rid")
    try:
        #Find whose review it is, make sure this matches with session
        cmd = 'SELECT reviewer_email, reviewed_email FROM Reviews WHERE review_id = :rid1';
        c = g.conn.execute(text(cmd), rid1 = rid);
        found_users = c.fetchall()
        c.close()
        if found_users[0][0] != session['email']:
            return redirect('/myprofile')

        #Delete review from person's page
        cmd = 'DELETE FROM Reviews WHERE review_id = :rid1';
        c = g.conn.execute(text(cmd), rid1 = rid);
        c.close()
        return redirect(url_for('.profile', uid=found_users[0][1]))
    except:
        return redirect('/')
    
    

##################### FILTERING POSTS #######

@app.route('/filteredposts', methods=['POST'])
def filter_posts():
    try:
        cmd = 'SELECT tag_id FROM Tags';
        c = g.conn.execute(text(cmd));
        tags = c.fetchall()
        c.close()

        my_tags = []

        for t in tags:
            if (str(t[0])) in request.form:
                my_tags.append(t[0])
        if len(my_tags) == 0:
            return redirect('/posts')

        values = '('
        for mt in my_tags:
            values = values + str(mt) + ','
        values = values[0:len(values)-1]
        values = values + ')'

        #Get products
        cmd = 'SELECT * FROM Products_Posted WHERE product_id IN ((SELECT product_id FROM Products_Posted) EXCEPT SELECT t2.product_id FROM ((SELECT product_id, tag_id FROM Products_Posted, (SELECT tag_id FROM Tags WHERE tag_id in '
        cmd = cmd + values + ') AS t) EXCEPT (SELECT * FROM Tagged_Products)) as t2)';
        c = g.conn.execute(text(cmd));
        posts = c.fetchall()
        c.close()

        cmd = 'SELECT * FROM Tags';
        cursor = g.conn.execute(text(cmd));
        alltags = cursor.fetchall()
        cursor.close()
        context = dict(posts=posts, tags=alltags)
        return render_template("posts.html", **context)
    except:
        return redirect('/posts')






    
    
##################### REVIEWS #######


@app.route('/newreview', methods=['GET'])
def new_review():
    args = request.args
    uid = args.get("uid")
    context = dict(current_user = uid)
    print(context)
    return render_template('newreview.html', **context)

@app.route('/createnewreview', methods=['POST'])
def create_new_review():
    try:
        uid = request.form['current_user']
        print(uid)

        values = []
        values.append(request.form['title'])
        values.append(request.form['description'])
        values.append(request.form['rating'])
        values = clear_null_entries(values)

        cmd = 'SELECT max(review_id) FROM Reviews';
        c = g.conn.execute(text(cmd));
        max_id = c.fetchall()
        rid = max_id[0][0]+1
        c.close()

        cmd = 'INSERT INTO Reviews VALUES (:rid1, :title1, :desc1, :rating1, :er1, :ed1, :date1)';
        c = g.conn.execute(text(cmd), rid1 = rid, title1 = values[0], desc1 = values[1], 
                           rating1 = values[2], er1 = session['email'], ed1 = uid, date1 = date.today());
        c.close()

        return redirect(url_for('.profile', uid=uid))
    except:
        flash('Error writing review! Ensure all fields are entered correctly.')
        return redirect(url_for('.new_review', uid=uid))

####################################

@app.route('/index')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print(name)
  cmd = 'INSERT INTO test(name) VALUES (:name1)';
  g.conn.execute(text(cmd), name1 = name);
  return redirect('/')



def clear_null_entries(values):
    for i in range(len(values)):
        if len(values[i]) == 0:
            values[i] = None
    return values
   
############ NEW ERROR PAGE ###################
@app.errorhandler(500)
def page_not_found(e):
    return redirect('/')

####################################



if __name__ == "__main__":
  import click

  app.secret_key = os.urandom(12)
  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()


