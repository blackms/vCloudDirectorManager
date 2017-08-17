import json
import time
from collections import OrderedDict
from xml.etree import ElementTree

import requests
from flask import render_template, request, jsonify

from app import global_variable, Config
from helper import wait_for_task, get_less_used_network
from vcloudlib.helper import create_org_user, set_org_metadata
from vcloudlib.objects import AdminOrg, CreateVdcParams, EdgeGateway, OrgVdcNetwork, EdgeGatewayServiceConfiguration, \
    UpdateVdcStorageProfiles, ControlAccessParams
from vcloudlib.schema.vcd.v1_5.schemas.vcloud import organizationType, taskType, queryRecordViewType

__author__ = 'alessio.rocchi'

GATEWAY_TRY_COUNT = 10
BUSY_MESSAGE = "is busy, cannot proceed with the operation."


@global_variable.app.route('/orgs')
def orgs():
    return '<br />'.join(x.name for x in global_variable.vcs.orgList)


@global_variable.app.route('/vm')
def vm():
    return render_template('vm.html')


@global_variable.app.route('/')
def summary():
    ordered_dict_jsonified = OrderedDict(sorted(global_variable.jsonified_data.items(), key=lambda x: x, reverse=True))
    return render_template('summary.html', data=ordered_dict_jsonified)


@global_variable.app.route('/findvm', methods=['POST'])
def findvm():
    data = request.form
    vm_name = data['vmname']
    _vm = global_variable.vcs.get_vm_by_name(name=vm_name)[0]
    if _vm is None:
        return 'VM Not Found'
    vm_obj = {'href': _vm.href,
              'org_href': _vm.org,
              'status': _vm.status,
              'storage_profile': _vm.storageProfileName,
              'datastore_name': _vm.datastoreName,
              'vapp_name': _vm.containerName,
              'host': _vm.hostName,
              'vdc': _vm.vdc,
              'name': vm_name
              }
    from vcloudlib.helper import Http
    from vcloudlib.schema.vcd.v1_5.schemas.vcloud import organizationType, vdcType
    org_content = Http.get(vm_obj['org_href'], headers=global_variable.vcs.get_vcloud_headers())
    org_object = organizationType.parseString(org_content.content)
    vm_obj['org_name'] = org_object.name
    vdc_content = Http.get(vm_obj['vdc'], headers=global_variable.vcs.get_vcloud_headers())
    vdc_object = vdcType.parseString(vdc_content.content)
    vm_obj['vdc_name'] = vdc_object.name
    return jsonify(vm_obj)


@global_variable.app.route('/pvdc')
def pvdc_summary():
    return render_template('pvdc.html')


@global_variable.app.route('/contacts')
def contacts():
    ordered_dict_jsonified = OrderedDict(sorted(global_variable.jsonified_data.items(), key=lambda x: x, reverse=True))
    return render_template('contacts.html', data=ordered_dict_jsonified)


@global_variable.app.route('/trigger_run')
def trigger_call():
    global_variable.run_trigger.set()
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@global_variable.app.route('/freeip')
def freeip():
    return render_template('freeip.html', data=global_variable.free_ips)


@global_variable.app.route('/freeipsearch')
def freeipsearch():
    return render_template('freeipsearch.html', data=global_variable.free_ips)


@global_variable.app.route('/manageorg', methods=['GET'])
def manageorg():
    return render_template('manageorg.html')


