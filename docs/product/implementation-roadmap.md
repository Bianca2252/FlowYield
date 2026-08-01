# FlowYield Implementation Roadmap

## 1. Purpose

This roadmap defines the implementation order for the FlowYield MVP.

The goals are to:

- reduce rework;
- keep development incremental;
- validate every major capability;
- preserve architectural boundaries;
- produce clear Git history;
- create demonstrable milestones;
- avoid building optional features before the core workflow works.

The roadmap is organized into phases.

Each phase includes:

- objective;
- implementation scope;
- difficulty;
- concrete result;
- verification;
- suggested commit message.

---

## 2. Development Principles

The project will follow these rules:

1. Build the smallest stable foundation first.
2. Do not implement dashboard features before reliable workflow data exists.
3. Do not implement optional attachments before the workflow is stable.
4. Keep routes thin.
5. Put business logic in services.
6. Use migrations from the beginning.
7. Add tests after each important module.
8. Do not continue over unresolved errors.
9. Commit only stable, understandable changes.
10. Keep documentation synchronized with implementation.

---

# Phase 0 — Environment and Repository Setup

## Objective

Prepare a clean local development environment and repository.

## Scope

- Python installation;
- virtual environment;
- Git;
- VS Code;
- `.gitignore`;
- `.editorconfig`;
- initial documentation;
- main branch setup.

## Difficulty

Low

## Result

A clean repository with an isolated Python environment and documented product direction.

## Verification

- virtual environment activates;
- Python and pip come from `.venv`;
- Git status is clean;
- `.venv` is ignored;
- documentation files exist.

## Suggested Commit

```text
chore: initialize repository configuration
```

## Status

Completed.

---

# Phase 1 — Application Skeleton

## Objective

Create the Flask application foundation without business features.

## Scope

- install initial dependencies;
- create `pyproject.toml` or requirements files;
- create `app/`;
- create application factory;
- create `extensions.py`;
- create environment-based configuration;
- create `run.py`;
- register a minimal main Blueprint;
- add basic error handlers;
- verify the application starts.

## Difficulty

Low to Medium

## Result

A Flask application that starts successfully using the application factory pattern.

## Verification

- application starts locally;
- development configuration loads;
- a basic route returns a valid response;
- no secrets are hardcoded;
- import structure has no circular dependency;
- initial smoke test passes.

## Suggested Commit

```text
feat: initialize Flask application structure
```

---

# Phase 2 — Testing Foundation

## Objective

Create the testing infrastructure before business logic grows.

## Scope

- install pytest;
- create testing configuration;
- create `tests/conftest.py`;
- create application fixture;
- create client fixture;
- create isolated test database strategy;
- add smoke tests;
- add coverage configuration.

## Difficulty

Medium

## Result

A repeatable test suite capable of creating isolated Flask application instances.

## Verification

- `pytest` runs successfully;
- tests do not use development data;
- tests are repeatable;
- application fixture starts correctly;
- coverage command works.

## Suggested Commit

```text
test: add application testing foundation
```

---

# Phase 3 — Database and Migration Foundation

## Objective

Connect SQLAlchemy and migrations before creating domain models.

## Scope

- configure SQLAlchemy;
- configure Flask-Migrate;
- configure SQLite development database;
- configure temporary test database;
- initialize migrations;
- add timestamp and enum conventions;
- verify first migration lifecycle.

## Difficulty

Medium

## Result

The application can create and migrate a database consistently.

## Verification

- migration repository exists;
- upgrade creates the schema;
- downgrade works for the test migration;
- development and testing databases are separate;
- database files are ignored by Git.

## Suggested Commit

```text
feat: configure database and migrations
```

---

# Phase 4 — Identity and Organization Models

## Objective

Implement the organizational foundation required by authentication and workflow assignment.

## Scope

- `User`;
- `Role`;
- `UserRole`;
- `Department`;
- manager relationship;
- model constraints;
- password helper methods;
- role helper methods;
- migrations;
- model tests.

## Difficulty

Medium

## Result

Users can belong to departments, report to managers, and hold multiple roles.

## Verification

- unique email constraint works;
- user cannot be their own manager;
- duplicate role assignments fail;
- password hashes are not plain text;
- inactive state is stored;
- relationships load correctly;
- tests pass.

## Suggested Commit

```text
feat: add identity and organization models
```

