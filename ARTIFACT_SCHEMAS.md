# Artifact Schemas - Complete Specification

## Overview
Each artifact type has a specific JSON schema that the agent produces and the frontend renders.

---

## 1. POLARITY_DIAGRAM - Animated Current Flow

**Use when**: User asks about polarity, cable connections, DC/AC setup

```json
{
  "type": "polarity_diagram",
  "title": "TIG Polarity Setup - DC Electrode Negative (DCEN)",
  "data": {
    "process": "TIG",
    "polarity": "DCEN",
    "components": [
      {
        "id": "welder",
        "type": "machine",
        "label": "Welder",
        "x": 50,
        "y": 150,
        "width": 100,
        "height": 80,
        "color": "#1e40af",
        "terminals": [
          {"id": "positive", "label": "+", "x": 150, "y": 170, "color": "#ef4444"},
          {"id": "negative", "label": "-", "x": 150, "y": 210, "color": "#000000"}
        ]
      },
      {
        "id": "workpiece",
        "type": "metal",
        "label": "Workpiece",
        "x": 400,
        "y": 150,
        "width": 120,
        "height": 80,
        "color": "#6b7280"
      },
      {
        "id": "torch",
        "type": "torch",
        "label": "TIG Torch",
        "x": 400,
        "y": 50,
        "width": 80,
        "height": 40,
        "color": "#3b82f6"
      }
    ],
    "connections": [
      {
        "id": "ground_cable",
        "from": {"component": "welder", "terminal": "positive"},
        "to": {"component": "workpiece", "point": {"x": 400, "y": 190}},
        "color": "#ef4444",
        "label": "Work Cable (+)",
        "animated": true,
        "currentFlow": "forward"
      },
      {
        "id": "torch_cable",
        "from": {"component": "welder", "terminal": "negative"},
        "to": {"component": "torch", "point": {"x": 440, "y": 90}},
        "color": "#000000",
        "label": "Torch Cable (-)",
        "animated": true,
        "currentFlow": "forward"
      },
      {
        "id": "arc",
        "from": {"component": "torch", "point": {"x": 440, "y": 90}},
        "to": {"component": "workpiece", "point": {"x": 440, "y": 150}},
        "color": "#a78bfa",
        "label": "Arc",
        "animated": true,
        "currentFlow": "forward",
        "style": "dashed",
        "glowEffect": true
      }
    ],
    "annotations": [
      {
        "text": "70% heat at workpiece",
        "x": 520,
        "y": 190,
        "color": "#ef4444"
      },
      {
        "text": "30% heat at electrode",
        "x": 520,
        "y": 70,
        "color": "#3b82f6"
      }
    ],
    "notes": [
      "DCEN provides deep, narrow penetration",
      "Ideal for steel and stainless steel",
      "Electrode stays cooler, lasts longer"
    ]
  }
}
```

---

## 2. DUTY_CYCLE_VISUALIZER - Heat & Time Animation

**Use when**: User asks about duty cycles, thermal limits, continuous operation

```json
{
  "type": "duty_cycle_visualizer",
  "title": "Duty Cycle at 200A, 240V - MIG Welding",
  "data": {
    "process": "MIG",
    "voltage": 240,
    "amperage": 200,
    "dutyCycle": 60,
    "timeWindow": 10,
    "visualization": {
      "type": "heat_bar",
      "segments": [
        {"duration": 6, "state": "welding", "color": "#ef4444", "label": "Welding (6 min)"},
        {"duration": 4, "state": "cooling", "color": "#3b82f6", "label": "Cooling (4 min)"}
      ],
      "heatLevels": {
        "welding": 100,
        "cooling": 0,
        "critical": 80
      }
    },
    "calculator": {
      "enabled": true,
      "ranges": {
        "voltage": [120, 240],
        "amperage": {"min": 30, "max": 220, "step": 10}
      },
      "lookupTable": {
        "MIG_200A_240V": 60,
        "MIG_180A_240V": 100,
        "MIG_200A_120V": 40,
        "FluxCored_200A_240V": 60,
        "TIG_200A_240V": 100,
        "Stick_200A_240V": 60
      }
    },
    "comparison": {
      "enabled": true,
      "scenarios": [
        {"amperage": 180, "dutyCycle": 100, "label": "Continuous at 180A"},
        {"amperage": 200, "dutyCycle": 60, "label": "60% at 200A"},
        {"amperage": 220, "dutyCycle": 30, "label": "30% at 220A (max)"}
      ]
    },
    "warnings": [
      {
        "threshold": 80,
        "message": "Approaching thermal limit - reduce duty cycle or amperage"
      }
    ]
  }
}
```

---

## 3. TROUBLESHOOTING_TREE - Interactive Decision Flow

