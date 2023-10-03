#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Modbus register abstraction class

Used to add, remove, set and get values or states of a register.
Additional helper properties and functions like getters for changed registers
are available as well.

This class is inherited by the Modbus client implementations
:py:class:`umodbus.serial.ModbusRTU` and :py:class:`umodbus.tcp.ModbusTCP`
"""

# system packages
import time

# custom packages
from . import functions
from . import const as Const
from .common import Request

# typing not natively supported on MicroPython
from .typing import Callable, dict_keys, List, Optional, Union


class Modbus(object):
    """
    Modbus register abstraction

    :param      itf:        Abstraction interface
    :type       itf:        Callable
    :param      addr_list:  List of addresses
    :type       addr_list:  List[int]
    """
    def __init__(self, itf, addr_list: List[int], default_value=None) -> None:
        self._itf = itf
        self._addr_list = addr_list
        self.default_value = default_value
        self._register_dict = dict()

    def process(self) -> bool:
        """
        Process the Modbus requests.

        :returns:   Result of processing, True on success, False otherwise
        :rtype:     bool
        """
        req_type = None

        request = self._itf.get_request(unit_addr_list=self._addr_list,
                                        timeout=0)
        if request is None:
            return False

        if request.function == Const.READ_HOLDING_REGISTERS:
            # Hregs (setter+getter) [0, 65535]
            # function 03 - read holding register
            req_type = 'READ'
        elif (request.function == Const.WRITE_SINGLE_REGISTER or
                request.function == Const.WRITE_MULTIPLE_REGISTERS):
            # Hregs (setter+getter) [0, 65535]
            # function 06 - write holding register
            # function 16 - write multiple holding register
            req_type = 'WRITE'
        else:
            request.send_exception(Const.ILLEGAL_FUNCTION)

        if req_type == 'READ':
            self._process_read_access(request=request)
        elif req_type == 'WRITE':
            self._process_write_access(request=request)

        return True

    def _create_response(self, request: Request) -> Union[List[bool], List[int]]:
        """
        Create a response.

        :param      request:   The request
        :type       request:   Request

        :returns:   Values of this register
        :rtype:     Union[List[bool], List[int]]
        """
        data = []
        default_value = 0xFFFF if self.default_value is None else self.default_value
        reg_dict = self._register_dict

        for addr in range(request.register_addr,
                          request.register_addr + request.quantity):
            value = reg_dict.get(addr, default_value)
            data.append(value)

        # caution LSB vs MSB
        # [
        #   1, 0, 1, 1, 0, 0, 1, 1,     # 0xB3
        #   1, 1, 0, 1, 0, 1, 1, 0,     # 0xD6
        #   1, 0, 1                     # 0x5
        # ]
        # but should be, documented at #38, see
        # https://github.com/brainelectronics/micropython-modbus/issues/38
        # this is only an issue of data provisioning as client/slave,
        # it has thereby NOT to be fixed in
        # :py:function:`umodbus.functions.bytes_to_bool`
        # [
        #   1, 1, 0, 0, 1, 1, 0, 1,     # 0xCD
        #   0, 1, 1, 0, 1, 0, 1, 1,     # 0x6B
        #   1, 0, 1                     # 0x5
        # ]
        #       27 .... 20
        # CD    1100 1101
        #
        #       35 .... 28
        # 6B    0110 1011
        #
        #       43 .... 36
        # 05    0000 0101
        #
        # 1011 0011   1101 0110   1010 0000

        return data

    def _process_read_access(self, request: Request) -> None:
        """
        Process read access to register

        :param      request:   The request
        :type       request:   Request
        """
        address = request.register_addr

        # If a default value is specified, then we always return a response,
        # so it doesn't matter if the address is not in the store.
        if self.default_value is not None or address in self._register_dict:
            vals = self._create_response(request=request)
            request.send_response(vals)
        else:
            request.send_exception(Const.ILLEGAL_DATA_ADDRESS)

    def _process_write_access(self, request: Request) -> None:
        """
        Process write access to register

        :param      request:   The request
        :type       request:   Request
        """
        address = request.register_addr
        val = 0

        if address in self._register_dict:
            if request.data is None:
                request.send_exception(Const.ILLEGAL_DATA_VALUE)
                return

            val = list(functions.to_short(byte_array=request.data, signed=False))

            if request.function in [Const.WRITE_SINGLE_REGISTER,
                                    Const.WRITE_MULTIPLE_REGISTERS]:
                self.set_hreg(address=address, value=val)

            request.send_response()
        else:
            request.send_exception(Const.ILLEGAL_DATA_ADDRESS)

    def set_hreg(self, address: int, value: Union[int, List[int]] = 0) -> None:
        """
        Set the holding register value.

        :param      address:  The address (ID) of the register
        :type       address:  int
        :param      value:    The default value
        :type       value:    int or list of int, optional
        """
        if isinstance(value, (list, tuple)):
            # flatten the list and add single registers only
            for idx, val in enumerate(value):
                this_addr = address + idx
                self._register_dict[this_addr] = val
        else:
            self._register_dict[address] = value

    def get_hreg(self, address: int) -> Union[int, List[int]]:
        """
        Get the holding register value.

        :param      address:  The address (ID) of the register
        :type       address:  int

        :returns:   Holding register value
        :rtype:     Union[int, List[int]]
        """
        if address in self._register_dict:
            return self._register_dict[address]
        else:
            raise KeyError('No value available for the register address {}'.
                           format(address))

    def setup_registers(self, registers: List) -> None:
        """
        Setup all registers of the client

        :param      registers:         The registers
        :type       registers:         dict
        """
        for address, sz, value in registers:
            self.set_hreg(address=address, value=value)
