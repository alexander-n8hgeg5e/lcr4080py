#!/usr/bin/env python3

from serial import Serial
from sys import exit
from time import sleep
from os import set_blocking
from types import FunctionType
from pprint import pprint
from re import match
from pint import UnitRegistry

ur=UnitRegistry()
Ohm=ur.ohm
dOhm=ur.deciohm
cOhm=ur.centiohm
kOhm=ur.kiloohm
H=ur.henry
F=ur.farad
Hz=ur.hertz
kHz=ur.kilohertz
uF=ur.microfarad
nF=ur.nanofarad
pF=ur.picofarad
fF=ur.femtofarad

data_translation = [
        ('LCR', lambda x:x),
        ('QDR', lambda x:x),
        {   'A': ('freq', 1*kHz),
            'B': ('freq', 120*Hz)},
        {   'P': ('PAL/SER', 'PAL'),
            'S': ('PAL/SER', 'SER'),
            '_': ('PAL/SER', '_' )},
        { 'A': ('range_sel','auto'),
          'S': ('range_sel','manual')},
        { '0' : (('LCR-value-state', 'LCR-value-0' ),('ok'      , lambda x : x )),
          '1' : (('LCR-value-state', 'LCR-value-0' ),('ok'      , lambda x : x )),
          '8' : (('LCR-value-state', 'LCR-value-0' ),('ch-range', None )),
          '9' : (('LCR-value-state', 'LCR-value-0' ),('OL'      , None ))},
        ('LCR-value-1',lambda x : x),
        ('LCR-value-2',lambda x : x),
        ('LCR-value-3',lambda x : x),
        ('LCR-value-4',lambda x : x),
        ('LCR-value-range',lambda x : x),
        ('2nd-value-0',lambda x : x),
        ('2nd-value-1',lambda x : x),
        ('2nd-value-2',lambda x : x),
        ('2nd-value-3',lambda x : x),
        {   '*' : (('2nd-value-range','2nd-value-state'),(lambda x : x,'ok')),
            '9' : (('2nd-value-range','2nd-value-state'),(        None,'OL'))},
        ('sequence',lambda x : x),
        ('d-val-0',lambda x : x),
        ('d-val-1',lambda x : x),
        ('d-val-2',lambda x : x),
        ('d-val-3',lambda x : x),
        {   '*' : (('d-val-range','d-val-state'),(lambda x : x,'ok')),
            '9' : (('d-val-range','d-val-state'),(None        ,'OL'))},
        ('q-val-0',lambda x : x),
        ('q-val-1',lambda x : x),
        ('q-val-2',lambda x : x),
        ('q-val-3',lambda x : x),
        {   '*' : (('q-val-range','q-val-state'),(lambda x : x,'ok')),
            '9' : (('q-val-range','q-val-state'),( None       ,'OL'))},
        {   'S' : ('set-mode','enabled'),
            '_' : ('set-mode','disabled')},
        {   'F' : ('fuse','FUSE'),
            '_' : ('fuse','normal')},
        {   'H' : ('hold','enabled'),
            '_' : ('hold','disabled')},
        {   'R' : ('min_max_avg-mode','Present Value'),
            'M' : ('min_max_avg-mode','Maximum Value'),
            'I' : ('min_max_avg-mode','Minimum Value'),
            'X' : ('min_max_avg-mode','Max-Min Value'),
            'A' : ('min_max_avg-mode','Average Value'),
            '_' : ('min_max_avg-mode','disabled')},
        {   'R' : ('rel-mode','REL'),
            'S' : ('rel-mode','REL SET'),
            '_' : ('rel-mode','disabled')},
        {   'L' : ('limit-mode','LIMIT'),
            '_' : ('limit-mode','disabled')},
        {   'T' : ('tol-mode','TOL'),
            'S' : ('tol-mode','TOL SET'),
            '_' : ('tol-mode','disabled')},
        {   'B' : ('backlight','enabled'),
            '_' : ('backlight','disabled')},
        {   'A' : ('adapter','True'),
            '_' : ('adapter','False')},
        {   'B' : ('battery','low'),
            '_' : ('battery','ok')},
]

