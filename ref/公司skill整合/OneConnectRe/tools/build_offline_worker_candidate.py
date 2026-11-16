"""Build a candidate using the same offline policy as the shipping build."""
import argparse
from build_offline_worker import build

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game-dir', required=True)
    args = parser.parse_args()
    version, count = build(args.game_dir)
    print('offline cache', version, 'files', count)
