import os

from jsonschema.exceptions import ValidationError
from rich.console import Console
from rich.syntax import Syntax

from piperider_cli.configuration import FileSystem
from piperider_cli.dbtutil import load_dbt_project
from piperider_cli.recipes import (RecipeConfiguration,
                                   RecipeDbtField, RecipeModel,
                                   RecipePiperiderField, tool, update_select_with_modified)

console = Console()


def _read_dbt_project_file(dbt_project_path):
    if dbt_project_path is None:
        return None
    try:
        dbt_project = load_dbt_project(dbt_project_path)
    except Exception as e:
        console.print(f'[[bold yellow]Skip[/bold yellow]] dbt project: {e}')
        return None
    return dbt_project


def _create_base_recipe(dbt_project_path=None, options: dict = None) -> RecipeModel:
    """
    Create the base recipe
    """
    base = RecipeModel()
    select_options = ''

    if tool().git_branch() is not None:
        base.branch = 'main'

    filtered_select = list(
        filter(lambda s: 'state:modified' not in s, options.get('select', ''))) if options else None
    if filtered_select:
        select_options = '--select ' + ' '.join(filtered_select)

    dbt_project = _read_dbt_project_file(dbt_project_path)
    if dbt_project:
        base.dbt = RecipeDbtField({
            'commands': [
                'dbt deps',
                f'dbt build'
            ]
        })

    base.piperider = RecipePiperiderField({
        'command': f'piperider run {select_options}'.strip(),
    })
    return base


def _create_target_recipe(dbt_project_path=None, options: dict = None) -> RecipeModel:
    """
    Create the target recipe
    """
    target = RecipeModel()
    piperider_select_options = ''
    dbt_select_options = ''
    state_option = ''
    select = options.get('select') if options else ()
    modified = options.get('modified') if options else False

    # The target branch should be empty by default
    select_contain_state_modified = any('state:modified' in s for s in select)
    if select_contain_state_modified or modified:
        state_option = ' --state <DBT_STATE_PATH>'
        if select_contain_state_modified:
            dbt_select_options = '--select ' + ' '.join(
                filter(lambda s: 'state:modified' in s, select)
            )
            piperider_select_options = '--select ' + ' '.join(
                select
            )
        elif modified:
            dbt_select_options = '--select state:modified+'
            piperider_select_options = '--select ' + ' '.join(
                update_select_with_modified(select, modified)
            )
    elif select:
        piperider_select_options = '--select ' + ' '.join(
            select
        )

    dbt_project = _read_dbt_project_file(dbt_project_path)
    if dbt_project:
        target.dbt = RecipeDbtField({
            'commands': [
                'dbt deps',
                f'dbt build {dbt_select_options}'.strip() + state_option
            ]
        })

    target.piperider = RecipePiperiderField({
        'command': f'piperider run {piperider_select_options}'.strip() + state_option,
    })
    return target


def generate_default_recipe(overwrite_existing: bool = False,
                            dbt_project_path=None, options: dict = None, interactive: bool = True):
    """
    Generate the default recipe
    """
    recipe_path = FileSystem.DEFAULT_RECIPE_PATH
    if overwrite_existing is True and os.path.exists(recipe_path):
        if interactive is True:
            console.print('[bold green]Piperider default recipe already exist[/bold green]')
        return None
    base = _create_base_recipe(dbt_project_path, options)
    target = _create_target_recipe(dbt_project_path, options)
    recipe = RecipeConfiguration(base=base, target=target)

    try:
        recipe.validate(recipe.__dict__())
    except ValidationError as e:
        console.print(f'[[bold red]Error[/bold red]] Recipe syntax error: {e}')
        return None
    except Exception as e:
        console.print(f'[[bold red]Error[/bold red]] {e}')
        return None

    return recipe


def show_recipe_content(recipe: RecipeConfiguration):
    """
    Display the recipe content
    """

    yaml_output = Syntax(recipe.dump(), 'yaml', theme='monokai', line_numbers=True)
    console.print(yaml_output)
    console.rule('End of Recipe')


if __name__ == '__main__':
    generate_default_recipe(overwrite_existing=True)
