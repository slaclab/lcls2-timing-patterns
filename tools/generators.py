from .seqlookup         import seq_lookup
from .periodicgenerator import PeriodicGenerator
from .traingenerator    import TrainGenerator
from .globals           import *
import collections


def generator(arg):
    if arg['generator']=='lookup':
        gen = collections.namedtuple('seq_lookup',['instr','async_start'])
        seq = seq_lookup(arg)
        return ('{}'.format(arg['name']),gen(**{'instr':seq['instr'],'async_start':seq['async_start']}))

    if arg['generator']=='train':
        arg['train_spacing']     = TPGSEC
        arg['trains_per_second'] = 1

        span = (arg['train_spacing']*(1-arg['trains_per_second']) +
                arg['bunch_spacing']*(arg['bunches_per_train']-1) +
                arg['start_bucket'])
        if span > TPGSEC:
            print('Bunch train spans the 1Hz marker.  Validation may not match.')
            print('Extending the validation simulation to the next 1-second interval')
            print('  may be necessary.')
            raise RuntimeError('Generator error')

        gen = TrainGenerator(charge            = arg['charge'],
                             start_bucket      = arg['start_bucket'],
                             bunch_spacing     = arg['bunch_spacing'],
                             bunches_per_train = arg['bunches_per_train'],
                             repeat            = arg['repeat'])

        return ('train (start={}, bunch_spacing={}, bunches_per_train={}, train_spacing={}, trains_per_second={})'
                .format(arg['start_bucket'],arg['bunch_spacing'],arg['bunches_per_train'],
                        arg['train_spacing'],arg['trains_per_second']),
                gen )
    
    if arg['generator']=='periodic':
        gen=PeriodicGenerator(arg['period'],arg['start_bucket'])
        name='periodic (period={}, start={})'.format(arg['period'],arg['start_bucket'])
        return (name,gen)

    raise RuntimeError('No generator matches {}'.format(arg['generator']))
