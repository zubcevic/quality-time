"""Unit tests for the report routes."""

from datetime import datetime
from typing import cast
from unittest.mock import Mock, patch
import copy

from shared.model.report import Report
from shared.utils.type import ReportId

from routes import (
    delete_report,
    export_report_as_json,
    export_report_as_pdf,
    get_report,
    get_report_issue_tracker_suggestions,
    get_report_issue_tracker_options,
    post_report_attribute,
    post_report_copy,
    post_report_import,
    post_report_new,
    post_report_issue_tracker_attribute,
)
from utils.functions import asymmetric_encrypt

from ..base import DataModelTestCase, disable_logging
from ..fixtures import JENNY, METRIC_ID, REPORT_ID, REPORT_ID2, SOURCE_ID, SUBJECT_ID, create_report


class ReportTestCase(DataModelTestCase):  # skipcq: PTC-W0046
    """Base class for report route unit tests."""

    ISSUE_TRACKER_URL = "https://jira"

    def setUp(self):
        """Extend to set up a report and a user session."""
        super().setUp()
        self.database.sessions.find_one.return_value = JENNY
        self.report = Report(self.database.datamodels.find_one(), create_report())
        self.database.reports.find.return_value = [self.report]
        self.database.reports.find_one.return_value = self.report
        self.database.measurements.find.return_value = []


@patch("bottle.request")
class PostReportAttributeTest(ReportTestCase):
    """Unit tests for the post report attribute route."""

    def test_post_report_title(self, request):
        """Test that the report title can be changed."""
        request.json = dict(title="New title")
        self.assertEqual(dict(ok=True), post_report_attribute(REPORT_ID, "title", self.database))
        self.database.reports.insert_one.assert_called_once_with(self.report)
        updated_report = self.database.reports.insert_one.call_args[0][0]
        self.assertEqual(
            dict(
                uuids=[REPORT_ID],
                email=JENNY["email"],
                description="Jenny Doe changed the title of report 'Report' from 'Report' to 'New title'.",
            ),
            updated_report["delta"],
        )

    def test_post_report_layout(self, request):
        """Test that the report layout can be changed."""
        request.json = dict(layout=[dict(x=1, y=2)])
        self.assertEqual(dict(ok=True), post_report_attribute(REPORT_ID, "layout", self.database))
        self.database.reports.insert_one.assert_called_once_with(self.report)
        updated_report = self.database.reports.insert_one.call_args[0][0]
        self.assertEqual(
            dict(
                uuids=[REPORT_ID],
                email=JENNY["email"],
                description="Jenny Doe changed the layout of report 'Report'.",
            ),
            updated_report["delta"],
        )

    def test_post_unsafe_comment(self, request):
        """Test that comments are sanitized, since they are displayed as inner HTML in the frontend."""
        request.json = dict(comment='Comment with script<script type="text/javascript">alert("Danger")</script>')
        self.assertEqual(dict(ok=True), post_report_attribute(REPORT_ID, "comment", self.database))
        self.database.reports.insert_one.assert_called_once_with(self.report)
        updated_report = self.database.reports.insert_one.call_args[0][0]
        self.assertEqual(
            dict(
                uuids=[REPORT_ID],
                email=JENNY["email"],
                description="Jenny Doe changed the comment of report 'Report' from '' to 'Comment with script'.",
            ),
            updated_report["delta"],
        )


