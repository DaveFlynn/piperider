import json
import os
import re
import sys
import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, inspect

from piperider_cli import clone_directory, convert_to_tzlocal, datetime_to_str, dbt_adapter
from piperider_cli.assertion_engine import AssertionEngine, ValidationResult
from piperider_cli.assertion_engine.recommender import RECOMMENDED_ASSERTION_TAG
from piperider_cli.compare_report import CompareReport
from piperider_cli.configuration import Configuration, PIPERIDER_WORKSPACE_NAME, PIPERIDER_CONFIG_PATH, \
    PIPERIDER_CREDENTIALS_PATH
from piperider_cli.datasource import DataSource
from piperider_cli.error import PipeRiderCredentialError, PipeRiderDiagnosticError, \
    PipeRiderNoProfilingResultError
from piperider_cli.profiler import Profiler

PIPERIDER_OUTPUT_PATH = os.path.join(os.getcwd(), PIPERIDER_WORKSPACE_NAME, 'outputs')
PIPERIDER_REPORT_PATH = os.path.join(os.getcwd(), PIPERIDER_WORKSPACE_NAME, 'reports')
PIPERIDER_COMPARISON_PATH = os.path.join(os.getcwd(), PIPERIDER_WORKSPACE_NAME, 'comparisons')

CONSOLE_MSG_PASS = '[bold green]✅ PASS[/bold green]\n'
CONSOLE_MSG_FAIL = '[bold red]😱 FAILED[/bold red]\n'
CONSOLE_MSG_ALL_SET = '[bold]🎉 You are all set![/bold]\n'


class AbstractChecker(metaclass=ABCMeta):
    console = Console()

    @abstractmethod
    def check_function(self, configurator: Configuration) -> (bool, str):
        pass


class CheckingHandler(object):
    def __init__(self):
        self.configurator = None
        self.checker_chain = []
        self.console = Console()

    def set_checker(self, name: str, checker: AbstractChecker):
        self.checker_chain.append({'name': name, 'cls': checker()})

    def execute(self):
        try:
            if not self.configurator:
                try:
                    self.configurator = Configuration.load()
                except Exception:
                    pass

            for checker in self.checker_chain:
                self.console.print(f'Check {checker["name"]}:')
                passed, error_msg = checker['cls'].check_function(self.configurator)
                if not passed:
                    raise PipeRiderDiagnosticError(checker['cls'].__class__.__name__, error_msg)
                self.console.print(CONSOLE_MSG_PASS)

            self.console.print(CONSOLE_MSG_ALL_SET)
        except Exception as e:
            self.console.print(CONSOLE_MSG_FAIL)
            raise e
        return True


class CheckConfiguration(AbstractChecker):
    def check_function(self, configurator: Configuration) -> (bool, str):
        if not configurator:
            self.console.print(f'  {PIPERIDER_CONFIG_PATH}: [[bold red]FAILED[/bold red]]')
            return False, 'No configuration found'
        self.console.print(f'  {PIPERIDER_CONFIG_PATH}: [[bold green]OK[/bold green]]')
        return True, ''


class CheckDataSources(AbstractChecker):
    def check_function(self, configurator: Configuration) -> (bool, str):
        all_passed = True
        for ds in configurator.dataSources:
            passed, reasons = ds.validate()
            if passed:
                self.console.print(f'  {ds.name}: [[bold green]OK[/bold green]]')
            else:
                all_passed = False
                self.console.print(f'  {ds.name}: [[bold red]FAILED[/bold red]]')
                for reason in reasons:
                    self.console.print(f'    {reason}')
            ds.show_installation_information()
        return all_passed, ''


class CheckConnections(AbstractChecker):
    def check_function(self, configurator: Configuration) -> (bool, str):
        all_passed = True
        for ds in configurator.dataSources:
            dbt = ds.args.get('dbt')
            name = ds.name
            type = ds.type_name

            if dbt:  # dbt provider
                self.console.print(f'  DBT: {ds.type_name} > {dbt["profile"]} > {dbt["target"]}')

            self.console.print(f'  Name: {name}')
            self.console.print(f'  Type: {type}')

            engine = None
            try:
                engine = create_engine(ds.to_database_url(), **ds.engine_args())
                self.console.print(f'  Available Tables: {inspect(engine).get_table_names()}')
                self.console.print('  Connection: [[bold green]OK[/bold green]]')
            except Exception as e:
                self.console.print(f'  Connection: [[bold red]FAILED[/bold red]] reason: {e}')
                all_passed = False
            finally:
                if engine:
                    engine.dispose()

        return all_passed, ''


