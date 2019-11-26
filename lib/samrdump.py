#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# -*- Mode: python -*-

import sys
from time import strftime, gmtime

from lib.logger import logger

try:
    from impacket.self.__dcerpc.v5 import samr
    from impacket.nt_errors import STATUS_MORE_ENTRIES
    from impacket.dcerpc.v5.rpcrt import DCERPCException
except ImportError:
    sys.stderr.write('samrdump: Impacket import error')
    sys.stderr.write('Impacket by SecureAuth Corporation is required for this tool to work. Please download it using:'
                     '\npip: pip install -r requirements.txt\nOr through your package manager:\npython-impacket.')
    sys.exit(255)


#################################################################
# Code borrowed and adapted from Impacket's samrdump.py example #
#################################################################
class Samr(object):

    def __init__(self):
        pass

    def users(self, usrdomain):
        self.__samr_connect()
        self.__samr_users(usrdomain)
        self.__samr_disconnect()

    def pswpolicy(self, usrdomain):
        self.__samr_connect()
        self.__samr_pswpolicy(usrdomain)
        self.__samr_disconnect()

    def domains(self):
        self.__samr_connect()
        self.__samr_domains()
        self.__samr_disconnect()

    def __samr_connect(self):
        '''
        Connect to samr named pipe
        '''
        logger.debug('Connecting to the SAMR named pipe')
        self.smb_transport('samr')

        logger.debug('Binding on Security Account Manager (SAM) interface')
        self.__self.__dce = self.trans.get_self.__dce_rpc()
        self.__self.__dce.bind(samr.MSRPC_UUID_SAMR)
        self.__resp = samr.hSamrConnect(self.__self.__dce)
        self.__mgr_handle = self.__resp['ServerHandle']

    def __samr_disconnect(self):
        '''
        Disconnect from samr named pipe
        '''
        logger.debug('Disconnecting from the SAMR named pipe')

        self.__self.__dce.disconnect()

    def __samr_users(self, usrdomain=None):
        '''
        Enumerate users on the system
        '''
        self.__samr_domains(False)

        encoding = sys.getdefaultencoding()

        for domain_name, domain in self.domains_dict.items():
            if usrdomain and usrdomain.upper() != domain_name.upper():
                continue

            logger.info('Looking up users in domain %s' % domain_name)

            resp = samr.hSamrLookupDomainInSamServer(self.__self.__dce, self.__mgr_handle, domain)
            resp = samr.hSamrOpenDomain(self.__self.__dce, serverHandle=self.__mgr_handle, domainId=resp['DomainId'])
            self.__domain_context_handle = resp['DomainHandle']
            resp = self.__samr.enumusers(self.__domain_context_handle)

            status = STATUS_MORE_ENTRIES
            enum_context = 0
            while status == STATUS_MORE_ENTRIES:
                try:
                    resp = samr.hSamrEnumerateUsersInDomain(self.__self.__dce, self.__domain_context_handle,
                                                            enumerationContext=enum_context)
                except self.__dceRPCException as e:
                    if str(e).find('STATUS_MORE_ENTRIES') < 0:
                        raise
                    resp = e.get_packet()

                for user in resp['Buffer']['Buffer']:
                    r = samr.hSamrOpenUser(self.__self.__dce, self.__domain_context_handle,
                                           samr.MAXIMUM_ALLOWED, user['RelativeId'])
                    logger.debug('Found user %s (UID: %d)' % (user['Name'], user['RelativeId']))
                    info = samr.hSamrQueryInformationUser2(self.__self.__dce, r['UserHandle'],
                                                           samr.USER_INFORMATION_CLASS.UserAllInformation)
                    entry = (user['Name'], user['RelativeId'], info['Buffer']['All'])
                    self.users_list.add(entry)
                    samr.hSamrCloseHandle(self.__self.__dce, r['UserHandle'])

                enum_context = resp['EnumerationContext']
                status = resp['ErrorCode']

            if self.users_list:
                num = len(self.users_list)
                logger.info('Retrieved %d user%s' % (num, 's' if num > 1 else ''))
            else:
                logger.info('No users enumerated')

            for entry in self.users_list:
                user, uid, info = entry

                print user
                print '  User ID: %d' % uid
                print '  Group ID: %d' % info['PrimaryGroupId']
                if info['UserAccountControl'] & samr.USER_ACCOUNT_DISABLED:
                    account_disabled = 'True'
                else:
                    account_disabled = 'False'
                print '  Enabled: %s' % account_disabled

                try:
                    print '  Logon count: %d' % info['LogonCount']
                except ValueError:
                    pass

                try:
                    print '  Last Logon: %s' % info['LastLogon']
                except ValueError:
                    pass

                try:
                    print '  Last Logoff: %s' % info['LastLogoff']
                except ValueError:
                    pass

                try:
                    print '  Last password set: %s' % info['PasswordLastSet']
                except ValueError:
                    pass

                try:
                    print '  Password expired: %d' % info['PasswordExpired']
                except ValueError:
                    pass

                if info['UserAccountControl'] & samr.USER_DONT_EXPIRE_PASSWORD:
                    dont_expire = 'True'
                else:
                    dont_expire = 'False'

                try:
                    print '  Password does not expire: %d' % dont_expire
                except ValueError:
                    pass

                try:
                    print '  Password can change: %s' % info['PasswordCanChange']
                except ValueError:
                    pass

                try:
                    print '  Password must change: %s' % info['PasswordMustChange']
                except ValueError:
                    pass

                try:
                    print '  Bad password count: %d' % info['BadPasswordCount']
                except ValueError:
                    pass

                try:
                    print '  Full name: %d' % info['FullName']
                except ValueError:
                    pass

                try:
                    print '  Home directory: %d' % info['HomeDirectory']
                except ValueError:
                    pass

                try:
                    print '  Home directory drive: %d' % info['HomeDirectoryDrive']
                except ValueError:
                    pass

                try:
                    print '  Script path: %d' % info['ScriptPath']
                except ValueError:
                    pass

                try:
                    print '  Profile path: %d' % info['ProfilePath']
                except ValueError:
                    pass

                try:
                    print '  Admin comment: %d' % info['AdminComment']
                except ValueError:
                    pass

                try:
                    print '  Workstations: %d' % info['WorkStations']
                except ValueError:
                    pass

                try:
                    print '  User comment: %d' % info['UserComment']
                except ValueError:
                    pass

            self.users_list = set()

    def __samr_pswpolicy(self, usrdomain=None):
        self.__samr_domains(False)

        for domain_name, domain in self.domains_dict.items():
            if usrdomain and usrdomain.upper() != domain_name.upper():
                continue

            logger.info('Looking up password policy in domain %s' % domain_name)

            resp = samr.hSamrLookupDomainInSamServer(self.__dce, serverHandle=self.__mgr_handle, name=domain_name)
            if resp['ErrorCode'] != 0:
                raise Exception('Connect error')

            resp = samr.hSamrOpenDomain(self.__dce, serverHandle=self.__mgr_handle, desiredAccess=samr.MAXIMUM_ALLOWED,
                                         domainId=resp['DomainId'])
            if resp['ErrorCode'] != 0:
                raise Exception('Connect error')
            domainHandle = resp['DomainHandle']
            # End Setup

            domain_passwd = samr.DOMAIN_INFORMATION_CLASS.DomainPasswordInformation
            re = samr.hSamrQueryInformationDomain2(
                self.__dce, domainHandle=domainHandle,
                domainInformationClass=domain_passwd)
            self.__min_pass_len = re['Buffer']['Password']['MinPasswordLength'] \
                                  or "None"
            pass_hist_len = re['Buffer']['Password']['PasswordHistoryLength']
            self.__pass_hist_len = pass_hist_len or "None"
            self.__max_pass_age = convert(
                int(re['Buffer']['Password']['MaxPasswordAge']['LowPart']),
                int(re['Buffer']['Password']['MaxPasswordAge']['HighPart']))
            self.__min_pass_age = convert(
                int(re['Buffer']['Password']['MinPasswordAge']['LowPart']),
                int(re['Buffer']['Password']['MinPasswordAge']['HighPart']))
            self.__pass_prop = d2b(re['Buffer']['Password']['PasswordProperties'])

            domain_lockout = samr.DOMAIN_INFORMATION_CLASS.DomainLockoutInformation
            re = samr.hSamrQueryInformationDomain2(
                self.__dce, domainHandle=domainHandle,
                domainInformationClass=domain_lockout)
            self.__rst_accnt_lock_counter = convert(
                0,
                re['Buffer']['Lockout']['LockoutObservationWindow'],
                lockout=True)
            self.__lock_accnt_dur = convert(
                0,
                re['Buffer']['Lockout']['LockoutDuration'],
                lockout=True)
            self.__accnt_lock_thres = re['Buffer']['Lockout']['LockoutThreshold'] \
                                      or "None"

            domain_logoff = samr.DOMAIN_INFORMATION_CLASS.DomainLogoffInformation
            re = samr.hSamrQueryInformationDomain2(
                self.__dce, domainHandle=domainHandle,
                domainInformationClass=domain_logoff)
            self.__force_logoff_time = convert(
                re['Buffer']['Logoff']['ForceLogoff']['LowPart'],
                re['Buffer']['Logoff']['ForceLogoff']['HighPart'])

            self.print_friendly()

    def print_friendly(self):
        PASSCOMPLEX = {
            5: 'Domain Password Complex:',
            4: 'Domain Password No Anon Change:',
            3: 'Domain Password No Clear Change:',
            2: 'Domain Password Lockout Admins:',
            1: 'Domain Password Store Cleartext:',
            0: 'Domain Refuse Password Change:'
        }

        print 'Minimum password length: %s' % str(self.__min_pass_len or 'None')
        print 'Password history length: %s' % str(self.__pass_hist_len or 'None')
        print 'Maximum password age: %s' % str(self.__max_pass_age)
        print 'Password Complexity Flags: %s' % str(self.__pass_prop or 'None')
        print 'Minimum password age: %s' % str(self.__min_pass_age)
        print 'Reset Account Lockout Counter: %s' % str(self.__rst_accnt_lock_counter)
        print 'Locked Account Duration: %s' % str(self.__lock_accnt_dur)
        print 'Account Lockout Threshold: %s' % str(self.__accnt_lock_thres)
        print 'Forced Log off Time: %s' % str(self.__force_logoff_time)

        for i, a in enumerate(self.__pass_prop):
            print '%s: %s' % (PASSCOMPLEX[i], str(a))
            i += 1

        return

    def __samr_domains(self, display=True):
        """
        Enumerate domains to which the system is part of
        """
        logger.info('Enumerating domains')

        resp = samr.hSamrEnumerateDomainsInSamServer(self.__self.__dce, self.__mgr_handle)
        domains = resp['Buffer']['Buffer']

        if display is True:
            print 'Domains:'

        for domain in domains:
            domain_name = domain['Name']

            if domain_name not in self.domains_dict:
                self.domains_dict[domain_name] = domain

            if display is True:
                print '  %s' % domain_name


