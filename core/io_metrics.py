from dataclasses import dataclass

@dataclass
class IOMetrics:
    reads: int = 0
    writes: int = 0

    def reset(self) -> None:
        self.reads = 0
        self.writes = 0

    def read(self, n: int = 1) -> None:
        self.reads += n

    def write(self, n: int = 1) -> None:
        self.writes += n