class CheckAssertionFiles(AbstractChecker):
    def check_function(self, configurator: Configuration) -> (bool, str):
        engine = AssertionEngine(None)
        passed_files, failed_files = engine.load_all_assertions_for_validation()
        results: List[ValidationResult] = engine.validate_assertions()

        for file in passed_files:
            self.console.print(f'  {file}: [[bold green]OK[/bold green]]')

        for file in failed_files:
            self.console.print(f'  {file}: [[bold red]FAILED[/bold red]]')

        newline_section = False
        validate_fail = False
        error_msg = ''
        for result in results:
            if result.has_errors():
                if not newline_section:
                    self.console.line()
                    newline_section = True
                self.console.print(f'  [[bold red]FAILED[/bold red]] {result.as_user_report()}')
                validate_fail = True

        if validate_fail or len(failed_files):
            error_msg = 'Syntax problem of PipeRider assertion yaml files'
            self.console.line()

        return error_msg == '', error_msg


def _is_piperider_workspace_exist(workspace_path: str) -> bool:
    if not os.path.exists(workspace_path):
        return False
    elif not os.path.exists(os.path.join(workspace_path, 'config.yml')):
        return False

    return True


def _generate_piperider_workspace() -> bool:
    from piperider_cli import data
    init_template_dir = os.path.join(os.path.dirname(data.__file__), 'piperider-init-template')
    working_dir = os.path.join(os.getcwd(), PIPERIDER_WORKSPACE_NAME)

    if _is_piperider_workspace_exist(working_dir) is False:
        clone_directory(init_template_dir, working_dir)
        # prepare .gitignore file
        os.rename(os.path.join(working_dir, 'gitignore'), os.path.join(working_dir, '.gitignore'))
        return True
    else:
        # Skip if workspace already exists
        return False


def _ask_user_update_credentials(ds: DataSource):
    console = Console()
    console.print(f'\nPlease enter the following fields for {ds.type_name}')
    return ds.ask_credential()


def _ask_user_input_datasource(config: Configuration = None):
    console = Console()
    if config is None:
        cls, name = DataSource.ask()
        ds: DataSource = cls(name=name)
        config = Configuration([ds])
        if _ask_user_update_credentials(ds):
            config.dump(PIPERIDER_CONFIG_PATH)
            config.dump_credentials(PIPERIDER_CREDENTIALS_PATH)
    else:
        if len(config.dataSources) == 1:
            ds = config.dataSources[0]
        else:
            ds = config.ask_for_datasource()
        if not ds.credential:
            console.print(
                f'[[bold yellow]Warning[/bold yellow]] No credential found for \'{ds.type_name}\' datasource \'{ds.name}\'')
            if _ask_user_update_credentials(ds):
                config.dump_credentials(PIPERIDER_CREDENTIALS_PATH)

    ds.show_installation_information()
    return config


def _inherit_datasource_from_dbt_project(dbt_project_path, dbt_profiles_dir=None,
                                         config: Configuration = None) -> bool:
    config = Configuration.from_dbt_project(dbt_project_path, dbt_profiles_dir)
    config.dump(PIPERIDER_CONFIG_PATH)

    return config


def _generate_configuration(dbt_project_path=None, dbt_profiles_dir=None):
    """
    :param dbt_project_path:
    :return: Configuration object
    """
    try:
        config = Configuration.load()
    except Exception:
        config = None
    if dbt_project_path is None:
        return _ask_user_input_datasource(config=config)

    return _inherit_datasource_from_dbt_project(dbt_project_path, dbt_profiles_dir)


def init(dbt_project_path=None, dbt_profiles_dir=None):
    console = Console()
    if _generate_piperider_workspace() is False:
        console.print('[bold green]Piperider workspace already exist[/bold green] ')

    # get Configuration object from dbt or user created configuration
    configuration = _generate_configuration(dbt_project_path, dbt_profiles_dir)
    return configuration