def d2b(a):
    tbin = []
    while a:
        tbin.append(a % 2)
        a /= 2

    t2bin = tbin[::-1]
    if len(t2bin) != 8:
        for x in xrange(6 - len(t2bin)):
            t2bin.insert(0, 0)
    return ''.join([str(g) for g in t2bin])


def convert(low, high, lockout=False):
    time = ""
    tmp = 0

    if low == 0 and hex(high) == "-0x80000000":
        return "Not Set"
    if low == 0 and high == 0:
        return "None"

    if not lockout:
        if (low != 0):
            high = abs(high+1)
        else:
            high = abs(high)
            low = abs(low)

        tmp = low + (high)*16**8  # convert to 64bit int
        tmp *= (1e-7)  # convert to seconds
    else:
        tmp = abs(high) * (1e-7)

    try:
        minutes = int(strftime("%M", gmtime(tmp)))
        hours = int(strftime("%H", gmtime(tmp)))
        days = int(strftime("%j", gmtime(tmp)))-1
    except ValueError as e:
        return "[-] Invalid TIME"

    if days > 1:
        time += "{0} days ".format(days)
    elif days == 1:
        time += "{0} day ".format(days)
    if hours > 1:
        time += "{0} hours ".format(hours)
    elif hours == 1:
        time += "{0} hour ".format(hours)
    if minutes > 1:
        time += "{0} minutes ".format(minutes)
    elif minutes == 1:
        time += "{0} minute ".format(minutes)
    return time