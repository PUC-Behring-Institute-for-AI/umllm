# ** GENERATED FILE: DO NOT EDIT! **
import itertools
import re
import setuptools
with open('umllm/__version__.py', 'r', encoding='utf-8') as fp:
    text = fp.read()
    VERSION, = re.findall(r"__version__\s*=\s*'(.*)'", text)
with open('README.md', 'r', encoding='utf-8') as fp:
    README = fp.read()
setuptools.setup(
    name='umllm',
    version=VERSION,
    description='An LLM-based Turing Machine Executor',
    long_description=README,
    long_description_content_type='text/markdown',
    author='PUC-Behring Institute for AI',
    author_email='glima@puc-rio.br',
    url='https://github.com/PUC-Behring-Institute-for-AI/umllm',
    license='Apache-2.0',
    classifiers=[ 'Programming Language :: Python', 'Programming Language :: Python :: 3', 'Programming Language :: Python :: 3.9', 'Programming Language :: Python :: 3.10', 'Programming Language :: Python :: 3.11', 'Programming Language :: Python :: 3.12', 'Programming Language :: Python :: 3.13', 'Programming Language :: Python :: 3.14', ],
    python_requires='>=3.9',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    package_data={ 'umllm': ['py.typed'], },
    include_package_data=True,
    package_dir={'umllm': 'umllm'},
    install_requires=[ 'click', 'flask', 'types-click', 'typing-extensions', ],
    extras_require={'all': [*['flake8', 'isort', 'mypy', 'pylint', 'pyright', 'pytest', 'pytest-asyncio', 'pytest-cov', 'pytest-mypy', 'pyupgrade', 'setuptools', 'tox'], *itertools.chain(*{}.values())], 'dev': ['build', 'twine', *[*['flake8', 'isort', 'mypy', 'pylint', 'pyright', 'pytest', 'pytest-asyncio', 'pytest-cov', 'pytest-mypy', 'pyupgrade', 'setuptools', 'tox'], *itertools.chain(*{}.values())]], 'tests': ['flake8', 'isort', 'mypy', 'pylint', 'pyright', 'pytest', 'pytest-asyncio', 'pytest-cov', 'pytest-mypy', 'pyupgrade', 'setuptools', 'tox'], **{}},
    entry_points={ 'console_scripts': ['umllm = umllm.cli:cli'], },
    zip_safe=False,
)
