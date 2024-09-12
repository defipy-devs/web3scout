from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(name='Web3Scout',
      version='0.0.2',
      description='Python library for Web3 surveillance',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/defipy-devs/web3scout',
      author = "icmoore",
      author_email = "defipy.devs@gmail.com",
        license="MIT",
        package_dir = {"web3scout": "python/prod"},
        packages=[
            "web3scout",
            "web3scout.event",
            "web3scout.event.tools",
            "web3scout.event.process",
            "web3scout.abi",
            "web3scout.utils",
            "web3scout.data",
            "web3scout.enums",
            "web3scout.token",
            "web3scout.contract",
            "web3scout.uniswap_v2"
        ],
        install_requires=['web3', 
                          'eth_abi', 
                          'eth_typing',
                          'eth_tester',
                          'eth_bloom',
                          'eth_utils', 
                          'web3-ethereum-defi',
                          'hexbytes', 
                          'pandas'],
        include_package_data=True,
        zip_safe=False,
    )
