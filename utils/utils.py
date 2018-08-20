import queue


class CallbackMixin:
    def __init__(self, *args, **kwargs):
        self.callback_list = []
        super(CallbackMixin, self).__init__(*args, **kwargs)

    def register_callback(self, callback):
        self.callback_list.append(callback)

    def _call_all(self, new_value):
        for callback in self.callback_list:
            callback(new_value)


class CallbackImmutableValue(CallbackMixin):
    def __init__(self, value):
        self._value = value
        super(CallbackImmutableValue, self).__init__()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._call_all(new_value)
        self._value = new_value


class CallbackQueue(CallbackMixin, queue.Queue):
    def __init__(self, *args, **kwargs):
        super(CallbackQueue, self).__init__(*args, **kwargs)

    def _put(self, item):
        super(CallbackQueue, self)._put(item)
        self._call_all(self)

    def _get(self):
        self._call_all(self)
        obj = super(CallbackQueue, self)._get()
        self._call_all(self)
        return obj
