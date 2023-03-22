import re
import requests
import json
import urllib3
import time

from requests.exceptions import ConnectionError
from requests.packages.urllib3.util.retry import Retry


# HTTP_ADAPTER = HTTPAdapter(max_retries=3)
REQ_TIMEOUT_T = (60, 60)


class Alkira(object):
    """
    RestApi Class
    Args:
    Returns:
    """

    def __init__(self,
                 url=None,
                 cookie=None,
                 headers=None,
                 data=None,
                 file=None,
                 login_d=None):

        self.url = url
        if not headers:
            self.headers = dict()
        self.data = data
        self.file = file
        self.login_d = login_d

        urllib3.disable_warnings()

        # Initialize the sessions object
        self.requests_session = requests.Session()

    def create(self,
               url=None,
               data=None,
               params_d=None,
               login_d=None,):

        if not url:
            url = self.url
        if not data:
            self.data = data
        if not login_d:
            login_d = self.login_d

        # Authenticate the session
        requests_session = self.create_session(url=url,
                                               login_d=login_d)

        try:
            if not data:
                self.headers['Content-type'] = 'application/json'
            else:
                self.headers = None
            response = self.requests_session.post(url=url,
                                                  json=data,
                                                  headers=self.headers,
                                                  params=params_d,
                                                  verify=False,)
            return response
        except ConnectionError as ce:
            print(f'Rest API create Exception: {ce}')
            return None

        return response

    def read(self,
             url=None):

        if not url:
            url = self.url

        # Use the same session as the provision call
        try:
            response = self.requests_session.get(url=url,
                                                 verify=False)
        except ConnectionError as ce:
            print(f'Rest API read Exception: {ce}')
            return None

        return response

    def get_login_url(self,
                      url=None):

        if url is None:
            url = self.url

        api_pat = re.compile(r'(.*/api/).*')
        match = api_pat.search(url)

        if match:
            api_url = match.group(1)
            login_url = f'{api_url}user/login'
            return login_url

        return None

    def get_session_url(self,
                        url=None):
        if url is None:
            url = self.url
        api_pat = re.compile(r'(.*/api/).*')
        match = api_pat.match(url)

        if match:
            api_url = match.group(1)
            session_url = f'{api_url}sessions'
            return session_url

        return None

    def create_session(self,
                       url=None,
                       login_d=None):

        self.login(login_d=login_d, url=url)
        self.session(url=url)

    def login(self,
              login_d=None,
              url=None):

        '''
        data_d = dict()

        data_d['userName'] = username
        data_d['password'] = password
        '''

        login_url = self.get_login_url(url=url)
        response = self.send_request(url=login_url, data=login_d)
        try:
            self.login_response_d = json.loads(response.content)
        except json.decoder.JSONDecodeError:
            self.login_response_d = dict()

    def session(self, url=None):
        session_url = self.get_session_url(url=url)
        response = self.send_request(url=session_url, data=self.login_response_d)
        self.session_d = response.content

    def send_request(self,
                     url=None,
                     data=None,):
        if not url:
            url = self.url

        headers = None
        response = self.requests_session.post(url=url,
                                              json=data,
                                              headers=headers,
                                              timeout=REQ_TIMEOUT_T,
                                              verify=False)
        return response

    def provision(self,
                  login_d=None,
                  tenant_network_url=None):

        provision_url = f'{tenant_network_url}/provision'

        resp = self.create(url=provision_url,
                           login_d=login_d)

        if resp is None:
            print(f'Provision Failure, please contact Alkira support')
            return False

        if resp.status_code > 300:
            print(f"Provision Failure, status_code: {resp.status_code}, please contact Alkira support")
            return False

        return True

    def provision_status(self,
                         max_timer=None,
                         tenant_network_url=None):

        if max_timer is None:
            max_timer = 7200

        step = 60

        timer = 0
        while timer < max_timer:
            response = self.read(url=tenant_network_url)
            if response is None:
                print('Error reading Alkira tenantnetworks url, check your credentials or contact Alkira support')
                return False

            if response.status_code > 300:
                print('Error reading Alkira tenantnetworks url, check your credentials or Alkira contact support')

            try:
                response_data = json.loads(response.content)
                state = response_data.get('state')
                if state == 'SUCCESS':
                    print('Tenant Provision Success')
                    return True

                if state == 'FAILED':
                    print('Tenant Provision Failure')
                    return False

                if state == 'PARTIAL_SUCCESS':
                    print('Tenant Provision Partial Success - A connector or service provision is likely to have failed')
                    return False

                time.sleep(step)
                timer += step

                print(f'Provisioning in progress, elapsed time (in sec): {timer}')

            except json.decoder.JSONDecodeError:
                print('Error decoding tenantnetworks data, contact Alkira support')

        print(f'Provisioning did not complete even after {max_timer} seconds, check portal for progress')

        return False

if __name__ == '__main__':
    ak_o = Alkira()

    login_d = dict()
    login_d['userName'] = <username>
    login_d['password'] = <password>

    tenant_network_url = f'https://msk.portal.alkira.com/api/tenantnetworks/122'

    prov = ak_o.provision(login_d=login_d,
                          tenant_network_url=tenant_network_url)

    # Do not remove this sleep, needed to capture the provision transition
    time.sleep(60)

    # Check for status
    max_timer = 7200
    if prov:
        prov_status = ak_o.provision_status(tenant_network_url=tenant_network_url,
                                            max_timer=max_timer)
