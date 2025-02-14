"""Unit tests for the model actions."""

from model.actions import copy_metric, copy_report, copy_source, copy_subject

from ..base import DataModelTestCase


class CopySourceTest(DataModelTestCase):
    """Unit tests for the copy source action."""

    def setUp(self):
        """Extend to set up the source under test."""
        super().setUp()
        self.source = dict(name="Source", type="pip")

    def test_copy_name(self):
        """Test that the copy name is changed."""
        source_copy = copy_source(self.source, self.DATA_MODEL)
        self.assertEqual("Source (copy)", source_copy["name"])

    def test_copy_without_name(self):
        """Test that the copy name is based on the data model if the original source doesn't have a name."""
        self.source["name"] = ""
        source_copy = copy_source(self.source, self.DATA_MODEL)
        self.assertEqual("pip (copy)", source_copy["name"])

    def test_copy_without_name_change(self):
        """Test that the copy name can be left unchanged."""
        source_copy = copy_source(self.source, self.DATA_MODEL, change_name=False)
        self.assertEqual("Source", source_copy["name"])


class CopyMetricTest(DataModelTestCase):
    """Unit tests for the copy metric action."""

    def setUp(self):
        """Extend to set up the metric under test."""
        super().setUp()
        self.metric = dict(
            name="Metric", type="security_warnings", sources=dict(source_uuid=dict(type="owasp_zap", name="Source"))
        )

    def test_copy_name(self):
        """Test that the copy name is changed."""
        metric_copy = copy_metric(self.metric, self.DATA_MODEL)
        self.assertEqual("Metric (copy)", metric_copy["name"])

    def test_copy_without_name(self):
        """Test that the copy name is based on the data model if the original metric doesn't have a name."""
        self.metric["name"] = ""
        metric_copy = copy_metric(self.metric, self.DATA_MODEL)
        self.assertEqual("Security warnings (copy)", metric_copy["name"])

    def test_copy_without_name_change(self):
        """Test that the copy name can be left unchanged."""
        metric_copy = copy_metric(self.metric, self.DATA_MODEL, change_name=False)
        self.assertEqual("Metric", metric_copy["name"])

    def test_copy_sources(self):
        """Test that the sources are copied too."""
        metric_copy = copy_metric(self.metric, self.DATA_MODEL)
        self.assertEqual("Source", list(metric_copy["sources"].values())[0]["name"])


class CopySubjectTest(DataModelTestCase):
    """Unit tests for the copy subject action."""

    def setUp(self):
        """Extend to set up the subject under test."""
        super().setUp()
        self.subject = dict(
            type="software",
            name="Subject",
            metrics=dict(metric_uuid=dict(type="violations", name="Metric", sources={})),
        )

    def test_copy_name(self):
        """Test that the copy name is changed."""
        subject_copy = copy_subject(self.subject, self.DATA_MODEL)
        self.assertEqual("Subject (copy)", subject_copy["name"])

    def test_copy_without_name(self):
        """Test that the copy name is based on the data model if the original subject doesn't have a name."""
        self.subject["name"] = ""
        subject_copy = copy_subject(self.subject, self.DATA_MODEL)
        self.assertEqual("Software (copy)", subject_copy["name"])

    def test_copy_without_name_change(self):
        """Test that the copy name can be left unchanged."""
        subject_copy = copy_subject(self.subject, self.DATA_MODEL, change_name=False)
        self.assertEqual("Subject", subject_copy["name"])

    def test_copy_metrics(self):
        """Test that the metrics are copied too."""
        subject_copy = copy_subject(self.subject, self.DATA_MODEL)
        self.assertEqual("Metric", list(subject_copy["metrics"].values())[0]["name"])


class CopyReportTest(DataModelTestCase):
    """Unit tests for the copy report action."""

    def setUp(self):
        """Extend to set up the report under test."""
        super().setUp()
        self.report = dict(
            report_uuid="report_uuid",
            title="Report",
            subjects=dict(subject_uuid=dict(name="Subject", type="software", metrics={})),
        )

    def test_copy_title(self):
        """Test that the copy title is changed."""
        report_copy = copy_report(self.report, self.DATA_MODEL)
        self.assertEqual("Report (copy)", report_copy["title"])

    def test_copy_report_uuid(self):
        """Test that the report UUID can be changed."""
        report_copy = copy_report(self.report, self.DATA_MODEL)
        self.assertNotEqual(self.report["report_uuid"], report_copy["report_uuid"])

    def test_copy_subjects(self):
        """Test that the subjects are copied too."""
        report_copy = copy_report(self.report, self.DATA_MODEL)
        self.assertEqual("Subject", list(report_copy["subjects"].values())[0]["name"])
