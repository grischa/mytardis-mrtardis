from django.conf.urls.defaults import patterns

urlpatterns = patterns('tardis.apps.mrtardis.views',
                       (r'^index/(?P<experiment_id>\d+)/$',
                        'index'),
                       (r'^test_user_setup/(?P<experiment_id>\d+)/$',
                        'test_user_setup'),
                       )
