# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/096_Docusaurus_Helper.ipynb.

# %% auto 0
__all__ = ['build_markdown_docs']

# %% ../nbs/096_Docusaurus_Helper.ipynb 2
import itertools
import re
import types
from inspect import Signature, getmembers, isclass, isfunction, signature
from pathlib import Path
from typing import *

import typer
from docstring_parser import parse
from docstring_parser.common import DocstringParam, DocstringRaises, DocstringReturns
from nbdev.config import get_config
from nbdev_mkdocs.mkdocs import (
    _add_all_submodules,
    _get_api_summary,
    _import_all_members,
    _import_functions_and_classes,
    _import_submodules,
)

# %% ../nbs/096_Docusaurus_Helper.ipynb 4
def _format_docstring_sections(
    items: Union[List[DocstringParam], List[DocstringReturns], List[DocstringRaises]],
    keyword: str,
) -> str:
    """Format a list of docstring sections

    Args:
        items: A list of DocstringParam objects
        keyword: The type of section to format (e.g. 'Parameters', 'Returns', 'Exceptions')

    Returns:
        The formatted docstring.
    """
    formatted_docstring = ""
    if len(items) > 0:
        formatted_docstring += f"**{keyword}**:\n"
        for item in items:
            if keyword == "Parameters":
                formatted_docstring += f"- `{item.arg_name}`: {item.description}\n"  # type: ignore
            elif keyword == "Exceptions":
                formatted_docstring += f"- `{item.type_name}`: {item.description}\n"
            else:
                formatted_docstring += f"- {item.description}\n"
        formatted_docstring = f"{formatted_docstring}\n"
    return formatted_docstring

# %% ../nbs/096_Docusaurus_Helper.ipynb 8
def _docstring_to_markdown(docstring: str) -> str:
    """Converts a docstring to a markdown-formatted string.

    Args:
        docstring: The docstring to convert.

    Returns:
        The markdown-formatted docstring.
    """
    parsed_docstring = parse(docstring)
    formatted_docstring = f"{parsed_docstring.short_description}\n\n"
    formatted_docstring += (
        f"{parsed_docstring.long_description}\n\n"
        if parsed_docstring.long_description
        else ""
    )
    formatted_docstring += _format_docstring_sections(
        parsed_docstring.params, "Parameters"
    )
    formatted_docstring += _format_docstring_sections(
        parsed_docstring.many_returns, "Returns"
    )
    formatted_docstring += _format_docstring_sections(
        parsed_docstring.raises, "Exceptions"
    )

    return formatted_docstring

# %% ../nbs/096_Docusaurus_Helper.ipynb 12
def _get_submodules(module_name: str) -> List[str]:
    """Get a list of all submodules contained within the module.

    Args:
        module_name: The name of the module to retrieve submodules from

    Returns:
        A list of submodule names within the module
    """
    members = _import_all_members(module_name)
    members_with_submodules = _add_all_submodules(members)
    members_with_submodules_str: List[str] = [
        x[:-1] if x.endswith(".") else x for x in members_with_submodules
    ]
    return members_with_submodules_str

# %% ../nbs/096_Docusaurus_Helper.ipynb 14
def _load_submodules(
    module_name: str, members_with_submodules: List[str]
) -> List[Union[types.FunctionType, Type[Any]]]:
    """Load the given submodules from the module.

    Args:
        module_name: The name of the module whose submodules to load
        members_with_submodules: A list of submodule names to load

    Returns:
        A list of imported submodule objects.
    """
    submodules = _import_submodules(module_name)
    members: List[Tuple[str, Union[types.FunctionType, Type[Any]]]] = list(
        itertools.chain(*[_import_functions_and_classes(m) for m in submodules])
    )
    names = [
        y
        for x, y in members
        if f"{y.__module__}.{y.__name__}" in members_with_submodules
    ]
    return names

# %% ../nbs/096_Docusaurus_Helper.ipynb 16
def _convert_union_to_optional(annotation_str: str) -> str:
    """Convert the 'Union[Type1, Type2, ..., NoneType]' to 'Optional[Type1, Type2, ...]' in the given annotation string

    Args:
        annotation_str: The type annotation string to convert.

    Returns:
        The converted type annotation string.
    """
    pattern = r"Union\[(.*)?,\s*NoneType\s*\]"
    match = re.search(pattern, annotation_str)
    if match:
        union_type = match.group(1)
        optional_type = f"Optional[{union_type}]"
        return re.sub(pattern, optional_type, annotation_str)
    else:
        return annotation_str

# %% ../nbs/096_Docusaurus_Helper.ipynb 18
def _get_arg_list_with_signature(_signature: Signature) -> str:
    """Converts a function's signature into a string representation of its argument list.

    Args:
        _signature (signature): The signature object for the function to convert.

    Returns:
        str: A string representation of the function's argument list.
    """
    arg_list = []
    for param in _signature.parameters.values():
        arg_list.append(_convert_union_to_optional(str(param)))

    return ", ".join(arg_list)

# %% ../nbs/096_Docusaurus_Helper.ipynb 21
def _get_symbol_definition(symbol: Union[types.FunctionType, Type[Any]]) -> str:
    """Return the definition of a given symbol.

    Args:
        symbol: A function or method object to get the definition for.

    Returns:
        A string representing the function definition
    """
    _signature = signature(symbol)
    arg_list = _get_arg_list_with_signature(_signature)
    ret_val = ""

    if isfunction(symbol):
        ret_val = f"`def {symbol.__name__}({arg_list})"
        if _signature.return_annotation and "inspect._empty" not in str(
            _signature.return_annotation
        ):
            if isinstance(_signature.return_annotation, type):
                ret_val = ret_val + f" -> {_signature.return_annotation.__name__}`\n"
            else:
                ret_val = ret_val + f" -> {_signature.return_annotation}`\n"

        else:
            ret_val = ret_val + " -> None`\n"

    return ret_val

