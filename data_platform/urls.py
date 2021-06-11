from django.conf.urls import url
from django.urls import path

from data_manager.views import login, downloadRosstatFiles, get_data_for_charts, predict_values, \
    get_monitoring, create_rules, manage_rules, get_logs, create_mapping_period, create_mapping_region

urlpatterns = [
    path('', downloadRosstatFiles),
    url(r'^charts/', get_data_for_charts, name='charts'),
    url(r'^predict/', predict_values, name='predict'),
    url(r'^create_rule/', create_rules, name='rules'),
    url(r'^manage_rules/', manage_rules, name='rules'),
    url(r'^monitoring/', get_monitoring, name='monitoring'),
    url(r'^logs/', get_logs),
    url(r'^mapping_period/', create_mapping_period, name='mapping_period'),
    url(r'^mapping_region/', create_mapping_region, name='mapping_region'),
    url(r'^login/', login)
]
