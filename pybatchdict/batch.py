'''
batch.py
pybatchdict

2013 Brandon Mechtley

Tools for creating a list of dictionaries from a specially formatted input
dictionary. Also has certain tools for helping set/get key-value pairs in
nested dictionaries.
'''

import random
from copy import deepcopy
from itertools import product
from pprint import PrettyPrinter

def nested_list_string(v):
    '''
    Return a string representation of a nested list where all elements are
    separated by hyphens.

    Args:
        v: the nested list.

    Returns:
        A string of all values in the list separated by hyphens.
    '''

    if hasattr(v, '__iter__'):
        return '-'.join('%s' % nested_list_string(c) for c in v)
    else:
        return str(v)

def getkeypath(d, keypath, default=None):
    '''
    Given an input (nested) dictionary and a keypath to a particular key, 
    return the key's value in the dictionary.
    
    For example: 
    
    getkeypath({
        'a': {'b': 1, 'c': 2}, 
        'd: 3
    }, '/a/b'})
    
    will return 1.

    Args:
        d (dict): input dictionary
        keypath (str): path to the key delimited by /.
        default (anything): optional default value to return if the key does 
            not exist in the dictionary.

    Returns:
        The value in the nested dictionary at the particular path.
    '''
    
    if default is None: default = {}
    
    v = d
    
    keys = keypath.split('/')
    
    for i, key in enumerate(keys):
        if len(key):
            v = v.get(key, {} if i < (len(keys) - 1) else default)
    
    return v

def setkeypath(d, keypath, value=None):
    '''
    Given an input dictionary and the path to a particular key, set the key's
    value in the dictionary.

    Args:
        d (dict): input dictionary
        keypath (str or dict): if keypath is a string, it is path to the key
            delimited by /. For example, to access key 'b' in  {'a': {'b': 0}},
            the path is '/a/b'. If keypath is a dictionary, it is dictionary of
            form {keypath: value} where each key corresponds to a unique
            keypath within the nested dictionary.
        value (anything): optional value to assign the key in the dictionary.
            Required if keypath is a str rather than a dictionary.
    '''
    
    if type(keypath) == dict:
        for k, v in keypath.items():
            setkeypath(d, k, v)
    else:
        keys = [k for k in keypath.split('/') if len(k)]
        
        for key in keys[:-1]:
            d = d[key]
        
        d[keys[-1]] = value

def dictpaths(indict, inpath=''):
    '''
    Given a (nested) dictionary, enumerate all keypaths in a flat list. For 
    example:
    
    dictpaths({
        'a': {'@1': [1, 2, 3]},
        'b': {'@1': [4, 5, 6]},
        'c': {'@': [7, 8]},
        'd': 9
    })
    
    will return ['/a/@1', '/b/@1', '/c/@', '/d'].

    Args:
        indict (dict): input nested dictionary
        inpath (str): parent path to the current place of execution (is a
            recursive function. So leave this to its default.)
    
    Returns:
        list of all paths in the dictionary.
    '''
    
    if type(indict) != dict:
        return {inpath: indict}
    else:
        outdict = {}

        for key in indict:
            paths = dictpaths(indict[key], inpath + '/' + key)

            if type(paths) == dict:
                for pkey in paths:
                    outdict[pkey] = paths[pkey]
            else:
                for ele in paths:
                    for ekey in ele:
                        outdict[ekey] = ele[ekey]
        
        return outdict