def debug():
    handler = CheckingHandler()
    handler.set_checker('config files', CheckConfiguration)
    handler.set_checker('format of data sources', CheckDataSources)
    handler.set_checker('connections', CheckConnections)
    handler.set_checker('assertion files', CheckAssertionFiles)
    return handler.execute()


def _agreed_to_run_recommended_assertions(console: Console, interactive: bool):
    if interactive:
        console.print('Please press enter to continue ...',
                      end=' ')
        confirm = input('').strip().lower()
        return confirm == 'yes' or confirm == 'y' or confirm == ''  # default yes
    else:
        return True


def _agreed_to_generate_recommended_assertions(console: Console, interactive: bool, skip_recommend: bool):
    if skip_recommend:
        return False

    if interactive:
        console.print('Do you want to auto generate recommended assertions for this datasource \[Yes/no]?',
                      end=' ')
        confirm = input('').strip().lower()
        return confirm == 'yes' or confirm == 'y' or confirm == ''  # default yes
    else:
        return True


def _execute_assertions(console: Console, profiler, ds: DataSource, interaction: bool,
                        output, result, created_at, skip_recommend: bool):
    # TODO: Implement running test cases based on profiling result
    assertion_engine = AssertionEngine(profiler)
    assertion_engine.load_assertions(result)
    assertion_exist = True if assertion_engine.assertions_content else False

    if not assertion_exist:
        console.print('[bold yellow]No assertion found[/]')
        if _agreed_to_generate_recommended_assertions(console, interaction, skip_recommend):
            # Generate recommended assertions
            console.rule('Generating Recommended Assertions')
            recommended_assertions = assertion_engine.generate_recommended_assertions(result)
            for f in recommended_assertions:
                console.print(f'[bold green]Recommended Assertion[/bold green]: {f}')
            if _agreed_to_run_recommended_assertions(console, interaction):
                assertion_engine.load_assertions()
            else:
                console.print(f'[[bold yellow]Skip[/bold yellow]] Executing assertion for datasource [ {ds.name} ]')
                return [], []
        else:
            # Generate assertion templates
            console.rule('Generating Assertion Templates')
            template_assertions = assertion_engine.generate_template_assertions(result)
            for f in template_assertions:
                console.print(f'[bold green]Template Assertion[/bold green]: {f}')

    # Execute assertions
    results, exceptions = assertion_engine.evaluate_all(result)
    return results, exceptions


def _show_dbt_test_result(console: Console, dbt_test_results, failed_only=False):
    max_target_len = 0
    max_assert_len = 0
    indent = '  ' if failed_only else ''
    for table, v in dbt_test_results.items():
        for column, results in v['columns'].items():
            for r in results:
                if failed_only and r.get('status') == 'passed':
                    continue
                target = f'{table}.{column}'
                test_name = r.get('name')
                max_target_len = max(max_target_len, len(target))
                max_assert_len = max(max_assert_len, len(test_name))

    for table, v in dbt_test_results.items():
        for column, results in v['columns'].items():
            for r in results:
                if failed_only and r.get('status') == 'passed':
                    continue
                success = True if r.get('status') == 'passed' else False
                test_name = r.get('name')
                test_name = test_name.ljust(max_assert_len + 1)
                target = f'{table}.{column}'
                target = target.ljust(max_target_len + 1)
                message = r.get('message')

                if success:
                    console.print(
                        f'{indent}[[bold green]  OK  [/bold green]] {target} {test_name} Message: {message}')
                else:
                    console.print(
                        f'{indent}[[bold red]FAILED[/bold red]] {target} {test_name} Message: {message}')


