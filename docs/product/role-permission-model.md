
# FlowYield Role and Permission Model

## 1. Purpose

This document defines the authorization model for the FlowYield MVP.

The goal is to ensure that every user can access only the data and actions required by their responsibilities.

The model must support:

- role-based access control;
- object-level authorization;
- workflow-step authorization;
- separation of administrative and business permissions;
- read-only audit access;
- prevention of unauthorized approvals;
- prevention of access to unrelated requests;
- clear and testable permission rules.

FlowYield must not rely only on hiding buttons in the user interface.

Every sensitive action must also be verified on the server.

---

## 2. Authorization Principles

### 2.1 Deny by Default

A user must not receive access unless a rule explicitly allows it.

If no permission rule matches, the action must be denied.

### 2.2 Server-Side Enforcement

Permission checks must be enforced in backend code.

The interface may hide unavailable actions, but this is only a usability feature.

A user must not be able to bypass authorization by:

- manually changing a URL;
- submitting a custom HTTP request;
- modifying form data;
- calling an API endpoint directly;
- changing a request identifier;
- replaying an earlier request.

### 2.3 Role and Context Are Both Required

A role alone is not always sufficient.

For example, a user with the `MANAGER_APPROVER` role must not automatically approve every request in the organization.

The user must also be:

- the assigned approver;
- the manager of the requester;
- or otherwise explicitly authorized for the active workflow step.

Authorization therefore depends on:

- the user's role;
- the requested action;
- the resource being accessed;
- the relationship between the user and the resource;
- the current workflow state.

### 2.4 Least Privilege

Each role receives only the permissions necessary for its responsibilities.

Administrative access must not automatically grant business approval authority.

Approval authority must not automatically grant user-management authority.

### 2.5 Separation of Duties

Where practical, FlowYield should separate:

- user administration;
- workflow configuration;
- business approval;
- auditing;
- executive reporting.

This reduces the risk that one user can create, approve, and audit the same action without independent oversight.

### 2.6 Read and Write Permissions Are Separate

The ability to view a resource does not automatically allow modification.

For example:

- an Auditor may view all requests but cannot approve them;
- a Process Manager may view workflow performance but cannot act as a Director unless separately authorized;
- an Administrator may manage user accounts but cannot approve purchase requests unless assigned an approval role.

---

## 3. Role Strategy

The MVP uses named business roles rather than a fully generic permission-management interface.

The initial roles are:

- `ADMINISTRATOR`;
- `REQUESTER`;
- `MANAGER_APPROVER`;
- `FINANCE_APPROVER`;
- `IT_REVIEWER`;
- `DIRECTOR_APPROVER`;
- `PROCESS_MANAGER`;
- `AUDITOR`;
- `EXECUTIVE_VIEWER`.

A user may hold more than one role.

Examples:

- a Finance employee may be both `REQUESTER` and `FINANCE_APPROVER`;
- a Process Manager may also be an `EXECUTIVE_VIEWER`;
- an Administrator may also receive `REQUESTER` access;
- a Director may be both `DIRECTOR_APPROVER` and `EXECUTIVE_VIEWER`.

Roles must not be mutually exclusive unless a future business rule requires it.

---

## 4. Role Definitions

## 4.1 Administrator

### Purpose

The Administrator manages application access and organizational setup.

### Allowed Actions

The Administrator may:

- create user accounts;
- view the user list;
- edit basic user information;
- activate users;
- deactivate users;
- assign roles;
- remove roles;
- assign departments;
- assign managers;
- view department configuration;
- view administrative audit events;
- view system-level configuration required for administration.

### Restricted Actions

The Administrator may not automatically:

- approve purchase requests;
- reject purchase requests;
- return purchase requests for changes;
- modify business rules;
- change workflow thresholds;
- act as a Process Manager;
- edit requests owned by another user.

These actions require additional roles.

### Important Constraint

An Administrator must not be able to bypass approval authorization merely because they manage user accounts.

---

## 4.2 Requester

### Purpose

The Requester creates and tracks purchase requests.

