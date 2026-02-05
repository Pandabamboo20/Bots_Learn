from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import List, Optional, TYPE_CHECKING

from presets import ControlPreset

if TYPE_CHECKING:
    from bots import BotGenome


@dataclass
class FrameSnapshot:
    frame_index: int
    viewport: str
    inputs: List[str]


@dataclass
class RomInfo:
    name: str
    size_kb: float
    valid_header: bool
    prg_banks: int
    chr_banks: int


@dataclass
class EpisodeResult:
    distance: float
    time_seconds: float
    mistakes: int
    coins: int
    powerups: int


class EmulatorSession:
    def __init__(self, rom_path: str, preset: ControlPreset) -> None:
        self.rom_path = Path(rom_path)
        self.preset = preset
        self.is_running = False
        self.goal_distance = 100.0
        self.rom_info = self._load_rom_info()
        self.seed = int(self.rom_path.stat().st_size) if self.rom_path.exists() else 1337

    def _load_rom_info(self) -> RomInfo:
        name = self.rom_path.stem
        if not self.rom_path.exists():
            return RomInfo(name=name, size_kb=0.0, valid_header=False, prg_banks=0, chr_banks=0)
        data = self.rom_path.read_bytes()
        size_kb = round(len(data) / 1024, 2)
        valid_header = data[:4] == b"NES\x1a"
        prg_banks = data[4] if len(data) > 4 else 0
        chr_banks = data[5] if len(data) > 5 else 0
        return RomInfo(
            name=name,
            size_kb=size_kb,
            valid_header=valid_header,
            prg_banks=prg_banks,
            chr_banks=chr_banks,
        )

    def evaluate_bot(
        self,
        genome: BotGenome,
        rng: Random,
        preset: Optional[ControlPreset] = None,
    ) -> EpisodeResult:
        self.is_running = True
        preset_to_use = preset or self.preset
        action_complexity = len(preset_to_use.buttons) + len(preset_to_use.sequences)
        reflex_score = max(0.1, 1.0 - genome.reaction_time)
        decision_score = max(0.1, genome.jump_timing + genome.risk_tolerance)
        bias_score = sum(genome.action_biases.values()) / max(1, len(genome.action_biases))
        raw_skill = (reflex_score * 0.4 + decision_score * 0.4 + bias_score * 0.2)
        difficulty = max(0.6, 1.2 - action_complexity * 0.03)
        noise = rng.uniform(-3.0, 4.0)
        distance = min(self.goal_distance, max(0.0, raw_skill * 110 * difficulty + noise))
        time_seconds = max(10.0, 320 - distance * 2.6 + rng.uniform(-6.0, 8.0))
        mistakes = int(max(0, 15 - distance / 8 + rng.uniform(-2.0, 3.0)))
        coins = int(max(0, distance / 4 + rng.uniform(-5.0, 5.0)))
        powerups = int(max(0, distance / 35 + rng.uniform(-1.0, 2.0)))
        return EpisodeResult(
            distance=round(distance, 2),
            time_seconds=round(time_seconds, 2),
            mistakes=mistakes,
            coins=coins,
            powerups=powerups,
        )

    def get_leader_frames(self) -> List[FrameSnapshot]:
        return [
            FrameSnapshot(
                frame_index=index,
                viewport=f"Frame {index}: desplazamiento +{index * 5}",
                inputs=["RUN", "JUMP"],
            )
            for index in range(6)
        ]

    def stop(self) -> None:
        self.is_running = False
