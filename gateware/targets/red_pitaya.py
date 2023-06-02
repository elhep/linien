# Copyright 2014-2015 Robert Jördens <jordens@gmail.com>
# Copyright 2018-2022 Benjamin Wiegand <benjamin.wiegand@physik.hu-berlin.de>
# Copyright 2021-2023 Bastian Leykauf <leykauf@physik.hu-berlin.de>
# Copyright 2022 Christian Freier <christian.freier@nomadatomics.com>
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

from migen import *
from misoc.interconnect import csr_bus
from misoc.interconnect.csr import AutoCSR

from gateware.linien_module import DummyHK, LinienModule
from gateware.logic.delta_sigma import DeltaSigma
from gateware.lowlevel.analog import PitayaAnalog
from gateware.lowlevel.crg import CRG
from gateware.lowlevel.dna import DNA
from gateware.lowlevel.gpio import Gpio
from gateware.lowlevel.pitaya_ps import PitayaPS, Sys2CSR, SysCDC, SysInterconnect
from gateware.lowlevel.xadc import XADC


class PitayaSoC(Module, AutoCSR):
    def __init__(self, platform):
        self.csr_map = {
            "gpio_n": 30,
            "gpio_p": 31,
            "dna": 28,
            "xadc": 29,
        }
        self.soc_name = "RedPitaya"
        self.interconnect_slaves = []

        self.submodules.ps = PitayaPS(platform.request("cpu"))
        self.submodules.crg = CRG(
            platform.request("clk125"), self.ps.fclk[0], ~self.ps.frstn[0]
        )
        self.submodules.sys2csr = Sys2CSR()
        self.submodules.syscdc = SysCDC()
        self.comb += self.syscdc.target.connect(self.sys2csr.sys)

        self.submodules.xadc = XADC(platform.request("xadc"))
        self.submodules.analog = PitayaAnalog(platform.request("adc"), platform.request("dac"))

        for i in range(4):
            pwm = platform.request("pwm", i)
            ds = ClockDomainsRenamer("sys_double")(DeltaSigma(width=15))
            self.comb += pwm.eq(ds.out)
            setattr(self.submodules, f"ds{i}", ds)

        exp = platform.request("exp")
        self.submodules.gpio_n = Gpio(exp.n)
        self.submodules.gpio_p = Gpio(exp.p)

        leds = Cat(*(platform.request("user_led", i) for i in range(8)))
        self.comb += leds.eq(self.gpio_n.o)

        self.submodules.dna = DNA(version=2)
        
        # ---------------------------------------------
        # 
        # FIXME - passing self to LinienModule
        self.submodules.linien = LinienModule(self)
        self.add_interconnect_slave(self.syscdc.source)
        self.run_finalize()


    def add_interconnect_slave(self, slave):
        self.interconnect_slaves.append(slave)

    def get_csr_dev_address(self, name, memory):
        if memory is not None:
            name = name + "_" + memory.name_override
        try:
            return self.csr_map[name]
        except KeyError:
            return None

    def run_finalize(self):
        self.submodules.csrbanks = csr_bus.CSRBankArray(self,
            self.get_csr_dev_address)
        self.submodules.csrcon = csr_bus.Interconnect(
            self.sys2csr.csr, [*self.csrbanks.get_buses(), *self.linien.csrbanks.get_buses()]
        )
        self.submodules.hk = DummyHK()
        self.submodules.interconnect = SysInterconnect(
            self.ps.axi.sys,
            self.hk.sys,
            *self.interconnect_slaves
        )