### Allowed Actions

A Requester may:

- create a purchase request;
- save a request as draft;
- view their own draft requests;
- edit their own draft requests;
- cancel their own draft requests;
- submit their own requests;
- view their own submitted requests;
- view the status of their own requests;
- view workflow history for their own requests;
- add comments to their own requests;
- edit a request returned for changes;
- resubmit a request returned for changes;
- download attachments associated with their own requests.

### Restricted Actions

A Requester may not:

- view requests belonging to unrelated users;
- edit another user's request;
- change a request after final submission unless it was returned for changes;
- directly change request status;
- approve their own request;
- reject their own request;
- bypass required workflow steps;
- change approval rules;
- change SLA configuration;
- access administrative pages.

### Ownership Rule

A user owns a request when:

```text
request.requester_id == current_user.id
```

Ownership alone does not allow every action.

The current request status must also permit the action.

---

## 4.3 Manager Approver

### Purpose

The Manager Approver evaluates requests submitted by employees for whom they are responsible.

### Allowed Actions

A Manager Approver may:

* view assigned Manager Approval tasks;
* view the complete request information required for a decision;
* view relevant request history;
* approve an active Manager Approval step;
* reject an active Manager Approval step;
* return an active Manager Approval step for changes;
* add a decision comment;
* view previously completed Manager Approval decisions assigned to them.

### Restricted Actions

A Manager Approver may not:

* approve requests not assigned to them;
* approve requests outside their reporting responsibility;
* approve an inactive workflow step;
* approve a completed workflow step;
* approve the same step twice;
* approve a request they created;
* skip Finance, IT, or Director steps;
* change the approval path manually;
* modify workflow configuration.

### Assignment Rule

For the MVP, Manager Approval should normally be assigned to the requester's configured manager.

The authorization condition should verify both:

* the active step is a Manager Approval step;
* the current user is the assigned approver.

A role check alone is not sufficient.

---

## 4.4 Finance Approver

### Purpose

The Finance Approver evaluates budget, financial justification, and financial compliance.

### Allowed Actions

A Finance Approver may:

* view assigned Finance Approval tasks;
* view the financial and business information required for a decision;
* view relevant workflow history;
* approve an active Finance Approval step;
* reject an active Finance Approval step;
* return an active Finance Approval step for changes;
* add a decision comment;
* view previously completed Finance Approval decisions assigned to them.

### Restricted Actions

A Finance Approver may not:

* approve a request before the Finance step becomes active;
* approve a request without assignment;
* approve the same step twice;
* approve a request they created;
* override an IT Review requirement;
* override a Director Approval requirement;
* edit the request amount;
* alter the approval path;
* modify threshold configuration unless they also hold `PROCESS_MANAGER`.

---

## 4.5 IT Reviewer

### Purpose

The IT Reviewer evaluates technical compatibility, security, architecture, licensing, and support implications for qualifying technology purchases.

### Allowed Actions

An IT Reviewer may:

* view assigned IT Review tasks;
* view relevant technical and business information;
* view workflow history;
* approve an active IT Review step;
* reject an active IT Review step;
* return an active IT Review step for changes;
* add a technical decision comment;
* view previously completed IT Review decisions assigned to them.

### Restricted Actions

An IT Reviewer may not:

* review requests that do not require IT Review unless explicitly assigned;
* approve a step before it becomes active;
* approve a completed step;
* approve a request they created;
* perform Finance Approval;
* perform Director Approval;
* edit monetary thresholds;
* edit the original request data.

---

## 4.6 Director Approver

### Purpose

The Director Approver evaluates high-value requests that exceed the configured executive approval threshold.

### Allowed Actions

A Director Approver may:

* view assigned Director Approval tasks;
* view the full request and approval history;
* approve an active Director Approval step;
* reject an active Director Approval step;
* return an active Director Approval step for changes;
* add an executive decision comment;
* view completed Director Approval decisions assigned to them.

### Restricted Actions

A Director Approver may not:

