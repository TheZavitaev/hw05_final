from django.forms import ModelForm, Textarea

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image') # почему в теории тут лист?


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        # labels = {
        #     'text': 'Комментарий'
        # }
        widgets = {
            'text': Textarea(attrs={'rows': 3}),
        }