range_translation_main_R = [
        {'Rs': 1e2*Ohm , 'R' : { '1000Hz' : {'range':2e1*Ohm, 'unit': 1e-3*Ohm} , '120Hz' : {'range':2e1*Ohm, 'unit': 1e-3*Ohm} }},
        {'Rs': 1e2*Ohm , 'R' : { '1000Hz' : {'range':2e2*Ohm, 'unit': 1e-2*Ohm} , '120Hz' : {'range':2e2*Ohm, 'unit': 1e-2*Ohm} }},
        {'Rs': 1e2*Ohm , 'R' : { '1000Hz' : {'range':2e3*Ohm, 'unit': 1e-1*Ohm} , '120Hz' : {'range':2e3*Ohm, 'unit': 1e-1*Ohm} }},
        {'Rs': 1e3*Ohm , 'R' : { '1000Hz' : {'range':2e4*Ohm, 'unit': 1e+0*Ohm} , '120Hz' : {'range':2e4*Ohm, 'unit': 1e+0*Ohm} }},
        {'Rs': 1e4*Ohm , 'R' : { '1000Hz' : {'range':2e5*Ohm, 'unit': 1e+1*Ohm} , '120Hz' : {'range':2e5*Ohm, 'unit': 1e+1*Ohm} }},
        {'Rs': 1e5*Ohm , 'R' : { '1000Hz' : {'range':2e6*Ohm, 'unit': 1e+2*Ohm} , '120Hz' : {'range':2e6*Ohm, 'unit': 1e+2*Ohm} }},
        {'Rs': 1e5*Ohm , 'R' : { '1000Hz' : {'range':1e7*Ohm, 'unit': 1e+3*Ohm} , '120Hz' : {'range':1e7*Ohm, 'unit': 1e+3*Ohm} }},
                            ]
range_translation_main_L = [
        {'Rs': 1e2*Ohm  , 'L' : { '1000Hz' : {'range':2e-3*H, 'unit':1e-7*H}, '120Hz' : {'range':2e-2*H, 'unit':1e-6*H} }},
        {'Rs': 1e2*Ohm  , 'L' : { '1000Hz' : {'range':2e-2*H, 'unit':1e-6*H}, '120Hz' : {'range':2e-1*H, 'unit':1e-5*H} }},
        {'Rs': 1e2*Ohm  , 'L' : { '1000Hz' : {'range':2e-1*H, 'unit':1e-5*H}, '120Hz' : {'range':2e-0*H, 'unit':1e-4*H} }},
        {'Rs':    kOhm  , 'L' : { '1000Hz' : {'range':2e+0*H, 'unit':1e-4*H}, '120Hz' : {'range':2e+1*H, 'unit':1e-3*H} }},
        {'Rs': 1e1*kOhm , 'L' : { '1000Hz' : {'range':2e+1*H, 'unit':1e-3*H}, '120Hz' : {'range':2e+2*H, 'unit':1e-2*H} }},
        {'Rs': 1e2*kOhm , 'L' : { '1000Hz' : {'range':2e+2*H, 'unit':1e-2*H}, '120Hz' : {'range':2e+3*H, 'unit':1e-1*H} }},
        {'Rs': 1e1*kOhm , 'L' : { '1000Hz' : {'range':1e+3*H, 'unit':1e-1*H}, '120Hz' : {'range':1e+4*H, 'unit':1e+0*H} }},
                            ]
range_translation_main_C =  [
        {'Rs': 1e2*kOhm , 'C' : { '1000Hz' : {'range':2e-9*F, 'unit': 1e+2*fF} , '120Hz' : {'range':2e-8*F, 'unit':      pF} }},
        {'Rs': 1e2*kOhm , 'C' : { '1000Hz' : {'range':2e-8*F, 'unit':      pF} , '120Hz' : {'range':2e-7*F, 'unit': 1e+1*pF} }},
        {'Rs': 1e1*kOhm , 'C' : { '1000Hz' : {'range':2e-7*F, 'unit': 1e+1*pF} , '120Hz' : {'range':2e-6*F, 'unit': 1e+2*pF} }},
        {'Rs':     kOhm , 'C' : { '1000Hz' : {'range':2e-6*F, 'unit': 1e+2*pF} , '120Hz' : {'range':2e-5*F, 'unit':      nF} }},
        {'Rs': 1e2* Ohm , 'C' : { '1000Hz' : {'range':2e-5*F, 'unit':      nF} , '120Hz' : {'range':2e-4*F, 'unit': 1e+1*nF } }},
        {'Rs': 1e2* Ohm , 'C' : { '1000Hz' : {'range':2e-4*F, 'unit': 1e+1*nF} , '120Hz' : {'range':2e-3*F, 'unit': 1e+2*nF} }},
        {'Rs': 1e2* Ohm , 'C' : { '1000Hz' : {'range':2e-3*F, 'unit': 1e+2*nF} , '120Hz' : {'range':2e-2*F, 'unit':      uF} }},
                            ]
