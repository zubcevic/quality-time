"""SonarQube security warnings collector."""

from base_collectors import SourceCollector
from collector_utilities.type import URL
from model import Entity, SourceMeasurement, SourceResponses

from .base import SonarQubeCollector
from .violations import SonarQubeViolations


class SonarQubeSecurityWarnings(SonarQubeViolations):
    """SonarQube security warnings. The security warnings are a sum of the vulnerabilities and security hotspots."""

    types_parameter = "security_types"

    async def _landing_url(self, responses: SourceResponses) -> URL:
        """Extend to return the correct landing url depending on the selected security types."""
        security_types = self._parameter(self.types_parameter)
        base_landing_url = await SourceCollector._landing_url(self, responses)  # pylint: disable=protected-access
        component = self._parameter("component")
        branch = self._parameter("branch")
        common_url_parameters, extra_url_parameters = f"?id={component}&branch={branch}", ""
        if "vulnerability" in security_types and "security_hotspot" in security_types:
            landing_path = "dashboard"
        elif "vulnerability" in security_types:
            landing_path = "project/issues"
            # We don't use self._query_parameter() because when we get here, the value of the types parameter is fixed
            extra_url_parameters = f"{self._query_parameter('severities')}&resolved=false&types=VULNERABILITY"
        else:
            landing_path = "project/security_hotspots"
        return URL(f"{base_landing_url}/{landing_path}{common_url_parameters}{extra_url_parameters}")

    async def _get_source_responses(self, *urls: URL, **kwargs) -> SourceResponses:  # skipcq: PYL-W0613
        """Extend to add urls for the selected security types."""
        api_urls = []
        security_types = self._parameter(self.types_parameter)
        component = self._parameter("component")
        branch = self._parameter("branch")
        base_url = await SonarQubeCollector._api_url(self)  # pylint: disable=protected-access
        if "vulnerability" in security_types:
            api_urls.append(
                URL(
                    f"{base_url}/api/issues/search?componentKeys={component}&resolved=false&ps=500"
                    f"{self._query_parameter('severities')}&types=VULNERABILITY&branch={branch}"
                )
            )
        if "security_hotspot" in security_types:
            api_urls.append(
                URL(f"{base_url}/api/hotspots/search?projectKey={component}&status=TO_REVIEW&ps=500&branch={branch}")
            )
        return await super()._get_source_responses(*api_urls, **kwargs)

    async def _parse_source_responses(self, responses: SourceResponses) -> SourceMeasurement:
        """Override to parse the selected security types."""
        security_types = self._parameter(self.types_parameter)
        review_priorities = [priority.upper() for priority in self._parameter("review_priorities")]
        vulnerabilities = (
            await super()._parse_source_responses(SourceResponses(responses=[responses[0]]))
            if "vulnerability" in security_types
            else SourceMeasurement()
        )
        if "security_hotspot" in security_types:
            json = await responses[-1].json()
            hotspots = [
                await self.__entity(hotspot)
                for hotspot in json.get("hotspots", [])
                if hotspot["vulnerabilityProbability"] in review_priorities
            ]
        else:
            hotspots = []
        return SourceMeasurement(
            value=str(int(vulnerabilities.value or 0) + len(hotspots)),
            entities=vulnerabilities.entities + hotspots,
        )

    async def __entity(self, hotspot) -> Entity:
        """Create the security warning entity."""
        return Entity(
            key=hotspot["key"],
            component=hotspot["component"],
            message=hotspot["message"],
            type="security_hotspot",
            url=await self.__hotspot_landing_url(hotspot["key"]),
            review_priority=hotspot["vulnerabilityProbability"].lower(),
            creation_date=hotspot["creationDate"],
            update_date=hotspot["updateDate"],
        )

    async def __hotspot_landing_url(self, hotspot_key: str) -> URL:
        """Generate a landing url for the hotspot."""
        url = await SonarQubeCollector._landing_url(self, SourceResponses())  # pylint: disable=protected-access
        component = self._parameter("component")
        branch = self._parameter("branch")
        return URL(f"{url}/security_hotspots?id={component}&hotspots={hotspot_key}&branch={branch}")
