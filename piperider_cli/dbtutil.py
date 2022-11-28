import json
import os
import sys
from glob import glob

import inquirer
from rich.console import Console
from rich.table import Table

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


def is_dbt_state_ready(dbt_state_dir: str):
    dbt_state_dir = os.path.abspath(dbt_state_dir)
    run_results_path = os.path.join(dbt_state_dir, 'run_results.json')
    manifest_path = os.path.join(dbt_state_dir, 'manifest.json')
    if not os.path.exists(run_results_path) or not os.path.exists(manifest_path):
        return False
    return True


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


def append_descriptions(profile_result, dbt_state_dir, default_schema):
    run_results = _get_state_run_results(dbt_state_dir)
    manifest = _get_state_manifest(dbt_state_dir)

    nodes = manifest.get('nodes')
    for result in run_results.get('results'):
        node = nodes.get(result.get('unique_id'))
        if node.get('resource_type') != 'model' and node.get('resource_type') != 'seed':
            continue
        if node.get('schema') != default_schema:
            continue

        table = node.get('alias')
        table_desc = node.get('description')
        if table not in profile_result['tables']:
            continue
        if table_desc:
            profile_result['tables'][table]['description'] = f"{table_desc} - via DBT"

        columns = node.get('columns', {})
        for column, v in columns.items():
            if column not in profile_result['tables'][table]['columns']:
                continue
            column_desc = v.get('description')
            if column_desc:
                profile_result['tables'][table]['columns'][column]['description'] = f"{column_desc} - via DBT"


def get_dbt_state_candidate(dbt_state_dir: str, default_schema: str):
    candidate = []
    run_results = _get_state_run_results(dbt_state_dir)
    manifest = _get_state_manifest(dbt_state_dir)

    nodes = manifest.get('nodes')
    for result in run_results.get('results'):
        if result.get('status') != 'success':
            continue
        node = nodes.get(result.get('unique_id'))
        if node.get('resource_type') not in ['model', 'seed', 'source']:
            continue
        if node.get('schema') != default_schema:
            continue
        candidate.append(node.get('alias'))

    return candidate


def get_dbt_state_tests_result(dbt_state_dir: str, default_schema: str):
    output = []
    compatible_output = {}
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
            if depends_on_node is None:
                if depends_on_node_id.startswith('source'):
                    depends_on_node = sources.get(depends_on_node_id)
                else:
                    continue

            if depends_on_node.get('resource_type') not in ['model', 'seed', 'source']:
                continue
            if depends_on_node.get('schema') != default_schema:
                continue
            # 'alias' for model node and 'identifier' for source
            table = depends_on_node.get('alias') if depends_on_node.get('alias') else depends_on_node.get(
                'identifier')
            break
        column = test_node.get('column_name')

        if table is None:
            continue

        output.append(dict(
            id=unique_id,
            name=unique_id,
            table=table,
            column=column if column != test_node['name'] else None,
            status='passed' if unique_tests[unique_id]['status'] == 'pass' else 'failed',
            tags=[],
            message=unique_tests[unique_id]['message'],
            display_name=test_node['name'],
            source='dbt'
        ))

    return output
