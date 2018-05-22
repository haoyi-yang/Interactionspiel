from pypokerengine.api.game import setup_config, start_poker
from Model_Player import ModelPlayer
from Rational_Player import RationalPlayer

config = setup_config(max_round=5, initial_stack=1000, small_blind_amount=1)
config.register_player(name="p1", algorithm=ModelPlayer("model"))
config.register_player(name="p2", algorithm=RationalPlayer())
game_result = start_poker(config, verbose=1)