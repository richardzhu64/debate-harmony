import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date


from helpers import apology, login_required, usd, tradematch, practicematch, coachmatch

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///debate.db")


@app.route("/")
@login_required
def index():
    # remove old practice, judging requests from past days
    currentDate = date.today()
    db.execute("DELETE FROM practice WHERE date < :date", date=currentDate)
    db.execute("DELETE FROM judging WHERE enddate < :date", date=currentDate)
    r = db.execute("SELECT role FROM users WHERE id=:id", id=session["user_id"])
    if (r[0]["role"] == "debater"):
        return redirect("/debater")
    elif (r[0]["role"] == "coach"):
        return redirect("/coach")


@app.route("/debater")
@login_required
def debater():
    """ Debater homepage"""
    # get set of trades/practice/coaching and initialize variables
    name = db.execute("SELECT name FROM users WHERE id = :id", id=session["user_id"])[0]["name"]
    username = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])[0]["username"]
    userTrades = tradematch(session["user_id"])
    # create trade return list (contents) for html table
    contents = []
    potentialcontents = ["cases", "blocks", "briefs", "cards"]
    # add in trade contents for each trade return
    for u in userTrades:
        for p in potentialcontents:
            if u[p] == 1:
                contents.append(p)
    userPractice = practicematch(session["user_id"])
    userCoaches = coachmatch(session["user_id"])
    userJudges = db.execute("SELECT * FROM judging WHERE username=:username", username=username)
    return render_template("debater.html", name=name, userTrades=userTrades, tNumber=len(userTrades), contents=contents, userCoaches=userCoaches, cNumber=len(userCoaches),
                           userPractice=userPractice, pNumber=len(userPractice), userJudges=userJudges, jNumber=len(userJudges))


@app.route("/coach")
@login_required
def coach():
    """ Coach homepage """
    # get set of trades/practice/coaching and initialize variables
    name = db.execute("SELECT name FROM users WHERE id = :id", id=session["user_id"])[0]["name"]
    username = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])[0]["username"]
    userCoaches = coachmatch(session["user_id"])
    judging = db.execute("SELECT * FROM judging")
    return render_template("coach.html", name=name, userCoaches=userCoaches, cNumber=len(userCoaches), userJudges=judging, jNumber=len(judging))


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get("username")
    enteredEmail = request.args.get("email")
    if len(username) > 0 and not db.execute("SELECT * FROM users WHERE username=:username", username=username) and not db.execute("SELECT * FROM users WHERE email=:email", email=enteredEmail):
        return jsonify(True)
    return jsonify(False)


@app.route("/contacts")
@login_required
def contacts():
    name = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])[0]["name"]
    contacts = db.execute("SELECT * FROM contacts WHERE id=:id ORDER BY time DESC", id=session["user_id"])
    return render_template("contacts.html", name=name, contacts=contacts, cNumber=len(contacts))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("role"):
            return apology("must provide role", 400)
        elif not request.form.get("email"):
            return apology("must provide email", 400)
        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation must match", 403)
        # check if username is taken/add username to database
        check1 = db.execute("SELECT username FROM users WHERE username=:username", username=request.form.get("username"))
        if check1:
            return apology("Username is taken!", 403)
        check2 = db.execute("SELECT email FROM users WHERE email=:email", email=request.form.get("email"))
        if check2:
            return apology("Email is taken!", 403)
        role = request.form.get("role")
        check3 = db.execute("INSERT INTO users (name, username, role, hash, email, contact) VALUES (:name, :username, :role, :hash, :email, :contact)",
                            name=request.form.get("name"), username=request.form.get("username"), role=request.form.get("role"),
                            hash=generate_password_hash(request.form.get("password")), email=request.form.get("email"), contact=request.form.get("contact"))
        if not check3:
            return apology("Registration failed!", 403)
        # login automatically
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = :username",
                                        username=request.form.get("username"))[0]["id"]
        return redirect("/")


