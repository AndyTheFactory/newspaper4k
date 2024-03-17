from _typeshed import Incomplete
from requests.adapters import HTTPAdapter
from requests.sessions import Session

__version__: str

class CipherSuiteAdapter(HTTPAdapter):
    __attrs__: Incomplete
    ssl_context: Incomplete
    cipherSuite: Incomplete
    source_address: Incomplete
    server_hostname: Incomplete
    ecdhCurve: Incomplete
    def __init__(self, *args, **kwargs) -> None: ...
    def wrap_socket(self, *args, **kwargs): ...
    def init_poolmanager(self, *args, **kwargs): ...
    def proxy_manager_for(self, *args, **kwargs): ...

class CloudScraper(Session):
    debug: Incomplete
    disableCloudflareV1: Incomplete
    delay: Incomplete
    captcha: Incomplete
    doubleDown: Incomplete
    interpreter: Incomplete
    requestPreHook: Incomplete
    requestPostHook: Incomplete
    cipherSuite: Incomplete
    ecdhCurve: Incomplete
    source_address: Incomplete
    server_hostname: Incomplete
    ssl_context: Incomplete
    allow_brotli: Incomplete
    user_agent: Incomplete
    solveDepth: Incomplete
    headers: Incomplete
    def __init__(self, *args, **kwargs) -> None: ...
    def perform_request(self, method, url, *args, **kwargs): ...
    def simpleException(self, exception, msg) -> None: ...
    @staticmethod
    def debugRequest(req) -> None: ...
    def decodeBrotli(self, resp): ...
    proxies: Incomplete
    def request(self, method, url, *args, **kwargs): ...
    @classmethod
    def create_scraper(cls, sess: Incomplete | None = None, **kwargs): ...
    @classmethod
    def get_tokens(cls, url, **kwargs): ...
    @classmethod
    def get_cookie_string(cls, url, **kwargs): ...

create_scraper: Incomplete
session: Incomplete
get_tokens: Incomplete
get_cookie_string: Incomplete
