from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Dict, List

from emulation import EmulatorSession, EpisodeResult
from presets import ControlPreset


@dataclass
class BotGenome:
    action_biases: Dict[str, float]
    reaction_time: float
    risk_tolerance: float
    jump_timing: float

    @classmethod
    def random(cls, rng: Random) -> "BotGenome":
        return cls(
            action_biases={
                "RUN": rng.uniform(0.4, 1.0),
                "JUMP": rng.uniform(0.4, 1.0),
                "DUCK": rng.uniform(0.0, 0.6),
                "FIRE": rng.uniform(0.0, 0.8),
            },
            reaction_time=rng.uniform(0.1, 0.6),
            risk_tolerance=rng.uniform(0.2, 0.9),
            jump_timing=rng.uniform(0.2, 0.9),
        )

    def mutate(self, rng: Random) -> "BotGenome":
        def tweak(value: float, delta: float = 0.12) -> float:
            return min(1.0, max(0.0, value + rng.uniform(-delta, delta)))

        return BotGenome(
            action_biases={key: tweak(value) for key, value in self.action_biases.items()},
            reaction_time=tweak(self.reaction_time, 0.08),
            risk_tolerance=tweak(self.risk_tolerance),
            jump_timing=tweak(self.jump_timing),
        )

    def crossover(self, rng: Random, other: "BotGenome") -> "BotGenome":
        merged = {
            key: (self.action_biases[key] if rng.random() > 0.5 else other.action_biases[key])
            for key in self.action_biases
        }
        return BotGenome(
            action_biases=merged,
            reaction_time=rng.choice([self.reaction_time, other.reaction_time]),
            risk_tolerance=rng.choice([self.risk_tolerance, other.risk_tolerance]),
            jump_timing=rng.choice([self.jump_timing, other.jump_timing]),
        )


@dataclass
class BotState:
    distance: float
    time_seconds: float
    mistakes: int
    coins: int
    powerups: int
    genome: BotGenome


@dataclass
class GenerationResult:
    generation: int
    best_distance: float
    best_time: float
    avg_distance: float
    avg_time: float
    success_rate: float
    leader_state: BotState
    elite_states: List[BotState]
    goal_reached: bool


class BotPopulation:
    def __init__(
        self, bot_count: int, preset: ControlPreset, elite_fraction: float = 0.15
    ) -> None:
        self.bot_count = bot_count
        self.preset = preset
        self.elite_fraction = max(0.05, min(0.4, elite_fraction))
        rng = Random(42)
        self.genomes = [BotGenome.random(rng) for _ in range(bot_count)]

    def run_generation(
        self, session: EmulatorSession, generation: int
    ) -> GenerationResult:
        rng = Random(session.seed + generation * 17)
        results = [self._simulate_bot(session, genome, rng) for genome in self.genomes]
        results.sort(key=lambda state: (-state.distance, state.time_seconds))
        leader_state = results[0]
        avg_distance = sum(state.distance for state in results) / len(results)
        avg_time = sum(state.time_seconds for state in results) / len(results)
        success_rate = sum(1 for state in results if state.distance >= session.goal_distance) / len(
            results
        )
        goal_reached = leader_state.distance >= session.goal_distance
        elite_count = max(2, int(len(results) * self.elite_fraction))
        elite_states = results[: min(5, elite_count)]
        self.genomes = self._next_generation(results, elite_count, rng)

        return GenerationResult(
            generation=generation,
            best_distance=leader_state.distance,
            best_time=leader_state.time_seconds,
            avg_distance=round(avg_distance, 2),
            avg_time=round(avg_time, 2),
            success_rate=success_rate,
            leader_state=leader_state,
            elite_states=elite_states,
            goal_reached=goal_reached,
        )

    def _simulate_bot(
        self, session: EmulatorSession, genome: BotGenome, rng: Random
    ) -> BotState:
        episode: EpisodeResult = session.evaluate_bot(genome, rng, self.preset)
        return BotState(
            distance=episode.distance,
            time_seconds=episode.time_seconds,
            mistakes=episode.mistakes,
            coins=episode.coins,
            powerups=episode.powerups,
            genome=genome,
        )

    def _next_generation(
        self, ranked: List[BotState], elite_count: int, rng: Random
    ) -> List[BotGenome]:
        elites = [state.genome for state in ranked[:elite_count]]
        next_gen = elites.copy()
        while len(next_gen) < self.bot_count:
            parent_a = rng.choice(elites)
            parent_b = rng.choice(elites)
            child = parent_a.crossover(rng, parent_b).mutate(rng)
            next_gen.append(child)
        return next_gen
