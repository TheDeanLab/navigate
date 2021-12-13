class Observable:
    def __init__(self, initialValue=None):
        self.data = initialValue
        self.callbacks = {}

    def addCallback(self, func):
        self.callbacks[func] = 1

    def delCallback(self, func):
        del self.callback[func]

    def _docallbacks(self):
        for func in self.callbacks:
            func(self.data)

    def set(self, data):
        self.data = data
        self._docallbacks()

    def get(self):
        return self.data

    def unset(self):
        self.data = None


class Model:
    def __init__(self):
        self.myMoney = Observable(0)

    def addMoney(self, value):
        self.myMoney.set(self.myMoney.get() + value)

    def removeMoney(self, value):
        self.myMoney.set(self.myMoney.get() - value)