"""Measurement routes."""

import logging
import time
from collections.abc import Iterator
from typing import cast

import bottle
from pymongo.database import Database

from shared.database import sessions
from shared.database.datamodels import latest_datamodel
from shared.database.measurements import insert_new_measurement, latest_measurement
from shared.model.measurement import Measurement
from shared.utils.type import MetricId, SourceId

from database.measurements import count_measurements, all_metric_measurements
from database.reports import latest_report_for_uuids, latest_reports
from utils.functions import report_date_time

from .plugins.auth_plugin import EDIT_ENTITY_PERMISSION


@bottle.post(
    "/api/v3/measurement/<metric_uuid>/source/<source_uuid>/entity/<entity_key>/<attribute>",
    permissions_required=[EDIT_ENTITY_PERMISSION],
)
def set_entity_attribute(
    metric_uuid: MetricId, source_uuid: SourceId, entity_key: str, attribute: str, database: Database
) -> Measurement:
    """Set an entity attribute."""
    data_model = latest_datamodel(database)
    report = latest_report_for_uuids(latest_reports(database, data_model), metric_uuid)[0]
    metric = report.metrics_dict[metric_uuid]
    new_measurement = cast(Measurement, latest_measurement(database, metric)).copy()
    source = [s for s in new_measurement["sources"] if s["source_uuid"] == source_uuid][0]
    entity = [e for e in source["entities"] if e["key"] == entity_key][0]
    entity_description = "/".join([str(entity[key]) for key in entity.keys() if key not in ("key", "url")])
    old_value = source.get("entity_user_data", {}).get(entity_key, {}).get(attribute) or ""
    new_value = dict(bottle.request.json)[attribute]
    source.setdefault("entity_user_data", {}).setdefault(entity_key, {})[attribute] = new_value
    user = sessions.find_user(database)
    new_measurement["delta"] = dict(
        uuids=[report.uuid, metric.subject_uuid, metric_uuid, source_uuid],
        description=f"{user.name()} changed the {attribute} of '{entity_description}' from '{old_value}' to "
        f"'{new_value}'.",
        email=user.email,
    )
    return insert_new_measurement(database, new_measurement)


def sse_pack(event_id: int, event: str, data: int, retry: str = "2000") -> str:
    """Pack data in Server-Sent Events (SSE) format."""
    return f"retry: {retry}\nid: {event_id}\nevent: {event}\ndata: {data}\n\n"


@bottle.get("/api/v3/nr_measurements", authentication_required=False)
def stream_nr_measurements(database: Database) -> Iterator[str]:
    """Return the number of measurements as server sent events."""
    # Keep event IDs consistent
    event_id = int(bottle.request.get_header("Last-Event-Id", -1)) + 1

    # Set the response headers
    # https://serverfault.com/questions/801628/for-server-sent-events-sse-what-nginx-proxy-configuration-is-appropriate
    bottle.response.set_header("Connection", "keep-alive")
    bottle.response.set_header("Content-Type", "text/event-stream")
    bottle.response.set_header("Cache-Control", "no-cache")
    bottle.response.set_header("X-Accel-Buffering", "no")

    # Provide an initial data dump to each new client and set up our message payload with a retry value in case of
    # connection failure
    nr_measurements = count_measurements(database)
    logging.info("Initializing nr_measurements stream with %s measurements", nr_measurements)
    yield sse_pack(event_id, "init", nr_measurements)
    skipped = 0
    # Now give the client updates as they arrive
    while True:
        time.sleep(10)
        if (new_nr_measurements := count_measurements(database)) > nr_measurements or skipped > 5:
            skipped = 0
            nr_measurements = new_nr_measurements
            event_id += 1
            logging.info("Updating nr_measurements stream with %s measurements", nr_measurements)
            yield sse_pack(event_id, "delta", nr_measurements)
        else:
            skipped += 1


@bottle.get("/api/v3/measurements/<metric_uuid>", authentication_required=False)
def get_measurements(metric_uuid: MetricId, database: Database) -> dict:
    """Return the measurements for the metric."""
    metric_uuid = cast(MetricId, metric_uuid.split("&")[0])
    return dict(measurements=list(all_metric_measurements(database, metric_uuid, max_iso_timestamp=report_date_time())))
