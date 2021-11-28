"""Data model metrics."""

from .meta.metric import Addition, Direction, Metrics, Tag, Unit


METRICS = Metrics.parse_obj(
    dict(
        accessibility=dict(
            name="Accessibility violations",
            description="The number of accessibility violations in the web user interface of the software.",
            unit=Unit.VIOLATIONS,
            default_source="axecsv",
            sources=["axecsv", "axe_core", "axe_html_reporter", "manual_number"],
            tags=[Tag.ACCESSIBILITY],
        ),
        commented_out_code=dict(
            name="Commented out code",
            description="The number of blocks of commented out lines of code.",
            unit=Unit.BLOCKS,
            near_target="100",
            sources=["manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
        complex_units=dict(
            name="Complex units",
            description="The amount of units (classes, functions, methods, files) that are too complex.",
            scales=["count", "percentage"],
            unit=Unit.COMPLEX_UNITS,
            sources=["manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY, Tag.TESTABILITY],
        ),
        dependencies=dict(
            name="Dependencies",
            description="The amount of (outdated) dependencies.",
            scales=["count", "percentage"],
            unit=Unit.DEPENDENCIES,
            default_source="npm",
            sources=["composer", "manual_number", "npm", "owasp_dependency_check", "pip"],
            tags=[Tag.MAINTAINABILITY],
        ),
        duplicated_lines=dict(
            name="Duplicated lines",
            description="The amount of lines that are duplicated.",
            scales=["count", "percentage"],
            unit=Unit.LINES,
            sources=["manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
        failed_jobs=dict(
            name="Failed CI-jobs",
            description="The number of continuous integration jobs or pipelines that have failed.",
            unit=Unit.CI_JOBS,
            near_target="5",
            default_source="jenkins",
            sources=["azure_devops", "jenkins", "gitlab", "manual_number"],
            tags=[Tag.CI],
        ),
        issues=dict(
            name="Issues",
            description="The number of issues.",
            unit=Unit.ISSUES,
            default_source="jira",
            sources=["azure_devops", "jira", "manual_number", "trello"],
        ),
        loc=dict(
            name="Size (LOC)",
            description="The size of the software in lines of code.",
            unit=Unit.LINES,
            target="30000",
            near_target="35000",
            default_source="sonarqube",
            sources=["cloc", "manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
        long_units=dict(
            name="Long units",
            description="The amount of units (functions, methods, files) that are too long.",
            unit=Unit.LONG_UNITS,
            scales=["count", "percentage"],
            sources=["manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
        manual_test_duration=dict(
            name="Manual test duration",
            description="The duration of the manual test in minutes.",
            unit=Unit.MINUTES,
            near_target="60",
            sources=["jira", "manual_number"],
            tags=[Tag.TEST_QUALITY],
        ),
        manual_test_execution=dict(
            name="Manual test execution",
            description="Measure the number of manual test cases that have not been tested on time.",
            unit=Unit.MANUAL_TEST_CASES,
            near_target="5",
            sources=["jira", "manual_number"],
            tags=[Tag.TEST_QUALITY],
        ),
        many_parameters=dict(
            name="Many parameters",
            description="The amount of units (functions, methods, procedures) that have too many parameters.",
            scales=["count", "percentage"],
            unit=Unit.UNITS_WITH_TOO_MANY_PARAMETERS,
            sources=["manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
        merge_requests=dict(
            name="Merge requests",
            description="The amount of merge requests.",
            scales=["count", "percentage"],
            unit=Unit.MERGE_REQUESTS,
            default_source="gitlab",
            sources=["azure_devops", "gitlab", "manual_number"],
            tags=[Tag.CI],
        ),
        metrics=dict(
            name="Metrics",
            description="The amount of metrics from one or more quality reports, with specific states and/or tags.",
            scales=["count", "percentage"],
            unit=Unit.METRICS,
            near_target="5",
            sources=["manual_number", "quality_time"],
        ),
        missing_metrics=dict(
            name="Missing metrics",
            description="Count the number of metrics that can be added to each report, but have not been added yet.",
            scales=["count", "percentage"],
            unit=Unit.MISSING_METRICS,
            near_target="5",
            sources=["manual_number", "quality_time"],
        ),
        performancetest_duration=dict(
            name="Performancetest duration",
            description="The duration of the performancetest in minutes.",
            unit=Unit.MINUTES,
            addition=Addition.MIN,
            direction=Direction.MORE_IS_BETTER,
            target="30",
            near_target="25",
            sources=["manual_number", "performancetest_runner"],
            tags=[Tag.PERFORMANCE],
        ),
        performancetest_stability=dict(
            name="Performancetest stability",
            description="The duration of the performancetest at which throughput or error count increases.",
            scales=["percentage"],
            unit=Unit.MINUTES,
            addition=Addition.MIN,
            direction=Direction.MORE_IS_BETTER,
            target="100",
            near_target="90",
            sources=["manual_number", "performancetest_runner"],
            tags=[Tag.PERFORMANCE],
        ),
        remediation_effort=dict(
            name="Violation remediation effort",
            description="The amount of effort it takes to remediate violations.",
            unit=Unit.MINUTES,
            target="60",
            near_target="600",
            sources=["manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
        scalability=dict(
            name="Scalability",
            description="The percentage of (max) users at which ramp-up of throughput breaks.",
            scales=["percentage"],
            unit=Unit.USERS,
            addition=Addition.MIN,
            direction=Direction.MORE_IS_BETTER,
            target="75",
            near_target="50",
            sources=["manual_number", "performancetest_runner"],
            tags=[Tag.PERFORMANCE],
        ),
        slow_transactions=dict(
            name="Slow transactions",
            description="The number of transactions slower than their performance threshold.",
            unit=Unit.TRANSACTIONS,
            near_target="5",
            default_source="jmeter_json",
            sources=["manual_number", "jmeter_json", "performancetest_runner"],
            tags=[Tag.PERFORMANCE],
        ),
        source_up_to_dateness=dict(
            name="Source up-to-dateness",
            description="The number of days since the source was last updated.",
            unit=Unit.DAYS,
            addition=Addition.MAX,
            target="3",
            near_target="7",
            default_source="sonarqube",
            sources=[
                "anchore",
                "anchore_jenkins_plugin",
                "axe_core",
                "azure_devops",
                "bandit",
                "calendar",
                "cobertura",
                "cobertura_jenkins_plugin",
                "cxsast",
                "gitlab",
                "jacoco",
                "jacoco_jenkins_plugin",
                "jenkins",
                "jenkins_test_report",
                "junit",
                "ncover",
                "robot_framework",
                "openvas",
                "owasp_dependency_check",
                "owasp_zap",
                "performancetest_runner",
                "quality_time",
                "robot_framework_jenkins_plugin",
                "sonarqube",
                "testng",
                "trello",
            ],
            tags=[Tag.CI],
        ),
        source_version=dict(
            name="Source version",
            description="The version number of the source.",
            scales=["version_number"],
            addition=Addition.MIN,
            direction=Direction.MORE_IS_BETTER,
            target="1.0",
            near_target="0.9",
            default_source="owasp_dependency_check",
            sources=[
                "axe_core",
                "cloc",
                "cobertura",
                "cxsast",
                "gitlab",
                "jenkins",
                "jira",
                "openvas",
                "owasp_dependency_check",
                "owasp_zap",
                "quality_time",
                "robot_framework",
                "sonarqube",
            ],
            tags=[Tag.CI],
        ),
        security_warnings=dict(
            name="Security warnings",
            description="The number of security warnings about the software.",
            unit=Unit.SECURITY_WARNINGS,
            near_target="5",
            default_source="owasp_dependency_check",
            sources=[
                "anchore",
                "anchore_jenkins_plugin",
                "bandit",
                "cxsast",
                "manual_number",
                "openvas",
                "owasp_dependency_check",
                "owasp_zap",
                "pyupio_safety",
                "snyk",
                "generic_json",
                "sonarqube",
            ],
            tags=[Tag.SECURITY],
        ),
        sentiment=dict(
            name="Sentiment",
            description="How are the team members feeling?",
            unit=Unit.NONE,
            addition=Addition.MIN,
            direction=Direction.MORE_IS_BETTER,
            target="10",
            near_target="8",
            sources=["manual_number"],
        ),
        suppressed_violations=dict(
            name="Suppressed violations",
            description="The amount of violations suppressed in the source.",
            scales=["count", "percentage"],
            unit=Unit.SUPPRESSED_VIOLATIONS,
            sources=["manual_number", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
        test_cases=dict(
            name="Test cases",
            description="The amount of test cases.",
            scales=["count", "percentage"],
            unit=Unit.TEST_CASES,
            direction=Direction.MORE_IS_BETTER,
            near_target="0",
            default_source="jira",
            sources=["jenkins_test_report", "jira", "junit", "manual_number", "robot_framework", "testng"],
            tags=[Tag.TEST_QUALITY],
        ),
        tests=dict(
            name="Tests",
            description="The amount of tests.",
            scales=["count", "percentage"],
            unit=Unit.TESTS,
            direction=Direction.MORE_IS_BETTER,
            near_target="0",
            default_source="jenkins_test_report",
            sources=[
                "azure_devops",
                "jenkins_test_report",
                "junit",
                "manual_number",
                "performancetest_runner",
                "robot_framework",
                "robot_framework_jenkins_plugin",
                "sonarqube",
                "testng",
            ],
            tags=[Tag.TEST_QUALITY],
        ),
        uncovered_branches=dict(
            name="Test branch coverage",
            description="The amount of code branches not covered by tests.",
            scales=["count", "percentage"],
            unit=Unit.UNCOVERED_BRANCHES,
            near_target="100",
            default_source="sonarqube",
            sources=[
                "cobertura",
                "cobertura_jenkins_plugin",
                "jacoco",
                "jacoco_jenkins_plugin",
                "manual_number",
                "ncover",
                "sonarqube",
            ],
            tags=[Tag.TEST_QUALITY],
        ),
        uncovered_lines=dict(
            name="Test line coverage",
            description="The amount of lines of code not covered by tests.",
            scales=["count", "percentage"],
            unit=Unit.UNCOVERED_LINES,
            near_target="100",
            default_source="sonarqube",
            sources=[
                "cobertura",
                "cobertura_jenkins_plugin",
                "jacoco",
                "jacoco_jenkins_plugin",
                "manual_number",
                "ncover",
                "sonarqube",
            ],
            tags=[Tag.TEST_QUALITY],
        ),
        unmerged_branches=dict(
            name="Unmerged branches",
            description="The number of branches that have not been merged to the default branch.",
            unit=Unit.BRANCHES,
            near_target="5",
            default_source="gitlab",
            sources=["azure_devops", "gitlab", "manual_number"],
            tags=[Tag.CI],
        ),
        unused_jobs=dict(
            name="Unused CI-jobs",
            description="The number of continuous integration jobs that are unused.",
            unit=Unit.CI_JOBS,
            near_target="5",
            default_source="jenkins",
            sources=["azure_devops", "gitlab", "jenkins", "manual_number"],
            tags=[Tag.CI],
        ),
        user_story_points=dict(
            name="User story points",
            description="The total number of points of a selection of user stories.",
            unit=Unit.USER_STORY_POINTS,
            direction=Direction.MORE_IS_BETTER,
            target="100",
            near_target="75",
            default_source="azure_devops",
            sources=["azure_devops", "jira", "manual_number"],
            tags=[Tag.PROCESS_EFFICIENCY],
        ),
        velocity=dict(
            name="Velocity",
            description="The average number of user story points delivered in recent sprints.",
            unit=Unit.USER_STORY_POINTS_PER_SPRINT,
            direction=Direction.MORE_IS_BETTER,
            target="20",
            near_target="15",
            sources=["jira", "manual_number"],
            tags=[Tag.PROCESS_EFFICIENCY],
        ),
        violations=dict(
            name="Violations",
            description="The number of violations of programming rules in the software.",
            unit=Unit.VIOLATIONS,
            default_source="sonarqube",
            sources=["manual_number", "ojaudit", "sonarqube"],
            tags=[Tag.MAINTAINABILITY],
        ),
    )
)
