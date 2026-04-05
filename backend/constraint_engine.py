"""
Deterministic constraint engine for machine-state validation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from domain_knowledge import WeldingDomainKnowledge


class ConstraintEngine:
    def __init__(self, domain_knowledge: WeldingDomainKnowledge):
        self.domain_knowledge = domain_knowledge

    def validate_state(
        self,
        analysis: Dict[str, Any],
        simulation: Dict[str, Any],
        query: str, # Added query parameter
    ) -> Dict[str, Any]:
        state = simulation.get("state", {})
        intent = analysis.get("primary_intent")

        if intent == "polarity":
            return self._validate_polarity_state(state, simulation)
        if intent == "duty_cycle":
            return self._validate_duty_cycle_state(state, query) # Pass query to duty_cycle validation
        if intent == "troubleshooting":
            return self._validate_troubleshooting_state(state)
        return self._validate_setup_state(state)

    def _validate_polarity_state(self, state: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        process = state.get("process")
        material = state.get("components", {}).get("workpiece", {}).get("material") or state.get("material")

        # Hard fail on missing process
        if not process:
            return self._package(
                False,
                "INSUFFICIENT_STATE",
                "Specify the welding process (MIG, TIG, Stick, Flux-Cored).",
                [
                    {"label": "Immediate", "text": "Polarity cannot be determined without knowing the welding process."},
                    {"label": "Short term", "text": "No valid connection setup can be recommended."},
                    {"label": "Continued use", "text": "The system remains unable to validate polarity."},
                ],
                [
                    self._trace(
                        rule="process_required_for_polarity",
                        passed=False,
                        severity="INSUFFICIENT_STATE",
                        detail="Missing process parameter. Cannot determine expected polarity.",
                    ),
                ],
            )

        # Default material to steel ONLY for polarity (domain fact: steel is baseline assumption for process-level polarity)
        if not material:
            material = "steel"

        expected = state.get("constraints", {}).get("expectedPolarity") or self.domain_knowledge.infer_polarity(process, material)["polarity"]
        torch_terminal = state.get("components", {}).get("torch", {}).get("terminal")
        actual = "DCEN" if torch_terminal == "negative" else "DCEP" if torch_terminal == "positive" else expected

        trace = [
            self._trace(
                rule="process_polarity_rule",
                passed=actual == expected,
                severity="DAMAGE RISK" if process.upper() == "TIG" else "FAILURE RISK",
                detail=f"{process} requires {expected}. Torch terminal resolves to {actual}.",
            ),
        ]

        if actual != expected:
            outcome = "DAMAGE RISK" if process.upper() == "TIG" else "FAILURE RISK"
            instruction = f"Set {process} to {expected}. Put the torch on {'negative' if expected == 'DCEN' else 'positive'} and the work clamp on {'positive' if expected == 'DCEN' else 'negative'}."
            if process.upper() == "TIG":
                consequences = [
                    {"label": "Immediate", "text": "Heat shifts into the torch. The tungsten electrode overheats."},
                    {"label": "Short term", "text": "The arc destabilizes. Tungsten contamination of the weld occurs."},
                    {"label": "Continued use", "text": "The torch is damaged. The weld fails completely."},
                ]
            elif process.upper() == "FLUX_CORE":
                consequences = [
                    {"label": "Immediate", "text": "Arc instability increases. Spatter generation is excessive."},
                    {"label": "Short term", "text": "Poor penetration and fusion result. Weld quality degrades significantly."},
                    {"label": "Continued use", "text": "The weld fails to meet structural requirements. Equipment wear accelerates."},
                ]
            else:
                consequences = [
                    {"label": "Immediate", "text": "Heat shifts away from the workpiece. Arc stability drops."},
                    {"label": "Short term", "text": "Penetration decreases. Bead profile is poor."},
                    {"label": "Continued use", "text": "The weld fails. Equipment experiences increased stress."},
                ]
            return self._package(False, outcome, instruction, consequences, trace)

        instruction = f"Use {expected} for {process}. Keep the torch on {'negative' if expected == 'DCEN' else 'positive'} and the work clamp on {'positive' if expected == 'DCEN' else 'negative'}."
        consequences = [
            {"label": "Immediate", "text": "Current flows in the intended direction. Arc is stable."},
            {"label": "Short term", "text": "Heat distribution is correct. Penetration is optimal."},
            {"label": "Continued use", "text": "Consumable wear is controlled. Weld quality is consistent."},
        ]
        return self._package(True, "SAFE", instruction, consequences, trace)

    def _validate_duty_cycle_state(self, state: Dict[str, Any], query: str) -> Dict[str, Any]: # Added query parameter
        voltage = state.get("components", {}).get("powerSource", {}).get("inputVoltage")
        amperage = int(state.get("constraints", {}).get("targetAmperage")) if state.get("constraints", {}).get("targetAmperage") else None
        duty_cycle = int(state.get("constraints", {}).get("dutyCycle")) if state.get("constraints", {}).get("dutyCycle") else 0
        
        # Check for continuous operation
        query_lower = (query or "").lower()
        is_continuous_request = "continuous" in query_lower or "continuously" in query_lower

        if is_continuous_request and duty_cycle < 100:
            trace = [
                self._trace(
                    rule="continuous_operation_duty_cycle_rule",
                    passed=False,
                    severity="FAILURE RISK",
                    detail=f"Continuous operation requested, but duty cycle is {duty_cycle}% (less than 100%).",
                ),
            ]
            return self._package(
                False,
                "FAILURE RISK",
                f"Do not run continuously. Operate within {duty_cycle}% duty cycle. Continuous operation requires 100% duty cycle.",
                [
                    {"label": "Immediate", "text": "The machine will overheat rapidly during continuous operation."},
                    {"label": "Short term", "text": "Thermal shutdown will occur. Components will experience accelerated wear."},
                    {"label": "Continued use", "text": "Machine damage is inevitable. Production stops."},
                ],
                trace,
            )

        # Original logic for duty cycle validation
        amp_range = self.domain_knowledge.duty_cycle_patterns.get(voltage, self.domain_knowledge.duty_cycle_patterns["240V"])["range"]

        trace = [
            self._trace(
                rule="input_range_rule",
                passed=amp_range[0] <= amperage <= amp_range[1],
                severity="FAILURE RISK",
                detail=f"{voltage} supports {amp_range[0]}A to {amp_range[1]}A. Requested point is {amperage}A.",
            ),
            self._trace(
                rule="thermal_limit_rule",
                passed=duty_cycle > 0,
                severity="FAILURE RISK",
                detail=f"Computed duty cycle at the requested point is {duty_cycle}%.",
            ),
        ]

        if not amp_range[0] <= amperage <= amp_range[1]:
            return self._package(
                False,
                "FAILURE RISK",
                f"Keep {voltage} operation inside {amp_range[0]}A to {amp_range[1]}A. Reduce the target from {amperage}A.",
                [
                    {"label": "Immediate", "text": "The requested operating point sits outside the supported input envelope. The machine cannot sustain this output."},
                    {"label": "Short term", "text": "Output stability breaks. Thermal stress rises rapidly. Components degrade."},
                    {"label": "Continued use", "text": "Protection trips. Internal wear accelerates. Machine failure occurs."},
                ],
                trace,
            )

        if duty_cycle == 0:
            return self._package(
                False,
                "FAILURE RISK",
                f"The machine cannot operate at {amperage}A on {voltage}. The duty cycle is 0%.",
                [
                    {"label": "Immediate", "text": "No welding operation is possible at this setting. The machine will not produce an arc."},
                    {"label": "Short term", "text": "The machine remains idle. Production stops."},
                    {"label": "Continued use", "text": "No work is completed. Operational goals are not met."},
                ],
                trace,
            )

        if duty_cycle <= 10: # Very low duty cycle
            return self._package(
                True,
                "SUBOPTIMAL",
                f"Use {amperage}A only for extremely short weld windows on {voltage}. Stop at the thermal limit and cool the machine fully.",
                [
                    {"label": "Immediate", "text": f"The machine allows only a {duty_cycle}% weld window at this output. Welding time is minimal."},
                    {"label": "Short term", "text": "Cooling time significantly exceeds welding time. Productivity is severely impacted."},
                    {"label": "Continued use", "text": "Thermal protection trips frequently. Throughput drops to unacceptable levels."},
                ],
                trace,
            )

        return self._package(
            True,
            "SAFE",
            f"Use {amperage}A on {voltage} inside the {duty_cycle}% duty-cycle window.",
            [
                {"label": "Immediate", "text": "The requested operating point stays inside the supported input envelope. Arc initiates reliably."},
                {"label": "Short term", "text": f"The machine welds for the computed {duty_cycle}% window without exceeding the thermal limit. Consistent output is maintained."},
                {"label": "Continued use", "text": "Thermal protection remains inactive if the cooldown window is observed. Machine longevity is preserved."},
            ],
            trace,
        )

    def _validate_setup_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # HARD FAIL on missing required parameters — no defaults allowed
        process = state.get("process")
        material = state.get("material")
        thickness = state.get("thickness")
        target_amp = state.get("constraints", {}).get("targetAmperage") or state.get("targetAmperage")

        missing = []
        if not process:
            missing.append("process")
        if not material:
            missing.append("material")
        if not thickness:
            missing.append("thickness")

        if missing:
            return self._package(
                False,
                "INSUFFICIENT_STATE",
                f"Specify required parameters: {', '.join(missing)}.",
                [
                    {"label": "Immediate", "text": "The system cannot determine a valid setup without the missing parameters."},
                    {"label": "Short term", "text": "No machine state can be reliably computed."},
                    {"label": "Continued use", "text": "The system remains unable to provide a deterministic decision."},
                ],
                [
                    self._trace(
                        rule="required_parameters_rule",
                        passed=False,
                        severity="INSUFFICIENT_STATE",
                        detail=f"Missing: {', '.join(missing)}. Cannot proceed without them.",
                    )
                ],
            )

        amperage = int(target_amp) if target_amp else 160
        expected = self.domain_knowledge.infer_amperage_from_material(material, thickness)
        amp_low, amp_high = expected["amperage_range"]

        trace = [
            self._trace(
                rule="material_thickness_amperage_rule",
                passed=amp_low <= amperage <= amp_high,
                severity="FAILURE RISK",
                detail=f"{thickness} {material} runs inside {amp_low}A to {amp_high}A. Computed setup point is {amperage}A.",
            )
        ]

        if amperage < amp_low or amperage > amp_high:
            return self._package(
                False,
                "FAILURE RISK",
                f"Set {process} for {thickness} {material} inside {amp_low}A to {amp_high}A. Reset the amperage before welding.",
                [
                    {"label": "Immediate", "text": "The setup operates outside the supported thickness window. Arc characteristics are unstable."},
                    {"label": "Short term", "text": "Penetration is incorrect. Bead shape is poor. Fusion defects occur."},
                    {"label": "Continued use", "text": "The weld fails to meet specifications. Joint quality is unacceptable."},
                ],
                trace,
            )

        return self._package(
            True,
            "SAFE",
            f"Use {process} at {amperage}A for {thickness} {material}. Start here and tune travel speed only after the arc stabilizes.",
            [
                {"label": "Immediate", "text": "The setup point sits inside the supported thickness window. Arc is stable and predictable."},
                {"label": "Short term", "text": "Penetration and bead shape remain within the target band. Consistent fusion is achieved."},
                {"label": "Continued use", "text": "The machine operates in a valid state for this material and thickness. Weld quality is maintained."},
            ],
            trace,
        )

    def _validate_troubleshooting_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        defect = state.get("derived", {}).get("activeDefect", "weld fault")
        top_causes = state.get("derived", {}).get("causeChain", [])[:3]
        trace = [
            self._trace(
                rule="observed_defect_rule",
                passed=False,
                severity="FAILURE RISK",
                detail=f"Observed weld state is {defect}.",
            )
        ]
        actions = ", ".join(top_causes) if top_causes else "gas flow, ground connection, and surface condition"
        return self._package(
            False,
            "FAILURE RISK",
            f"Stop welding and correct {actions}. Restart only after the defect state is removed.",
            [
                {"label": "Immediate", "text": f"The current weld state exhibits {defect}. Weld integrity is compromised."},
                {"label": "Short term", "text": "Bead quality remains outside the valid process envelope. Structural weakness is introduced."},
                {"label": "Continued use", "text": "Defects accumulate. Rework costs increase significantly. Component failure is inevitable."},
            ],
            trace,
        )

    def _trace(self, rule: str, passed: bool, severity: str, detail: str) -> Dict[str, Any]:
        return {
            "rule": rule,
            "passed": passed,
            "severity": severity,
            "detail": detail,
        }

    def _package(
        self,
        valid: bool,
        outcome: str,
        instruction: str,
        consequences: List[Dict[str, str]],
        constraint_trace: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        headline_map = {
            "SAFE": "SAFE — Recommended",
            "SUBOPTIMAL": "SUBOPTIMAL — Works but inefficient",
            "FAILURE RISK": "FAILURE RISK — Weld fails",
            "DAMAGE RISK": "DAMAGE RISK — Will damage torch",
            "INSUFFICIENT_STATE": "INSUFFICIENT STATE — Missing parameters",
        }
        violations = [item for item in constraint_trace if not item["passed"]]
        return {
            "valid": valid,
            "outcome": outcome,
            "headline": headline_map[outcome],
            "instruction": instruction,
            "consequences": consequences,
            "violations": violations,
            "constraint_trace": constraint_trace,
        }
