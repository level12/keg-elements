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
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    version=version['VERSION'],
    python_requires='>=3.11',
    install_requires=[
        'arrow',
        'Flask-WTF',
        'Keg>=0.11.0',
        'pytz',
        'WTForms-Alchemy>=0.18.0',
        'wtforms>=3.3.2',
        'WTForms-Components>=0.12.0',
        'cryptography',
        'sentry_sdk>=2',
    ],
    extras_require={
        'tests': [
            'alembic',
            'flask-webtest',
            'pre-commit',
            'psycopg[binary]>=3',
            'pyquery',
            'pytest',
            'pytest-cov',
            'pyodbc',
            'responses',
            'sqlalchemy_pyodbc_mssql',
            'tox',
            'freezegun',
            'webgrid',
            'six',
            'SQLAlchemy>=2.1',
            'xlsxwriter',
        ],
        'i18n': [
            'morphi'
        ]
    }
)