@patch("bottle.request")
class ReportIssueTrackerPostAttributeTest(ReportTestCase):
    """Unit tests for the post report issue tracker attribute route."""

    def test_post_report_issue_tracker_type(self, request):
        """Test that the issue tracker type can be changed."""
        request.json = dict(type="azure_devops")
        self.assertEqual(dict(ok=True), post_report_issue_tracker_attribute(REPORT_ID, "type", self.database))
        self.database.reports.insert_one.assert_called_once_with(self.report)
        updated_report = self.database.reports.insert_one.call_args[0][0]
        self.assertEqual(
            dict(
                uuids=[REPORT_ID],
                email=JENNY["email"],
                description="Jenny Doe changed the type of the issue tracker of report 'Report' from "
                "'jira' to 'azure_devops'.",
            ),
            updated_report["delta"],
        )
        self.assertEqual(
            dict(type="azure_devops", parameters=dict(username="jadoe", password="secret")),
            updated_report["issue_tracker"],
        )

    def test_post_report_issue_tracker_url(self, request):
        """Test that the issue tracker url can be changed."""
        self.report["issue_tracker"] = dict(type="jira")
        request.json = dict(url=self.ISSUE_TRACKER_URL)
        result = post_report_issue_tracker_attribute(REPORT_ID, "url", self.database)
        self.assertTrue(result["ok"])
        self.assertEqual(-1, result["availability"][0]["status_code"])
        self.database.reports.insert_one.assert_called_once_with(self.report)
        updated_report = self.database.reports.insert_one.call_args[0][0]
        self.assertEqual(
            dict(
                uuids=[REPORT_ID],
                email=JENNY["email"],
                description="Jenny Doe changed the url of the issue tracker of report 'Report' from '' to "
                f"'{self.ISSUE_TRACKER_URL}'.",
            ),
            updated_report["delta"],
        )
        expected_issue_tracker = dict(type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL))
        self.assertEqual(expected_issue_tracker, updated_report["issue_tracker"])

    def test_post_report_issue_tracker_username(self, request):
        """Test that the issue tracker username can be changed."""
        request.json = dict(username="jodoe")
        self.assertEqual(dict(ok=True), post_report_issue_tracker_attribute(REPORT_ID, "username", self.database))
        self.database.reports.insert_one.assert_called_once_with(self.report)
        updated_report = self.database.reports.insert_one.call_args[0][0]
        self.assertEqual(
            dict(
                uuids=[REPORT_ID],
                email=JENNY["email"],
                description="Jenny Doe changed the username of the issue tracker of report 'Report' from "
                "'jadoe' to 'jodoe'.",
            ),
            updated_report["delta"],
        )
        expected_issue_tracker = dict(type="jira", parameters=dict(username="jodoe", password="secret"))
        self.assertEqual(expected_issue_tracker, updated_report["issue_tracker"])

    def test_post_report_issue_tracker_password(self, request):
        """Test that the issue tracker password can be changed."""
        request.json = dict(password="another secret")
        self.assertEqual(dict(ok=True), post_report_issue_tracker_attribute(REPORT_ID, "password", self.database))
        self.database.reports.insert_one.assert_called_once_with(self.report)
        updated_report = self.database.reports.insert_one.call_args[0][0]
        self.assertEqual(
            dict(
                uuids=[REPORT_ID],
                email=JENNY["email"],
                description="Jenny Doe changed the password of the issue tracker of report 'Report' from "
                "'******' to '**************'.",
            ),
            updated_report["delta"],
        )
        expected_issue_tracker = dict(parameters=dict(password="another secret", username="jadoe"), type="jira")
        self.assertEqual(expected_issue_tracker, updated_report["issue_tracker"])

    def test_post_report_issue_tracker_password_unchanged(self, request):
        """Test that nothing happens when the new issue tracker password is unchanged."""
        self.report["issue_tracker"] = dict(type="jira", parameters=dict(password="secret"))
        request.json = dict(password="secret")
        self.assertEqual(dict(ok=True), post_report_issue_tracker_attribute(REPORT_ID, "password", self.database))
        self.database.reports.insert_one.assert_not_called()


