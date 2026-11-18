"""
Exécution de code avec Piston, appelable depuis le serveur (correction des questions de code des quiz).

La vue /api/execute/ (lab/views/execution.py) garde son propre appel HTTP : ce module ne la remplace pas.
Il réutilise la même URL (PISTON_URL) et les runtimes installés par infrastructure/piston/install-runtimes.sh
(les mêmes que contents-lab/lib/lab/languages.ts).
"""
import requests
from django.conf import settings

from lab.views.execution import _piston_url

# Runtimes installés dans le conteneur Piston : version et nom de fichier par langage
RUNTIMES = {
    'python': {'version': '3.12.0', 'filename': 'main.py'},
    'php': {'version': '8.2.3', 'filename': 'main.php'},
    'typescript': {'version': '5.0.3', 'filename': 'main.ts'},
}

# Durée maximale d'une exécution côté Piston (ms) et de la requête HTTP (s)
RUN_TIMEOUT_MS = 3000
DEFAULT_HTTP_TIMEOUT = 15


class PistonError(Exception):
    """Piston injoignable, en erreur, ou langage non pris en charge."""


def run_code(language, code, stdin='', timeout=None):
    """
    Exécute `code` avec l'entrée standard `stdin`.
    Retourne {'stdout', 'stderr', 'exit_code'} ; lève PistonError si l'exécution n'a pas pu avoir lieu.
    """
    runtime = RUNTIMES.get(language)
    if runtime is None:
        raise PistonError(f"Langage non pris en charge : {language}")

    payload = {
        'language': language,
        'version': runtime['version'],
        'files': [{'name': runtime['filename'], 'content': code}],
        'stdin': stdin or '',
        'run_timeout': RUN_TIMEOUT_MS,
    }
    http_timeout = timeout or getattr(settings, 'PISTON_TIMEOUT_SECONDS', DEFAULT_HTTP_TIMEOUT)
    try:
        response = requests.post(f'{_piston_url()}/api/v2/execute', json=payload, timeout=http_timeout)
    except requests.RequestException as error:
        raise PistonError("Service d'exécution de code injoignable.") from error

    if response.status_code >= 400:
        raise PistonError(f"Le service d'exécution a répondu {response.status_code}.")
    try:
        data = response.json()
    except ValueError as error:
        raise PistonError("Réponse inattendue du service d'exécution.") from error

    # Erreur de compilation (TypeScript) : pas d'exécution
    compile_step = data.get('compile') or {}
    if compile_step.get('code'):
        return {'stdout': '', 'stderr': compile_step.get('stderr') or compile_step.get('output', ''), 'exit_code': 1}

    run = data.get('run') or {}
    return {
        'stdout': run.get('stdout', ''),
        'stderr': run.get('stderr', ''),
        'exit_code': run.get('code'),
    }
