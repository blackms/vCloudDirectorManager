__author__ = 'alessio.rocchi'

from xml.etree import ElementTree


class ModelBase(object):
    def __init__(self):
        self.xml = ''

    def get_xml(self):
        return '<?xml version="1.0" encoding="UTF-8"?>{}'.format(ElementTree.tostring(self.xml))

    def __str__(self):
        return ElementTree.tostring(self.xml)


class AdminOrg(ModelBase):
    def __init__(self, name):
        super(AdminOrg, self).__init__()
        self.name = name
        self.xml = ElementTree.Element("AdminOrg", {'xmlns': "http://www.vmware.com/vcloud/v1.5",
                                                    'name': self.name,
                                                    'type': 'application/vnd.vmware.admin.organization+xml'})
        self.description = ElementTree.SubElement(self.xml, 'Description')
        self.fullName = ElementTree.SubElement(self.xml, 'FullName')
        self.isEnabled = ElementTree.SubElement(self.xml, 'IsEnabled').text = 'true'
        self.settings = ElementTree.SubElement(self.xml, 'Settings')
        self.orgGeneralSettings = ElementTree.SubElement(self.settings, 'OrgGeneralSettings')
        self.vAppLeaseSettings = ElementTree.SubElement(self.settings, 'VAppLeaseSettings')
        ElementTree.SubElement(self.vAppLeaseSettings, 'DeleteOnStorageLeaseExpiration').text = 'false'
        ElementTree.SubElement(self.vAppLeaseSettings, 'DeploymentLeaseSeconds').text = '0'
        ElementTree.SubElement(self.vAppLeaseSettings, 'StorageLeaseSeconds').text = '0'
        self.vAppTemplateLeaseSettings = ElementTree.SubElement(self.settings, 'VAppTemplateLeaseSettings')
        ElementTree.SubElement(self.vAppTemplateLeaseSettings, 'DeleteOnStorageLeaseExpiration').text = 'false'
        ElementTree.SubElement(self.vAppTemplateLeaseSettings, 'StorageLeaseSeconds').text = '0'
        self.orgLdapSettings = ElementTree.SubElement(self.settings, 'OrgLdapSettings')
        self.orgEmailSettings = ElementTree.SubElement(self.settings, 'OrgEmailSettings')
        self.orgPasswordPolicySettings = ElementTree.SubElement(self.settings, 'OrgPasswordPolicySettings')
        ElementTree.SubElement(self.orgPasswordPolicySettings, 'AccountLockoutEnabled').text = 'false'
        ElementTree.SubElement(self.orgPasswordPolicySettings, 'InvalidLoginsBeforeLockout').text = '15'
        ElementTree.SubElement(self.orgPasswordPolicySettings, 'AccountLockoutIntervalMinutes').text = '5'
        self.orgOperationLimitsSettings = ElementTree.SubElement(self.settings, 'OrgOperationLimitsSettings')
        ElementTree.SubElement(self.orgOperationLimitsSettings, 'ConsolesPerVmLimit').text = '5'
        ElementTree.SubElement(self.orgOperationLimitsSettings, 'OperationsPerUser').text = '10'
        ElementTree.SubElement(self.orgOperationLimitsSettings, 'OperationsPerOrg').text = '10'
        ElementTree.SubElement(self.orgGeneralSettings, 'CanPublishCatalogs').text = 'true'
        ElementTree.SubElement(self.orgGeneralSettings, 'DeployedVMQuota').text = '0'
        ElementTree.SubElement(self.orgGeneralSettings, 'StoredVmQuota').text = '0'
        ElementTree.SubElement(self.orgGeneralSettings, 'UseServerBootSequence').text = 'false'
        ElementTree.SubElement(self.orgGeneralSettings, 'DelayAfterPowerOnSeconds').text = '0'
        ElementTree.SubElement(self.orgLdapSettings, 'OrgLdapMode').text = 'SYSTEM'
        ElementTree.SubElement(self.orgLdapSettings, 'CustomUsersOu')
        ElementTree.SubElement(self.orgEmailSettings, 'IsDefaultSmtpServer').text = 'true'
        ElementTree.SubElement(self.orgEmailSettings, 'IsDefaultOrgEmail').text = 'true'
        ElementTree.SubElement(self.orgEmailSettings, 'FromEmailAddress')
        ElementTree.SubElement(self.orgEmailSettings, 'DefaultSubjectPrefix')
        ElementTree.SubElement(self.orgEmailSettings, 'IsAlertEmailToAllAdmins').text = 'true'

    def set_full_name(self, full_name):
        self.fullName.text = full_name

    def set_description(self, description):
        self.description.text = description

    def add_sub_element(self, parent, name, text=None):
        """
        Create a SubElement from a given parent object (or name).
        :param parent: string
        :param name: string
        :return: bool
        """
        starting_element = self.xml.find('.//{}'.format(parent))
        if starting_element is not None:
            _subEl = ElementTree.SubElement(starting_element, name)
            if text is not None:
                _subEl.text = text
            return True
        return False