class ReportIssueTrackerGetTest(ReportTestCase):
    """Unit tests for the issue tracker GET routes."""

    def setUp(self):
        """Extend to add fixtures."""
        super().setUp()
        self.project_response = Mock()
        self.project_response.json.return_value = [dict(key="FOO", name="Foo")]
        self.issue_types_response = Mock()
        self.issue_types_response.json.return_value = dict(values=[dict(id="1", name="Bug", subtask=False)])

    @patch("requests.get")
    def test_get_issue_suggestions(self, requests_get):
        """Test that issue id suggestions can be retrieved from the issue tracker."""
        self.report["issue_tracker"] = dict(type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL))
        response = Mock()
        response.json.return_value = dict(issues=[dict(key="FOO-42", fields=dict(summary="Summary"))])
        requests_get.return_value = response
        suggested_issues = get_report_issue_tracker_suggestions(REPORT_ID, "summ", self.database)
        self.assertEqual(dict(suggestions=[dict(key="FOO-42", text="Summary")]), suggested_issues)

    @patch("requests.get")
    def test_get_issue_tracker_options_without_configured_report(self, requests_get):
        """Test the the issue tracker attribute options are retrieved from the issue tracker."""
        self.report["issue_tracker"] = dict(type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL))
        requests_get.return_value = self.project_response
        expected_options = dict(projects=[dict(key="FOO", name="Foo")], issue_types=[], fields=[])
        self.assertEqual(expected_options, get_report_issue_tracker_options(REPORT_ID, self.database))

    @patch("requests.get")
    def test_get_issue_tracker_options_without_configured_issue_type(self, requests_get):
        """Test the the issue tracker attribute options are retrieved from the issue tracker."""
        self.report["issue_tracker"] = dict(type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL, project_key="FOO"))
        requests_get.side_effect = [self.project_response, self.issue_types_response]
        expected_options = dict(
            projects=[dict(key="FOO", name="Foo")], issue_types=[dict(key="1", name="Bug")], fields=[]
        )
        self.assertEqual(expected_options, get_report_issue_tracker_options(REPORT_ID, self.database))

    @patch("requests.get")
    def test_get_issue_tracker_options_with_configured_issue_type(self, requests_get):
        """Test the the issue tracker attribute options are retrieved from the issue tracker."""
        self.report["issue_tracker"] = dict(
            type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL, project_key="FOO", issue_type="Bug")
        )
        fields_response = Mock()
        fields_response.json.return_value = dict(values=[dict(fieldId="labels", name="Labels")])
        requests_get.side_effect = [self.project_response, self.issue_types_response, fields_response]
        expected_options = dict(
            projects=[dict(key="FOO", name="Foo")],
            issue_types=[dict(key="1", name="Bug")],
            fields=[dict(key="labels", name="Labels")],
        )
        self.assertEqual(expected_options, get_report_issue_tracker_options(REPORT_ID, self.database))

    @patch("requests.get")
    @disable_logging
    def test_get_issue_tracker_project_options_error(self, requests_get):
        """Test the the issue tracker attribute options are retrieved from the issue tracker."""
        self.report["issue_tracker"] = dict(
            type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL, project_key="FOO", issue_type="Bug")
        )
        requests_get.side_effect = RuntimeError("yo")
        expected_options = dict(projects=[], issue_types=[], fields=[])
        self.assertEqual(expected_options, get_report_issue_tracker_options(REPORT_ID, self.database))

    @patch("requests.get")
    @disable_logging
    def test_get_issue_tracker_issue_type_options_error(self, requests_get):
        """Test the the issue tracker attribute options are retrieved from the issue tracker."""
        self.report["issue_tracker"] = dict(
            type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL, project_key="FOO", issue_type="Bug")
        )
        requests_get.side_effect = [self.project_response, RuntimeError("yo")]
        expected_options = dict(projects=[dict(key="FOO", name="Foo")], issue_types=[], fields=[])
        self.assertEqual(expected_options, get_report_issue_tracker_options(REPORT_ID, self.database))

    @patch("requests.get")
    @disable_logging
    def test_get_issue_tracker_field_options_error(self, requests_get):
        """Test the the issue tracker attribute options are retrieved from the issue tracker."""
        self.report["issue_tracker"] = dict(
            type="jira", parameters=dict(url=self.ISSUE_TRACKER_URL, project_key="FOO", issue_type="Bug")
        )
        requests_get.side_effect = [self.project_response, self.issue_types_response, RuntimeError("yo")]
        expected_options = dict(
            projects=[dict(key="FOO", name="Foo")], issue_types=[dict(key="1", name="Bug")], fields=[]
        )
        self.assertEqual(expected_options, get_report_issue_tracker_options(REPORT_ID, self.database))


