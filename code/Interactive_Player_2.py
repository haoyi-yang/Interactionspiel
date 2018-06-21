from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random
from utils import get_win_rate, get_stack, is_raise_limit_reached
import numpy as np
import sqlite3 as lite

db_name = 'game_information.db'
class InteractivePlayer(BasePokerPlayer):
    def __init__(self):
        #First type of defensive player
        self.raise_threshold_defensive_1 = 0.7
        self.fold_threshold_defensive_1 = 0.4
        self.bluffing_max_defensive_1 = 0.3

        #Second type of defensive player
        self.raise_threshold_defensive_2 = 0.75
        self.fold_threshold_defensive_2 = 0.45
        self.bluffing_max_defensive_2 = 0.25

        #Third type of defensive player
        self.raise_threshold_defensive_3 = 0.8
        self.fold_threshold_defensive_3 = 0.5
        self.bluffing_max_defensive_3 = 0.3

        #First type of aggressive player
        self.raise_threshold_aggressive_1 = 0.6
        self.fold_threshold_aggressive_1 = 0.2
        self.bluffing_max_aggresive_1 = 0.45
        #Second type of aggressive player
        self.raise_threshold_aggressive_2 = 0.65
        self.fold_threshold_aggressive_2 = 0.25
        self.bluffing_max_aggresive_2 = 0.4
        #Third type of aggressive player
        self.raise_threshold_aggressive_3 = 0.7
        self.fold_threshold_aggressive_3 = 0.3
        self.bluffing_max_aggresive_3 = 0.35

        self.player_type = 0 # 0 => defensiv_1 1 => defensive_2 2 => defensive_3 3 => aggressive_1 4 => aggressive_2 5 => aggressive_3
        self.strategy_change_count = 100 #how many hands it will change its strategy
        
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
            self.player_type = random.sample(range(6), 1)[0]
            # self.player_type = random_type_array[0]
            
        #set the player parameters      
        if self.player_type == 0:
            raise_threshold = self.raise_threshold_defensive_1
            bluffing_threshold = (win_rate - self.fold_threshold_defensive_1) / \
                                (self.raise_threshold_defensive_1 - self.fold_threshold_defensive_1) * self.bluffing_max_defensive_1
            fold_threshold = self.fold_threshold_defensive_1
        elif self.player_type == 1:
            raise_threshold = self.raise_threshold_defensive_2
            bluffing_threshold = (win_rate - self.fold_threshold_defensive_2) / \
                                (self.raise_threshold_defensive_2 - self.fold_threshold_defensive_2) * self.bluffing_max_defensive_2
            fold_threshold = self.fold_threshold_defensive_2
        elif self.player_type == 2:
            raise_threshold = self.raise_threshold_defensive_3
            bluffing_threshold = (win_rate - self.fold_threshold_defensive_3) / \
                                (self.raise_threshold_defensive_3 - self.fold_threshold_defensive_3) * self.bluffing_max_defensive_3
            fold_threshold = self.fold_threshold_defensive_3
        elif self.player_type == 3:
            raise_threshold = self.raise_threshold_aggressive_1
            bluffing_threshold = (win_rate - self.fold_threshold_aggressive_1) / \
                                (self.raise_threshold_aggressive_1 - self.fold_threshold_aggressive_1) * self.bluffing_max_aggresive_1
            fold_threshold = self.fold_threshold_aggressive_1
        elif self.player_type == 4:
            raise_threshold = self.raise_threshold_aggressive_2
            bluffing_threshold = (win_rate - self.fold_threshold_aggressive_2) / \
                                (self.raise_threshold_aggressive_2 - self.fold_threshold_aggressive_2) * self.bluffing_max_aggresive_2
            fold_threshold = self.fold_threshold_aggressive_2
        elif self.player_type == 5:
            raise_threshold = self.raise_threshold_aggressive_3
            bluffing_threshold = (win_rate - self.fold_threshold_aggressive_3) / \
                                (self.raise_threshold_aggressive_3 - self.fold_threshold_aggressive_3) * self.bluffing_max_aggresive_3
            fold_threshold = self.fold_threshold_aggressive_3   
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
                    record.append('defensive_1_r0.70f0.40b0.30')
                elif self.player_type == 1:
                    record.append('defensive_2_r0.75f0.45b0.25')
                elif self.player_type == 2:
                    record.append('defensive_3_r0.80f0.50b0.30')
                elif self.player_type == 3:
                    record.append('aggressive_1_r0.60f0.20b0.45')
                elif self.player_type == 4:
                    record.append('aggressive_2_r0.65f0.25b0.40')
                elif self.player_type == 5:
                    record.append('aggressive_3_r0.70f0.30b0.35')
                else:
                    raise('>>>>>>>no such type<<<<<<<<<<')

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
