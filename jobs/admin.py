from django.contrib import admin

# Register your models here.
from jobs.models import JobLog, JobStatus

admin.site.register(JobLog)
admin.site.register(JobStatus)
