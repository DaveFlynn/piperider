import json
import os
import sys
from glob import glob

import inquirer
from rich.console import Console
from rich.table import Table
from ruamel import yaml

from piperider_cli.error import DbtProjectInvalidError
from piperider_cli.metrics_engine import Metric
from piperider_cli.profiler import ProfileSubject

from piperider_cli.error import \
    DbtProjectInvalidError, \
    DbtProfileInvalidError, \
    DbtProfileBigQueryAuthWithTokenUnsupportedError

console = Console()


def search_dbt_project_path():
    exclude_patterns = ['site-packages', 'dbt_packages']
    _warning_if_search_path_too_widely(os.getcwd())
    paths = glob(os.path.join(os.getcwd(), '**', 'dbt_project.yml'), recursive=True)
    for exclude_pattern in exclude_patterns:
        paths = list(filter(lambda x: exclude_pattern not in x, paths))
    dbt_project_path = None
    if not paths:
        # No dbt project found
        return dbt_project_path

    if len(paths) == 1:
        # Only one dbt project found, use it
        dbt_project_path = paths[0]
    else:
        # Multiple dbt projects found, ask user to select one
        paths = sorted(paths, key=len)
        default_index = 0
        console.print(f'\nMultiple dbt projects found. Please select the dbt project: (Default: {default_index})')
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column('Index', style="bold", width=5, justify='right')
        table.add_column('Path', style="bold")
        for i, p in enumerate(paths):
            table.add_row(str(i), p)
        console.print(table)
        in_index = input('index : ').strip()
        try:
            in_index = int(in_index) if in_index else default_index
            index = int(in_index)
            dbt_project_path = paths[index]
        except Exception as e:
            console.print(f'[bold yellow]Failed to read index![/] Error: {e}')
            return None

    return dbt_project_path


def load_dbt_project(dbt_project_path):
    with open(dbt_project_path, 'r') as fd:
        try:
            yml = yaml.YAML()
            yml.allow_duplicate_keys = True
            dbt_project = yml.load(fd)
        except Exception as e:
            raise DbtProjectInvalidError(dbt_project_path, e)
    return dbt_project


def _warning_if_search_path_too_widely(search_path):
    # Only warning user on macOS platform
    if sys.platform != "darwin":
        return

    home_dir = os.path.expanduser('~')

    if search_path in home_dir:
        console.print(
            f"[[bold yellow]Warning[/bold yellow]] Search path '{search_path}' is too widely. It will take some time to parse directories and may need extra permissions.")
        if inquirer.confirm(message="Do you still want to keep going?", default=True) is not True:
            raise KeyboardInterrupt()


def is_ready(config):
    if not config.get('profile'):
        return False

    if not config.get('target'):
        return False

    if not config.get('projectDir'):
        return False

    if not os.path.expanduser(config.get('projectDir')):
        return False

    return True


def _is_dbt_file_existing(dbt_state_dir: str, filename: str):
    dbt_state_dir = os.path.abspath(dbt_state_dir)
    filepath = os.path.join(dbt_state_dir, filename)
    if not os.path.exists(filepath):
        return False
    return True


def is_dbt_state_ready(dbt_state_dir: str):
    return _is_dbt_file_existing(dbt_state_dir, 'manifest.json')


def is_dbt_run_results_ready(dbt_state_dir: str):
    return _is_dbt_file_existing(dbt_state_dir, 'run_results.json')


def _get_state_run_results(dbt_state_dir: str):
    path = os.path.join(dbt_state_dir, 'run_results.json')
    with open(path) as f:
        run_results = json.load(f)

    return run_results


def _get_state_manifest(dbt_state_dir: str):
    path = os.path.join(dbt_state_dir, 'manifest.json')
    with open(path) as f:
        manifest = json.load(f)

    return manifest


def append_descriptions(profile_result, dbt_state_dir):
    run_results = _get_state_run_results(dbt_state_dir)
    manifest = _get_state_manifest(dbt_state_dir)

    nodes = manifest.get('nodes')
    for result in run_results.get('results'):
        node = nodes.get(result.get('unique_id'))
        if node.get('resource_type') != 'model' and node.get('resource_type') != 'seed':
            continue

        model = node.get('name')
        model_desc = node.get('description')
        if model not in profile_result['tables']:
            continue
        if model_desc:
            profile_result['tables'][model]['description'] = f"{model_desc} - via DBT"

        columns = node.get('columns', {})
        for column, v in columns.items():
            if column not in profile_result['tables'][model]['columns']:
                continue
            column_desc = v.get('description')
            if column_desc:
                profile_result['tables'][model]['columns'][column]['description'] = f"{column_desc} - via DBT"


def get_dbt_state_candidate(dbt_state_dir: str, options: dict = None):
    candidate = []
    material_whitelist = ['seed', 'table', 'incremental']
    resource_whitelist = ['model']
    tag = options.get('tag') if options else None
    if options and options.get('view_profile'):
        material_whitelist.append('view')
    manifest = _get_state_manifest(dbt_state_dir)
    nodes = manifest.get('nodes')

    unique_ids = list(nodes.keys())
    if options and options.get('dbt_run_results'):
        run_results = _get_state_run_results(dbt_state_dir)
        run_results_ids = []
        for result in run_results.get('results'):
            if result.get('status') != 'success':
                continue
            run_results_ids.append(result.get('unique_id'))
        unique_ids = run_results_ids

    for unique_id in unique_ids:
        node = nodes.get(unique_id)
        if node.get('resource_type') not in resource_whitelist:
            continue
        if tag is not None and tag not in node.get('tags', []):
            continue
        config_material = node.get('config').get('materialized')
        if config_material in material_whitelist:
            candidate.append(node)

    return candidate


