from django.urls import path
from .views import receive_essay, generate_prompt

urlpatterns = [
    path('receive_essay', receive_essay, name='receive_essay'),
    path('generate_prompt', generate_prompt, name='generate_prompt'),
]
