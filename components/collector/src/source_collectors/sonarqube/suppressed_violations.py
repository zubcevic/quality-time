"""SonarQube suppressed violations collector."""

from base_collectors import SourceCollector
from collector_utilities.type import URL
from model import Entity, SourceMeasurement, SourceResponses

from .violations import SonarQubeViolations


class SonarQubeSuppressedViolations(SonarQubeViolations):
    """SonarQube suppressed violations collector."""

    rules_configuration = "suppression_rules"

    async def _landing_url(self, responses: SourceResponses) -> URL:  # skipcq: PYL-W0613
        """Override to not include the rules parameter in the landing URL.

        This collector uses two SonarQube endpoints to get the suppressed violations. As we can't include both URLs in
        the landing URL, we use the overview of all issues as landing page.
        """
        url = await SourceCollector._api_url(self)  # pylint: disable=protected-access
        component = self._parameter("component")
        branch = self._parameter("branch")
        return URL(f"{url}/project/issues?id={component}&branch={branch}")

    async def _get_source_responses(self, *urls: URL, **kwargs) -> SourceResponses:
        """Get the suppressed violations from SonarQube.

        In addition to the suppressed rules, also get issues closed as false positive and won't fix from SonarQube
        as well as the total number of violations.
        """
        url = await SourceCollector._api_url(self)  # pylint: disable=protected-access
        component = self._parameter("component")
        branch = self._parameter("branch")
        all_issues_api_url = URL(f"{url}/api/issues/search?componentKeys={component}&branch={branch}")
        resolved_issues_api_url = URL(
            f"{all_issues_api_url}&status=RESOLVED&resolutions=WONTFIX,FALSE-POSITIVE&ps=500"
            f"{self._query_parameter('severities')}{self._query_parameter(self.types_parameter)}"
        )
        return await super()._get_source_responses(*(urls + (resolved_issues_api_url, all_issues_api_url)), **kwargs)

    async def _parse_source_responses(self, responses: SourceResponses) -> SourceMeasurement:
        """Extend to get the total number of violations from the responses."""
        measurement = await super()._parse_source_responses(responses[:-1])
        measurement.total = str((await responses[-1].json())["total"])
        return measurement

    async def _entity(self, issue) -> Entity:
        """Extend to add the resolution to the entity."""
        entity = await super()._entity(issue)
        resolution = issue.get("resolution", "").lower()
        entity["resolution"] = dict(wontfix="won't fix").get(resolution, resolution)
        return entity
