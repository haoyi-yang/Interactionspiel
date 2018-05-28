from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
from utils import get_win_rate
import sqlite3 as lite

class RationalPlayer(BasePokerPlayer):

    def __init__(self, name):
        self.name = name
        self.name_table = "record_rationalplayer_{nm}".format(nm = name)
        self.win_rate = None
        self.small_blind_amount = None
        self.hole_card = None
        self.community_card = None
        self.action = None
        self.db_name = "game_information.db"
        self.__init_database()

    def declare_action(self, valid_actions, hole_card, round_state):
        self.community_card = round_state['community_card']
        self.hole_card = hole_card
        call_amount = valid_actions[1]['amount']
        pot = round_state['pot']['main']['amount']
        self.win_rate = get_win_rate(self.hole_card, self.community_card)
        ev = self.ev_calculation(self.win_rate, pot, call_amount)

        if ev.index(max(ev)) == 0:
            self.action = 0
            self.record_action()
            return valid_actions[0]['action'], valid_actions[0]['amount']

        elif ev.index(max(ev)) == 1:
            self.action = 1
            self.record_action()            
            return valid_actions[1]['action'], valid_actions[1]['amount']

        else:
            self.action = 2
            self.record_action()            
            return valid_actions[2]['action'], 2 * self.small_blind_amount
                        


    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']
        self.uuid = game_info['seats'][0]
        self.small_blind_amount = game_info['rule']['small_blind_amount']

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.self_bet = 0

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        if action['player_uuid'] == self.uuid:
            self.self_bet = self.self_bet + action['amount']

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    def ev_calculation(self, win_rate, pot, call_amount):
        ev = [0 for i in range(3)]
        ev[0] = -self.self_bet
        ev[1] = win_rate * (pot - self.self_bet) - (1 - win_rate) * (self.self_bet + call_amount)
        ev[2] = win_rate * (pot - self.self_bet + 2 * self.small_blind_amount) - (1 - win_rate) * (self.self_bet + 2 * self.small_blind_amount + call_amount)
        return ev

    def __init_database(self):
        con = lite.connect(self.db_name)

        with con:
            cur = con.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS {tbl_name}(_Id INTEGER PRIMARY KEY, win_rate REAL,  \
                                                                hole_cards TEXT, community_cards TEXT, action INT, small_blind_amount INT)".format(tbl_name = self.name_table))

    def __make_message(self):
        msg = []
        msg.append(self.win_rate)
        msg.append(str(self.hole_card))
        msg.append(str(self.community_card))
        msg.append(self.action)
        msg.append(self.small_blind_amount)

        return msg                                                            

    def record_action(self):
        msg_record = self.__make_message()

        con = lite.connect(self.db_name)

        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO {nm_tbl}(win_rate, hole_cards, community_cards, action, small_blind_amount) VALUES(?,?,?,?,?)".format(nm_tbl = self.name_table), msg_record)