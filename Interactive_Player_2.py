from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random
from utils import get_win_rate, get_stack, is_raise_limit_reached
import numpy as np
import sqlite3 as lite

db_name = 'game_information.db'
class InteractivePlayer(BasePokerPlayer):
    def __init__(self):
        self.raise_threshold_defensive = 0.8
        self.fold_threshold_defensive = 0.5
        self.bluffing_max_defensive = 0.3
        
        self.raise_threshold_aggressive = 0.6
        self.fold_threshold_aggressive = 0.2
        self.bluffing_max_aggresive = 0.5
        self.player_type = 0 # 0 = defensiv 1 = aggresiv
        self.strategy_change_count = 50 #how many hands it will change its strategy
        
        self.hand_count = 0
        
        self.opponent_hand_count = 0
        self.opponent_fold_count = 0
        self.opponent_raise_count = 0
        self.opponent_call_count = 0
    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        # pot = round_state['pot']['main']['amount']
        win_rate = get_win_rate(hole_card, community_card)
#         self_bet = self.cal_self_bet(round_state)
        # call_amount = valid_actions[1]['amount']
        # raise_amount = valid_actions[2]['amount']['min']
#         ev = self.ev_calculation(win_rate, pot, call_amount, self_bet, raise_amount)
        
        chosen_action = self.choose_action(win_rate, round_state, valid_actions)
        
        return chosen_action


    def receive_game_start_message(self, game_info):
        self.small_blind_amount = game_info['rule']['small_blind_amount']
        self.uuid = game_info['seats'][0]['uuid'] #don't know if there is another way
        self.init_opponent_table(game_info)
    def receive_round_start_message(self, round_count, hole_card, seats):
        self.stack_at_round_start = get_stack(seats, self.uuid)
	
    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        self.record_opponent(action, round_state)

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass
    
    # def cal_self_bet(self,round_state):
    #     if round_state['seats'][big_blind_pos]['uuid'] == self.uuid['uuid']:
    #         return self.stack_at_round_start - get_stack(round_state['seats'], self.uuid) + self.small_blind_amount * 2
    #     else:
    #         return self.stack_at_round_start - get_stack(round_state['seats'], self.uuid) + self.small_blind_amount
    
    def choose_action(self, win_rate, round_state, valid_actions):
        self.hand_count += 1
        bet = round_state['pot']['main']['amount'] - valid_actions[1]['amount']
        r = np.random.random()
        if self.hand_count % 50 == 0:
            random_type_array = random.sample([0, 1], 1)
            self.player_type = random_type_array[0]
            
                
        if self.player_type == 0:
            raise_threshold = self.raise_threshold_defensive
            bluffing_threshold = (win_rate - self.fold_threshold_defensive) / \
                                (self.raise_threshold_defensive - self.fold_threshold_defensive) * self.bluffing_max_defensive
            fold_threshold = self.fold_threshold_defensive
        elif self.player_type == 1:
            raise_threshold = self.raise_threshold_aggressive
            bluffing_threshold = (win_rate - self.fold_threshold_aggressive) / \
                                (self.raise_threshold_aggressive - self.fold_threshold_aggressive) * self.bluffing_max_aggresive
            fold_threshold = self.fold_threshold_aggressive
        else:
            raise('?????')

        # print("The bet is ", round_state['pot']['main']['amount'] - valid_actions[1]['amount']) 
        EV_fold = -bet
        EV_call = (2 * win_rate - 1) * valid_actions[1]['amount']

        if win_rate > raise_threshold:
            if not is_raise_limit_reached(round_state):
                return valid_actions[2]['action'], valid_actions[2]['amount']['min']
            else:
                return valid_actions[1]['action'], valid_actions[1]['amount']
        elif win_rate < fold_threshold:
            if EV_fold > EV_call:
                return valid_actions[0]['action'], valid_actions[0]['amount']
            else:
                return valid_actions[1]['action'], valid_actions[1]['amount']
        elif r < bluffing_threshold:
            return valid_actions[2]['action'], valid_actions[2]['amount']['min']
        else:
            return valid_actions[1]['action'], valid_actions[1]['amount']
        
        
    def record_opponent(self, new_action, round_state):
        if not new_action['player_uuid'] == self.uuid:
            self.opponent_hand_count += 1
            if new_action['action'] == 'raise':
                self.opponent_raise_count += 1
            elif new_action['action'] == 'fold':
                self.opponent_fold_count += 1
            elif new_action['action'] == 'call':
                self.opponent_call_count += 1
            else:
                raise('?????')
        
            if not self.opponent_hand_count == 0 and self.opponent_hand_count % 50 == 0:
                record = []
                record.append(self.opponent_call_count / 50.)
                record.append(self.opponent_fold_count / 50.)
                record.append(self.opponent_raise_count / 50.)

                if self.player_type == 0:
                    record.append('defensive')
                else:
                    record.append('aggressive')

                self.opponent_fold_count = 0
                self.opponent_raise_count = 0
                self.opponent_call_count = 0
                con = lite.connect(db_name)

                with con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO {tn}(call_percentage, fold_percentage, raise_percentage, AI_type) VALUES(?,?,?,?)".format(tn = self.oppo_table_name), record)

    def init_opponent_table(self, game_info):
        for player in game_info['seats']:
            if not player['uuid'] == self.uuid:
                opponent_name = player['name']
        self.oppo_table_name = "Percentages_record_{on}".format(on = opponent_name)
        con = lite.connect(db_name)

        with con:
            cur = con.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS {nt}(_Id INTEGER PRIMARY KEY, call_percentage REAL, fold_percentage REAL, raise_percentage REAL, AI_type TEXT)".format(nt = self.oppo_table_name))

#     def ev_calculation(self, win_rate, pot, call_amount, self_bet, raise_amount):
#         ev = [0 for i in range(3)]
#         ev[0] = -self_bet
#         ev[1] = win_rate * (pot - self_bet) - (1 - win_rate) * call_amount
#         ev[2] = win_rate * (pot - self_bet + 2 * self.small_blind_amount) - (1 - win_rate) * raise_amount
#         return ev
def setup_ai():
    return InteractivePlayer()
