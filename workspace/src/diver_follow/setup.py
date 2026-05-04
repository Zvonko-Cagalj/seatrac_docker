from setuptools import setup

package_name = "diver_follow"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/diver_follow.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zvonko",
    maintainer_email="zvonko@example.com",
    description="Diver target and MARUS boat follower",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "diver_target_node = diver_follow.diver_target_node:main",
            "boat_follow_node = diver_follow.boat_follow_node:main",
        ],
        "console_scripts": [
            "diver_keyboard_node = diver_follow.diver_keyboard_node:main",
            "seatrac_sim_node = diver_follow.seatrac_sim_node:main",
            "boat_follow_node = diver_follow.boat_follow_node:main",
        ],
    },
)