# %% ../nbs/096_Docusaurus_Helper.ipynb 27
def _get_formatted_docstring_for_symbol(
    symbol: Union[types.FunctionType, Type[Any]]
) -> str:
    """Recursively parses and get formatted docstring of a symbol.

    Args:
        symbol: A Python class or function object to parse the docstring for.

    Returns:
        A formatted docstring of the symbol and its members.

    """

    def traverse(symbol: Union[types.FunctionType, Type[Any]], contents: str) -> str:
        """Recursively traverse the members of a symbol and append their docstrings to the provided contents string.

        Args:
            symbol: A Python class or function object to parse the docstring for.
            contents: The current formatted docstrings.

        Returns:
            The updated formatted docstrings.

        """
        for x, y in getmembers(symbol):
            if not x.startswith("_") or x.endswith("__"):
                if isfunction(y) and y.__doc__ is not None:
                    contents += f"{_get_symbol_definition(y)}\n{_docstring_to_markdown(y.__doc__)}"
                elif isclass(y) and not x.startswith("__") and y.__doc__ is not None:
                    contents += f"{_get_symbol_definition(y)}\n{_docstring_to_markdown(y.__doc__)}"
                    contents = traverse(y, contents)
        return contents

    contents = (
        f"{_get_symbol_definition(symbol)}\n{_docstring_to_markdown(symbol.__doc__)}"
        if symbol.__doc__ is not None
        else ""
    )
    if isclass(symbol):
        contents = traverse(symbol, contents)
    return contents

# %% ../nbs/096_Docusaurus_Helper.ipynb 31
def _convert_html_style_attribute_to_jsx(contents: str) -> str:
    """Converts the inline style attributes in an HTML string to JSX compatible format.

    Args:
        contents: A string containing an HTML document or fragment.

    Returns:
        A string with inline style attributes converted to JSX compatible format.
    """
    style_regex = re.compile(r'style="(.+?)"')
    style_matches = style_regex.findall(contents)

    for style_match in style_matches:
        style_dict = {}
        styles = style_match.split(";")
        for style in styles:
            key_value = style.split(":")
            if len(key_value) == 2:
                key = re.sub(
                    r"-(.)", lambda m: m.group(1).upper(), key_value[0].strip()
                )
                value = key_value[1].strip().replace("'", '"')
                style_dict[key] = value
        replacement = "style={{"
        for key, value in style_dict.items():
            replacement += f"{key}: '{value}', "
        replacement = replacement[:-2] + "}}"
        contents = contents.replace(f'style="{style_match}"', replacement)

    return contents

# %% ../nbs/096_Docusaurus_Helper.ipynb 33
def _get_all_markdown_files_path(docs_path: Path) -> List[Path]:
    """Get all Markdown files in a directory and its subdirectories.

    Args:
        directory: The path to the directory to search in.

    Returns:
        A list of paths to all Markdown files found in the directory and its subdirectories.
    """
    markdown_files = [file_path for file_path in docs_path.glob("**/*.md")]
    return markdown_files

# %% ../nbs/096_Docusaurus_Helper.ipynb 35
def _fix_special_symbols_in_html(contents: str) -> str:
    contents = contents.replace("”", '"')
    return contents

# %% ../nbs/096_Docusaurus_Helper.ipynb 37
def _fix_invalid_syntax_in_markdown(docs_path: Path) -> None:
    """Fix invalid HTML syntax in markdown files and converts inline style attributes to JSX-compatible format.

    Args:
        docs_path: The path to the root directory to search for markdown files.
    """
    markdown_files = _get_all_markdown_files_path(docs_path)
    updated_contents = [
        _convert_html_style_attribute_to_jsx(Path(file).read_text())
        for file in markdown_files
    ]
    updated_contents = [
        _fix_special_symbols_in_html(contents) for contents in updated_contents
    ]
    for i, file_path in enumerate(markdown_files):
        file_path.write_text(updated_contents[i])

# %% ../nbs/096_Docusaurus_Helper.ipynb 39
def _generate_markdown_docs(module_name: str, docs_path: Path) -> None:
    """Generates Markdown documentation files for the symbols in the given module and save them to the given directory.

    Args:
        module_name: The name of the module to generate documentation for.
        docs_path: The path to the directory where the documentation files will be saved.
    """
    members_with_submodules = _get_submodules(module_name)
    symbols = _load_submodules(module_name, members_with_submodules)

    for symbol in symbols:
        content = f"`{symbol.__module__}.{symbol.__name__}`\n\n"
        content += _get_formatted_docstring_for_symbol(symbol)
        target_file_path = (
            "/".join(f"{symbol.__module__}.{symbol.__name__}".split(".")) + ".md"
        )

        with open((docs_path / "api" / target_file_path), "w") as f:
            f.write(content)

# %% ../nbs/096_Docusaurus_Helper.ipynb 41
_app = typer.Typer()


@_app.command()
def build_markdown_docs(
    module_name: str = typer.Option(
        None,
        help="The name of the module for which the markdown documentation should be generated. If None, then the module name will be read from settings.ini file.",
    ),
    docs_path: str = typer.Option(
        "./docusaurus/docs",
        help="The docs root path to save the generated markdown files",
    ),
) -> None:
    if module_name is None:
        module_name = get_config().lib_name

    _fix_invalid_syntax_in_markdown(Path(docs_path))
    _generate_markdown_docs(module_name, Path(docs_path))
