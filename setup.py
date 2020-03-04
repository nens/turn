from setuptools import setup

version = '1.0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'redis>=2.10.5',
    ],

tests_require = ["flake8", "ipdb", "ipython", "pytest", "pytest-cov"]

setup(name='turn',
      version=version,
      description=('A shared-resource-locking '
                   'queue system using python and redis.'),
      long_description=long_description,
      keywords=['redis', 'queue', 'resource', 'shared'],
      author='Arjan Verkerk',
      author_email='arjan.verkerk@nelen-schuurmans.nl',
      url='https://github.com/nens/turn',
      license='GPL',
      packages=['turn'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      classifiers = [
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      entry_points={
          'console_scripts': [
              'turn = turn.console:main',
          ]},
      )
