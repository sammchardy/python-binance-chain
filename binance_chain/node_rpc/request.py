import itertools
import json
from collections import OrderedDict


class RpcRequest:

    id_generator = itertools.count(1)

    def __init__(self, method, params=None):

        self._method = method
        self._params = params

    def _sort_request(self, request):
        sort_order = ["jsonrpc", "method", "params", "id"]
        return OrderedDict(sorted(request.items(), key=lambda k: sort_order.index(k[0])))

    def __str__(self):

        request = {
            'jsonrpc': '2.0',
            'method': self._method,
            'id': next(self.id_generator)
        }

        if self._params:
            request['params'] = self._params

        return json.dumps(self._sort_request(request), separators=(',', ':'), ensure_ascii=False)
