#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright 2017 ROBOTIS CO., LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

# Author: Ryu Woon Jung (Leon)

import ctypes
import logging
from ctypes import cdll
from pathlib import Path
import sys
import platform
from unittest.mock import MagicMock

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def create_mock_dxl_device():
    """Create a mock Dynamixel device for testing and documentation.

    Returns
    -------
    dxl_lib : MagicMock
        Mock Dynamixel device.
    """
    # Create a MagicMock instance for dxl_lib
    dxl_lib = MagicMock()

    # port_handler
    dxl_lib.portHandler = MagicMock()
    dxl_lib.openPort = MagicMock()
    dxl_lib.closePort = MagicMock()
    dxl_lib.clearPort = MagicMock()
    dxl_lib.setPortName = MagicMock()
    dxl_lib.getPortName = MagicMock()
    dxl_lib.setBaudRate = MagicMock()
    dxl_lib.getBaudRate = MagicMock()
    dxl_lib.readPort = MagicMock()
    dxl_lib.writePort = MagicMock()
    dxl_lib.setPacketTimeout = MagicMock()
    dxl_lib.setPacketTimeoutMSec = MagicMock()
    dxl_lib.isPacketTimeout = MagicMock()

    # packet_handler
    dxl_lib.packetHandler = MagicMock()
    dxl_lib.printTxRxResult = MagicMock()
    dxl_lib.getTxRxResult = MagicMock()
    dxl_lib.getTxRxResult.restype = ctypes.c_char_p
    dxl_lib.printRxPacketError = MagicMock()
    dxl_lib.getRxPacketError = MagicMock()
    dxl_lib.getRxPacketError.restype = ctypes.c_char_p
    dxl_lib.getLastTxRxResult = MagicMock()
    dxl_lib.getLastRxPacketError = MagicMock()
    dxl_lib.setDataWrite = MagicMock()
    dxl_lib.getDataRead = MagicMock()
    dxl_lib.txPacket = MagicMock()
    dxl_lib.rxPacket = MagicMock()
    dxl_lib.txRxPacket = MagicMock()
    dxl_lib.ping = MagicMock()
    dxl_lib.pingGetModelNum = MagicMock()
    dxl_lib.broadcastPing = MagicMock()
    dxl_lib.getBroadcastPingResult = MagicMock()
    dxl_lib.reboot = MagicMock()
    dxl_lib.factoryReset = MagicMock()
    dxl_lib.readTx = MagicMock()
    dxl_lib.readRx = MagicMock()
    dxl_lib.readTxRx = MagicMock()
    dxl_lib.read1ByteTx = MagicMock()
    dxl_lib.read1ByteRx = MagicMock()
    dxl_lib.read1ByteTxRx = MagicMock()
    dxl_lib.read2ByteTx = MagicMock()
    dxl_lib.read2ByteRx = MagicMock()
    dxl_lib.read2ByteTxRx = MagicMock()
    dxl_lib.read4ByteTx = MagicMock()
    dxl_lib.read4ByteRx = MagicMock()
    dxl_lib.read4ByteTxRx = MagicMock()
    dxl_lib.writeTxOnly = MagicMock()
    dxl_lib.writeTxRx = MagicMock()
    dxl_lib.write1ByteTxOnly = MagicMock()
    dxl_lib.write1ByteTxRx = MagicMock()
    dxl_lib.write2ByteTxOnly = MagicMock()
    dxl_lib.write2ByteTxRx = MagicMock()
    dxl_lib.write4ByteTxOnly = MagicMock()
    dxl_lib.write4ByteTxRx = MagicMock()
    dxl_lib.regWriteTxOnly = MagicMock()
    dxl_lib.regWriteTxRx = MagicMock()
    dxl_lib.syncReadTx = MagicMock()
    dxl_lib.syncWriteTxOnly = MagicMock()
    dxl_lib.bulkReadTx = MagicMock()
    dxl_lib.bulkWriteTxOnly = MagicMock()

    # group_bulk_read
    dxl_lib.groupBulkRead = MagicMock()
    dxl_lib.groupBulkReadAddParam = MagicMock()
    dxl_lib.groupBulkReadRemoveParam = MagicMock()
    dxl_lib.groupBulkReadClearParam = MagicMock()
    dxl_lib.groupBulkReadTxPacket = MagicMock()
    dxl_lib.groupBulkReadRxPacket = MagicMock()
    dxl_lib.groupBulkReadTxRxPacket = MagicMock()
    dxl_lib.groupBulkReadIsAvailable = MagicMock()
    dxl_lib.groupBulkReadGetData = MagicMock()

    # group_bulk_write
    dxl_lib.groupBulkWrite = MagicMock()
    dxl_lib.groupBulkWriteAddParam = MagicMock()
    dxl_lib.groupBulkWriteRemoveParam = MagicMock()
    dxl_lib.groupBulkWriteChangeParam = MagicMock()
    dxl_lib.groupBulkWriteClearParam = MagicMock()
    dxl_lib.groupBulkWriteTxPacket = MagicMock()

    # group_sync_read
    dxl_lib.groupSyncRead = MagicMock()
    dxl_lib.groupSyncReadAddParam = MagicMock()
    dxl_lib.groupSyncReadRemoveParam = MagicMock()
    dxl_lib.groupSyncReadClearParam = MagicMock()
    dxl_lib.groupSyncReadTxPacket = MagicMock()
    dxl_lib.groupSyncReadRxPacket = MagicMock()
    dxl_lib.groupSyncReadTxRxPacket = MagicMock()
    dxl_lib.groupSyncReadIsAvailable = MagicMock()
    dxl_lib.groupSyncReadGetData = MagicMock()

    # group_sync_write
    dxl_lib.groupSyncWrite = MagicMock()
    dxl_lib.groupSyncWriteAddParam = MagicMock()
    dxl_lib.groupSyncWriteRemoveParam = MagicMock()
    dxl_lib.groupSyncWriteChangeParam = MagicMock()
    dxl_lib.groupSyncWriteClearParam = MagicMock()
    dxl_lib.groupSyncWriteTxPacket = MagicMock()

    return dxl_lib


