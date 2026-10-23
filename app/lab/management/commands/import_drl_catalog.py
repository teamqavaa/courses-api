import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from lab.models import Lab, LabObjective, Skill, SkillOutcome, SkillPrerequisite
from lab.slugs import make_unique_slug

CATALOG_MODELS = {
    'lab.skill',
    'lab.skilloutcome',
    'lab.skillprerequisite',
    'lab.lab',
    'lab.labobjective',
}


class Command(BaseCommand):
    help = 'Import a DRL catalog dump without importing sessions, progress, or users.'

    def add_arguments(self, parser):
        parser.add_argument('path', type=Path, help='Path to the DRL catalog JSON fixture.')
        parser.add_argument(
            '--database',
            default='default',
            help='Database alias to import into.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate the fixture and report counts without writing.',
        )

    def handle(self, *args, **options):
        path = options['path']
        if not path.is_file():
            raise CommandError(f'Fixture not found: {path}')

        try:
            with path.open(encoding='utf-8') as fixture:
                objects = json.load(fixture)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f'Could not read fixture: {exc}')

        if not isinstance(objects, list):
            raise CommandError('Expected a Django JSON fixture containing a list.')

        models = {item.get('model') for item in objects if isinstance(item, dict)}
        unexpected = models - CATALOG_MODELS
        if unexpected:
            raise CommandError(
                'Fixture contains non-catalog models: ' + ', '.join(sorted(unexpected))
            )

        counts = {}
        for item in objects:
            model = item.get('model')
            counts[model] = counts.get(model, 0) + 1

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('Fixture is valid (dry run).'))
        else:
            database = options['database']
            existing_slugs = {
                str(lab.pk): lab.slug
                for lab in Lab.objects.using(database).all()
            }
            used_slugs = {slug for slug in existing_slugs.values() if slug}

            for item in objects:
                if not isinstance(item, dict) or item.get('model') != 'lab.lab':
                    continue
                fields = item.setdefault('fields', {})
                pk = str(item.get('pk'))
                existing_slug = existing_slugs.get(pk)
                slug = fields.get('slug') or existing_slug

                if not slug:
                    slug = make_unique_slug(fields.get('title', ''), used_slugs)
                elif slug in used_slugs and slug != existing_slug:
                    slug = make_unique_slug(slug, used_slugs)

                fields['slug'] = slug
                used_slugs.add(slug)

            with tempfile.TemporaryDirectory() as tmpdir:
                fixture_path = Path(tmpdir) / 'catalog-with-slugs.json'
                fixture_path.write_text(
                    json.dumps(objects, ensure_ascii=False),
                    encoding='utf-8',
                )
                call_command(
                    'loaddata',
                    str(fixture_path),
                    database=database,
                    verbosity=options.get('verbosity', 1),
                )
            self.stdout.write(self.style.SUCCESS('Catalog import complete.'))

        self.stdout.write(
            'Imported: '
            f'{counts.get("lab.skill", 0)} skills, '
            f'{counts.get("lab.skilloutcome", 0)} skill outcomes, '
            f'{counts.get("lab.skillprerequisite", 0)} prerequisites, '
            f'{counts.get("lab.lab", 0)} labs, '
            f'{counts.get("lab.labobjective", 0)} lab objectives.'
        )
        self.stdout.write(
            f'Current totals: {Skill.objects.count()} skills, '
            f'{SkillOutcome.objects.count()} outcomes, '
            f'{SkillPrerequisite.objects.count()} prerequisites, '
            f'{Lab.objects.count()} labs, '
            f'{LabObjective.objects.count()} objectives.'
        )
