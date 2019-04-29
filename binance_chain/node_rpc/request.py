import ujson as json
from collections import OrderedDict


class RpcRequest:

    def __init__(self, method, id, params=None):

        self._method = method
        self._params = params
        self._id = id

    def _sort_request(self, request):
        sort_order = ["jsonrpc", "method", "params", "id"]
        return OrderedDict(sorted(request.items(), key=lambda k: sort_order.index(k[0])))

    def __str__(self):

        request = {
            'jsonrpc': '2.0',
            'method': self._method,
            'id': self._id
        }

        if self._params:
            request['params'] = self._params

        return json.dumps(self._sort_request(request), ensure_ascii=False)
