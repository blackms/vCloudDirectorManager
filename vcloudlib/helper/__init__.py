__author__ = 'alessio.rocchi'

from random import choice

from vcloudlib.objects import User, Metadata

charsets = [
    'abcdefghijklmnopqrstuvwxyz',
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    '0123456789']


def mk_password(length=16):
    pwd = []
    charset = choice(charsets)
    while len(pwd) < length:
        pwd.append(choice(charset))
        charset = choice(list(set(charsets) - {charset}))
    return "".join(pwd)


def create_org_user(vcloud_session, username, full_name, org_name, password=None, email=''):
    headers = vcloud_session.get_vcloud_headers()
    headers['Content-Type'] = 'application/vnd.vmware.admin.user+xml'
    if password is None:
        password = mk_password(length=11)
    role_href = vcloud_session.get_role(name='Organization Administrator')[0].href
    org_href = vcloud_session.get_org(name=org_name)[0].href
    # https://admin01.dc4.private.arubacloud.fr/api/admin/org/12d08c6a-a71c-42ae-a4ce-230e0a915ae9/users
    user_href = '{}/users'.format(org_href.replace('api/', 'api/admin/'))
    user_scheme = User(name=username,
                       password=password,
                       full_name=full_name,
                       email=email,
                       role_href=role_href)
    create_vdc_response = requests.post(url=user_href,
                                        data=user_scheme.get_xml(),
                                        headers=headers,
                                        verify=vcloud_session.verify)
    if create_vdc_response.status_code != requests.codes.created:
        return {'status': 'fail', 'content': create_vdc_response.content}
    return {'status': 'success', 'password': password}


def set_org_metadata(vcloud_session, org_name, metadata):
    """
    Set metadata for the given organization name
    :param vcloud_session: :class VCS object
    :param org_name: string representing the org name
    :param metadata: a list containing a dict with key: value for any metadata to add.
    :return:
    """
    headers = vcloud_session.get_vcloud_headers()
    headers['Content-Type'] = 'application/vnd.vmware.vcloud.metadata+xml'
    org_href = vcloud_session.get_org(name=org_name)[0].href
    metadata_xml_scheme = Metadata()
    for element in metadata:
        metadata_xml_scheme.add_metadata_entry(element['key'], element['value'])
    metadata_href = '{}/metadata'.format(org_href.replace('api/', 'api/admin/'))
    set_org_metadata_response = requests.post(url=metadata_href,
                                              data=metadata_xml_scheme.get_xml(),
                                              headers=headers,
                                              verify=vcloud_session.verify)
    if set_org_metadata_response.status_code != requests.codes.accepted:
        return False
    return True

import tempfile
import logging
import requests

_logger = None


def _get_logger():
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("pyvcloud")
    _logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("%s/pyvcloud.log" % tempfile.gettempdir())
    formatter = logging.Formatter("%(asctime)-23.23s | %(levelname)-5.5s | %(name)-15.15s | %(module)-15.15s | %(funcName)-12.12s | %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    requests_logger = logging.getLogger("requests.packages.urllib3")
    requests_logger.addHandler(handler)
    requests_logger.setLevel(logging.DEBUG)

    return _logger


class Log(object):
    @staticmethod
    def debug(logger, s):
        if logger is not None:
            logger.debug(s)

    @staticmethod
    def error(logger, s):
        if logger is not None:
            logger.error(s)

    @staticmethod
    def info(logger, s):
        if logger is not None:
            logger.info(s)


class Http(object):
    @staticmethod
    def _log_request(logger, data=None, headers=None):
        if logger is not None:
            if headers is not None:
                for header in headers:
                    logger.debug('request header: %s: %s', header, headers[header])
            if data is not None:
                logger.debug('request data:\n %s', data)

    @staticmethod
    def _log_response(logger, response):
        if logger is not None:
            logger.debug('[%d] %s', response.status_code, response.text)

    @staticmethod
    def get(url, data=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(logger, data=data, headers=kwargs.get('headers', None))
        response = requests.get(url, data=data, verify=False, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def post(url, data=None, json=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(logger, data=data, headers=kwargs.get('headers', None))
        response = requests.post(url, data=data, json=json, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def put(url, data=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(logger, data=data, headers=kwargs.get('headers', None))
        response = requests.put(url, data=data, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def delete(url, data=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(logger, data=data, headers=kwargs.get('headers', None))
        response = requests.delete(url, data=data, **kwargs)
        Http._log_response(logger, response)
        return response





