from setuptools import setup, find_packages

setup(name='aybu-manager-daemon',
      version=':versiontools:aybu.manager.daemon:',
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
      namespace_packages=('aybu', 'aybu.manager'),
      include_package_data=True,
      zip_safe=False,
      install_requires=(
      ),
      tests_require=('nose', 'coverage'),
      setup_requires=('versiontools >= 1.8',),
      test_suite='tests',
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
