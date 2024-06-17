# UWR Victoria Seadragons Team Splitter
# Quan Nguyen, on an afternoon where things seem boring.
# Do what you want with it, I offer no guarantee nor take any responsibility.

import asyncio
import datetime
import json
import pprint
from random import shuffle
from spond import spond
from flask import Flask
from google.cloud import firestore

app = Flask(__name__)

db = firestore.Client(project="team-maker-426414", database="vsddb")
creds = db.collection("credentials").document("quan").get().to_dict()
username = creds["username"]
password = creds["password"]
group_id = creds["group_id"]
group = db.collection("groups").document(group_id).get().to_dict()

@app.route("/")
def index():
    teams = split_team()
    output_str = ''
    for i, color in enumerate(['Oscuro', 'Claro']):
        output_str += str(f'<h3> {color}:</h3>')
        output_str += '<p>'
        for member in teams[i]:
            output_str += member['firstName'] + ' ' + member['lastName'] + '<br>'

        output_str += '</p>'

    return output_str

def read_json(file_name):
    with open(file_name) as f:
        d = json.load(f)

    return d


async def print_groups():
    s = spond.Spond(username=username, password=password)
    group = await s.get_group(group_id)
    pprint.pprint(group)

    await s.clientsession.close()


async def print_events(from_date):
    s = spond.Spond(username=username, password=password)
    events = await s.get_events(group_id=group_id, min_start=from_date, max_events=10)
    earliest_start = datetime.datetime(9999, 12, 31)
    earliest_event = { }
    for event in events:
        event_start = datetime.datetime.strptime(event['startTimestamp'], '%Y-%m-%dT%H:%M:%SZ')
        if event_start < earliest_start:
            earliest_event = event.copy()
            earliest_start = event_start

    #pprint.pprint(earliest_event)

    await s.clientsession.close()
    return earliest_event


def split_team():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    #asyncio.run(print_groups())
    utc_from_date = datetime.datetime.now(datetime.UTC)
    event = asyncio.run(print_events(utc_from_date))
    #group = read_json('group.json')
    #event = read_json('event.json')

    members = group['members']
    attendees_ids = event['responses']['acceptedIds']

    attendees = []
    for member in members:
        if member['id'] in attendees_ids:
            attendees.append(member)

    teams = [[], []]
    team_idx = 0
    for skill in ["3", "2", "1", "0"]:
        for sex in ["f", "m"]:
            segment = [x for x in attendees if x['skill'] == skill and x['sex'] == sex]
            if (len(segment) == 0):
                continue

            shuffle(segment)
            for member in segment:
                teams[team_idx].append(member)
                team_idx = (team_idx + 1) % 2

    shuffle(teams[0])
    shuffle(teams[1])
    shuffle(teams)

    return teams


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=9090, debug=True)