class OrgVdcNetwork(ModelBase):
    def __init__(self, name, vshield_edge_href):
        super(OrgVdcNetwork, self).__init__()
        self.name = name

        self.xml = ElementTree.Element("OrgVdcNetwork", {'xmlns': 'http://www.vmware.com/vcloud/v1.5',
                                                         'name': self.name})
        self.description = ElementTree.SubElement(self.xml,
                                                  'Description').text = 'First Local Network. Routed by a vShield Edge'
        self.configuration = ElementTree.SubElement(self.xml, 'Configuration')
        self.ipScopes = ElementTree.SubElement(self.configuration, 'IpScopes')
        ElementTree.SubElement(self.configuration, 'FenceMode').text = 'natRouted'
        ElementTree.SubElement(self.xml, 'EdgeGateway', {'href': vshield_edge_href})
        ElementTree.SubElement(self.xml, 'IsShared').text = 'false'

    def add_ip_socpe(self, gateway, netmask, dns, dns_suffix, start_address, end_address):
        ip_scope = ElementTree.SubElement(self.ipScopes, 'IpScope')
        ElementTree.SubElement(ip_scope, 'IsInherited').text = 'false'
        ElementTree.SubElement(ip_scope, 'Gateway').text = gateway
        ElementTree.SubElement(ip_scope, 'Netmask').text = netmask
        ElementTree.SubElement(ip_scope, 'Dns1').text = dns
        ElementTree.SubElement(ip_scope, 'DnsSuffix').text = dns_suffix
        ip_ranges = ElementTree.SubElement(ip_scope, 'IpRanges')
        ip_range = ElementTree.SubElement(ip_ranges, 'IpRange')
        ElementTree.SubElement(ip_range, 'StartAddress').text = start_address
        ElementTree.SubElement(ip_range, 'EndAddress').text = end_address

    def get_xml(self):
        return '<?xml version="1.0" encoding="UTF-8"?>{}'.format(ElementTree.tostring(self.xml))

    def __str__(self):
        return ElementTree.tostring(self.xml)


