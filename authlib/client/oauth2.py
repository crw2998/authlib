from requests import Session
from ..common.security import generate_token
from ..common.urls import url_decode


class OAuth2Session(Session):
    def __init__(self, client_id, client_secret=None, token=None,
                 token_placement=None, state=None):
        super(OAuth2Session, self).__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token
        self.token_placement = token_placement or 'header'
        self.state = state or generate_token

        self.compliance_hook = {
            'access_token_response': set(),
            'refresh_token_response': set(),
            'protected_request': set(),
        }

    def authorization_url(self, url, state=None, **kwargs):
        pass

    def fetch_access_token(
            self, url=None, code=None, authorization_response=None,
            body='', auth=None, username=None, password=None, method='POST',
            timeout=None, headers=None, verify=True, proxies=None, **kwargs):
        if url is None and authorization_response:
            return self.token_from_fragment(authorization_response)

        if headers is None:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            }

        if method.upper() == 'POST':
            resp = self.post(
                url, data=dict(url_decode(body)), timeout=timeout,
                headers=headers, auth=auth, verify=verify, proxies=proxies
            )
        else:
            resp = self.get(
                url, params=dict(url_decode(body)), timeout=timeout,
                headers=headers, auth=auth, verify=verify, proxies=proxies
            )

        for hook in self.compliance_hook['access_token_response']:
            resp = hook(resp)
        return {}

    def fetch_token(self, url, **kwargs):
        """Alias for fetch_access_token. Compatible with requests-oauthlib."""
        return self.fetch_access_token(url, **kwargs)

    def token_from_fragment(self, authorization_response):
        pass

    def refresh_token(self, url, **kwargs):
        pass

    def request(self, method, url, data=None, headers=None,
                withhold_token=False, **kwargs):
        return super(OAuth2Session, self).request(
            method, url, headers=headers, data=data, **kwargs)

    def register_compliance_hook(self, hook_type, hook):
        """Register a hook for request/response tweaking.

        Available hooks are:
        * access_token_response: invoked before token parsing.
        * refresh_token_response: invoked before refresh token parsing.
        * protected_request: invoked before making a request.
        """
        if hook_type not in self.compliance_hook:
            raise ValueError('Hook type %s is not in %s.',
                             hook_type, self.compliance_hook)
        self.compliance_hook[hook_type].add(hook)