@app.route("/trade", methods=["GET", "POST"])
@login_required
def trade():
    """ Trade request route for debaters """
    if request.method == "GET":
        return render_template("trade.html")
    elif request.method == "POST":
        # check all data entry
        if not request.form.get("url"):
            return apology("must provide URL to prep", 400)
        elif not request.form.get("topic1"):
            return apology("must provide topic you have prep for", 400)
        elif not request.form.get("have"):
            return apology("must provide what prep you have", 400)
        elif not request.form.get("want"):
            return apology("must provide what prep you want", 400)
        elif not request.form.get("topic2"):
            return apology("must provide what topic you want prep for", 400)
        # assign variables for entries
        user = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])[0]
        url = request.form.get("url")
        topic1 = request.form.get("topic1")
        have = request.form.get("have")
        topic2 = request.form.get("topic2")
        want = request.form.get("want")
        comments = request.form.get("comments")
        current_trade_id = 0
        if db.execute("SELECT * FROM trades"):
            # get trade id (increment by 1)
            current_trade_id = db.execute("SELECT * FROM trades ORDER BY trade_id DESC LIMIT 1")[0]["trade_id"] + 1
        # insert have trade offer into contents db
        have_trade = db.execute("INSERT INTO trades (name, email, contact, username, hw, id, trade_id, topic, url, comments) VALUES (:name, :email, :contact, :username, :hw, :id, :trade_id, :topic, :url, :comments)",
                                name=user["name"], email=user["email"], contact=user["contact"], username=user["username"], hw=1, id=session["user_id"], trade_id=current_trade_id, topic=topic1, url=url, comments=comments)
        if not have_trade:
            return apology("trade offer failed", 403)
        # enter in specific contents in offer
        db.execute("UPDATE trades SET :h = :info WHERE trade_id=:trade_id AND hw=:hw",
                   h=have, info=1, trade_id=current_trade_id, hw=1)

        # insert generic request into contents db
        want_trade = db.execute("INSERT INTO trades (name, email, contact, username, hw, id, trade_id, topic, url) VALUES (:name, :email, :contact, :username, :hw, :id, :trade_id, :topic, :url)",
                                name=user["name"], email=user["email"], contact=user["contact"], username=user["username"], hw=0, id=session["user_id"], trade_id=current_trade_id, topic=topic2, url=url)
        if not want_trade:
            return apology("trade request failed", 403)
        # enter in specific contents in request
        db.execute("UPDATE trades SET :w = :info WHERE trade_id=:trade_id AND hw=:hw",
                   w=want, info=1, trade_id=current_trade_id, hw=0)

    return redirect("/")


@app.route("/practice", methods=["GET", "POST"])
@login_required
def practice():
    """Practice round request form/route for debaters"""
    if request.method == "GET":
        return render_template("practice.html")
    elif request.method == "POST":
        r = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])[0]['role']
        if r == "coach":
            return apology("sorry you're a coach, you can't do a practice round", 403)
        elif not request.form.get("experience"):
            return apology("must provide experience level", 400)
        elif not request.form.get("topic"):
            return apology("must provide topic you want to debate", 400)
        elif not request.form.get("side"):
            return apology("must provide what side you would like to debate", 400)
        elif not request.form.get("early"):
            return apology("must provide earliest time you can debate", 400)
        elif not request.form.get("late"):
            return apology("must provide latest time you can debate", 400)
        # assign variables for entries
        user = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])[0]
        # enter into practice table
        check = db.execute("INSERT INTO practice (name, username, email, contact, experience, side, topic, early, late, comments) VALUES (:name, :username, :email, :contact, :experience, :side, :topic, :early, :late, :comments)",
                           name=user["name"], email=user["email"], contact=user["contact"], username=user["username"], experience=request.form.get("experience"), side=request.form.get("side"), topic=request.form.get("topic"),
                           early=request.form.get("early"), late=request.form.get("late"), comments=request.form.get("comments"))
        if not check:
            return apology("could not request practice round", 403)
        return redirect("/")


@app.route("/getcoach", methods=["GET", "POST"])
@login_required
def getcoach():
    """ Coach request for debaters route"""
    if request.method == "GET":
        return render_template("getcoach.html")
    elif request.method == "POST":
        r = db.execute("SELECT role FROM users WHERE id=:id", id=session["user_id"])[0]["role"]
        if r == "coach":
            return apology("sorry you're a coach, you can't get a coach", 403)
        elif not request.form.get("event"):
            return apology("must provide event", 400)
        elif not request.form.get("maxpay"):
            return apology("must provide maximum pay", 400)
        # assign variables
        user = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])[0]
        # insert into coaching
        check = db.execute("INSERT INTO coaching (name, username, email, contact, role, event, minhours, maxpay, comments) VALUES (:name, :username, :email, :contact, :role, :event, :minhours, :maxpay, :comments)",
                           name=user["name"], email=user["email"], contact=user["contact"], username=user["username"], role="debater", event=request.form.get("event"), minhours=request.form.get("minhours"),
                           maxpay=request.form.get("maxpay"), comments=request.form.get("comments"))
        if not check:
            return apology("coaching request failed", 403)

        # return to homepage
        return redirect("/")


