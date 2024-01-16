import logging
import asyncio

from mlflow.openai import log_model
import openai


_logger = logging.getLogger(__name__)

SUMMARIZATION_PROMPT = """You're an AI assistant for home automation. You're being given the latest set of events from the home automation system. You are to concisely summarize the events relevant to the user's query followed by an explanation of your reasoning.
    EXAMPLE SENSOR DATA:
    {{'event_type': 'state_changed', 'event_data': {{'entity_id': 'binary_sensor.washer_wash_completed', 'old_state': {{'entity_id': 'binary_sensor.washer_wash_completed', 'state': 'off', 'attributes': {{'friendly_name': 'Washer Wash completed'}}, 'last_changed': '2023-12-23T09:20:07.695950+00:00', 'last_updated': '2023-12-23T09:20:07.695950+00:00', 'context': {{'id': '01HJAZK20FGR2Z9NTCD46XMQEG', 'parent_id': None, 'user_id': None}}}}, 'new_state': {{'entity_id': 'binary_sensor.washer_wash_completed', 'state': 'on', 'attributes': {{'friendly_name': 'Washer Wash completed'}}, 'last_changed': '2023-12-23T09:53:07.724686+00:00', 'last_updated': '2023-12-23T09:53:07.724686+00:00', 'context': {{'id': '01HJB1FFMCT64MM6GKQX55HMKQ', 'parent_id': None, 'user_id': None}}}}}}}}
    {{'event_type': 'call_service', 'event_data': {{'domain': 'tts', 'service': 'cloud_say', 'service_data': {{'cache': True, 'entity_id': ['media_player.kitchen_interrupt', 'media_player.master_bedroom_interrupt'], 'message': 'The washer is complete! Move the clothes to the dryer or they gonna get so so so stinky poo poo!!!!'}}}}}}
    {{'event_type': 'call_service', 'event_data': {{'domain': 'media_player', 'service': 'play_media', 'service_data': {{'entity_id': ['media_player.kitchen_interrupt', 'media_player.master_bedroom_interrupt'], 'media_content_id': 'media-source://tts/cloud?message=The+washer+is+complete!+Move+the+clothes+to+the+dryer+or+they+gonna+get+so+so+so+stinky+poo+poo!!!!&cache=true', 'media_content_type': 'music', 'announce': True}}}}}}
    {{'event_type': 'state_changed', 'event_data': {{'entity_id': 'binary_sensor.bedroom_motion_sensor_motion', 'old_state': {{'entity_id': 'binary_sensor.bedroom_motion_sensor_motion', 'state': 'off', 'attributes': {{'device_class': 'motion', 'friendly_name': 'Bedroom motion sensor Motion'}}, 'last_changed': '2023-12-23T09:46:48.945634+00:00', 'last_updated': '2023-12-23T09:46:48.945634+00:00', 'context': {{'id': '01HJB13XQHGYJYCBH1BS9E6JQY', 'parent_id': None, 'user_id': None}}}}, 'new_state': {{'entity_id': 'binary_sensor.bedroom_motion_sensor_motion', 'state': 'on', 'attributes': {{'device_class': 'motion', 'friendly_name': 'Bedroom motion sensor Motion'}}, 'last_changed': '2023-12-23T09:53:26.786268+00:00', 'last_updated': '2023-12-23T09:53:26.786268+00:00', 'context': {{'id': '01HJB1G282MSCK7H5KDVE5S260', 'parent_id': None, 'user_id': None}}}}}}}}
    {{'event_type': 'state_changed', 'event_data': {{'entity_id': 'binary_sensor.bedroom_motion_sensor_motion', 'old_state': {{'entity_id': 'binary_sensor.bedroom_motion_sensor_motion', 'state': 'on', 'attributes': {{'device_class': 'motion', 'friendly_name': 'Bedroom motion sensor Motion'}}, 'last_changed': '2023-12-23T09:53:26.786268+00:00', 'last_updated': '2023-12-23T09:53:26.786268+00:00', 'context': {{'id': '01HJB1G282MSCK7H5KDVE5S260', 'parent_id': None, 'user_id': None}}}}, 'new_state': {{'entity_id': 'binary_sensor.bedroom_motion_sensor_motion', 'state': 'off', 'attributes': {{'device_class': 'motion', 'friendly_name': 'Bedroom motion sensor Motion'}}, 'last_changed': '2023-12-23T09:53:50.016556+00:00', 'last_updated': '2023-12-23T09:53:50.016556+00:00', 'context': {{'id': '01HJB1GRY0RSE049YV3NPJ6QFC', 'parent_id': None, 'user_id': None}}}}}}}}

    EXAMPLE QUERY: "Is the laundry running?"
    EXAMPLE OUTPUT: "The washer is complete. You should move the clothes to the dryer. I see the washer completed sensor turned on at 2023-12-23T09:20:07.695950+00:00"

    EXAMPLE QUERY: "Is there anyone in the bedroom?"
    EXAMPLE OUTPUT: "There is no one in the bedroom. Even though there was recent activity, I see the bedroom motion sensor turned off at 2023-12-23T09:53:50.016556+00:00"

    EXAMPLE QUERY: "What rooms have activity recently?"
    EXAMPLE OUTPUT: "The bedroom has had activity. I see the bedroom motion sensor turned on at 2023-12-23T09:53:26.786268+00:00"

    Remember to be concise and that there could be multiple sequences of events interleaved, so you can output multiple lines.
    """


def log_system_models():
    QUERY_PROMPT = """
    You are given a query about events or actions happening for home automation over an unknown period of time.
    Based on the input user's question, return the start and end times for the query. Prefix lines with THOUGHT: to decide next steps. Show your work.

    EXAMPLE INPUT: How many people are in the house?
    EXAMPLE THOUGHT: I need to detect recent motion, so an hour lookback for motion sensors should be sufficient.
    EXAMPLE THOUGHT: The current time is 2024-01-02 22:27:46.379954, which is the end time. Therefore the start time is 2024-01-02 21:27:46.379954
    EXAMPLE OUTPUT: {{"start": "2024-01-02 21:27:46.379954", "end": "2024-01-02 22:27:46.379954"}}

    OUTPUT ONLY JSON FORMATTED OBJECTS WITH "start" and "end" keys!
    """
    log_model(
        model="gpt-3.5-turbo",
        task=openai.ChatCompletion,
        messages=[
            {"role": "system", "content": QUERY_PROMPT},
            {"role": "user", "content": "INPUT: {query}"},
        ],
        artifact_path="model",
        registered_model_name="querytime",
    )

    log_model(
        model="gpt-3.5-turbo",
        task=openai.ChatCompletion,
        messages=[
            {"role": "system", "content": SUMMARIZATION_PROMPT},
            {
                "role": "user",
                "content": "SENSOR DATA:\n{state_lines}\n\nQUERY: {query}",
            },
        ],
        artifact_path="model",
        registered_model_name="chat",
    )
    log_model(
        model="text-embedding-ada-002",
        task=openai.Embedding,
        artifact_path="embeddings",
        registered_model_name="embeddings",
    )

    return {}


# TODO: Add webhooks/eventing to MLflow OSS server. AzureML has eventgrid support
# In its absence, we poll the MLflow server for changes to the model registry
async def poll_registry(delay_seconds: float = 10.0):
    while True:
        # Sync any new models by tag/label/all
        # Solve any environment dependencies mismatch or fail
        # TODO: Consider running a separate server for each model to solve the isolation problem
        _logger.debug("Polling registry for changes")
        await asyncio.sleep(delay=delay_seconds)
