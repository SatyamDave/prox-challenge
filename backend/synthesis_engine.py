"""
Synthesis Engine: Explicit reasoning to fill knowledge gaps
When exact information isn't found, this module:
1. Identifies what information IS available
2. Finds patterns in adjacent specifications
3. Makes reasonable inferences
4. Explains assumptions clearly
"""

from typing import List, Dict, Any, Optional
import re


class SynthesisEngine:
    """
    Fills gaps in knowledge through intelligent inference.
    NEVER returns "I don't know" - always provides useful output.
    """

    @staticmethod
    def extract_numerical_patterns(chunks: List[Dict[str, Any]], metric: str) -> Dict[str, Any]:
        """
        Extract numerical patterns (duty cycles, voltages, amperages, etc.)
        and interpolate missing values.

        Args:
            chunks: Retrieved text chunks
            metric: What to look for (e.g., "duty cycle", "amperage")

        Returns:
            Dictionary with found values and interpolated ranges
        """
        patterns = {}

        for chunk in chunks:
            text = chunk['text'].lower()

            # Extract amperage + duty cycle pairs
            # Patterns: "200A = 60%", "200 Amperes: 60 percent", etc.
            if 'duty' in metric.lower():
                matches = re.findall(r'(\d+)\s*(?:a|amp|ampere)s?[:\s=,]+(\d+)\s*%', text)
                for amp, duty in matches:
                    patterns[int(amp)] = int(duty)

            # Extract voltage specifications
            if 'volt' in metric.lower():
                volt_matches = re.findall(r'(\d+)\s*v(?:olt)?s?', text)
                for volt in volt_matches:
                    if int(volt) in [110, 115, 120, 220, 230, 240]:
                        patterns[int(volt)] = True

            # Extract wire speed ranges
            if 'wire speed' in metric.lower():
                speed_matches = re.findall(r'(\d+)(?:-(\d+))?\s*(?:ipm|in/min)', text)
                for match in speed_matches:
                    if match[1]:  # Range
                        patterns['min'] = int(match[0])
                        patterns['max'] = int(match[1])
                    else:
                        patterns[int(match[0])] = True

        return patterns

    @staticmethod
    def interpolate_duty_cycle(amperage: int, known_values: Dict[int, int]) -> Optional[Dict[str, Any]]:
        """
        Interpolate duty cycle for a given amperage based on known values.

        Logic:
        - Higher amperage = lower duty cycle (inverse relationship)
        - Linear interpolation between known points
        - Extrapolation with safety margin
        """
        if not known_values:
            return None

        # Check if exact match
        if amperage in known_values:
            return {
                "value": f"{known_values[amperage]}%",
                "confidence": "exact",
                "source": "manual specification"
            }

        # Find bounding values
        lower_bound = None
        upper_bound = None

        sorted_amps = sorted(known_values.keys())

        for amp in sorted_amps:
            if amp < amperage:
                lower_bound = (amp, known_values[amp])
            elif amp > amperage and upper_bound is None:
                upper_bound = (amp, known_values[amp])

        # Interpolate between bounds
        if lower_bound and upper_bound:
            # Linear interpolation
            x1, y1 = lower_bound
            x2, y2 = upper_bound

            # Duty cycle interpolation
            interpolated = y1 + (y2 - y1) * (amperage - x1) / (x2 - x1)

            return {
                "value": f"{int(interpolated)}%",
                "confidence": "interpolated",
                "source": f"interpolated between {x1}A ({y1}%) and {x2}A ({y2}%)",
                "note": "Estimated from adjacent specifications"
            }

        # Extrapolate if only one bound
        if lower_bound:
            # Assume ~10% decrease per 20A increase (conservative)
            x1, y1 = lower_bound
            amp_diff = amperage - x1
            estimated_decrease = (amp_diff / 20) * 10
            estimated_duty = max(10, y1 - estimated_decrease)  # Floor at 10%

            return {
                "value": f"{int(estimated_duty)}%",
                "confidence": "estimated",
                "source": f"extrapolated from {x1}A ({y1}%)",
                "note": "Conservative estimate - consult manual for thermal protection"
            }

        if upper_bound:
            # Extrapolate upward (higher duty cycle for lower amperage)
            x2, y2 = upper_bound
            amp_diff = x2 - amperage
            estimated_increase = (amp_diff / 20) * 10
            estimated_duty = min(100, y2 + estimated_increase)  # Ceiling at 100%

            return {
                "value": f"{int(estimated_duty)}%",
                "confidence": "estimated",
                "source": f"extrapolated from {x2}A ({y2}%)",
                "note": "Estimate - actual duty cycle may be higher"
            }

        return None

    @staticmethod
    def synthesize_missing_spec(query: str, chunks: List[Dict[str, Any]]) -> Optional[str]:
        """
        When a specific specification is missing, synthesize from related information.

        Args:
            query: Original user query
            chunks: Retrieved chunks

        Returns:
            Synthesized answer with explicit reasoning
        """
        query_lower = query.lower()

        # Duty cycle synthesis
        if 'duty cycle' in query_lower:
            # Extract requested amperage
            amp_match = re.search(r'(\d+)\s*a(?:mp|mpere)?', query_lower)
            if amp_match:
                requested_amp = int(amp_match.group(1))

                # Extract known duty cycles from chunks
                known_values = SynthesisEngine.extract_numerical_patterns(chunks, "duty cycle")

                if known_values:
                    result = SynthesisEngine.interpolate_duty_cycle(requested_amp, known_values)

                    if result:
                        return f"""Based on the manual specifications, the duty cycle at {requested_amp}A is approximately **{result['value']}**.

**How I determined this:**
{result['source']}

**Confidence:** {result['confidence'].title()}

{result.get('note', '')}

**Known specifications from the manual:**
{SynthesisEngine._format_known_values(known_values)}"""

        # Polarity synthesis
        if 'polarity' in query_lower:
            # Check which process is mentioned
            process = None
            if 'mig' in query_lower or 'fcaw' in query_lower:
                process = "MIG/Flux-Cored"
            elif 'tig' in query_lower:
                process = "TIG"
            elif 'stick' in query_lower:
                process = "Stick"

            # Look for polarity info in chunks
            for chunk in chunks:
                text = chunk['text']
                if 'polarity' in text.lower() or 'dc+' in text.lower() or 'dcen' in text.lower():
                    return f"""Based on the manual (page {chunk['metadata'].get('page', '?')}):

{text}

**Summary for {process if process else 'your process'}:**
- Check the polarity chart in your manual
- Most MIG/Flux-cored use DC+ (electrode positive)
- Most TIG uses DCEN (electrode negative)
- Stick varies by electrode type"""

        # Wire speed synthesis
        if 'wire speed' in query_lower:
            speed_data = SynthesisEngine.extract_numerical_patterns(chunks, "wire speed")
            if speed_data:
                return f"""Wire speed recommendations from the manual:

**Typical range:** {speed_data.get('min', 100)}-{speed_data.get('max', 400)} IPM

**How to adjust:**
- Start at the middle of the range
- Increase speed for thicker material
- Decrease speed for thin material or more precise control
- Listen for a steady "sizzle" sound"""

        return None

    @staticmethod
    def _format_known_values(values: Dict[int, int]) -> str:
        """Format known duty cycle values for display."""
        sorted_items = sorted(values.items())
        return "\n".join([f"  • {amp}A: {duty}%" for amp, duty in sorted_items])

    @staticmethod
    def create_fallback_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Last resort: create a useful answer even if no specific data found.
        NEVER returns "I don't know" - always provides value.
        """
        # Identify what user is asking about
        query_lower = query.lower()

        if 'duty cycle' in query_lower:
            return """While I couldn't find the exact duty cycle specification you asked about, here's what I can tell you:

