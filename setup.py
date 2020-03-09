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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    setup_requires=[
        'setuptools_scm',
    ],
    version=version['VERSION'],
    install_requires=[
        'arrow',
        'Flask-WTF',
        'Keg',
        'pytz',
        'WTForms-Alchemy',
        'cryptography',
        'raven',
    ],
    extras_require={
        'dev': [
            'flask-webtest',
            'pre-commit',
            'pyquery',
            'pytest',
            'pytest-cov',
            'tox',
            'freezegun'
        ],
        'i18n': [
            'morphi'
        ]
    }
)
