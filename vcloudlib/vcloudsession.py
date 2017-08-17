import base64
import xml.etree

import requests

from vcloudlib.gateway import Gateway
from vcloudlib.schema.vcd.v1_5.schemas.vcloud import networkType
from vcloudlib.schema.vcd.v1_5.schemas.vcloud import organizationType
from vcloudlib.schema.vcd.v1_5.schemas.vcloud import queryRecordViewType
from vcloudlib.schema.vcd.v1_5.schemas.vcloud import sessionType
from vcloudlib.schema.vcd.v1_5.schemas.vcloud import vdcType

__author__ = 'alessio.rocchi'


class VCS(object):
    def __init__(self, host, username, password, version='5.5', verify=False, org='System'):
        if not (host.startswith('https://') or host.startswith('http://')):
            self.host = 'https://{host}'.format(host=host)
        else:
            self.host = host
        self.url = self.host + '/api/sessions'
        self.username = username
        self.password = password
        self.version = version
        self.verify = verify
        self.token = None
        self.org = org
        self.org_list_url = None
        self.orgList = []
        self.session = None

    def login(self):
        encode = "Basic " + base64.standard_b64encode(self.username + "@" + self.org + ":" + self.password)
        headers = {"Authorization": encode.rstrip(), "Accept": "application/*+xml;version=" + self.version}
        response = requests.post(self.url, headers=headers, verify=self.verify)
        if response.status_code == requests.codes.ok:
            self.token = response.headers["x-vcloud-authorization"]
            self.session = sessionType.parseString(response.content, True)
            return True
        else:
            return False

    def get_vcloud_headers(self):
        headers = {"x-vcloud-authorization": self.token, "Accept": "application/*+xml;version=" + self.version}
        return headers

    def get_orgs(self):
        headers = self.get_vcloud_headers()
        response = requests.get('{}/api/query?type=organization&pageSize=128'.format(self.host),
                                headers=self.get_vcloud_headers(),
                                verify=self.verify)
        from vcloudlib.helper import Http
        query_result_record = queryRecordViewType.parseString(response.content, True)
        records = []
        if query_result_record.total > 128:
            records = query_result_record.get_Record()
            # start to iterate from page 2 assuming that the first one is already processed.
            for page in xrange(2, ((int(query_result_record.total) / 128) + 2)):
                response = Http.get('{}/api/query?type=organization&page={}&pageSize=128'.format(self.host, page),
                                    headers=self.get_vcloud_headers())
                map(lambda x: records.append(x), queryRecordViewType.parseString(response.content, True).get_Record())
        else:
            records = query_result_record.get_Record()
        orgs = []
        for elem in records:
            org = organizationType.parseString(Http.get(url=elem.href, headers=headers).content, True)
            orgs.append(org)
        return orgs

    def get_metadata(self, org_href):
        response = requests.get('{}/metadata'.format(org_href.replace('api/', 'api/admin/')),
                                headers=self.get_vcloud_headers(),
                                verify=self.verify)
        metadatas = []
        if response.status_code == requests.codes.ok:
            metadata_type = xml.etree.ElementTree.fromstring(response.content)
            entries = metadata_type.findall('{http://www.vmware.com/vcloud/v1.5}MetadataEntry')
            for metadata in entries:
                key = metadata.find('{http://www.vmware.com/vcloud/v1.5}Key').text
                value = metadata.find(
                    '{http://www.vmware.com/vcloud/v1.5}TypedValue'
                ).find(
                    '{http://www.vmware.com/vcloud/v1.5}Value'
                ).text
                metadatas.append({
                    key: value
                })
        return metadatas

    def get_storage_profile_limit(self, vdc_storage_profiles_href):
        response = requests.get(vdc_storage_profiles_href, headers=self.get_vcloud_headers(), verify=self.verify)
        x_sp = xml.etree.ElementTree.fromstring(response.content)
        limit = x_sp.find('{http://www.vmware.com/vcloud/v1.5}Limit').text
        return int(limit) / 1024

    def get_vdc(self, org):
        refs = filter(lambda ref: ref.type_ == 'application/vnd.vmware.vcloud.vdc+xml', org.Link)
        vdcs = []
        for vdc in refs:
            try:
                response = requests.get(vdc.href, headers=self.get_vcloud_headers(), verify=self.verify)
            except requests.ConnectionError:
                raise requests.ConnectionError()
            if response.status_code == requests.codes.ok:
                parsed_vdc = vdcType.parseString(response.content, True)
                vdcs.append(parsed_vdc)
        return vdcs

    def get_gateway(self, name=None):
        gateways = []
        if name is not None:
            query = '{}/api/query?type=edgeGateway&filter=(name=={})'.format(self.host, name)
        else:
            query = '{}/api/query?type=edgeGateway'.format(self.host)
        response = requests.get(query, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            for edge_gateway_record in query_result_records.get_Record():
                response = requests.get(edge_gateway_record.get_href(),
                                        headers=self.get_vcloud_headers(),
                                        verify=self.verify)
                if response.status_code == requests.codes.ok:
                    gateway = Gateway(networkType.parseString(response.content, True),
                                      headers=self.get_vcloud_headers(),
                                      verify=self.verify)
                    gateways.append(gateway)
            return gateways
        return None

    def get_gateways(self, vdc):
        gateways = []
        if not vdc:
            return gateways
        link = filter(lambda link_: link_.get_rel() == "edgeGateways", vdc.get_Link())
        response = requests.get(link[0].get_href(), headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                for edgeGatewayRecord in query_result_records.get_Record():
                    response = requests.get(edgeGatewayRecord.get_href(), headers=self.get_vcloud_headers(),
                                            verify=self.verify)
                    if response.status_code == requests.codes.ok:
                        try:
                            gateway = Gateway(
                                networkType.parseString(response.content, True),
                                headers=self.get_vcloud_headers(),
                                verify=self.verify)
                            gateways.append(gateway)
                        except Exception as e:
                            print(e)
        return gateways

    def get_pvdc(self):
        response = requests.get('{}/api/query?type=providerVdc'.format(self.host), headers=self.get_vcloud_headers(),
                                verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get_pvdc_by_name(self, name):
        response = requests.get('{}/api/query?type=providerVdc&filter=(name=={})'.format(self.host, name),
                                headers=self.get_vcloud_headers(),
                                verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record[0]
        return None

    def get_pvdc_available_storage_profiles(self, pvdc):
        # if not isinstance(pvdc, queryRecordViewType):
        # raise TypeError('Excepted: queryRecordViewType, received: {}'.format(pvdc.__class__.__name__))
        response = requests.get(pvdc.href, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            provider_vdc = xml.etree.ElementTree.fromstring(response.content)
            storage_profiles = provider_vdc.find('{http://www.vmware.com/vcloud/v1.5}StorageProfiles').getchildren()
            return storage_profiles
        return None

    def get_network(self):
        response = requests.get('{}/api/query?type=externalNetwork'.format(self.host),
                                headers=self.get_vcloud_headers(),
                                verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get_ovdc(self, name=None):
        if name is not None:
            query = '{}/api/query?type=adminOrgVdc&filter=(name=={})'.format(self.host, name)
        else:
            query = '{}/api/query?type=adminOrgVdc'.format(self.host)
        response = requests.get(query, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get_networks_pool(self):
        query = '{}/api/query?type=networkPool'.format(self.host)
        response = requests.get(query, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get_role(self, name=None):
        if name is not None:
            query = '{}/api/query?type=role&filter=(name=={})'.format(self.host, name)
        else:
            query = '{}/api/query?type=role'.format(self.host)
        response = requests.get(query, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get_org(self, name=None):
        if name is not None:
            query = '{}/api/query?type=organization&filter=(name=={})'.format(self.host, name)
        else:
            query = '{}/api/query?type=organization'.format(self.host)
        response = requests.get(query, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get_catalog(self, name=None):
        if name is not None:
            query = '{}/api/query?type=adminCatalog&filter=(name=={})'.format(self.host, name)
        else:
            query = '{}/api/query?type=adminCatalog'.format(self.host)
        response = requests.get(query, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get_vm_by_name(self, name=None):
        name = name.replace(" ", "%20")
        if name is not None:
            query = '{}/api/query?type=adminVM&filter=(name=={})'.format(self.host, name)
        else:
            query = '{}/api/query?type=adminVM'.format(self.host)
        response = requests.get(query, headers=self.get_vcloud_headers(), verify=self.verify)
        if response.status_code == requests.codes.ok:
            query_result_records = queryRecordViewType.parseString(response.content, True)
            if query_result_records.get_Record():
                return query_result_records.Record
        return None

    def get(self, url, content_type=None):
        headers = self.get_vcloud_headers()
        if content_type is not None:
            headers['Content-Type'] = content_type
        response = requests.get(url=url,
                                headers=headers,
                                verify=self.verify)
        return response.content
