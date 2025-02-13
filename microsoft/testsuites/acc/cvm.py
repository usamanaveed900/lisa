# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import re

from assertpy import assert_that

from lisa import Logger, Node, TestCaseMetadata, TestSuite, TestSuiteMetadata
from lisa.features.security_profile import CvmEnabled
from lisa.testsuite import simple_requirement
from lisa.tools import Dmesg, Lsvmbus
from lisa.util import LisaException


@TestSuiteMetadata(
    area="ACC_CVM",
    category="functional",
    description="""
    This test suite ensures correct configuration and allowed devices for CVM
    """,
)
class CVMSuite(TestSuite):
    # [    0.000000] Hyper-V: Isolation Config: Group A 0x1, Group B 0xba2
    __isolation_config_pattern = re.compile(
        r"\[\s+\d+.\d+\]\s+Hyper-V: Isolation Config: Group A."
        r"(?P<config_a>(0x[a-z,A-Z,0-9]+)), Group B.(?P<config_b>(0x[a-z,A-Z,0-9]+))"
    )

    @TestCaseMetadata(
        description="""
        This case verifies that lsvmbus only shows devices
        that are allowed in a CVM guest

        Steps:
        1. Call lsvmbus
        2. Iterate through list returned by lsvmbus to ensure all devices
           listed are included in valid_class_ids
        """,
        priority=1,
        requirement=simple_requirement(
            supported_features=[CvmEnabled()],
        ),
    )
    def verify_lsvmbus(self, log: Logger, node: Node) -> None:
        valid_class_ids = {
            "ba6163d9-04a1-4d29-b605-72e2ffb1dc7f": "Synthetic SCSI Controller",
            "f8615163-df3e-46c5-913f-f2d2f965ed0e": "Synthetic network adapter",
            "9527e630-d0ae-497b-adce-e80ab0175caf": "[Time Synchronization]",
            "57164f39-9115-4e78-ab55-382f3bd5422d": "[Heartbeat]",
            "0e0b6031-5213-4934-818b-38d90ced39db": "[Operating system shutdown]",
        }
        lsvmbus_tool = node.tools[Lsvmbus]
        device_list = lsvmbus_tool.get_device_channels()
        class_id_list = [device.class_id for device in device_list]
        assert_that(class_id_list).is_subset_of(list(valid_class_ids.keys()))

    @TestCaseMetadata(
        description="""
        This case verifies the isolation config on guest

        Steps:
        1. Call dmesg to get output
        2. Find isolation config in output
        3. Check to ensure config a is 0x1
        4. Check to ensure config b is 0xba2
        """,
        priority=1,
        requirement=simple_requirement(
            supported_features=[CvmEnabled()],
        ),
    )
    def verify_isolation_config(self, log: Logger, node: Node) -> None:
        valid_cvm_type = {
            "HV_ISOLATION_TYPE_SNP": 2,
        }

        dmesg_tool = node.tools[Dmesg]
        dmesg_output = dmesg_tool.get_output()
        isolation_config = re.search(self.__isolation_config_pattern, dmesg_output)
        if isolation_config is not None:
            isolation_config_a = int(isolation_config.group("config_a"), 16)
            isolation_config_b = bin(int(isolation_config.group("config_b"), 16))
            log.debug(
                f"Isolation Config is Group A:{isolation_config_a}, "
                f"Group B:{isolation_config_b}"
            )
        else:
            raise LisaException("No find matched Isolation Config in dmesg")

        cvm_type = int(isolation_config_b[10:14], 2)
        assert_that(list(valid_cvm_type.values())).contains(cvm_type)
        if cvm_type == valid_cvm_type["HV_ISOLATION_TYPE_SNP"]:
            # config_a has 1 bit that indicates if paravisor is present
            assert_that(isolation_config_a).is_equal_to(1)

            # shared_gpa_boundary_active indicates that shared_gpa_boundary_bits is set
            shared_gpa_boundary_active = int(isolation_config_b[8:9], 2)
            assert_that(shared_gpa_boundary_active).is_equal_to(1)

            # shared_gpa_boundary_bits indicates the bit that is used for vTOM
            shared_gpa_boundary_bits = int(isolation_config_b[2:8], 2)
            assert_that(shared_gpa_boundary_bits).is_equal_to(46)