class EdgeGateway(ModelBase):
    def __init__(self, name, gw_type):
        super(EdgeGateway, self).__init__()
        self.name = name

        self.xml = ElementTree.Element('EdgeGateway', {'xmlns': 'http://www.vmware.com/vcloud/v1.5',
                                                       'name': self.name})
        ElementTree.SubElement(self.xml, 'Description').text = 'Organization vShiled Edge'
        self.configuration = ElementTree.SubElement(self.xml, 'Configuration')
        ElementTree.SubElement(self.configuration, 'GatewayBackingConfig').text = gw_type
        self.gatewayInterfaces = ElementTree.SubElement(self.configuration, 'GatewayInterfaces')
        ElementTree.SubElement(self.configuration, 'HaEnabled').text = 'false'
        ElementTree.SubElement(self.configuration, 'UseDefaultRouteForDnsRelay').text = 'false'

    def add_gateway_interface(self, name, network_href, gateway, netmask, iplist):
        gateway_interface = ElementTree.SubElement(self.gatewayInterfaces, 'GatewayInterface')
        ElementTree.SubElement(gateway_interface, 'Name').text = name
        ElementTree.SubElement(gateway_interface, 'Network', {'href': network_href})
        ElementTree.SubElement(gateway_interface, 'InterfaceType').text = 'uplink'
        subnet_participation = ElementTree.SubElement(gateway_interface, 'SubnetParticipation')
        ElementTree.SubElement(subnet_participation, 'Gateway').text = gateway
        ElementTree.SubElement(subnet_participation, 'Netmask').text = netmask
        ip_ranges = ElementTree.SubElement(subnet_participation, 'IpRanges')
        for ip in iplist:
            ip_range = ElementTree.SubElement(ip_ranges, 'IpRange')
            ElementTree.SubElement(ip_range, 'StartAddress').text = str(ip)
            ElementTree.SubElement(ip_range, 'EndAddress').text = str(ip)
        ElementTree.SubElement(gateway_interface, 'UseForDefaultRoute').text = 'true'


class EdgeGatewayServiceConfiguration(ModelBase):
    def __init__(self):
        super(EdgeGatewayServiceConfiguration, self).__init__()
        self.xml = ElementTree.Element('EdgeGatewayServiceConfiguration',
                                       {'xmlns': 'http://www.vmware.com/vcloud/v1.5'})
        self.firewallService = ElementTree.SubElement(self.xml, 'FirewallService')
        self.natService = ElementTree.SubElement(self.xml, 'NatService')
        ElementTree.SubElement(self.natService, 'IsEnabled').text = 'true'
        ElementTree.SubElement(self.firewallService, 'IsEnabled').text = 'true'
        ElementTree.SubElement(self.firewallService, 'DefaultAction').text = 'drop'
        ElementTree.SubElement(self.firewallService, 'LogDefaultAction').text = 'false'

    def add_firewall_rule(self,
                          description='Allow outgoing NAT rules',
                          policy='allow',
                          protocols=None,
                          dest_port_range='any',
                          dest_ip='External',
                          source_port_range='any',
                          source_ip='Internal',
                          logging='false'):
        firewall_rule = ElementTree.SubElement(self.firewallService, 'FirewallRule')
        ElementTree.SubElement(firewall_rule, 'IsEnabled').text = 'true'
        ElementTree.SubElement(firewall_rule, 'Description').text = description
        ElementTree.SubElement(firewall_rule, 'Policy').text = policy
        if protocols is None:
            protos = ElementTree.SubElement(firewall_rule, 'Protocols')
            ElementTree.SubElement(protos, 'Any').text = 'true'
        else:
            firewall_rule.append(protocols)
        ElementTree.SubElement(firewall_rule, 'DestinationPortRange').text = dest_port_range
        ElementTree.SubElement(firewall_rule, 'DestinationIp').text = dest_ip
        ElementTree.SubElement(firewall_rule, 'SourcePortRange').text = source_port_range
        ElementTree.SubElement(firewall_rule, 'SourceIp').text = source_ip
        ElementTree.SubElement(firewall_rule, 'EnableLogging').text = logging

    def add_source_nat_rule(self, network_href, translated_ip, original_ip='192.168.1.0/24'):
        nat_rule = ElementTree.SubElement(self.natService, 'NatRule')
        ElementTree.SubElement(nat_rule, 'RuleType').text = 'SNAT'
        ElementTree.SubElement(nat_rule, 'IsEnabled').text = 'true'
        gateway_nat_rule = ElementTree.SubElement(nat_rule, 'GatewayNatRule')
        ElementTree.SubElement(gateway_nat_rule, 'Interface', {'href': network_href})
        ElementTree.SubElement(gateway_nat_rule, 'OriginalIp').text = str(original_ip)
        ElementTree.SubElement(gateway_nat_rule, 'TranslatedIp').text = str(translated_ip)
        ElementTree.SubElement(gateway_nat_rule, 'Protocol').text = 'any'