@app.route("/offercoach", methods=["GET", "POST"])
@login_required
def offercoach():
    """ Coaching offers for coaches route"""
    if request.method == "GET":
        return render_template("offercoach.html")
    elif request.method == "POST":
        r = db.execute("SELECT role FROM users WHERE id=:id", id=session["user_id"])[0]["role"]
        if r == "debater":
            return apology("sorry you're a debater, you can't offer to coach", 403)
        elif not request.form.get("event"):
            return apology("must provide event", 400)
        elif not request.form.get("minpay"):
            return apology("must provide minimum pay", 400)
        # assign variables
        user = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])[0]
        # insert into coaching
        check = db.execute("INSERT INTO coaching (name, username, email, contact, role, event, maxhours, minpay, comments) VALUES (:name, :username, :email, :contact, :role, :event, :maxhours, :minpay, :comments)",
                           name=user["name"], email=user["email"], contact=user["contact"], username=user["username"], role="coach", event=request.form.get("event"), maxhours=request.form.get("maxhours"),
                           minpay=request.form.get("minpay"), comments=request.form.get("comments"))
        if not check:
            return apology("coaching post failed", 403)

        # return to homepage
        return redirect("/")


@app.route("/judge", methods=["GET", "POST"])
@login_required
def judge():
    """Insert judging opportunity route"""
    if request.method == "GET":
        return render_template("judge.html")

    elif request.method == "POST":
        if not request.form.get("event"):
            return apology("must provide event", 400)
        elif not request.form.get("startdate"):
            return apology("must provide start date", 400)
        elif not request.form.get("enddate"):
            return apology("must provide end date", 400)
        elif not request.form.get("payformat"):
            return apology("must provide pay format", 400)
        elif not request.form.get("pay"):
            return apology("must provide pay", 400)
        # assign variables
        user = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])[0]
        # insert into judging db
        check = db.execute("INSERT INTO judging (name, username, email, contact, tournament, event, startdate, enddate, payformat, pay, comments) VALUES (:name, :username, :email, :contact, :tournament, :event, :startdate, :enddate, :payformat, :pay, :comments)",
                           name=user["name"], email=user["email"], contact=user["contact"], username=user["username"], tournament=request.form.get("tournament"), event=request.form.get("event"), startdate=request.form.get("startdate"),
                           enddate=request.form.get("enddate"), payformat=request.form.get("payformat"), pay=request.form.get("pay"),
                           comments=request.form.get("comments"))
        if not check:
            return apology("judging post failed", 403)

        # return to homepage
        return redirect("/")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """Change Password Route"""
    if request.method == "GET":
        return render_template("changepassword.html")
    else:
        # Ensure all entries exist new password and confirmation were submitted
        if not request.form.get("oldpassword"):
            return apology("must provid original password", 400)
        elif not request.form.get("newpassword"):
            return apology("must provide new password", 400)

        # Ensure password and confirmation match
        elif request.form.get("newpassword") != request.form.get("confirmation"):
            return apology("password and confirmation must match", 400)

        # check if old password is correct
        check = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])
        if not check_password_hash(check[0]["hash"], request.form.get("oldpassword")):
            return apology("original password incorrect", 400)
        # change password
        db.execute("UPDATE users SET hash = :hash WHERE id=:id",
                   id=session["user_id"], hash=generate_password_hash(request.form.get("newpassword")))
        return redirect("/logout")


@app.route("/wiki", methods=["GET", "POST"])
@login_required
def wiki():
    """ Insert into wiki route"""
    if request.method == "GET":
        return render_template("wiki.html")
    elif request.method == "POST":
        if not request.form.get("event"):
            return apology("must provide event for entry", 400)
        elif not request.form.get("description"):
            return apology("must provide description for entry", 400)
        elif not request.form.get("url"):
            return apology("must provide url for entry", 400)
        name = db.execute("SELECT name FROM users WHERE id=:id", id=session["user_id"])[0]["name"]
        check = db.execute("INSERT INTO wiki (name, event, description, url) VALUES (:name, :event, :description, :url)", name=name,
                           event=request.form.get("event"), description=request.form.get("description"), url=request.form.get("url"))
        if not check:
            return apology("could not enter into wiki", 403)
        return redirect("/wikiaccess")


@app.route("/wikiaccess", methods=["GET"])
@login_required
def wikiaccess():
    """Display wiki route"""
    wiki = db.execute("SELECT * FROM wiki ORDER BY date DESC")
    wlength = len(wiki)
    return render_template("wikiaccess.html", wiki=wiki, wlength=wlength)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
