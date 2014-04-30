from flask import Blueprint
import flask
from flask import current_app
from flask import request
from flask import json
from flask import abort, url_for

from eudat_http_api.common import request_wants, ContentTypes

from eudat_http_api.registration.models import db
from eudat_http_api import auth
from eudat_http_api.registration.registration_worker import add_task, \
    start_workers

from models import RegistrationRequest, RegistrationRequestSerializer
from datetime import datetime
from requests.auth import HTTPBasicAuth

registration = Blueprint('registration', __name__,
                         template_folder='templates')


class Context():
    pass


def get_hal_links(reg_requests, page):
    """returns links in json hal format"""
    navi = dict()
    navi['self'] = {'href': url_for('get_requests', page=page)}
    if reg_requests.has_next:
        navi['next'] = {
            'href': url_for('get_requests', page=reg_requests.next_num)}
    if reg_requests.has_prev:
        navi['prev'] = {
            'href': url_for('get_requests', page=reg_requests.prev_num)}

    return navi


@registration.route('/request/', methods=['GET'])
@auth.requires_auth
def get_requests():
    """Get a requests list."""
    page = int(request.args.get('page', '1'))
    reg_requests = RegistrationRequest.query.order_by(
        RegistrationRequest.timestamp.desc()).paginate(page,
                                                       current_app.config[
                                                           'REQUESTS_PER_PAGE'],
                                                       False)

    if request_wants(ContentTypes.json):
        return flask.jsonify(
            {"requests": RegistrationRequestSerializer(reg_requests.items,
                                                       many=True).data,
             "_links": get_hal_links(reg_requests, page)})

    return flask.render_template('requests.html', requests=reg_requests)


def extract_auth_creds():
    return HTTPBasicAuth(request.authorization.username, request.authorization
                         .password)


def extract_url(url):
    #FIXME: generalize beyond cdmi
    return url+"?value", url+"?metadata"


@registration.before_app_first_request
def initialize():
    start_workers(5)

@registration.route('/request/', methods=['POST'])
@auth.requires_auth
def post_request():
    """Submit a new registration request

  Specify in the message body:
  src: url of the source file
  checksum: the file you expect the file will have.

  The function returns a URL to check the status of the request.
  The URL includes a request ID.
  """
    current_app.logger.debug('Entering post_request()')

    if flask.request.headers.get('Content-Type') == 'application/json':
        req_body = json.loads(flask.request.data)
    else:
        req_body = flask.request.form

    r = RegistrationRequest(src_url=req_body['src_url'],
                            status_description='Registration request created',
                            timestamp=datetime.utcnow())
    db.session.add(r)
    db.session.commit()
    db.session.close()

    c = Context()
    c.request_id = r.id
    c.auth = extract_auth_creds()
    c.src_url, c.md_url = extract_url(req_body['src_url'])

    add_task(c)

    if request_wants(ContentTypes.json):
        return flask.jsonify(request_id=r.id), 201
    else:
        return flask.render_template('requestcreated.html', reg=r), 201


@registration.route('/request/<request_id>', methods=['GET'])
@auth.requires_auth
def get_request(request_id):
    """Poll the status of a request by ID."""
    r = RegistrationRequest.query.get(request_id)

    #TODO: json error?
    if r is None:
        return abort(404)

    if request_wants(ContentTypes.json):
        return flask.jsonify(
            {'request': RegistrationRequestSerializer(r).data})

    return flask.render_template('singleRequest.html', r=r)


#### /registered container ####
#jj: this is a separate component?

@registration.route('/registered/<pid_prefix>/', methods=['GET'])
@auth.requires_auth
def get_pids_by_prefix():
    # search PIDs with this prefix on handle.net

    # return list of PIDs
    # (with links to /registered/<full_pid>) to download
    pass


@registration.route('/registered/<pid_prefix>/<pid_suffix>', methods=['GET'])
@auth.requires_auth
def get_pid_by_handle(pid_prefix, pid_suffix):
    """Retrieves a data object by PID."""
    pid = pid_prefix + '/' + pid_suffix


    # resolve PID

    # extract link to data object

    # choose link to data object

    # return data object
    return 'nothing there, baeh!'