def _show_assertion_result(console: Console, results, exceptions, failed_only=False, single_table=None):
    if results:
        max_target_len = 0
        max_assert_len = 0
        indent = '  ' if failed_only else ''
        for assertion in results:
            if single_table and single_table != assertion.table:
                continue
            if assertion.column:
                if failed_only and assertion.result.status():
                    continue
                target = f'{assertion.table}.{assertion.column}'
                max_target_len = max(max_target_len, len(target))
            max_assert_len = max(max_assert_len, len(assertion.name))

        for assertion in results:
            if single_table and single_table != assertion.table:
                continue
            if failed_only and assertion.result.status():
                continue
            table = assertion.table
            column = assertion.column
            test_function = assertion.name
            test_function = test_function.ljust(max_assert_len + 1)
            success = assertion.result.status()
            target = f'{table}.{column}' if column else table
            target = target.ljust(max_target_len + 1)
            if success:
                console.print(
                    f'{indent}[[bold green]  OK  [/bold green]] {target} {test_function} Expected: {assertion.result.expected()} Actual: {assertion.result.actual}')
            else:
                console.print(
                    f'{indent}[[bold red]FAILED[/bold red]] {target} {test_function} Expected: {assertion.result.expected()} Actual: {assertion.result.actual}')
                if assertion.result.exception:
                    console.print(f'         {indent}[bold white]Reason[/bold white]: {assertion.result.exception}')
    # TODO: Handle exceptions
    pass


def _show_recommended_assertion_notice_message(console: Console, results):
    for assertion in results:
        if assertion.result.status() is False and RECOMMENDED_ASSERTION_TAG in assertion.tags:
            console.print(
                f'\n[[bold yellow]Notice[/bold yellow]] You can use command '
                f'"{os.path.basename(sys.argv[0])} generate-assertions" '
                f'to re-generate recommended assertions with new profiling results.')
            break


def _show_dbt_test_result_summary(console: Console, table: str, dbt_test_results):
    if not dbt_test_results:
        return False

    num_of_testcases = 0
    num_of_passed_testcases = 0
    num_of_failed_testcases = 0

    for k, v in dbt_test_results.items():
        if k == table:
            for column, results in v['columns'].items():
                for r in results:
                    num_of_testcases += 1
                    if r.get('status') == 'passed':
                        num_of_passed_testcases += 1

            num_of_failed_testcases = num_of_testcases - num_of_passed_testcases
            if num_of_testcases > 0:
                console.print(f'  {num_of_testcases} dbt test executed')

            if (num_of_failed_testcases > 0):
                console.print(f'  {num_of_failed_testcases} of {num_of_testcases} dbt tests failed:')
                _show_dbt_test_result(console, {k: v}, failed_only=True)
                return True
    return False


def _show_table_summary(console: Console, table: str, profiled_result, assertion_results, dbt_test_results):
    profiled_columns = profiled_result.get('col_count')
    num_of_testcases = 0
    num_of_passed_testcases = 0
    num_of_failed_testcases = 0
    failed_testcases = []

    if assertion_results:
        for r in assertion_results:
            if r.table == table:
                num_of_testcases += 1
                if r.result.status():
                    num_of_passed_testcases += 1
                else:
                    failed_testcases.append(r)

    num_of_failed_testcases = num_of_testcases - num_of_passed_testcases

    console.print(f"Table '{table}'")
    console.print(f'  {profiled_columns} columns profiled')

    dbt_showed = _show_dbt_test_result_summary(console, table, dbt_test_results)
    pr = ' PipeRider' if dbt_showed else ''
    if assertion_results and dbt_showed:
        console.print()

    if num_of_testcases > 0:
        console.print(f'  {num_of_testcases}{pr} test executed')

    if (num_of_failed_testcases > 0):
        console.print(f'  {num_of_failed_testcases} of {num_of_testcases}{pr} tests failed:')
        _show_assertion_result(console, assertion_results, None, failed_only=True, single_table=table)
    console.print()
    pass


def _transform_assertion_result(table: str, results):
    tests = []
    columns = {}
    if results is None:
        return dict(tests=tests, columns=columns)

    for r in results:
        if r.table == table:
            entry = r.to_result_entry()
            if r.column:
                if r.column not in columns:
                    columns[r.column] = []
                columns[r.column].append(entry)
            else:
                tests.append(entry)

    return dict(tests=tests, columns=columns)


def _validate_assertions(console: Console):
    assertion_engine = AssertionEngine(None)
    assertion_engine.load_all_assertions_for_validation()
    results = assertion_engine.validate_assertions()
    # if results
    for result in results:
        # result
        console.print(f'  [[bold red]FAILED[/bold red]] {result.as_user_report()}')

    if results:
        # stop runner
        return True

    # continue to run profiling
    console.print('everything is OK.')
    return False


