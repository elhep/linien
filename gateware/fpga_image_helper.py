# Copyright 2014-2015 Robert Jördens <jordens@gmail.com>
# Copyright 2018-2022 Benjamin Wiegand <benjamin.wiegand@physik.hu-berlin.de>
# Copyright 2023 Jakub Matyas <jakubk.m@gmail.com>
#
# This file is part of Linien and based on redpid.
#
# Linien is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linien is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linien.  If not, see <http://www.gnu.org/licenses/>.

# this file compiles the FPGA image. You shouldn't call it directly though but
# use `build_fpga_image.sh`
from pathlib import Path

REPO_ROOT_DIR = Path(__file__).resolve().parents[1]

from .bit2bin import bit2bin


def py_csrconstants(map, fil):
    fil.write("csr_constants = {\n")
    for k, v in root.csrbanks.constants:
        if k == "linien":
            # compaitbility layer
            fil.write("    '{}': {},\n".format(v.name, v.value.value))
        else:
            fil.write("    '{}_{}': {},\n".format(k, v.name, v.value.value))
    fil.write("}\n\n")


def get_csrmap(banks):
    for name, csrs, map_addr, rmap in banks:
        reg_addr = 0
        for csr in csrs:
            yield [
                name,
                csr.name,
                map_addr,
                reg_addr,
                csr.size,
                not hasattr(csr, "status"),
            ]
            reg_addr += (csr.size + 8 - 1) // 8


def py_csrmap(it, fil):
    fil.write("csr = {\n")
    for reg in it:
        main_name = reg[0]
        secondary_name = reg[1]
        # compaitbility layer
        if main_name == "linien" or secondary_name.startswith(main_name):
            fil.write("    '{}': ({}, 0x{:03x}, {}, {}),\n".format(*reg[1:]))
        else:
            fil.write("    '{}_{}': ({}, 0x{:03x}, {}, {}),\n".format(*reg))
    fil.write("}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--platform", default=None)
    args = parser.parse_args()
    if args.platform is None or args.platform.lower() == "redpitaya":
        from gateware.hw_platform import Platform
        from gateware.targets.red_pitaya import PitayaSoC

        platform = Platform()
        root = PitayaSoC(platform)
    elif args.platform.lower() == "fastservo":
        from fast_servo.gateware.fast_servo_platform import Platform

        from gateware.targets.fast_servo import LinienFastServo

        platform = Platform()
        root = LinienFastServo(platform)
    else:
        raise ValueError("Unknown platform")

    platform.add_source_dir(REPO_ROOT_DIR / "gateware" / "verilog")
    build_dir = REPO_ROOT_DIR / "gateware" / "build"
    platform.build(root, build_name="top", build_dir=build_dir, run=True)
    with open(
        REPO_ROOT_DIR / "linien-server" / "linien_server" / "csrmap.py", "w"
    ) as fil:
        py_csrconstants(root.csrbanks.constants, fil)
        csr = get_csrmap([*root.csrbanks.banks, *root.linien.csrbanks.banks])
        py_csrmap(csr, fil)
        fil.write("states = {}\n".format(repr(root.linien.state_names)))
        fil.write("signals = {}\n".format(repr(root.linien.signal_names)))
    bit2bin(
        build_dir / "top.bit",
        REPO_ROOT_DIR / "linien-server" / "linien_server" / "gateware.bin",
        flip=True,
    )
