'''
Created on 10/12/2010

@author: Ulrich Felzmann
@author: Gerson Galang
'''

from django.contrib.auth.models import User, AnonymousUser
from django.conf import settings

from tardis.tardis_portal.auth.interfaces import GroupProvider
from tardis.tardis_portal.models import *
from tardis.tardis_portal.logger import logger

from suds.client import Client


EPN_LIST = "_epn_list"
SOAPLoginKey = "_vbl_session_key"

auth_key = u'vbl'
auth_display_name = u'VBL'


class VblGroupProvider(GroupProvider):
    name = u'vbl_group'

    def __init__(self):
        if settings.VBLSTORAGEGATEWAY:
            self.client = Client(settings.VBLSTORAGEGATEWAY)
            self.client.set_options(cache=None)
        else:
            self.client = None

    def getGroups(self, request):
        """
        return an iteration of the available groups.
        """
        if not request.session.__contains__(EPN_LIST):
            # check if the user is linked to any experiments
            if not settings.VBLSTORAGEGATEWAY:
                return []

            try:
                # check if a user exists that can authenticate using the VBL
                # auth method
                userAuth = UserAuthentication.objects.get(
                    userProfile__user=request.user,
                    authenticationMethod=auth_key)

            except UserAuthentication.DoesNotExist:
                return []

            result = str(
                self.client.service.VBLgetExpIDsFromEmail(userAuth.username))
            return result.split(',')

        epnList = request.session[EPN_LIST]
        return epnList

    def getGroupById(self, id):
        """
        return the group associated with the id::

            {"id": 123,
            "display": "Group Name",}

        """
        return {'id': id,
                'display': 'EPN_%i' % id}

    def searchGroups(self, **filter):
        if not settings.VBLSTORAGEGATEWAY:
            return []

        epn = filter.get('name')
        if not epn:
            return []

        users = str(self.client.service.VBLgetEmailsFromExpID(epn))
        if not users == 'None':

            # chop off literals (a,b,c) from epn (2467a -> 2467)
            from re import match
            epn = match('\d*', epn).group(0)

            return [{'id': int(epn),
                     'display': 'VBL/EPN_%s' % epn,
                     'members': users.split(',')}]
        else:
            return []

    def getGroupsForEntity(self, entity):
        """
        return a list of the groups an entity belongs to::

           [{'name': 'Group 456', 'id': '2'},
           {'name': 'Group 123', 'id': '1'}]

        """
        result = str(self.client.service.VBLgetExpIDsFromEmail(entity))
        if not result == 'None':
            return [{'id': epn,
                     'name': 'EPN_%i' % epn} for epn in result.split(',')]
        else:
            return []

    def getUser(self, user_dict):
        return None


class Backend():
    """
    Authenticate against the VBL SOAP Webservice. It is assumed that the
    request object contains the username and password to be provided to the
    VBLgetExpIDs function.

    a new local user is created if it doesn't already exist

    if the authentication succeeds, the session will contain a VBL
    session key used for downloads as well as the user's EPN list

    """
    def authenticate(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if not username or not password:
            return None

        # authenticate user and update group memberships
        if not settings.VBLSTORAGEGATEWAY:
            return None

        client = Client(settings.VBLSTORAGEGATEWAY)
        client.set_options(cache=None)
        # result = str(client.service.VBLgetExpIDs(username, password))
        result = str(client.service.VBLgetSOAPLoginKey(username, password))
        if result == 'None' or result.startswith('Error'):
            return None
        else:
            request.session[SOAPLoginKey] = result
        
        isADjangoAccount = True

        try:
            # check if the given username in combination with the VBL
            # auth method is already in the UserAuthentication table
            user = UserAuthentication.objects.get(username=username,
                authenticationMethod=auth_key).userProfile.user

        except UserAuthentication.DoesNotExist:
            # if request.user is not null, then we can assume that we are only
            # calling this function to verify if the provided username and
            # password will authenticate with this backend
            if type(request.user) is not AnonymousUser:
                user = request.user

            # else, create a new user with a random password
            else:
                isADjangoAccount = False
                name = username.partition('@')[0]
                name = '%s_%s' % (auth_key, name[0:26])
                password = User.objects.make_random_password()
                user = User.objects.create_user(username=name,
                                                password=password,
                                                email=username)
                user.save()

            try:
                # we'll also try and check if the user already has an
                # existing userProfile attached to his/her account
                userProfile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                userProfile = UserProfile(user=user,
                    isADjangoAccount=isADjangoAccount)
                userProfile.save()

            userAuth = UserAuthentication(userProfile=userProfile,
                username=username, authenticationMethod=auth_key)
            userAuth.save()

        # result contains comma separated list of epns
        request.session[EPN_LIST] = \
            str(client.service.VBLgetExpIDsFromEmail(username)).split(',')
        return user

    def get_user(self, user_id):
        raise NotImplemented()
