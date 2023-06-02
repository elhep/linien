# Copyright 2023 Jakub Matyas <jakubk.m@gmail.com>
# Warsaw University of Technology
#
# This file is part of Linien and provides support for Linien on
# Fast Servo platform.
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

from fast_servo.gateware.fast_servo_soc import BaseSoC
from migen import *
from misoc.interconnect import csr_bus

from gateware.linien_module import DummyHK, LinienModule
from gateware.lowlevel.dna import DNA
from gateware.lowlevel.gpio import Gpio
from gateware.lowlevel.pitaya_ps import SysInterconnect


class FastServoAnalog(Module):
    def __init__(self, adc, dac):
        size = 14       # length of DAC

        self.adc_a = Signal(size)
        self.adc_b = Signal(size)
        self.dac_a = Signal(size)
        self.dac_b = Signal(size)

        self.comb += [
            self.adc_a.eq(adc.data_out[0][2:]),
            self.adc_b.eq(adc.data_out[1][2:]),        
        ]

        self.sync += [
            dac.data_in[0].eq(self.dac_a),
            dac.data_in[1].eq(self.dac_b),
        ]


class LinienFastServo(BaseSoC):
    def __init__(self, platform):
        super().__init__(platform)
    
        self.submodules.dna = DNA(version=2)

        self.submodules.analog = FastServoAnalog(self.adc, self.dac)
        gpios = platform.request("gpio")
        self.submodules.gpio_n = Gpio(gpios.n)
        # self.csr_devices.append("gpio_n")
        self.submodules.gpio_p = Gpio(gpios.p)
        # self.csr_devices.append("gpio_p")
        self.csr_map.update({
            "dna": 28,
            "gpio_n": 30,
            "gpio_p": 31,
        })

        # ---------------------------------------------
        # 
        # FIXME - passing self to LinienModule
        self.submodules.linien = LinienModule(self)

    def soc_finalize(self):
        self.add_interconnect_slave(self.syscdc.source)
        self.submodules.csrbanks = csr_bus.CSRBankArray(self,
            self.get_csr_dev_address)
        self.submodules.csrcon = csr_bus.Interconnect(
            self.sys2csr.csr, [*self.csrbanks.get_buses(), *self.linien.csrbanks.get_buses()]
        )
        self.submodules.hk = DummyHK()
        self.submodules.interconnect = SysInterconnect(
            self.axi2sys.sys,
            self.hk.sys,
            *self.interconnect_slaves
        )