def run(datasource=None, table=None, output=None, interaction=True, skip_report=False, dbt_command='',
        skip_recommend=False):
    console = Console()
    configuration = Configuration.load()

    datasources = {}
    datasource_names = []
    for ds in configuration.dataSources:
        datasource_names.append(ds.name)
        datasources[ds.name] = ds

    if len(datasource_names) == 0:
        console.print("[bold red]Error: no datasource found[/bold red]")
        return 1

    if datasource and datasource not in datasource_names:
        console.print(f"[bold red]Error: datasource '{datasource}' doesn't exist[/bold red]")
        console.print(f"Available datasources: {', '.join(datasource_names)}")
        return 1

    # Use the first datasource if no datasource is specified
    ds_name = datasource if datasource else datasource_names[0]
    ds = datasources[ds_name]

    passed, _ = ds.validate()
    if passed is not True:
        raise PipeRiderCredentialError(ds.name)

    if not datasource and len(datasource_names) > 1:
        console.print(
            f"[bold yellow]Warning: multiple datasources found ({', '.join(datasource_names)}), using '{ds_name}'[/bold yellow]\n")

    console.print(f'[bold dark_orange]DataSource:[/bold dark_orange] {ds.name}')

    if ds.show_installation_information() is False:
        console.print(f'[[bold red]FAILED[/bold red]] Failed to load the \'{ds.type_name}\' connector')
        return 1

    console.rule('Validating')
    stop_runner = _validate_assertions(console)
    if stop_runner:
        console.print('\n\n[bold red]ERROR:[/bold red] Stop profiling, please fix the syntax errors above.')
        return 1

    default_schema = ds.credential.get('schema')
    dbt = ds.args.get('dbt')
    dbt_exists = dbt_adapter._check_dbt_command(dbt)
    if dbt_command and not dbt_exists:
        console.print(f'[bold yellow]Warning: dbt command not found. Skip running dbt {dbt_command}.[/bold yellow]')

    if dbt and dbt_exists:
        dbt['resources'] = dbt_adapter._list_dbt_resources(dbt)
    tables = _get_table_list(table, default_schema, dbt)

    dbt_test_results = None
    if dbt and dbt_command in ['build', 'test'] and dbt_exists:
        dbt['cmd'] = dbt_command
        dbt_test_results = dbt_adapter._run_dbt_command(table, default_schema, dbt)

    console.rule('Profiling')
    run_id = uuid.uuid4().hex
    created_at = datetime.utcnow()
    engine = create_engine(ds.to_database_url(), **ds.engine_args())
    profiler = Profiler(engine)
    profile_result = profiler.profile(tables)

    output_path = prepare_output_path(created_at, ds, output)

    # output profiling result
    with open(os.path.join(output_path, ".profiler.json"), "w") as f:
        f.write(json.dumps(profile_result))

    # TODO stop here if tests was not needed.
    assertion_results, assertion_exceptions = _execute_assertions(console, profiler, ds, interaction, output,
                                                                  profile_result, created_at, skip_recommend)
    if assertion_results or dbt_test_results:
        console.rule('Assertion Results')
        if dbt_test_results:
            console.rule('dbt')
            _show_dbt_test_result(console, dbt_test_results)
            if assertion_results:
                console.rule('PipeRider')
        if assertion_results:
            _show_assertion_result(console, assertion_results, assertion_exceptions)

    console.rule('Summary')

    profile_result['id'] = run_id
    profile_result['created_at'] = datetime_to_str(created_at)
    profile_result['datasource'] = dict(name=ds.name, type=ds.type_name)

    # Include dbt test results
    if dbt_test_results:
        for k, v in dbt_test_results.items():
            if k not in profile_result['tables']:
                continue
            profile_result['tables'][k]['dbt_assertion_result'] = v

    output_file = os.path.join(output_path, 'run.json')
    for t in profile_result['tables']:
        profile_result['tables'][t]['piperider_assertion_result'] = _transform_assertion_result(t, assertion_results)

        _show_table_summary(console, t, profile_result['tables'][t], assertion_results, dbt_test_results)

    _show_recommended_assertion_notice_message(console, assertion_results)

    _append_descriptions(profile_result)
    if dbt and dbt_exists:
        dbt_adapter._append_descriptions_from_dbt(profile_result, dbt, default_schema)
    _append_descriptions_from_assertion(profile_result)

    with open(output_file, 'w') as f:
        f.write(json.dumps(profile_result, indent=4))
    if skip_report:
        console.print(f'Results saved to {output_path}')
    return 0


