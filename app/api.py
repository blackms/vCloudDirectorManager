from itertools import chain

from flask import jsonify

from app import global_variable

__author__ = 'alessio.rocchi'


@global_variable.app.route('/api/v1.0/get_ips/<org_name>', methods=['GET'])
def get_ips(org_name):
    ip_list = []
    if global_variable.jsonified_data[org_name]:
        org_data = global_variable.jsonified_data[org_name]
        ip_list = list(chain(*[x['usedIp'] for x in org_data.values()]))
    return jsonify({'ips': ip_list})