is_64bits = sys.maxsize > 2**32
if platform.system() == "Darwin":
    dxl_config = (str(Path(__file__).resolve().parent) + "/libdxl_mac_c.dylib").replace(
        "\\", "/"
    )
elif platform.system() == "Windows":
    if is_64bits:
        dxl_config = (str(Path(__file__).resolve().parent) + "/dxl_x64_c.dll").replace(
            "\\", "/"
        )
    else:
        dxl_config = (str(Path(__file__).resolve().parent) + "/dxl_x86_c.dll").replace(
            "\\", "/"
        )
elif platform.system() == "Linux":
    if is_64bits:
        dxl_config = (
            str(Path(__file__).resolve().parent) + "/libdxl_x64_c.so"
        ).replace("\\", "/")
    else:
        dxl_config = (
            str(Path(__file__).resolve().parent) + "/libdxl_x86_c.so"
        ).replace("\\", "/")

if Path(dxl_config).exists():
    dxl_lib = cdll.LoadLibrary(dxl_config)
    print("ROBOTIS dll Loaded")
else:
    print(
        "Error Dynamixel DLL to Failed to Load Properly."
        "Will Mock Dynamixel Library for Testing and Documentation."
    )
    dxl_lib = create_mock_dxl_device()

# port_handler
portHandler = dxl_lib.portHandler

openPort = dxl_lib.openPort
closePort = dxl_lib.closePort
clearPort = dxl_lib.clearPort

setPortName = dxl_lib.setPortName
getPortName = dxl_lib.getPortName

setBaudRate = dxl_lib.setBaudRate
getBaudRate = dxl_lib.getBaudRate

readPort = dxl_lib.readPort
writePort = dxl_lib.writePort

setPacketTimeout = dxl_lib.setPacketTimeout
setPacketTimeoutMSec = dxl_lib.setPacketTimeoutMSec
isPacketTimeout = dxl_lib.isPacketTimeout

# packet_handler
packetHandler = dxl_lib.packetHandler

printTxRxResult = dxl_lib.printTxRxResult
getTxRxResult = dxl_lib.getTxRxResult
getTxRxResult.restype = ctypes.c_char_p
printRxPacketError = dxl_lib.printRxPacketError
getRxPacketError = dxl_lib.getRxPacketError
getRxPacketError.restype = ctypes.c_char_p

getLastTxRxResult = dxl_lib.getLastTxRxResult
getLastRxPacketError = dxl_lib.getLastRxPacketError

setDataWrite = dxl_lib.setDataWrite
getDataRead = dxl_lib.getDataRead

txPacket = dxl_lib.txPacket

rxPacket = dxl_lib.rxPacket

txRxPacket = dxl_lib.txRxPacket