def _get_table_list(table, default_schema, dbt):
    tables = None

    if table:
        table = re.sub(f'^({default_schema})\.', '', table)
        tables = [table]

    if dbt:
        dbt_tables = dbt_adapter._list_dbt_tables(dbt, default_schema)
        if not dbt_tables:
            raise Exception('No table found in dbt project.')

        if not table:
            tables = dbt_tables
        elif table not in dbt_tables:
            suggestion = ''
            lower_tables = [t.lower() for t in dbt_tables]
            if table.lower() in lower_tables:
                index = lower_tables.index(table.lower())
                suggestion = f"Do you mean '{dbt_tables[index]}'?"
            raise Exception(f"Table '{table}' doesn't exist in dbt project. {suggestion}")

    return tables


def prepare_output_path(created_at, ds, output):
    latest_symlink_path = os.path.join(PIPERIDER_OUTPUT_PATH, 'latest')
    output_path = os.path.join(PIPERIDER_OUTPUT_PATH,
                               f"{ds.name}-{convert_to_tzlocal(created_at).strftime('%Y%m%d%H%M%S')}")
    if output:
        output_path = output
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    # Create a symlink pointing to the latest output directory
    if os.path.islink(latest_symlink_path):
        os.unlink(latest_symlink_path)
    if not os.path.exists(latest_symlink_path):
        os.symlink(output_path, latest_symlink_path)
    else:
        console = Console()
        console.print(f'[bold yellow]Warning: {latest_symlink_path} already exists[/bold yellow]')

    return output_path


def _validate_input_result(result):
    for f in ['tables', 'id', 'created_at', 'datasource']:
        if f not in result:
            return False
    return True


def setup_report_variables(template_html: str, is_single: bool, data):
    if isinstance(data, dict):
        output = json.dumps(data)
    else:
        output = data
    if is_single:
        variables = f'<script id="piperider-report-variables">\nwindow.PIPERIDER_SINGLE_REPORT_DATA={output};window.PIPERIDER_COMPARISON_REPORT_DATA="";</script>'
    else:
        variables = f'<script id="piperider-report-variables">\nwindow.PIPERIDER_SINGLE_REPORT_DATA="";window.PIPERIDER_COMPARISON_REPORT_DATA={output};</script>'
    html_parts = re.sub(r'<script id="piperider-report-variables">.+?</script>', '#PLACEHOLDER#', template_html).split(
        '#PLACEHOLDER#')
    html = html_parts[0] + variables + html_parts[1]
    return html


def _generate_static_html(result, html, output_path):
    filename = os.path.join(output_path, "index.html")
    with open(filename, 'w') as f:
        html = setup_report_variables(html, True, result)
        f.write(html)


def _get_run_json_path(input=None):
    console = Console()
    run_json = None
    if input:
        if not os.path.exists(input):
            console.print(f'[bold red]Error: {input} not found[/bold red]')
            return
        if os.path.isdir(input):
            run_json = os.path.join(input, 'run.json')
        else:
            run_json = input
    else:
        latest = os.path.join(PIPERIDER_OUTPUT_PATH, 'latest')
        run_json = os.path.join(latest, 'run.json')
    return run_json


