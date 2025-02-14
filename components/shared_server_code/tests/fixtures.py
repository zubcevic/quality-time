"""Shared test data."""

from typing import cast

from shared.utils.type import MetricId, ReportId, SourceId, SubjectId


METRIC_ID = cast(MetricId, "metric_uuid")
METRIC_ID2 = cast(MetricId, "metric_uuid2")
REPORT_ID = cast(ReportId, "report_uuid")
REPORT_ID2 = cast(ReportId, "report_uuid2")
SOURCE_ID = cast(SourceId, "source_uuid")
SOURCE_ID2 = cast(SourceId, "source_uuid2")
SUBJECT_ID = cast(SubjectId, "subject_uuid")

JOHN = dict(user="John", email="john@example.org", common_name="John Doe")
