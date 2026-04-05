"""
Executable state transition engine for machine behavior.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


class SimulationEngine:
    def build_base_state(
        self,
        process: str,
        material: str,
        voltage: str,
        amperage: int,
        expected_polarity: str,
    ) -> Dict[str, Any]:
        torch_terminal = "negative" if expected_polarity in {"DCEN", "AC"} else "positive"
        work_terminal = "positive" if torch_terminal == "negative" else "negative"
        return {
            "components": {
                "powerSource": {"status": "ready", "inputVoltage": voltage},
                "torch": {"terminal": torch_terminal, "heatShare": 0.3},
                "workClamp": {"terminal": work_terminal, "heatShare": 0.7},
                "workpiece": {"material": material, "penetration": "stable"},
            },
            "connections": {
                "torchLead": {"from": torch_terminal, "to": "torch"},
                "workLead": {"from": work_terminal, "to": "workClamp"},
            },
            "process": process,
            "constraints": {
                "expectedPolarity": expected_polarity,
                "targetAmperage": amperage,
                "thermal": {"accumulation": 0.35, "shutdownRisk": "low"},
            },
            "derived": {
                "currentFlow": "balanced",
                "heatDistribution": {"torch": 0.3, "workpiece": 0.7},
                "weldOutcome": "normal penetration and stable arc",
            },
        }

    def apply_change(self, state: Dict[str, Any], change: Dict[str, Any]) -> Dict[str, Any]:
        next_state = deepcopy(state)
        if change["type"] == "reverse_polarity":
            torch_terminal = next_state["components"]["torch"]["terminal"]
            work_terminal = next_state["components"]["workClamp"]["terminal"]
            next_state["components"]["torch"]["terminal"] = "positive" if torch_terminal == "negative" else "negative"
            next_state["components"]["workClamp"]["terminal"] = "positive" if work_terminal == "negative" else "negative"
            next_state["connections"]["torchLead"]["from"] = next_state["components"]["torch"]["terminal"]
            next_state["connections"]["workLead"]["from"] = next_state["components"]["workClamp"]["terminal"]
        elif change["type"] == "set_amperage":
            next_state["constraints"]["targetAmperage"] = change["value"]
        return next_state

    def propagate_effects(self, state: Dict[str, Any]) -> Dict[str, Any]:
        next_state = deepcopy(state)
        expected = next_state["constraints"]["expectedPolarity"]
        actual = "DCEN" if next_state["components"]["torch"]["terminal"] == "negative" else "DCEP"

        if actual != expected:
            next_state["derived"]["currentFlow"] = "reversed"
            next_state["derived"]["heatDistribution"] = {"torch": 0.7, "workpiece": 0.3}
            next_state["components"]["torch"]["heatShare"] = 0.7
            next_state["components"]["workClamp"]["heatShare"] = 0.3
            next_state["components"]["workpiece"]["penetration"] = "shallow"
            next_state["constraints"]["thermal"]["accumulation"] = 0.78
            next_state["constraints"]["thermal"]["shutdownRisk"] = "medium"
            next_state["derived"]["weldOutcome"] = "poor penetration, unstable arc, and elevated spatter risk"
        else:
            next_state["derived"]["currentFlow"] = "balanced"
            next_state["derived"]["heatDistribution"] = {"torch": 0.3, "workpiece": 0.7}
            next_state["components"]["torch"]["heatShare"] = 0.3
            next_state["components"]["workClamp"]["heatShare"] = 0.7
            next_state["components"]["workpiece"]["penetration"] = "stable"
            next_state["constraints"]["thermal"]["accumulation"] = 0.35
            next_state["constraints"]["thermal"]["shutdownRisk"] = "low"
            next_state["derived"]["weldOutcome"] = "normal penetration and stable arc"

        return next_state

    def simulate_polarity_transition(
        self,
        process: str,
        material: str,
        voltage: str,
        amperage: int,
        expected_polarity: str,
        reverse: bool,
    ) -> Dict[str, Any]:
        # If process is unknown, refuse to simulate
        if not process or not expected_polarity:
            return {
                "state": {},
                "baselineState": {},
                "comparison": {},
                "steps": [{"step": 1, "event": "Cannot simulate", "stateKey": "state_t0", "effect": "Missing process or polarity information."}],
                "effects": ["Insufficient state for simulation."],
                "mode": "insufficient",
            }
        state_t0 = self.build_base_state(process, material, voltage, amperage, expected_polarity)
        baseline = self.propagate_effects(state_t0)

        state_t1 = self.apply_change(baseline, {"type": "reverse_polarity"} if reverse else {"type": "set_amperage", "value": amperage})
        state_t2 = self.propagate_effects(state_t1)

        steps: List[Dict[str, Any]] = [
            {"step": 1, "event": "Construct baseline state", "stateKey": "state_t0", "effect": f"{process} expects {expected_polarity}"},
            {"step": 2, "event": "Apply configuration change", "stateKey": "state_t1", "effect": "torch/work leads reversed" if reverse else "retain nominal polarity"},
            {
                "step": 3,
                "event": "Propagate current and heat",
                "stateKey": "state_t2",
                "effect": state_t2["derived"]["weldOutcome"],
            },
        ]

        return {
            "state": state_t2,
            "baselineState": baseline,
            "comparison": {
                "before": baseline,
                "after": state_t2,
                "diff": {
                    "currentFlow": {"before": baseline["derived"]["currentFlow"], "after": state_t2["derived"]["currentFlow"]},
                    "torchHeat": {
                        "before": baseline["derived"]["heatDistribution"]["torch"],
                        "after": state_t2["derived"]["heatDistribution"]["torch"],
                    },
                    "workpieceHeat": {
                        "before": baseline["derived"]["heatDistribution"]["workpiece"],
                        "after": state_t2["derived"]["heatDistribution"]["workpiece"],
                    },
                    "weldOutcome": {"before": baseline["derived"]["weldOutcome"], "after": state_t2["derived"]["weldOutcome"]},
                },
            },
            "steps": steps,
            "effects": [
                f"Current flow: {state_t2['derived']['currentFlow']}",
                f"Weld outcome: {state_t2['derived']['weldOutcome']}",
            ],
            "mode": "fault" if reverse else "nominal",
        }
