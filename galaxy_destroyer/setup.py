from setuptools import setup, find_packages

setup(
    name="galaxy-destroyer",
    version="0.1.0",
    description="AI-powered terminal assistant - Claude Code equivalent",
    author="Galaxy Team",
    author_email="team@galaxy.dev",
    license="MIT",
    packages=find_packages(include=[
        "galaxy_destroyer",
        "galaxy_destroyer.core",
        "galaxy_destroyer.commands", 
        "galaxy_destroyer.services",
        "galaxy_destroyer.services.api",
        "galaxy_destroyer.services.tools",
        "galaxy_destroyer.tools",
        "galaxy_destroyer.state",
        "galaxy_destroyer.utils",
        "galaxy_destroyer.hooks",
        "galaxy_destroyer.components",
    ]),
    python_requires=">=3.10",
    install_requires=[
        "prompt_toolkit>=3.0.40",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "galaxy=galaxy_destroyer.cli:main",
            "gd=galaxy_destroyer.cli:main",
        ],
    },
)