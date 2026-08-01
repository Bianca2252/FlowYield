# FlowYield User Stories and Acceptance Criteria

## 1. Purpose

This document defines the user stories for the FlowYield MVP.

Each user story includes:

- role;
- objective;
- business value;
- priority;
- acceptance criteria;
- dependencies;
- release scope.

The stories are grouped by product capability and are written to support:

- implementation planning;
- test design;
- GitHub Issues;
- milestone planning;
- technical interviews;
- business analysis discussions.

Priority levels:

- **P0** — required for MVP completion;
- **P1** — strongly desired for the MVP;
- **P2** — optional or post-MVP.

Release scope:

- **MVP** — included in the first complete version;
- **Post-MVP** — intentionally deferred.

---

# 2. Authentication and Account Access

## US-AUTH-001 — Log in

**As an active user, I want to log in with my email address and password, so that I can access the features allowed by my roles.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The login form requires an email address and password.
2. Valid credentials for an active user create an authenticated session.
3. Invalid credentials do not create a session.
4. The application displays a generic error message for invalid credentials.
5. The error message does not reveal whether the email address exists.
6. Passwords are never stored or compared in plain text.
7. The user is redirected to an appropriate landing page after login.
8. The login event is recorded in the audit log.
9. CSRF protection is enabled for the form.

### Dependencies

- User model;
- password hashing;
- session management;
- audit logging.

---

## US-AUTH-002 — Block inactive users

**As an Administrator, I want inactive users to be prevented from logging in, so that former or suspended users cannot access company data.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. An inactive user cannot establish an authenticated session.
2. The user receives a generic access error.
3. The blocked login attempt is recorded where appropriate.
4. An already authenticated user who becomes inactive is denied access on the next protected request.
5. Inactive users cannot use protected API endpoints.

### Dependencies

- User activation status;
- authentication service;
- protected-route checks.

---

## US-AUTH-003 — Log out

**As an authenticated user, I want to log out, so that my session is closed when I finish using the application.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The logout action ends the current session.
2. Protected pages are no longer accessible after logout.
3. The user is redirected to the login page.
4. Reusing the browser Back button does not restore protected access.
5. The logout action uses an appropriate protected request method.

### Dependencies

- Authentication;
- session management.

---

## US-AUTH-004 — Reset password

**As a user who forgot my password, I want to reset it securely, so that I can regain access to my account.**

**Priority:** P2  
**Scope:** Post-MVP

### Acceptance Criteria

1. A reset request does not reveal whether an account exists.
2. Reset tokens expire.
3. Reset tokens can be used only once.
4. The new password is hashed.
5. Existing reset tokens become invalid after a successful reset.

### Dependencies

- Email delivery;
- token generation;
- password policy.

---

# 3. User and Organization Administration

## US-ADMIN-001 — Create a user

**As an Administrator, I want to create a user account, so that an employee can access FlowYield.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only an authorized Administrator can access the user-creation page.
2. The form requires name, email, department, manager where applicable, and at least one role.
3. Email addresses must be unique.
4. The email address is normalized before storage.
5. The initial password is hashed.
6. The account can be created as active or inactive.
7. The user-creation event is audited.
8. Invalid data does not create a partial user record.
9. A non-Administrator receives a 403 response.

### Dependencies

- User model;
- Role model;
- Department model;
- authorization;
- audit logging.

---

## US-ADMIN-002 — Assign roles

**As an Administrator, I want to assign one or more roles to a user, so that the user receives the correct application permissions.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only an Administrator can assign or remove roles.
2. A user may hold multiple roles.
3. Duplicate role assignments are prevented.
4. Self-assignment of roles is prohibited.
5. Previous and new roles are recorded in the audit event.
6. Removing a role does not remove historical workflow records.
7. Changes take effect on future authorization checks.

### Dependencies

- User-role relationship;
- authorization helpers;
- audit logging.

---

## US-ADMIN-003 — Assign a department

**As an Administrator, I want to assign a department to a user, so that requests and analytics can be associated with the correct business unit.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only an Administrator can change a user's department.
2. A user belongs to one department in the MVP.
3. The selected department must be active.
4. Department changes do not rewrite historical request ownership.
5. The change is audited.

### Dependencies

- Department model;
- User model;
- audit logging.

---

## US-ADMIN-004 — Assign a manager