* approve a request before prior required steps are complete;
* approve an unassigned request;
* approve the same step twice;
* approve a request they created;
* bypass a rejected previous step;
* change workflow rules directly;
* edit request values.

---

## 4.7 Process Manager

### Purpose

The Process Manager controls selected workflow parameters and monitors process performance.

### Allowed Actions

A Process Manager may:

* view all purchase requests;
* view active and completed workflows;
* view step-level performance;
* view SLA performance;
* view dashboard analytics;
* view bottleneck indicators;
* view ROI analytics;
* view current workflow configuration;
* update configurable monetary thresholds;
* update SLA durations;
* activate or deactivate the IT Review rule;
* assign responsible approval roles;
* validate workflow configuration;
* activate approved configuration changes;
* view workflow-related audit events.

### Restricted Actions

A Process Manager may not automatically:

* create users;
* assign application roles;
* approve purchase requests;
* reject purchase requests;
* edit requester-owned business data;
* delete audit records;
* modify historical workflow instances;
* change the approval path of a request already in progress.

### Configuration Constraint

Configuration changes must apply only to new workflow instances unless a specific migration mechanism is designed.

Existing in-progress requests must preserve the rules used when they were submitted.

---

## 4.8 Auditor

### Purpose

The Auditor reviews compliance, historical actions, and process execution.

### Allowed Actions

An Auditor may:

* view all requests;
* view workflow histories;
* view approval decisions;
* view audit records;
* view SLA information;
* view configuration-change history;
* filter audit records;
* view dashboard and ROI information;
* export audit information if export is added later.

### Restricted Actions

An Auditor may not:

* create requests on behalf of another user;
* edit requests;
* approve requests;
* reject requests;
* return requests for changes;
* create users;
* change roles;
* modify workflow configuration;
* delete audit records.

### Audit Integrity Rule

Audit records must be read-only through the application interface.

---

## 4.9 Executive Viewer

### Purpose

The Executive Viewer accesses high-level process and business performance information.

### Allowed Actions

An Executive Viewer may:

* view organization-level dashboards;
* view aggregated KPIs;
* view ROI analytics;
* view bottleneck indicators;
* view high-level request summaries;
* view approved and rejected request statistics;
* view SLA compliance metrics.

### Restricted Actions

An Executive Viewer may not:

* approve requests unless they also hold an approver role;
* edit requests;
* change workflow settings;
* manage users;
* view sensitive administrative configuration;
* alter dashboard calculations;
* delete any data.

### Data-Minimization Rule

Where practical, executive views should focus on aggregated information rather than exposing unnecessary personal details.

---

## 5. Permission Categories

Permissions will be grouped conceptually by business capability.

The MVP does not require a fully generic permission editor, but the code should use centralized permission names or checks.

## 5.1 User Administration Permissions

Possible permission identifiers:

```text
users.view
users.create
users.edit
users.activate
users.deactivate
users.assign_roles
users.assign_department
users.assign_manager
```

Primary role:

```text
ADMINISTRATOR
```

---

## 5.2 Request Permissions

Possible permission identifiers:

```text
requests.create
requests.view_own
requests.view_all
requests.edit_own_draft
requests.edit_returned
requests.submit
requests.resubmit
requests.cancel_draft
requests.comment
```

Primary roles:

```text
REQUESTER
PROCESS_MANAGER
AUDITOR
```

The exact permission depends on ownership and request status.

---

## 5.3 Approval Permissions

Possible permission identifiers:

```text
approvals.view_assigned
approvals.manager_decide
approvals.finance_decide
approvals.it_decide
approvals.director_decide
approvals.return_for_changes
```

Primary roles:

```text
MANAGER_APPROVER
FINANCE_APPROVER
IT_REVIEWER
DIRECTOR_APPROVER
```

Every approval action also requires active-step assignment.

---

## 5.4 Workflow Configuration Permissions

Possible permission identifiers:

```text
workflow.view_configuration
workflow.update_thresholds
workflow.update_sla
workflow.toggle_it_rule
workflow.assign_responsible_roles
workflow.activate_configuration
```

