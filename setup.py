#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import shutil
import sys
from io import open

from setuptools import find_packages, setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('davinci_crawling')


if sys.argv[-1] == 'publish':
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    shutil.rmtree('dist')
    shutil.rmtree('build')
    shutil.rmtree('django-davinci-crawling.egg-info')
    sys.exit()


setup(
    name='django-davinci-crawling',
    version=version,
    url='http://buildgroupai.com',
    license='MIT',
    description='Django DaVinci Crawling Framework.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Javier Alperte',
    author_email='xalperte@buildgroupai.com',  # SEE NOTE BELOW (*)
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    scripts=['davinci_crawling/gcp/startup-script.sh'],
    install_requires=[
        'spitslurp>=0.4',
        'python-dateutil>=2',
        'requests>=2.19',
        'untangle>=1.1',
        'selenium>=3',
        'beautifulsoup4>=4',
        'xmljson>=0.1',
        'jsonpath>=0.80',
        'gevent>=1.2.2',
        'django-apscheduler>=0.2.13',
        'google-api-python-client>=1.7',
        'google-cloud-storage>=1.10',
        'XlsxWriter>=1.1.2',
        'django-cassandra-engine==1.5.5.bgds-1',
        'django-caravaggio-rest-api==0.1.7-SNAPSHOT'],
    tests_require=[
        'spitslurp>=0.4',

        'django-debug-toolbar>=1.10.1',
        'django-extensions>=2.1.3',

        'psycopg2-binary>=2.7.5',

        #cassandra-driver>=3.15.0
        'dse-driver>=2.6',
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ],
    dependency_links=[
        "git+ssh://git@github.com/buildgroupai/django-cassandra-engine.git"
        "@bgds-1#"
        "egg=django-cassandra-engine-1.5.5-bgds-1",

        "git+ssh://git@github.com/buildgroupai/django-caravaggio-rest-api.git"
        "@clients-support_external-systems#"
        "egg=django-caravaggio-rest-api-0.1.7-SNAPSHOT",
    ],
)

# (*) Please direct queries to the discussion group, rather than to me directly
#     Doing so helps ensure your question is helpful to other users.
#     Queries directly to my email are likely to receive a canned response.
#
#     Many thanks for your understanding.