ping = dxl_lib.ping

pingGetModelNum = dxl_lib.pingGetModelNum

broadcastPing = dxl_lib.broadcastPing
getBroadcastPingResult = dxl_lib.getBroadcastPingResult

reboot = dxl_lib.reboot

factoryReset = dxl_lib.factoryReset

readTx = dxl_lib.readTx
readRx = dxl_lib.readRx
readTxRx = dxl_lib.readTxRx

read1ByteTx = dxl_lib.read1ByteTx
read1ByteRx = dxl_lib.read1ByteRx
read1ByteTxRx = dxl_lib.read1ByteTxRx

read2ByteTx = dxl_lib.read2ByteTx
read2ByteRx = dxl_lib.read2ByteRx
read2ByteTxRx = dxl_lib.read2ByteTxRx

read4ByteTx = dxl_lib.read4ByteTx
read4ByteRx = dxl_lib.read4ByteRx
read4ByteTxRx = dxl_lib.read4ByteTxRx

writeTxOnly = dxl_lib.writeTxOnly
writeTxRx = dxl_lib.writeTxRx

write1ByteTxOnly = dxl_lib.write1ByteTxOnly
write1ByteTxRx = dxl_lib.write1ByteTxRx

write2ByteTxOnly = dxl_lib.write2ByteTxOnly
write2ByteTxRx = dxl_lib.write2ByteTxRx

write4ByteTxOnly = dxl_lib.write4ByteTxOnly
write4ByteTxRx = dxl_lib.write4ByteTxRx

regWriteTxOnly = dxl_lib.regWriteTxOnly
regWriteTxRx = dxl_lib.regWriteTxRx

syncReadTx = dxl_lib.syncReadTx

syncWriteTxOnly = dxl_lib.syncWriteTxOnly

bulkReadTx = dxl_lib.bulkReadTx

bulkWriteTxOnly = dxl_lib.bulkWriteTxOnly

# group_bulk_read
groupBulkRead = dxl_lib.groupBulkRead

groupBulkReadAddParam = dxl_lib.groupBulkReadAddParam
groupBulkReadRemoveParam = dxl_lib.groupBulkReadRemoveParam
groupBulkReadClearParam = dxl_lib.groupBulkReadClearParam

groupBulkReadTxPacket = dxl_lib.groupBulkReadTxPacket
groupBulkReadRxPacket = dxl_lib.groupBulkReadRxPacket
groupBulkReadTxRxPacket = dxl_lib.groupBulkReadTxRxPacket

groupBulkReadIsAvailable = dxl_lib.groupBulkReadIsAvailable
groupBulkReadGetData = dxl_lib.groupBulkReadGetData

# group_bulk_write
groupBulkWrite = dxl_lib.groupBulkWrite

groupBulkWriteAddParam = dxl_lib.groupBulkWriteAddParam
groupBulkWriteRemoveParam = dxl_lib.groupBulkWriteRemoveParam
groupBulkWriteChangeParam = dxl_lib.groupBulkWriteChangeParam
groupBulkWriteClearParam = dxl_lib.groupBulkWriteClearParam

groupBulkWriteTxPacket = dxl_lib.groupBulkWriteTxPacket

# group_sync_read
groupSyncRead = dxl_lib.groupSyncRead

groupSyncReadAddParam = dxl_lib.groupSyncReadAddParam
groupSyncReadRemoveParam = dxl_lib.groupSyncReadRemoveParam
groupSyncReadClearParam = dxl_lib.groupSyncReadClearParam

groupSyncReadTxPacket = dxl_lib.groupSyncReadTxPacket
groupSyncReadRxPacket = dxl_lib.groupSyncReadRxPacket
groupSyncReadTxRxPacket = dxl_lib.groupSyncReadTxRxPacket

groupSyncReadIsAvailable = dxl_lib.groupSyncReadIsAvailable
groupSyncReadGetData = dxl_lib.groupSyncReadGetData

# group_sync_write
groupSyncWrite = dxl_lib.groupSyncWrite

groupSyncWriteAddParam = dxl_lib.groupSyncWriteAddParam
groupSyncWriteRemoveParam = dxl_lib.groupSyncWriteRemoveParam
groupSyncWriteChangeParam = dxl_lib.groupSyncWriteChangeParam
groupSyncWriteClearParam = dxl_lib.groupSyncWriteClearParam

groupSyncWriteTxPacket = dxl_lib.groupSyncWriteTxPacket