Primary role:

```text
PROCESS_MANAGER
```

---

## 5.5 Audit Permissions

Possible permission identifiers:

```text
audit.view
audit.filter
audit.view_security_events
audit.view_configuration_changes
```

Primary roles:

```text
AUDITOR
PROCESS_MANAGER
ADMINISTRATOR
```

Access may differ by audit-event category.

---

## 5.6 Analytics Permissions

Possible permission identifiers:

```text
analytics.view_operational
analytics.view_sla
analytics.view_roi
analytics.view_executive
```

Primary roles:

```text
PROCESS_MANAGER
AUDITOR
EXECUTIVE_VIEWER
```

---

## 6. Permission Matrix

| Capability                 |         Administrator |        Requester |          Manager |          Finance |      IT Reviewer |         Director | Process Manager |  Auditor | Executive Viewer |
| -------------------------- | --------------------: | ---------------: | ---------------: | ---------------: | ---------------: | ---------------: | --------------: | -------: | ---------------: |
| Create users               |                   Yes |               No |               No |               No |               No |               No |              No |       No |               No |
| Assign roles               |                   Yes |               No |               No |               No |               No |               No |              No |       No |               No |
| Create own request         |              Optional |              Yes |         Optional |         Optional |         Optional |         Optional |        Optional | Optional |         Optional |
| View own requests          |              Optional |              Yes |         Optional |         Optional |         Optional |         Optional |        Optional | Optional |         Optional |
| View all requests          |                    No |               No |               No |               No |               No |               No |             Yes |      Yes |     Summary only |
| Edit own draft             |              Optional |              Yes |         Optional |         Optional |         Optional |         Optional |        Optional | Optional |         Optional |
| Submit own request         |              Optional |              Yes |         Optional |         Optional |         Optional |         Optional |        Optional | Optional |         Optional |
| Manager decision           |                    No |               No |    Assigned only |               No |               No |               No |              No |       No |               No |
| Finance decision           |                    No |               No |               No |    Assigned only |               No |               No |              No |       No |               No |
| IT decision                |                    No |               No |               No |               No |    Assigned only |               No |              No |       No |               No |
| Director decision          |                    No |               No |               No |               No |               No |    Assigned only |              No |       No |               No |
| Configure thresholds       |                    No |               No |               No |               No |               No |               No |             Yes |       No |               No |
| Configure SLA              |                    No |               No |               No |               No |               No |               No |             Yes |       No |               No |
| View audit logs            | Administrative events | Own history only | Relevant history | Relevant history | Relevant history | Relevant history | Workflow events |      Yes |               No |
| View operational dashboard |               Limited |      Own summary | Assigned summary | Assigned summary | Assigned summary | Assigned summary |             Yes |      Yes |              Yes |
| View ROI dashboard         |                    No |               No |               No |         Optional |               No |         Optional |             Yes |      Yes |              Yes |
| Delete audit records       |                    No |               No |               No |               No |               No |               No |              No |       No |               No |

`Optional` means that the user may receive the capability through an additional role.

---

## 7. Object-Level Authorization Rules

Role-based access is not enough for FlowYield.

The following object-level rules must be enforced.

## 7.1 Viewing Requests

A user may view a request when at least one of the following is true:

* the user created the request;
* the user is assigned to an active or completed workflow step;
* the user has `PROCESS_MANAGER`;
* the user has `AUDITOR`;
* the user has an executive permission that allows the relevant level of detail;
* the user is otherwise explicitly authorized by a documented business rule.

A user must not gain access only by guessing a request ID.

---

## 7.2 Editing Requests

A user may edit a request only when:

* they are the requester;
* and the request status is `DRAFT`;

or:

* they are the requester;
* and the request status is `CHANGES_REQUESTED`;
* and the workflow currently permits correction.

Submitted requests must not be silently edited while approval is in progress.

---

## 7.3 Cancelling Requests

For the MVP, a Requester may cancel only their own draft request.

Cancellation of submitted or active requests is outside the initial MVP unless explicitly added later.

