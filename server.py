#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
import logging
import os.path
from collections import namedtuple
from datetime import datetime, timedelta
from os import environ

from flask import Flask, render_template, send_from_directory, request, redirect



logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG', False)) else logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.update(
    DEBUG=bool(environ.get('DEBUG', False)),
    )


Vote = namedtuple('Vote', ['for_choice', 'by'])
TeamVotes = namedtuple('TeamVotes', ['team_str', 'votes'])

# Just wanna match on these strings, which are the team names AND substrings in each's URL:
TEAM_VOTES_DICT = {'unichance': None, 'textitdone': None, 'goya': None, 'skillmatrix': None, 'weatherselfie': None}
for t in TEAM_VOTES_DICT:
    # we only count 1st and 2nd votes, i.e. 1st and 2nd ranks
    TEAM_VOTES_DICT[t] = {1: [], 2: []}


HAS_VOTED = set()
FINISHED_VOTING = set()


@app.route('/')
def index():
    """Serve a self-refreshing page of the ranks.
    """
    sorted_teamvotes = sorted([TeamVotes(team_str=team, votes=TEAM_VOTES_DICT[team]) for team in TEAM_VOTES_DICT],
                              key=lambda t: len(t.votes[1]),
                              reverse=True)

    # in the case of a winner/runner-up draw, use supplementary votes
    if len(sorted_teamvotes[0].votes[1]) == len(sorted_teamvotes[1].votes[2]):
        rank_a = len(sorted_teamvotes[0].votes[1]) + len(sorted_teamvotes[0].votes[2])
        rank_b = len(sorted_teamvotes[1].votes[1]) + len(sorted_teamvotes[1].votes[2])
        if rank_a < rank_b:
            sorted_teamvotes[0], sorted_teamvotes[1] = sorted_teamvotes[1], sorted_teamvotes[0]

    winner = sorted_teamvotes[0].team_str if len(sorted_teamvotes[0].votes[1]) > 0 else None
    runnerup = sorted_teamvotes[1].team_str if len(sorted_teamvotes[0].votes[1]) > 0 else None


    return render_template('index.html', winner=winner, runnerup=runnerup, sorted_teamvotes=sorted_teamvotes)


@app.route('/yote')
def yote():
    """Callback URL to vote by sending a link to the PRODUCTFORGE account
    """
    logging.debug('incoming Yote on PRODUCTFORGE account')

    username = request.args.get('username')
    link = request.args.get('link')
    vote = None

    for team_str in TEAM_VOTES_DICT:
        if team_str in link:
            vote = Vote(for_choice=team_str, by=username)

            if username in FINISHED_VOTING:
                logging.info('rejected >2nd URL Yote - ' + str(vote))
                pass
            elif vote in TEAM_VOTES_DICT[team_str][1]:
                logging.info('rejected double URL Yote - ' + str(vote))
                pass
            elif username in HAS_VOTED:
                logging.info('recorded URL Yote 2 - ' + str(vote))
                TEAM_VOTES_DICT[team_str][2].append(vote)
                FINISHED_VOTING.add(username)
            else:
                logging.info('recorded URL Yote 1 - ' + str(vote))
                TEAM_VOTES_DICT[team_str][1].append(vote)
                HAS_VOTED.add(username)

            break

    return vote


@app.route('/yote/<team_account>')
def yote_channel(team_account):
    """Callback URL to vote by Yo-ing a PF3-<team> account (used by website buttons)
    """
    logging.debug('incoming Yote on ' + team_account + ' account')

    username = request.args.get('username')
    vote = None

    for team_str in TEAM_VOTES_DICT:
        if team_str in team_account:
            vote = Vote(for_choice=team_str, by=username)

            if username in FINISHED_VOTING:
                logging.info('rejected >2nd team account Yote - ' + str(vote))
                pass
            elif vote in TEAM_VOTES_DICT[team_str][1]:
                logging.info('rejected double team account Yote - ' + str(vote))
                pass
            elif username in HAS_VOTED:
                logging.info('recorded team account Yote 2 - ' + str(vote))
                TEAM_VOTES_DICT[team_str][2].append(vote)
                FINISHED_VOTING.add(username)
            else:
                logging.info('recorded team account Yote 1 - ' + str(vote))
                TEAM_VOTES_DICT[team_str][1].append(vote)
                HAS_VOTED.add(username)

            break

    return vote




@app.route('/reset')
def reset():
    """Resets all votes to 0.
    """
    logging.warn('reset TEAM_VOTES_DICT count')
    TEAM_VOTES_DICT = {}
    for team_str in TEAM_VOTES_DICT:
        TEAM_VOTES_DICT[team_str] = {1: [], 2: []}

    return redirect('/')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    app.run(host='0.0.0.0', port=port)
