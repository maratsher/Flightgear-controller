import dataclasses


@dataclasses.dataclass
class Port:
    port_out: int
    port_in: int
