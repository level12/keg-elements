import os.path as osp
from setuptools import setup, find_packages

cdir = osp.abspath(osp.dirname(__file__))
README = open(osp.join(cdir, 'readme.rst')).read()
CHANGELOG = open(osp.join(cdir, 'changelog.rst')).read()

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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    setup_requires=[
        'setuptools_scm',
    ],
    use_scm_version=True,
    install_requires=[
        'arrow',
        'Flask-WTF',
        'Keg',
        'pytz',
        'WTForms-Alchemy',
    ]
)
