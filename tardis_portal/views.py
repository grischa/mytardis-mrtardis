from django.template import Context, loader
from django.http import HttpResponse

from django.conf import settings

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.contrib.auth.decorators import login_required

from tardis.tardis_portal.ProcessExperiment import ProcessExperiment
from tardis.tardis_portal.RegisterExperimentForm import RegisterExperimentForm

from django.core.paginator import Paginator, InvalidPage, EmptyPage

from tardis.tardis_portal.models import *
from django.db.models import Sum

def render_response_index(request, *args, **kwargs):

	kwargs['context_instance'] = RequestContext(request)
	
	kwargs['context_instance']['is_authenticated'] = request.user.is_authenticated()
	kwargs['context_instance']['username'] = request.user.username
	
	#stats
	kwargs['context_instance']['public_datasets'] = Dataset.objects.filter(experiment__approved=True)
	kwargs['context_instance']['public_datafiles'] = Dataset_File.objects.filter(dataset__experiment__approved=True)
	kwargs['context_instance']['public_experiments'] = Experiment.objects.filter(approved=True)
	kwargs['context_instance']['public_pdbids'] = Pdbid.objects.filter(experiment__approved=True)

	return render_to_response(*args, **kwargs)
	
def return_response_error(request):
	c = Context({
		'status': "ERROR: Forbidden",
		'error': True		
	})

	return HttpResponseForbidden(render_response_index(request, 'tardis_portal/blank_status.html', c))
	
def return_response_not_found(request):
	c = Context({
		'status': "ERROR: Not Found",
		'error': True
	})

	return HttpResponseNotFound(render_response_index(request, 'tardis_portal/blank_status.html', c))	
	
def return_response_error_message(request, redirect_path, message):
	c = Context({
		'status': message,
		'error': True		
	})

	return HttpResponseServerError(render_response_index(request, redirect_path, c))
	
def get_accessible_experiments(user_id):

		experiments = None

		# from stackoverflow question 852414
		from django.db.models import Q

		user = User.objects.get(id=user_id)

		queries = [Q(id=group.name) for group in user.groups.all()]

		if queries:
				query = queries.pop()

				for item in queries:
						query |= item

				experiments = Experiment.objects.filter(query)

		return experiments

def get_owned_experiments(user_id):

	experiments = Experiment.objects.filter(experiment_owner__user__pk=user_id)

	return experiments	
	
def has_experiment_ownership(experiment_id, user_id):
	
	experiment = Experiment.objects.get(pk=experiment_id)

	eo = Experiment_Owner.objects.filter(experiment=experiment, user=user_id)

	if eo:
		return True
	else:
		return False
		
#custom decorator
def experiment_ownership_required(f):
        def wrap(request, *args, **kwargs):
				#if user isn't logged in it will redirect to login page
				if not request.user.is_authenticated():
					return HttpResponseRedirect("/login")
				if not has_experiment_ownership(kwargs['experiment_id'], request.user.pk):
					return return_response_error(request)

				return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap		

#custom decorator
def experiment_access_required(f):
        def wrap(request, *args, **kwargs):
				#if user isn't logged in it will redirect to login page
				if not request.user.is_authenticated():
					return HttpResponseRedirect("/login")
				if not has_experiment_access(kwargs['experiment_id'], request.user.pk):
					return return_response_error(request)
				
				return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

#custom decorator
def dataset_access_required(f):
        def wrap(request, *args, **kwargs):
				#if user isn't logged in it will redirect to login page
				if not request.user.is_authenticated():
					return HttpResponseRedirect("/login")
				if not has_dataset_access(kwargs['dataset_id'], request.user.pk):
					return return_response_error(request)

				return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

#custom decorator
def datafile_access_required(f):
        def wrap(request, *args, **kwargs):
				#if user isn't logged in it will redirect to login page
				if not request.user.is_authenticated():
					return HttpResponseRedirect("/login")
				if not has_datafile_access(kwargs['dataset_file_id'], request.user.pk):
					return return_response_error(request)

				return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

def has_experiment_access(experiment_id, user_id):

	g = Group.objects.filter(name=experiment_id, user__id=user_id)

	if g:
		return True
	else:
		return False
		
