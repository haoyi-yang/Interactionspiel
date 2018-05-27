from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
from utils import get_win_rate

class RationalPlayer(BasePokerPlayer):


    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        call_amount = valid_actions[1]['amount']
        pot = round_state['pot']['main']['amount']
        win_rate = get_win_rate(hole_card, community_card)
        ev = self.ev_calculation(win_rate, pot, call_amount)

        if ev.index(max(ev)) == 0:
            return valid_actions[0]['action'], valid_actions[0]['amount']

        elif ev.index(max(ev)) == 1:
            return valid_actions[1]['action'], valid_actions[1]['amount']

        else:
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