**As an Administrator, I want to assign a manager to a user, so that Manager Approval steps can be routed correctly.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only an Administrator can assign or change a manager.
2. A user cannot be their own manager.
3. The manager must be active.
4. The manager must hold the required Manager Approver role.
5. Cyclic manager relationships are prevented where practical.
6. The change is audited.
7. Existing in-progress requests preserve their assigned approver.

### Dependencies

- User reporting relationship;
- role validation;
- audit logging.

---

## US-ADMIN-005 — Deactivate a user

**As an Administrator, I want to deactivate a user account, so that access can be removed without deleting historical records.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only an Administrator can deactivate a user.
2. A deactivated user cannot log in.
3. Historical requests and decisions remain visible.
4. The user record is not deleted.
5. The change is audited.
6. The application identifies active workflow steps assigned to the user.
7. The workflow does not silently skip those steps.

### Dependencies

- User activation status;
- workflow assignments;
- audit logging.

---

# 4. Purchase Request Drafts

## US-REQ-001 — Create a purchase request

**As a Requester, I want to create a purchase request, so that I can request approval for a company expense.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only an authenticated active user with Requester capability can create a request.
2. A new request is created with status `DRAFT`.
3. The requester is automatically set to the current user.
4. The department is captured from the current organizational assignment.
5. Required fields are validated.
6. The amount must be positive.
7. Only EUR is accepted for workflow calculation in the MVP.
8. The creation event is audited.
9. The Requester cannot change the stored requester identity.

### Dependencies

- Authentication;
- Requester authorization;
- PurchaseRequest model;
- Department relationship;
- validation;
- audit logging.

---

## US-REQ-002 — Save a draft

**As a Requester, I want to save an incomplete request as a draft, so that I can finish it later.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. A draft may be saved without meeting all submission requirements.
2. Minimum safe field validation still applies.
3. Only the request owner may save changes.
4. The request remains `DRAFT`.
5. The updated timestamp changes.
6. No workflow is created.
7. The update is audited without storing sensitive duplicate content unnecessarily.

### Dependencies

- PurchaseRequest model;
- ownership checks;
- validation.

---

## US-REQ-003 — Edit own draft

**As a Requester, I want to edit my own draft, so that I can correct or complete it before submission.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only the request owner can edit the draft.
2. The request must have status `DRAFT`.
3. Another user receives 403 or 404 according to the security policy.
4. Submitted, approved, rejected, or cancelled requests cannot be edited.
5. Changes are validated and audited.

### Dependencies

- Ownership authorization;
- request status validation;
- audit logging.

---

## US-REQ-004 — Cancel a draft

**As a Requester, I want to cancel my draft request, so that obsolete requests do not remain active.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only the owner can cancel the request.
2. Only a `DRAFT` request can be cancelled.
3. The request becomes `CANCELLED`.
4. Cancelled requests cannot be submitted.
5. No workflow instance is created.
6. The cancellation is audited.

### Dependencies

- Request state transitions;
- ownership authorization;
- audit logging.

---

# 5. Request Submission and Workflow Generation

## US-WF-001 — Submit a valid request

**As a Requester, I want to submit a complete request, so that the approval process can begin.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The Requester owns the request.
2. The request is `DRAFT` or validly `CHANGES_REQUESTED`.
3. All required fields are present and valid.
4. The current workflow configuration is loaded.
5. Required approvers are validated before activation.
6. The approval path is generated deterministically.
7. The first step becomes `ACTIVE`.
8. Later steps become `PENDING`.
9. The request becomes `IN_REVIEW`.
10. The first SLA deadline is calculated.
11. Workflow creation and rule evaluation are audited.
12. Submission is atomic.
13. If initialization fails, the request remains editable and no partial workflow remains.

### Dependencies

- Request validation;
- workflow configuration;
- business rule service;
- approver assignment;
- transactions;
- audit logging;
- SLA service.

---

## US-WF-002 — Generate a low-value path

**As the system, I want requests below EUR 1,000 to require only Manager Approval, so that low-value purchases use a proportionate process.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. An amount below EUR 1,000 produces one step.
2. The step type is `MANAGER_APPROVAL`.
3. The step is assigned to the requester's configured manager.
4. No Finance or Director step is created.
5. The rule explanation is stored.
6. Boundary cases are tested.

### Dependencies

- Business rule service;
- manager assignment.

---

## US-WF-003 — Generate a medium-value path

