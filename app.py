import os
import urllib.parse
import sys
import json
import urllib.request
import datetime
import psycopg2
from psycopg2 import sql

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

rulesXIII = ["XIII.A. If the disc is on the ground, whether in- or out-of-bounds, any member of the team becoming offense may take possession of it.",
"XIII.A.1.If an offensive player picks up the disc, that player must put it into play.",
"XIII.A.2.If possession is gained at the spot where the disc is to be put into play, the thrower must establish a pivot at the spot of the disc.",
"XIII.A.3.If the disc comes to rest on the playing field proper , a member of the team becoming offense must put the disc into play within ten seconds after it comes to rest. After ten seconds elapse, a defensive player within three meters of the disc may announce disc in, and then initiate and continue the stall count, but only if a defensive player has given audible warnings of ten and five seconds (the pre-stall).",
"XIII.A.4.If the disc comes to rest other than on the playing field proper, a member of the team becoming offense must put the disc into play within twenty seconds after it comes to rest.",
"XIII.A.4.a.If the disc is not reasonably retrievable within twenty seconds (e.g., far out-of-bounds or through a crowd), the player retrieving it may request another disc and any delay or pre-stall count is suspended until the offensive player receives the new disc.",
"XIII.A.4.b.If the disc is in the end zone, after twenty seconds elapse, a defensive player within three meters of the disc may announce disc in, and then initiate and continue the stall count, but only if a defensive player has given audible warnings of twenty, ten and five seconds (the pre-stall).",
"XIII.A.4.c.If the disc is out-of-bounds, after twenty seconds elapse, a defensive player within three meters of the spot the disc is to be put into play may announce disc in, and then initiate and continue the stall count, but only if a defensive player has given audible warnings of twenty, ten and five seconds (the pre-stall)."
"XIII.A.5.If an offensive player unnecessarily delays putting the disc into play in violation of rule XIX.B, a defender within three meters of the spot the disc is to be put into play may issue a delay of game warning instead of calling a violation. If the behavior in violation of rule XIX.B is not immediately stopped, the marker may initiate and continue a stall count, regardless of the actions of the offense. In order to invoke this rule, after announcing delay of game, the marker must give the offense two seconds to react to the warning, and then announce disc in before initiating the stall count.",
"XIII.B.For a live disc to be put into play, the thrower must establish a pivot at the appropriate spot on the field, touch the disc to the ground, and put it into play."]
rulesXIV = ["XIV.A. Stalling: The period of time within which a thrower must release a throw may be timed by the stall count.",
            "XIV.A.1. The stall count consists of announcing stalling and counting from one to ten loudly enough for the thrower to hear.",
            "XIV.A.1.a. The interval between the first utterance of each number in the stall count must be at least one second.",
            "XIV.A.1.b. All stall counts initiated, reinitiated or resumed after a stoppage of play must start with the word stalling.",
            "XIV.A.1.c. If the count resets to one during a stoppage of play, it is considered a new count.",
            "XIV.A.2. Only the marker may initiate or continue a stall count, and may do so anytime a thrower has possession of a disc that is live or in play. However, directly after a turnover or thwen putting the pull into play the stall may not be initiated before a pivot is established, unless delay of game or pre-stall rules(XIII.A.3, XIII.A.4) apply.",
            "XIV.A.3. If the thrower has not released the disc at the first utterance of the word ten, it is a turnover. The marker loudly announces stall and play stops. A stall is not a violation and rule XVI.C does not apply.",
            "XIV.A.3.a. The marker calling the stall takes possession of the disc where the stall occurred and then may either:",
            "XIV.A.3.a.1. place the disc on the ground and after acknowledgment by the defense, touch the disc and loudly announce in play or",
            "XIV.A.3.a.2. retain possession and have the former thrower restart play with a check.",
            "XIV.A.3.b. The thrower may contest a stall call in the belief that the disc was released before the first utterance of the word ten. If a stall is contested:",
            "XIV.A.3.b.1. If the pass was complete, play stops and possession reverts to the thrower. After a check, the marker resumes the stall count at 8.",
            "XIV.A.3.b.2. If the pass was incomplete, it is a turnover; play stops and resumes with a check.",
            "XIV.A.4. If the defense switches markers, the new marker must reinitiate the stall count . A marker leaving the three-meter radius and returning is considered a new marker.",
            "XIV.A.5. If a stall count is interrupted by a call, the thrower and marker are responsible for agreeing on the correct count before the check.  The count reached is the last number fully uttered by the marker before the call. The count is resumed with the word stalling followed by the number listed below:",
            "XIV.A.5.a.1. General rules: 1. Uncontested defensive foul or violation: 1. ",
            "XIV.A.5.a.2. Uncontested offensive foul or violation: Count reached plus 1, or 9 if over 8",
            "XIV.A.5.a.3. Contested foul or violation: Count reached plus 1, or 6 if over 5",
            "XIV.A.5.a.4. Offsetting calls: Count reached plus 1, or 6 if over 5",
            "XIV.A.5.a.5. Unresolved calls: Count reached plus 1, or 6 if over 5",
            "XIV.A.5.b.1. Specific Rules: Pick: Count reached plus 1, or 6 if over 5",
            "XIV.A.5.b.2. Marking violation (no stoppage): Count reached minus 1, no stalling",
            "XIV.A.5.b.3. Contested stall: First Call:8, Second and Subsequent calls when due to a fast count: 6",
            "XIV.A.5.b.4. Defensive technical time-out: Count reached plus 1, or 6 if over 5",
            "XIV.A.5.b.5. Offensive technical time-out: Count reached plus 1, or 9 if over 8",
            "XIV.A.5.b.6. Obstruction within 5 meters of playing field: Count reached plus 1, or 9 if over 8"]