---

# Phase 5 — Authentication

## Objective

Implement secure session-based authentication.

## Scope

- Flask-Login configuration;
- login form;
- login route;
- logout route;
- inactive-user prevention;
- password verification;
- current-user loading;
- safe redirect handling;
- authentication audit events;
- route tests.

## Difficulty

Medium

## Result

Active users can log in and out, while inactive and invalid users are blocked.

## Verification

- valid login works;
- invalid credentials fail safely;
- inactive users cannot log in;
- protected routes require authentication;
- logout invalidates access;
- passwords are never logged;
- tests pass.

## Suggested Commit

```text
feat: implement user authentication
```

---

# Phase 6 — Authorization Foundation

## Objective

Centralize role, permission, and object-level checks.

## Scope

- role constants;
- permission constants where useful;
- route decorators;
- `has_role`;
- `can_view_request`;
- `can_edit_request`;
- workflow authorization interfaces;
- 401 and 403 behavior;
- authorization tests.

## Difficulty

Medium to High

## Result

Authorization rules are reusable and not duplicated across routes.

## Verification

- unauthorized pages return correct responses;
- hidden navigation is not the only protection;
- inactive users remain blocked;
- tests cover role and object-level denial;
- no sensitive route uses only a template check.

## Suggested Commit

```text
feat: add centralized authorization policies
```

---

# Phase 7 — User Administration

## Objective

Allow Administrators to manage application users and organizational assignments.

## Scope

- user list;
- user creation;
- user editing;
- activation and deactivation;
- role assignment;
- department assignment;
- manager assignment;
- validation;
- audit events;
- permission tests.

## Difficulty

Medium

## Result

Administrators can create and manage realistic demo users securely.

## Verification

- non-Administrators receive 403;
- duplicate email is rejected;
- self-role assignment is blocked;
- invalid manager assignments are rejected;
- role and status changes are audited;
- historical references remain intact;
- tests pass.

## Suggested Commit

```text
feat: add user administration
```

---

# Phase 8 — Purchase Request Models

## Objective

Implement request data and revision history.

## Scope

- `PurchaseRequest`;
- `RequestRevision`;
- `RequestComment`;
- request and category enums;
- constraints;
- reference-number generation;
- relationships;
- migrations;
- model tests.

## Difficulty

Medium to High

## Result

The application can store current request data and immutable submitted revisions.

## Verification

- reference numbers are unique;
- submitted amount must be positive;
- revision numbers are unique per request;
- comments are immutable through normal flows;
- relationships load correctly;
- tests pass.

## Suggested Commit

```text
feat: add purchase request domain models
```

---

# Phase 9 — Draft Request Management

## Objective

Allow Requesters to create and manage drafts.

## Scope

- request creation form;
- draft save;
- own-request list;
- draft editing;
- draft cancellation;
- ownership checks;
- validation;
- request history foundation;
- route and permission tests.

## Difficulty

Medium

## Result

A Requester can create, save, edit, view, and cancel their own draft.

## Verification

- another user cannot view or edit the draft;
- cancelled drafts cannot be submitted;
- draft saves do not create workflow cycles;
- fields validate correctly;
- empty states work;
- tests pass.

## Suggested Commit

```text
feat: implement purchase request drafts
```

---

# Phase 10 — Workflow Configuration Models

## Objective

Store versioned thresholds, SLA settings, and default assignments.

## Scope

- `WorkflowConfiguration`;
- `StepConfiguration`;
- active configuration rules;
- threshold validation;
- default assignee configuration;
- initial seed configuration;
- migrations;
- tests.

## Difficulty

High

## Result

New requests can reference a stable, versioned workflow configuration.

## Verification

- threshold ordering is validated;
- SLA values are positive;
- configuration versions remain historical;
- one active configuration is enforced by the service;
- default assignees are eligible;
- tests pass.

## Suggested Commit

```text
feat: add versioned workflow configuration
```

---

# Phase 11 — Workflow Execution Models

## Objective

Store approval cycles, steps, and authoritative decisions.

## Scope

- `WorkflowCycle`;
- `WorkflowStep`;
- `ApprovalDecision`;
- status enums;
- sequence constraints;
- one-decision-per-step constraint;
- relationships;
- migrations;
- model tests.

## Difficulty

High

## Result

The database can represent multiple approval cycles and preserve every decision.

