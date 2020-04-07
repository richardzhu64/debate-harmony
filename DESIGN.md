Most of the technical stuff was done with Python and SQL. Let's talk about the main parts.

Also, in advance I apologize for the long db.execute statements. For some reason I couldn't split the string correctly in Python, so it's kind of hard
to read. The logic there is pretty simple though - it's just inserting and/or selecting using db.execute. Thanks!

### Debate Database

## Users
Users stores the user id, name, username, role, hash, email, and contact info (optional). This info is important for displaying to potential
matches, and also just to track users. The role column specifically allowed me to prevent users from going to the wrong pages and messing up entries
(ie. debaters "offering to coach" or coaches trying to hire coaches), and also let me display different homepages for different user roles.

## Trades
Oofta. This one has a lot of information, with id, name, usernname, email, contact, trade_id, hw, topic, url, cases, blocks, briefs, cards, and
sentemail. All the identifiers are for giving to a potential match (except for ID, which allows us to find all the trade requests of a user). Trade_id
provides an ID for each trade request which comprises of two entries - one in which hw (standing for have/want) is 1 and one where it's 0. I
defined hw=1 as what the user has/is offering and hw=0 as what the user wants to receive. From there, the provided URL is attached to both entries
along with 1 being entered for whichever content the user desires (cases, blocks, briefs, or cards) and which one they already have. At the end,
each trade "request" results in two trades table entries with the same trade_id, one with hw=1 and one of cases/blocks/briefs/cards set to 1, and one
with hw=0 and cases/blocks/briefs/cards set to 1. Any additional comments are optional.

The sentemail column was made to ensure that the first time a user's trade request was matched up, they got an email. The details will be explained
later, but basically sentemail stores whether or not the user's trade request has been matched before.

## Practice
This table stores practice rounds, with the same user identifiers from trades in addition to practice_id, experience, topic, side, and
earliest/latest times and sentemail. The practice table was meant to store only requests from each day, so the earliest and latest times provide
user availability. Each practice request has its own unique practice_id, allowing us to update sentemail similar to trade above. Like with trades,
comments are optional.

The date column is especially important. Since I wanted to have a database that was accurate in availability for each day, I created the column so
that every time a user logged in, the practice table was updated to remove any old requests from days past by comparing the entered date to the
current date.

## Coaching
This table stores coaching requests and offers, with the same user identifiers from trades but also role, coach_id, event, maximum/minimum
pay, max/min hours, and sentemail. For each of the maximum/minimum variables, I set the default to 0 - I assumed that for each debater, there was
no minimum amount they wanted to pay (anyone would want to get coaching for free) or maximum hours (an always available coach is always good). Similarly,
there's no max amount of pay or minimum amount of hours to work for coaches. The sentemail column works the same way as above, and each entry has its
own unique coach_id for that purpose. Comments are optional.

## Judging
The judging table contains the same user identifiers in addition to tournament, start/end dates, pay, and pay format. Rather than matching up users,
it simply creates a database of opportunities to show all coaches who may want to judge.

Similar to practice, judging also has a built-in mechanism to clean through its entries. When a user logs in, they delete any entries in judging where
the current date is past the end-date.

## Contacts
The contacts table contains all potentially made contacts by all users. Each contact information has identifiers for each contact, a date, and the
user's ID. This way, each user has unique set of contacts for which the user_ID is the id. This table is then displayed in contacts and is updated
in the match methods that I'll discuss below.

# WIKI
The wiki database contains all entries into the wiki - name, event, description, URL, and date. It's displayed in the wikiaccess.html page, ordered
by date added with the most recent entries at the top.

You may be thinking, why do you have the same identifiers for each table instead of just referring back to the users database repeatedly? I initailly
tried creating this connection, but found that when displaying it in HTML form, it was easier to simply have it as an entry in the tables. I decided
to just enter them into each table when entering in the other information gotten from the HTML forms.

### METHODS

These 3 methods are in helpers.py - tradematch, coachmatch, and practicematch. I also used usd formatting, but that was from CS50. These are the
mechanisms for matching trades, practice rounds, and coaching.

## tradematch
For tradematch, I started by creating a list of all trade_id's associated with the user. I then created a separate list of dicts containing all of
the trades of the user. Then, I created a for loop to parse through every trade_id associated with the user and found the "have" and the "want" entry
for each ID. Then, I find matches for both the have and the want entries by testing all of the specifications from the entire trades table,
create a lists of the trade_ids of these entries, and find the intersection of the two lists to find the "overall" matches.
Then, I add each match into the overall match set that is ultimately returned, but in the mean time also send an email that I'll get into later.
For each parse through the for loop of the "overall" matches, an email is potentially sent to the "match" email and the contact information
is potentially added to the user's contacts. At the end, we return the compiled list of all "overall" matches.

## practicematch
For practicematch, the method is quite similar. we first take in all the requests that the user has submitted (during that day, since we update
the database each day) and create a for loop, finding matches for each individual request based on the specifications. We then add the individual
matches for one request to the overall list of matches before a for loop that (potentially) sends an email and adds contact info to the user's contact
list for each individual match. Importantly, the method returns a match in time if the time range of the two requests overlap (for example, 4-6 PM and
5-7PM would constitute a match). If a user wants to be affirmative, then they will only be matched with negative teams, same with vice versa. If a
request states it can be either team, then side becomes irrelevant to the matching. At the end, the method returns the compiled list of practice matches.

## coachmatch
Coachmatch is basically identical to practicematch in its mechanics except for changing the specifications for a match. If the pay range and hour range
match ($0-300 for minimum 5 hours and $250 minimum for 0-10 hours would overlap and thus match), then the requests are considered matches. One key
difference is that only coaches and debaters can match - debaters cannot match with other debaters, nor can coaches match with coaches. The same
email and contact mechanism then applies before returning the entire list of coach matches.
## email stuff
For emailing, I chose to use the SMTP server to send an email. I created an email account for the site (debaterharmony@gmail.com) to notify users for'
the first time their request finds a match. After checking to see if this specific request has already een sent an email, it updates the sentemail
of that entry to say it has received an email, then sends an email message to the match's email address from debaterharmony.

## contact stuff
For contact, it checks whether the match's username is already in the user's contacts - if so, then it does not add it again. However, if it isn't
in the user's contacts, then it adds the information of the match to the user's contact table under its ID.