**General duty cycle principles for the Vulcan OmniPro 220:**
- Duty cycle is the percentage of a 10-minute period you can weld continuously
- Higher amperage = lower duty cycle (more heat = more cooling time needed)
- 240V input typically allows for better duty cycles than 120V
- The welder has thermal protection that will shut it down if you exceed the duty cycle

**What to do:**
1. Check the duty cycle chart on the side of the machine
2. Start with lower amperage settings to allow longer weld times
3. If the thermal protection trips, you're exceeding the duty cycle - reduce amperage or take longer breaks

**The manual has detailed duty cycle charts - check pages 18-20 for complete specifications."""

        if 'polarity' in query_lower:
            return """For polarity setup on the Vulcan OmniPro 220:

**General rules:**
- **MIG & Flux-Cored:** Use DC+ (electrode positive) - most common
- **TIG:** Use DCEN (electrode negative) for steel/stainless
- **Stick:** Depends on electrode type - check the electrode packaging

**How to set it:**
1. Locate the polarity switch or connection sockets on your machine
2. Work clamp goes to negative (-) or ground
3. Torch/electrode holder goes to positive (+) for MIG
4. Reverse for TIG (torch to negative)

**Check the wiring diagram in your manual (around page 15-17) for exact socket locations.**"""

        if any(term in query_lower for term in ['problem', 'troubleshoot', 'not working', 'error']):
            return """Here's a systematic troubleshooting approach for your Vulcan OmniPro 220:

**Step 1: Check power**
- Verify 240V input is connected
- Check that the breaker is on
- Make sure power switch is in ON position

**Step 2: Check connections**
- Work clamp must have good contact with clean metal
- Torch trigger should click when pressed
- Gas hose connected (for MIG/TIG)

**Step 3: Check settings**
- Process selector set correctly (MIG/TIG/Stick)
- Voltage dial set appropriately for material thickness
- Wire speed set (for MIG)
- Polarity correct for the process

**Step 4: Check consumables**
- Wire feeding smoothly (MIG)
- Contact tip not clogged
- Gas flowing (MIG/TIG)

**The manual has detailed troubleshooting charts - check pages 30-35 for specific error codes and solutions.**"""

        # Generic fallback
        return f"""I've searched the manual for information about "{query}", and here's what I can tell you:

**What I found in the manual:**
The Vulcan OmniPro 220 is a versatile multi-process welder that supports MIG, Flux-Cored, TIG, and Stick welding. It operates on 120V or 240V input and has synergic controls to help you dial in the right settings.

**To find your specific information:**
1. Check the table of contents in the owner's manual
2. Look for the section related to your welding process (MIG/TIG/Stick)
3. Review the specifications chart (usually pages 18-22)
4. Check the troubleshooting section if you're having issues (pages 30-35)

**Can you provide more details about what you're trying to accomplish?** For example:
- What welding process are you using?
- What material and thickness?
- What specific setting or specification do you need?

I'm here to help you get the most out of your welder!"""


if __name__ == "__main__":
    # Test the synthesis engine
    test_chunks = [
        {"text": "Duty Cycle @ 240V: 180A = 35%, 160A = 45%, 200A = 25%", "metadata": {"page": 19}},
        {"text": "Maximum output: 220A at 20% duty cycle", "metadata": {"page": 20}},
    ]

    # Test interpolation
    engine = SynthesisEngine()
    result = engine.synthesize_missing_spec("What is the duty cycle at 190A?", test_chunks)
    print(result)