def get_dbt_state_tests_result(dbt_state_dir: str):
    output = []
    unique_tests = {}

    run_results = _get_state_run_results(dbt_state_dir)
    manifest = _get_state_manifest(dbt_state_dir)

    nodes = manifest.get('nodes')
    sources = manifest.get('sources')
    for result in run_results.get('results', []):
        unique_id = result.get('unique_id')

        node = nodes.get(unique_id)
        if node.get('resource_type') != 'test':
            continue

        unique_tests[unique_id] = dict(
            status=result.get('status'),
            failures=result.get('failures'),
            message=result.get('message'),
        )

        test_node = node
        table = None
        depends_on_nodes = test_node.get('depends_on', {}).get('nodes', [])
        for depends_on_node_id in depends_on_nodes:
            depends_on_node = nodes.get(depends_on_node_id)
            if depends_on_node_id.startswith('source'):
                source = sources.get(depends_on_node_id)
                table = f"{source.get('source_name')}.{source.get('name')}"
                break
            elif depends_on_node.get('resource_type') in ['model', 'seed']:
                table = depends_on_node.get('name')
                break
        column = test_node.get('column_name')

        if table is None:
            continue

        output.append(dict(
            id=unique_id,
            name=unique_id,
            table=table,
            column=column if column != test_node['name'] else None,
            status='failed' if unique_tests[unique_id]['status'] == 'fail' else 'passed',
            tags=[],
            message=unique_tests[unique_id]['message'],
            display_name=test_node['name'],
            source='dbt'
        ))

    return output


def get_dbt_state_metrics(dbt_state_dir: str, dbt_tag: str):
    manifest = _get_state_manifest(dbt_state_dir)

    metrics = []
    metric_map = {}
    for key, metric in manifest.get('metrics').items():
        if metric.get('calculation_method') == 'derived':
            table = None
            schema = None
            database = None
        else:
            depends_on_node = metric.get('depends_on').get('nodes')[0]
            table = manifest.get('nodes').get(depends_on_node).get('alias')
            schema = manifest.get('nodes').get(depends_on_node).get('schema')
            database = manifest.get('nodes').get(depends_on_node).get('database')

        m = Metric(metric.get('name'), table, schema, database, metric.get('expression'), metric.get('timestamp'),
                   metric.get('calculation_method'), metric.get('time_grains'), dimensions=None,
                   filters=metric.get('filters'), label=metric.get('label'), description=metric.get('description'))

        metric_map[key] = m
        if dbt_tag in metric.get('tags'):
            if metric.get('window'):
                console.print(
                    f"[[bold yellow]Warning[/bold yellow]] Skip metric '{metric.get('name')}'. Property 'window' is not supported.")
                continue
            metrics.append(m)

    for key, metric in metric_map.items():
        if metric.calculation_method == 'derived':
            for depends_on_metric in manifest.get('metrics').get(key).get('depends_on').get('nodes'):
                metric.ref_metrics.append(metric_map.get(depends_on_metric))

    return metrics


def load_dbt_project(path: str):
    if not path.endswith('dbt_project.yml'):
        path = os.path.join(path, 'dbt_project.yml')

    with open(path, 'r') as fd:
        try:
            yml = yaml.YAML()
            yml.allow_duplicate_keys = True
            return yml.load(fd)
        except Exception as e:
            raise DbtProjectInvalidError(path, e)


def load_dbt_profile(path):
    from jinja2 import Environment, FileSystemLoader

    def env_var(var, default=None):
        return os.getenv(var, default)

    def as_bool(var):
        return var.lower() in ('true', 'yes', '1')

    def as_number(var):
        if var.isnumeric():
            return int(var)
        return float(var)

    def as_text(var):
        return str(var)

    env = Environment(loader=FileSystemLoader(searchpath=os.path.dirname(path)))
    env.globals['env_var'] = env_var
    env.filters['as_bool'] = as_bool
    env.filters['as_number'] = as_number
    env.filters['as_text'] = as_text
    template = env.get_template(os.path.basename(path))
    try:
        yml = yaml.YAML()
        yml.allow_duplicate_keys = True
        return yml.load(template.render())
    except Exception as e:
        raise DbtProfileInvalidError(path, e)


def load_credential_from_dbt_profile(dbt_profile, profile_name, target_name):
    credential = dbt_profile.get(profile_name, {}).get('outputs', {}).get(target_name, {})

    if credential.get('type') == 'bigquery':
        # BigQuery Data Source
        from piperider_cli.datasource.bigquery import AUTH_METHOD_OAUTH_SECRETS
        # DBT profile support 4 types of methods to authenticate with BigQuery:
        #   [ 'oauth', 'oauth-secrets', 'service-account', 'service-account-json' ]
        # Ref: https://docs.getdbt.com/reference/warehouse-profiles/bigquery-profile#authentication-methods
        if credential.get('method') == 'oauth-secrets':
            credential['method'] = AUTH_METHOD_OAUTH_SECRETS
            # TODO: Currently SqlAlchemy haven't support using access token to authenticate with BigQuery.
            #       Ref: https://github.com/googleapis/python-bigquery-sqlalchemy/pull/459
            raise DbtProfileBigQueryAuthWithTokenUnsupportedError
    elif credential.get('type') == 'redshift':
        if credential.get('method') is None:
            credential['method'] = 'password'
        host = credential.get('host')
        port = credential.get('port')
        dbname = credential.get('dbname')
        credential['endpoint'] = f'{host}:{port}/{dbname}'
    return credential