def has_dataset_access(dataset_id, user_id):

	experiment = Experiment.objects.get(dataset__pk=dataset_id)
	g = Group.objects.filter(name=experiment.id, user__pk=user_id)
	

	if g:
		return True
	else:
		return False	
		
def has_datafile_access(dataset_file_id, user_id):

	df = Dataset_File.objects.get(id=dataset_file_id)
	g = Group.objects.filter(name=df.dataset.experiment.id, user__pk=user_id)


	if g:
		return True
	else:
		return False
		
def in_group(user, group):
	"""Returns True/False if the user is in the given group(s).
	Usage::
		{% if user|in_group:"Friends" %}
		or
		{% if user|in_group:"Friends,Enemies" %}
		...
		{% endif %}
	You can specify a single group or comma-delimited list.
	No white space allowed.
	"""

	group_list = [group.name]
	
	user_groups = []
	
	for group in user.groups.all(): user_groups.append(str(group.name))
	
	print group_list
	print user_groups
	
	if filter(lambda x:x in user_groups, group_list):
		return True
	else:
		return False			

def index(request):
	
	status = ""
	
	#import feedparser

	#channels = feedparser.parse('http://tardis.edu.au/site_media/xml/localBlogCopy.xml')
	
	# 'entries': channels.entries,

	c = Context({
		'status': status,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/index.html', c))		
	
def download(request, dfid):

	#todo handle missing file, general error
	if request.GET.has_key('dfid') and len(request.GET['dfid']) > 0:
		datafile = Dataset_File.objects.get(pk=request.GET['dfid'])
		if has_datafile_access(datafile.id, request.user.id):
			url = datafile.url
		
			if url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://'):
				return HttpResponseRedirect(datafile.url)
			else:
				file_path = settings.FILE_STORE_PATH + "/" + str(datafile.dataset.experiment.id) + "/" + datafile.url.partition('//')[2]
			
				try:
					print file_path
					from django.core.servers.basehttp import FileWrapper
					wrapper = FileWrapper(file(file_path))
					
					response = HttpResponse(wrapper, mimetype='application/octet-stream')
					response['Content-Disposition'] = 'attachment; filename=' + datafile.filename
					
					import os
					response['Content-Length'] = os.path.getsize(file_path)
					
					return response

				except IOError, io:
					return return_response_not_found(request)				

		else:
			return return_response_error(request)
		
def downloadTar(request):
	# Create the HttpResponse object with the appropriate headers.
	# todo handle no datafile, invalid filename, all http links (tarfile count?)
	
	if request.POST.has_key('datafile'):
		
		if not len(request.POST.getlist('datafile')) == 0:
			from django.utils.safestring import SafeUnicode	
			from django.core.servers.basehttp import FileWrapper
		
			import StringIO

			buffer = StringIO.StringIO()			
	
			import os		
	
			fileString = ""
			fileSize = 0
			for dfid in request.POST.getlist('datafile'):
				datafile = Dataset_File.objects.get(pk=dfid)
				if has_datafile_access(dfid, request.user.id):
					if datafile.url.startswith('file://'):
						absolute_filename = datafile.url.partition('//')[2]
						fileString = fileString + request.POST['expid'] + '/' + absolute_filename + " "
						fileSize = fileSize + long(datafile.size)
	
			#tarfile class doesn't work on large files being added and streamed on the fly, so going command-line-o
			
			tar_command = "tar -C " + settings.FILE_STORE_PATH + " -c " + fileString												
			
			import shlex, subprocess
			
			response = HttpResponse(FileWrapper(subprocess.Popen(tar_command, stdout=subprocess.PIPE, shell=True).stdout), mimetype='application/x-tar')
			response['Content-Disposition'] = 'attachment; filename=experiment' + request.POST['expid'] + '.tar'
			response['Content-Length'] = fileSize + 5120

			return response
		else:
			return return_response_not_found(request)
	else:
		return return_response_not_found(request)
		

def about(request):
	
	c = Context({
		'subtitle': "About",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/about.html', c))	

def partners(request):

	c = Context({

	})
	return HttpResponse(render_response_index(request, 'tardis_portal/partners.html', c))

@experiment_access_required
def view_experiment(request, experiment_id):
	
	try:
		experiment = Experiment.objects.get(pk=experiment_id)
		author_experiments = Author_Experiment.objects.all()
		author_experiments = author_experiments.filter(experiment=experiment)
		author_experiments = author_experiments.order_by('order')
		
		datafiles = Dataset_File.objects.filter(dataset__experiment=experiment_id)
		
		c = Context({
			'experiment': experiment,
			'authors': author_experiments,
			'datafiles': datafiles,
			# 'totalfilesize': datafiles.aggregate(Sum('size'))['size__sum'],			
			'subtitle': experiment.title,			
		})
	except Experiment.DoesNotExist, de:
		return return_response_not_found(request)
	
	return HttpResponse(render_response_index(request, 'tardis_portal/view_experiment.html', c))

@login_required()
def experiment_index(request):
	
	experiments = get_accessible_experiments(request.user.id)
	if experiments:
		experiments = experiments.order_by('title')
	
	c = Context({
		'experiments': experiments,
		'subtitle': "Experiment Index",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/experiment_index.html', c))

# web service, depreciated
def register_experiment_ws(request):
	# from java.lang import Exception
	import sys

	process_experiment = ProcessExperiment()
	status = ""
	if request.method == 'POST': # If the form has been submitted...

		url = request.POST['url']
		username = request.POST['username']
		password = request.POST['password']
		
		from django.contrib.auth import authenticate
		user = authenticate(username=username, password=password)
		if user is not None:
		    if not user.is_active:
		        return return_response_error(request)
		else:
		    return return_response_error(request)		

		try:
			experiments = Experiment.objects.all()
			experiments = experiments.filter(url__iexact=url)
			if not experiments:
				eid = process_experiment.register_experiment(url=url, created_by=user)
			else:
				return return_response_error_message(request, 'tardis_portal/blank_status.html', "Error: Experiment already exists")
		except IOError, i:
			return return_response_error_message(request, 'tardis_portal/blank_status.html', "Error reading file. Perhaps an incorrect URL?")				
		except:
			return return_response_error_message(request, 'tardis_portal/blank_status.html', "Unexpected Error - ", sys.exc_info()[0])				

		response = HttpResponse(status=200)
		response['Location'] = settings.TARDISURLPREFIX + "/experiment/view/" + str(eid)

		return response	
	else:
		return return_response_error(request)

# web service
def register_experiment_ws_xmldata(request):
	import sys

	process_experiment = ProcessExperiment()
	status = ""
	if request.method == 'POST': # If the form has been submitted...

		form = RegisterExperimentForm(request.POST) # A form bound to the POST data
		if form.is_valid(): # All validation rules pass

			xmldata = form.cleaned_data['xmldata']
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			experiment_owner = form.cleaned_data['experiment_owner']

			from django.contrib.auth import authenticate
			user = authenticate(username=username, password=password)
			if user is not None:
				if not user.is_active:
					return return_response_error(request)
			else:
				return return_response_error(request)			

			eid = process_experiment.register_experiment_xmldata(xmldata=xmldata, created_by=user) # steve dummy data
			dir = settings.FILE_STORE_PATH + "/" + str(eid)
			
			#todo this entire function needs a fancy class with functions for each part..
			import os
			if not os.path.exists(dir):
				os.makedirs(dir)
				os.system('chmod g+w ' + dir)
			
			file = open(dir + '/METS.xml', 'w')

			file.write(xmldata)

			file.close()	
			
			#create group
			
			#for each PI
				#check if they exist
					#if exist
						#assign to group
					#else
						#create user, generate username, randomly generated pass, send email with pass
			
			if not len(request.POST.getlist('experiment_owner')) == 0:
				g = Group(name=eid)
				g.save()
							
				for owner in request.POST.getlist('experiment_owner'):
					
					u = None
					try:
						u = User.objects.get(email__exact=owner)
					except User.DoesNotExist, ue:
						from random import choice
						import string
						
						#random password
						random_password = ""
						chars = string.letters + string.digits
						for i in range(8):
							random_password = random_password + choice(chars)					
						
						new_username = owner.partition('@')[0]
						new_username = new_username.replace(".", "_")

						# email new username and password
						from django.core.mail import send_mail

						recipient_list = list()

						subject = "TARDIS User Automatically Created"
						message = "A new user has been created in myTARDIS as a result of data you own being stored. Log in to " + settings.TARDISURLPREFIX + "/login with the username: " + new_username + " password: " + random_password
						from_email = "steve.androulakis@gmail.com"
						recipient_list.append(owner)
						print recipient_list
						
						u = User.objects.create_user(new_username, owner, random_password)
						
						#send_mail(subject, message, from_email, recipient_list, fail_silently=False)						
					
					exp_owner = Experiment_Owner(experiment=Experiment.objects.get(pk=eid), user=u)
					exp_owner.save()
					u.groups.add(g)			

			response = HttpResponse(str(eid), status=200)
			response['Location'] = settings.TARDISURLPREFIX + "/experiment/view/" + str(eid)

			return response

	else:
		form = RegisterExperimentForm() # An unbound form

	c = Context({
		'form': form,
		'status': status,
		'subtitle': "Register Experiment",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/register_experiment.html', c))

@datafile_access_required	
def retrieve_parameters(request, dataset_file_id):

	parameters = DatafileParameter.objects.all()
	parameters = parameters.filter(dataset_file__pk=dataset_file_id)

	c = Context({
		'parameters': parameters,
	})

	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/parameters.html', c))

@datafile_access_required
def retrieve_xml_data(request, dataset_file_id):
	from pygments import highlight
	from pygments.lexers import XmlLexer
	from pygments.formatters import HtmlFormatter
	from pygments.styles import get_style_by_name

	xml_data = XML_data.objects.get(datafile__pk=dataset_file_id)

	formatted_xml = highlight(xml_data.data, XmlLexer(), HtmlFormatter(style='default', noclasses=True))	

	c = Context({
		'formatted_xml': formatted_xml,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/xml_data.html', c))	

@dataset_access_required
def retrieve_datafile_list(request, dataset_id):
	from django.db.models import Count

	dataset = Dataset_File.objects.filter(dataset__pk=dataset_id).order_by('filename')

	c = Context({
		'dataset': dataset,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/datafile_list.html', c)) 	

@login_required()
def control_panel(request):
	
	experiments = get_owned_experiments(request.user.id)
	if experiments:
		experiments = experiments.order_by('title')
	
	c = Context({
		'experiments': experiments,
		'subtitle': "Experiment Control Panel",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/control_panel.html', c))
	
def search_experiment(request):
	get = False
	experiments = Experiment.objects.all()
	experiments = Experiment.objects.order_by('title')
	
	experiments = Experiment.objects.filter(approved=True)

	if request.GET.has_key('results'):
		get = True
		if request.GET.has_key('title') and len(request.GET['title']) > 0:
			experiments = experiments.filter(title__icontains=request.GET['title'])

		if request.GET.has_key('description') and len(request.GET['description']) > 0:
			experiments = experiments.filter(description__icontains=request.GET['description'])

		if request.GET.has_key('institution_name') and len(request.GET['institution_name']) > 0:
			experiments = experiments.filter(institution_name__icontains=request.GET['institution_name'])

		if request.GET.has_key('creator') and len(request.GET['creator']) > 0:
			experiments = experiments.filter(author_experiment__author__name__icontains=request.GET['creator'])

	c = Context({
		'submitted': get,
		'experiments': experiments,
		'subtitle': "Search Experiments",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/search_experiment.html', c))	
	
def search_quick(request):
	get = False
	experiments = Experiment.objects.all()
	experiments = Experiment.objects.order_by('title')

	experiments = Experiment.objects.filter(approved=True)

	if request.GET.has_key('results'):
		get = True
		if request.GET.has_key('quicksearch') and len(request.GET['quicksearch']) > 0:
			experiments = experiments.filter(title__icontains=request.GET['quicksearch']) | \
			experiments.filter(institution_name__icontains=request.GET['quicksearch']) | \
			experiments.filter(author_experiment__author__name__icontains=request.GET['quicksearch']) | \
			experiments.filter(pdbid__pdbid__icontains=request.GET['quicksearch'])
			
			experiments = experiments.distinct()

			print experiments

	c = Context({
		'submitted': get,
		'experiments': experiments,
		'subtitle': "Search Experiments",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/search_experiment.html', c))	
	
def search_datafile(request):
	get = False
	datafile_results = Dataset_File.objects.all()
	datafile_results = Dataset_File.objects.order_by('filename')

	datafile_results = Dataset_File.objects.filter(dataset__experiment__approved=True)	

	if request.GET.has_key('results'):
		get = True
		if request.GET.has_key('filename') and len(request.GET['filename']) > 0:
			datafile_results = datafile_results.filter(filename__icontains=request.GET['filename'])

		if request.GET.has_key('diffractometerType') and request.GET['diffractometerType'] != '-':
			datafile_results = datafile_results.filter(dataset__datasetparameter__name__name__icontains='diffractometerType', \
			dataset__datasetparameter__string_value__icontains=request.GET['diffractometerType'])
			
		if request.GET.has_key('xraySource') and len(request.GET['xraySource']) > 0:
			datafile_results = datafile_results.filter(dataset__datasetparameter__name__name__icontains='xraySource', \
			dataset__datasetparameter__string_value__icontains=request.GET['xraySource'])			
		
		if request.GET.has_key('crystalName') and len(request.GET['crystalName']) > 0:
			datafile_results = datafile_results.filter(dataset__datasetparameter__name__name__icontains='crystalName', \
			dataset__datasetparameter__string_value__icontains=request.GET['crystalName'])			

		if request.GET.has_key('resLimitTo') and len(request.GET['resLimitTo']) > 0:
			datafile_results = datafile_results.filter(datafileparameter__name__name__icontains='resolutionLimit', \
			datafileparameter__numerical_value__lte=request.GET['resLimitTo'])

		if request.GET.has_key('xrayWavelengthFrom') and len(request.GET['xrayWavelengthFrom']) > 0 and request.GET.has_key('xrayWavelengthTo') and len(request.GET['xrayWavelengthTo']) > 0:
			datafile_results = datafile_results.filter(datafileparameter__name__name__icontains='xrayWavelength', \
			datafileparameter__numerical_value__range=(request.GET['xrayWavelengthFrom'], \
			request.GET['xrayWavelengthTo']))	
			
	paginator = Paginator(datafile_results, 25)	
		
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1

	# If page request (9999) is out of range, deliver last page of results.
	try:
		datafiles = paginator.page(page)
	except (EmptyPage, InvalidPage):
		datafiles = paginator.page(paginator.num_pages)
				
	c = Context({
		'submitted': get,
		'datafiles': datafiles,
		'paginator': paginator,
		'query_string': request.META['QUERY_STRING'],
		'subtitle': "Search Datafiles",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/search_datafile.html', c))
	
@login_required()
def retrieve_user_list(request):

	users = User.objects.all().order_by('username')

	c = Context({
		'users': users,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/user_list.html', c))	
	
@experiment_ownership_required
def retrieve_access_list(request, experiment_id):

	users = User.objects.filter(groups__name=experiment_id).order_by('username')

	c = Context({
		'users': users,
		'experiment_id': experiment_id,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/access_list.html', c))
	
@experiment_ownership_required
def add_access_experiment(request, experiment_id, username):
	try:
		u = User.objects.get(username=username)

		g = Group.objects.get(name=experiment_id)

		if not in_group(u, g):
			u.groups.add(g)
			
			c = Context({
				'user': u,
				'experiment_id': experiment_id,
			})			
			return HttpResponse(render_response_index(request, 'tardis_portal/ajax/add_user_result.html', c))
		else:
			return return_response_error(request)

	except User.DoesNotExist, ue:
		return return_response_not_found(request)		
	except Group.DoesNotExist, ge:
		return return_response_not_found(request)

	return return_response_error(request)
	
@experiment_ownership_required
def remove_access_experiment(request, experiment_id, username):

	try:
		u = User.objects.get(username=username)

		g = Group.objects.get(name=experiment_id)
		
		e = Experiment.objects.get(pk=experiment_id)

		if in_group(u, g):
			u.groups.remove(g)		

			try:
				eo = Experiment_Owner.objects.filter(experiment=e, user=u)
				eo.delete()
			except User.DoesNotExist, ue:
				pass

			c = Context({
			})			
			return HttpResponse(render_response_index(request, 'tardis_portal/ajax/remove_user_result.html', c))
		else:
			return return_response_error(request)

	except User.DoesNotExist, ue:
		return return_response_not_found(request)		
	except Group.DoesNotExist, ge:
		return return_response_not_found(request)
	except Experiment.DoesNotExist, ge:
		return return_response_not_found(request)		

	return return_response_error(request)