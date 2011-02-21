from django.db import models
from django.contrib.auth.models import User


class HPCUser(models.Model):
    """
    holds hpc log in information for a user account.
    """
    user = models.ForeignKey(User, unique=True)
    hpc_username = models.CharField(max_length=20)
    testedConnection = models.BooleanField()

    def __unicode__(self):
        return self.user.username
