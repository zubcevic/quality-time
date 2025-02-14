"""Database migration code.

This migration code was added when the most recent version of Quality-time was 4.3.0.
Bug issue: https://github.com/ICTU/quality-time/issues/4554
Cleanup issue: https://github.com/ICTU/quality-time/issues/4556.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, TypedDict
import logging

from bson.objectid import ObjectId
from pymongo.database import Database
from pymongo.operations import DeleteMany, UpdateOne
import pymongo


SCALES = ("count", "percentage", "version_number")  # All scales Quality-time has ever supported
OLD_TO_NEW = [("start", pymongo.ASCENDING)]


class MeasurementJSON(TypedDict):
    """The relevant attributes of the measurement JSON as returned by MongoDB."""

    _id: ObjectId
    end: str


@dataclass
class Stats:  # pragma: no cover-behave
    """Keep track of the number of measurements merged."""

    nr_measurements_updated: int = 0
    nr_measurements_deleted: int = 0
    nr_measurements: int = 0
    nr_metrics: int = 0

    def __iadd__(self, other) -> "Stats":
        """Add the other stats."""
        return self.__class__(
            self.nr_measurements_updated + other.nr_measurements_updated,
            self.nr_measurements_deleted + other.nr_measurements_deleted,
            self.nr_measurements + other.nr_measurements,
            self.nr_metrics + other.nr_metrics,
        )

    @property
    def percentage_measurements_updated(self) -> int:
        """Return the percentage of the measurements updated."""
        return percentage(self.nr_measurements_updated, self.nr_measurements)

    @property
    def percentage_measurements_deleted(self) -> int:
        """Return the percentage of the measurements deleted."""
        return percentage(self.nr_measurements_deleted, self.nr_measurements)


def merge_unmerged_measurements(database: Database, dry_run: bool = False) -> Stats:
    """Due to a bug, measurements were not properly merged. Clean up by merging measurements where possible."""
    start = datetime.now()
    logger = logging.getLogger(__name__)
    logger.info("Starting %smigration 'merge unmerged measurements' at %s", "DRY RUN " if dry_run else "", start)
    estimated_nr_measurements = int(database.measurements.estimated_document_count())
    metric_uuids = database.measurements.distinct("metric_uuid")
    nr_metrics = len(metric_uuids)
    logger.info("Measurements collection has %d measurements for %d metrics", estimated_nr_measurements, nr_metrics)
    total_stats = Stats()
    for index, metric_uuid in enumerate(metric_uuids):  # pragma: no cover-behave
        logger.info("Merging measurements for metric %s (%d/%d)", metric_uuid, index + 1, nr_metrics)
        stats = _merge_unmerged_measurements_for_metric(database, metric_uuid, dry_run)
        log_stats(logger, stats, dry_run)
        total_stats += stats
    stop = datetime.now()
    logger.info("Finished migration 'merge unmerged measurements' at %s, took %s", stop, stop - start)
    log_stats(logger, total_stats, dry_run)
    return total_stats


def _merge_unmerged_measurements_for_metric(
    database: Database, metric_uuid: str, dry_run: bool
) -> Stats:  # pragma: no cover-behave
    """Merge the unmerged measurements of the specified metric."""
    updates: dict[ObjectId, str] = {}  # Mongo object ids of measurements that will be updated with a new end-timestamp
    deletes: list[ObjectId] = []  # The Mongo object ids of measurements that have been merged and will be deleted
    # The current measurement that will be updated if it is equal to a later measurement:
    current: MeasurementJSON = {"_id": ObjectId(), "end": ""}
    nr_measurements = 0
    for measurement in database.measurements.find(dict(metric_uuid=metric_uuid), sort=OLD_TO_NEW):
        nr_measurements += 1
        if _equal(current, measurement):
            updates[current["_id"]] = max(measurement["end"], current["end"])
            deletes.append(measurement["_id"])
        else:
            current = measurement
    mongo_operations: list[UpdateOne | DeleteMany] = [
        UpdateOne({"_id": object_id}, {"$set": dict(end=end)}) for object_id, end in updates.items()
    ]
    if deletes:
        mongo_operations.append(DeleteMany({"_id": {"$in": deletes}}))
    if mongo_operations and not dry_run:
        _backup_measurements(database, updates.keys(), "backup_updated_measurements")
        _backup_measurements(database, deletes, "backup_deleted_measurements")
        database.measurements.bulk_write(mongo_operations)
    return Stats(len(updates), len(deletes), nr_measurements, nr_metrics=1)


def _backup_measurements(
    database: Database, object_ids: Iterable[ObjectId], destination_collection: str
) -> None:  # pragma: no cover-behave
    """Backup the specified measurements to the specified collection."""
    database.measurements.aggregate(
        [
            {"$match": {"_id": {"$in": list(object_ids)}}},
            {"$merge": {"into": destination_collection, "on": "_id", "whenMatched": "replace"}},
        ]
    )


def _equal(measurement1: MeasurementJSON, measurement2: MeasurementJSON) -> bool:  # pragma: no cover-behave
    """Return whether the measurements are equal."""
    scales_equal = all(measurement1.get(scale) == measurement2.get(scale) for scale in SCALES)
    issues_statuses_equal = measurement1.get("issue_status") == measurement2.get("issue_status")
    sources_equal = measurement1.get("sources") == measurement2.get("sources")
    return scales_equal and issues_statuses_equal and sources_equal


def log_stats(logger: logging.Logger, stats: Stats, dry_run: bool) -> None:  # pragma: no cover-behave
    """Log the update and deletion statistics, if any."""
    if stats.nr_measurements_updated > 0 or stats.nr_measurements_deleted > 0 or stats.nr_metrics > 1:
        dry_run_label = "...DRY RUN, so not " if dry_run else "..."
        logger.info(
            "%supdated %d (%d%%) measurements and deleted %d (%d%%) measurements of %d measurements",
            dry_run_label,
            stats.nr_measurements_updated,
            stats.percentage_measurements_updated,
            stats.nr_measurements_deleted,
            stats.percentage_measurements_deleted,
            stats.nr_measurements,
        )


def percentage(value: int, total: int) -> int:  # pragma: no cover-behave
    """Calculate the percentage."""
    return round(100 * value / total) if total > 0 else 0