class Protocols(ModelBase):
    def __init__(self):
        super(Protocols, self).__init__()
        self.xml = ElementTree.Element('Protocols')

    def tcp(self):
        ElementTree.SubElement(self.xml, 'Tcp').text = 'true'

    def udp(self):
        ElementTree.SubElement(self.xml, 'Udp').text = 'true'


class AdminCatalog(ModelBase):
    def __init__(self, name, description, vcs):
        super(AdminCatalog, self).__init__()
        self.name = name
        self.description = description
        self.vcs = vcs
        self.content_type = 'application/vnd.vmware.admin.catalog+xml'
        self.xml = ElementTree.Element('AdminCatalog', {'xmlns': 'http://www.vmware.com/vcloud/v1.5',
                                                        'name': self.name})
        ElementTree.SubElement(self.xml, 'Description').text = self.description

    def add_catalog_to_org(self, org_name=None, org_href=None):
        if org_name is None and org_href is None:
            raise ValueError('Excepted org_name or org_href')
        if org_name is not None:
            org_href = self.vcs.get_org(name=org_name)[0].href
        org_href = '{}/catalogs'.format(org_href.replace('api/', 'api/admin/'))
        import requests
        headers = self.vcs.get_vcloud_headers()
        headers['Content-Type'] = self.content_type
        response = requests.post(url=org_href,
                                 headers=headers,
                                 data=self.get_xml(),
                                 verify=self.vcs.verify)
        if response.status_code != requests.codes.created:
            return False
        return True