class ReportTest(ReportTestCase):
    """Unit tests for adding, deleting, and getting reports."""

    PAST_DATE = "2021-08-31T23:59:59.000Z"

    def setUp(self):
        """Extend to set up a database with a report and a user session."""
        super().setUp()
        self.database.reports.distinct.return_value = [REPORT_ID]
        self.database.measurements.find_one.return_value = {"sources": []}
        self.database.measurements.aggregate.return_value = []

    def test_get_report(self):
        """Test that a report can be retrieved."""
        self.assertEqual(REPORT_ID, get_report(self.database, REPORT_ID)["reports"][0][REPORT_ID])

    def test_get_all_reports(self):
        """Test that all reports can be retrieved."""
        self.assertEqual(1, len(get_report(self.database)["reports"]))

    @patch("bottle.request")
    def test_get_all_reports_with_time_travel(self, request):
        """Test that all reports can be retrieved."""
        request.query = dict(report_date=self.PAST_DATE)
        self.assertEqual(1, len(get_report(self.database)["reports"]))

    @patch("bottle.request")
    def test_ignore_deleted_reports_when_time_traveling(self, request):
        """Test that deleted reports are not retrieved."""
        request.query = dict(report_date=self.PAST_DATE)
        self.report["deleted"] = "true"
        self.assertEqual(0, len(get_report(self.database)["reports"]))

    def test_get_report_and_info_about_other_reports(self):
        """Test that a report can be retrieved, and that other reports are also returned."""
        self.database.reports.find.return_value.insert(0, dict(_id="id2", report_uuid=REPORT_ID2))
        self.assertEqual(2, len(get_report(self.database, REPORT_ID)["reports"]))

    def test_get_report_missing(self):
        """Test that a non-existant report can not be retrieved."""
        self.database.reports.find.return_value = []
        self.assertEqual([], get_report(self.database, ReportId("report does not exist"))["reports"])

    @patch("bottle.request")
    def test_get_old_report(self, request):
        """Test that an old report can be retrieved and credentials are hidden."""
        request.query = dict(report_date=self.PAST_DATE)
        report = get_report(self.database, REPORT_ID)["reports"][0]
        self.assertEqual("this string replaces credentials", report["issue_tracker"]["parameters"]["password"])
        self.assertEqual(
            "this string replaces credentials",
            report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"]["password"],
        )
        expected_counts = dict(blue=0, red=0, green=0, yellow=0, grey=0, white=1)
        self.assertEqual(expected_counts, report["summary"])
        self.assertEqual({SUBJECT_ID: expected_counts}, report["summary_by_subject"])
        self.assertEqual(dict(security=expected_counts), report["summary_by_tag"])

    def test_issue_status(self):
        """Test that the issue status is part of the metric."""
        issue_status = dict(issue_id="FOO-42", name="In progress", description="Issue is being worked on")
        measurement = dict(
            _id="id",
            metric_uuid=METRIC_ID,
            count=dict(status="target_not_met", status_start="2020-12-03:22:29:00+00:00"),
            sources=[dict(source_uuid=SOURCE_ID, parse_error=None, connection_error=None, value="42")],
            issue_status=[issue_status],
        )
        self.database.measurements.aggregate.return_value = []
        self.database.measurements.find.return_value = [measurement]
        self.report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["issue_ids"] = ["FOO-42"]
        report = get_report(self.database, REPORT_ID)["reports"][0]
        self.assertEqual(issue_status, report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["issue_status"][0])

    @patch("shared.utils.functions.datetime")
    def test_get_tag_report(self, date_time):
        """Test that a tag report can be retrieved."""
        date_time.now.return_value = now = datetime.now()
        self.database.reports.find.return_value = [
            dict(
                _id="id",
                report_uuid=REPORT_ID,
                title="Report",
                subjects={
                    "subject_without_metrics": dict(metrics={}),
                    SUBJECT_ID: dict(
                        name="Subject",
                        type="software",
                        metrics=dict(
                            metric_with_tag=dict(type="violations", tags=["tag"]),
                            metric_without_tag=dict(type="violations", tags=["other tag"]),
                        ),
                    ),
                },
            )
        ]
        expected_counts = dict(blue=0, red=0, green=0, yellow=0, grey=0, white=1)
        self.assertDictEqual(
            dict(
                reports=[
                    dict(
                        summary=expected_counts,
                        summary_by_tag=dict(tag=expected_counts),
                        summary_by_subject={SUBJECT_ID: expected_counts},
                        title='Report for tag "tag"',
                        subtitle="Note: tag reports are read-only",
                        report_uuid="tag-tag",
                        timestamp=now.replace(microsecond=0).isoformat(),
                        subjects={
                            SUBJECT_ID: dict(
                                name="Report ❯ Subject",
                                type="software",
                                metrics=dict(
                                    metric_with_tag=dict(
                                        status=None,
                                        status_start=None,
                                        scale="count",
                                        sources={},
                                        recent_measurements=[],
                                        latest_measurement=None,
                                        type="violations",
                                        tags=["tag"],
                                    )
                                ),
                            )
                        },
                    ),
                ]
            ),
            get_report(self.database, "tag-tag"),
        )

    @patch("shared.utils.functions.datetime")
    def test_no_empty_tag_report(self, date_time):
        """Test that empty tag reports are omitted."""
        date_time.now.return_value = datetime.now()
        self.database.reports.find.return_value = [
            dict(
                _id="id",
                report_uuid=REPORT_ID,
                title="Report",
                subjects={
                    "subject_without_metrics": dict(metrics={}),
                    SUBJECT_ID: dict(
                        name="Subject",
                        type="software",
                        metrics=dict(
                            metric_with_tag=dict(type="metric_type", tags=["tag"]),
                            metric_without_tag=dict(type="metric_type", tags=["other tag"]),
                        ),
                    ),
                },
            )
        ]
        self.assertDictEqual(dict(reports=[]), get_report(self.database, "tag-non-existing-tag"))

    def test_add_report(self):
        """Test that a report can be added."""
        self.assertTrue(post_report_new(self.database)["ok"])
        self.database.reports.insert_one.assert_called_once()
        inserted = self.database.reports.insert_one.call_args_list[0][0][0]
        self.assertEqual("New report", inserted["title"])
        self.assertEqual(
            dict(uuids=[inserted[REPORT_ID]], email=JENNY["email"], description="Jenny Doe created a new report."),
            inserted["delta"],
        )

    def test_copy_report(self):
        """Test that a report can be copied."""
        self.assertTrue(post_report_copy(REPORT_ID, self.database)["ok"])
        self.database.reports.insert_one.assert_called_once()
        inserted_report = self.database.reports.insert_one.call_args[0][0]
        inserted_report_uuid = inserted_report[REPORT_ID]
        self.assertNotEqual(self.report[REPORT_ID], inserted_report_uuid)
        self.assertEqual(
            dict(
                uuids=sorted([REPORT_ID, inserted_report_uuid]),
                email=JENNY["email"],
                description="Jenny Doe copied the report 'Report'.",
            ),
            inserted_report["delta"],
        )

    @patch("requests.get")
    def test_get_pdf_report(self, requests_get):
        """Test that a PDF version of the report can be retrieved."""
        response = Mock()
        response.content = b"PDF"
        requests_get.return_value = response
        self.assertEqual(b"PDF", export_report_as_pdf(REPORT_ID))
        requests_get.assert_called_once_with(f"http://renderer:9000/api/render?path={REPORT_ID}")

    @patch("requests.get")
    def test_get_pdf_tag_report(self, requests_get):
        """Test that a PDF version of a tag report can be retrieved."""
        requests_get.return_value = Mock(content=b"PDF")
        self.assertEqual(b"PDF", export_report_as_pdf(cast(ReportId, "tag-security")))
        requests_get.assert_called_once_with("http://renderer:9000/api/render?path=tag-security")

    def test_delete_report(self):
        """Test that the report can be deleted."""
        self.assertEqual(dict(ok=True), delete_report(REPORT_ID, self.database))
        inserted = self.database.reports.insert_one.call_args_list[0][0][0]
        self.assertEqual(
            dict(uuids=[REPORT_ID], email=JENNY["email"], description="Jenny Doe deleted the report 'Report'."),
            inserted["delta"],
        )


