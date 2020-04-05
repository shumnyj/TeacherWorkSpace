from django.contrib import admin
# from .models import SGroup, Student, Teacher, Attendance, ControlCategory,ControlEntity

import workspace.models as wsm

admin.site.register(wsm.SGroup)
admin.site.register(wsm.Student)
admin.site.register(wsm.Teacher)
admin.site.register(wsm.Discipline)
admin.site.register(wsm.ControlCategory)
admin.site.register(wsm.ControlEntity)
admin.site.register(wsm.Location)
admin.site.register(wsm.Lesson)
admin.site.register(wsm.Attendance)
admin.site.register(wsm.Mark)

