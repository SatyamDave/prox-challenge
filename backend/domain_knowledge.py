"""
Domain knowledge for welding - the stuff a senior welder knows by heart.
This module provides heuristics, rules of thumb, and expert knowledge
to help the agent reason when exact specifications aren't found.
"""

from typing import Dict, Any, List, Optional, Tuple
import re


class WeldingDomainKnowledge:
    """
    Encapsulates domain expertise for welding operations.
    Think of this as the "experience" that makes a tech a senior tech.
    """

    def __init__(self):
        # Typical duty cycle patterns
        self.duty_cycle_patterns = {
            "120V": {
                "range": (100, 140),
                "typical_duty": {"low": (100, 35), "mid": (120, 25), "high": (140, 20)}
            },
            "240V": {
                "range": (100, 250),
                "typical_duty": {"low": (150, 60), "mid": (200, 40), "high": (250, 30)}
            }
        }

        # Material thickness to amperage rules of thumb
        self.amperage_rules = {
            "mild_steel": {
                "1/16": (30, 50),
                "1/8": (75, 125),
                "1/4": (140, 180),
                "3/8": (200, 250)
            },
            "stainless": {
                "1/16": (25, 45),
                "1/8": (65, 115),
                "1/4": (130, 170)
            },
            "aluminum": {
                "1/16": (40, 60),
                "1/8": (90, 140),
                "1/4": (160, 200)
            }
        }

        # Wire speed to amperage relationships (MIG)
        self.wire_speed_patterns = {
            "0.023": {"range": (30, 130), "ipm_per_amp": 0.8},
            "0.030": {"range": (40, 145), "ipm_per_amp": 0.7},
            "0.035": {"range": (50, 180), "ipm_per_amp": 0.6},
            "0.045": {"range": (75, 250), "ipm_per_amp": 0.5}
        }

        # Gas flow rates by process
        self.gas_flow_rates = {
            "MIG": {"min": 15, "typical": 20, "max": 25, "unit": "CFH"},
            "TIG": {"min": 10, "typical": 15, "max": 20, "unit": "CFH"},
            "FLUX": {"min": 0, "typical": 0, "max": 0, "unit": "CFH"}  # No gas
        }

        # Polarity settings by process
        self.polarity_map = {
            "MIG_steel": "DCEP",  # DC Electrode Positive
            "MIG_aluminum": "DCEP",
            "FLUX_core": "DCEN",  # DC Electrode Negative
            "TIG_steel": "DCEN",
            "TIG_aluminum": "AC",
            "STICK_steel": "DCEP",
            "STICK_cast": "AC"
        }

        # Common troubleshooting patterns
        self.troubleshooting_rules = {
            "porosity": ["gas flow too high", "gas flow too low", "contaminated base metal", "draft/wind"],
            "spatter": ["voltage too high", "wire speed too fast", "wrong polarity", "dirty material"],
            "undercut": ["travel speed too fast", "amperage too high", "wrong angle"],
            "lack_of_penetration": ["amperage too low", "travel speed too fast", "poor fit-up"],
            "burn_through": ["amperage too high", "travel speed too slow", "gap too wide"]
        }

    def infer_duty_cycle(self, amperage: float, voltage: str = "240V") -> Dict[str, Any]:
        """
        Infer duty cycle based on amperage and voltage using typical patterns.
        Returns estimated duty cycle with confidence level.
        """
        patterns = self.duty_cycle_patterns.get(voltage, self.duty_cycle_patterns["240V"])

        # Find closest match
        closest_duty = None
        min_diff = float('inf')

        for level, (amps, duty) in patterns["typical_duty"].items():
            diff = abs(amperage - amps)
            if diff < min_diff:
                min_diff = diff
                closest_duty = duty

        # Calculate confidence based on how close we are to known values
        confidence = max(0.5, 1.0 - (min_diff / 100))

        return {
            "estimated_duty_cycle": closest_duty,
            "confidence": confidence,
            "reasoning": f"Based on typical {voltage} duty cycle patterns. At {amperage}A, expect around {closest_duty}% duty cycle.",
            "voltage": voltage,
            "note": "This is an approximation. Check manual for exact specifications."
        }

    def infer_wire_speed(self, amperage: float, wire_diameter: str = "0.035") -> Dict[str, Any]:
        """
        Estimate wire speed from amperage for MIG welding.
        """
        pattern = self.wire_speed_patterns.get(wire_diameter)

        if not pattern:
            # Default to .035 if unknown
            pattern = self.wire_speed_patterns["0.035"]
            confidence = 0.6
        else:
            confidence = 0.8

        # Rough calculation: wire speed (IPM) ≈ amperage * factor
        estimated_ipm = amperage * pattern["ipm_per_amp"]

        # Clamp to reasonable range
        min_speed, max_speed = pattern["range"]
        if estimated_ipm < min_speed:
            estimated_ipm = min_speed
            confidence *= 0.7
        elif estimated_ipm > max_speed:
            estimated_ipm = max_speed
            confidence *= 0.7

        return {
            "estimated_wire_speed_ipm": round(estimated_ipm, 1),
            "wire_diameter": wire_diameter,
            "amperage": amperage,
            "confidence": confidence,
            "reasoning": f"For {wire_diameter}\" wire at {amperage}A, typical speed is around {estimated_ipm:.0f} IPM",
            "range": f"{min_speed}-{max_speed} IPM for this wire size"
        }

    def infer_amperage_from_material(self, material: str, thickness: str) -> Dict[str, Any]:
        """
        Suggest amperage range based on material and thickness.
        """
        # Normalize material name
        material_lower = material.lower()
        if "steel" in material_lower or "mild" in material_lower:
            material_key = "mild_steel"
        elif "stainless" in material_lower:
            material_key = "stainless"
        elif "aluminum" in material_lower or "aluminium" in material_lower:
            material_key = "aluminum"
        else:
            material_key = "mild_steel"  # Default assumption

        # Parse thickness
        thickness_clean = thickness.strip().replace('"', '').replace('inch', '').strip()

        amp_data = self.amperage_rules.get(material_key, {})
        amp_range = amp_data.get(thickness_clean)

        if amp_range:
            confidence = 0.85
            min_amp, max_amp = amp_range
        else:
            # Estimate based on nearest thickness
            confidence = 0.6
            min_amp, max_amp = (100, 150)  # Generic fallback

        return {
            "material": material,
            "thickness": thickness,
            "amperage_range": (min_amp, max_amp),
            "recommended_start": (min_amp + max_amp) // 2,
            "confidence": confidence,
            "reasoning": f"For {thickness} {material}, start around {(min_amp + max_amp) // 2}A and adjust based on puddle behavior"
        }

    def infer_polarity(self, process: str, material: str = "steel") -> Dict[str, Any]:
        """
        Determine correct polarity based on process and material.
        """
        # Guard against missing process
        if not process:
            return {
                "polarity": "N/A",
                "process": "unknown",
                "material": material or "unknown",
                "confidence": 0.0,
                "reasoning": "Cannot determine polarity without knowing the welding process."
            }

        # Create lookup key
        process_upper = process.upper()
        material_lower = (material or "steel").lower()

        # Try exact match first
        for key, polarity in self.polarity_map.items():
            if process_upper in key.upper() and material_lower in key.lower():
                return {
                    "polarity": polarity,
                    "process": process,
                    "material": material,
                    "confidence": 0.95,
                    "reasoning": f"{process} on {material} uses {polarity} polarity"
                }

        # Fallback to process only
        for key, polarity in self.polarity_map.items():
            if process_upper in key.upper():
                return {
                    "polarity": polarity,
                    "process": process,
                    "material": material,
                    "confidence": 0.75,
                    "reasoning": f"{process} typically uses {polarity} polarity"
                }

        # Last resort
        return {
            "polarity": "DCEP",
            "process": process,
            "material": material,
            "confidence": 0.5,
            "reasoning": "DCEP is most common for MIG/wire processes. Verify in manual."
        }

    def diagnose_weld_defect(self, defect_description: str) -> List[Dict[str, Any]]:
        """
        Suggest likely causes for weld defects based on description.
        """
        defect_lower = defect_description.lower()
        likely_causes = []

        for defect_type, causes in self.troubleshooting_rules.items():
            if defect_type in defect_lower or any(word in defect_lower for word in defect_type.split('_')):
                likely_causes.append({
                    "defect": defect_type,
                    "likely_causes": causes,
                    "confidence": 0.8
                })

        if not likely_causes:
            # Generic troubleshooting
            likely_causes.append({
                "defect": "general",
                "likely_causes": [
                    "check amperage settings",
                    "verify wire speed",
                    "ensure proper gas flow",
                    "clean base metal",
                    "check ground connection"
                ],
                "confidence": 0.5
            })

        return likely_causes

    def cross_reference_specs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-reference multiple specs to validate/infer missing data.
        For example: if we know voltage and amperage, infer duty cycle.
        """
        inferences = {}

        # Extract what we know
        voltage = context.get("voltage")
        amperage = context.get("amperage")
        material = context.get("material")
        thickness = context.get("thickness")
        process = context.get("process")
        wire_diameter = context.get("wire_diameter")

        # Infer duty cycle if we have voltage and amperage
        if voltage and amperage:
            inferences["duty_cycle"] = self.infer_duty_cycle(amperage, voltage)

        # Infer wire speed if we have amperage
        if amperage and process and "MIG" in process.upper():
            inferences["wire_speed"] = self.infer_wire_speed(amperage, wire_diameter or "0.035")

        # Infer amperage if we have material and thickness
        if material and thickness and not amperage:
            inferences["amperage"] = self.infer_amperage_from_material(material, thickness)

        # Infer polarity if we have process
        if process:
            inferences["polarity"] = self.infer_polarity(process, material or "steel")

        return inferences

    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a set of welding parameters and flag potential issues.
        """
        warnings = []
        recommendations = []

        amperage = settings.get("amperage")
        voltage = settings.get("voltage")
        wire_speed = settings.get("wire_speed")
        gas_flow = settings.get("gas_flow")
        process = settings.get("process", "MIG")

        # Check gas flow
        if gas_flow and process.upper() in self.gas_flow_rates:
            expected = self.gas_flow_rates[process.upper()]
            if gas_flow < expected["min"]:
                warnings.append(f"Gas flow {gas_flow} CFH is below minimum {expected['min']} CFH - may cause porosity")
            elif gas_flow > expected["max"]:
                warnings.append(f"Gas flow {gas_flow} CFH is above maximum {expected['max']} CFH - wasteful and may cause turbulence")

        # Check voltage/amperage relationship for duty cycle
        if amperage and voltage:
            duty_info = self.infer_duty_cycle(amperage, voltage)
            if duty_info["estimated_duty_cycle"] < 30:
                warnings.append(f"At {amperage}A on {voltage}, duty cycle is around {duty_info['estimated_duty_cycle']}% - you'll need frequent cool-down breaks")

        return {
            "warnings": warnings,
            "recommendations": recommendations,
            "validation_confidence": 0.75
        }
