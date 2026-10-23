from django.db import migrations, models
from django.utils.text import slugify

SLUG_MAX_LENGTH = 255
FALLBACK_SLUG = 'lab'


def make_unique_slug(title, used_slugs):
    base = slugify(title or '')[:SLUG_MAX_LENGTH] or FALLBACK_SLUG
    candidate = base
    suffix = 2

    while candidate in used_slugs:
        suffix_text = f'-{suffix}'
        candidate = f'{base[:SLUG_MAX_LENGTH - len(suffix_text)]}{suffix_text}'
        suffix += 1

    return candidate


def backfill_lab_slugs(apps, schema_editor):
    Lab = apps.get_model('lab', 'Lab')
    database = schema_editor.connection.alias
    used_slugs = set(
        Lab.objects.using(database)
        .exclude(slug__isnull=True)
        .exclude(slug='')
        .values_list('slug', flat=True)
    )

    for lab in Lab.objects.using(database).order_by('created_at', 'id'):
        if lab.slug:
            continue
        lab.slug = make_unique_slug(lab.title, used_slugs)
        lab.save(using=database, update_fields=['slug'])
        used_slugs.add(lab.slug)


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lab',
            name='slug',
            field=models.SlugField(
                blank=True,
                db_index=False,
                max_length=255,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_lab_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='lab',
            name='slug',
            field=models.SlugField(max_length=255, unique=True, db_index=False),
        ),
    ]
