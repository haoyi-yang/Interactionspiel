from pypokerengine.api.game import setup_config, start_poker
from Model_Player import ModelPlayer
from Rational_Player import RationalPlayer

config = setup_config(max_round=20, initial_stack=1000, small_blind_amount=1)
# config.register_player(name="p1", algorithm=ModelPlayer("model"))
config.register_player(name="p1", algorithm=RationalPlayer("sda"))
config.register_player(name="p2", algorithm=RationalPlayer("sda"))
game_result = start_poker(config, verbose=1)

# from utils import record_win_rate

# str1 = ['abc']
# str2 = ['bcd']

# record_win_rate(0.55, str1, str2)