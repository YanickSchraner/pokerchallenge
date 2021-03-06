import time
import argparse
import importlib
import json
import os

from baseline.ConsolePokerPlayer import ConsolePlayer
from configuration.CashGameConfig import CashGameConfig
from agent.MyBot import MyBotPlayer

parser = argparse.ArgumentParser(description='Run poker evaluation')
parser.add_argument('--config', help='Config file')
parser.add_argument('--store_result', dest='store_result', action='store_true')
parser.set_defaults(store_result=False)


def load_configuration(config_file: str):
    with open(config_file, 'r', encoding='utf-8') as fp:
        config = json.load(fp)
    return config


def register_players(config_file, poker_config, n_baselines) -> None:
    """
    Seat baseline and players set in the evaluation_config.json file.
    :param config_file: json
    :param poker_config: CashGame configuration object
    """
    baseline_counter = 1
    while len(poker_config.config.players_info) < n_baselines:
        for module, cls in config_file['baselines'].items():
            module = importlib.import_module(f'baseline.{module}')
            baseline_class = getattr(module, cls)
            poker_config.register_player(f"{cls}_{baseline_counter}", baseline_class())
            baseline_counter += 1

            if (len(poker_config.config.players_info)) is n_baselines:
                break

    for module, cls in config_file['players'].items():
        module = importlib.import_module(f'agent.{module}')
        baseline_class = getattr(module, cls)
        poker_config.register_player(cls, baseline_class())


if __name__ == '__main__':
    args = parser.parse_args()

    if args.config and os.path.isfile(args.config):
        # Used by run_evaluation.sh script
        config_file = load_configuration(args.config)
        poker_config = CashGameConfig(evaluations=config_file['n_evaluations'],
                                      small_blind_amount=config_file['small_blind'],
                                      log_file_location=config_file['log_file_location'])
        register_players(config_file, poker_config, config_file['n_baselines'])
    else:
        # Use this for manual evaluation
        poker_config = CashGameConfig(evaluations=100000)
        poker_config.add_all_available_baselines(n_baselines=5)
        # poker_config.register_player("Console", ConsolePlayer())
        poker_config.register_player("MyBot", MyBotPlayer())

    print(f"Start evaluating {poker_config.evaluations} hands")

    start = time.time()
    result = poker_config.run_evaluation()
    end = time.time()
    time_taken = end - start
    print('Evaluation Time: ', time_taken)

    if args.store_result:
        with open('result.txt', 'w+') as fp:
            pretty_result = '\n'.join(f"{rank + 1:2}. Player: {name:>25}, Stack: {stack:n}" for rank, (name, stack) in
                                      enumerate(result.items()))
            fp.write(pretty_result)
