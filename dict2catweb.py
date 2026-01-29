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

def add_insert(value, table, f, fun_id):
    f['content'][find_fun(f, fun_id)]['actions'].append(
        {
            "id": "89",
            "globalid": id_gen(),
            "text": [
                "Insert",
                {
                    "value": "{" + value + "}",
                    "l": "any",
                    "t": "string"
                },
                "at position",
                {
                    "l": "number?",
                    "t": "number"
                },
                "of",
                {
                    "value": table,
                    "l": "array",
                    "t": "string"
                }
            ]
        }
    )


def n2l(n) -> str:
    s = ''
    n = n+1
    while n > 0:
        n -= 1
        s = chr(97 + (n % 26)) + s
        n = floor(n/26)
    
    return s  

def convert(data:list, item_per_block=30):
    file = create_file('projects')
    
    blockid, x, y = add_fun_wwloaded(file, 0, 0, 450)
    add_create_tbl('projects', file, blockid)
    
    # init values
    idx = -1
    blockid = None
    
    #start iterating
    for i, project in enumerate(data):
        idx += 1
        # make a new block each 30 song (180 sub-blocks)
        if idx % item_per_block == 0:
            blockid, x, y = add_fun_wwloaded(file, x, y, 450)
        name = 'item_' + n2l(idx)
        
        add_create_tbl(name, file, blockid)
        #print(project)
        for k, v in project.items():
            add_set(k, v, name, file, blockid)
        
        #add_set(i, '{'+name+'}', 'projects', file, blockid)
        add_insert(name, 'projects', file, blockid)


    return file


if __name__ == '__main__':
    path = argv[1]
    print(path)
    with open(path) as f:
        with open(path.split('/')[-1], 'w+') as nf:
            json.dump([convert(json.load(f))], nf, indent=4)