**Use when**: User describes a problem (porosity, spatter, weak welds, etc.)

```json
{
  "type": "troubleshooting_tree",
  "title": "Porosity Diagnosis - MIG/Flux-Cored Welding",
  "data": {
    "problem": "Porosity (pinholes in weld)",
    "rootNode": "start",
    "nodes": [
      {
        "id": "start",
        "type": "question",
        "text": "What process are you using?",
        "options": [
          {"label": "MIG (solid wire)", "next": "mig_check"},
          {"label": "Flux-Cored", "next": "flux_check"}
        ]
      },
      {
        "id": "mig_check",
        "type": "question",
        "text": "Is your shielding gas flowing?",
        "options": [
          {"label": "Yes, I can hear/feel it", "next": "mig_gas_type"},
          {"label": "No gas flow", "next": "fix_gas_flow"},
          {"label": "Not sure", "next": "check_gas_flow"}
        ]
      },
      {
        "id": "fix_gas_flow",
        "type": "solution",
        "text": "Gas flow issue detected",
        "steps": [
          "Check gas cylinder - is it open?",
          "Verify regulator is set to 15-20 CFH",
          "Inspect gas hose for kinks or damage",
          "Check gas diffuser in MIG gun for clogs"
        ],
        "severity": "critical",
        "icon": "alert-circle"
      },
      {
        "id": "mig_gas_type",
        "type": "question",
        "text": "What gas are you using?",
        "options": [
          {"label": "75/25 Argon/CO2", "next": "mig_wind"},
          {"label": "100% CO2", "next": "mig_wind"},
          {"label": "Other/Unknown", "next": "wrong_gas"}
        ]
      },
      {
        "id": "mig_wind",
        "type": "question",
        "text": "Are you welding outdoors or in a draft?",
        "options": [
          {"label": "Yes, windy conditions", "next": "wind_shield"},
          {"label": "No, indoors/calm", "next": "mig_contamination"}
        ]
      },
      {
        "id": "wind_shield",
        "type": "solution",
        "text": "Wind is blowing away shielding gas",
        "steps": [
          "Set up wind barriers or welding curtains",
          "Increase gas flow to 20-25 CFH",
          "Move to sheltered area if possible",
          "Consider switching to flux-cored wire (self-shielding)"
        ],
        "severity": "moderate",
        "icon": "wind"
      },
      {
        "id": "mig_contamination",
        "type": "question",
        "text": "Is the base metal clean?",
        "options": [
          {"label": "Yes, cleaned with grinder/wire brush", "next": "wire_quality"},
          {"label": "No, has rust/paint/oil", "next": "clean_metal"}
        ]
      },
      {
        "id": "clean_metal",
        "type": "solution",
        "text": "Contaminated base metal",
        "steps": [
          "Remove all rust, paint, oil, and mill scale",
          "Use angle grinder or wire brush to clean",
          "Wipe with acetone or degreaser",
          "Clean 1-2 inches around weld area"
        ],
        "severity": "high",
        "icon": "tool"
      },
      {
        "id": "flux_check",
        "type": "question",
        "text": "Are you using self-shielding or gas-shielded flux-cored wire?",
        "options": [
          {"label": "Self-shielding (no gas)", "next": "flux_wind"},
          {"label": "Gas-shielded", "next": "mig_check"}
        ]
      },
      {
        "id": "flux_wind",
        "type": "question",
        "text": "Check polarity - is it set to DC electrode NEGATIVE (DCEN)?",
        "options": [
          {"label": "Yes, DCEN (-)", "next": "flux_contamination"},
          {"label": "No, it's DCEP (+)", "next": "wrong_polarity"}
        ]
      },
      {
        "id": "wrong_polarity",
        "type": "solution",
        "text": "Wrong polarity for self-shielding flux-cored wire",
        "steps": [
          "Self-shielding flux-cored requires DCEN (electrode negative)",
          "Swap your cables at the machine terminals",
          "Torch cable goes to (-) terminal",
          "Work clamp goes to (+) terminal",
          "Refer to page 8 of manual for polarity diagram"
        ],
        "severity": "critical",
        "icon": "zap",
        "referenceImage": "polarity_diagram"
      }
    ],
    "interactivity": {
      "highlightPath": true,
      "showProgress": true,
      "allowBacktrack": true
    }
  }
}
```

---

## 4. INTERACTIVE_TABLE - Sortable, Filterable, Highlightable

**Use when**: Displaying specifications, settings charts, comparison data

