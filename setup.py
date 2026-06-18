from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(name='Web3Scout',
      version='1.0.0',
      description='Onchain Event Framework for DeFiPy',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/defipy-devs/web3scout',
      author = "icmoore",
      author_email = "defipy.devs@gmail.com",
      license="Apache-2.0",
      classifiers=[
            "License :: OSI Approved :: Apache Software License",
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Scientific/Engineering :: Information Analysis",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
      ],
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
            "web3scout.token.fetch",
            "web3scout.contract",
            "web3scout.uniswap_v2",
      ],
      install_requires=[
            # Ethereum / Web3 stack. web3 6.x pinned below 7 because
            # abi_load.py still uses web3._utils.contracts.get_function_info,
            # which was removed in web3 7.x. Drop the ceiling once abi_load
            # migrates to the public ABI helpers.
            'web3 >= 6.0, < 7.0',
            'eth_abi >= 4.0',
            'eth_typing >= 3.0',
            'eth_tester >= 0.9',
            'eth_bloom >= 2.0',
            'eth_utils >= 2.0',
            'hexbytes >= 0.3',
            # DeFiPy ecosystem (FetchToken uses uniswappy.erc.ERC20)
            'uniswappy >= 1.7.6',
            # System utilities (used by shutdown_hard for process management)
            'psutil >= 5.9',
            # Progress reporting for block header downloads
            'tqdm >= 4.65',
            # In-memory caching for token details lookups
            'cachetools >= 5.0',
            # Data handling
            'pandas >= 1.3',
      ],
      include_package_data=True,
      zip_safe=False,
)