**As the system, I want requests from EUR 1,000 through EUR 10,000 to require Manager and Finance Approval, so that medium-value purchases receive financial review.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. EUR 1,000 is included in this rule.
2. EUR 10,000 is included in this rule.
3. The sequence is Manager, then Finance.
4. Only the first step is active after submission.
5. The rule explanation is stored.
6. Boundary cases are tested.

### Dependencies

- Business rule service;
- Finance approver assignment.

---

## US-WF-004 — Generate a high-value path

**As the system, I want requests above EUR 10,000 to require Manager, Finance, and Director Approval, so that high-value purchases receive executive oversight.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. An amount above EUR 10,000 triggers the rule.
2. Exactly EUR 10,000 does not trigger Director Approval.
3. The sequence is Manager, Finance, Director.
4. The Director step remains pending until Finance approves.
5. The rule explanation is stored.
6. Boundary cases are tested.

### Dependencies

- Business rule service;
- Director approver assignment.

---

## US-WF-005 — Insert IT Review

**As the system, I want qualifying Software and IT Services requests above EUR 5,000 to include IT Review, so that technical compatibility and risk are evaluated.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The rule applies only to configured IT categories.
2. The amount must be greater than EUR 5,000.
3. Exactly EUR 5,000 does not trigger IT Review.
4. IT Review is inserted after Manager Approval.
5. IT Review occurs before Finance Approval.
6. For high-value requests, Director Approval remains last.
7. The rule can be activated or deactivated by configuration.
8. The reason for inclusion is stored.
9. All rule combinations are tested.

### Dependencies

- Category model;
- workflow configuration;
- IT reviewer assignment;
- business rule service.

---

## US-WF-006 — Block submission when an approver is missing

**As a Requester, I want a clear error when the workflow cannot assign an approver, so that the request does not enter a broken process.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Submission validates every required approver.
2. An inactive approver is not eligible.
3. A requester cannot be assigned to approve their own request.
4. A missing manager blocks submission.
5. A missing role-based approver blocks submission.
6. The request remains editable.
7. No partial workflow is committed.
8. The user receives a clear, non-technical message.
9. The failure is logged appropriately.

### Dependencies

- Assignment service;
- transaction handling;
- validation errors.

---

# 6. Approval Tasks and Decisions

## US-APP-001 — View assigned tasks

**As an Approver, I want to view my assigned approval tasks, so that I know which requests require my action.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The queue contains active tasks assigned to the current user.
2. Tasks assigned to other users are not shown.
3. Completed tasks can be viewed separately.
4. The queue shows request title, requester, amount, category, step type, and deadline.
5. Overdue and approaching-deadline tasks are visibly identified.
6. The list can be filtered by status.
7. Opening a task still performs object-level authorization.

### Dependencies

- Step assignments;
- authorization;
- SLA calculation.

---

## US-APP-002 — Approve an active step

**As an assigned Approver, I want to approve an active step, so that the request can continue through the workflow.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The user is authenticated and active.
2. The user holds the required role.
3. The user is assigned to the active step.
4. The user is not the requester.
5. The step is `ACTIVE`.
6. Previous required steps are complete.
7. The step becomes `APPROVED`.
8. The decision actor and timestamp are stored.
9. SLA completion status is calculated.
10. The next pending step becomes active.
11. If no step remains, the request becomes `APPROVED`.
12. The transition is audited.
13. The operation is transactional.
14. Repeating the same submission does not advance the workflow twice.

### Dependencies

- Approval service;
- authorization service;
- workflow state transitions;
- SLA service;
- audit logging;
- transaction management.

---

## US-APP-003 — Reject a request

**As an assigned Approver, I want to reject an active request with a reason, so that invalid or unjustified purchases do not proceed.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only the assigned authorized approver can reject.
2. The step must be `ACTIVE`.
3. A rejection comment is required.
4. The active step becomes `REJECTED`.
5. The request becomes `REJECTED`.
6. Future pending steps become `CANCELLED`.
7. No further approval action is permitted.
8. The actor, reason, and timestamp are stored.
9. The rejection is audited.
10. Duplicate rejection is prevented.

### Dependencies

- Approval service;
- workflow transition validation;
- audit logging.

---

## US-APP-004 — Return a request for changes

**As an assigned Approver, I want to return a request for correction, so that the Requester can fix incomplete or inaccurate information.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only the assigned authorized approver can return the request.
2. The step must be `ACTIVE`.
3. A return comment is required.
4. The step becomes `CHANGES_REQUESTED`.
5. The request becomes `CHANGES_REQUESTED`.
6. Approval actions are blocked until resubmission.
7. The Requester can view the comment.
8. The action is audited.
9. Future pending steps do not become active.