@app.route('/', methods=['POST'])


def webhook():
    data = request.get_json()
    log('Recieved {}'.format(data))
    # We don't want to reply to ourselves
    if data['name'] != 'WerkBot' and data['name'] != 'testwreckbot':
        #send_debug_message("message detected")
        text = data['text'].lower()
        
        if '!help' in text:
            #Special command for Jeffrey Minowa
            send_wreck_message("available commands: !throw, !cardio")
        if '!cardio' in text:
            #send_debug_message("cardio detected")
            names = []
            if len(data['attachments']) > 0:
                #attachments are images or @mentions
                group_members = get_group_info(data['group_id']) #should get the groupme names of all members in the group.
                for attachment in data["attachments"]:
                    if attachment['type'] == 'mentions': #grab all the people @'d in the post to include them
                        for mentioned in attachment['user_ids']:
                            for member in group_members:
                                if member["user_id"] == mentioned:
                                    names.append(member["nickname"])
                #append the poster to the list of names to be uodated in the database
            names.append(data['name'])
            add_to_db(names, "gym")
            total = getTotal()
            rulePointer = total % 10
            rule = rulesXIV[rulePointer]
            send_wreck_message(rule)
        if '!throw' in text:
            #send_debug_message("throw detected")
            names = []
            if len(data['attachments']) > 0:
                # attachments are images or @mentions
                group_members = get_group_info(
                    data['group_id'])  # should get the groupme names of all members in the group.
                for attachment in data["attachments"]:
                    if attachment['type'] == 'mentions':  # grab all the people @'d in the post to include them
                        for mentioned in attachment['user_ids']:
                            for member in group_members:
                                if member["user_id"] == mentioned:
                                    names.append(member["nickname"])
                # append the poster to the list of names to be uodated in the database
            names.append(data['name'])
            add_to_db(names, "throw")
            total = getTotal()
            rulePointer = total % 10
            rule = rulesXIV[rulePointer]
            send_wreck_message(rule)
        """
        elif '!leaderboard' in text: #post the leaderboard in the groupme
            try:
                urllib.parse.uses_netloc.append("postgres")
                url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
                conn = psycopg2.connect(
                    database=url.path[1:],
                    user=url.username,
                    password=url.password,
                    host=url.hostname,
                    port=url.port
                )
                cursor = conn.cursor()
                #get all of the people who's workout scores are greater than -1 (any non players have a workout score of -1)
                cursor.execute(sql.SQL(
                    "SELECT * FROM wreck_data WHERE num_throw > -1.0 and num_gym > -1.0"),)
                leaderboard = cursor.fetchall()
                leaderboard.sort(key=lambda s: s[3], reverse=True) #sort the leaderboard by score descending
                string1 = "Top 15:\n"
                string2 = "Everyone Else:\n"
                for x in range(0, 15):
                    string1 += '%d) %s with %.1f points \n' % (x + 1, leaderboard[x][0], leaderboard[x][3])
                for x in range(15, len(leaderboard)):
                    string2 += '%d) %s with %.1f points \n' % (x + 1, leaderboard[x][0], leaderboard[x][3])
                send_wreck_message(string1) #need to split it up into 2 because groupme has a max message length for bots
                send_wreck_message(string2)
                cursor.close()
                conn.close()
            except (Exception, psycopg2.DatabaseError) as error:
                send_debug_message(error)
        """
    return "ok", 200

