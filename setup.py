from setuptools import setup, find_packages

setup(name='aybu-manager',
      version=':versiontools:aybu.manager.version:',
      description="AyBU instances manager ReST API and daemon",
      long_description="""AyBU instances manager ReST API and daemon""",
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
          'alembic>=0.2',
          'SQLAlchemy<0.8a',
          'pyramid',
          'pyzmq',
          'redis',
          'aybu-core',
          'pwgen',
          'mako',
      ),
      paster_plugins=['pyramid'],
      entry_points = """\
      [paste.app_factory]
        main = aybu.manager.rest:main
      [paste.paster_command]
        uwsgi = pasteuwsgi.serve:ServeCommand
      [console_scripts]
        aybu_manager_worker = aybu.manager.daemon:start
      [nose.plugins.0.10]
        aybuconfig = aybu.core.testing:ReadAybuConfigPlugin
      """,
      tests_require=('nose', 'coverage', 'mock'),
      setup_requires=('versiontools >= 1.8',),
      test_suite='tests',
)