range_translation_2nd = [
        {'D': {'unit':None,'range': None}, 'Q': {'unit':None,'range':None  }, 'R' : {'range':None          , 'unit':None     }},
        {'D': {'unit':1e-1,'range':999.9}, 'Q': {'unit':1e-1,'range':999.9 }, 'R' : {'range':99.99*1e-2*Ohm, 'unit':1e-2*Ohm }},
        {'D': {'unit':1e-2,'range':99.99}, 'Q': {'unit':1e-2,'range':99.99 }, 'R' : {'range':999.9*1e-1*Ohm, 'unit':1e-1*Ohm }},
        {'D': {'unit':1e-3,'range':9.999}, 'Q': {'unit':1e-3,'range':9.999 }, 'R' : {'range':9.999*1e+0*Ohm, 'unit': Ohm }},
        {'D': {'unit':1e-4,'range':.9999}, 'Q': {'unit':1e-4,'range':.9999 }, 'R' : {'range':99.99*1e+1*Ohm, 'unit':1e+1*Ohm }},
        {'D': {'unit':None,'range': None}, 'Q': {'unit':None,'range': None }, 'R' : {'range':999.9*1e+2*Ohm, 'unit':1e+2*Ohm }},
                        ]


range_translation_2nd_D = [{'D': v['D']} for v in range_translation_2nd]
range_translation_2nd_R = [{'R': v['R']} for v in range_translation_2nd]
range_translation_2nd_Q = [{'Q': v['Q']} for v in range_translation_2nd]

range_translation_2nd_Rs =  [
        {'None': None                              },
        {'Rs' : [i*Ohm for i in [1e2,1e3,1e4    ]] },
        {'Rs' : [i*Ohm for i in [1e2,1e3,1e4,1e5]] },
        {'Rs' : [i*Ohm for i in [1e2,1e3,1e4,1e5]] },
        {'Rs' : [i*Ohm for i in [1e2,1e3,1e4,1e5]] },
        {'Rs' : [i*Ohm for i in [        1e4,1e5]] }, 
                            ]
def ud(d,dd):
    d.update(dd)
    return d


range_translations = {
                         "LCR-value" :  {
                                        'L': range_translation_main_L ,
                                        'C': range_translation_main_C ,
                                        'R': range_translation_main_R ,
                                        },
                         "2nd-value" :   {
                                        'Q' : [ud(k,j) for j,k in zip(range_translation_2nd_Rs,range_translation_2nd_Q)],
                                        'D' : [ud(k,j) for j,k in zip(range_translation_2nd_Rs,range_translation_2nd_D)],
                                        'R' : [ud(k,j) for j,k in zip(range_translation_2nd_Rs,range_translation_2nd_R)],
                                        },
                     }
def combine(d,key):
    s=d
    lk=len(key)

    num_parts=0
    for k,v in s.items():
        if k[:lk]==key:
            num_parts+=1
    parts=['']*num_parts

    keys2remove=[]
    for k,v in s.items():
        if k[:lk]==key:
            if match('\d',k[lk]):
                parts[int(k[lk])] = v
                keys2remove.append(k)
    try:
        if not s[key+"state"] == 'ok':
            value = s[key+"state"]
        else:
            value = int(''.join(parts))
    except TypeError:
        if not None in parts:
            raise
        else:
            value=None
    s.update({ key.strip("-_") : value})
    for k in keys2remove:
        s.pop(k)
    return s

def decode_data(data):
    s={}
    dt=data_translation
    for ci in range(len(data)):
        if ci < len(dt):
            if type(dt[ci]) is dict:
                try:
                    name,_data=dt[ci][data[ci]]
                except KeyError:
                    if '*' in dt[ci].keys():
                        name,_data=dt[ci]['*']
                    else:
                        name,_data='key_error','key_error'
            else:
                name,_data=dt[ci]
            if type(name) is tuple:
                for k,v in zip(name,_data):
                    if type(v) is FunctionType:
                        v=v(data[ci])
                    s.update({ k : v })
            else:
                if type(_data) is FunctionType:
                    _data=_data(data[ci])
                s.update({ name : _data })

    # combine data 
    combine_list=['LCR-value-','2nd-value-',"d-val-","q-val-"]
    for k in combine_list:
        s=combine(s,k)

    return s