## Verification

- cycle numbers are unique per request;
- step sequence is unique per cycle;
- one decision exists per step;
- previous cycles remain immutable;
- one active step is enforced by services;
- tests pass.

## Suggested Commit

```text
feat: add workflow execution models
```

---

# Phase 12 — Approval Path Rule Service

## Objective

Generate the correct workflow path from amount, category, and configuration.

## Scope

- deterministic rule service;
- low-value path;
- medium-value path;
- high-value path;
- conditional IT Review;
- boundary behavior;
- rule explanations;
- unit tests.

## Difficulty

High

## Result

The application can generate an ordered approval path without route-level hardcoding.

## Verification

Tests cover:

- below EUR 1,000;
- exactly EUR 1,000;
- exactly EUR 5,000;
- IT category above EUR 5,000;
- exactly EUR 10,000;
- above EUR 10,000;
- high-value IT request.

## Suggested Commit

```text
feat: implement approval path rules
```

---

# Phase 13 — Approver Assignment Service

## Objective

Assign eligible users to generated workflow steps.

## Scope

- manager assignment;
- default IT reviewer;
- default Finance approver;
- default Director approver;
- active-user validation;
- required-role validation;
- self-approval prevention;
- controlled assignment errors;
- unit and integration tests.

## Difficulty

High

## Result

Every required step receives an eligible approver before workflow activation.

## Verification

- missing manager blocks submission;
- inactive approver is rejected;
- wrong-role assignee is rejected;
- requester is not assigned to approve own request;
- no partial workflow remains after failure;
- tests pass.

## Suggested Commit

```text
feat: implement approver assignment
```

---

# Phase 14 — Request Submission and Workflow Initialization

## Objective

Convert a valid draft into an active workflow transactionally.

## Scope

- submission service;
- request validation;
- revision creation;
- rule evaluation;
- workflow cycle creation;
- workflow step creation;
- first-step activation;
- request status update;
- deadline creation;
- audit events;
- rollback behavior;
- integration tests.

## Difficulty

High

## Result

A valid draft becomes an `IN_REVIEW` request with the correct active approval path.

## Verification

- submission is atomic;
- first step is active;
- later steps are pending;
- request revision is immutable;
- configuration version is stored;
- audit events exist;
- failed submission leaves request editable;
- tests pass.

## Suggested Commit

```text
feat: initialize workflows on request submission
```

---

# Phase 15 — SLA Service

## Objective

Calculate deadlines and SLA status consistently.

## Scope

- activation deadline;
- on-time status;
- approaching-deadline status;
- overdue status;
- completion result;
- overdue duration;
- time helper for tests;
- unit tests.

## Difficulty

Medium to High

## Result

Every active and completed step has a correct SLA interpretation.

## Verification

- pending steps have no active clock;
- 75% boundary works;
- exact deadline behavior is defined;
- completed-on-time and completed-late work;
- tests use controlled timestamps;
- tests pass.

## Suggested Commit

```text
feat: implement SLA calculations
```

---

# Phase 16 — Approval Decision Service

## Objective

Implement approve, reject, and return-for-changes transitions.

## Scope

- active-step authorization;
- approve;
- reject;
- return for changes;
- activate next step;
- complete request;
- cancel future steps;
- required comments;
- duplicate-action prevention;
- out-of-order prevention;
- transactions;
- audit events;
- integration tests.

## Difficulty

Very High

## Result

Authorized approvers can progress or terminate workflows safely.

## Verification

- only assigned approver can act;
- requester cannot self-approve;
- only active step accepts decisions;
- next step activates once;
- final approval completes request;
- rejection cancels future steps;
- return pauses workflow;
- duplicate submissions do not corrupt state;
- rollback works;
- tests pass.

## Suggested Commit

```text
feat: implement approval workflow transitions
```

---

# Phase 17 — Approver Task Queue and Request Timeline

## Objective

Expose workflow execution through a professional interface.

## Scope

- assigned task queue;
- request detail page;
- workflow timeline;
- decision forms;
- status badges;
- SLA badges;
- completed-task history;
- permission-aware controls;
- empty states.

## Difficulty

Medium

## Result

Approvers can clearly see and act on assigned work.

## Verification

- task queue shows only assigned work;
- request details are protected;
- decision controls match permissions;
- SLA status is visible;
- history is ordered;
- server-side checks remain authoritative;
- route tests pass.