### Dependencies

- Approval service;
- request state transitions;
- audit logging.

---

## US-APP-005 — Prevent self-approval

**As the organization, I want users to be prevented from approving their own requests, so that separation of duties is preserved.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. A user cannot decide a step for a request they created.
2. Holding the required role does not override this rule.
3. The system attempts to use another eligible approver where configured.
4. If no eligible approver exists, workflow initialization is blocked.
5. A self-approval attempt is denied and audited where appropriate.
6. Automated tests cover multi-role users.

### Dependencies

- Assignment service;
- authorization service;
- audit logging.

---

## US-APP-006 — Prevent duplicate decisions

**As the organization, I want duplicate approval actions to be rejected, so that repeated submissions do not corrupt workflow state.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. A completed step cannot be decided again.
2. Repeated browser submissions create only one decision.
3. A rejected request cannot later be approved.
4. Only one next step becomes active.
5. Invalid repetitions raise a controlled business error.
6. The database remains consistent after repeated requests.

### Dependencies

- State validation;
- transaction handling;
- database constraints where appropriate.

---

## US-APP-007 — Prevent out-of-order decisions

**As the organization, I want later approval steps to remain inaccessible until previous steps are complete, so that the workflow sequence is enforced.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. A `PENDING` step cannot be approved.
2. Finance cannot act before required IT Review.
3. Director cannot act before Finance.
4. URL manipulation does not bypass the check.
5. Direct API requests do not bypass the check.
6. Invalid attempts return the correct error response.
7. Invalid attempts do not change workflow data.

### Dependencies

- Workflow state validation;
- authorization service.

---

# 7. Return for Changes and Revision History

## US-REV-001 — Edit a returned request

**As a Requester, I want to edit a request returned for changes, so that I can address the approver's concerns.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only the request owner can edit it.
2. The request must be `CHANGES_REQUESTED`.
3. The Requester can view the return comment.
4. Permitted business fields can be changed.
5. Historical decisions and comments cannot be changed.
6. Assigned approvers cannot be edited directly.
7. Another user cannot edit the request.
8. Changes are recorded.

### Dependencies

- Ownership authorization;
- revision handling;
- validation.

---

## US-REV-002 — Resubmit a returned request

**As a Requester, I want to resubmit a corrected request, so that the approval process can restart using the updated data.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Only the request owner can resubmit.
2. The request must be `CHANGES_REQUESTED`.
3. Updated fields are validated.
4. The revision number increases.
5. The approval path is recalculated.
6. A new approval cycle is created.
7. Manager Approval starts again.
8. Previous approval cycles remain visible.
9. New SLA deadlines are created.
10. The request returns to `IN_REVIEW`.
11. The operation is transactional.
12. The resubmission is audited.

### Dependencies

- Revision model;
- workflow cycle model;
- rule service;
- SLA service;
- audit logging.

---

## US-REV-003 — View revision history

**As an authorized user, I want to view request revisions and previous approval cycles, so that I can understand how the request changed over time.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Authorized users can view the current revision number.
2. Previous revisions remain read-only.
3. Each revision shows the submitted values or a structured snapshot.
4. Each revision shows its generated approval path.
5. Each revision shows decisions and comments.
6. Requesters see only their own request history.
7. Auditors and Process Managers can view all revision histories.
8. Revision records cannot be deleted through the application.

### Dependencies

- Revision persistence;
- object-level authorization.

---

# 8. Request Visibility and History

## US-VIEW-001 — View own requests

**As a Requester, I want to see my requests and their statuses, so that I know what is happening with them.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The list contains only requests owned by the current user.
2. The list shows status, amount, category, created date, and current step.
3. Requests can be filtered by status.
4. Opening a request verifies ownership.
5. The user can see whether a request is overdue or waiting for changes.
6. Empty states are displayed when no requests exist.

### Dependencies

- Request queries;
- object-level authorization;
- SLA display.

---

## US-VIEW-002 — View request details

**As an authorized user, I want to view request details and workflow history, so that I can understand the current and previous decisions.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The page shows all relevant business fields.
2. The current request status is visible.
3. The active workflow step is visible.
4. Completed and pending steps are shown in order.
5. Decision actors, timestamps, and comments are shown according to permission.
6. SLA indicators are shown.
7. Unauthorized users receive 403 or 404 according to policy.
8. Sensitive administrative data is not exposed unnecessarily.

