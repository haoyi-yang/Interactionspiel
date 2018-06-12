import sqlite3 as lite
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate, _pick_unused_card
import numpy as np

name_database = "game_information.db"
name_win_rate_table = "win_rate_table"

def get_win_rate(hole_card, community_card):
    win_rate = None
    if is_win_rate_in_database(hole_card, community_card):
        win_rate = get_win_rate_in_database(hole_card, community_card)
    else:
        win_rate = calculate_win_rate(hole_card, community_card)
        record_win_rate(win_rate, hole_card, community_card)

    if np.isreal(win_rate) and win_rate >= 0 and win_rate <= 1:
        return win_rate
    else:
        raise("invalid win_rate")


def get_broad_win_rate(hole_card, community_card):
    rpt_times = 10
    if is_win_rate_in_database(hole_card, community_card):
        win_rate = get_win_rate_in_database(hole_card, community_card)
    else:
        win_rate = calculate_broad_win_rate(hole_card, community_card, rpt_times)
    return win_rate

def record_win_rate(win_rate, hole_card, community_card):
    con = lite.connect('{name_db}'.format(name_db = name_database))
    tup = make_tuple2record(win_rate, hole_card, community_card)

    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS {name_tbl}(_Id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                     win_rate REAL, hole_card TEXT, community_card TEXT)".format(name_tbl = name_win_rate_table))
        cur.execute("INSERT INTO {name_tbl}(win_rate, hole_card, community_card) \
                                            VALUES(?, ?, ?)".format(
                                                name_tbl = name_win_rate_table), tup)
                                                
def make_tuple2record(win_rate, hole_care, community_card):
    tup = []
    tup.append(win_rate)
    tup.append(str(hole_care))
    tup.append(str(community_card))

    return tup

def is_win_rate_in_database(hole_card, community_card):
    db_var = []
    db_var.append(str(hole_card))
    db_var.append(str(community_card))

    con = lite.connect('{nd}'.format(nd = name_database))

    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS {name_tbl}(_Id INTEGER PRIMARY KEY AUTOINCREMENT, \
                    win_rate REAL, hole_card TEXT, community_card TEXT)".format(name_tbl = name_win_rate_table))
        cur.execute('SELECT win_rate FROM {name_tbl} WHERE hole_card=? AND community_card=?'.format(name_tbl = name_win_rate_table),db_var)
        res = cur.fetchone()

    if res == None:
        return False
    else:
        return True

def get_win_rate_in_database(hole_card, community_card):
    db_var = []
    db_var.append(str(hole_card))
    db_var.append(str(community_card))

    con = lite.connect('{nd}'.format(nd = name_database))

    with con:
        cur = con.cursor()
        cur.execute('SELECT win_rate FROM win_rate_table WHERE hole_card=? AND community_card=?',db_var)
        res = cur.fetchone()
        res = res[0]
    return res

def calculate_win_rate(hole_card, community_card):
    ls_win_rate = [.0 for _ in range(10)]
    rpt_times = 10
    counter = 0  ##the newer calculated win percentage must be the avarage number
    while True:
        newer_win_rate = estimate_hole_card_win_rate(nb_simulation = rpt_times,
                                                nb_player = 2, #####only consider 2 players situation
                                                hole_card=gen_cards(hole_card),
                                                community_card=gen_cards(community_card))
        ls_win_rate.pop(0)
        itered_win_rate = (ls_win_rate[-1] * counter + newer_win_rate) / (counter + 1)
        ls_win_rate.append(itered_win_rate)
        if (np.max(ls_win_rate) - np.min(ls_win_rate)) < 0.01:
            break
        counter = counter + 1


    return ls_win_rate[-1]

def calculate_broad_win_rate(hole_card, community_card, rpt_times):
    win_rate = estimate_hole_card_win_rate(nb_simulation = rpt_times,
                                                nb_player = 2, #####only consider 2 players situation
                                                hole_card=gen_cards(hole_card),
                                                community_card=gen_cards(community_card))
    return win_rate

def assuming_card(my_hole_card):
    return _pick_unused_card(2, my_hole_card)

def is_raise_limit_reached(round_state):
    street_now = round_state['street']
    raise_count = 0
    for term in round_state['action_histories'][street_now]:
        if term['action'] == 'RAISE':
            raise_count += 1
    
    if raise_count >= 3:
        return True
    else:
        return False

def get_self_bet(round_state, valid_actions):
    bet = (round_state['pot']['main']['amount'] - valid_actions[1]['amount']) / 2
    
    return bet

def get_stack(seats, uuid):
    str_uuid = uuid
    for player in seats:
        if player['uuid'] == str_uuid:
            return player['stack']
    raise('player not exists')