def getTotal():
    total = 0
    try:
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cursor = conn.cursor()
        #get all of the people who's workout scores are greater than -1 (any non players have a workout score of -1)
        cursor.execute(sql.SQL(
            "SELECT * FROM wreck_data WHERE num_throw > -1.0 and num_gym > -1.0"),)
        leaderboard = cursor.fetchall()
        for x in range(0, len(leaderboard)):
            total += leaderboard[x][1] # add a person's throw score
            total += leaderboard[x][2] # add a persnon's gym score
        cursor.close()
        conn.close()
        return total
    except (Exception, psycopg2.DatabaseError) as error:
        send_debug_message(error)
        return 0
        
    
def send_wreck_message(msg):
    send_message(msg, os.getenv("WRECK_BOT_ID"))


def send_message(msg, bot_ID):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id': bot_ID,
        'text': msg,
    }
    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()


def send_workout_selfie(msg, image_url):
    send_message(msg, os.getenv("WORKOUT_BOT_ID"))
    send_message(image_url, os.getenv("WORKOUT_BOT_ID"))

def send_debug_message(msg):
    send_message(msg, os.getenv("TEST_BOT_ID"))

def log(msg):
    print(str(msg))
    sys.stdout.flush()


def get_group_info(group_id):
    with urllib.request.urlopen("https://api.groupme.com/v3/groups/%s?token=%s" % (
    group_id, os.getenv("ACCESS_TOKEN"))) as response:
        html = response.read()
    dict = parse_group_for_members(html)
    return dict["response"]["members"]


def parse_group_for_members(html_string):
    return json.loads(html_string)


def add_to_db(names, string): #poorly named method. It works, but it didn't always work so it was just a "test"
    send_debug_message(str(names))
    cursor = None
    conn = None
    try:
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cursor = conn.cursor()
        for name in names:
            if string == "throw":
                cursor.execute(sql.SQL(
                    "UPDATE wreck_data SET num_throw = num_throw+1 WHERE name = %s"),
                    (name, ))
                send_debug_message("throw +1 for %s" % name)
                if cursor.rowcount == 0:
                    cursor.execute(sql.SQL(
                        "INSERT INTO wreck_data values (%s, 1, 0)"),
                        (name,))
                    #send_debug_message("added %s to the db" % name)
            elif string == "gym":
                cursor.execute(sql.SQL(
                    "UPDATE wreck_data SET num_gym = num_gym+1 WHERE name = %s"),
                    (name, ))
                #send_debug_message("gym +1 for %s" % name)
                if cursor.rowcount == 0:
                    cursor.execute(sql.SQL(
                        "INSERT INTO wreck_data values (%s, 0, 1)"),
                        (name,))
                    #send_debug_message("added %s to the db" % name)
            conn.commit()
            #send_debug_message("committed %s" % name)
    except (Exception, psycopg2.DatabaseError) as error:
        pass
    finally:
        if cursor is not None:
            cursor.close()
            conn.close()




