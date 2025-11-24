"""LLM-based explanation module for health metric anomalies."""

from typing import Any, Dict, List

from openai import AzureOpenAI

from .config import config

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=config.azure_openai.api_key,
    api_version=config.azure_openai.api_version,
    azure_endpoint=config.azure_openai.endpoint,
)

SYSTEM_PROMPT = """You are a health metrics explainer for wearable health devices. 
You help users understand their health data including HRV (Heart Rate Variability), 
resting heart rate, sleep quality, and step counts.

IMPORTANT DISCLAIMERS:
- You are NOT a doctor or medical professional.
- You must NOT provide medical diagnoses.
- You must NOT provide treatment recommendations.
- You should recommend consulting with a healthcare clinician for any health concerns.
- Your explanations are for informational purposes only and should not replace professional medical advice.

Your role is to:
- Explain what the health metrics mean in simple terms
- Identify patterns and potential implications
- Suggest general lifestyle adjustments (not medical treatments)
- Always emphasize the importance of consulting healthcare professionals for medical concerns."""


def build_user_prompt(anomalies: List[Dict[str, Any]]) -> str:
    """Build a user prompt from a list of anomaly records.

    Formats each anomaly as a bullet point with key metrics and flags,
    then provides instructions for the LLM to summarize and provide recommendations.

    Args:
        anomalies: List of dictionaries, each representing an anomalous day.
            Each dictionary should contain:
            - date: Date of the anomaly
            - hrv: Heart rate variability value
            - resting_hr: Resting heart rate value
            - sleep_score: Sleep quality score
            - steps: Daily step count
            - Additional flag fields (low_hrv_flag, high_rhr_flag, low_sleep_flag, etc.)

    Returns:
        Formatted prompt string for the LLM.
    """
    if not anomalies:
        return ""

    prompt_parts = [
        "The following health metric anomalies were detected:",
        "",
    ]

    # Format each anomaly as a bullet point
    for anomaly in anomalies:
        date_str = str(anomaly.get("date", "Unknown date"))
        hrv = anomaly.get("hrv", "N/A")
        resting_hr = anomaly.get("resting_hr", "N/A")
        sleep_score = anomaly.get("sleep_score", "N/A")
        steps = anomaly.get("steps", "N/A")

        # Collect active flags
        flags = []
        if anomaly.get("low_hrv_flag", False):
            flags.append("Low HRV")
        if anomaly.get("high_rhr_flag", False):
            flags.append("High Resting HR")
        if anomaly.get("low_sleep_flag", False):
            flags.append("Low Sleep Score")
        if anomaly.get("low_recovery_flag", False):
            flags.append("Low Recovery Index")
        if anomaly.get("low_movement_flag", False):
            flags.append("Low Movement Index")
        if anomaly.get("low_steps_flag", False):
            flags.append("Low Steps")
        if anomaly.get("low_active_flag", False):
            flags.append("Low Active Minutes")
        if anomaly.get("low_vo2_flag", False):
            flags.append("Low VO2 Max")

        flags_str = ", ".join(flags) if flags else "No specific flags"
        severity = anomaly.get("anomaly_severity", 0)

        prompt_parts.append(
            f"• Date: {date_str} | HRV: {hrv} | Resting HR: {resting_hr} bpm | "
            f"Sleep Score: {sleep_score} | Steps: {steps} | "
            f"Flags: {flags_str} | Severity: {severity}"
        )

    # Add instructions
    prompt_parts.extend(
        [
            "",
            "Please provide:",
            "1. A summary of what's going on with these health metrics",
            "2. Potential implications of these patterns",
            "3. 3-4 general lifestyle adjustment suggestions (not medical treatments)",
            "4. A reminder that this is not medical advice and to consult a healthcare professional",
        ]
    )

    return "\n".join(prompt_parts)


def generate_explanation(anomalies: List[Dict[str, Any]]) -> str:
    """Generate an LLM explanation for detected health metric anomalies.

    Uses Azure OpenAI to generate a natural language explanation of the anomalies,
    including summaries, implications, and lifestyle recommendations.

    Args:
        anomalies: List of dictionaries representing anomalous days.
            Each dictionary should contain date, hrv, resting_hr, sleep_score,
            steps, and various flag fields.

    Returns:
        String containing the LLM-generated explanation. Returns a simple
        message if no anomalies are provided.

    Raises:
        Exception: If the OpenAI API call fails.
    """
    if not anomalies:
        return (
            "No anomalies detected in your health metrics. "
            "Your recent data appears to be within normal ranges. "
            "Continue monitoring your health metrics regularly."
        )

    # Build the user prompt
    user_prompt = build_user_prompt(anomalies)

    try:
        # Call Azure OpenAI API
        response = client.chat.completions.create(
            model=config.azure_openai.deployment_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=600,
        )

        # Extract the text content from the response
        explanation = response.choices[0].message.content
        return explanation.strip() if explanation else "Unable to generate explanation."

    except Exception as e:
        # Re-raise with more context
        raise RuntimeError(
            f"Failed to generate LLM explanation: {e}. "
            f"Check your Azure OpenAI configuration and API credentials."
        ) from e
