#!/usr/bin/env python3

from serial import Serial
from sys import exit,stderr,stdout
from time import sleep
from os import set_blocking
from types import FunctionType
from pprint import pprint
from re import match,sub
from pint import UnitRegistry
from math import inf
from pylib.electronic.resistor_utils import resistor_string_to_float


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
diml=ur.dimensionless

data_translation = [
        ('LCR', lambda x:x),
        ('QDR', lambda x:x),
        {   'A': ('freq', 1*kHz),
            'B': ('freq', 120*Hz)},
        {   'P': ('PAL/SER', 'PAL'),
            'S': ('PAL/SER', 'SER'),
            '_': ('PAL/SER', '_' )},
        { 'A': ('range_sel','auto'),
          'M': ('range_sel','manual')},
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

tolerances_R =  [ # format := ( percentage , add fixed value )
                (0.012 , 8 * 1e-3*Ohm),
                (0.008 , 5 * 1e-2*Ohm),
                (0.005 , 3 * 1e-1*Ohm),
                (0.005 , 3 * 1e+0*Ohm),
                (0.005 , 3 * 1e+1*Ohm),
                (0.005 , 5 * 1e+2*Ohm),
                (0.020 , 8 * 1e+3*Ohm),
                ]

tolerances = { "R" : tolerances_R }

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
        k=key+"state"
        if k in s.keys() and not s[key + "state"] == 'ok':
            value = s[key+"state"]
        else:
            try:
                s_value=''.join(parts)
                value = int(s_value)
            except ValueError:
                if s_value == '':
                    value=None
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
    if not hasattr(data,'keys'):
        return None
        raise Exception("ERROR: Could not find LCR-value-state, probably the device is not turned on or not connected.")
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
        if qdr in 'QDR':
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
            data['d-val']= qdr
    else:
        data['d-val']=data['d-val-state']

    if data['q-val-state'] == "ok":
        ri=int(data["q-val-range"])
        qdr = data['QDR']
        if qdr in 'QDR':
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
            data['q-val']=data['QDR']
    else:
        data['q-val']=data['q-val-state']

    return data

def init_serial():
    serial_kwargs = {
                    'baudrate' : 1200,
                    'bytesize' : 7,
                    'parity'   : 'E',
                    'stopbits'  : 1,
                    'port'     : '/dev/ttyUSB0',
                    'timeout'  : 1
                  }
    global s
    global serial
    s = Serial(**serial_kwargs)
    serial=s

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
    if data.strip() == "":
        return None
        raise Exception("ERROR: Could not get any data, probably the device is not turned on or not connected.")
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

def get_data(print_data=False):
    return process_data_further(read_data(print_data=print_data))

def main_setup(lcr="[lcr]",qdr="[qdr]", freq='120|1k',serpal='s|p',sel_range='auto|[0-6]'):
    """
    The defaults are regexes that will not change the setting.
    The possible options are described in the regexes.
    To change an option, set a value that the regex would match.
    Unset values are obtained from the lcr-meter and send but are not changed.
    """
    defaults=   {
                'lcr':'[lcr]',
                'qdr':'[qdr]',
                'freq':'120|1k',
                'serpal':'s|p',
                'sel_range':'auto|[0-6]',
                }
    current_values=get_data()
    current_values.update({ 'serpal': current_values["PAL/SER"][0] })
    current_values.update({ 'sel_range':current_values["range_sel"]})
    current_values.update({ 'qdr':current_values["QDR"]})
    current_values.update({ 'lcr':current_values["LCR"]})
    setup_values={}
    for k,v in defaults.items():
        if locals()[k] != v:
            # changed
            setup_values.update({k:locals()[k]})
        else:
            setup_values.update({k:current_values[k]})
    #print(setup_values)
    sv=setup_values
    cmdstr="[E"+(sv['lcr']+sv['qdr']+sv['serpal']+('A' if (sv['freq'] in [ "1k", 1*kHz]) else ('B' if (sv['freq'] in[120*Hz,'120']) else ''))).upper()
    cmdstr+= ("A" if sv['sel_range'] == "auto" else "M")
    if cmdstr[-1] == 'M':
        cmdstr+=str(int(sv['sel_range']))
    else:
        cmdstr+="0"
    cmdstr+="]"
    send_command(cmdstr)

def send_command(data):
    if type(data) is str:
        data=data.encode()
    enter_setup()
    s.write(data)
    s.flush()
    print(get_reply())
    exit_setup()

def default_setup(code,val):
    cmdstr='['
    cmdstr+=code
    cmdstr+=str(val)
    cmdstr+=']'
    send_command(cmdstr)

def set_relative(val):
    if not type(val) is float:
        val=float(val)
    val="{:04.0f}".format(val)
    default_setup("U? ",val)

def get_val1(blocking=False):
    while True:
        data=get_data()
        if not data is None and data['LCR-value-state'] == 'ok':
            seq=int(data['sequence'])
            return data['LCR-value'],data['LCR-value-range-index'],seq
        elif not blocking:
            return None,None,None

def remove_indexes(indexes,thing):
    _thing=thing
    thing=[]
    for i in range(len(_thing)):
        if not i in indexes:
            thing.append(_thing[i])
    return thing

def readfile2list(filepath):
    with open(filepath) as f:
        data=f.read()
    try:
        data=data.strip()
        if data[0]=='[' and data[-1] != ']':
            data+='\n]'
            print("appended \"\n]\"")
        l=eval(data)
    except SyntaxError:
        l=[]
        lines=data.split("\n")
        for line in lines:
            l.append(readline(line))
    return l

def readline(line):
    line=line.strip()
    try:
        data=eval(line)
    except SyntaxError:
        data=float(line)
    return data

def is_seq_continous(p,n):
    if p==9:
        return  n == 0 
    else:
        return n == p+1

def are_continuous(seq):
    if len(seq) in [0,1]:
        return False
    for i in range(len(seq)-1):
        if not is_seq_continous(seq[i],seq[i+1]):
            return False
    return True

def get_val(samples=3,mode="R",last_seq=None,verbose=False,precision='tol',maxtry=inf):
    VERBOSE=verbose
    MAXTRY=maxtry
    PRECISION=precision
    SAMPLESLEEP=0
    fails=0
    avgval=None
    vals=[]
    need_newline_stdout=False
    need_newline_stderr=False
    while fails <= MAXTRY and len(vals) < samples:
        val,range_index,seq=get_val1()
        if val is None:
            print('.',end="")
            stdout.flush()
            need_newline_stdout=True
            fails+=1
        else:
            vals.append((val,range_index,seq))
            print('o',end="",file=stdout)
            need_newline_stdout=True
            stdout.flush()
        # calc avgval befor loop exit
        if len(vals) > 0:
            _vals=[v[0] for v in vals]
            avgval=sum(_vals)/len(vals)
            # do check befor continue
            upper_index=len(vals)-1
            poplist=[]
            for ti in range(upper_index+1):
                if not ti <= upper_index:
                    break
                delta = vals[ti][0] - avgval
                delta = abs(delta)
                if PRECISION == 'tol':
                    # use tolerances
                    tol=tolerances[mode]
                    precision  = vals[ti][0]*tol[vals[ti][1]][0]
                    precision += tol[vals[ti][1]][1]
                else:
                    precision = PRECISION
                # add the precision
                val_ti = vals[ti]
                vals[ti]=(*val_ti,precision)
                # check the precision and add to remove/poplist if check fails
                if delta > precision:
                    poplist.append(ti)
                    if VERBOSE:
                        nl='\n' if need_newline_stderr else ''
                        print(nl+'Discarded unstable measurement: '+str(vals[ti][0]),file=stderr)
                        need_newline_stderr=False
                    else:
                        print("X",end='')
                        need_newline_stderr=True
                    fails+=1
            vals=remove_indexes(poplist,vals)
            if last_seq is None:
                sequences=[-2]
            else:
                sequences=[last_seq]
            sequences+= [v[2] for v in vals]
            if are_continuous(sequences):
                last_seq=vals[-1][2]
                vals=[]
                if VERBOSE:
                    nl='\n' if need_newline_stdout else ''
                    print(nl+"dropping vals because of continous sequence")
                    need_newline_stdout=False
                else:
                    print("x",end='')
                    stdout.flush()
                    need_newline_stdout=True
        sleep(SAMPLESLEEP)
    if need_newline_stdout:
        print()
    if need_newline_stderr:
        print(file=stderr)

    # return the worst precision
    worst_prec=inf*Ohm
    for v in vals:
        worst_prec = min(v[-1],worst_prec)

    return avgval,vals[-1][-2],worst_prec

def scan_values(filepath):
    last_seq_num = None
    while True:
        f=open(filepath,"at")
        try:
            val,last_seq_num,tol=get_val(samples=2,last_seq=last_seq_num)
            print(val)
            beep.play()
            f.write(sub('[ ]ohm','', str(val))+",\n")
        finally:
            f.close()

def init_audio():
    """
    """
    #from pyaudio import PyAudio as pa
    #global PyAudio
    #PyAudio=pa
    print("loading pygame for beep support...")
    from pygame import mixer
    mixer.init(frequency=44100,size=8,channels=1)
    from pygame.mixer import Sound
    global beep
    s = b'\x80\x80\x88\x97\x8f\xab\x97\xb9\x9e\xbf\xa5\xbc\xab\xb1\xb1\x9f\xb5\x88\xb9p\xbcZ\xbeJ\xbfA\xbfA\xbeI\xbcY\xbao\xb6\x87\xb1\x9d\xac\xb0'
    s+= b'\xa5\xbc\x9f\xbf\x97\xba\x90\xac\x88\x98\x80\x81xipUhFa@ZBTMO_JvF\x8eC\xa4A\xb4@\xbe@\xbfA\xb7B\xa7E\x92IzNcSPYC`@gEoRwe'
    beep=s*100
    beep=Sound(beep)

def test_audio():
    init_audio()
    beep.play()

def l2float(l):
    return [resistor_string_to_float(i) for i in l]

def calc_range_cross(r0,r1):
    """
    How much of r0 is in r1 ?
    r0:= |>---a---------b----------<|
    r1:= |>---------c-------d------<|
    """
    r0.sort()
    r1.sort()

    a,b = r0[0],r0[-1]
    c,d = r1[0],r1[-1]

    full=b-a
    
    if d<a:
        return 0
    elif c <= a and a <= d:
        start = a
        case=1
    elif a<c:
        start=c
        case=2
    if b<c:
        return 0
    elif a <= d and d <= b:
        case+=8
        end=d
    elif c<b:
        case+=4
        end=b
    part = end-start
    return part/full

def find_mode(filepath,min_rx=0.90):
    last_seq_num = None
    values = l2float(readfile2list(filepath))
    while True:
        val, last_seq_num, abs_error = get_val( samples=1, last_seq=last_seq_num, precision="tol" )
        for v in values:
            _v = v * Ohm
            # assume v was measured with the same absolute error as val
            range_val=[i*abs_error+val for i in [+1,-1]]
            range_v=[i*abs_error+_v for i in [+1,-1]]
            rx=calc_range_cross(range_val,range_v)
            if  rx >= min_rx:
                beep.play()
                sleep(0.3)
                beep.play()
                sleep(0.3)
                beep.play()
                print("FOUND: M: {} L: {}  rx = {:0.3f}".format(val,_v,rx))
            beep.play()
        print("NOTF:, val = {}  ".format(val) ,end='')

def parse_args():
    global args
    from argparse import ArgumentParser
    ap=ArgumentParser()
    ap.add_argument("-f",'--file',default=None)
    ap.add_argument("-s","--scan",action="store_true",default=False)
    ap.add_argument("-b","--beep",action="store_true",default=True)
    ap.add_argument("--test",action="store_true",default=False)
    ap.add_argument("-v","--verbose",action="store_true",default=True)
    args=ap.parse_args()

if __name__ == '__main__':
    parse_args()
    if args.test:
        print('audio test...')
        test_audio()
        inp=input("You should have heard a beep, press \"<Enter>\" here to continue.")
        print("testing done")
        exit()
    init_serial()
    if args.beep:
        init_audio()
    if args.scan and not args.file is None:
        scan_values(args.file)
    elif not args.scan and not args.file is None:
        # find mode
        print("interactive find-value-mode\nprogram emits double beep if value is in declared file ("+args.file+")")
        find_mode(args.file)
    
# vim: set foldlevel=0 :
