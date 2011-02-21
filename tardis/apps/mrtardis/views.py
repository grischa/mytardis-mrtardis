from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import Context
from django.core.urlresolvers import reverse
from tardis.apps.mrtardis.utils import test_hpc_connection
#from tardis.apps.mrtardis.forms import HPCSetupForm
from tardis.apps.mrtardis.models import HPCUser
import tardis.apps.mrtardis.forms as forms
#from tardis.tardis_portal.logger import logger


def index(request, experiment_id):
    """return overview page for MR processing
    this page also contains javascript for moving between ajax inserts
    """
    hpc_username = test_hpc_connection(request.user)
#    newDSForm = forms.NewDSForm()
#    continueForm = forms.ContinueForm()
#    viewForm = forms.ViewForm()
#    rerunForm = forms.RerunForm()

    c = Context({
#            'newDSForm': newDSForm,
#            'continueForm': continueForm,
#            'viewForm': viewForm,
#            'rerunForm': rerunForm,
            'experiment_id': experiment_id,
            'hpc_username': hpc_username,
            })
    return render_to_response('mrtardis/index.html', c)


def test_user_setup(request, experiment_id):
    if request.method == 'POST':
        print "fuccck"
        form = forms.HPCSetupForm(request.POST)
        if form.is_valid():
            hpc_username = form.cleaned_data['hpc_username']
            newHPCUser = HPCUser(user=request.user,
                                 hpc_username=hpc_username)
            newHPCUser.save()
           # print reverse('index', args=[experiment_id])
            return HttpResponseRedirect(reverse(
                    'tardis.apps.mrtardis.views.index',
                    args=[experiment_id]))
    else:
        form = forms.HPCSetupForm()
    c = Context({
            'experiment_id': experiment_id,
            'HPCSetupForm': form,
            })
    return render_to_response("mrtardis/usersetup.html", c)
