"""Measurement model class."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Optional, cast

from packaging.version import InvalidVersion, Version

from shared_data_model import DATA_MODEL
from shared.utils.functions import iso_timestamp, percentage
from shared.utils.type import Scale, Status, Value

from .metric import Metric
from .source import Source


class ScaleMeasurement(dict):  # lgtm [py/missing-equals]
    """Class representing a measurement on a specific scale."""

    def __init__(
        self,
        *args,
        previous_scale_measurement: ScaleMeasurement | None,
        measurement: Measurement,
        **kwargs,
    ):
        self.__previous_scale_measurement: ScaleMeasurement | None = previous_scale_measurement
        self._measurement: Measurement = measurement
        self._metric: Metric = self._measurement.metric
        super().__init__(*args, **kwargs)

    def status(self) -> Status | None:
        """Return the measurement status."""
        return cast(Optional[Status], self.get("status"))

    def status_start(self) -> str | None:
        """Return the start date of the status."""
        if status_start := self.get("status_start"):
            return cast(str, status_start)
        return None  # pragma: no cover-behave

    def update_value_and_status(self) -> None:
        """Update the measurement value and status."""
        self["direction"] = self._metric.direction()
        self["value"] = value = (
            self._calculate_value() if self._measurement.sources_exist() and self._measurement.sources_ok() else None
        )
        self["status"] = status = self.__calculate_status(value)
        self.__set_status_start(status)

    def __set_status_start(self, status: str | None) -> None:
        """Set the status start date."""
        previous = self.__previous_scale_measurement
        self["status_start"] = (
            previous.status_start() if previous and previous.status() == status else self._measurement["start"]
        )

    def update_targets(self) -> None:
        """Update the measurement targets."""
        self["target"] = self._metric.get_target("target")
        self["near_target"] = self._metric.get_target("near_target")
        self["debt_target"] = self._metric.get_target("debt_target")

    @abstractmethod
    def _calculate_value(self) -> str:
        """Calculate the value of the measurement."""

    def __calculate_status(self, value: str | None) -> Status | None:
        """Determine the status of the measurement."""
        target, near_target, debt_target = (
            self.get("target"),
            self.get("near_target"),
            self.get("debt_target"),
        )
        if value is None:
            status = self.__calculate_status_without_measurement()
        elif not self._metric.evaluate_targets():
            status = "informative"
        elif self._better_or_equal(value, target):
            status = "target_met"
        elif (
            self._metric.accept_debt()
            and not self._measurement.debt_target_expired()
            and self._better_or_equal(value, debt_target)
        ):
            status = "debt_target_met"
        elif self._better_or_equal(target, near_target) and self._better_or_equal(value, near_target):
            status = "near_target_met"
        else:
            status = "target_not_met"
        return status

    def __calculate_status_without_measurement(self) -> Status | None:
        """Determine the status of the measurement if there is no measurement value."""
        # Allow for accepted debt if there is no measurement yet so that the fact that a metric does not have a
        # source can be accepted as technical debt
        if not self._metric.sources and self._metric.accept_debt() and not self._metric.debt_end_date_passed():
            return "debt_target_met"
        return None

    @abstractmethod
    def _better_or_equal(self, value1: str | None, value2: str | None) -> bool:
        """Return whether value 1 is better or equal than value 2."""


class CountScaleMeasurement(ScaleMeasurement):
    """Measurement with a count scale."""

    def _calculate_value(self) -> str:
        """Override to calculate the value of the count scale measurement."""
        sources = self._measurement.sources()
        values = [int(str(source.value())) - source.value_of_entities_to_ignore() for source in sources]
        add = self._metric.addition()
        return str(add(values))

    def _better_or_equal(self, value1: str | None, value2: str | None) -> bool:
        """Override to convert the values to integers before comparing."""
        better_or_equal = {">": int.__ge__, "<": int.__le__}[self["direction"]]
        return better_or_equal(int(value1 or 0), int(value2 or 0))


class PercentageScaleMeasurement(ScaleMeasurement):
    """Measurement with a percentage scale."""

    def _calculate_value(self) -> str:
        """Override to calculate the percentage."""
        sources = self._measurement.sources()
        values = [int(str(source.value())) - source.value_of_entities_to_ignore() for source in sources]
        totals = [int(source.total() or 100) for source in sources]
        direction = self._metric.direction()
        if (add := self._metric.addition()) is sum:
            # The metric specifies to sum the percentages of each source. Directly summing percentages isn't possible
            # mathematically, so we first sum the nominators and denominators and then divide the sums
            value = percentage(add(values), add(totals), direction)
        else:
            # The metric specifies to take the minimum or maximum of the percentage of each source, so we first divide
            # the nominators and denominators per source to calculate the percentage per source, and then take the
            # minimum or maximum value
            value = add([percentage(value, total, direction) for value, total in zip(values, totals)])
        return str(value)

    def _better_or_equal(self, value1: str | None, value2: str | None) -> bool:
        """Override to convert the values to floats before comparing."""
        better_or_equal = {">": float.__ge__, "<": float.__le__}[self["direction"]]
        return better_or_equal(float(value1 or 0), float(value2 or 0))


class VersionNumberScaleMeasurement(ScaleMeasurement):
    """Measurement with a version number scale."""

    def _calculate_value(self) -> str:
        """Override to calculate the version number."""
        values = [self.parse_version(source.value()) for source in self._measurement.sources()]
        add = self._metric.addition()  # Returns either min or max
        return str(add(values))

    def _better_or_equal(self, value1: str | None, value2: str | None) -> bool:
        """Override to convert the values to version numbers before comparing."""
        better_or_equal = {">": Version.__ge__, "<": Version.__le__}[self["direction"]]
        return better_or_equal(self.parse_version(value1), self.parse_version(value2))

    @staticmethod
    def parse_version(value: str | None) -> Version:
        """Parse the version."""
        if value is not None:  # pragma: no cover-behave
            try:
                return Version(value)
            except InvalidVersion:
                pass
        return Version("0")


class Measurement(dict):  # lgtm [py/missing-equals]
    """Class representing a measurement."""

    # LGTM wants us to implement __eq__ because this class has extra instance attributes. However, the measurement
    # dictionary contains the metric UUID and thus we don't need to compare the instance attributes to know whether
    # two measurements are the same.

    SCALE_CLASSES = dict(
        count=CountScaleMeasurement,
        percentage=PercentageScaleMeasurement,
        version_number=VersionNumberScaleMeasurement,
    )

    def __init__(self, metric: Metric, *args, **kwargs) -> None:
        self.metric = metric
        self.__previous_measurement: Measurement | None = kwargs.pop("previous_measurement", None)
        super().__init__(*args, **kwargs)
        if self.__previous_measurement or "start" not in self:
            self["start"] = self["end"] = iso_timestamp()
        self["sources"] = [Source(source["source_uuid"], self.metric, source) for source in self.get("sources", [])]

    def scale_measurement(self, scale: Scale) -> ScaleMeasurement:
        """Create a measurement with a specific scale."""
        measurement_class = self.SCALE_CLASSES[scale]
        previous = None if self.__previous_measurement is None else self.__previous_measurement[scale]
        # Mypy thinks the SCALE_CLASSES dict lookup results in a class of type ScaleMeasurement and complains that
        # ScaleMeasurement, being abstract, can't be instantiated. Suppress the error.
        return measurement_class(
            self.get(scale, {}), measurement=self, previous_scale_measurement=previous
        )  # type: ignore[abstract]

    def copy(self) -> Measurement:
        """Extend to return an instance of this class instead of a dict."""
        return self.__class__(self.metric, super().copy(), previous_measurement=self)

    def __getitem__(self, item):
        """Override to convert the scale dictionary to a ScaleMeasurement instance before returning it."""
        if item in self.metric.scales() and not isinstance(self.get(item), ScaleMeasurement):
            self[item] = self.scale_measurement(item)
        return super().__getitem__(item)

    def equals(self, other: Measurement) -> bool:
        """Return whether this measurement is unchanged compared to an (older) measurement."""
        scales_equal = all(self[scale] == other[scale] for scale in self.metric.scales())
        issues_statuses_equal = other.get("issue_status") == self.get("issue_status")
        sources_equal = other.sources() == self.sources()
        return scales_equal and issues_statuses_equal and sources_equal

    def debt_target_expired(self) -> bool:
        """Return whether the technical debt target is expired.

        Technical debt is considered expired when it was turned off, when the end date passed or when the metric has
        issues that all have been done.
        """
        any_debt_target = any(self[scale].get("debt_target") is not None for scale in self.metric.scales())
        accept_debt_expired = not self.metric.accept_debt() or self.metric.debt_end_date_passed()
        return (accept_debt_expired or self.__all_issues_done()) if any_debt_target else False

    def __all_issues_done(self) -> bool:
        """Return whether all issues have been done. Return False if there are no issues."""
        issues_ids = self.metric.issue_ids()
        if not issues_ids:
            return False
        issue_statuses = self.metric.issue_statuses(self)
        if len(issue_statuses) < len(issues_ids):
            return False  # Not all issue ids have a status; assume issues without status have not been done
        return all(status.get("status_category") == "done" for status in issue_statuses)

    def status(self) -> Status:
        """Return the status of the measurement."""
        return cast(Status, self.get(self.metric.scale(), {}).get("status", self.get("status")))

    def status_start(self):
        """Return the start timestamp of the current status, if any."""
        return self.get(self.metric.scale(), {}).get("status_start")

    def copy_entity_user_data(self, measurement: Measurement) -> None:
        """Copy the entity user data from the measurement to this measurement."""
        old_sources = {source["source_uuid"]: source for source in measurement.sources()}
        for new_source in self.sources():
            if old_source := old_sources.get(new_source["source_uuid"]):
                new_source.copy_entity_user_data(old_source)

    def update_measurement(self) -> None:
        """Update the measurement targets, values, and statuses."""
        self[self.metric.scale()].update_targets()
        for scale in self.metric.scales():
            self[scale].update_value_and_status()

    def sources_ok(self) -> bool:
        """Return whether there are sources and none have configuration, parse, or connection errors."""
        sources = self.sources()
        for source in sources:
            source_type = self.metric["sources"][source["source_uuid"]]["type"]
            if source_type not in DATA_MODEL.metrics[self.metric["type"]].sources:
                return False
        return bool(sources) and not any(source["parse_error"] or source["connection_error"] for source in sources)

    def sources_exist(self) -> bool:
        """Return whether all measurement sources exist in the metric."""
        return all(source["source_uuid"] in self.metric.source_uuids for source in self.sources())

    def sources(self) -> Sequence[Source]:
        """Return the measurement's sources."""
        return cast(Sequence[Source], self["sources"])

    def value(self) -> Value:
        """Return the value of the measurement."""
        return cast(Value, self[self.metric.scale()].get("value"))

    def summarize(self):
        """Return a summary of this measurement."""
        return {
            self.metric.scale(): dict(value=self.value(), status=self.status()),
            "start": self["start"],
            "end": self["end"],
        }