---

## 7.4 Approval Decisions

A user may decide a workflow step only when all conditions are true:

* the user is authenticated;
* the user account is active;
* the user holds the required role;
* the user is assigned to the step;
* the step status is `ACTIVE`;
* the step has not already been completed;
* the request is in a compatible status;
* all required previous steps are complete;
* the user is not the requester;
* the submitted action is valid for the current step;
* the decision has not already been processed.

If any condition fails, the action must be denied.

---

## 7.5 Viewing Audit Records

Audit access depends on scope.

* Requesters may view human-readable history for their own requests.
* Approvers may view history relevant to assigned requests.
* Process Managers may view workflow and configuration audit events.
* Administrators may view user-administration and security-related events.
* Auditors may view the full audit log.
* Executive Viewers do not require raw audit access.

---

## 8. Self-Approval Prevention

A user must not approve a purchase request that they created.

This rule applies even if the user holds an approval role.

Example:

* a Finance Approver submits their own purchase request;
* the Finance step must be assigned to another authorized Finance Approver.

If no alternative approver is available, the system must not silently allow self-approval.

The request should remain blocked or require administrative reassignment.

The MVP seed data must include enough users to avoid this scenario during normal demonstrations.

---

## 9. Duplicate Action Prevention

Approval actions must be idempotent from a business perspective.

The system must prevent:

* double approval;
* double rejection;
* approving after rejection;
* approving a previously completed step;
* resubmitting the same decision request;
* processing repeated browser submissions.

Possible implementation protections may include:

* checking current step state before every transition;
* database constraints where appropriate;
* transaction boundaries;
* optimistic locking or version checking if needed;
* rejecting invalid repeated transitions;
* disabling buttons after submission as a UI convenience.

Backend validation remains mandatory.

---

## 10. Out-of-Order Action Prevention

Workflow steps must be completed in the required sequence.

Example:

```text
Manager Approval
IT Review
Finance Approval
Director Approval
```

Finance Approval must not be possible while IT Review is still pending.

A later step may exist in the database but must remain inactive until all required prior steps are complete.

Only the active step may accept a decision.

---

## 11. Inactive User Rules

An inactive user:

* cannot log in;
* cannot create requests;
* cannot submit requests;
* cannot approve requests;
* cannot access protected pages;
* cannot call protected API endpoints.

If an inactive user is assigned to an active workflow step, the request must not silently advance.

The issue should be visible to an Administrator or Process Manager for reassignment.

Automated reassignment is outside the MVP.

---

## 12. Role Assignment Rules

Only an Administrator may assign or remove user roles.

Every role change must create an audit event containing:

* acting Administrator;
* affected user;
* previous roles;
* new roles;
* timestamp;
* optional reason.

A user must not assign roles to themselves unless explicitly permitted by a future policy.

For the MVP, self-assignment is prohibited.

---

## 13. Permission Enforcement Architecture

The exact code design will be finalized during architecture design.

The preferred approach is:

* authentication through Flask-Login;
* centralized role and permission helpers;
* decorators for route-level capability checks;
* service-layer checks for business actions;
* object-level authorization functions;
* workflow-step validation inside the approval service;
* no authorization logic embedded in templates;
* no reliance on frontend-only restrictions.

Possible helper concepts:

```text
has_role(user, role_name)
has_permission(user, permission_name)
can_view_request(user, request)
can_edit_request(user, request)
can_decide_step(user, step)
can_manage_workflow(user)
```

Templates may use permission helpers to hide unavailable controls, but the same rules must be enforced again in backend code.

---

## 14. HTTP Behavior for Authorization Failures

The application should use consistent responses.

### Unauthenticated Browser Request

Expected behavior:

* redirect to the login page;
* preserve the intended destination where safe.

### Authenticated but Unauthorized Browser Request

Expected behavior:

```text
403 Forbidden
```

The user should see a professional 403 page.

### Missing Resource

Expected behavior:

```text
404 Not Found
```

For sensitive resources, returning 404 instead of 403 may sometimes reduce information disclosure.