```json
{
  "type": "interactive_table",
  "title": "MIG Welding Settings - Mild Steel",
  "data": {
    "columns": [
      {"key": "thickness", "label": "Material Thickness", "type": "dimension", "sortable": true},
      {"key": "wireSize", "label": "Wire Size", "type": "dimension", "sortable": true},
      {"key": "voltage", "label": "Voltage", "type": "range", "sortable": true},
      {"key": "wireSpeed", "label": "Wire Speed (IPM)", "type": "range", "sortable": true},
      {"key": "amperage", "label": "Amperage", "type": "range", "sortable": true},
      {"key": "gas", "label": "Shielding Gas", "type": "text", "sortable": false}
    ],
    "rows": [
      {
        "id": "row_1",
        "thickness": "1/16\"",
        "wireSize": ".023\"",
        "voltage": "14-16V",
        "wireSpeed": "180-220",
        "amperage": "40-60A",
        "gas": "75/25 Ar/CO2",
        "metadata": {"category": "thin", "common": true}
      },
      {
        "id": "row_2",
        "thickness": "1/8\"",
        "wireSize": ".030\"",
        "voltage": "16-18V",
        "wireSpeed": "200-280",
        "amperage": "60-100A",
        "gas": "75/25 Ar/CO2",
        "metadata": {"category": "medium", "common": true, "recommended": true}
      },
      {
        "id": "row_3",
        "thickness": "3/16\"",
        "wireSize": ".030\"",
        "voltage": "18-20V",
        "wireSpeed": "280-350",
        "amperage": "100-140A",
        "gas": "75/25 Ar/CO2",
        "metadata": {"category": "medium", "common": true}
      },
      {
        "id": "row_4",
        "thickness": "1/4\"",
        "wireSize": ".035\"",
        "voltage": "20-22V",
        "wireSpeed": "300-400",
        "amperage": "140-180A",
        "gas": "75/25 Ar/CO2",
        "metadata": {"category": "thick", "common": false}
      },
      {
        "id": "row_5",
        "thickness": "3/8\"",
        "wireSize": ".035\"",
        "voltage": "22-24V",
        "wireSpeed": "350-450",
        "amperage": "180-220A",
        "gas": "75/25 Ar/CO2",
        "metadata": {"category": "thick", "common": false}
      }
    ],
    "features": {
      "sorting": true,
      "filtering": {
        "enabled": true,
        "filters": [
          {"key": "category", "label": "Thickness Category", "options": ["thin", "medium", "thick"]},
          {"key": "common", "label": "Common Applications", "type": "boolean"}
        ]
      },
      "highlighting": {
        "enabled": true,
        "rules": [
          {"condition": {"key": "recommended", "value": true}, "style": "bg-green-50 border-l-4 border-green-500"}
        ]
      },
      "search": true,
      "export": true
    },
    "notes": [
      "Settings are starting points - adjust based on arc sound and bead appearance",
      "For aluminum, use 100% Argon and adjust voltage down 10-15%"
    ]
  }
}
```

---

## 5. PARAMETER_EXPLORER - Real-time Sliders

**Use when**: User wants to explore settings interactively

```json
{
  "type": "parameter_explorer",
  "title": "Wire Feed Speed Calculator",
  "data": {
    "description": "Adjust parameters to see recommended wire feed speed and voltage",
    "parameters": [
      {
        "id": "material",
        "label": "Material",
        "type": "select",
        "value": "mild-steel",
        "options": [
          {"value": "mild-steel", "label": "Mild Steel"},
          {"value": "stainless", "label": "Stainless Steel"},
          {"value": "aluminum", "label": "Aluminum"}
        ]
      },
      {
        "id": "thickness",
        "label": "Thickness (inches)",
        "type": "slider",
        "value": 0.125,
        "min": 0.0625,
        "max": 0.375,
        "step": 0.0625,
        "displayFormat": "fraction",
        "marks": [
          {"value": 0.0625, "label": "1/16\""},
          {"value": 0.125, "label": "1/8\""},
          {"value": 0.1875, "label": "3/16\""},
          {"value": 0.25, "label": "1/4\""},
          {"value": 0.375, "label": "3/8\""}
        ]
      },
      {
        "id": "wireSize",
        "label": "Wire Diameter",
        "type": "select",
        "value": 0.030,
        "options": [
          {"value": 0.023, "label": ".023\""},
          {"value": 0.030, "label": ".030\""},
          {"value": 0.035, "label": ".035\""},
          {"value": 0.045, "label": ".045\""}
        ]
      },
      {
        "id": "process",
        "label": "Process",
        "type": "select",
        "value": "MIG",
        "options": [
          {"value": "MIG", "label": "MIG (Short Circuit)"},
          {"value": "MIG-Spray", "label": "MIG (Spray Transfer)"},
          {"value": "Flux-Cored", "label": "Flux-Cored"}
        ]
      }
    ],
    "outputs": [
      {
        "id": "wireSpeed",
        "label": "Wire Feed Speed",
        "unit": "IPM",
        "calculation": "wireSpeedFormula",
        "displayStyle": "large",
        "color": "#3b82f6"
      },
      {
        "id": "voltage",
        "label": "Voltage Setting",
        "unit": "V",
        "calculation": "voltageFormula",
        "displayStyle": "large",
        "color": "#ef4444"
      },
      {
        "id": "amperage",
        "label": "Estimated Amperage",
        "unit": "A",
        "calculation": "amperageFormula",
        "displayStyle": "medium",
        "color": "#10b981"
      },
      {
        "id": "gasFlow",
        "label": "Gas Flow Rate",
        "unit": "CFH",
        "calculation": "gasFlowFormula",
        "displayStyle": "small",
        "color": "#6b7280"
      }
    ],
    "formulas": {
      "wireSpeedFormula": {
        "type": "lookup",
        "table": {
          "mild-steel_0.125_0.030_MIG": {"wireSpeed": 250, "voltage": 17, "amperage": 80, "gasFlow": 20},
          "mild-steel_0.1875_0.030_MIG": {"wireSpeed": 320, "voltage": 19, "amperage": 120, "gasFlow": 20},
          "stainless_0.125_0.030_MIG": {"wireSpeed": 220, "voltage": 16, "amperage": 75, "gasFlow": 25}
        }
      }
    },
    "visualization": {
      "type": "gauge",
      "ranges": [
        {"min": 0, "max": 150, "color": "#10b981", "label": "Low"},
        {"min": 150, "max": 300, "color": "#3b82f6", "label": "Medium"},
        {"min": 300, "max": 500, "color": "#ef4444", "label": "High"}
      ]
    }
  }
}
```

