import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb_fault_injection.yosys_json_parser import parse_ff_info
from cocotb_fault_injection import (
    HierarchyFaultInjector,
    BoundedRandomTimer,
    SEEsPerNode
)
from cocotb_fault_injection.strategy import RandomInjectionStrategy
import logging

CLOCK_PERIOD_NS = 10
DEFAULT_BAUD_DIVIDER = 5
BIT_PERIOD_NS_DEFAULT = 16 * DEFAULT_BAUD_DIVIDER * CLOCK_PERIOD_NS

TX_REG_ADDR    = 0x04
RX_REG_ADDR    = 0x08
STATUS_REG_ADDR= 0x0C
DELAY_REG_ADDR = 0x10

def uart_frame(data: int) -> list:
    return [0] + [(data >> i) & 1 for i in range(8)] + [1]

async def reset_dut(dut):
    dut.RST_N.value       = 0
    dut.io_SIN.value      = 1
    dut.EN_write_req.value= 0
    dut.EN_read_req.value = 0
    await Timer(CLOCK_PERIOD_NS * 5, units="ns")
    dut.RST_N.value       = 1
    await Timer(CLOCK_PERIOD_NS * 10, units="ns")
    cocotb.log.info("DUT Reset Complete")


async def start_fault_injection(dut):
    # Parse the flip-flop info from yosys.json

    seugen = HierarchyFaultInjector(
        root=dut,
        exclude_names=["CLK", "RST_N"],
        mttf_timer=BoundedRandomTimer(mttf_min=50, mttf_max=100, units="ns"),
        transient_duration_timer=BoundedRandomTimer(mttf_min=10, mttf_max=20, units="ns"),
        injection_strategy=RandomInjectionStrategy(),
        injection_goal=SEEsPerNode(30),
        log_level=logging.INFO
    )

    print("SEU Candidates:")
    for s in seugen._seu_signals:  # ✅ FIXED: was 'injector'
        print(s["handle"]._path)

    cocotb.log.info(f"Found {len(seugen._seu_signals)} SEU targets, "
                    f"{len(seugen._set_signals)} SET targets")
    for sig in seugen._seu_signals:
        cocotb.log.info(f"  SEU target handle: {sig['handle']._path}")

    cocotb.start_soon(seugen.start())
    return seugen

# TX Test With Faults
@cocotb.test()
async def uart_tx_test_with_fault(dut):
    cocotb.log.info("TX Test with Fault Injection")
    cocotb.start_soon(Clock(dut.CLK, CLOCK_PERIOD_NS, units="ns").start())
    await reset_dut(dut)

    seugen = await start_fault_injection(dut)

    tx_byte = 0xA3
    expected_bits = uart_frame(tx_byte)

    dut.write_req_addr.value = TX_REG_ADDR
    dut.write_req_data.value = tx_byte
    dut.write_req_size.value = 0
    dut.EN_write_req.value  = 1
    await RisingEdge(dut.CLK)
    dut.EN_write_req.value  = 0

    dut.write_req_addr.value = DELAY_REG_ADDR
    dut.write_req_data.value = 1
    dut.write_req_size.value = 1
    dut.EN_write_req.value  = 1
    await RisingEdge(dut.CLK)
    dut.EN_write_req.value  = 0

    await FallingEdge(dut.io_SOUT)
    await Timer(BIT_PERIOD_NS_DEFAULT/2, units="ns")

    received_bits = []
    for _ in range(10):
        received_bits.append(dut.io_SOUT.value.integer)
        await Timer(BIT_PERIOD_NS_DEFAULT, units="ns")

    cocotb.log.info(f"TX byte written: 0x{tx_byte:02X}")
    cocotb.log.info(f"Expected frame: {expected_bits}")
    cocotb.log.info(f"Observed frame: {received_bits}")

    mismatches = []
    for i, (e, o) in enumerate(zip(expected_bits, received_bits)):
        if e != o:
            mismatches.append((i, e, o))
            cocotb.log.warning(f"Bit {i}: expected {e}, got {o}")

    if not mismatches:
        cocotb.log.info("TX output unaffected by fault")
    else:
        cocotb.log.warning(f"TX corrupted in {len(mismatches)} bit(s)")

    seugen.stop()
    await seugen.join()
    seugen.print_summary()

# RX Test With Faults
@cocotb.test()
async def uart_rx_test_with_fault(dut):
    cocotb.log.info("RX Test with Fault Injection")
    cocotb.start_soon(Clock(dut.CLK, CLOCK_PERIOD_NS, units="ns").start())
    await reset_dut(dut)

    seugen = await start_fault_injection(dut)

    tx_byte = 0xC1
    bits_to_send = uart_frame(tx_byte)

    for bit in bits_to_send:
        dut.io_SIN.value = bit
        await Timer(BIT_PERIOD_NS_DEFAULT, units="ns")
    dut.io_SIN.value = 1
    await Timer(BIT_PERIOD_NS_DEFAULT*2, units="ns")

    dut.read_req_addr.value = RX_REG_ADDR
    dut.read_req_size.value = 1
    dut.EN_read_req.value  = 1
    await RisingEdge(dut.CLK)
    dut.EN_read_req.value  = 0
    await RisingEdge(dut.CLK)

    full_val      = dut.read_req.value.integer
    received_byte = (full_val >> 1) & 0xFF

    cocotb.log.info(f"Expected RX byte: 0x{tx_byte:02X}")
    cocotb.log.info(f"Received RX byte: 0x{received_byte:02X}")

    if received_byte == tx_byte:
        cocotb.log.info("RX output unaffected by fault")
    else:
        cocotb.log.warning("RX mismatch due to fault")

    seugen.stop()
    await seugen.join()
    seugen.print_summary()