def generate_recommended_assertions(input=None, interaction=True):
    console = Console()

    run_json_path = _get_run_json_path(input)
    if not os.path.isfile(run_json_path):
        raise PipeRiderNoProfilingResultError(run_json_path)

    with open(run_json_path) as f:
        profiling_result = json.loads(f.read())
    if not _validate_input_result(profiling_result):
        console.print(f'[bold red]Error: {run_json_path} is invalid[/bold red]')
        return
    console.print(f'[bold dark_orange]Generating recommended assertions from:[/bold dark_orange] {run_json_path}')

    # Generate recommended assertions
    assertion_engine = AssertionEngine(None)
    assertion_engine.load_assertions(profiling_result=profiling_result)
    assertion_exist = True if assertion_engine.assertions_content else False
    console.rule('Generating Recommended Assertions')
    recommended_assertions = assertion_engine.generate_recommended_assertions(profiling_result,
                                                                              assertion_exist=assertion_exist)
    # Show the generated recommended assertions
    ascii_table = Table(show_header=True, header_style="bold magenta")
    ascii_table.add_column('Table Name', style="bold yellow")
    ascii_table.add_column('Column Name', style="bold blue")
    ascii_table.add_column('Test Function', style="bold green")
    ascii_table.add_column('Asserts', style="bold")

    for assertion in assertion_engine.recommender.generated_assertions:
        assert_values = str(assertion.asserts) if assertion.asserts else ''
        ascii_table.add_row(
            assertion.table,
            assertion.column,
            assertion.name,
            assert_values,
        )

    console.print(ascii_table)

    # Show the recommended assertions files
    console.rule('Generated Recommended Assertions')
    for f in recommended_assertions:
        console.print(f'[bold green]Recommended Assertion[/bold green]: {f}')
    pass


def generate_report(input=None):
    console = Console()

    from piperider_cli import data
    report_template_dir = os.path.join(os.path.dirname(data.__file__), 'report', 'single-report')
    with open(os.path.join(report_template_dir, 'index.html')) as f:
        report_template_html = f.read()

    run_json_path = _get_run_json_path(input)
    if not os.path.isfile(run_json_path):
        raise PipeRiderNoProfilingResultError(run_json_path)

    with open(run_json_path) as f:
        result = json.loads(f.read())
    if not _validate_input_result(result):
        console.print(f'[bold red]Error: {run_json_path} is invalid[/bold red]')
        return

    console.print(f'[bold dark_orange]Generating reports from:[/bold dark_orange] {run_json_path}')

    dir = os.path.dirname(run_json_path)
    clone_directory(report_template_dir, dir)

    _generate_static_html(result, report_template_html, dir)
    console.print(f"Report generated in {dir}/index.html")


def _append_descriptions(profile_result):
    for table_v in profile_result['tables'].values():
        table_v['description'] = 'Description: N/A'
        for column_v in table_v['columns'].values():
            column_v['description'] = 'Description: N/A'


def _append_descriptions_from_assertion(profile_result):
    engine = AssertionEngine(None)
    engine.load_assertion_content()
    for table_name, table_v in engine.assertions_content.items():
        if table_name not in profile_result['tables']:
            continue
        table_desc = table_v.get('description', '')
        if table_desc:
            profile_result['tables'][table_name]['description'] = f"{table_desc} - via PipeRider"
        for column_name, column_v in table_v.get('columns', {}).items():
            if column_name not in profile_result['tables'][table_name]['columns']:
                continue
            column_desc = column_v.get('description', column_name)
            if column_desc:
                profile_result['tables'][table_name]['columns'][column_name]['description'] = f"{column_desc} - via PipeRider"


def compare_report(a=None, b=None):
    console = Console()

    report = CompareReport(PIPERIDER_OUTPUT_PATH, a, b)
    if not report.select_reports():
        raise Exception('No valid reports found')
    comparison_data = report.generate_data()

    from piperider_cli import data
    report_template_dir = os.path.join(os.path.dirname(data.__file__), 'report', 'comparison-report')
    with open(os.path.join(report_template_dir, 'index.html')) as f:
        report_template_html = f.read()

    data_id = comparison_data.id()
    dir = os.path.join(PIPERIDER_COMPARISON_PATH, data_id)
    clone_directory(report_template_dir, dir)

    filename = os.path.join(dir, 'index.html')
    with open(filename, 'w') as f:
        html = setup_report_variables(report_template_html, False, comparison_data.to_json())
        f.write(html)

    console.print()
    console.print(f"Comparison report: {filename}")

    # TODO for debugging intermediate data, remove this
    with open(os.path.join(dir, 'comparison_data.json'), 'w') as f:
        f.write(comparison_data.to_json())

    pass