---

## 6. COMPARISON_MATRIX - Side-by-side Visual Comparison

**Use when**: Comparing processes, settings, or equipment specifications

```json
{
  "type": "comparison_matrix",
  "title": "Welding Process Comparison",
  "data": {
    "items": [
      {"id": "mig", "name": "MIG", "color": "#3b82f6"},
      {"id": "flux", "name": "Flux-Cored", "color": "#10b981"},
      {"id": "tig", "name": "TIG", "color": "#8b5cf6"},
      {"id": "stick", "name": "Stick", "color": "#ef4444"}
    ],
    "criteria": [
      {
        "id": "ease",
        "label": "Ease of Use",
        "type": "rating",
        "values": {
          "mig": 5,
          "flux": 4,
          "tig": 2,
          "stick": 3
        }
      },
      {
        "id": "speed",
        "label": "Welding Speed",
        "type": "rating",
        "values": {
          "mig": 5,
          "flux": 5,
          "tig": 2,
          "stick": 3
        }
      },
      {
        "id": "quality",
        "label": "Weld Quality",
        "type": "rating",
        "values": {
          "mig": 4,
          "flux": 3,
          "tig": 5,
          "stick": 4
        }
      },
      {
        "id": "outdoor",
        "label": "Outdoor Use",
        "type": "boolean",
        "values": {
          "mig": false,
          "flux": true,
          "tig": false,
          "stick": true
        }
      },
      {
        "id": "materials",
        "label": "Materials",
        "type": "list",
        "values": {
          "mig": ["Steel", "Stainless", "Aluminum"],
          "flux": ["Steel", "Stainless"],
          "tig": ["Steel", "Stainless", "Aluminum", "Exotic"],
          "stick": ["Steel", "Stainless", "Cast Iron"]
        }
      },
      {
        "id": "dutyCycle",
        "label": "Duty Cycle @ 200A",
        "type": "text",
        "values": {
          "mig": "60%",
          "flux": "60%",
          "tig": "100%",
          "stick": "60%"
        }
      }
    ],
    "layout": "columns"
  }
}
```

---

## Agent Decision Logic

The agent should choose artifact types based on:

```python
ARTIFACT_SELECTION_RULES = {
    "polarity_diagram": {
        "triggers": ["polarity", "cable", "connection", "dc", "ac", "electrode", "setup wiring"],
        "processes": ["TIG", "Stick", "Flux-Cored"]
    },
    "duty_cycle_visualizer": {
        "triggers": ["duty cycle", "thermal", "overheat", "continuous", "how long"],
        "numeric": True
    },
    "troubleshooting_tree": {
        "triggers": ["problem", "issue", "defect", "porosity", "spatter", "weak", "not working", "help"],
        "conversational": True
    },
    "interactive_table": {
        "triggers": ["settings", "chart", "specifications", "comparison", "all", "list"],
        "data_heavy": True
    },
    "parameter_explorer": {
        "triggers": ["calculate", "what setting", "wire speed", "voltage for", "explore"],
        "interactive": True
    },
    "comparison_matrix": {
        "triggers": ["compare", "difference between", "which process", "vs", "better"],
        "comparative": True
    }
}
```