def process_data_further(data):

    if data['LCR-value-state'] == "ok":
        ri=int(data["LCR-value-range"])
        lcr = data['LCR']
        rt = range_translations['LCR-value'][lcr][ri]
        Rs = rt['Rs']
        f = str(int(Hz.from_(data['freq']).magnitude))+'Hz'
        unit = rt[lcr][f]['unit']
        _range = rt[lcr][f]['range']
        data['LCR-value']=data['LCR-value']*unit
        data['LCR-value-range'] = _range.to(unit)
        data.update({'LCR-value-range-index': ri })
        data.update({'Rs':Rs})
        data.update({'LCR-value-unit':unit})
    else:
        data['2nd-value-state'] = None
        data['q-val-state'] = None
        data['d-val-state'] = None

    if data['2nd-value-state'] == "ok":
        ri=int(data["2nd-value-range"])
        qdr = data['QDR']
        rt = range_translations['2nd-value'][qdr][ri]
        unit = rt[qdr]['unit']
        _range = rt[qdr]['range']
        data['2nd-value']=data['2nd-value']*unit
        if qdr == "R":
            _range=_range.to(unit)
        data['2nd-value-range'] = _range
        data.update({'2nd-value-range-index': ri })
        data.update({'2nd-value-unit':unit})
    else:
        data['2nd-value']=data['2nd-value-state']


    if data['d-val-state'] == "ok":
        ri=int(data["d-val-range"])
        qdr = data['QDR']
        rt = range_translations['2nd-value'][qdr][ri]
        unit = rt[qdr]['unit']
        _range = rt[qdr]['range']
        data['d-val']=data['d-val']*unit
        if qdr == "R":
            _range=_range.to(unit)
        data['d-val-range'] = _range
        data.update({'d-val-range-index': ri })
        data.update({'d-val-unit':unit})
    else:
        data['d-val']=data['d-val-state']

    if data['q-val-state'] == "ok":
        ri=int(data["q-val-range"])
        qdr = data['QDR']
        rt = range_translations['2nd-value'][qdr][ri]
        unit = rt[qdr]['unit']
        _range = rt[qdr]['range']
        data['q-val']=data['q-val']*unit
        if qdr == "R":
            _range=_range.to(unit)
        data['q-val-range'] = _range
        data.update({'q-val-range-index': ri })
        data.update({'q-val-unit':unit})
    else:
        data['q-val']=data['q-val-state']

    return data

serial_kwargs = {
                'baudrate' : 1200,
                'bytesize' : 7,
                'parity'   : 'E',
                'stopbits'  : 1,
                'port'     : '/dev/ttyUSB0',
                'timeout'  : 1
              }
s = Serial(**serial_kwargs)

def get_reply(decode=True,print_data=False):
    data = s.readall()
    if not data is None and decode:
        data=data.decode()
    if print_data:
        print(data,end='')
    return data

def read_data(print_data=True):
    s.write(b'N')
    s.flush()
    data=get_reply(print_data=print_data)
    return decode_data(data)

def exit_setup(print_data=True):
    s.write(b'[BXXXXXX]')
    return get_reply(print_data=print_data)

def enter_setup(print_data=True):
    s.write(b'S')
    return get_reply(print_data=print_data)

def printsort(k):
    if k == 'LCR-value':
        return 0
    if k == '2nd-value':
        return 1
    if k == 'q-val':
        return 2
    if k == 'd-val':
        return 3
    return k.encode()[0]

def print_data(data):
    exclude={
                '2nd-value-range': None, # None -> exclude no matter the value
                '2nd-value-unit':None,
                '2nd-value-state':None,
                '2nd-value-range-index': None,
                'LCR-value-range': None,
                'LCR-value-state': None,
                'LCR-value-unit': None,
                'LCR-value-range-index': None,
                'adapter': 'False',
                'backlight': 'disabled',
                'battery': 'ok',
                'd-val-range': None,
                'd-val-unit': None,
                'd-val-state': None,
                'd-val-range-index': None,
                'fuse': 'normal',
                'hold': 'disabled',
                'limit-mode': 'disabled',
                'min_max_avg-mode': 'disabled',
                'q-val-range': None,
                'q-val-unit': None,
                'q-val-state': None,
                'q-val-range-index': None,
                'rel-mode': 'disabled',
                'sequence':  None,
                'set-mode': 'disabled',
                'tol-mode': 'disabled',
            }
    ek=exclude.keys()
    pk=[]
    for k,v in data.items():
        if not k in ek:
            pk.append(k)
        else:
            if not exclude[k] is None and exclude[k] != data[k]:
                pk.append(k)
    pk.sort(key=printsort,reverse=True)
    for k in pk:
        print("{:>20} = {}".format(k,data[k]))

if __name__ == '__main__':
    #print(help(Serial))
    #print(read_data())
    data=read_data(print_data=False)
    #pprint(data)
    data=process_data_further(data)
    print_data(data)
# vim: set foldlevel=0 :
