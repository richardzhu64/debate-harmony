import requests
import urllib.parse
import smtplib
import os

from datetime import date
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///debate.db")


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def usd(value):
    """Format value as USD."""
    return f"${value}"


def tradematch(id):
    """ Trade matching method"""
    # create list of all trade_id of requested trades for user
    requested = db.execute("SELECT trade_id FROM trades WHERE id=:id", id=id)
    requestedID = []
    for r in requested:
        temp = r["trade_id"]
        requestedID.append(temp)
    # make all unique trade_id
    requestedID = list(set(requestedID))
    # create list of all trades of user
    details = db.execute("SELECT * FROM trades WHERE id=:id", id=id)
    # initialize final list of successful trades
    receive = []
    # for loop to parse through each trade_id and matches for each ID
    for r in requestedID:
        for d in details:
            if (d["trade_id"] == r):
                if (d["hw"] == True):
                    have = d
                else:
                    want = d
        # create matches for request and offer, intersection set is overall match
        wantmatches = db.execute("SELECT trade_id FROM trades WHERE hw=:hw AND cases=:cases AND blocks=:blocks AND briefs=:briefs AND cards=:cards AND topic=:topic AND id!=:id",
                                 hw=1, cases=want["cases"], blocks=want["blocks"], briefs=want["briefs"], cards=want["cards"], topic=want["topic"], id=id)
        havematches = db.execute("SELECT trade_id FROM trades WHERE hw=:hw AND cases=:cases AND blocks=:blocks AND briefs=:briefs AND cards=:cards AND topic=:topic AND id!=:id",
                                 hw=0, cases=have["cases"], blocks=have["blocks"], briefs=have["briefs"], cards=have["cards"], topic=have["topic"], id=id)
        wantID = []
        haveID = []
        for w in wantmatches:
            wantID.append(w["trade_id"])
        for h in havematches:
            haveID.append(h["trade_id"])
        # create intersection list
        matches = list(set(wantID).intersection(set(haveID)))
        # add each of matches to overall receive for user
        for m in matches:
            # add match
            receive.extend(db.execute("SELECT * FROM trades WHERE trade_id=:trade_id AND hw=:hw", trade_id=m, hw=1))
            # send email to the person who got matched (for first time they get matched)
            if (db.execute("SELECT sentemail FROM trades WHERE trade_id=:trade_id", trade_id=m)[0]["sentemail"] == 0):
                db.execute("UPDATE trades SET sentemail=:sentemail WHERE trade_id=:trade_id", sentemail=1, trade_id=m)
                recipient = db.execute("SELECT email FROM trades WHERE trade_id=:trade_id AND hw=:hw", trade_id=m, hw=1)[0]['email']
                msg = "\r\n".join([
                                  "From: debaterharmony@gmail.com",
                                  "To: <"+recipient+">",
                                  "Subject: Trade Successful",
                                  "",
                                  "We successfully found a trade with someone!"
                                  ])
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.ehlo()
                server.starttls()
                server.login("debaterharmony@gmail.com", "cs502018")
                server.sendmail("debaterharmony@gmail.com", recipient, msg)
            # add match to contact list (if not there already)
            username = db.execute("SELECT username FROM trades WHERE trade_id=:trade_id", trade_id=m)[0]["username"]
            if not db.execute("SELECT * FROM contacts WHERE id=:id AND username=:username", id=id, username=username):
                c = db.execute("SELECT * FROM users WHERE username=:username", username=username)
                db.execute("INSERT INTO contacts (id, name, username, email, contact) VALUES (:id, :name, :username, :email, :contact)",
                           id=id, name=c[0]["name"], username=c[0]["username"], email=c[0]["email"], contact=c[0]["contact"])
    return receive


