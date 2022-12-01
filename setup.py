import os.path as osp
from setuptools import setup, find_packages

cdir = osp.abspath(osp.dirname(__file__))
README = open(osp.join(cdir, 'readme.rst')).read()
CHANGELOG = open(osp.join(cdir, 'changelog.rst')).read()

version = {}
with open(osp.join(cdir, 'keg_elements', 'version.py')) as version_fp:
    exec(version_fp.read(), version)

setup(
    name="KegElements",
    description=("A testing ground for Keg related code and ideas."),
    long_description='\n\n'.join((README, CHANGELOG)),
    author="Randy Syring",
    author_email="randy.syring@level12.io",
    url='https://github.com/level12/keg-elements',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    version=version['VERSION'],
    install_requires=[
        'arrow',
        'Flask-WTF',
        'Keg',
        'pytz',
        'WTForms-Alchemy>=0.18.0',
        'wtforms>=3.0.0',
        'cryptography',
        'sentry_sdk',
    ],
    extras_require={
        'dev': [
            'alembic',
            'flask-webtest',
            'pre-commit',
            'psycopg2-binary',
            'pyquery',
            'pytest',
            'pytest-cov',
            # pinned to version in our package index.
            'pyodbc==4.0.34',
            'sqlalchemy_pyodbc_mssql',
            'tox',
            'freezegun',
            'webgrid',
            'xlsxwriter',
        ],
        'i18n': [
            'morphi'
        ]
    }
)