def pathcombos(paths, data):
    '''
    Given a) a flat list of keypaths in a nested dictionary, as produced by
    dictpaths, and b) the original nested dictionary, return a list of
    dictionaries that are every combination of values for paths that are to be
    iterated.
    
    An iterated value is a dictionary with a key '@X', where X is any
    identifier or the empty string, and value that is a list of values over
    which to iterate. If two values are iterated by the same identifier they
    will be considered a single group and need to have the same number of
    elements (like zip). If a value is iterated by '@', it will take on a
    unique random identifier. For example: 
    
    pathcombos(['/a', '/b', '/c', '/d'], {
        'a': {'@1': [1, 2, 3]}, 
        'b': {'@1': [4, 5, 6]}, 
        'c': {'@': [7, 8]},
        'd' 9
    })
    
    will return [
        {'/a': 1, '/b': 4, '/c': 7},
        {'/a': 1, '/b': 4, '/c': 8},
        {'/a': 2, '/b': 5, '/c': 7},
        {'/a': 2, '/b': 5, '/c': 8},
        {'/a': 3, '/b': 6, '/c': 7},
        {'/a': 3, '/b': 6, '/c': 8}
    ].
    
    Notice that 'd' is not included. Use dictlist to reproduce the entire 
    dictionary.

    Additionally, if the value for an iterated value begins with @range, it
    will be interpreted as a range that operates similar to numpy's "linspace."
    e.g.
        @range(5): [0, 1, 2, 3, 4]
        @range(3,10): [3, 4, 5, 6, 7, 8, 9]
        @range(0,1,5): [0, .2, .4, .6, .8]

    Args:
        paths (list): list of str keypaths.
        data (dict): original config dictionary with lists to which the
            keypaths refer.
    
    Returns:
        list of dictionaries for every combination of values for paths that are
        to be iterated.
    '''
    
    combosets = {}
    
    for key in paths:
        keytokens = key.split('/')
        lastkey = keytokens[-1]
        
        if lastkey[0] == '@':
            setname = ''
            
            if len(lastkey) > 1:
                setname = lastkey
            else:                    
                setname = '@' + str(random.getrandbits(128))
                
                if len(combosets.keys()):
                    while setname in combosets.keys():
                        setname = '@' + str(random.getrandbits(128))
        
            combosets.setdefault(setname, {})
            keybase = '/'.join(keytokens[:-1])
            vardata = getkeypath(data, key)

            if isinstance(vardata, basestring):
                if vardata[0:6] == '@range':
                    tokens = vardata[7:].rstrip(')').split(',')
                    tokens = [float(t) if '.' in t else int(t) for t in tokens]
                    bottom = tokens[0]

                    if len(tokens) == 1:
                        count = tokens[0]
                    elif len(tokens) == 2:
                        count = tokens[1] - tokens[0]
                    else:
                        count = tokens[3]

                    vardata = range(count)

                    if len(tokens) == 2:
                        vardata = [v + bottom for v in vardata]
                    elif len(tokens) == 3:
                        top = tokens[1]
                        vardata = [v + bottom / (top - bottom) for v in tokens]

            combosets[setname][keybase] = vardata
      
    # TODO: This can probably be cleaned up quite a bit.
    
    combos = [{
        k: v 
        for k, v in sum(valueset, [])} for valueset in [
            list(combotuple) 
            for combotuple in list(product(*[
                [
                    list(pair) for pair in 
                    zip(*[
                        list(product([keypath], values))
                        for keypath, values in comboset.items()
                    ])
                ]
                for comboset in combosets.values()
            ]))
        ]
    ]
    
    return combos, combosets

def dictlist(combos, data):
    '''
    Given a list of dictionaries containing keypath: value pairs from
    pathcombos, return a list of dictionaries that are modified copies of an
    input dictionary (data), where each dictionary has the values corresponding
    to the keypaths replaced by their desired values.

    Args:
        combos (dict): dictionary of combinations of the iterated parameters.
        data (dict): original dictionary to copy combinations' values into.
    
    Returns:
        list of dictionaries where each dict has the values corresponding to
        the keypaths replaced by their desired values.
    '''
    
    dicts = []
    
    for combo in combos:
        newdict = deepcopy(data)
        setkeypath(newdict, combo)
        dicts.append(newdict)
    
    return dicts

def parseconfig(d):
    '''
    Shortcut to automatically generate a list of dictionaries given an input
    config dictionary.

    Args:
        d (dict): input configuration dictionary
    
    Returns:
        list of dictionaries given an input configuration dictionary.
    '''
    
    paths = dictpaths(d)
    combos, combosets = pathcombos(paths, d)
    return dictlist(combos, d)

class BatchDict:
    def __init__(self, d=None):
        self.d = d
        self.paths = dictpaths(d)
        self.unique, self.itsets = pathcombos(self.paths, d)
        self.combos = dictlist(self.unique, d)
    
    def sorted_unique_items(self):
        sorted_sets = sorted(self.itsets.keys())
        rlist = []
        
        for u in self.unique:
            paths = [] 
            for set in sorted_sets:
                for k in self.itsets[set]: 
                    paths.append((k, u[k]))
            
            rlist.append(paths)
        
        return rlist
    
    def hyphenate_changes(self):
        '''
        Create a list of strings that describe the unique portions of each
        combination from the batch dictionary. Variables are sorted by
        iteration set name. 

        For example, if batchdict has original configuration dictionary 
        {'a': {'@2': [0, 1]}, 'b': {'@1': [2, 3]}, 'c': 4}, then the output
        names will be: ['b-2-a-0', 'b-2-a-1', 'b-3-a-0', 'b-3-a-1'].
        
        Returns:
            list of strings formatted for the unique portions of each config 
            combination.
        '''
    
        outnames = []
        
        for c, items in zip(self.combos, self.sorted_unique_items()):
            outnames.append(
                '-'.join([
                    k.strip('/').replace('/', '.') + '-' + nested_list_string(v)
                    for k, v in items
                ])
            )
    
        return outnames
