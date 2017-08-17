__author__ = 'alessio.rocchi'

import logging
from threading import Thread, BoundedSemaphore
from requests import ConnectionError
from socket import inet_aton
from helper import calculate_free_ips
from helper.LookupIp import lookup
from vcloudlib.helper import Http
import struct
import itertools
import json

runLock = BoundedSemaphore(1)
orgFetcherSem = BoundedSemaphore(20)

from app.models import Org, Vdc, db


class Poller(Thread):
    def __init__(self, log_format, timer=1200, global_variable=None):
        assert global_variable is not None, ValueError('Global Variable container must be passed.')
        super(Poller, self).__init__()
        self.name = 'Poller'
        self.timer = timer
        # use another logging system to improve readability
        log_formatter = logging.Formatter(log_format)
        self.logger = logging.getLogger('poller')
        self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

        file_handler = logging.FileHandler("poller_debug.log", "w")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_formatter)
        self.logger.addHandler(file_handler)

        self.logger.debug('Poller initialized correctly.')
        self.global_variable = global_variable
        self.stop = False

    def get_org_data(self, org):
        orgFetcherSem.acquire()
        self.global_variable.jsonified_data[org.name] = {}
        org.metadata = self.global_variable.vcs.get_metadata(org.href)
        self.logger.debug('Processing: {}'.format(org.name))
        try:
            for vdc in self.global_variable.vcs.get_vdc(org):
                self.global_variable.jsonified_data[org.name][vdc.name] = {
                    'metadata': org.metadata,
                    'href': vdc.href,
                    'allocationModel': vdc.AllocationModel,
                    'cpu': int(vdc.ComputeCapacity.Cpu.Limit) / 1000,
                    'memory': int(vdc.ComputeCapacity.Memory.Limit) / 1024,
                    'storages': [{'name': x.name,
                                  'limit': self.global_variable.vcs.get_storage_profile_limit(x.href)}
                                 for x in vdc.VdcStorageProfiles.VdcStorageProfile]
                }
                """
                with self.global_variable.app.app_context():
                    orgid = Org.query.filter_by(orgname=org.name).first().id
                    if len(Vdc.query.filter_by(name=vdc.name).all()) == 0:
                                _v = Vdc(
                                    orgid=orgid,
                                    name=vdc.name,
                                    cpu_reservation=self.global_variable.jsonified_data[org.name][vdc.name]['cpu'],
                                    memory_allocation=self.global_variable.jsonified_data[org.name][vdc.name]['memory'],
                                )
                                db.session.add(_v)
                                db.session.commit()
                """
                gateways = self.global_variable.vcs.get_gateways(vdc)
                self.global_variable.jsonified_data[org.name][vdc.name]['gateways'] = [vse.me.name for vse in gateways]
                self.global_variable.jsonified_data[org.name][vdc.name]['usedIp'] = sorted(
                    list(
                        itertools.chain(*[
                            [ip_ for ip_ in vse.get_full_public_ips() if not lookup(ip_)] for vse in gateways])),
                    key=lambda ip: struct.unpack("!L", inet_aton(ip))[0]
                )
                self.global_variable.used_ips.append(self.global_variable.jsonified_data[org.name][vdc.name]['usedIp'])
            orgFetcherSem.release()
        except ConnectionError as e:
            self.logger.exception(e)
            orgFetcherSem.release()

    def cancel(self):
        self.logger.debug("Stopping Poller Thread.")
        self.stop = True

    def run(self):
        self.logger.debug(
            "Loading Objects In Memory... Poller will reload data every: {timer} seconds.".format(timer=self.timer))
        while self.stop is False:
            self.global_variable.run_trigger.clear()
            self.global_variable.vcs.login()
            self.logger.info("Building Initial Org list...")
            # Make sure to be the only one running...
            runLock.acquire()
            thread_list = []
            try:
                for org in self.global_variable.vcs.get_orgs():
                    try:
                        # check if the org is present in db
                        """
                        with self.global_variable.app.app_context():
                            if len(Org.query.filter_by(orgname=org.name).all()) == 0:
                                _o = Org(orgname=org.name)
                                db.session.add(_o)
                                db.session.commit()
                        """
                        _t = Thread(target=self.get_org_data(org))
                        thread_list.append(_t)
                        _t.start()
                    except ConnectionError as e:
                        self.logger.exception(e)
                        break
                self.logger.debug("Waiting for all threads to finish...")
                for t in thread_list:
                    t.join()
                if calculate_free_ips(global_variable=self.global_variable):
                    self.logger.debug("Poller finished to load data. Dispatching to Flask route.")
                else:
                    self.logger.error('Cannot process free IP.')
                with open(self.global_variable.dump_file, 'w') as fh:
                    fh.write(json.dumps(self.global_variable.jsonified_data))
            except AttributeError as e:
                self.logger.exception(e)
                self.global_variable.run_trigger.wait(self.timer)
                continue
            runLock.release()
            self.global_variable.run_trigger.wait(self.timer)
