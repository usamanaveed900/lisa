# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import cast

from lisa.executable import Tool
from lisa.operating_system import Posix


class Stat(Tool):
    @property
    def command(self) -> str:
        return "stat"

    @property
    def can_install(self) -> bool:
        return True

    def install(self) -> bool:
        posix_os: Posix = cast(Posix, self.node.os)
        package_name = "coreutils"
        posix_os.install_packages(package_name)
        return self._check_exists()

    def get_fs_block_size(self, file: str) -> int:
        cmd_result = self.run(
            "-f --format='%S' " f"{file}",
            force_run=True,
            expected_exit_code=0,
            expected_exit_code_failure_message=(
                f"fail to get block size of {file} in file system"
            ),
        )
        return int(cmd_result.stdout)

    def get_fs_available_size(self, file: str) -> int:
        cmd_result = self.run(
            "-f --format='%a' " f"{file}",
            force_run=True,
            expected_exit_code=0,
            expected_exit_code_failure_message=(
                f"fail to get available size of {file} in filesystem"
            ),
        )
        return int(cmd_result.stdout)

    def get_total_size(self, file: str) -> int:
        cmd_result = self.run(
            f"{file}" " --format='%s'",
            force_run=True,
            expected_exit_code=0,
            expected_exit_code_failure_message=(f"fail to get total size of {file}"),
        )
        return int(cmd_result.stdout)

    def get_fs_free_blocks(self, file: str) -> int:
        cmd_result = self.run(
            "-f --format='%f'" f" {file}",
            force_run=True,
            expected_exit_code=0,
            expected_exit_code_failure_message=(
                f"fail to get free blocks of {file} in file system"
            ),
        )
        return int(cmd_result.stdout)
