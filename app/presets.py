import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class ControlPreset:
    game_title: str
    description: str
    buttons: Dict[str, str]
    sequences: List[Dict[str, str]]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ControlPreset":
        return cls(
            game_title=str(data["game_title"]),
            description=str(data.get("description", "")),
            buttons=dict(data.get("buttons", {})),
            sequences=list(data.get("sequences", [])),
        )


class PresetLibrary:
    @staticmethod
    def default_super_mario_bros() -> ControlPreset:
        return ControlPreset(
            game_title="Super Mario Bros (NES)",
            description=(
                "Preset por defecto para entrenar bots en el nivel 1-1. "
                "Incluye combinaciones básicas y timings recomendados."
            ),
            buttons={
                "A": "JUMP",
                "B": "RUN",
                "START": "PAUSE",
                "SELECT": "MENU",
                "UP": "LOOK",
                "DOWN": "DUCK",
                "LEFT": "MOVE_LEFT",
                "RIGHT": "MOVE_RIGHT",
            },
            sequences=[
                {"name": "salto_largo", "pattern": "RUN+JUMP", "frames": 18},
                {"name": "avance_seguro", "pattern": "MOVE_RIGHT+RUN", "frames": 30},
                {"name": "salto_rebote", "pattern": "JUMP+RUN", "frames": 12},
                {"name": "freno_rapido", "pattern": "MOVE_LEFT+DUCK", "frames": 8},
            ],
        )

    @staticmethod
    def load_from_path(path: str) -> Dict[str, object]:
        content = Path(path).read_text(encoding="utf-8")
        return json.loads(content)

    @staticmethod
    def save(path: str, preset: ControlPreset) -> None:
        payload = {
            "game_title": preset.game_title,
            "description": preset.description,
            "buttons": preset.buttons,
            "sequences": preset.sequences,
        }
        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
