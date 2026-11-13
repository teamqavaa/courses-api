import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0002_lab_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lab',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('review', 'Pending review'), ('published', 'Published')],
                default='draft',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='lab',
            name='user_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='lab',
            name='user_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='lab',
            name='author_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='lab',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
