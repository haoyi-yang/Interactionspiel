from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random as rand
import sqlite3 as lite

NB_SIMULATION = 1000

class ModelPlayer(BasePokerPlayer):

    table_name = "gameinfotbl"
    standard_insert = "Player_name, win_rate, hole_cards, community_cards, action, stack, small_blind_amount"
    db_name = "game_information.db"

    def __init__(self, name):

        self.name = name
        self.seat = None

        self.win_rate = None
        self.stack = None
        self.small_blind_amount = None
        self.hole_card = None
        self.community_card = None
        self.action = None
        self.raise_threshold = 0.5
        self.bluffing_ratio = 0.5
        self.__init_database()

    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        pot = round_state['pot']['main']['amount']
        self.win_rate = estimate_hole_card_win_rate(nb_simulation = NB_SIMULATION,
                                                nb_player = self.nb_player,
                                                hole_card=gen_cards(hole_card),
                                                community_card=gen_cards(community_card))
        choose_action, amount = self.choose_action(self.win_rate, pot, valid_actions)

        if choose_action == "FOLD":
            self.action = 0
        elif choose_action == "CALL":
            self.action = 1
        else:
            self.action = 2

        self.record_action()


        return choose_action, amount

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']
        self.small_blind_amount = game_info['rule']['small_blind_amount']
        for player in game_info['seats']:
            if game_info['seats'][player]['uuid'] == self.uuid:
                self.seat = player
            else:
                raise('not participating!')

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.self_bet = 0
        self.hole_card = hole_card

    def receive_street_start_message(self, street, round_state):
        self.community_card = round_state['community_card']

    def receive_game_update_message(self, action, round_state):
        if action['player_uuid'] == self.uuid:
            self.self_bet = self.self_bet + action['amount']

        self.stack = round_state['seats'][self.seat]['stack']

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    
    def record_action(self):
        msg_record = self.__make_message()

        con = lite.connect(self.db_name)

        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO ?(?) VALUES(?,?,?,?,?,?,?)", msg_record)





    #######################################################################

    def ev_calculation(self, win_rate, pot, call_amount):
        ev = [0 for i in range(3)]
        ev[0] = -self.self_bet
        ev[1] = win_rate * (pot - self.self_bet) - (1 - win_rate) * (self.self_bet + call_amount)
        ev[2] = win_rate * (pot - self.self_bet + 2 * self.small_blind_amount) - \
                        (1 - win_rate) * (self.self_bet + 2 * self.small_blind_amount + call_amount)
        return ev    

    def choose_action(self, win_rate, pot, valid_actions):                    
        r = rand.random()
        ev = self.ev_calculation(win_rate, pot, valid_actions[1]['amount'])
        if win_rate >= self.raise_threshold:
            return valid_actions[2]['action'], 2 * self.small_blind_amount
        elif r >= self.bluffing_ratio:
            return valid_actions[2]['action'], 2 * self.small_blind_amount
        elif ev[1] >= ev[0]:
            return valid_actions[1]['action'], valid_actions[1]['amount']
        else:
            return valid_actions[0]['action'], valid_actions[0]['amount']

    
    def __make_message(self):
        msg = []
        msg.append(self.table_name)
        msg.append(self.standard_insert)
        msg.append(self.name)
        msg.append(self.win_rate)
        msg.append(self.hole_card)
        msg.append(self.community_card)
        msg.append(self.action)
        msg.append(self.stack)
        msg.append(self.small_blind_amount)

        return msg


    def __init_database(self):
        con = lite.connect(self.db_name)

        with con:
            cur = con.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS {tbl_name}(_Id INTEGER PRIMARY KEY, Player_name TEXT, win_rate REAL,  \
                                                                hole_cards TEXT, community_cards TEXT, action INT, stack INT, small_blind_amount INT)".format(tbl_name = self.table_name))
