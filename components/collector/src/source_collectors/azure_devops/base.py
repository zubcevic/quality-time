"""Azure DevOps Server base classes for collectors."""

import urllib.parse
from datetime import datetime
from abc import ABC

from dateutil.parser import parse

from base_collectors import SourceCollector
from collector_utilities.exceptions import CollectorException
from collector_utilities.functions import match_string_or_regular_expression
from collector_utilities.type import URL, Job
from model import Entities, Entity, SourceResponses


class AzureDevopsRepositoryBase(SourceCollector, ABC):
    """Base class for Azure DevOps collectors that work with repositories."""

    async def _api_url(self) -> URL:
        """Extend to add the repository."""
        api_url = str(await super()._api_url())
        return URL(f"{api_url}/_apis/git/repositories/{await self.__repository_id()}")

    async def _landing_url(self, responses: SourceResponses) -> URL:
        """Extend to add the repository."""
        landing_url = str(await super()._landing_url(responses))
        repository = self._parameter("repository") or landing_url.rsplit("/", 1)[-1]
        return URL(f"{landing_url}/_git/{repository}")

    async def __repository_id(self) -> str:
        """Return the repository id belonging to the repository."""
        api_url = str(await super()._api_url())
        repository = self._parameter("repository") or urllib.parse.unquote(api_url.rsplit("/", 1)[-1])
        repositories_url = URL(f"{api_url}/_apis/git/repositories?api-version=4.1")
        repositories = (await (await super()._get_source_responses(repositories_url))[0].json())["value"]
        matching_repositories = [r for r in repositories if repository in (r["name"], r["id"])]
        if not matching_repositories:
            raise CollectorException(f"Repository '{repository}' not found")
        return str(matching_repositories[0]["id"])


class AzureDevopsJobs(SourceCollector):
    """Base class for job collectors."""

    async def _api_url(self) -> URL:
        """Extend to add the build definitions API path."""
        return URL(f"{await super()._api_url()}/_apis/build/definitions?includeLatestBuilds=true&api-version=4.1")

    async def _landing_url(self, responses: SourceResponses) -> URL:
        """Override to add the builds path."""
        return URL(f"{await super()._api_url()}/_build")

    async def _parse_entities(self, responses: SourceResponses) -> Entities:
        """Override to parse the jobs."""
        entities = Entities()
        for job in (await responses[0].json())["value"]:
            if not self._include_job(job):
                continue
            name = self.__job_name(job)
            url = job["_links"]["web"]["href"]
            build_status = self._latest_build_result(job)
            build_date_time = self._latest_build_date_time(job)
            entities.append(
                Entity(key=name, name=name, url=url, build_date=str(build_date_time.date()), build_status=build_status)
            )
        return entities

    def _include_job(self, job: Job) -> bool:
        """Return whether this job should be included."""
        if not job.get("latestCompletedBuild", {}).get("result"):
            return False  # The job has no completed builds
        jobs_to_include = self._parameter("jobs_to_include")
        if len(jobs_to_include) > 0 and not match_string_or_regular_expression(job["name"], jobs_to_include):
            return False
        return not match_string_or_regular_expression(self.__job_name(job), self._parameter("jobs_to_ignore"))

    @staticmethod
    def _latest_build_result(job: Job) -> str:
        """Return the result of the latest build."""
        return str(job["latestCompletedBuild"]["result"])

    @staticmethod
    def _latest_build_date_time(job: Job) -> datetime:
        """Return the finish time of the latest build of the job."""
        return parse(job["latestCompletedBuild"]["finishTime"])

    @staticmethod
    def __job_name(job: Job) -> str:
        """Return the job name."""
        return "/".join(job["path"].strip(r"\\").split(r"\\") + [job["name"]]).strip("/")


class AzureDevopsPipelines(SourceCollector):
    """Base class for pipeline collectors."""

    async def _api_url(self, pipeline_id: int = None) -> URL:
        """Extend to add the pipelines API path."""
        pipeline_id_runs = f"/{pipeline_id}/runs" if pipeline_id else ""
        # currently the pipelines api is not available in any version which is not a -preview version
        return URL(f"{await super()._api_url()}/_apis/pipelines{pipeline_id_runs}?api-version=6.0-preview.1")

    async def _active_pipeline_ids(self) -> list[int]:
        """Find all active pipeline ids to traverse."""
        api_pipelines_url = await self._api_url()
        pipelines = (await (await super()._get_source_responses(api_pipelines_url))[0].json())["value"]
        return [pipeline['id'] for pipeline in pipelines if 'id' in pipeline and self._include_pipeline(pipeline)]

    async def _parse_entities(self, responses: SourceResponses) -> Entities:  # skipcq: PYL-W0613
        """Override to parse the pipelines."""
        entities = Entities()

        for pipeline_id in await self._active_pipeline_ids():
            api_pipelines_url = await self._api_url(pipeline_id)

            for pipeline_run in (await (await super()._get_source_responses(api_pipelines_url))[0].json())["value"]:
                if not self._include_pipeline_run(pipeline_run):
                    continue

                entities.append(
                    Entity(
                        key="-".join([str(pipeline_id), pipeline_run["name"]]),
                        name=pipeline_run["name"],
                        url=pipeline_run["_links"]["web"]["href"],
                        build_date=str(parse(pipeline_run["finishedDate"]).date()),
                        build_status=pipeline_run["state"]
                    )
                )
        return entities

    def _include_pipeline(self, job: Job) -> bool:
        """Return whether this pipeline should be included."""
        jobs_to_include = self._parameter("jobs_to_include")
        if len(jobs_to_include) > 0 and not match_string_or_regular_expression(job["name"], jobs_to_include):
            return False
        return not match_string_or_regular_expression(job["name"], self._parameter("jobs_to_ignore"))

    def _include_pipeline_run(self, job: Job) -> bool:  # skipcq: PYL-R0201
        """Return whether this pipeline run should be included."""
        return bool(job.get("finishedDate"))
