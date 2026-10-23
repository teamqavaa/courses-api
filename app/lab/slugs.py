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
