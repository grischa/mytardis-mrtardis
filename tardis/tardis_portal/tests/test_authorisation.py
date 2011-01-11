from django.test import TestCase
from django.test.client import Client

from django.contrib.auth.models import User, Group

from tardis.tardis_portal.models import ExperimentACL, Experiment


class ExperimentACLTestCase(TestCase):
    urls = 'tardis.urls'

    def setUp(self):

        # create a couple of test users
        self.user1 = User.objects.create_user('testuser1', '', 'secret')
        self.user2 = User.objects.create_user('testuser2', '', 'secret')
        self.user3 = User.objects.create_user('testuser3', '', 'secret')
        self.user4 = User.objects.create_user('testuser4', '', 'secret')

        # each user will have their own client
        self.client1 = Client()
        self.client2 = Client()
        self.client3 = Client()
        self.client4 = Client()

        # user1 will own experiment1
        self.experiment1 = Experiment(
            title='Experiment1',
            institution_name='Australian Synchrotron',
            approved=True,
            public=False,
            created_by=self.user1,
            )
        self.experiment1.save()

        # user2 will own experiment2
        self.experiment2 = Experiment(
            title='Experiment2',
            institution_name='Australian Synchrotron',
            approved=True,
            public=False,
            created_by=self.user2,
            )
        self.experiment2.save()

        # experiment3 is public
        self.experiment3 = Experiment(
            title='Experiment3',
            institution_name='Australian Synchrotron',
            approved=True,
            public=True,
            created_by=self.user3,
            )
        self.experiment3.save()

        # experiment4 will be accessible based on location information
        self.experiment4 = Experiment(
            title='Experiment4',
            institution_name='Australian Synchrotron',
            approved=True,
            public=False,
            created_by=self.user1,
            )
        self.experiment4.save()

        # user1 owns experiment1
        acl = ExperimentACL(
            pluginId='user',
            entityId=str(self.user1.id),
            experiment=self.experiment1,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        acl.save()

        # user2 owns experiment2
        acl = ExperimentACL(
            pluginId='user',
            entityId=str(self.user2.id),
            experiment=self.experiment2,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        acl.save()

        # experiment4 is accessible via location
        acl = ExperimentACL(
            pluginId='ip_address',
            entityId='127.0.0.1',
            experiment=self.experiment4,
            canRead=True,
            aclOwnershipType=ExperimentACL.SYSTEM_OWNED,
            )
        acl.save()

    def tearDown(self):
        self.client1.logout()
        self.client2.logout()
        self.client3.logout()
        self.client4.logout()

        self.experiment1.delete()
        self.experiment2.delete()
        self.experiment3.delete()
        self.experiment4.delete()

        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.user4.delete()

    def testAccessControl(self):
        login = self.client1.login(username='testuser1', password='secret')
        self.assertTrue(login)

        # user1 should be see experiment1
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # user1 should not be allowed to see experiment2
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment2.id))
        self.assertEqual(response.status_code, 403)

        # user1 should be allowed to see experiment3 as it's public
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment3.id))
        self.assertEqual(response.status_code, 200)

        # user1 should be allowed to see experiment4 based on his IP address
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment4.id))
        self.assertEqual(response.status_code, 200)

        # create a group and add it to experiment1
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/group/%s?canRead=true&create=true'
                                   % (self.experiment1.id, 'group1'))
        self.assertEqual(response.status_code, 200)

        # add user2 as admin to the newly created group
        group = Group.objects.get(name='group1')
        response = self.client1.get('/group/%i/add/%s?isAdmin=true'
                                   % (group.id, 'testuser2'))
        self.assertEqual(response.status_code, 200)

        self.client1.logout()

        # now check user2's permissions
        login = self.client2.login(username='testuser2', password='secret')
        self.assertTrue(login)

        # user2 should be able to see experiment1 now
        response = self.client2.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # user2 should be also able to see experiment2
        response = self.client2.get('/experiment/view/%i/'
                                   % (self.experiment2.id))
        self.assertEqual(response.status_code, 200)

        # user2 should be allowed to see experiment3 as it's public
        response = self.client2.get('/experiment/view/%i/'
                                   % (self.experiment3.id))
        self.assertEqual(response.status_code, 200)

        # user2 should be able to add user3 to group1 (experiment1)
        response = self.client2.get('/group/%i/add/%s?isAdmin=false'
                                   % (group.id, self.user3.username))

        self.client1.logout()

        # now check user3's permissions
        login = self.client3.login(username='testuser3', password='secret')
        self.assertTrue(login)

        # user3 should be able to see experiment1 via his group permissions
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # user3 should not be able to see experiment2
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment2.id))
        self.assertEqual(response.status_code, 403)

        # user3 should be able to see experiment3
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment3.id))
        self.assertEqual(response.status_code, 200)

        # user3 should not be able to add another user4 to group1
        response = self.client3.get('/group/%i/add/%s?isAdmin=false'
                                   % (group.id, self.user4.username))
        self.assertEqual(response.status_code, 403)

        self.client3.logout()

        # ok, now do some tricky stuff
        import datetime
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        url = '/experiment/control_panel/%i/access_list/change/user/%s/'

        login = self.client1.login(username='testuser1', password='secret')
        self.assertTrue(login)

        # remove user3 from group1
        response = self.client1.get('/group/%i/remove/%s/'
                                   % (group.id, self.user3.username))
        self.assertEqual(response.status_code, 200)

        # add user3 to experiment1
        self.client1.get('/experiment/control_panel/%i/access_list/add/user/%s'
                         % (self.experiment1.id, self.user3.username))
        self.assertEqual(response.status_code, 200)

        # give user3 read permissions for experiment1 effictive TOMORROW
        self.client1.post(url % (self.experiment1.id, self.user3.username),
                          {'canRead': True,
                           'effectiveDate_year': tomorrow.year,
                           'effectiveDate_month': tomorrow.month,
                           'effectiveDate_day': tomorrow.day,
                           })
        self.assertEqual(response.status_code, 200)

        # check permissions for user3
        login = self.client3.login(username='testuser3', password='secret')
        self.assertTrue(login)

        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 403)

        # change effictive date to TODAY
        self.client1.post(url % (self.experiment1.id, self.user3.username),
                          {'canRead': True,
                           'effectiveDate_year': today.year,
                           'effectiveDate_year': today.month,
                           'effectiveDate_year': today.day,
                           })

        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # change effictive date to YESTERDAY
        self.client1.post(url % (self.experiment1.id, self.user3.username),
                          {'canRead': True,
                           'effectiveDate_year': yesterday.year,
                           'effectiveDate_year': yesterday.month,
                           'effectiveDate_year': yesterday.day,
                           })

        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # set expiry date to TOMORROW
        self.client1.post(url % (self.experiment1.id, self.user3.username),
                          {'canRead': True,
                           'expiryDate_year': tomorrow.year,
                           'expiryDate_month': tomorrow.month,
                           'expiryDate_day': tomorrow.day,
                           })

        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # set expiry date to TODAY
        self.client1.post(url % (self.experiment1.id, self.user3.username),
                          {'canRead': True,
                           'expiryDate_year': today.year,
                           'expiryDate_month': today.month,
                           'expiryDate_day': today.day,
                           })

        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # set expiry date to YESTERDAY
        self.client1.post(url % (self.experiment1.id, self.user3.username),
                          {'canRead': True,
                           'expiryDate_year': yesterday.year,
                           'expiryDate_month': yesterday.month,
                           'expiryDate_day': yesterday.day,
                           })

        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 403)

        # can't think of any more stuff atm...
        self.client1.logout()
        self.client3.logout()

        # TODO: Unit Tests to check write and delete permissions!
