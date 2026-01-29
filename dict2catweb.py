import json
from math import floor
from random import choice
from sys import argv

files = []
used_ids = []
charset = 'abcdefjgijklmnopqrstuvwxyz'

def id_gen():
    rng_id = ''
    for i in range(6):
        rng_id += choice(charset)
    if rng_id in used_ids:
        rng_id = id_gen()
    return rng_id

def create_file(alias:str):
    return {
        'class': 'script',
        'globalid': id_gen(),
        'alias': alias,
        'content': []
    }

def add_fun_wwloaded(f, x, y, step):
    new_id = id_gen()
    f['content'].append(
        {
            'x': x,
            'y': y,
            'globalid': new_id,
            'id': '0',
            'text': [
                'When Website loaded...'
            ],
            'actions': []
        }
    )
    x += step
    if x > 9500:
        x = 0
        y += step
    
    return new_id, x, y
    

def find_fun(f, fun_id):
    for i, v in enumerate(f['content']):
        if v['globalid'] == fun_id:
            return i
    return -1

def add_create_tbl(table, f, fun_id):
    f['content'][find_fun(f, fun_id)]['actions'].append(
        {
            'id': '54',
            'text': [
                'Create table',
                {
                    'value': table,
                    't': 'string',
                    'l': 'table'
                }
            ],
            'globalid': id_gen()
        }
    )

def add_set(key, value, table, f, fun_id):
    f['content'][find_fun(f, fun_id)]['actions'].append(
        {
            'id': '55',
            'text': [
                'Set entry',
                {
                    'value': key,
                    't': 'string',
                    'l': 'entry'
                },
                'of',
                {
                    'value': table,
                    't': 'string',
                    'l': 'table'
                },
                'to',
                {
                    'value': value,
                    't': 'string',
                    't': 'any'
                }
            ],
            'globalid': id_gen()
        }
    )
    

# const numberToLetters = (n) => {
#   let s = "";
#   n = n + 1;
#   while (n > 0) {
#     n--;
#     s = String.fromCharCode(97 + (n % 26)) + s;
#     n = Math.floor(n / 26);
#   }
#   return s;
# };

def n2l(n) -> str:
    s = ''
    n = n+1
    while n > 0:
        n -= 1
        s = chr(97 + (n % 26)) + s
        n = floor(n/26)
    
    return s  

def convert(data:dict, songs_pblock=30):
    f = create_file('songs')
    
    # init songs list
    blockid, x, y = add_fun_wwloaded(f, 0, 0, 450)
    add_create_tbl('songs', f, blockid)
    
    # init values
    idx = -1
    blockid = None
    
    #start iterating
    for songid, info in data.items():
        idx += 1
        # make a new block each 30 song (180 sub-blocks)
        if idx % songs_pblock == 0:
            blockid, x, y = add_fun_wwloaded(f, x, y, 450)
        name = 'item_' + n2l(idx)
        
        # making a song obj
        add_create_tbl(name, f, blockid)
        add_set('title', info['title'], name, f, blockid)
        add_set('artist', info['artist'], name, f, blockid)
        add_set('decal', info['decal'], name, f, blockid)
        add_set('genres', info['genres'], name, f, blockid)
        
        # setting key -> song in songs table
        add_set(songid, '{'+name+'}', 'songs', f, blockid)
    
    return f


if __name__ == '__main__':
    with open(argv[1]) as f:
        with open(argv[1].split('/')[-1], 'w+') as nf:
            json.dump([convert(json.load(f))], nf, indent=4)