@global_variable.app.route('/update_vdc', methods=['POST'])
def update_vdc():
    headers = global_variable.vcs.get_vcloud_headers()

    ghz_amount = request.form['ghzAmount']
    ram_amount = request.form['ramAmount']
    vdc_name = request.form['vdcId']

    ovdc_href = global_variable.vcs.get_ovdc(name=vdc_name)[0].href
    ovdc_response = requests.get(url=ovdc_href, headers=headers, verify=global_variable.vcs.verify)
    ovdc_object = ElementTree.fromstring(ovdc_response.content)
    ovdc_object.find(
        '{http://www.vmware.com/vcloud/v1.5}ComputeCapacity').find(
        '{http://www.vmware.com/vcloud/v1.5}Cpu').find(
        '{http://www.vmware.com/vcloud/v1.5}Limit'
    ).text = str(int(ghz_amount) * 1000)
    ovdc_object.find(
        '{http://www.vmware.com/vcloud/v1.5}ComputeCapacity').find(
        '{http://www.vmware.com/vcloud/v1.5}Cpu').find(
        '{http://www.vmware.com/vcloud/v1.5}Allocated'
    ).text = str(int(ghz_amount) * 1000)
    ovdc_object.find(
        '{http://www.vmware.com/vcloud/v1.5}ComputeCapacity').find(
        '{http://www.vmware.com/vcloud/v1.5}Memory').find(
        '{http://www.vmware.com/vcloud/v1.5}Limit'
    ).text = str(int(ram_amount) * 1024)
    ovdc_object.find(
        '{http://www.vmware.com/vcloud/v1.5}ComputeCapacity').find(
        '{http://www.vmware.com/vcloud/v1.5}Memory').find(
        '{http://www.vmware.com/vcloud/v1.5}Allocated'
    ).text = str(int(ram_amount) * 1024)
    ovdc_final_xml = ElementTree.tostring(ovdc_object)

    headers['Content-Type'] = 'application/vnd.vmware.admin.vdc+xml'
    update_response = requests.put(url=ovdc_href, headers=headers, data=ovdc_final_xml,
                                   verify=global_variable.vcs.verify)
    if update_response.status_code == requests.codes.accepted:
        global_variable.run_trigger.set()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}, 200, {'ContentType': 'application/json'})


@global_variable.app.route('/add_storage_to_ovdc', methods=['POST'])
def add_storage_to_ovdc():
    from vcloudlib.helper import Http
    headers = global_variable.vcs.get_vcloud_headers()

    storage_name = request.form['storageName']
    storage_href = request.form['storageHref']
    limit = str(int(request.form['storageLimit']) * 1024)
    vdc_name = request.form['vdcId']
    vdc_href = global_variable.vcs.get_ovdc(name=vdc_name)[0].href
    vdc_sps = ElementTree.fromstring(
        Http.get(vdc_href, headers=headers).content
    ).findall('{http://www.vmware.com/vcloud/v1.5}VdcStorageProfiles')[0]

    if storage_name in [x.attrib['name'] for x in vdc_sps.getchildren()]:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

    add_sp_to_vdc = UpdateVdcStorageProfiles()
    add_sp_to_vdc.add_storage_profile(limit=limit, pvdcsp_href=storage_href)

    url = '{}/vdcStorageProfiles'.format(vdc_href)
    headers['Content-Type'] = 'application/vnd.vmware.admin.updateVdcStorageProfiles+xml'

    add_response = Http.post(url, data=add_sp_to_vdc.get_xml(), headers=headers)
    if add_response.status_code == requests.codes.accepted:
        global_variable.run_trigger.set()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}


@global_variable.app.route('/update_storage', methods=['POST'])
def update_storage():
    from vcloudlib.helper import Http
    headers = global_variable.vcs.get_vcloud_headers()

    gb_amount = request.form['gbAmount']
    storage_name = request.form['storageName']
    vdc_name = request.form['vdcId']
    ovdc_href = global_variable.vcs.get_ovdc(name=vdc_name)[0].href

    http = Http()
    ovdc_response = http.get(ovdc_href, headers=headers)
    ovdc_xml = ElementTree.fromstring(ovdc_response.content)
    storage_profiles = ovdc_xml.findall('{http://www.vmware.com/vcloud/v1.5}VdcStorageProfiles')
    storage_profile_href = filter(
        lambda x: x.attrib['name'] == storage_name,
        storage_profiles[0].findall('{http://www.vmware.com/vcloud/v1.5}VdcStorageProfile')
    )[0].attrib['href']
    storage_profile_xml = ElementTree.fromstring(
        Http.get(
            storage_profile_href, headers=headers
        ).content
    )
    storage_profile_xml.find('{http://www.vmware.com/vcloud/v1.5}Limit').text = str(int(gb_amount) * 1024)
    headers['Content-Type'] = 'application/vnd.vmware.admin.vdcStorageProfile+xml'
    update_response = http.put(storage_profile_href, data=ElementTree.tostring(storage_profile_xml), headers=headers)
    if update_response.status_code == requests.codes.ok:
        global_variable.run_trigger.set()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}, 200, {'ContentType': 'application/json'})


