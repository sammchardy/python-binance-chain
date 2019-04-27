LEDGER_RESPONSE_CODES = {
    0x6400: 'Execution Error',
    0x6982: 'Empty buffer',
    0x6983: 'Output buffer too small',
    0x6986: 'Command not allowed',
    0x6A80: 'Incorrect tx data',
    0x6D00: 'INS not supported',
    0x6E00: 'CLA not supported',
    0x6F00: 'Unknown',
}


class LedgerRequestException(Exception):

    def __init__(self, response_code, request):
        self._response_code = response_code
        self._response_msg = LEDGER_RESPONSE_CODES.get(response_code, 'Unknown')

        self._request = request

    def __str__(self):  # pragma: no cover
        return f'LedgerRequestException(code={self._response_code}): {self._response_msg} - request {self._request}'
