from django.contrib import admin

from .models import Student, Course, Lecture, Evaluation, TimeTable, TimeSlot, Classroom, College, Department, Major

admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Lecture)
admin.site.register(Evaluation)
admin.site.register(TimeTable)
admin.site.register(TimeSlot)
admin.site.register(Classroom)
admin.site.register(College)
admin.site.register(Department)
admin.site.register(Major)
