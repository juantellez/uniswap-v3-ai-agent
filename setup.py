# setup.py
from setuptools import setup, find_packages

# Lee las dependencias desde requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="uniswap_v3_agent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=required,
    entry_points={
        "console_scripts": [
            "run-agent=daemon:main",
            "clean-db=script_limpiar_recomendaciones:main",
        ],
    },
)