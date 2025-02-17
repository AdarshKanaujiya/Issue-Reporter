from django import forms
from .models import Issue, Comment

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['title', 'description', 'category', 'location', 'image', 'lat', 'lng']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