### Dependencies

- Request detail query;
- authorization;
- workflow history;
- SLA presentation.

---

# 9. Workflow Configuration

## US-CONF-001 — View workflow configuration

**As a Process Manager, I want to view the current workflow thresholds and SLA settings, so that I understand how new requests will be processed.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Only authorized users can access the configuration page.
2. The page shows low-value, high-value, and IT Review thresholds.
3. The page shows whether the IT rule is active.
4. The page shows SLA duration by step type.
5. The page identifies the active configuration version or effective configuration.
6. The page clearly states that changes affect new workflow instances only.

### Dependencies

- Workflow configuration model;
- Process Manager authorization.

---

## US-CONF-002 — Update thresholds

**As a Process Manager, I want to update monetary thresholds, so that the workflow reflects current approval policy.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Only a Process Manager can update thresholds.
2. Thresholds must be positive.
3. The low-value threshold must be lower than the high-value threshold.
4. The IT threshold must be valid.
5. Invalid combinations are rejected.
6. Existing in-progress workflows remain unchanged.
7. New requests use the updated configuration.
8. Previous and new values are audited.
9. The update is transactional.

### Dependencies

- Workflow configuration model;
- validation service;
- audit logging.

---

## US-CONF-003 — Configure SLA durations

**As a Process Manager, I want to configure SLA durations per approval step, so that deadlines reflect operational expectations.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Only a Process Manager can update SLA durations.
2. Every duration must be greater than zero.
3. Durations are stored in a consistent unit.
4. Existing active-step deadlines remain unchanged.
5. Newly activated steps use the current configuration.
6. Changes are audited.
7. Invalid values are rejected.

### Dependencies

- SLA configuration;
- Process Manager authorization;
- audit logging.

---

## US-CONF-004 — Toggle the IT Review rule

**As a Process Manager, I want to activate or deactivate the IT Review rule, so that workflow routing can match company policy.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Only a Process Manager can change the setting.
2. Existing workflow instances remain unchanged.
3. New requests use the updated setting.
4. The change is audited.
5. The configuration page clearly displays the current state.

### Dependencies

- Workflow configuration;
- audit logging.

---

# 10. SLA Management

## US-SLA-001 — Calculate a step deadline

**As the system, I want to calculate a deadline when a workflow step becomes active, so that SLA performance can be measured.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. A deadline is created only when the step becomes `ACTIVE`.
2. A pending step has no active SLA clock.
3. The deadline uses the configured duration for the step type.
4. Activation timestamp and deadline are stored.
5. Elapsed clock hours are used in the MVP.
6. New cycles receive new deadlines.
7. Tests cover each step type.

### Dependencies

- SLA configuration;
- workflow activation service.

---

## US-SLA-002 — Show current SLA status

**As an authorized user, I want to see whether a step is on time, approaching its deadline, or overdue, so that I can prioritize action.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Before 75% of the duration has elapsed, the status is `ON_TIME`.
2. At or after 75% and before the deadline, the status is `APPROACHING_DEADLINE`.
3. After the deadline, the status is `OVERDUE`.
4. Completed steps show `COMPLETED_ON_TIME` or `COMPLETED_LATE`.
5. The result is based on stored timestamps.
6. The interface displays a clear indicator.
7. Boundary behavior is tested.

### Dependencies

- SLA calculation service;
- UI status indicators.

---

## US-SLA-003 — Calculate completed SLA performance

**As a Process Manager, I want completed steps to record whether they met their SLA, so that process performance can be analyzed.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Completion timestamp is stored.
2. Completion on or before the deadline counts as on time.
3. Completion after the deadline counts as late.
4. Overdue duration is calculated for late steps.
5. The stored result is available to analytics.
6. Returned and superseded cycles remain traceable.

### Dependencies

- Step completion service;
- analytics queries.

---

# 11. Audit Logging

## US-AUD-001 — Record structured workflow events

**As an Auditor, I want important workflow actions to be recorded in structured audit events, so that process activity can be reviewed reliably.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Audit events contain actor, action, entity type, entity ID, and timestamp.
2. Relevant previous and new states are stored.
3. Request and workflow identifiers are included when applicable.
4. Metadata is structured.
5. Plain-text passwords and session tokens are never stored.
6. Audit records are not editable through the application.
7. Workflow transitions and audit creation occur transactionally where appropriate.

