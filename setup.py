from setuptools import setup, find_packages

setup(
        name="still_func",
        version="1.0.0",
        author="Dongyu Xu",
        author_email="xudongyu@bupt.edu.cn",
        description="a filter to remove the still object",
        packages = find_packages(
            exclude = ['test*']
        )
    )
