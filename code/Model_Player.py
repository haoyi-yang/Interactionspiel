from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
from pypokerengine.utils.game_state_utils import restore_game_state, attach_hole_card_from_deck, attach_hole_card
from pypokerengine.api.emulator import Emulator
from Opponent_Model import OpponentModel
import random as rand
import sqlite3 as lite
import random
from utils import get_win_rate, assuming_card, get_broad_win_rate
import numpy as np

NB_SIMULATION = 10
DEBUG_MODE = True
def log(msg):
    if DEBUG_MODE: print("[debug_info] --> %s" % msg)

street_table = {'preflop': 0, 'flop':3, 'turn':4, 'river':5, 'showdown':5} #number of community card at each street

class ModelPlayer(BasePokerPlayer):

    table_name = "gameinfotbl"
    standard_insert = "Player_name, win_rate, hole_cards, community_cards, action, stack, small_blind_amount"
    db_name = "game_information.db"
    street = ['preflop', 'flop', 'turn', 'river', 'showdown']

    def __init__(self, name):

        self.name = name
        self.seat = None
        self.raise_amount = 0
        self.win_rate = None
        self.stack = None
        self.small_blind_amount = None
        self.hole_card = None
        self.community_card = None
        self.action = None
        self.opponent_raise_threshold = 0.7
        self.opponent_bluffing_ratio = 0.5
        self.__init_database()
        self.Opponent_Model = OpponentModel("Opponent",0.5,0.5)
        self.my_model = MyModel()

    def declare_action(self, valid_actions, hole_card, round_state):
        
        # try_actions = [MyModel.FOLD, MyModel.CALL, MyModel.RAISE]
        # community_card = round_state['community_card']
        pot = round_state['pot']['main']['amount']
        call_amount = valid_actions[1]['amount']
        self.raise_amount = valid_actions[2]['amount']['min']
        # round_strategy = {'preflop' : 0, 'flop' : 0, 'turn' : 0, 'river' : 0, 'showdown' : 0}
        # street_now = round_state['street']

        # # self.win_rate = estimate_hole_card_win_rate(nb_simulation = NB_SIMULATION,
        # #                                         nb_player = self.nb_player,
        # #                                         hole_card=gen_cards(hole_card),
        # #                                         community_card=gen_cards(community_card))

        # action_results = [0 for i in range(len(try_actions))]

        # # win_rate = calculate_win_rate_with_model(hole_card, community_card)
        # log("hole_card of emulator player is %s" % hole_card)
        # for action_now in try_actions:
        #     round_strategy[round_state['street']] = action_now
        #     for street in enumerate(self.street, self.street.index(street_now) + 1):
        #         for action_later in try_actions:
        #             round_strategy[street] = action_later
        #             self.my_model.set_round_strategy(round_strategy)
        #             simulation_results = []
        #             for _ in range(NB_SIMULATION):
        #                 game_state = self._setup_game_state(round_state, hole_card)
        #                 round_finished_state, _events = self.emulator.run_until_round_finish(game_state)
        #                 new_winner_uuid = _events[-1]['winners'][-1]['uuid']
        #                 my_stack = [player for player in round_finished_state['table'].seats.players if player.uuid == self.uuid][0].stack
        #                 simulation_results.append(my_stack)
                    
        #             if action_results[action_now] < 1.0 * sum(simulation_results) / NB_SIMULATION:
        #                 action_results[action_now] = 1.0 * sum(simulation_results) / NB_SIMULATION
        #                 log("average stack after simulation when declares %s : %s" % (
        #                     {0:'FOLD', 1:'CALL', 2:'RAISE'}[action_now], action_results[action_now])
        #                     )

        # best_action = max(zip(action_results, try_actions))[1]
        # round_strategy[round_state['street']] = best_action
        # self.my_model.set_round_strategy(round_strategy)
        # declare_action, amount = self.my_model.declare_action(valid_actions, hole_card, round_state)

        # if declare_action == "FOLD":
        #     self.action = 0
        # elif declare_action == "CALL":
        #     self.action = 1
        # else:
        #     self.action = 2
        # self.record_action()
        win_rate_with_model = self.estimate_win_rate_with_model_to_convergent(hole_card, round_state)
        print(win_rate_with_model)
        ev = self.ev_calculation(win_rate_with_model, pot, call_amount)

        if ev.index(max(ev)) == 0:
            return valid_actions[0]['action'], valid_actions[0]['amount']

        elif ev.index(max(ev)) == 1:
            return valid_actions[1]['action'], valid_actions[1]['amount']

        else:
            return valid_actions[2]['action'], valid_actions[2]['amount']['min']

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']
        self.small_blind_amount = game_info['rule']['small_blind_amount']
        self.Opponent_Model.set_nb_player(self.nb_player)
        self.my_model = MyModel()
        max_round = game_info['rule']['max_round']
        sb_amount = game_info['rule']['small_blind_amount']
        ante_amount = game_info['rule']['ante']

        for player in game_info['seats']:
            if player['uuid'] == self.uuid:
                self.seat = game_info['seats'].index(player)
                break
            else:
                raise('not participating!')

        self.emulator = Emulator()
        self.emulator.set_game_rule(self.nb_player, max_round, sb_amount, ante_amount)
        for player_info in game_info['seats']:
            uuid = player_info['uuid']
            player_model = self.my_model if uuid == self.uuid else self.Opponent_Model
            self.emulator.register_player(uuid, player_model)



    def receive_round_start_message(self, round_count, hole_card, seats):
        self.self_bet = 0
        self.hole_card = hole_card

    def receive_street_start_message(self, street, round_state):
        self.community_card = round_state['community_card']

    def receive_game_update_message(self, action, round_state):
        if action['player_uuid'] == self.uuid:
            self.self_bet = self.self_bet + action['amount']
        Opponent_bet = round_state['pot']['main']['amount'] - self.self_bet
        self.Opponent_Model.set_bet(Opponent_bet)
        self.stack = round_state['seats'][self.seat]['stack']

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    
    def record_action(self):
        msg_record = self.__make_message()

        con = lite.connect(self.db_name)

        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO gameinfotbl(Player_name, win_rate, hole_cards, community_cards, action, stack, small_blind_amount) VALUES(?,?,?,?,?,?,?)", msg_record)





    #######################################################################

    def ev_calculation(self, win_rate, pot, call_amount):
        ev = [0 for i in range(3)]
        ev[0] = -self.self_bet
        ev[1] = win_rate * (pot - self.self_bet) - (1 - win_rate) * (self.self_bet + call_amount)
        ev[2] = win_rate * (pot - self.self_bet + self.raise_amount) - \
                        (1 - win_rate) * (self.self_bet + self.raise_amount + call_amount)
        return ev    

    # def choose_action(self, win_rate, pot, valid_actions):                    
    #     r = rand.random()
    #     ev = self.ev_calculation(win_rate, pot, valid_actions[1]['amount'])
    #     if win_rate >= self.raise_threshold:
    #         return valid_actions[2]['action'], 2 * self.small_blind_amount
    #     elif r >= self.bluffing_ratio:
    #         return valid_actions[2]['action'], 2 * self.small_blind_amount
    #     elif ev[1] >= ev[0]:
    #         return valid_actions[1]['action'], valid_actions[1]['amount']
    #     else:
    #         return valid_actions[0]['action'], valid_actions[0]['amount']

    def _setup_game_state(self, round_state, my_hole_card):
        game_state = restore_game_state(round_state)
        game_state['table'].deck.shuffle()
        community_card = round_state['community_card']
        current_street = round_state['street']

        player_uuids = [player_info['uuid'] for player_info in round_state['seats']]
        for uuid in player_uuids:
            if uuid == self.uuid:
                game_state = attach_hole_card(game_state, uuid, gen_cards(my_hole_card))  # attach my holecard
            else:
                while True:
                    opponent_card = assuming_card(gen_cards(my_hole_card))
                    if not self.is_already_fold(opponent_card, current_street, community_card):
                        break
                game_state = attach_hole_card(game_state, uuid, opponent_card)  # attach opponents holecard at random
        return game_state

    def __make_message(self):
        msg = []
        msg.append(self.name)
        msg.append(self.win_rate)
        msg.append(str(self.hole_card))
        msg.append(str(self.community_card))
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

    def _modify_round_strategy_list(self, action, street, round_strategy):
        round_strategy['street'] = action
        
    def is_already_fold(self, opponent_card, current_street, community_card):
        win_rate = 0
        r = rand.random()
        str_card = [str(a) for a in opponent_card]
        for street in street_table.keys():
            win_rate = get_broad_win_rate(str_card, community_card[0:street_table[street]])
            if win_rate < self.opponent_raise_threshold and r < self.opponent_bluffing_ratio:
                return True
            if street == current_street or street == 'river':
                break
        return False

    def simulate_one_time(self, round_state, hole_card):
        game_state = self._setup_game_state(round_state, hole_card)
        _round_finished_state, _events = self.emulator.run_until_round_finish(game_state)
        if _events[-1]['type'] == 'event_game_finish':
            return 0 #if not 0, the last round will report a error
        new_winner_uuid = _events[-1]['winners'][-1]['uuid']
        
        # my_stack = [player for player in round_finished_state['table'].seats.players if player.uuid == self.uuid][0].stack
        # simulation_results.append(my_stack)

        return 1 if new_winner_uuid == self.uuid else 0

    def calculate_win_rate_with_model_serval_time(self, round_state, hole_card, nb_simulation):
        win_count = sum([self.simulate_one_time(round_state, hole_card) for _ in range(nb_simulation)])
        return 1.0 * win_count / nb_simulation
    
    def estimate_win_rate_with_model_to_convergent(self, hole_card, round_state):
        ls_win_rate = [.0 for _ in range(10)]
        rpt_times = 50
        counter = 0  ##the newer calculated win percentage must be the avarage number
        while True:
            newer_win_rate = self.calculate_win_rate_with_model_serval_time(round_state,                                       
                                                hole_card,
                                                rpt_times)
            ls_win_rate.pop(0)
            itered_win_rate = (ls_win_rate[-1] * counter + newer_win_rate) / (counter + 1)
            ls_win_rate.append(itered_win_rate)
            if (np.max(ls_win_rate) - np.min(ls_win_rate)) < 0.1:
                break
            counter = counter + 1

        return ls_win_rate[-1]

class MyModel(BasePokerPlayer):

    FOLD = 0
    CALL = 1
    RAISE = 2

    def __init__(self):
        self.round_strategy = {'preflop' : 1, 'flop' : 1, 'turn' : 1, 'river' : 1, 'showdown' : 1}

    def set_round_strategy(self, round_strategy):
        for key in round_strategy.keys():
            self.round_strategy[key] = round_strategy[key]


    def declare_action(self, valid_actions, hole_card, round_state):
        street_now = round_state['street']
        self.action = self.round_strategy[street_now]


        if self.FOLD == self.action:
            return valid_actions[0]['action'], valid_actions[0]['amount']
        elif self.CALL == self.action:
            return valid_actions[1]['action'], valid_actions[1]['amount']
        elif self.RAISE == self.action:
            return valid_actions[2]['action'], 2 * round_state['small_blind_amount']
        else:
            raise Exception("Invalid action [ %s ] is set" % self.action)