### Dependencies

- AuditLog model;
- audit service;
- workflow services.

---

## US-AUD-002 — View audit records

**As an Auditor, I want to view audit records, so that I can investigate decisions and configuration changes.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Only authorized users can access the audit page.
2. Records are ordered by timestamp.
3. The page supports basic filtering by action, actor, entity type, and date.
4. Audit records are read-only.
5. Requesters see only human-readable history for their own requests.
6. Executive Viewers do not receive raw audit access.
7. Empty states are handled.

### Dependencies

- Audit queries;
- role and scope authorization.

---

# 12. Dashboard and KPI Analytics

## US-DASH-001 — View operational KPIs

**As a Process Manager, I want to view key workflow metrics, so that I can understand process volume and performance.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The dashboard shows total requests.
2. It shows active, approved, rejected, changes-requested, and overdue counts.
3. Metrics are calculated from database data.
4. Filters use consistent date ranges.
5. Empty datasets return zero values safely.
6. Access is restricted to authorized roles.
7. Queries are tested against known seed data.

### Dependencies

- Analytics service;
- authorization;
- seed data.

---

## US-DASH-002 — View duration metrics

**As a Process Manager, I want to see average and median process duration, so that I can understand approval speed without relying on only one measure.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Average duration is calculated for completed requests.
2. Median duration is calculated correctly.
3. Active requests are excluded from completed-duration metrics.
4. The time unit is displayed.
5. Empty datasets are handled safely.
6. Calculation tests cover even and odd record counts.

### Dependencies

- Analytics service;
- completed request timestamps.

---

## US-DASH-003 — View SLA compliance

**As a Process Manager, I want to view SLA compliance rates, so that I can identify whether approval teams meet deadlines.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. The dashboard shows completed-on-time steps divided by eligible completed steps.
2. Cancelled and pending steps are excluded.
3. The formula is documented.
4. Results can be shown overall and by step type.
5. Zero-denominator cases are handled safely.
6. Known seed data produces predictable results.

### Dependencies

- SLA results;
- analytics service.

---

## US-DASH-004 — Identify bottlenecks

**As a Process Manager, I want to identify the slowest workflow step, so that I know where process improvement is needed.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Average completed duration is calculated per step type.
2. The slowest step is identified.
3. Steps with insufficient data are handled transparently.
4. The dashboard shows supporting values, not only a label.
5. The calculation excludes cancelled steps.
6. The methodology is documented.

### Dependencies

- Step duration data;
- analytics service.

---

## US-DASH-005 — View charts

**As an Executive Viewer, I want to view clear charts, so that I can quickly understand process trends.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. The dashboard includes monthly volume.
2. It includes status distribution.
3. It includes category distribution.
4. It includes average duration by step.
5. It includes SLA compliance summary.
6. Charts receive validated data.
7. Charts have accessible labels or supporting text.
8. The server-rendered page remains usable if JavaScript fails.

### Dependencies

- Dashboard API or embedded JSON data;
- Chart.js;
- analytics service.

---

# 13. ROI Analytics

## US-ROI-001 — Configure ROI assumptions

**As a Process Manager, I want to define ROI assumptions, so that savings estimates are based on transparent inputs.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Inputs include manual time, digital time, hourly cost, manual interventions, digital interventions, and implementation cost.
2. Inputs are validated as non-negative.
3. Units are clearly displayed.
4. Assumptions are labeled as estimates.
5. Changes are audited.
6. Historical calculations can identify which assumptions were used.

### Dependencies

- ROI configuration model;
- validation;
- audit logging.

---

## US-ROI-002 — Calculate hours saved

**As an Executive Viewer, I want to see estimated hours saved, so that I can understand the operational benefit of digitization.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Hours saved are calculated from documented assumptions.
2. Negative savings are not silently converted to positive values.
3. The number of eligible processed requests is defined.
4. The formula is documented.
5. The result clearly distinguishes estimated from measured data.
6. Tests cover zero and negative-savings scenarios.

### Dependencies

- ROI service;
- request counts;
- ROI assumptions.

---

## US-ROI-003 — Calculate cost savings and ROI

