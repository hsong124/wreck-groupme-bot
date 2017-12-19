import os
import urllib.parse
import sys
import json
import urllib.request
import datetime
import psycopg2
import random
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
        elif '!cardio' in text:
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
            rule = rulesXIII[rulePointer]
            send_wreck_message(rule)
        elif '!throw' in text:
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
            rule = rulesXIII[rulePointer]
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
        #leaderboard.sort(key=lambda s: s[], reverse=True) #sort the leaderboard by score descending
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




