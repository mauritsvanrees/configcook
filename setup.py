import codecs
import sys

from setuptools import find_packages
from setuptools import setup


version = '1.0.0a1.dev0'


def read(filename):
    try:
        with codecs.open(filename, encoding='utf-8') as f:
            return unicode(f.read())
    except NameError:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()


long_description = u'\n\n'.join(
    [read('README.rst'), read('CREDITS.rst'), read('CHANGES.rst')]
)

if sys.version_info < (3,):
    long_description = long_description.encode('utf-8')


setup(
    name='configcook',
    version=version,
    description="Task automation by cooking recipes in a configuration file",
    long_description=long_description,
    classifiers=[
        #   "Development Status :: 1 - Alpha",
        #   "Intended Audience :: Developers",
        #   "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=['make', 'buildout', 'configuration', 'task', 'automation'],
    author='Maurits van Rees',
    author_email='maurits@vanrees.org',
    url='https://github.com/mauritsvanrees/configcook',
    license='GPL',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=[],
    include_package_data=True,
    zip_safe=True,
    install_requires=['setuptools', 'six'],
    extras_require={},
    entry_points={
        'console_scripts': ['configcook = configcook.cli:main'],
        'configcook.extension': [
            'configcook:extension_example = configcook.extensions:ExampleExtension',
        ],
        'configcook.recipe': [
            'configcook:recipe = configcook.recipes:BaseRecipe',
            'configcook:recipe_example = configcook.recipes:ExampleRecipe',
        ],
    },
)