class CreateVdcParams(ModelBase):
    """
    Create an XML Structure representing the request to create the OrgVDC
    the vcs object is necessary to resolve the storage types.
    """

    def __init__(self, name, vcs, choosen_pvdc):
        super(CreateVdcParams, self).__init__()
        self.name = name
        self.vcs = vcs
        self.ghzAmount = ''
        self.ramAmount = ''
        self.choosen_pvdc = choosen_pvdc

        self.xml = ElementTree.Element("CreateVdcParams", {'xmlns': "http://www.vmware.com/vcloud/v1.5",
                                                           'name': self.name})
        self.description = ElementTree.SubElement(self.xml, 'Description').text = 'Primary Org VDC'
        self.allocationModel = ElementTree.SubElement(self.xml, 'AllocationModel').text = 'AllocationPool'
        self.computeCapacity = ElementTree.SubElement(self.xml, 'ComputeCapacity')
        self.Cpu = ElementTree.SubElement(self.computeCapacity, 'Cpu')
        self.Memory = ElementTree.SubElement(self.computeCapacity, 'Memory')
        ElementTree.SubElement(self.xml, 'NicQuota').text = '0'
        self.networkQuota = ElementTree.SubElement(self.xml, 'NetworkQuota')
        self.networkQuota.text = '5'
        self.vmQuota = ElementTree.SubElement(self.xml, 'VmQuota')
        ElementTree.SubElement(self.xml, 'IsEnabled').text = 'true'

    def add_new_vdc_storage_profile(self, limit, p_vdc_sp_href, default='false'):
        current_vdc_storage_profile = ElementTree.SubElement(self.xml, 'VdcStorageProfile')
        ElementTree.SubElement(current_vdc_storage_profile, 'Enabled').text = 'true'
        ElementTree.SubElement(current_vdc_storage_profile, 'Units').text = 'MB'
        ElementTree.SubElement(current_vdc_storage_profile, 'Limit').text = str(limit)
        ElementTree.SubElement(current_vdc_storage_profile, 'Default').text = default
        ElementTree.SubElement(current_vdc_storage_profile, 'ProviderVdcStorageProfile', {'href': p_vdc_sp_href})

    def parse_dict(self, data_dict, pvdc_data, network_pool_href):
        self.ghzAmount = data_dict['ghzAmount']
        self.ramAmount = data_dict['ramAmount']
        ElementTree.SubElement(self.Cpu, 'Units').text = 'MHz'
        ElementTree.SubElement(self.Cpu, 'Allocated').text = str(int(self.ghzAmount) * 1000)
        ElementTree.SubElement(self.Cpu, 'Limit').text = str(int(self.ghzAmount) * 1000)
        ElementTree.SubElement(self.Memory, 'Units').text = 'MB'
        ElementTree.SubElement(self.Memory, 'Allocated').text = str(int(self.ramAmount) * 1024)
        ElementTree.SubElement(self.Memory, 'Limit').text = str(int(self.ramAmount) * 1024)
        self.vmQuota.text = str(int(data_dict['ghzAmount']))

        available_vdc_storage_profiles = self.vcs.get_pvdc_available_storage_profiles(pvdc_data)
        # start processing replicated storage
        default = 'true'
        if int(data_dict['rGold']) > 0:
            limit = (int(data_dict['rGold']) + int(data_dict['ramAmount'])) * 1024
            p_vdc_sp_href = filter(lambda x: x.attrib['name'] == 'Gold Mirrored Storage',
                                   available_vdc_storage_profiles
                                   )[0]
            self.add_new_vdc_storage_profile(limit=limit, p_vdc_sp_href=p_vdc_sp_href.attrib['href'], default=default)
            default = 'false'

        if int(data_dict['nrGold']) > 0:
            limit = (int(data_dict['nrGold']) + int(data_dict['ramAmount'])) * 1024
            p_vdc_sp_href = filter(lambda x: x.attrib['name'] == 'Gold Storage', available_vdc_storage_profiles)[0]
            self.add_new_vdc_storage_profile(limit=limit, p_vdc_sp_href=p_vdc_sp_href.attrib['href'], default=default)
            default = 'false'

        if int(data_dict['rSilver']) > 0:
            limit = (int(data_dict['rSilver']) + int(data_dict['ramAmount'])) * 1024
            p_vdc_sp_href = filter(
                lambda x: x.attrib['name'] == 'Silver Mirrored Storage', available_vdc_storage_profiles
            )[0]
            self.add_new_vdc_storage_profile(limit=limit, p_vdc_sp_href=p_vdc_sp_href.attrib['href'], default=default)
            default = 'false'

        if int(data_dict['nrSilver']) > 0:
            limit = (int(data_dict['nrSilver']) + int(data_dict['ramAmount'])) * 1024
            p_vdc_sp_href = filter(lambda x: x.attrib['name'] == 'Silver Storage', available_vdc_storage_profiles)[0]
            self.add_new_vdc_storage_profile(limit=limit, p_vdc_sp_href=p_vdc_sp_href.attrib['href'], default=default)
            default = 'false'

        if int(data_dict['rPlat']) > 0:
            limit = (int(data_dict['rPlat']) + int(data_dict['ramAmount'])) * 1024
            p_vdc_sp_href = filter(
                lambda x: x.attrib['name'] == 'Platinum Mirrored Storage', available_vdc_storage_profiles
            )[0]
            self.add_new_vdc_storage_profile(limit=limit, p_vdc_sp_href=p_vdc_sp_href.attrib['href'], default=default)
            default = 'false'

        if int(data_dict['nrPlat']) > 0:
            limit = (int(data_dict['nrPlat']) + int(data_dict['ramAmount'])) * 1024
            p_vdc_sp_href = filter(lambda x: x.attrib['name'] == 'Platinum Storage', available_vdc_storage_profiles)[0]
            self.add_new_vdc_storage_profile(limit=limit, p_vdc_sp_href=p_vdc_sp_href.attrib['href'], default=default)

        ElementTree.SubElement(self.xml, 'ResourceGuaranteedMemory').text = '0.5'
        ElementTree.SubElement(self.xml, 'ResourceGuaranteedCpu').text = '1'
        ElementTree.SubElement(self.xml, 'IsThinProvision').text = 'true'

        ElementTree.SubElement(self.xml, 'NetworkPoolReference', {'href': network_pool_href})

        # add the provider vdc reference
        ElementTree.SubElement(self.xml, 'ProviderVdcReference', {'name': self.choosen_pvdc.name,
                                                                  'href': self.choosen_pvdc.href})

        ElementTree.SubElement(self.xml, 'OverCommitAllowed').text = 'false'


