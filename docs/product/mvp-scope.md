# FlowYield MVP Scope

## 1. MVP Objective

The FlowYield MVP must demonstrate one complete and realistic business workflow from request creation to final resolution.

The MVP focuses on the **Purchase Request Approval** process and must prove that the application can:

- collect structured business requests;
- calculate the correct approval path;
- enforce role-based permissions;
- manage workflow state transitions;
- track step-level SLA performance;
- record auditable actions;
- calculate operational KPIs;
- estimate automation ROI;
- support realistic demonstration scenarios.

The MVP is not intended to provide every capability of a commercial workflow platform.

Its purpose is to demonstrate strong software engineering, business process modeling, security, analytics, and product thinking within a scope that can realistically be completed by one developer.

---

## 2. Core Demonstration Scenario

The primary demonstration scenario is:

**Purchase Request Approval at Aurevia Solutions**

An employee creates a purchase request containing:

- title;
- description;
- business justification;
- category;
- supplier;
- requested amount;
- currency;
- expected purchase date;
- department;
- optional supporting attachment.

The approval path is determined by configurable business rules.

### Default approval rules

#### Requests below EUR 1,000

Required steps:

1. Manager Approval

#### Requests between EUR 1,000 and EUR 10,000

Required steps:

1. Manager Approval
2. Finance Approval

#### Requests above EUR 10,000

Required steps:

1. Manager Approval
2. Finance Approval
3. Director Approval

#### Additional IT rule

Requests in the following categories:

- Software;
- IT Services;

with a value above EUR 5,000 require:

1. Manager Approval
2. IT Review
3. Finance Approval

If the request value is above EUR 10,000, Director Approval is also required after Finance Approval.

---

## 3. MVP User Roles

The MVP will use the following roles.

### Administrator

Responsible for application access and organizational setup.

Permissions:

- create users;
- activate and deactivate users;
- assign roles;
- assign departments;
- assign managers;
- view users;
- view audit records;
- access administrative settings.

The Administrator does not automatically receive permission to approve business requests unless explicitly assigned an approval role.

### Requester

Responsible for creating and following purchase requests.

Permissions:

- create purchase requests;
- save drafts;
- edit own drafts;
- submit requests;
- view own requests;
- view own request history;
- respond to return-for-changes decisions;
- resubmit corrected requests;
- add comments;
- upload permitted supporting files.

### Manager Approver

Responsible for evaluating requests submitted by direct reports.

Permissions:

- view assigned Manager Approval tasks;
- approve;
- reject;
- return a request for changes;
- add a decision comment;
- view relevant request history.

### Finance Approver

Responsible for financial review.

Permissions:

- view assigned Finance Approval tasks;
- approve;
- reject;
- return a request for changes;
- add a decision comment;
- view relevant request history.

### IT Reviewer

Responsible for technical review of qualifying requests.

Permissions:

- view assigned IT Review tasks;
- approve;
- reject;
- return a request for changes;
- add a decision comment;
- view relevant request history.

### Director Approver

Responsible for high-value approvals.

Permissions:

- view assigned Director Approval tasks;
- approve;
- reject;
- return a request for changes;
- add a decision comment;
- view relevant request history.

### Process Manager

Responsible for controlled workflow configuration and operational monitoring.

Permissions:

- configure monetary thresholds;
- configure SLA durations;
- configure responsible roles;
- activate or deactivate selected workflow parameters;
- view process performance;
- view all requests;
- view dashboard analytics;
- view audit records related to workflow execution.

### Auditor / Executive Viewer

Read-only role.

Permissions:

- view completed and active requests;
- view workflow history;
- view SLA performance;
- view audit records;
- view dashboards;
- view ROI analytics.

The exact permission implementation will be refined during RBAC design.

---

## 4. MVP Functional Scope

## 4.1 Authentication

Included:

- administrator-created user accounts;
- login using email and password;
- logout;
- password hashing;
- protected routes;
- session-based authentication;
- inactive-user access prevention;
- current-user tracking.

Not included:

- public registration;
- social login;
- single sign-on;
- multi-factor authentication;
- automated password reset email;
- enterprise directory integration.

A future version may add password reset and MFA.

---

## 4.2 User and Organization Management

Included:

- user creation by Administrator;
- user activation and deactivation;
- role assignment;
- department assignment;
- manager assignment;
- basic user listing;
- basic user editing;
- prevention of duplicate email addresses.

