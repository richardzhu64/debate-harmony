# DOCUMENTATION

## General

I implemented a website that allows debaters to share and collaborate with each other through a web-based application called DebateHarmony using Javascript, Python,
SQL, HTML, and a tiny bit of CSS. The application includes features which connect debaters across the country to contribute to a wiki of resources, trade preparation, coordinate practice
rounds, seek coaching, and post judging opportunities. This was my final project for Harvard's CS50 class.

## Use
### HTML Pages

Apology: Displays apology message for errors.

Layout: Stores general layout of the webpage - the navbar is a bit different with the DebateHarmony symbol and a few dropdowns. Very similar functionality.

Register: Users have to register first before logging in to access the pages on the website. For each user, there are 6 parts to
registering: your name, username, password role (coach/debater), email, and contact info (optional). The register method then checks if the username  or email is already taken - if it is, it won't enter it into the
database and will return an apology.

Login: When logging in, you must enter your username and password. Then it stores the session ID and redirects to the "/" route.

Debater: This is the homepage for users whose role is "debater". It will display a welcome message with the user's name, and then 4 tables: trade
returns, practice round matches, coach matches, and judging posts by the user. For practice rounds and judging, the "/" route should update the
practice and judging tables in debate.db and delete any old requests/posts within 24 hours. The information in the tables provides everything needed
for the user to see trade results and gives user info for who they've been matched with. One distinction is that coach matches for debaters show the
maximum hours and minimum pay a coach requests so the negotiation can happen from there.

Coach: This is the homepage for users whose role is "coach". It will display a similar welcome message, any coaching matches and all judging
opportunities that have been posted. Similar to the debater homepage, but there are no trade matches nor practice round matches. One distinction is that
coach matches for coaches show the minimum hours and maximum pay that a debater requests, so that the negotiation can happen from there.

Trade: The trade form intakes a lot of information: a URL link to your prep, topic and contents for what you have, topic and contents for what you
receive, and any potential comments (optional). This trade information then gets stored as two entries in the trades table of debate.db - one for
what you have, one for what you want - both connected by having the same trade_id in the table. Required fields should be alerted in JS and
stopped in Python with apologies.

Practice: Much like trade, practice asks for your experience level, topic you want to debate, side you want to debate, the range of times you can
debate for, and any potential comments (optional). It then stores your request in the practice table in debate.db. Required fields should be alerted
in JS and stopped in Python with apologies.

Getcoach: The "hire a coach" option for debaters allows debaters to fill out a form to request a coach. It requires your event, maximum amount to pay,
minimum amount of hours you want to work, and potential comments. These results then get stored in the coaching table.

Getcoach: The "Offer to coach" option for coaches allows coaches to fill out a form to offer to coach. It requires your event, minimum amount to pay,
maximum amount of hours you want to work, and potential comments. These results then get stored in the coaching table.

Judge: Users are able to post judging opportunities through a form: the tournament, start/end dates, the event needed, and pay/payformat.
This info is then stored in the judging table.

Contacts: Contacts displays all of the users past trade, coach, and practice round matches. For coaches, this is limited to coachmatches.

Wiki: The "add to the wiki" option wiki provides a form with the event, a description of contents, and the URL. It then stores these entries
in the wiki table.

Wikiaccess: Displays all previous entries into the wiki. Anything that is uploaded to the wiki is shown when clicking "The wiki"

Change password: allows users to change their password by entering old password and new password + confirmation.
