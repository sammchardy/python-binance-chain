from binance_chain.environment import BinanceEnvironment


class TestEnvironment:

    def test_prod_environment(self):

        env = BinanceEnvironment()

        assert env.hrp == BinanceEnvironment.PROD_ENV['hrp']
        assert env.wss_url == BinanceEnvironment.PROD_ENV['wss_url']
        assert env.api_url == BinanceEnvironment.PROD_ENV['api_url']

        prod_env = BinanceEnvironment.get_production_env()

        assert prod_env.hrp == BinanceEnvironment.PROD_ENV['hrp']
        assert prod_env.wss_url == BinanceEnvironment.PROD_ENV['wss_url']
        assert prod_env.api_url == BinanceEnvironment.PROD_ENV['api_url']

    def test_testnet_environment(self):
        env = BinanceEnvironment.get_testnet_env()

        assert env.hrp == BinanceEnvironment.TESTNET_ENV['hrp']
        assert env.wss_url == BinanceEnvironment.TESTNET_ENV['wss_url']
        assert env.api_url == BinanceEnvironment.TESTNET_ENV['api_url']

    def test_custom_environment(self):

        api_url = 'my_api_url'
        wss_url = 'my_wss_url'
        hrp = 'my_hrp'
        env = BinanceEnvironment(api_url, wss_url, hrp)

        assert env.hrp == hrp
        assert env.wss_url == wss_url
        assert env.api_url == api_url
