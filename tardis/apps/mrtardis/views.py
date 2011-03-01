from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.template import Context
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
import zipfile

from tardis.apps.mrtardis.utils import test_hpc_connection
from tardis.apps.mrtardis.utils import add_staged_file_to_dataset
#from tardis.apps.mrtardis.forms import HPCSetupForm
from tardis.apps.mrtardis.models import HPCUser
from tardis.apps.mrtardis.forms import DatasetDescriptionForm
from tardis.apps.mrtardis.forms import selectDSForm
from tardis.apps.mrtardis.forms import HPCSetupForm
from tardis.apps.mrtardis.mrtask import MRtask
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import DatasetParameterSet
from tardis.tardis_portal.models import DatasetParameter
from tardis.tardis_portal.models import ParameterName
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import Dataset_File
from tardis.tardis_portal.auth import decorators as authz

#from tardis.tardis_portal.logger import logger


def index(request, experiment_id):
    """return overview page for MR processing
    this page also contains javascript for moving between ajax inserts
    """
    hpc_username = test_hpc_connection(request.user)
    newDSForm = DatasetDescriptionForm()

    def getChoices(status):
        return [(dps.dataset.id, dps.dataset.description)
                       for dps in
                       MRtask.getTaskList(experiment_id,
                                          status=status)]
    continueChoices = getChoices("unsubmitted")
    print continueChoices
    if continueChoices:
        continueForm = selectDSForm(continueChoices)
    else:
        continueForm = False
    viewFormChoices = getChoices("finished")
    if viewFormChoices:
        viewForm = selectDSForm(viewFormChoices)
    else:
        viewForm = False
    rerunFormChoices = getChoices("finished")
    if rerunFormChoices:
        rerunForm = selectDSForm(rerunFormChoices)
    else:
        rerunForm = False

    c = Context({
            'newDSForm': newDSForm,
            'continueForm': continueForm,
            'viewForm': viewForm,
            'rerunForm': rerunForm,
            'experiment_id': experiment_id,
            'hpc_username': hpc_username,
            })
    return render_to_response('mrtardis/index.html', c)


def test_user_setup(request, experiment_id):
    if request.method == 'POST':
        print "fuccck"
        form = HPCSetupForm(request.POST)
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
        form = HPCSetupForm()
    c = Context({
            'experiment_id': experiment_id,
            'HPCSetupForm': form,
            })
    return render_to_response("mrtardis/usersetup.html", c)


def MRform(request, experiment_id):
    #logger.debug(repr(request.POST))
    if 'action' not in request.POST:
        return HttpResponseNotFound('<h1>Wrong use of function</h1>')
    action = request.POST['action']
    if action == "newDS":
        description = request.POST['description']
        newDataset = Dataset()
        newDataset.experiment_id = experiment_id
        newDataset.description = description
        newDataset.save()
        dataset = newDataset
        schema = Schema.objects.get(namespace__endswith="mrtardis")
        newDPS = DatasetParameterSet()
        newDPS.schema = schema
        newDPS.dataset = newDataset
        newDPS.save()
        newDP = DatasetParameter()
        newDP.parameterset = newDPS
        try:
            paramName = ParameterName.objects.get(name="TaskStatus",
                                             schema=schema)
        except ObjectDoesNotExist:
            paramName = ParameterName()
            paramName.schema = schema
            paramName.name = "TaskStatus"
            paramName.full_name = "Status of task"
            paramName.is_numeric = False
            paramName.is_searchable = True
            paramName.save()
        newDP.name = paramName
        newDP.string_value = "unsubmitted"
        newDP.save()
    elif action == "continue":
        dataset = Dataset.objects.get(pk=int(request.POST['dataset']))
        pass  # load existing parameters into form
    elif action == "rerunDS":
        dataset = Dataset.objects.get(pk=request.POST['dataset'])
        pass  # run new MR based on finished one
    c = Context({
            'dataset': dataset,
            'experiment_id': experiment_id,
            })
    return render_to_response("mrtardis/MRform.html", c)


def parForm(request, experiment_id):
    pass


def displayResults(request, experiment_id):
    c = Context({
            'sometext': "describing what to do dep on context",
            'experiment_id': experiment_id,
            })
    return render_to_response("mrtardis/displayResults.html", c)


@authz.dataset_access_required
def type_filtered_file_list(request, dataset_id):
    if 'type' not in request.POST:
        return HttpResponseNotFound('<h1>Wrong use of function</h1>')
    type = request.POST['type']
    print type
    filequeryset = Dataset_File.objects.filter(
        dataset__pk=dataset_id, filename__iendswith=type).order_by('filename')
    for file in filequeryset:
        print file
    print filequeryset
    c = Context({
        'filequeryset': filequeryset,
        })
    return render_to_response('mrtardis/file_list.html', c)


def extractPDBzips(request, dataset_id):
    """
    Extracts pdb files out of zips, adds them to the dataset and
    removes the zip. Returns 'true' for ajax if successful.
    """
    zipquery = Dataset_File.objects.filter(dataset__pk=dataset_id,
                                           filename__iendswith=".zip")
    if len(zipquery) == 0:
        return HttpResponseNotFound()
    print "sadkfhaksfhgakjshfdasd"
    for zipfileobj in zipquery:
        print zipfileobj.id
        zippath = zipfileobj.get_absolute_filepath()
        thiszip = zipfile.ZipFile(zippath, 'r')
        extractlist = []
        for filename in thiszip.namelist():
            if filename.endswith((".pdb", ".PDB")) and \
                    not filename.startswith("__MACOSX"):
                extractlist.append(filename)
        thiszip.extractall(settings.STAGING_PATH, extractlist)
        thiszip.close()
        for pdbfile in extractlist:
            #print pdbfile
            add_staged_file_to_dataset(pdbfile, dataset_id,
                                       mimetype="chemical/x-pdb")
        zipfileobj.deleteCompletely()
    return HttpResponse("true")
