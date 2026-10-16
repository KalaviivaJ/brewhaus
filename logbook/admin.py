from django.contrib import admin
from .models import Batch

from django.contrib import admin
from .models import Batch, UserProfile

admin.site.register(Batch)
admin.site.register(UserProfile)