"""Unit tests for the Jenkins job runs within time period collector."""

from datetime import datetime, timedelta

from .base import JenkinsTestCase


class JenkinsJobRunsWithinTimePeriodTest(JenkinsTestCase):
    """Unit tests for the Jenkins job runs within time period collector."""

    METRIC_TYPE = "job_runs_within_time_period"

    async def test_job_lookback_days(self):
        """Test that the build lookback_days are verified."""
        self.set_source_parameter("lookback_days", "3")

        now_dt = datetime.now()
        now_timestamp = int(datetime.timestamp(now_dt) * 1000)
        last_week_timestamp = int(datetime.timestamp(now_dt - timedelta(weeks=1)) * 1000)
        self.builds.extend([
            dict(result="SUCCESS", timestamp=now_timestamp),
            dict(result="SUCCESS", timestamp=last_week_timestamp)
        ])

        jenkins_json = dict(jobs=[dict(name="job", url=self.job_url, buildable=True, color="blue", builds=self.builds)])
        response = await self.collect(get_request_json_return_value=jenkins_json)

        expected_entities = [dict(build_count=1, key="job", name="job", url=self.job_url)]
        self.assert_measurement(response, value='1', entities=expected_entities)
