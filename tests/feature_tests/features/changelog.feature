Feature: changelog
  Get a changelog with recent changes

  Background:
    Given a logged-in client
    When the client waits a second
    And the client changes the reports_overview title to "Reports"
    And the client waits a second
    And the client changes the reports_overview title to "Reports overview"
    And the client waits a second

  Scenario: create a report
    When the client creates a report
    Then the changelog reads
      """
      Jane Doe created a new report.
      Jane Doe changed the title of the reports overview from 'Reports' to 'Reports overview'.
      """
    And the report changelog reads
      """
      Jane Doe created a new report.
      """

  Scenario: create a report and a subject
    When the client creates a report
    And the client waits a second
    And the client creates a subject
    Then the changelog reads
      """
      Jane Doe created a new subject in report 'New report'.
      Jane Doe created a new report.
      Jane Doe changed the title of the reports overview from 'Reports' to 'Reports overview'.
      """
    And the report changelog reads
      """
      Jane Doe created a new subject in report 'New report'.
      Jane Doe created a new report.
      """
    And the subject changelog reads
      """
      Jane Doe created a new subject in report 'New report'.
      """

  Scenario: create a report, a subject, and a metric
    When the client creates a report
    And the client waits a second
    And the client creates a subject
    And the client waits a second
    And the client creates a metric
    Then the changelog reads
      """
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      Jane Doe created a new subject in report 'New report'.
      Jane Doe created a new report.
      Jane Doe changed the title of the reports overview from 'Reports' to 'Reports overview'.
      """
    And the report changelog reads
      """
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      Jane Doe created a new subject in report 'New report'.
      Jane Doe created a new report.
      """
    And the subject changelog reads
      """
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      Jane Doe created a new subject in report 'New report'.
      """
    And the metric changelog reads
      """
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      """

  Scenario: create a report, a subject, a metric, and a source
    When the client creates a report
    And the client waits a second
    And the client creates a subject
    And the client waits a second
    And the client creates a metric
    And the client waits a second
    And the client creates a source
    Then the changelog reads
      """
      Jane Doe added a new source to metric 'Accessibility violations' of subject 'Software' in report 'New report'.
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      Jane Doe created a new subject in report 'New report'.
      Jane Doe created a new report.
      Jane Doe changed the title of the reports overview from 'Reports' to 'Reports overview'.
      """
    And the report changelog reads
      """
      Jane Doe added a new source to metric 'Accessibility violations' of subject 'Software' in report 'New report'.
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      Jane Doe created a new subject in report 'New report'.
      Jane Doe created a new report.
      """
    And the subject changelog reads
      """
      Jane Doe added a new source to metric 'Accessibility violations' of subject 'Software' in report 'New report'.
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      Jane Doe created a new subject in report 'New report'.
      """
    And the metric changelog reads
      """
      Jane Doe added a new source to metric 'Accessibility violations' of subject 'Software' in report 'New report'.
      Jane Doe added a new metric to subject 'Software' in report 'New report'.
      """
    And the source changelog reads
      """
      Jane Doe added a new source to metric 'Accessibility violations' of subject 'Software' in report 'New report'.
      """