**As an Executive Viewer, I want to see estimated cost savings, ROI, and payback period, so that I can evaluate the business case for automation.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Estimated cost saved is derived from hours saved and hourly cost.
2. Saving per request is calculated.
3. Monthly and annualized savings are shown.
4. ROI percentage uses the documented implementation-cost formula.
5. Payback period is calculated only when savings are positive.
6. Division-by-zero cases are handled.
7. Limitations are displayed.
8. Tests cover zero implementation cost and zero savings.

### Dependencies

- ROI service;
- documented methodology;
- analytics data.

---

# 14. REST API

## US-API-001 — Retrieve request status

**As an authenticated client, I want to retrieve the status of an authorized request, so that selected data can be consumed as JSON.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. The endpoint requires authentication.
2. Object-level authorization is enforced.
3. The response includes request ID, status, current step, and relevant timestamps.
4. Unauthorized access returns 403 or 404 according to policy.
5. Missing resources return 404.
6. The response uses a consistent JSON format.
7. Sensitive fields are excluded.

### Dependencies

- API Blueprint;
- authorization service;
- serialization.

---

## US-API-002 — Retrieve assigned approval tasks

**As an authenticated Approver, I want to retrieve my assigned tasks as JSON, so that the API demonstrates useful workflow access.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. The endpoint returns only tasks assigned to the current user.
2. Only active users can access it.
3. Filters are validated.
4. The response includes pagination or a documented limit if needed.
5. Unauthorized users receive the correct status code.
6. API tests cover role and assignment checks.

### Dependencies

- API Blueprint;
- approval task query;
- authorization.

---

## US-API-003 — Retrieve dashboard data

**As an authorized analytics user, I want to retrieve dashboard metrics as JSON, so that charts can load structured data.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Access is restricted to authorized roles.
2. Date filters are validated.
3. Metrics match the server-rendered dashboard.
4. Empty datasets return valid JSON.
5. Errors use a consistent JSON structure.
6. Automated tests verify response codes and values.

### Dependencies

- Analytics service;
- API Blueprint;
- authorization.

---

# 15. Error Handling and Security

## US-SEC-001 — Deny unauthorized access

**As the organization, I want unauthorized actions to be denied consistently, so that users cannot access or modify data outside their responsibility.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Unauthenticated browser requests redirect to login.
2. Authenticated but unauthorized browser requests return 403.
3. Unauthenticated API requests return 401.
4. Unauthorized API requests return 403.
5. Object IDs cannot be changed to access unrelated requests.
6. Hidden buttons are not the only control.
7. Unauthorized attempts do not change data.

### Dependencies

- Authentication;
- authorization helpers;
- error handlers.

---

## US-SEC-002 — Display professional error pages

**As a user, I want clear error pages, so that failures are understandable without exposing internal details.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Custom 403, 404, and 500 pages exist.
2. Production errors do not expose stack traces.
3. The 500 page provides a safe recovery action.
4. Errors are logged with appropriate context.
5. Sensitive data is not included in logs or pages.

### Dependencies

- Error handlers;
- logging;
- templates.

---

## US-SEC-003 — Protect secrets and configuration

**As a developer, I want secrets to be loaded from environment variables, so that credentials are not committed to Git.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Secret keys are not hardcoded.
2. `.env` is ignored by Git.
3. `.env.example` contains only safe placeholders.
4. Missing required production configuration fails clearly.
5. Development, testing, and production configurations are separated.

### Dependencies

- Configuration classes;
- environment loading;
- repository configuration.

---

# 16. Testing and Continuous Integration

## US-TEST-001 — Run automated tests locally

**As a developer, I want to run the full automated test suite locally, so that I can verify the application before committing changes.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. A documented command runs all tests.
2. Tests use an isolated test database.
3. Fixtures create predictable data.
4. Tests do not depend on execution order.
5. Critical workflow tests are included.
6. Failures return useful output.

### Dependencies

- pytest configuration;
- application factory;
- test database;
- fixtures.

---

## US-TEST-002 — Run tests in GitHub Actions

**As a developer, I want GitHub Actions to run tests automatically, so that regressions are detected on pushes and pull requests.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. The workflow installs dependencies in a clean environment.
2. It runs linting and tests.
3. It fails when tests fail.
4. It does not require committed secrets.
5. The README displays or references CI status.
6. The workflow runs on the supported Python version.

### Dependencies

- GitHub repository;
- dependency files;
- test suite;
- lint configuration.

---

# 17. Seed Data and Demo

## US-DEMO-001 — Load realistic seed data

