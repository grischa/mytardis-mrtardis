from django.contrib import admin
admin.autodiscover()
from django.contrib.auth.views import logout

from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic import list_detail

from tardis.tardis_portal.models import Equipment
from tardis.tardis_portal.views import getNewSearchDatafileSelectionForm

from tardis.tardis_portal.forms import RegistrationForm


urlpatterns = patterns(
    # (r'^search/quick/$', 'tardis.tardis_portal.views.search_quick'),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    '',
    (r'^$', 'tardis.tardis_portal.views.index'),
    (r'^site-settings.xml/$', 'tardis.tardis_portal.views.site_settings'),
    (r'^about/$', 'tardis.tardis_portal.views.about'),
    (r'^partners/$', 'tardis.tardis_portal.views.partners'),
    (r'^stats/$', 'tardis.tardis_portal.views.stats'),
    (r'^import_params/$', 'tardis.tardis_portal.views.import_params'),
    (r'^equipment/$', list_detail.object_list,
     {'queryset': Equipment.objects.all(),
      'paginate_by': 15,
      'extra_context':
      {'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()}}),
    (r'^equipment/(?P<object_id>\d+)/$', list_detail.object_detail,
     {'queryset': Equipment.objects.all()}),
    (r'^search/equipment/$',
     'tardis.tardis_portal.views.search_equipment'),
    (r'^experiment/view/(?P<experiment_id>\d+)/$',
     'tardis.tardis_portal.views.view_experiment'),
    (r'^experiment/edit/(?P<experiment_id>\d+)/$',
     'tardis.tardis_portal.views.edit_experiment'),
    (r'^experiment/view/$',
     'tardis.tardis_portal.views.experiment_index'),
    (r'^experiment/register/$',
     'tardis.tardis_portal.views.register_experiment_ws_xmldata'),
    (r'^experiment/register/internal/$',
     'tardis.tardis_portal.views.register_experiment_ws_xmldata_internal'),
    (r'^experiment/view/(?P<experiment_id>\d+)/publish/$',
     'tardis.tardis_portal.views.publish_experiment'),
    (r'^experiment/create/$',
     'tardis.tardis_portal.views.create_experiment'),
    (r'^search/experiment/$',
     'tardis.tardis_portal.views.search_experiment'),
    (r'^search/datafile/$',
     'tardis.tardis_portal.views.search_datafile'),
    (r'^download/datafile/(?P<datafile_id>\d+)/$',
     'tardis.tardis_portal.download.download_datafile'),
    #(r'^download/dataset/(?P<dataset_id>\d+)/$',
    # 'tardis.tardis_portal.download.download_dataset'),
    (r'^download/experiment/(?P<experiment_id>\d+)/$',
     'tardis.tardis_portal.download.download_experiment'),
    (r'^download/datafiles/$',
     'tardis.tardis_portal.download.download_datafiles'),
    (r'^displayExperimentImage/(?P<experiment_id>\d+)/'
     '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
     'tardis.tardis_portal.views.display_experiment_image'),
    (r'^displayDatasetImage/(?P<dataset_id>\d+)/(?P<parameterset_id>\d+)/'
     '(?P<parameter_name>\w+)/$',
     'tardis.tardis_portal.views.display_dataset_image'),
    (r'^displayDatafileImage/(?P<dataset_file_id>\d+)/'
     '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
     'tardis.tardis_portal.views.display_datafile_image'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/add/user/'
     '(?P<username>[\w\.]+)$', 'tardis.tardis_portal.views.add_experiment_access_user'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/remove/user/'
     '(?P<username>[\w\.]+)/$',
     'tardis.tardis_portal.views.remove_experiment_access_user'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/change/user/'
     '(?P<username>[\w\.]+)/$', 'tardis.tardis_portal.views.change_user_permissions'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/user/$',
     'tardis.tardis_portal.views.retrieve_access_list_user'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/add/group/'
     '(?P<groupname>[\w\s\.]+)$', 'tardis.tardis_portal.views.add_experiment_access_group'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/remove/group/'
     '(?P<group_id>\d+)/$',
     'tardis.tardis_portal.views.remove_experiment_access_group'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/change/group/'
     '(?P<group_id>\d+)/$', 'tardis.tardis_portal.views.change_group_permissions'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/group/$',
     'tardis.tardis_portal.views.retrieve_access_list_group'),
    (r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/external/$',
     'tardis.tardis_portal.views.retrieve_access_list_external'),
    (r'^experiment/control_panel/$',
     'tardis.tardis_portal.views.control_panel'),
    (r'^ajax/parameters/(?P<dataset_file_id>\d+)/$',
     'tardis.tardis_portal.views.retrieve_parameters'),
    (r'^ajax/xml_data/(?P<dataset_file_id>\d+)/$',
     'tardis.tardis_portal.views.retrieve_xml_data'),
    (r'^ajax/datafile_list/(?P<dataset_id>\d+)/$',
     'tardis.tardis_portal.views.retrieve_datafile_list'),
    (r'^ajax/user_list/$',
     'tardis.tardis_portal.views.retrieve_user_list'),
    (r'^ajax/group_list/$',
     'tardis.tardis_portal.views.retrieve_group_list'),
    (r'^groups/$', 'tardis.tardis_portal.views.manage_groups'),
    (r'^group/(?P<group_id>\d+)/$',
     'tardis.tardis_portal.views.retrieve_group_userlist'),
    (r'^group/(?P<group_id>\d+)/add/(?P<username>[\w\.]+)$',
     'tardis.tardis_portal.views.add_user_to_group'),
    (r'^group/(?P<group_id>\d+)/remove/(?P<username>[\w\.]+)/$',
     'tardis.tardis_portal.views.remove_user_from_group'),
    (r'^logout/$', logout, {'next_page': '/'}),
    (r'^login/$', 'tardis.tardis_portal.views.login'),
    (r'^accounts/login/$', 'tardis.tardis_portal.views.login'),
    (r'^accounts/manage_auth_methods/$',
     'tardis.tardis_portal.views.manage_auth_methods'),
    (r'^accounts/register/$', 'registration.views.register',
     {'form_class': RegistrationForm}),
    (r'^accounts/', include('registration.urls')),
    (r'site_media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_DOC_ROOT}),
    (r'media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.ADMIN_MEDIA_STATIC_DOC_ROOT}),
    (r'^admin/(.*)', admin.site.root),
    (r'^ajax/upload_complete/$',
     'tardis.tardis_portal.views.upload_complete'),
    (r'^upload/(?P<dataset_id>\d+)/$', 'tardis.tardis_portal.views.upload'),
    (r'^ajax/upload_files/(?P<dataset_id>\d+)/$',
     'tardis.tardis_portal.views.upload_files'),
)
