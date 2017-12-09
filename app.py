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
        try:
            #set up connection to the database
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
            #add 1 to the number of posts of the person that posted
            cursor.execute(sql.SQL(
                "UPDATE wreck_data SET num_posts = num_posts+1 WHERE name = %s"),
                (data['name'],))
            if cursor.rowcount == 0:
                send_debug_message("adding %s to the database" % data['name'])
                cursor.execute(sql.SQL("INSERT INTO wreck_data VALUES (%s, 1, 0, 0, now()), %s"), (data['name'], data['user_id'],))
                send_debug_message("added %s to the group" % data['name'])
            conn.commit()
            cursor.close()
            conn.close()
        except (Exception, psycopg2.DatabaseError) as error:
            send_debug_message(error)
        text = data['text'].lower()
        if '!iloveyou' in text:
            #special command for Stephen Mock
            send_wreck_message("I love you too %s <3" % data['name'])
        elif '!help' in text:
            #Special command for Jeffrey Minowa
            send_wreck_message("available commands: !throw, !gym, !leaderboard")
        elif '!gym' in text or '!throw' in text:
            addition = 1.0 if "!gym" in text else 0.5
            if len(data['attachments']) > 0:
                #attachments are images or @mentions
                group_members = get_group_info(data['group_id']) #should get the groupme names of all members in the group.
                names = []
                found_attachment = False #This will track whether we found an image or not, which is required
                for attachment in data["attachments"]:
                    if attachment['type'] == 'image':
                        send_workout_selfie(data["name"] + " says \"" + data['text'] + "\"", attachment['url']) #send the workout selfie to the other groupme
                        found_attachment = True
                    if attachment['type'] == 'mentions': #grab all the people @'d in the post to include them
                        for mentioned in attachment['user_ids']:
                            for member in group_members:
                                if member["user_id"] == mentioned:
                                    names.append(member["nickname"])
                if found_attachment: #append the poster to the list of names to be uodated in the database
                    names.append(data['name'])
                    test_db_connection(names, addition)
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
                    "SELECT * FROM wreck_data WHERE workout_score > -1.0"),)
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


def test_db_connection(names, addition): #poorly named method. It works, but it didn't always work so it was just a "test"
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
        now = datetime.datetime.now()
        for name in names:
            cursor.execute(sql.SQL(
                "UPDATE wreck_data SET num_workouts = num_workouts+1, workout_score = workout_score+%s, last_post = now() WHERE name = %s"),
                [str(addition), name])
            if cursor.rowcount == 0:
                cursor.execute(sql.SQL("INSERT INTO wreck_data VALUES(%s, %s, %s, %s"), (name, "0", "1", str(addition),))
                send_debug_message("added %s to the group" % name)
            conn.commit()
            send_debug_message("committed %s" % name)
    except (Exception, psycopg2.DatabaseError) as error:
        send_debug_message(error)
    finally:
        if cursor is not None:
            cursor.close()
            conn.close()




