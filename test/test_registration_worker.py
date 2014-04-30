import os
import unittest
from datetime import datetime
import requests


from eudat_http_api.registration.models import RegistrationRequest
from eudat_http_api import create_app
from eudat_http_api.registration.models import db

from httmock import HTTMock, all_requests
from requests.auth import HTTPBasicAuth




# @urlmatch(netloc=r'(.*\.)?foo.bar$')
from eudat_http_api.registration.registration_worker import check_src, \
    check_url, check_metadata


@all_requests
def my_mock(url, request):
    return {'status_code': requests.codes.ok,
            'content': 'Incoming request %s on %s' % (request, url)}

@all_requests
def failing_mock(url, request):
    return {'status_code': requests.codes.not_found, 'content': ''}

class Context():
    pass


class TestCase(unittest.TestCase):
    def setUp(self):
        app = create_app('test_config')
        self.app = app
        self.client = app.test_client()
        db.create_all()

    def tearDown(self):
        db.drop_all()
        os.remove(self.app.config['DB_FILENAME'])

    def add_request(self):
        r = RegistrationRequest(src_url='http://www.foo.bar/',
                                status_description='Registration request '
                                                   'created',
                                timestamp=datetime.utcnow())
        db.session.add(r)
        db.session.commit()
        return r

    def test_check_url(self):
        c = Context()
        c.src_url = 'http://www.google.com/aaa?value'
        c.auth = HTTPBasicAuth('user', 'pass')

        with HTTMock(my_mock):
            ret = check_url(c.src_url, c.auth)

        assert ret is True

    def test_check_url_fails(self):
        c = Context()
        c.src_url = 'http://www.google.com/aaa?value'
        c.auth = HTTPBasicAuth('user', 'pass')

        with HTTMock(failing_mock):
            ret = check_url(c.src_url, c.auth)

        assert ret is False

    def test_check_src(self):
        r = self.add_request()
        c = Context()
        c.src_url = 'http://www.google.com/aaa?value'
        c.auth = HTTPBasicAuth('user', 'pass')
        c.request_id = r.id
        with HTTMock(my_mock):
            ret = check_src(c)
        assert ret
        assert c.status.startswith('Checking source')
        r = RegistrationRequest.query.get(c.request_id)
        assert r.status_description.startswith('Checking source')
        assert c.status == r.status_description

    def test_check_md(self):
        r = self.add_request()
        c = Context()
        c.md_url = 'http://www.google.com/aaa?metadata'
        c.auth = HTTPBasicAuth('user', 'pass')
        c.request_id = r.id
        with HTTMock(my_mock):
            ret = check_metadata(c)
        assert ret
        assert c.status.startswith('Checking metadata')

        r = RegistrationRequest.query.get(c.request_id)
        assert r.status_description == c.status