## Suggested Commit

```text
feat: add approval task interface
```

---

# Phase 18 — Return, Edit, and Resubmission

## Objective

Support correction cycles without overwriting history.

## Scope

- returned-request editing;
- requester response;
- revision increment;
- new workflow cycle;
- path recalculation;
- previous-cycle supersession;
- new SLA deadlines;
- revision timeline;
- tests.

## Difficulty

Very High

## Result

A returned request can be corrected and restarted from Manager Approval while preserving previous history.

## Verification

- only owner can edit;
- previous decision history is immutable;
- new amount can change path;
- new category can add IT Review;
- cycle number increments;
- Manager Approval restarts;
- new deadlines are created;
- tests pass.

## Suggested Commit

```text
feat: support request revision and resubmission
```

---

# Phase 19 — Structured Audit Logging

## Objective

Provide credible, append-only audit records.

## Scope

- `AuditLog` model;
- audit service;
- login events;
- user administration events;
- request events;
- workflow events;
- unauthorized-attempt events where appropriate;
- audit list;
- basic filtering;
- tests.

## Difficulty

High

## Result

Important business and security actions are traceable through structured records.

## Verification

- audit events contain structured fields;
- sensitive data is excluded;
- records are read-only;
- scope-based audit access works;
- transactional events remain consistent;
- tests pass.

## Suggested Commit

```text
feat: add structured audit logging
```

---

# Phase 20 — Core Analytics

## Objective

Calculate operational KPIs from real workflow data.

## Scope

- status counts;
- active and overdue counts;
- approval and rejection rates;
- average duration;
- median duration;
- SLA compliance;
- average duration by step;
- monthly volume;
- volume by category;
- volume by department;
- bottleneck calculation;
- unit and query tests.

## Difficulty

High

## Result

FlowYield can explain process performance using database-derived metrics.

## Verification

- empty datasets return safe values;
- median is correct;
- active requests are excluded where required;
- cancelled steps are excluded from SLA compliance;
- known seed data produces expected metrics;
- tests pass.

## Suggested Commit

```text
feat: implement workflow analytics
```

---

# Phase 21 — Dashboard Interface

## Objective

Present analytics clearly in a professional B2B dashboard.

## Scope

- metric cards;
- status distribution;
- monthly trend;
- category distribution;
- average duration by step;
- SLA summary;
- bottleneck panel;
- Chart.js;
- accessible supporting text;
- responsive layout.

## Difficulty

Medium

## Result

A reviewer can understand workflow performance quickly.

## Verification

- charts use real analytics data;
- dashboard works with empty data;
- page remains understandable without charts;
- role access is enforced;
- labels and units are clear;
- route tests pass.

## Suggested Commit

```text
feat: add operational analytics dashboard
```

---

# Phase 22 — ROI Assumptions and Service

## Objective

Implement the documented ROI methodology.

## Scope

- `ROIAssumption` model;
- versioning;
- active assumption set;
- decimal calculations;
- time saved;
- cost saved;
- interventions eliminated;
- annualized savings;
- ROI percentage;
- payback period;
- limitations;
- unit tests.

## Difficulty

High

## Result

FlowYield produces transparent, testable ROI estimates.

## Verification

- formulas match documentation;
- measured and estimated values are separated;
- zero and negative cases work;
- division by zero is prevented;
- monetary calculations use Decimal;
- tests pass.

## Suggested Commit

```text
feat: implement ROI calculation service
```

---

# Phase 23 — ROI Dashboard

## Objective

Present ROI assumptions and results responsibly.

## Scope

- ROI summary cards;
- assumptions panel;
- measured vs estimated labels;
- reporting period;
- limitations section;
- Process Manager configuration form;
- Executive Viewer access;
- route tests.

## Difficulty

Medium

## Result

The project's business differentiator is visible and explainable.

## Verification

- outputs are labeled as estimates;
- active assumptions are visible;
- invalid inputs are rejected;
- non-authorized users are denied;
- zero-savings states display correctly;
- tests pass.

## Suggested Commit

```text
feat: add ROI analytics dashboard
```

---

# Phase 24 — Selected REST API

## Objective

Demonstrate appropriate API design without duplicating the whole application.

## Scope

