import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from setuptools import find_packages

# search for all files in root_path directory recursively, and create list of
# tuples (dir, file), root_path is relative to setup.py location.


def get_data_files_recursively(search_dir):
    base_path = os.path.dirname(os.path.abspath(__file__))
    search_path = os.path.join(base_path, search_dir)

    matches = []
    for root, dirnames, filenames in os.walk(search_path):
        for filename in filenames:
            rel_dir_path = root.split(base_path, 1)[1].lstrip("//")
            match = (rel_dir_path, [os.path.join(rel_dir_path, filename)])
            matches.append(match)

    return matches


def find_data_files():
    data_files = [
    ]

    data_files.extend(get_data_files_recursively('pkginstaller'))
    return data_files

setup(
    name='pkginstaller',
    version='0.1.0',
    zip_safe=False,
    description='package installer utility.',
    long_description=open('README').read(),
    author='Gaurav Goel',
    author_email='gauravgoel9nov@gmail.com',
    url='http://www.gagoel.com/',

    packages=find_packages(),
    data_files=find_data_files(),
    scripts=[],
    install_requires=[
    ],
)
