import requests


class CDMIClient:
    def __init__(self, auth):
        self.auth = auth

    def cdmi_head(self, url):
        headers = {
            'Accept': 'application/cdmi-object',
            'X-CDMI-Specification-Version': '1.0.2',
        }
        r = requests.head(url, headers=headers, auth=self.auth)
        return r

    def cdmi_get(self, url):
        headers = {
            'Accept': 'application/cdmi-object',
            'X-CDMI-Specification-Version': '1.0.2',
        }

        r = requests.get(url, headers=headers, auth=self.auth)

        return r

    def cdmi_put(self, url, data):
        headers = {
            'Content-type': 'application/cdmi-object',
            'X-CDMI-Specification-Version': '1.0.2',
        }

        return requests.put(url, headers=headers, data=data, auth=self.auth)