def practicematch(id):
    """ Practice round matching method"""
    # take in coach offer/requests from user
    username = db.execute("SELECT username FROM users WHERE id=:id", id=id)[0]['username']
    request = db.execute("SELECT * FROM practice WHERE username=:username", username=username)
    # create overall matches, matches for specific requests variables
    matches = []
    # find matches for each individual request
    for r in request:
        if r["side"] == "aff":
            rmatches = db.execute("SELECT * FROM practice WHERE experience=:experience AND topic=:topic AND side!=:side AND (early<=:late OR late>=:early) AND username !=:username",
                                  experience=r["experience"], topic=r["topic"], side="aff", late=r["late"], early=r["early"], username=username)
        elif r["side"] == "neg":
            rmatches = db.execute("SELECT * FROM practice WHERE experience=:experience AND topic=:topic AND side !=:side AND (early<=:late OR late>=:early) AND username !=:username",
                                  experience=r["experience"], topic=r["topic"], side="neg", late=r["late"], early=r["early"], username=username)
        else:
            rmatches = db.execute("SELECT * FROM practice WHERE experience=:experience AND topic=:topic AND (early<=:late OR late>=:early) AND username !=:username",
                                  experience=r["experience"], topic=r["topic"], late=r["late"], early=r["early"], username=username)
        # add individual matches to overall match set
        matches.extend(rmatches)
        for m in rmatches:
            # send email to the person who got matched (for first time their request gets matched)
            if (db.execute("SELECT sentemail FROM practice WHERE practice_id=:id", id=m["practice_id"])[0]["sentemail"] != 1):
                db.execute("UPDATE practice SET sentemail=:sentemail WHERE practice_id=:id", id=m["practice_id"], sentemail=1)
                recipient = db.execute("SELECT email FROM practice WHERE practice_id=:id", id=m["practice_id"])[0]['email']
                msg = "\r\n".join([
                                  "From: debaterharmony@gmail.com",
                                  "To: <"+recipient+">",
                                  "Subject: Practice Round Match",
                                  "",
                                  "We successfully matched you with someone for a practice round!"
                                  ])
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.ehlo()
                server.starttls()
                server.login("debaterharmony@gmail.com", "cs502018")
                server.sendmail("debaterharmony@gmail.com", recipient, msg)
            # add match to contact list (if not there already)
            username = db.execute("SELECT username FROM practice WHERE practice_id=:id", id=m["practice_id"])[0]["username"]
            if not db.execute("SELECT * FROM contacts WHERE id=:id AND username=:username", id=id, username=username):
                c = db.execute("SELECT * FROM users WHERE username=:username", username=username)
                db.execute("INSERT INTO contacts (id, name, username, email, contact) VALUES (:id, :name, :username, :email, :contact)",
                           id=id, name=c[0]["name"], username=c[0]["username"], email=c[0]["email"], contact=c[0]["contact"])
    # return all matches
    return matches


def coachmatch(id):
    """ Coaching match method """
    username = db.execute("SELECT username FROM users WHERE id=:id", id=id)[0]["username"]
    role = db.execute("SELECT role FROM users WHERE id=:id", id=id)
    # take in coach offer/requests from user
    request = db.execute("SELECT * FROM coaching WHERE username=:username", username=username)
    # create individual and overall match variables
    matches = []
    cmatches = []
    for r in request:
        # find individual matches based on role
        if role[0]["role"] == "debater":
            cmatches = db.execute("SELECT * FROM coaching WHERE event=:event AND role=:role AND (minpay<=:maxpay OR maxpay>=:minpay) AND (minhours<=:maxhours OR maxhours>=:minhours)",
                                  event=r["event"], role="coach", maxpay=r["maxpay"], minpay=r["minpay"], maxhours=r["maxhours"], minhours=r["minhours"])
        else:
            cmatches = db.execute("SELECT * FROM coaching WHERE event=:event AND role=:role AND (minpay<=:maxpay OR maxpay>=:minpay) AND (minhours<=:maxhours OR maxhours>=:minhours)",
                                  event=r["event"], role="debater", maxpay=r["maxpay"], minpay=r["minpay"], maxhours=r["maxhours"], minhours=r["minhours"])
        # add individual matches to overall list
        matches.extend(cmatches)
        # add contact and send email loop
        for c in cmatches:
            # send email to the person who got matched (for first time their request gets matched)
            if (db.execute("SELECT sentemail FROM coaching WHERE coach_id=:id", id=c["coach_id"])[0]["sentemail"] != 1):
                db.execute("UPDATE coaching SET sentemail=:sentemail WHERE coach_id=:id", id=c["coach_id"], sentemail=1)
                recipient = db.execute("SELECT email FROM coaching WHERE coach_id=:id", id=c["coach_id"])[0]['email']
                msg = "\r\n".join([
                                  "From: debaterharmony@gmail.com",
                                  "To: <"+recipient+">",
                                  "Subject: Coaching Match",
                                  "",
                                  "We successfully matched you with someone for coaching!"
                                  ])
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.ehlo()
                server.starttls()
                server.login("debaterharmony@gmail.com", "cs502018")
                server.sendmail("debaterharmony@gmail.com", recipient, msg)
            # add match to contact list (if not there already)
            username = db.execute("SELECT username FROM coaching WHERE coach_id=:id", id=c["coach_id"])[0]["username"]
            if not db.execute("SELECT * FROM contacts WHERE id=:id AND username=:username", id=id, username=username):
                c = db.execute("SELECT * FROM users WHERE username=:username", username=username)
                db.execute("INSERT INTO contacts (id, name, username, email, contact) VALUES (:id, :name, :username, :email, :contact)",
                           id=id, name=c[0]["name"], username=c[0]["username"], email=c[0]["email"], contact=c[0]["contact"])
    return matches