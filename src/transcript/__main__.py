import json
import sys

from . import transcripter


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python transcript.py <FILE_PATH>')
    else:
        with open(sys.argv[1], encoding='utf-8') as f:
            scenario = transcripter.transcript(f)
            print(json.dumps(scenario, ensure_ascii=False, indent=2))
