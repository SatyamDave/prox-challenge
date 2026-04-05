"""
Lightweight verification for structured machine answers.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


class VerificationEngine:
    def verify(
        self,
        analysis: Dict[str, Any],
        simulation: Dict[str, Any],
        artifact: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        verified_simulation = deepcopy(simulation)
        verified_artifact = deepcopy(artifact) if artifact else None
        warnings: List[str] = []

        if analysis.get("primary_intent") == "polarity":
            verified_simulation, verified_artifact, warnings = self._verify_polarity(
                verified_simulation,
                verified_artifact,
            )

        return {
            "simulation": verified_simulation,
            "artifact": verified_artifact,
            "warnings": warnings,
        }

    def _verify_polarity(
        self,
        simulation: Dict[str, Any],
        artifact: Optional[Dict[str, Any]],
    ) -> tuple[Dict[str, Any], Optional[Dict[str, Any]], List[str]]:
        warnings: List[str] = []
        state = simulation.get("state", {})
        constraints = state.get("constraints", {})
        components = state.get("components", {})
        derived = state.get("derived", {})

        expected = constraints.get("expectedPolarity")
        torch_terminal = components.get("torch", {}).get("terminal")
        actual = "DCEN" if torch_terminal == "negative" else "DCEP" if torch_terminal == "positive" else expected
        inferred_mode = "fault" if expected and actual and actual != expected else "nominal"

        if simulation.get("mode") != inferred_mode:
            simulation["mode"] = inferred_mode
            warnings.append("Adjusted polarity mode to match the computed torch terminal.")

        if simulation.get("effects"):
            simulation["effects"] = [
                f"Current flow: {derived.get('currentFlow')}",
                f"Weld outcome: {derived.get('weldOutcome')}",
            ]

        comparison = simulation.get("comparison")
        if comparison:
            before = comparison.get("before", {})
            after = comparison.get("after", {})
            comparison["diff"] = {
                "currentFlow": {
                    "before": before.get("derived", {}).get("currentFlow"),
                    "after": after.get("derived", {}).get("currentFlow"),
                },
                "torchHeat": {
                    "before": before.get("derived", {}).get("heatDistribution", {}).get("torch"),
                    "after": after.get("derived", {}).get("heatDistribution", {}).get("torch"),
                },
                "workpieceHeat": {
                    "before": before.get("derived", {}).get("heatDistribution", {}).get("workpiece"),
                    "after": after.get("derived", {}).get("heatDistribution", {}).get("workpiece"),
                },
                "weldOutcome": {
                    "before": before.get("derived", {}).get("weldOutcome"),
                    "after": after.get("derived", {}).get("weldOutcome"),
                },
            }

        if artifact and artifact.get("type") == "polarity_diagram":
            data = artifact.setdefault("data", {})
            data["simulationMode"] = simulation.get("mode")
            data["comparison"] = simulation.get("comparison")
            data["effects"] = simulation.get("effects", [])
            outcome_headline = data.get("outcomeHeadline", "FAILURE RISK — Invalid state" if simulation.get("mode") == "fault" else "SAFE — Recommended")
            data["statusBadges"] = [
                {
                    "label": outcome_headline,
                    "tone": "danger" if simulation.get("mode") == "fault" else "success",
                },
                {
                    "label": "Heat shifts to the torch" if simulation.get("mode") == "fault" else "Heat stays in the workpiece",
                    "tone": "warning" if simulation.get("mode") == "fault" else "info",
                },
            ]

        return simulation, artifact, warnings