Included organizational entities:

- Aurevia Solutions;
- departments;
- users;
- manager-report relationships.

Not included:

- multiple organizations;
- advanced organizational charts;
- employee synchronization;
- bulk CSV import;
- HR system integration.

---

## 4.3 Purchase Request Management

Included:

- create request;
- save as draft;
- edit own draft;
- validate required fields;
- submit request;
- view request details;
- view current status;
- view approval history;
- view current pending step;
- add comments;
- return for changes;
- edit returned request;
- resubmit returned request;
- cancel draft request;
- list own requests;
- filter requests by status.

Possible request statuses:

- DRAFT;
- SUBMITTED;
- IN_REVIEW;
- CHANGES_REQUESTED;
- APPROVED;
- REJECTED;
- CANCELLED.

Not included:

- cloning requests;
- recurring requests;
- request delegation;
- bulk request creation;
- purchase order generation;
- supplier portal;
- procurement contract generation.

---

## 4.4 Approval Workflow

Included:

- automatic approval-path calculation;
- sequential approval steps;
- conditional IT Review;
- conditional Finance Approval;
- conditional Director Approval;
- assignment by responsible role;
- step activation;
- step completion;
- approve action;
- reject action;
- return-for-changes action;
- resubmission;
- prevention of duplicate decisions;
- prevention of out-of-order decisions;
- prevention of unauthorized decisions;
- final request completion;
- structured decision comments;
- timestamps for every workflow action.

Possible step statuses:

- PENDING;
- ACTIVE;
- APPROVED;
- REJECTED;
- CHANGES_REQUESTED;
- SKIPPED;
- CANCELLED.

Not included:

- parallel approvals;
- voting approvals;
- approval delegation;
- dynamic approver groups;
- ad hoc approval steps;
- drag-and-drop workflow editing;
- BPMN execution;
- arbitrary user-defined transitions.

Sequential approval is sufficient for the MVP.

---

## 4.5 Business Rules

Included:

- amount-based approval rules;
- category-based IT Review rule;
- configurable monetary thresholds;
- configurable category rule activation;
- deterministic approval-path calculation;
- rule evaluation before workflow execution;
- stored explanation of why each step was included;
- tests for every rule combination.

The business rules must not be implemented directly inside route functions.

The MVP will use a dedicated business rule service or workflow-building service.

Not included:

- a generic rule language;
- natural-language rule creation;
- complex nested expressions;
- external rule engines;
- AI-based decision-making.

---

## 4.6 Workflow Configuration

Included:

- edit low-value threshold;
- edit high-value threshold;
- edit IT Review threshold;
- configure SLA duration per step type;
- activate or deactivate the IT category rule;
- assign responsible roles;
- view current configuration;
- validate configuration changes;
- record configuration changes in the audit log.

Configuration must be controlled and limited.

Not included:

- visual workflow designer;
- arbitrary step creation;
- arbitrary transition creation;
- full workflow template editor;
- full workflow versioning interface.

The application architecture should leave room for future workflow versioning, but a complete workflow designer is outside the MVP.

---

## 4.7 SLA Management

Included:

- SLA duration per approval step;
- deadline calculation when a step becomes active;
- current SLA status;
- on-time status;
- approaching-deadline status;
- overdue status;
- overdue duration calculation;
- dashboard count of overdue requests;
- SLA compliance calculation for completed steps;
- step-level SLA history.

Initial SLA status values:

- ON_TIME;
- APPROACHING_DEADLINE;
- OVERDUE;
- COMPLETED_ON_TIME;
- COMPLETED_LATE.

The definition of “approaching deadline” will be documented separately.

Not included:

- email escalations;
- SMS notifications;
- scheduled background workers;
- automatic reassignment;
- business-calendar support;
- holiday-calendar support.

For the MVP, SLA status may be calculated when relevant pages or analytics are loaded.

---

## 4.8 Audit Logging

Included:

- successful login;
- failed login attempt where appropriate;
- user creation;
- user activation or deactivation;
- role change;
- request creation;
- draft update;
- request submission;
- approval;
- rejection;
- return for changes;
- resubmission;
- request status change;
- workflow step activation;
- workflow configuration change;
- unauthorized action attempt where appropriate.

