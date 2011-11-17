from setuptools import setup, find_packages

setup(name='aybu-instances-${instance.domain}',
      version='0.0',
      description="aybu ${instance.domain} instance",
      long_description="aybu ${instance.domain} instance",
      classifiers=[],
      keywords='',
      author='${instance.owner.name} ${instance.owner.surname}',
      author_email='${instance.owner.email}',
      url='${instance.owner.web}',
      license='',
      packages=find_packages(),
      namespace_packages=["aybu", "aybu.instances"],
      include_package_data=True,
      zip_safe=False,
      install_requires=["aybu-controlpanel"],
      entry_points="",
)

