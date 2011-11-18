from setuptools import setup, find_packages

setup(name='aybu-manager',
      version=':versiontools:aybu.manager:',
      description="AyBU instances manager daemon",
      long_description="""AyBU instances manager daemon""",
      classifiers=('License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Systems Administration'),
      keywords='',
      author='Giacomo Bagnoli',
      author_email='g.bagnoli@asidev.com',
      url='http://code.asidev.net/projects/aybu',
      license='Apache Software License',
      packages=find_packages(),
      namespace_packages=('aybu',),
      include_package_data=True,
      zip_safe=False,
      install_requires=(
          'SQLAlchemy>=0.7',
          'ConfigObj',
          'aybu-core',
          'pwgen',
          'mako',
      ),
      tests_require=('nose', 'coverage'),
      setup_requires=('versiontools >= 1.8',),
      test_suite='tests',
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
