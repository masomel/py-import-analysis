version = VERSION = __version__ = '0.0.2'

class Signals(object):
    __slots__ = ['_signals', '_connections', '_silenced', '_controller']

    def __init__(self, controller, *signals):
        self._signals = signals
        self._controller = controller
        self._connections = {}
        self._silenced = set()

    def get_connections(self):
        return self._connections
        
    def emit(self, signal, *args):
        if signal in self._signals:
            if signal not in self._silenced:
                if signal in self._connections:
                    returns = []
                    for func, user_data in self._connections[signal]:
                        # signal args
                        data = list(args)
                        # insert me
                        data.insert(0, self._controller)
                        # add user args
                        data.extend(list(user_data))
                        # call it
                        returns.append(func(*tuple(data)))
                    return returns
        else:
            raise TypeError('Signal is not a valid signal prototype.')
    
    def connect(self, signal, func, *user_data):
        if signal in self._signals:
            if hasattr(func, "__call__"):
                if signal in self._connections:
                    self._connections[signal].append((func,user_data))
                    return len(self._connections[signal])-1
                else:
                    self._connections[signal] = [(func,user_data)]
                    return 0
            else:
                raise TypeError('Callback must be a callable object.')
        else:
            raise TypeError('Signal: %s is not a valid signal listener.' % signal)
        
    def disconnect(self, signal, index):
        if signal in self._connections and index in self._connections[signal]:
            self._connections[signal].remove(index)
    
    def disconnect_all(self, match_class):
        for signal, callbacks in self._connections.iteritems():
            for index, cb in enumerate(callbacks):
                if hasattr(cb[0], 'im_class') and cb[0].im_class == match_class:
                    del self._connections[signal][index]

    def has_connection(self, signal):
        return len(self.get_connections().get(signal, [])) > 0

    def silence(self, *signals):
        """Method to silence these signals from triggering
        """
        [self._silenced.add(signal) for signal in signals]

    def listen(self, *signals):
        """Method to begin listening to silenced signals
        """
        [self._silenced.remove(signal) for signal in signals]