Each audit record should contain structured fields such as:

- actor;
- action type;
- entity type;
- entity identifier;
- timestamp;
- request identifier;
- previous state;
- new state;
- relevant metadata.

Audit records should not be represented only as unstructured text.

Not included:

- external log shipping;
- SIEM integration;
- cryptographic log signing;
- immutable external storage.

---

## 4.9 Dashboard and Analytics

Included dashboard indicators:

- total requests;
- active requests;
- approved requests;
- rejected requests;
- changes-requested requests;
- overdue requests;
- approval rate;
- rejection rate;
- average process duration;
- median process duration;
- SLA compliance rate;
- average duration per approval step;
- monthly request volume;
- monthly approved value;
- request volume by category;
- request volume by department;
- slowest approval step;
- top bottleneck indicator.

Included visualizations:

- monthly request trend;
- status distribution;
- category distribution;
- average duration by step;
- SLA compliance summary.

Not included:

- predictive analytics;
- anomaly detection;
- process mining;
- custom report builder;
- user-defined dashboards;
- data warehouse integration.

---

## 4.10 ROI Analytics

Included inputs:

- estimated manual processing time per request;
- estimated digital processing time per request;
- average employee hourly cost;
- number of processed requests;
- estimated manual interventions before automation;
- estimated manual interventions after automation;
- estimated implementation cost.

Included outputs:

- hours saved;
- processing-time reduction percentage;
- estimated cost saved;
- estimated saving per request;
- monthly estimated savings;
- annualized estimated savings;
- estimated ROI percentage;
- estimated payback period.

The ROI methodology must:

- document every formula;
- document every assumption;
- separate measured values from estimated values;
- explain its limitations;
- avoid presenting estimates as guaranteed financial results.

Not included:

- accounting-system integration;
- verified financial reporting;
- complex cost allocation;
- tax calculations;
- predictive ROI models.

---

## 4.11 Attachments

Included only if core workflow functionality is stable:

- one or more supporting attachments;
- allowed extension validation;
- maximum file-size validation;
- secure generated filenames;
- storage outside public static paths;
- authorization checks before download.

Initial permitted formats may include:

- PDF;
- PNG;
- JPG;
- DOCX.

Attachments are a **secondary MVP feature**.

If they threaten the completion timeline, they may be moved to the first post-MVP release without compromising the core portfolio value.

---

## 4.12 REST API

Included:

- authenticated JSON endpoint for request status;
- authenticated JSON endpoint for dashboard data;
- authenticated JSON endpoint for approval tasks;
- validation and structured error responses;
- correct HTTP methods and status codes.

The primary application interface will remain server-rendered using Flask, Jinja2, Bootstrap, and JavaScript.

Not included:

- full API-first architecture;
- public developer API;
- OAuth;
- API keys;
- third-party integrations;
- complete CRUD exposure for every entity.

The API exists to demonstrate appropriate REST design, not to duplicate the entire application.

---

## 5. User Interface Scope

Included:

- login page;
- main navigation;
- requester dashboard;
- approver task queue;
- request list;
- request creation and editing form;
- request details page;
- approval history;
- approval decision form;
- administration pages;
- process configuration page;
- analytics dashboard;
- ROI dashboard;
- audit log view;
- status badges;
- SLA indicators;
- success and error messages;
- empty states;
- responsive basic layout;
- 403 page;
- 404 page;
- 500 page;
- basic accessibility.

Not included:

- custom design system;
- advanced animations;
- native mobile interface;
- complex drag-and-drop components;
- pixel-perfect commercial branding;
- extensive theme customization.

The interface should look professional and consistent, but backend correctness has priority.

---

## 6. Technical Scope

The MVP will use:

- Python;
- Flask;
- Flask application factory;
- Flask Blueprints;
- SQLAlchemy;
- Flask-Migrate or Alembic;
- SQLite for local development;
- Jinja2;
- Bootstrap;
- JavaScript;
- Chart.js;
- pytest;
- Git;
- GitHub;
- GitHub Actions;
- environment variables;
- structured logging.

Likely supporting libraries:

- Flask-Login;
- Flask-WTF;
- WTForms;
- Werkzeug password hashing;
- python-dotenv;
- Ruff;
- coverage.py.

Additional dependencies will only be introduced when a concrete requirement justifies them.

---

## 7. Explicitly Excluded Technical Complexity

