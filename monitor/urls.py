from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),  # Main dashboard page
    path("start-monitoring/", views.start_monitoring, name="start_monitoring"),  # Start monitoring
    path("stop-monitoring/", views.stop_monitoring, name="stop_monitoring"),  # Stop monitoring
    path("select-directory/", views.select_directory, name="select_directory"),  # Select directory to monitor
    path("select-log-directory/", views.select_log_directory, name="select_log_directory"),  # Select log directory
    path("get-logs/", views.get_logs, name="get_logs"),  # Fetch logs dynamically
    path("download-logs/", views.download_logs, name="download_logs"),  # Download logs
]