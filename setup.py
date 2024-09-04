from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(name='Web3Scout',
      version='0.0.1',
      description='web3scout',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='http://github.com/defipy-devs/web3scout',
      author = "icmoore",
      author_email = "defipy.devs@gmail.com",
      license='MIT',
      package_dir = {"web3scout": "python/prod"},
      packages=[
          'web3scout',
          'web3scout.erc'
      ],   
      zip_safe=False)