The MVP will not use:

- React;
- Vue;
- Angular;
- microservices;
- Kubernetes;
- Redis;
- Celery;
- RabbitMQ;
- Kafka;
- GraphQL;
- NoSQL databases;
- event sourcing;
- distributed systems;
- serverless architecture;
- machine learning;
- large language models.

These technologies would not provide enough portfolio value to justify the added implementation and maintenance complexity for this project.

---

## 8. Testing Scope

The MVP must include automated tests for:

- authentication;
- inactive-user access;
- role permissions;
- object-level authorization;
- request validation;
- request submission;
- approval-path calculation;
- low-value requests;
- medium-value requests;
- high-value requests;
- IT Review rule;
- approve transitions;
- reject transitions;
- return-for-changes transitions;
- resubmission;
- duplicate action prevention;
- out-of-order action prevention;
- unauthorized approval prevention;
- SLA calculations;
- audit record creation;
- dashboard KPI calculations;
- ROI calculations;
- API authentication;
- API validation;
- API response codes.

The critical workflow logic must not rely only on manual browser testing.

---

## 9. Security Scope

The MVP must implement:

- password hashing;
- CSRF protection;
- server-side validation;
- output escaping;
- route protection;
- role checks;
- object-level authorization;
- secure environment variables;
- safe error handling;
- secure session configuration;
- duplicate action protection;
- mass-assignment prevention;
- secure attachment validation if attachments are included;
- no secrets committed to Git;
- no real personal data in seed data.

A separate security document will explain the threats and mitigations.

---

## 10. MVP Priority Levels

### Priority P0 — Required for MVP completion

- project architecture;
- application configuration;
- database and migrations;
- authentication;
- RBAC;
- users and departments;
- purchase request drafts;
- request submission;
- workflow-path calculation;
- sequential approvals;
- approve, reject, and return-for-changes;
- resubmission;
- authorization enforcement;
- duplicate action prevention;
- audit logging;
- SLA calculation;
- dashboard core KPIs;
- ROI calculations;
- critical automated tests;
- seed data;
- README;
- local setup documentation;
- deployment-ready configuration.

### Priority P1 — Strongly desired

- workflow threshold configuration;
- step-level analytics;
- bottleneck indicators;
- selected REST API endpoints;
- charts;
- advanced filtering;
- auditor role;
- GitHub Actions;
- PostgreSQL production support;
- public demo deployment.

### Priority P2 — Optional for MVP

- attachments;
- extensive audit filtering;
- advanced ROI configuration UI;
- additional workflow templates;
- richer executive dashboards;
- Docker;
- demo GIF or video.

P2 features may be implemented after the core MVP is stable.

---

## 11. MVP Definition of Done

The FlowYield MVP is complete only when all of the following conditions are met:

### Functional

- a Requester can create, save, edit, submit, and track a request;
- the approval path is calculated correctly;
- authorized approvers can complete their assigned steps;
- unauthorized users cannot approve requests;
- reject and return-for-changes paths work correctly;
- returned requests can be edited and resubmitted;
- completed requests reach a valid final state;
- duplicate actions are prevented;
- workflow history is visible;
- SLA status is calculated;
- dashboard indicators use real database data;
- ROI calculations follow documented formulas.

### Technical

- application factory is implemented;
- Blueprints separate major modules;
- business logic is separated from routes;
- database migrations are used;
- environment-based configuration exists;
- errors are handled safely;
- automated tests cover critical paths;
- test suite passes;
- code is formatted and linted;
- repository contains no secrets;
- CI runs tests automatically.

### Documentation

- README is complete;
- product brief exists;
- MVP scope exists;
- architecture is documented;
- database design is documented;
- ER diagram exists;
- API behavior is documented;
- ROI methodology is documented;
- security decisions are documented;
- local setup instructions are verified;
- known limitations are listed.

### Portfolio

- realistic seed data is available;
- demo accounts exist;
- screenshots are included;
- a clear demo scenario is documented;
- the project can be explained in technical and business terms;
- the repository looks complete and intentional.

---

## 12. MVP Success Statement

The MVP succeeds if it demonstrates that FlowYield can take a purchase request from draft to final approval or rejection through a secure, rule-driven, auditable, measurable workflow.

A complete and well-tested workflow is more valuable than multiple incomplete workflows.