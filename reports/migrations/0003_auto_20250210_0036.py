from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

def set_default_user(apps, schema_editor):
    Comment = apps.get_model('reports', 'Comment')
    # Set any existing comments without a user to None
    for comment in Comment.objects.filter(user__isnull=True):
        comment.user = None  # Or you could assign a specific user
        comment.save()

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_auto_20250209_2331'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='auth.User'),
        ),
        migrations.RunPython(set_default_user, reverse_code=migrations.RunPython.noop),
        migrations.CreateModel(
            name='CommentView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=100)),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_view', to='reports.Issue')),
            ],
        ),
    ]
