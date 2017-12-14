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

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    log('Recieved {}'.format(data))
    # We don't want to reply to ourselves
    if data['name'] != 'WORKOUT BOT' and data['name'] != 'TEST':
        send_debug_message("message detected")
        text = data['text'].lower()
        if '!help' in text:
            #Special command for Jeffrey Minowa
            send_wreck_message("available commands: !throw, !gym")
        elif '!gym' in text:
            send_debug_message("gym detected")
            if len(data['attachments']) > 0:
                #attachments are images or @mentions
                group_members = get_group_info(data['group_id']) #should get the groupme names of all members in the group.
                names = []
                for attachment in data["attachments"]:
                    if attachment['type'] == 'mentions': #grab all the people @'d in the post to include them
                        for mentioned in attachment['user_ids']:
                            for member in group_members:
                                if member["user_id"] == mentioned:
                                    names.append(member["nickname"])
                #append the poster to the list of names to be uodated in the database
                names.append(data['name'])
                add_to_db(names, "gym")
        elif '!throw' in text:
            send_debug_message("throw detected")
            if len(data['attachments']) > 0:
                # attachments are images or @mentions
                group_members = get_group_info(
                    data['group_id'])  # should get the groupme names of all members in the group.
                names = []
                for attachment in data["attachments"]:
                    if attachment['type'] == 'mentions':  # grab all the people @'d in the post to include them
                        for mentioned in attachment['user_ids']:
                            for member in group_members:
                                if member["user_id"] == mentioned:
                                    names.append(member["nickname"])
                # append the poster to the list of names to be uodated in the database
                names.append(data['name'])
                add_to_db(names, "throw")
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
                    "UPDATE wreck_data SET num_throw = num_throw+1, WHERE name = %s"),
                    (name, ))
                send_debug_message("throw +1 for %s" % name)
                if cursor.rowcount == 0:
                    cursor.execute(sql.SQL(
                        "INSERT INTO wreck_data values (%s, 1, 0)"),
                        (name,))
                    send_debug_message("added %s to the db" % name)
            elif string == "gym":
                cursor.execute(sql.SQL(
                    "UPDATE wreck_data SET num_gym = num_gym+1, WHERE name = %s"),
                    (name, ))
                send_debug_message("gym +1 for %s" % name)
                if cursor.rowcount == 0:
                    cursor.execute(sql.SQL(
                        "INSERT INTO wreck_data values (%s, 0, 1)"),
                        (name,))
                    send_debug_message("added %s to the db" % name)
            conn.commit()
            send_debug_message("committed %s" % name)
    except (Exception, psycopg2.DatabaseError) as error:
        send_debug_message(error)
    finally:
        if cursor is not None:
            cursor.close()
            conn.close()