class User(ModelBase):
    def __init__(self, name, password, full_name, email, role_href):
        super(User, self).__init__()
        self.name = name
        self.password = password
        self.full_name = full_name
        self.email = email
        self.role_href = role_href
        self.xml = ElementTree.Element("User", {'xmlns': "http://www.vmware.com/vcloud/v1.5", 'name': self.name})
        self.fullName = ElementTree.SubElement(self.xml, 'FullName').text = self.full_name
        self.emailAddress = ElementTree.SubElement(self.xml, 'EmailAddress').text = self.email
        self.isEnabled = ElementTree.SubElement(self.xml, 'IsEnabled').text = 'true'
        self.role = ElementTree.SubElement(self.xml, 'Role', {'href': self.role_href})
        self.password = ElementTree.SubElement(self.xml, 'Password').text = self.password
        ElementTree.SubElement(self.xml, 'GroupReferences')


class Metadata(ModelBase):
    def __init__(self):
        super(Metadata, self).__init__()
        self.xml = ElementTree.Element('Metadata', {'xmlns': 'http://www.vmware.com/vcloud/v1.5',
                                                    'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                                    'type': 'application/vnd.vmware.vcloud.metadata+xml'})

    def add_metadata_entry(self, key, value, domain='SYSTEM', visibility='READONLY'):
        el = ElementTree.SubElement(self.xml, 'MetadataEntry',
                                    {'type': 'application/vnd.vmware.vcloud.metadata.value+xml'})
        ElementTree.SubElement(el, 'Domain', {'visibility': visibility}).text = domain
        ElementTree.SubElement(el, 'Key').text = key
        typed_value = ElementTree.SubElement(el, 'TypedValue', {'xsi:type': 'MetadataStringValue'})
        ElementTree.SubElement(typed_value, 'Value').text = value


class UpdateVdcStorageProfiles(ModelBase):
    def __init__(self):
        super(UpdateVdcStorageProfiles, self).__init__()
        self.xml = ElementTree.Element('UpdateVdcStorageProfiles', {'xmlns': 'http://www.vmware.com/vcloud/v1.5'})

    def add_storage_profile(self, limit, pvdcsp_href):
        add_sp = ElementTree.SubElement(self.xml, 'AddStorageProfile')
        ElementTree.SubElement(add_sp, 'Enabled').text = 'true'
        ElementTree.SubElement(add_sp, 'Units').text = 'MB'
        ElementTree.SubElement(add_sp, 'Limit').text = limit
        ElementTree.SubElement(add_sp, 'Default').text = 'false'
        ElementTree.SubElement(add_sp, 'ProviderVdcStorageProfile', {'href': pvdcsp_href})


class ControlAccessParams(ModelBase):
    def __init__(self, is_shared_to_everyone):
        super(ControlAccessParams, self).__init__()
        self.xml = ElementTree.Element('ControlAccessParams', {'xmlns': 'http://www.vmware.com/vcloud/v1.5'})
        ElementTree.SubElement(self.xml, 'IsSharedToEveryone').text = is_shared_to_everyone
        ElementTree.SubElement(self.xml, 'EveryoneAccessLevel').text = 'ReadOnly'
