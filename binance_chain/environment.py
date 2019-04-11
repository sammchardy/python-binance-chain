

class BinanceEnvironment:
    PROD_ENV = {
        'api_url': 'https://dex.binance.org',
        'wss_url': 'wss://dex.binance.org/api/',
        'hrp': 'bnb'
    }
    TESTNET_ENV = {
        'api_url': 'https://testnet-dex.binance.org',
        'wss_url': 'wss://testnet-dex.binance.org/api/',
        'hrp': 'tbnb'
    }

    def __init__(self, api_url: str = None, wss_url: str = None, hrp: str = None):
        """Create custom environment

        """

        self._api_url = api_url or self.PROD_ENV['api_url']
        self._wss_url = wss_url or self.PROD_ENV['wss_url']
        self._hrp = hrp or self.PROD_ENV['hrp']

    @classmethod
    def get_production_env(cls):
        return cls(**cls.PROD_ENV)

    @classmethod
    def get_testnet_env(cls):
        return cls(**cls.TESTNET_ENV)

    @property
    def api_url(self):
        return self._api_url

    @property
    def wss_url(self):
        return self._wss_url

    @property
    def hrp(self):
        return self._hrp

    def hash(self):
        return hash(f"{self.api_url}{self.wss_url}{self.hrp}")