@global_variable.app.route('/update_metadata', methods=['POST'])
def update_metadata():
    data = request.form
    metadata_object = [
        {'key': 'OrderNumber', 'value': data['OrderNumber']},
        {'key': 'CustomerPhone', 'value': data['CustomerPhone']},
        {'key': 'CustomerEmail', 'value': data['CustomerEmail']},
        {'key': 'LicSqlStdAmount', 'value': data['LicSqlStdAmount']},
        {'key': 'LicSqlEntAmount', 'value': data['LicSqlEntAmount']},
        {'key': 'LicWinAmount', 'value': data['LicWinAmount']},
        {'key': 'ExpirationData', 'value': data['ExpirationData']}
    ]
    if not set_org_metadata(global_variable.vcs, data['OrgName'], metadata=metadata_object):
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@global_variable.app.route('/addorg', methods=['POST'])
def addorg():
    from vcloudlib.helper import Http
    org_data = request.form
    admin_org_scheme = AdminOrg(name=org_data['orgName'])
    admin_org_scheme.set_description(org_data['orgDescription'])
    admin_org_scheme.set_full_name(org_data['orgFullName'])
    global_variable.vcs.login()
    # noinspection PyBroadException
    try:
        # initializing headers
        headers = global_variable.vcs.get_vcloud_headers()
        headers['Content-Type'] = 'application/vnd.vmware.admin.organization+xml'

        # creating organization
        data = admin_org_scheme.get_xml()
        response = requests.post('{}/api/admin/orgs'.format(global_variable.vcs.host),
                                 data=data,
                                 headers=headers,
                                 verify=global_variable.vcs.verify)
        global_variable.app.logger.debug(response.content)
        org_xml_scheme = organizationType.parseString(response.content)
        if response.status_code != requests.codes.created:
            global_variable.app.logger.error(response.content)
            return 'Failed to Create Organization.'

        # set metadata
        metadata_object = [
            {'key': 'OrderNumber', 'value': org_data['orgOrderNumber']},
            {'key': 'CustomerPhone', 'value': org_data['customerPhone']},
            {'key': 'CustomerEmail', 'value': org_data['customerEmail']},
            {'key': 'LicSqlStdAmount', 'value': org_data['LicSqlStdAmount']},
            {'key': 'LicSqlEntAmount', 'value': org_data['LicSqlEntAmount']},
            {'key': 'LicWinAmount', 'value': org_data['LicWinAmount']},
            {'key': 'ExpirationData', 'value': org_data['ExpirationDate']}
        ]
        if not set_org_metadata(global_variable.vcs, org_data['orgName'], metadata=metadata_object):
            return 'Failed to set metadata information.'

        # enable Linux catalog to Org
        linux_catalog = global_variable.vcs.get_catalog(name='Linux')[0]
        control_access = ControlAccessParams(is_shared_to_everyone='true')
        headers = global_variable.vcs.get_vcloud_headers()
        headers['Content-Type'] = 'application/vnd.vmware.vcloud.controlAccess+xml'
        update_link = '{}/catalog/{}/action/controlAccess'.format(linux_catalog.org,
                                                                  linux_catalog.href.split('/')[-1])
        catalog_update_xml = control_access.get_xml()
        update_response = Http.post(update_link, data=catalog_update_xml, headers=headers)
        if update_response.status_code != requests.codes.ok:
            return 'Failed to add Linux Catalog'

        # create Org User
        passwd = create_org_user(vcloud_session=global_variable.vcs,
                                 username=org_data['orgUsername'],
                                 full_name='Organization Administrator',
                                 org_name=org_data['orgName'],
                                 password=org_data['orgAdminPassword'])
        if passwd['status'] is not 'success':
            global_variable.app.logger.error(passwd['content'])
            return 'Failed to Create User. Aborting Process.'

        # create VDC
        net_pool = global_variable.vcs.get_networks_pool()[0].href
        chosen_pvdc = global_variable.vcs.get_pvdc_by_name(org_data['pvdc'])
        vdc_creator = CreateVdcParams(name='vdc1-{}'.format(org_data['orgName']),
                                      vcs=global_variable.vcs, choosen_pvdc=chosen_pvdc)
        vdc_creator.parse_dict(org_data, chosen_pvdc, network_pool_href=net_pool)
        link = filter(
            lambda x: x.type_ == 'application/vnd.vmware.admin.createVdcParams+xml', org_xml_scheme.Link
        )[0].href
        headers['Content-Type'] = 'application/vnd.vmware.admin.createVdcParams+xml'
        vdc_creator.networkQuota.text = org_data['netQuota']
        org_vdc_creation_scheme = vdc_creator.get_xml()
        global_variable.app.logger.debug(org_vdc_creation_scheme)
        org_vdc_creation_response = requests.post(link,
                                                  data=org_vdc_creation_scheme,
                                                  headers=headers,
                                                  verify=global_variable.vcs.verify)
        global_variable.app.logger.error(org_vdc_creation_response.content)
        org_vdc_xml_data = ElementTree.fromstring(org_vdc_creation_response.content)

        # check if I have to create a vShield Edge
        if 'isGatewayEdgePresent' not in org_data.keys():
            global_variable.run_trigger.set()
            return 'Organization Created Successfully. Admin Password: {}'.format(passwd)

        # create vShield Edge
        _tag = '{http://www.vmware.com/vcloud/v1.5}Link'
        _type = 'application/vnd.vmware.admin.edgeGateway+xml'
        edge_gateway_link = filter(
            lambda x: x.tag == _tag and x.attrib['type'] == _type, org_vdc_xml_data.getchildren()
        )[0].attrib['href']
        vshield_edge_xml = EdgeGateway(name='gw1-{}'.format(org_data['orgName']),
                                       gw_type=org_data['gatewayEdgeType'].lower())
        less_used_network = get_less_used_network(int(org_data['numberOfIp']), global_variable, Config)
        if less_used_network is None:
            return 'Cannot find a network with enough IP Available.'
        vshield_edge_xml.add_gateway_interface(name='uplink1',
                                               network_href=less_used_network['object'].href,
                                               gateway=less_used_network['object'].gateway,
                                               netmask=less_used_network['object'].netmask,
                                               iplist=less_used_network['iplist'])
        headers['Content-Type'] = 'application/vnd.vmware.admin.edgeGateway+xml'
        vshield_edge_creation_response = requests.post(edge_gateway_link,
                                                       data=vshield_edge_xml.get_xml(),
                                                       headers=headers,
                                                       verify=global_variable.vcs.verify)
        if vshield_edge_creation_response.status_code != requests.codes.created:
            return 'Failed to Create Organization'
        global_variable.app.logger.debug(vshield_edge_creation_response.content)

        vshield_edge_xml = ElementTree.fromstring(vshield_edge_creation_response.content)
        task = taskType.parseString(ElementTree.tostring(
            filter(lambda x: x.tag == '{http://www.vmware.com/vcloud/v1.5}Tasks', vshield_edge_xml)[0]
        )).Task[0]
        wait_for_task(task, global_variable)
        # to be sure we wait another 10 seconds, the vse could still be busy and return an error
        time.sleep(10)

        # set vshield firewall rules
        _rel = 'edgeGateway:configureServices'
        _type = 'application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml'
        vse_service_conf_href = filter(lambda x: x.attrib['rel'] == _rel and x.attrib['type'] == _type,
                                       vshield_edge_xml.findall(
                                           '{http://www.vmware.com/vcloud/v1.5}Link')
                                       )[0].attrib['href']
        headers['Content-Type'] = 'application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml'
        edge_service_configuration = EdgeGatewayServiceConfiguration()
        edge_service_configuration.add_firewall_rule()
        edge_service_configuration.add_source_nat_rule(network_href=less_used_network['object'].href,
                                                       translated_ip=less_used_network['iplist'][0])
        edge_service_configuration_xml = edge_service_configuration.get_xml()
        egsc_conf_response = requests.post(url=vse_service_conf_href,
                                           data=edge_service_configuration_xml,
                                           headers=headers,
                                           verify=global_variable.vcs.verify)
        if egsc_conf_response.status_code != requests.codes.accepted:
            return 'Failed to set firewall setup'

        # create Org Network
        headers['Content-Type'] = 'application/vnd.vmware.vcloud.orgVdcNetwork+xml'
        ovdc_href = global_variable.vcs.get_ovdc(name='vdc1-{}'.format(org_data['orgName']))[0].href
        if ovdc_href is None:
            return 'Cannot find vdc with name {} during the OrgNet creation.'.format(
                name='vdc1-{}'.format(org_data['orgName'])
            )

        org_vdc_get_response = requests.get(ovdc_href, headers=headers, verify=global_variable.vcs.verify)
        if org_vdc_creation_response.status_code != requests.codes.created:
            return 'Failed to retrieve Org VDC scheme.'

        org_vdc_xml = ElementTree.fromstring(org_vdc_get_response.content)
        links = filter(lambda x: x.tag == '{http://www.vmware.com/vcloud/v1.5}Link', org_vdc_xml.getchildren())
        org_vdc_network_link = filter(lambda x:
                                      x.attrib['rel'] == 'add' and
                                      x.attrib['type'] == 'application/vnd.vmware.vcloud.orgVdcNetwork+xml',
                                      links)[0].attrib['href']
        org_vdc_network_creation_schema = OrgVdcNetwork(name='net1-{}'.format(org_data['orgName']),
                                                        vshield_edge_href=vshield_edge_xml.attrib['href'])
        org_vdc_network_creation_schema.add_ip_socpe(gateway='192.168.1.1',
                                                     netmask='255.255.255.0',
                                                     dns='192.168.1.1',
                                                     dns_suffix='',
                                                     start_address='192.168.1.10',
                                                     end_address='192.168.1.254')
        for count in xrange(0, GATEWAY_TRY_COUNT):
            org_vdc_network_creation_response = requests.post(org_vdc_network_link,
                                                              data=org_vdc_network_creation_schema.get_xml(),
                                                              headers=headers,
                                                              verify=global_variable.vcs.verify)
            if org_vdc_network_creation_response.status_code != requests.codes.created:
                error = taskType.parseString(org_vdc_network_creation_response.content, True)
                if BUSY_MESSAGE in error.message:
                    time.sleep(5)
            else:
                global_variable.run_trigger.set()
                return 'Organization Created Successfully. Admin Password: {}'.format(passwd)
        return 'Failed to create Network organization. Proceed manually. Admin password: {}'.format(passwd)
    except Exception:
        global_variable.app.logger.exception("OMG")
    return 'Failed to Create Organization'


