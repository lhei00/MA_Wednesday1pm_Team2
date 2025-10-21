from django.urls import path
from . import views


urlpatterns = [
    path("", views.classrooms, name="classrooms"),
    path("create/", views.create_classroom, name="create_classroom"),
    path('classrooms/<int:classroom_id>/preview/', views.classroom_preview, name='classroom_preview'),

    path("manage/<int:classroom_id>/", views.manage_classroom, name="manage_classroom"),
    path("classrooms/<int:classroom_id>/delete/", views.delete_classroom, name="delete_classroom"),  
]