- `/api/v1/requests/<id>/status`;
- `/api/v1/approval-tasks`;
- `/api/v1/dashboard`;
- JSON serializers;
- JSON error format;
- authentication;
- object-level authorization;
- API tests.

## Difficulty

Medium to High

## Result

Selected application capabilities are exposed through secure JSON endpoints.

## Verification

- 401, 403, and 404 are correct;
- sensitive fields are excluded;
- assignment filtering works;
- metrics match server-rendered views;
- invalid parameters return structured errors;
- tests pass.

## Suggested Commit

```text
feat: add authenticated REST API endpoints
```

---

# Phase 25 — Seed Data and Demo Scenario

## Objective

Create realistic, repeatable data for demonstration.

## Scope

- Aurevia Solutions departments;
- all roles;
- demo users;
- manager relationships;
- workflow configuration;
- ROI assumptions;
- requests in every status;
- multiple approval paths;
- returns and resubmissions;
- SLA breaches;
- predictable analytics;
- CLI seed command.

## Difficulty

Medium to High

## Result

The application looks complete immediately after seeding.

## Verification

- seed command is repeatable;
- no real personal data exists;
- every dashboard section has data;
- all major workflows can be demonstrated;
- self-approval scenarios have eligible alternatives;
- expected KPI values are documented.

## Suggested Commit

```text
feat: add realistic demo seed data
```

---

# Phase 26 — Security Hardening

## Objective

Review and strengthen security before deployment.

## Scope

- CSRF verification;
- cookie configuration;
- safe redirects;
- object-level authorization review;
- mass-assignment prevention;
- error-message review;
- secret handling;
- inactive-user checks;
- unsafe logging review;
- file-upload design if attachments are included;
- security tests.

## Difficulty

High

## Result

Critical application paths are protected consistently.

## Verification

- no sensitive action trusts the frontend;
- secrets are not committed;
- production errors hide internals;
- unauthorized object access fails;
- session settings are environment-specific;
- security tests pass.

## Suggested Commit

```text
security: harden application access controls
```

---

# Phase 27 — Error Pages and UX Polish

## Objective

Make the application consistent and interview-ready.

## Scope

- 403 page;
- 404 page;
- 500 page;
- flash messages;
- loading and empty states;
- consistent forms;
- navigation;
- status badges;
- accessibility basics;
- responsive review.

## Difficulty

Medium

## Result

The application feels like one coherent B2B product.

## Verification

- common error flows are understandable;
- navigation changes by permission;
- forms show clear validation;
- status colors also have text labels;
- layout works on common viewport sizes.

## Suggested Commit

```text
feat: polish application interface and errors
```

---

# Phase 28 — Linting, Formatting, and CI

## Objective

Automate code-quality checks.

## Scope

- Ruff configuration;
- formatting command;
- lint command;
- test command;
- GitHub Actions;
- coverage output;
- CI documentation.

## Difficulty

Medium

## Result

Every push and pull request receives automated quality feedback.

## Verification

- local lint passes;
- local tests pass;
- CI passes in a clean environment;
- no local-only dependency exists;
- CI uses the supported Python version.

## Suggested Commit

```text
ci: add automated quality and test checks
```

---

# Phase 29 — Production Configuration and Deployment

## Objective

Publish a stable demonstration environment.

## Scope

- ProductionConfig;
- PostgreSQL support if required;
- WSGI server;
- production environment variables;
- migration execution;
- secure cookies;
- production logging;
- hosting platform;
- demo reset strategy;
- deployment documentation.

## Difficulty

High

## Result

FlowYield is accessible through a public demo URL.

## Verification

- debug mode is disabled;
- secret key is external;
- production database migrates successfully;
- demo accounts work;
- logs are available;
- test suite passes before deployment;
- deployment instructions are documented.

## Suggested Commit

```text
chore: prepare production deployment
```

---

# Phase 30 — Final Documentation and Portfolio Packaging

## Objective

Prepare FlowYield for recruiters and interviews.

## Scope

- professional README;
- architecture summary;
- ER diagram;
- setup instructions;
- demo accounts;
- screenshots;
- GIF or video;
- API documentation;
- test instructions;
- security considerations;
- limitations;
- roadmap;
- ROI methodology;
- CV description;
- LinkedIn description;
- 30-second pitch;
- 2-minute pitch;
- demo script;
- interview questions.

## Difficulty