@global_variable.app.route('/test')
def test():
    pass


# noinspection PyPep8Naming
@global_variable.app.route('/getvdcs')
def getvdcs():
    pvdcs = global_variable.vcs.get_pvdc()
    # choosing the one with more available resources
    pvdcs = sorted(pvdcs, key=lambda p: p.cpuLimitMhz - p.cpuAllocationMhz, reverse=True)
    returnDict = OrderedDict()
    for pvdc in pvdcs:
        returnDict[pvdc.name] = pvdc.cpuLimitMhz - pvdc.cpuAllocationMhz
    return json.dumps(returnDict)


@global_variable.app.route('/get_vdcs_full')
def get_vdcs_full():
    from flask import jsonify

    pvdcs = global_variable.vcs.get_pvdc()
    data = {}

    for record in pvdcs:
        data[record.name] = {}
        data[record.name]['cpu_limit'] = record.cpuLimitMhz / 1000
        data[record.name]['cpu_used'] = record.cpuUsedMhz / 1000
        data[record.name]['cpu_allocation'] = record.cpuAllocationMhz / 1000
        data[record.name]['memory_limit'] = record.memoryLimitMB / 1024
        data[record.name]['memory_used'] = record.memoryUsedMB / 1024
        data[record.name]['memory_allocation'] = record.memoryAllocationMB / 1024
        data[record.name]['storage_limit'] = record.storageLimitMB / 1024
        data[record.name]['storage_used'] = record.storageUsedMB / 1024
        data[record.name]['storage_allocation'] = record.storageAllocationMB / 1024
        data[record.name]['vdcs_number'] = record.numberOfVdcs / 1024
        data[record.name]['datastore_number'] = record.numberOfDatastores / 1024
        data[record.name]['href'] = record.href

    return jsonify(data)


@global_variable.app.route('/get_sp')
def get_sp():
    from vcloudlib.helper import Http
    headers = global_variable.vcs.get_vcloud_headers()
    return_dict = {}

    query = '{}/api/query?type=providerVdcStorageProfile'.format(global_variable.vcs.host)
    query_response = Http.get(query, headers=headers)
    if query_response.status_code == requests.codes.ok:
        query_result_records = queryRecordViewType.parseString(query_response.content, True)
        profiles = query_result_records.get_Record()
        for sp in profiles:
            return_dict[sp.name] = sp.href
    return json.dumps(return_dict)


@global_variable.app.route('/give_me_ip', methods=['POST'])
def give_me_ip():
    num_ip = int(request.form['numip'])
    free_ip_list = []
    for ip_class in global_variable.free_ips.keys():
        if len(global_variable.free_ips[ip_class]) > num_ip:
            while len(free_ip_list) < num_ip:
                free_ip_list.append([global_variable.free_ips[ip_class][len(free_ip_list)].__str__()])
        break
    print(json.dumps({'data': free_ip_list}))
    return json.dumps(free_ip_list)
