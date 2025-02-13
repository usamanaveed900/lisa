# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from lisa.executable import Tool
from lisa.operating_system import Redhat, Ubuntu
from lisa.tools.git import Git
from lisa.util import UnsupportedDistroException


class Modetest(Tool):
    repo = "https://github.com/grate-driver/libdrm"

    @property
    def command(self) -> str:
        return "modetest"

    @property
    def can_install(self) -> bool:
        return True

    def is_status_connected(self, driver_name: str) -> bool:
        cmd_result = self.run(
            f"-M {driver_name}", sudo=True, shell=True, force_run=True
        )
        # output segment
        # Connectors:
        # id encoder status          name             size (mm)       modes   encoders
        # 31 35      connected       Virtual-1        0x0             24      35
        return any("connected" in line for line in cmd_result.stdout.splitlines())

    def _install(self) -> bool:
        if isinstance(self.node.os, Ubuntu):
            self.node.os.install_packages("libdrm-tests")
        if isinstance(self.node.os, Redhat):
            self._install_from_src()
        return self._check_exists()

    def _install_dep_packages(self) -> None:
        if isinstance(self.node.os, Redhat):
            self.node.os.install_packages(
                (
                    "git",
                    "make",
                    "autoconf",
                    "automake",
                    "libpciaccess-devel.x86_64",
                    "libtool",
                    "http://mirror.stream.centos.org/9-stream/CRB/x86_64/os/Packages/xorg-x11-util-macros-1.19.3-4.el9.noarch.rpm",  # noqa: E501
                    "http://mirror.stream.centos.org/9-stream/CRB/x86_64/os/Packages/ninja-build-1.10.2-6.el9.x86_64.rpm",  # noqa: E501
                    "http://mirror.stream.centos.org/9-stream/CRB/x86_64/os/Packages/meson-0.58.2-1.el9.noarch.rpm",  # noqa: E501
                )
            )
        else:
            raise UnsupportedDistroException(self.node.os)

    def _install_from_src(self) -> None:
        self._install_dep_packages()
        tool_path = self.get_tool_path()
        self.node.tools[Git].clone(self.repo, tool_path)
        code_path = tool_path.joinpath("libdrm")
        self.node.execute(
            "./autogen.sh --enable-install-test-programs", cwd=code_path
        ).assert_exit_code()
        self.node.execute(
            "meson builddir/", cwd=code_path, sudo=True
        ).assert_exit_code()
        self.node.execute(
            "ninja -C builddir/ install", cwd=code_path, sudo=True
        ).assert_exit_code()
        self.node.execute(
            f"ln -s {code_path}/builddir/tests/modetest/modetest /usr/bin/modetest",
            sudo=True,
            cwd=code_path,
        ).assert_exit_code()