Medium

## Result

The repository communicates technical and business value without requiring the reviewer to inspect every file.

## Verification

- setup instructions are tested from a clean environment;
- screenshots reflect current UI;
- demo script works;
- limitations are honest;
- README links to detailed documentation;
- repository is clean;
- public demo is reachable if deployed.

## Suggested Commit

```text
docs: complete portfolio documentation
```

---

# 3. Optional Post-MVP Phases

These phases must not delay the core MVP.

## Attachments

Possible commit:

```text
feat: add secure request attachments
```

## Notifications

Possible commit:

```text
feat: add in-app workflow notifications
```

## Additional Workflow

Possible commit:

```text
feat: add employee access request workflow
```

## Docker

Possible commit:

```text
chore: add Docker development setup
```

Docker should be added only after the local application is stable.

---

# 4. Recommended Milestones

## Milestone 1 — Foundation

Includes:

- application skeleton;
- testing foundation;
- database configuration;
- identity models;
- authentication;
- authorization.

Completion result:

A secure Flask foundation with users and roles.

---

## Milestone 2 — Request Management

Includes:

- purchase request models;
- draft management;
- workflow configuration;
- workflow execution models.

Completion result:

Requests can be created and stored with workflow-ready data.

---

## Milestone 3 — Workflow Engine

Includes:

- rule service;
- approver assignment;
- workflow initialization;
- SLA;
- approval decisions;
- resubmission.

Completion result:

The full purchase approval lifecycle works correctly.

---

## Milestone 4 — Visibility and Audit

Includes:

- approver queue;
- request timeline;
- audit logging;
- structured history.

Completion result:

Users can understand and verify every workflow action.

---

## Milestone 5 — Business Analytics

Includes:

- operational analytics;
- dashboard;
- ROI service;
- ROI dashboard.

Completion result:

FlowYield demonstrates measurable business value.

---

## Milestone 6 — Portfolio Release

Includes:

- API;
- seed data;
- security hardening;
- UX polish;
- CI;
- deployment;
- final documentation.

Completion result:

A recruiter-ready public portfolio project.

---

# 5. Branch Strategy

For early setup and small changes, working directly on `main` is acceptable.

Once implementation begins, use focused feature branches for meaningful modules.

Examples:

```text
feature/application-foundation
feature/authentication
feature/purchase-requests
feature/workflow-engine
feature/analytics
feature/roi-dashboard
```

Recommended workflow:

```text
main
-> create feature branch
-> implement a small coherent change
-> run tests
-> review diff
-> merge into main
```

Pull requests may be used even when working alone to document decisions and practice professional workflow.

---

# 6. Commit Strategy

Commits should be:

- small;
- coherent;
- descriptive;
- stable;
- written in English.

Common prefixes:

```text
feat:
fix:
test:
docs:
refactor:
chore:
security:
ci:
```

Avoid commits such as:

```text
stuff
changes
works now
final final
update
```

---

# 7. Test Gates

Development must stop and resolve failures at these points:

- application skeleton does not start;
- migration fails;
- authentication test fails;
- authorization test fails;
- workflow path test fails;
- transaction test fails;
- duplicate decision test fails;
- self-approval test fails;
- analytics test disagrees with known seed data;
- ROI formula test fails;
- CI fails.

No later phase should hide or bypass a broken earlier phase.

---

# 8. MVP Completion Criteria

The MVP is complete when:

- a Requester creates and submits a request;
- the correct approval path is generated;
- every approver acts only on an assigned active step;
- self-approval is blocked;
- duplicate and out-of-order decisions are blocked;
- rejection and return-for-changes work;
- resubmission preserves history;
- SLA results are correct;
- audit history is structured;
- dashboards use real data;
- ROI formulas match documentation;
- critical tests pass;
- CI passes;
- demo seed data is available;
- production configuration exists;
- documentation is complete.

---

# 9. Immediate Next Step

The planning phase is complete enough to begin implementation.

The first implementation phase is:

```text
Phase 1 — Application Skeleton
```

The next work session should:

1. confirm the virtual environment is active;
2. define the initial dependency list;
3. install only the required foundation dependencies;
4. create the Flask application factory;
5. create configuration classes;
6. initialize extensions;
7. register a minimal Blueprint;
8. run the application;
9. add a smoke test;
10. commit the stable foundation.
