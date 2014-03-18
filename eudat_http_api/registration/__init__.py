# -*- coding: utf-8 -*-

from flask import Blueprint
import flask
from flask import current_app
from flask import request
from flask import json
from flask import abort, url_for

from eudat_http_api.registration.models import db
from eudat_http_api.registration import registration_worker
from eudat_http_api import invenioclient
from eudat_http_api import auth
from models import RegistrationRequest, RegistrationRequestSerializer
from config import REQUESTS_PER_PAGE

from datetime import datetime
# it seems not to be possible to send
# http requests from a separate Process
#from multiprocessing import Process
from threading import Thread

registration = Blueprint('registration', __name__,
                         template_folder='templates')


def request_wants_json():
    """from http://flask.pocoo.org/snippets/45/"""
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
           request.accept_mimetypes[best] > \
           request.accept_mimetypes['text/html']


def get_hal_links(reg_requests, page):
    """returns links in json hal format"""
    navi = dict()
    navi['self'] = {'href': url_for('get_requests', page=page)}
    if reg_requests.has_next:
        navi['next'] = {'href': url_for('get_requests', page=reg_requests.next_num)}
    if reg_requests.has_prev:
        navi['prev'] = {'href': url_for('get_requests', page=reg_requests.prev_num)}

    return navi


@registration.route('/request/', methods=['GET'])
@auth.requires_auth
def get_requests():
    """Get a requests list."""
    page = int(request.args.get('page', '1'))
    reg_requests = RegistrationRequest.query.order_by(RegistrationRequest.timestamp.desc()).paginate(page,
                                                                                                     REQUESTS_PER_PAGE,
                                                                                                     False)

    if request_wants_json():
        return flask.jsonify(
            {"requests": RegistrationRequestSerializer(reg_requests.items, many=True).data,
             "_links": get_hal_links(reg_requests, page)})

    return flask.render_template('requests.html', requests=reg_requests)


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

    req_body = None
    if flask.request.headers.get('Content-Type') == 'application/json':
        req_body = json.loads(flask.request.data)
    else:
        req_body = flask.request.form

    src_url = req_body['src_url']
    #TODO: check if src is a valid URL
    r = RegistrationRequest(src_url=src_url, status_description='W', timestamp=datetime.utcnow())
    db.session.add(r)
    db.session.commit()

    # start worker
    p = Thread(target=registration_worker.register_data_object,
               args=r.id)
    p.start()

    if request_wants_json():
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

    if request_wants_json():
        return flask.jsonify({'request': RegistrationRequestSerializer(r).data})

    return flask.render_template('singleRequest.html', r=r)


#### /registered container ####


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

    if 'metadata' in flask.request.args:
        invenioclient.get_metadata(pid)

    # resolve PID

    # extract link to data object

    # choose link to data object

    # return data object
    return 'nothing there, baeh!'