**As a reviewer, I want realistic demonstration data, so that the workflow, dashboard, and ROI features can be evaluated immediately.**

**Priority:** P0  
**Scope:** MVP

### Acceptance Criteria

1. Seed data creates Aurevia Solutions departments.
2. It creates users for every required role.
3. It creates manager-report relationships.
4. It creates requests across all major statuses.
5. It includes low-, medium-, and high-value requests.
6. It includes IT Review scenarios.
7. It includes approvals, rejections, returns, and SLA violations.
8. Data contains no real personal information.
9. The seed command is documented and repeatable.

### Dependencies

- Database models;
- CLI command;
- workflow services.

---

## US-DEMO-002 — Use demo accounts

**As a reviewer, I want documented demo accounts for different roles, so that I can test the application quickly.**

**Priority:** P1  
**Scope:** MVP

### Acceptance Criteria

1. Demo accounts exist for Requester, Manager, Finance, IT, Director, Process Manager, Administrator, and Auditor.
2. Credentials are safe for public demonstration.
3. Production secrets are not reused.
4. Demo accounts are documented.
5. The demo environment can be reset.

### Dependencies

- Seed data;
- deployment configuration;
- README.

---

# 18. Post-MVP Stories

## US-FILE-001 — Upload supporting attachments

**As a Requester, I want to attach supporting documents, so that approvers can review evidence related to the purchase.**

**Priority:** P2  
**Scope:** Post-MVP unless the core workflow is stable

### Acceptance Criteria

1. Only permitted file types are accepted.
2. File size is limited.
3. Stored filenames are generated safely.
4. Files are stored outside public static paths.
5. Downloads require object-level authorization.
6. Original filenames are treated as untrusted metadata.
7. Malicious paths are rejected.

### Dependencies

- Secure file storage;
- attachment model;
- authorization.

---

## US-NOTIF-001 — Receive notifications

**As a user, I want to receive notifications about workflow actions, so that I know when my attention is required.**

**Priority:** P2  
**Scope:** Post-MVP

### Acceptance Criteria

1. Notification events are generated for assignment, return for changes, approval, and rejection.
2. Delivery failures do not corrupt workflow state.
3. Users can see in-app notifications.
4. Email delivery may be added separately.

### Dependencies

- Notification model;
- event handling;
- optional email service.

---

## US-WF-FUTURE-001 — Configure arbitrary workflows

**As a Process Manager, I want to define custom workflow steps and transitions, so that FlowYield can support additional business processes.**

**Priority:** P2  
**Scope:** Post-MVP

### Acceptance Criteria

1. Workflow definitions are versioned.
2. Invalid graphs are rejected.
3. In-progress instances preserve their version.
4. The interface prevents impossible configurations.
5. The feature does not alter historical workflows.

### Dependencies

- Workflow templates;
- versioning;
- transition model;
- configuration UI.

---

# 19. MVP Story Summary

## P0 Stories

The P0 stories cover:

- authentication;
- inactive-user protection;
- user administration;
- departments and managers;
- request drafts;
- request submission;
- path generation;
- approver assignment;
- approval, rejection, and return for changes;
- resubmission;
- self-approval prevention;
- duplicate and out-of-order action prevention;
- request visibility;
- SLA calculations;
- audit logging;
- core KPIs;
- ROI calculations;
- security;
- automated testing;
- realistic seed data.

These stories define the minimum complete portfolio product.

## P1 Stories

The P1 stories strengthen the portfolio through:

- revision-history views;
- workflow configuration;
- audit filtering;
- detailed analytics;
- bottleneck indicators;
- charts;
- selected REST endpoints;
- GitHub Actions;
- demo accounts;
- public deployment.

## P2 Stories

The P2 stories are intentionally deferred:

- password reset;
- attachments;
- notifications;
- arbitrary workflow configuration.

---

# 20. Definition of Ready

A user story is ready for implementation when:

- the business objective is clear;
- acceptance criteria are testable;
- dependencies are identified;
- authorization requirements are known;
- required data is understood;
- unresolved architectural decisions are documented;
- the story is assigned to a milestone.

---

# 21. Definition of Done

A user story is complete when:

- the implementation satisfies every acceptance criterion;
- authorization is enforced server-side;
- validation is implemented;
- expected errors are handled;
- automated tests cover the normal path and relevant edge cases;
- documentation is updated;
- no secrets or generated local files are committed;
- the code passes formatting, linting, and tests;
- the change is committed with a clear message.