### Unauthenticated API Request

Expected behavior:

```text
401 Unauthorized
```

### Authenticated but Unauthorized API Request

Expected behavior:

```text
403 Forbidden
```

API errors should use structured JSON responses.

---

## 15. Audit Requirements for Sensitive Permission Events

The following events should be logged where appropriate:

* successful login;
* failed login;
* blocked inactive-user login;
* user creation;
* user activation;
* user deactivation;
* role assignment;
* role removal;
* unauthorized approval attempt;
* unauthorized object-access attempt;
* workflow configuration change;
* request approval;
* request rejection;
* return for changes;
* duplicate action attempt.

Audit logging must not store:

* plain-text passwords;
* session tokens;
* secret keys;
* unnecessary sensitive request data.

---

## 16. Permission Testing Requirements

Automated tests must verify at least the following scenarios.

### Requester Tests

* Requester can create a request.
* Requester can edit their own draft.
* Requester cannot edit another user's draft.
* Requester cannot edit an active request.
* Requester can view their own request.
* Requester cannot view an unrelated request.
* Requester cannot approve any step.
* Requester cannot approve their own request even with an approver role.

### Manager Tests

* Assigned Manager can view the request.
* Assigned Manager can approve an active Manager step.
* Unassigned Manager cannot approve the step.
* Manager cannot approve a completed step.
* Manager cannot approve before the step becomes active.

### Finance Tests

* Assigned Finance Approver can approve an active Finance step.
* Finance Approver cannot bypass IT Review.
* Unassigned Finance Approver cannot act.
* Finance Approver cannot edit the request amount.

### IT Tests

* IT Reviewer can act only on qualifying assigned requests.
* IT Reviewer cannot act before the IT step becomes active.
* IT Reviewer cannot perform Finance Approval.

### Director Tests

* Director can approve only an assigned active Director step.
* Director cannot approve before previous steps are complete.
* Director cannot modify workflow thresholds.

### Administrator Tests

* Administrator can create users.
* Administrator can assign roles.
* Administrator cannot approve requests without an approver role.
* Administrator cannot edit another user's request.

### Process Manager Tests

* Process Manager can update permitted configuration.
* Process Manager cannot alter historical workflow instances.
* Process Manager cannot approve without an approver role.
* Configuration changes create audit records.

### Auditor Tests

* Auditor can view audit records.
* Auditor cannot modify requests.
* Auditor cannot approve steps.
* Auditor cannot change workflow configuration.

### Inactive User Tests

* Inactive user cannot log in.
* Inactive user cannot call protected API endpoints.
* Inactive user cannot perform an approval action.

---

## 17. MVP Simplifications

To keep the authorization model realistic but achievable, the MVP will not include:

* custom permissions created through the interface;
* attribute-based access control engine;
* external identity providers;
* approval delegation;
* temporary role assignments;
* geographical restrictions;
* IP allowlists;
* multi-organization isolation;
* field-level encryption policies;
* legal-hold permissions;
* dynamic policy languages.

The MVP will use a well-structured role model combined with object-level and workflow-state checks.

---

## 18. Key Design Decision

FlowYield will not treat authorization as a single role comparison.

The final authorization decision will combine:

```text
Authentication
+ Active account
+ Role
+ Permission
+ Object relationship
+ Workflow assignment
+ Current state
```

This model is more realistic than simple role-only checks and demonstrates a strong understanding of application security and business-process authorization.

---

## 19. Definition of Done

The role and permission model is considered successfully implemented when:

* every protected route requires authentication;
* inactive users are blocked;
* administrative actions require administrative permission;
* workflow configuration requires Process Manager permission;
* request visibility follows ownership or assigned responsibility;
* approval decisions require role and step assignment;
* self-approval is blocked;
* duplicate decisions are blocked;
* out-of-order decisions are blocked;
* audit access is read-only;
* permission failures return correct HTTP responses;
* critical permission scenarios are covered by automated tests;
* no sensitive action relies only on frontend restrictions.