class ReportImportAndExportTest(ReportTestCase):
    """Unit tests for importing and exporting reports."""

    def setUp(self):
        """Extend to set up a database with a report and a user session."""
        super().setUp()
        self.private_key = """-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBANdJVRdylaadsaau
hRxNToIUIk/nSKMzfjjjP/20FEShkax1g4CYTwTdSMcuV+4blzzFSE+eDmMs1LNk
jAPzfNAnHwJsjz2vt16JXDma+PuIPTCI5uobCbPUJty+6XlnzFyVjy36+SgeA8SM
HHTprOxhwxU++O5cnzO7Jb4mjoOvAgMBAAECgYEAr9gMErzbE16Wroi53OYgDAua
Ax3srLDwllK3/+fI7k3yCKVrpevCDz0XpulplOkgXNjfOXjmU4dYrLahztBgzrwt
KzA7H8XylleIbuk7wUJ8jD+1dzxgu/ZB+iLzUla8r9/MmdhAzELmYBc9hIEWl6FW
2BlQxmLNbOj2kh/aWoECQQD4GyLDzxEFVBPYYo+Ut3T05a0IlCnCSKU6saDSuFFG
GhiM1HQMAnnuC3okgVpAOA7Rn2z9xMqLcdiv+Amnzh3hAkEA3iLgQUwMj6v97Jkb
KFxQazzkOmgMKFGH2MbZGGwDDva1QlD9awjBW0aj4nUHNsUob6LVJCbCocQFSNDu
eXgzjwJATSg7NoPFuk98YHW+SzSGZcarehiBqA7pe4hUCFQTymZBLkK/2CBJBPOC
x6mGhKQqT5xxy7WQe68rAQZ1Ej9yYQJAbgd8aRuQRUH+HsmfyBghxVx99+g9zWLF
FT05n30w7qKJGfYf8Hp/vAR7fNpW3mw+IT3YsXV5hsMfkvfah9RgRQJAVGysMIfp
eX94CsogDhIWSaXreAfpcWQu1Dg5FCmpZTGRJps2x52CPq5icgBZeIODElIvkJbn
JqqQtg8ZsTm6Pw==
-----END PRIVATE KEY-----
"""

        self.public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDXSVUXcpWmnbGmroUcTU6CFCJP
