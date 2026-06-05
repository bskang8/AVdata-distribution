"""
4개 Stage별 프롬프트 템플릿.
각 함수는 최종 user 메시지 문자열을 반환한다.
"""


SYSTEM_PROMPT = (
    "You are an expert autonomous driving video analyst. "
    "You reason carefully about what you observe in the video before answering. "
    "Always ground your answers in visual evidence from the video."
)


def stage1_grounding(existing_caption: str) -> str:
    return f"""\
Watch this driving video carefully from start to finish.

I have an existing text caption for this video:
<existing_caption>
{existing_caption}
</existing_caption>

Analyze the caption against the visual content and respond ONLY with valid JSON:

{{
  "grounded": [
    "Exact claim from caption that is clearly visible in the video"
  ],
  "hallucinated": [
    "Exact claim from caption that is NOT supported by visual evidence"
  ],
  "missed": [
    "Significant event or condition visible in the video but absent from the caption"
  ]
}}

Rules:
- Quote the original caption text verbatim for grounded/hallucinated items.
- Be specific for missed items (describe what you see, not vague categories).
- If the caption is fully accurate, hallucinated may be an empty list.
- Do NOT add commentary outside the JSON."""


def stage2_extract() -> str:
    return """\
Watch this autonomous driving video carefully.

Think step by step about each field before committing to an answer, then reply ONLY with valid JSON:

{
  "time_of_day": {
    "value": "<day|night|dawn|dusk|unknown>",
    "confidence": 0.0,
    "evidence": "brief visual cue (e.g. sun position, streetlight state, sky color)"
  },
  "weather": {
    "value": "<clear|cloudy|rainy|foggy|snowy|unknown>",
    "confidence": 0.0,
    "evidence": "brief visual cue"
  },
  "road_type": {
    "value": "<highway|urban|intersection|rural|parking_lot|tunnel|bridge|unknown>",
    "confidence": 0.0,
    "evidence": "brief visual cue"
  },
  "num_lanes": {
    "value": null,
    "confidence": 0.0,
    "evidence": "how you counted"
  },
  "ego_lane_position": {
    "value": "<leftmost|second_from_left|center|second_from_right|rightmost|unknown>",
    "confidence": 0.0,
    "evidence": "brief visual cue"
  },
  "road_surface": {
    "value": "<dry|wet|icy|unpaved|unknown>",
    "confidence": 0.0,
    "evidence": "brief visual cue"
  },
  "road_markings": {
    "value": ["<lane_lines|crosswalk|stop_line|turn_arrow|bicycle_lane|none>"],
    "confidence": 0.0
  },
  "traffic_density": {
    "value": "<free|light|moderate|congested|unknown>",
    "confidence": 0.0,
    "evidence": "brief visual cue"
  },
  "surrounding_vehicles": {
    "types": ["<car|truck|bus|motorcycle|cyclist|emergency_vehicle|none>"],
    "count_estimate": null,
    "notable_behaviors": ["e.g. stalled vehicle blocking lane, vehicle running red light"],
    "confidence": 0.0
  },
  "ego_actions": {
    "value": ["<straight|braking|lane_change|left_turn|right_turn|stopping|u_turn|reversing>"],
    "confidence": 0.0,
    "evidence": "brief visual cue"
  },
  "pedestrians": {
    "present": false,
    "count_estimate": null,
    "behavior": "e.g. crossing, waiting at curb, jaywalking",
    "confidence": 0.0
  },
  "traffic_signals": {
    "present": false,
    "state": "<red|yellow|green|not_visible|none>",
    "confidence": 0.0,
    "evidence": "brief visual cue"
  },
  "road_signs": {
    "types": ["<speed_limit|warning|direction|prohibition|information|none>"],
    "details": "e.g. speed limit 60, railway crossing warning",
    "confidence": 0.0
  },
  "hazard_level": {
    "value": "<low|medium|high|unknown>",
    "rationale": "why this hazard level",
    "confidence": 0.0
  },
  "lighting_condition": {
    "value": "<daylight|artificial|mixed|dark|unknown>",
    "confidence": 0.0,
    "evidence": "brief visual cue"
  }
}

Rules:
- num_lanes must be an integer or null (not a string).
- count_estimate must be an integer or null.
- All confidence values must be between 0.0 and 1.0.
- Do NOT add commentary outside the JSON."""


def stage3_verify(low_confidence_fields: dict) -> str:
    fields_text = "\n".join(
        f"- {field}: currently '{info.get('value', info.get('present', '?'))}' "
        f"(confidence {info.get('confidence', '?'):.2f}) — evidence: {info.get('evidence', info.get('rationale', ''))}"
        for field, info in low_confidence_fields.items()
    )
    return f"""\
Watch this video again and focus ONLY on the fields listed below, which had low confidence:

{fields_text}

For each field:
1. Describe exactly what you observe in the video relevant to this field.
2. State your verdict: CONFIRM (original answer is correct) or CORRECT (provide new value).

Reply ONLY with valid JSON:

{{
  "field_name": {{
    "observation": "what you see in the video",
    "verdict": "<CONFIRM|CORRECT>",
    "corrected_value": null
  }}
}}

- corrected_value must match the allowed values for that field (see Stage 2 schema).
- Set corrected_value to null when verdict is CONFIRM.
- Do NOT include fields not listed above.
- Do NOT add commentary outside the JSON."""


def stage4_refine(
    original_caption: str,
    verified_odd: dict,
    hallucinated: list[str],
    missed: list[str],
) -> str:
    import json
    odd_summary = json.dumps(verified_odd, ensure_ascii=False, indent=2)
    hal_text = "\n".join(f"- {h}" for h in hallucinated) if hallucinated else "None"
    miss_text = "\n".join(f"- {m}" for m in missed) if missed else "None"

    return f"""\
Watch this driving video. You will write a corrected, factual caption.

=== Original caption (may contain errors) ===
{original_caption}

=== Verified scene information ===
{odd_summary}

=== Claims from original caption NOT supported by the video ===
{hal_text}

=== Important events visible in video but missing from original caption ===
{miss_text}

Write a refined caption that:
1. Removes all hallucinated content listed above.
2. Naturally incorporates the verified scene information (weather, road type, time of day, etc.).
3. Preserves grounded content from the original caption.
4. Adds any missed observations.
5. Describes events chronologically (beginning → middle → end of clip).
6. Is 150–300 words.
7. Uses third-person past tense ("The ego-vehicle...").

Output the caption text ONLY — no JSON, no headers, no explanation."""
