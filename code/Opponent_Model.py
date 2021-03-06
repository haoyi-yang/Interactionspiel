from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random as rand
import sqlite3 as lite
from utils import get_win_rate

NB_SIMULATION = 1000

class OpponentModel(BasePokerPlayer):


    def __init__(self, name, bluffing_ratio, raise_threshold):

        self.name = name
        self.seat = None

        self.win_rate = None
        self.raise_threshold = raise_threshold
        self.bluffing_ratio = bluffing_ratio

    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        pot = round_state['pot']['main']['amount']
        self.small_blind_amount = round_state['small_blind_amount']

        self.win_rate = get_win_rate(hole_card, community_card)
        choose_action, amount = self.choose_action(self.win_rate, pot, valid_actions)
        return choose_action, amount

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']
        self.small_blind_amount = game_info['rule']['small_blind_amount']
        for player in game_info['seats']:
            if player['uuid'] == self.uuid:
                self.seat = game_info['seats'].index(player)
                break
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


    def set_nb_player(self, nb_player):
        self.nb_player = nb_player

    def set_bet(self, bet):
        self.self_bet = bet


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