50ijM3444z/9tBREoZGsdYOAmE8E3UjHLlfuG5c8xUhPng5jLNSzZIwD83zQJx8C
bI89r7deiVw5mvj7iD0wiObqGwmz1Cbcvul5Z8xclY8t+vkoHgPEjBx06azsYcMV
PvjuXJ8zuyW+Jo6DrwIDAQAB
-----END PUBLIC KEY-----
"""

        self.database.secrets.find_one.return_value = {"public_key": self.public_key, "private_key": self.private_key}

    def test_get_json_report(self):
        """Test that a JSON version of the report can be retrieved with encrypted credentials."""
        expected_report = copy.deepcopy(self.report)
        expected_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"].pop(
            "password"
        )
        expected_report["issue_tracker"]["parameters"].pop("password")
        self.database.reports.find_one.return_value = copy.deepcopy(self.report)

        # Without provided public key
        exported_report = export_report_as_json(self.database, REPORT_ID)
        exported_password = exported_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID][
            "parameters"
        ].pop("password")
        exported_report["issue_tracker"]["parameters"].pop("password")

        self.assertDictEqual(exported_report, expected_report)
        self.assertTrue(isinstance(exported_password, tuple))
        self.assertTrue(len(exported_password) == 2)

    def test_get_nonexisting_json_report(self):
        """Test that None is returned if report doesn't exist."""
        self.database.reports.find_one.return_value = None

        # Without provided public key
        exported_report = export_report_as_json(self.database, "non_existing_report")
        self.assertIsNone(exported_report)

    def test_get_json_report_without_public_key(self):
        """Test that an error message is returned if the database has no public key."""
        self.database.secrets.find_one.return_value = None
        response = export_report_as_json(self.database, REPORT_ID)
        self.assertIn("error", response)

    @patch("routes.report.bottle.request")
    def test_get_json_report_with_public_key(self, request):
        """Test that a provided public key can be used to encrypt the passwords."""
        expected_report = copy.deepcopy(self.report)
        expected_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"].pop(
            "password"
        )
        expected_report["issue_tracker"]["parameters"].pop("password")

        request.query = {"public_key": self.public_key}
        mocked_report = copy.deepcopy(self.report)
        mocked_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"]["password"] = [
            "0",
            "1",
        ]  # Use a list as password for coverage of the last line
        self.database.reports.find_one.return_value = mocked_report
        exported_report = export_report_as_json(self.database, REPORT_ID)
        exported_password = exported_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID][
            "parameters"
        ].pop("password")
        exported_report["issue_tracker"]["parameters"].pop("password")

        self.assertDictEqual(exported_report, expected_report)
        self.assertTrue(isinstance(exported_password, tuple))
        self.assertTrue(len(exported_password) == 2)

    @patch("bottle.request")
    def test_post_report_import(self, request):
        """Test that a report is imported correctly."""
        mocked_report = copy.deepcopy(self.report)
        mocked_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"][
            "password"
        ] = asymmetric_encrypt(self.public_key, "test_message")
        request.json = mocked_report
        post_report_import(self.database)
        inserted = self.database.reports.insert_one.call_args_list[0][0][0]
        self.assertEqual("Report", inserted["title"])
        self.assertEqual("Jenny Doe imported a new report", inserted["delta"]["description"])
        self.assertNotEqual(REPORT_ID, inserted[REPORT_ID])

    @patch("bottle.request")
    def test_post_report_import_without_encrypted_credentials(self, request):
        """Test that a report is imported correctly."""
        mocked_report = copy.deepcopy(self.report)
        mocked_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"][
            "password"
        ] = "unencrypted_password"
        request.json = mocked_report
        post_report_import(self.database)
        inserted_report = self.database.reports.insert_one.call_args_list[0][0][0]
        inserted_subject = list(inserted_report["subjects"].items())[0][1]
        inserted_metric = list(inserted_subject["metrics"].items())[0][1]
        inserted_source = list(inserted_metric["sources"].items())[0][1]
        self.assertEqual("unencrypted_password", inserted_source["parameters"]["password"])

    @patch("bottle.request")
    def test_post_report_import_with_failed_decryption(self, request):
        """Test that a report is imported correctly."""
        mocked_report = copy.deepcopy(self.report)
        mocked_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"]["password"] = (
            "not_properly_encrypted==",
            "test_message",
        )
        request.json = mocked_report
        response = post_report_import(self.database)
        self.assertIn("error", response)

    @patch("bottle.request")
    def test_post_report_import_without_private_key(self, request):
        """Test that a report cannot be imported if the Quality-time instance has no private key."""
        self.database.secrets.find_one.return_value = None
        mocked_report = copy.deepcopy(self.report)
        mocked_report["subjects"][SUBJECT_ID]["metrics"][METRIC_ID]["sources"][SOURCE_ID]["parameters"][
            "password"
        ] = "unencrypted_password"
        request.json = mocked_report
        response = post_report_import(self.database)
        self.assertIn("error", response)
