import re
from typing import Optional

from btchip.btchip import writeUint32LE, BTChipException

from binance_chain.environment import BinanceEnvironment


class LedgerApp:

    BNC_CLA = 0xbc
    BNC_INS_GET_VERSION = 0x00
    BNC_INS_PUBLIC_KEY_SECP256K1 = 0x01
    BNC_INS_SIGN_SECP256K1 = 0x02
    BNC_INS_SHOW_ADDR_SECP256K1 = 0x03
    ACCEPT_STATUSES = 0x9000

    CHUNK_SIZE = 250
    HD_PATH = "44'/714'/0'/0/0"

    def __init__(self, dongle, env: Optional[BinanceEnvironment] = None):
        self._dongle = dongle
        self._path = LedgerApp.HD_PATH
        self._env = env or BinanceEnvironment.get_production_env()
        self._hrp = self._env.hrp

    def get_version(self):
        result = {}
        apdu = [self.BNC_CLA, self.BNC_INS_GET_VERSION, 0x00, 0x00, 0x00]
        response = self._dongle.exchange(bytearray(apdu))

        result['compressedKeys'] = (response[0] == 0x01)
        result['version'] = "%d.%d.%d" % (response[2], response[3], response[4])
        result['specialVersion'] = response[1]
        return result

    def get_public_key(self):
        result = {}
        dongle_path = self._parse_hd_path(self._path)
        apdu = [self.BNC_CLA, self.BNC_INS_PUBLIC_KEY_SECP256K1, 0x00, 0x00, len(dongle_path)]
        apdu.extend(dongle_path)
        response = self._dongle.exchange(bytearray(apdu))

        return_code = response[:-2]
        result['pk'] = response[0: 1 + 64]
        result['return_code'] = return_code[0] * 256 + return_code[1]

        # TODO: handle error response

        return result['pk']

    def show_address(self):
        dongle_path = self._parse_hrp(self._hrp) + self._parse_hd_path(self._path)
        apdu = [self.BNC_CLA, self.BNC_INS_SHOW_ADDR_SECP256K1, 0x00, 0x00, len(dongle_path)]
        apdu.extend(dongle_path)
        response = self._dongle.exchange(bytearray(apdu))
        # TODO: check 0x9000 response
        return response

    def _get_sign_chunks(self, msg: bytes):
        chunks = [self._parse_hd_path(self._path)]
        chunks += [msg[i:i + self.CHUNK_SIZE] for i in range(0, len(msg), self.CHUNK_SIZE)]
        return chunks

    def sign(self, msg: bytes):
        chunks = self._get_sign_chunks(msg)
        response = ''
        for idx, chunk in enumerate(chunks):
            apdu = [self.BNC_CLA, self.BNC_INS_SIGN_SECP256K1, idx + 1, len(chunks), len(chunk)]
            apdu.extend(chunk)
            response = self._dongle.exchange(bytearray(apdu))
        return response

    def _parse_hd_path(self, path):
        if len(path) == 0:
            return bytearray([0])
        result = []
        elements = path.split('/')
        if len(elements) > 10:
            raise BTChipException("Path too long")
        for pathElement in elements:
            element = re.split('\'|h|H', pathElement)
            if len(element) == 1:
                writeUint32LE(int(element[0]), result)
            else:
                writeUint32LE(0x80000000 | int(element[0]), result)
        return bytearray([len(elements)] + result)

    def _parse_hrp(self, hrp):
        return bytearray([len(hrp)]) + hrp.encode()
