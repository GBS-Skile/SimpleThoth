import json
import sys

from . import transcripter


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python transcript.py <INPUT_FILE> <OUTPUT_FILE>')
    else:
        scenario = None
        with open(sys.argv[1], encoding='utf-8') as f_in:
            scenario = transcripter.transcript(f_in)
        
        if scenario:
            with open(sys.argv[2], 'w', encoding='utf-8') as f_out:
                json.dump(scenario, f_out, ensure_ascii=False, indent=2)
