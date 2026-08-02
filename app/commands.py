"""FlowYield CLI commands."""

from datetime import date
from decimal import Decimal

import click
from flask import Flask
from sqlalchemy import select

from app.authorization import RoleName
from app.extensions import db
from app.models import (
    Department,
    PurchaseRequest,
    RequestCategory,
    RequestStatus,
    Role,
    StepConfiguration,
    StepType,
    User,
    UserRole,
    WorkflowConfiguration,
)

DEMO_PASSWORD = "FlowYieldDemo123!"


ROLE_DESCRIPTIONS = {
    RoleName.ADMINISTRATOR: (
        "Manage users, roles, departments, and application settings."
    ),
    RoleName.REQUESTER: ("Create, edit, submit, and track purchase requests."),
    RoleName.MANAGER_APPROVER: (
        "Review purchase requests submitted by direct reports."
    ),
    RoleName.FINANCE_APPROVER: ("Review the financial impact of purchase requests."),
    RoleName.IT_REVIEWER: ("Review software and IT services purchase requests."),
    RoleName.DIRECTOR_APPROVER: ("Approve high-value purchase requests."),
    RoleName.PROCESS_MANAGER: (
        "Manage workflow configuration and operational processes."
    ),
    RoleName.AUDITOR: ("Review workflow history and audit information."),
    RoleName.EXECUTIVE_VIEWER: ("View executive workflow and performance information."),
}


def get_or_create_role(role_name: RoleName) -> Role:
    """Return an existing role or create it."""
    role = db.session.scalar(select(Role).where(Role.name == role_name.value))

    if role is None:
        role = Role(
            name=role_name.value,
            description=ROLE_DESCRIPTIONS[role_name],
        )
        db.session.add(role)
        db.session.flush()
    else:
        role.description = ROLE_DESCRIPTIONS[role_name]

    return role


def get_or_create_department(
    *,
    name: str,
    code: str,
) -> Department:
    """Return an existing department or create it."""
    department = db.session.scalar(select(Department).where(Department.code == code))

    if department is None:
        department = Department(
            name=name,
            code=code,
            is_active=True,
        )
        db.session.add(department)
        db.session.flush()
    else:
        department.name = name
        department.is_active = True

    return department


def get_or_create_user(
    *,
    email: str,
    first_name: str,
    last_name: str,
    department: Department,
) -> User:
    """Return an existing demo user or create it."""
    user = db.session.scalar(select(User).where(User.email == email))

    if user is None:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            department=department,
            password_hash="temporary",
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()
    else:
        user.first_name = first_name
        user.last_name = last_name
        user.department = department
        user.is_active = True

    user.set_password(DEMO_PASSWORD)

    return user


def assign_role(
    *,
    user: User,
    role: Role,
    assigned_by: User | None = None,
) -> None:
    """Assign a role unless the assignment already exists."""
    assignment = db.session.scalar(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
        )
    )

    if assignment is None:
        assignment = UserRole(
            user=user,
            role=role,
            assigned_by=assigned_by,
        )
        db.session.add(assignment)


def get_or_create_workflow_configuration(
    *,
    administrator: User,
    it_reviewer: User,
    finance_approver: User,
    director_approver: User,
) -> WorkflowConfiguration:
    """Create or update the active demo workflow configuration."""
    configurations = list(db.session.scalars(select(WorkflowConfiguration)).all())

    for configuration in configurations:
        configuration.is_active = False

    configuration = db.session.scalar(
        select(WorkflowConfiguration).where(WorkflowConfiguration.version_number == 1)
    )

    if configuration is None:
        configuration = WorkflowConfiguration(
            version_number=1,
            name="Aurevia Purchase Approval Workflow",
            low_value_threshold=Decimal("1000.00"),
            high_value_threshold=Decimal("10000.00"),
            it_review_threshold=Decimal("5000.00"),
            it_review_enabled=True,
            is_active=True,
            created_by=administrator,
        )
        db.session.add(configuration)
        db.session.flush()
    else:
        configuration.name = "Aurevia Purchase Approval Workflow"
        configuration.low_value_threshold = Decimal("1000.00")
        configuration.high_value_threshold = Decimal("10000.00")
        configuration.it_review_threshold = Decimal("5000.00")
        configuration.it_review_enabled = True
        configuration.is_active = True
        configuration.created_by = administrator

    step_values = {
        StepType.MANAGER_APPROVAL: {
            "sla_duration_hours": 24,
            "required_role_name": (RoleName.MANAGER_APPROVER.value),
            "sequence_hint": 1,
            "default_assignee": None,
        },
        StepType.IT_REVIEW: {
            "sla_duration_hours": 36,
            "required_role_name": RoleName.IT_REVIEWER.value,
            "sequence_hint": 2,
            "default_assignee": it_reviewer,
        },
        StepType.FINANCE_APPROVAL: {
            "sla_duration_hours": 48,
            "required_role_name": (RoleName.FINANCE_APPROVER.value),
            "sequence_hint": 3,
            "default_assignee": finance_approver,
        },
        StepType.DIRECTOR_APPROVAL: {
            "sla_duration_hours": 72,
            "required_role_name": (RoleName.DIRECTOR_APPROVER.value),
            "sequence_hint": 4,
            "default_assignee": director_approver,
        },
    }

    existing_steps = {
        step_configuration.step_type: step_configuration
        for step_configuration in configuration.step_configurations
    }

    for step_type, values in step_values.items():
        step_configuration = existing_steps.get(step_type)

        if step_configuration is None:
            step_configuration = StepConfiguration(
                workflow_configuration=configuration,
                step_type=step_type,
                sla_duration_hours=values["sla_duration_hours"],
                required_role_name=values["required_role_name"],
                sequence_hint=values["sequence_hint"],
                default_assignee=values["default_assignee"],
                is_enabled=True,
            )
            db.session.add(step_configuration)
        else:
            step_configuration.sla_duration_hours = values["sla_duration_hours"]
            step_configuration.required_role_name = values["required_role_name"]
            step_configuration.sequence_hint = values["sequence_hint"]
            step_configuration.default_assignee = values["default_assignee"]
            step_configuration.is_enabled = True

    return configuration


def get_or_create_demo_request(
    *,
    requester: User,
    title: str,
    description: str,
    business_justification: str,
    category: RequestCategory,
    supplier: str,
    requested_amount: Decimal,
    expected_purchase_date: date,
) -> PurchaseRequest:
    """Return an existing named demo request or create it."""
    purchase_request = db.session.scalar(
        select(PurchaseRequest).where(
            PurchaseRequest.requester_id == requester.id,
            PurchaseRequest.title == title,
        )
    )

    if purchase_request is None:
        purchase_request = PurchaseRequest(
            requester=requester,
            department=requester.department,
            title=title,
            description=description,
            business_justification=business_justification,
            category=category,
            supplier=supplier,
            requested_amount=requested_amount,
            currency="EUR",
            expected_purchase_date=expected_purchase_date,
            status=RequestStatus.DRAFT,
        )
        db.session.add(purchase_request)

    return purchase_request


def seed_demo_data() -> None:
    """Create or update the complete FlowYield demo environment."""
    roles = {role_name: get_or_create_role(role_name) for role_name in RoleName}

    operations = get_or_create_department(
        name="Operations",
        code="OPS",
    )
    information_technology = get_or_create_department(
        name="Information Technology",
        code="IT",
    )
    finance = get_or_create_department(
        name="Finance",
        code="FIN",
    )
    executive = get_or_create_department(
        name="Executive Office",
        code="EXEC",
    )

    administrator = get_or_create_user(
        email="admin@aurevia.example",
        first_name="Amelia",
        last_name="Administrator",
        department=operations,
    )
    requester = get_or_create_user(
        email="requester@aurevia.example",
        first_name="Alex",
        last_name="Morgan",
        department=operations,
    )
    manager = get_or_create_user(
        email="manager@aurevia.example",
        first_name="Maya",
        last_name="Manager",
        department=operations,
    )
    it_reviewer = get_or_create_user(
        email="it@aurevia.example",
        first_name="Isaac",
        last_name="Reviewer",
        department=information_technology,
    )
    finance_approver = get_or_create_user(
        email="finance@aurevia.example",
        first_name="Fiona",
        last_name="Finance",
        department=finance,
    )
    director_approver = get_or_create_user(
        email="director@aurevia.example",
        first_name="Diana",
        last_name="Director",
        department=executive,
    )

    user_roles = {
        administrator: [
            RoleName.ADMINISTRATOR,
            RoleName.PROCESS_MANAGER,
            RoleName.AUDITOR,
        ],
        requester: [
            RoleName.REQUESTER,
        ],
        manager: [
            RoleName.MANAGER_APPROVER,
            RoleName.REQUESTER,
        ],
        it_reviewer: [
            RoleName.IT_REVIEWER,
        ],
        finance_approver: [
            RoleName.FINANCE_APPROVER,
        ],
        director_approver: [
            RoleName.DIRECTOR_APPROVER,
            RoleName.EXECUTIVE_VIEWER,
        ],
    }

    for user, role_names in user_roles.items():
        for role_name in role_names:
            assign_role(
                user=user,
                role=roles[role_name],
                assigned_by=administrator,
            )

    requester.manager = manager

    get_or_create_workflow_configuration(
        administrator=administrator,
        it_reviewer=it_reviewer,
        finance_approver=finance_approver,
        director_approver=director_approver,
    )

    get_or_create_demo_request(
        requester=requester,
        title="Annual CRM software licenses",
        description=(
            "Purchase annual CRM licenses for the Sales and Operations teams."
        ),
        business_justification=(
            "The current licenses expire soon and are required "
            "for customer management and reporting."
        ),
        category=RequestCategory.SOFTWARE,
        supplier="Northstar Software Europe",
        requested_amount=Decimal("7200.00"),
        expected_purchase_date=date(2026, 10, 1),
    )

    get_or_create_demo_request(
        requester=requester,
        title="Operations office supplies",
        description=(
            "Restock stationery, printer consumables, and meeting-room materials."
        ),
        business_justification=(
            "Current supplies are below the minimum operational stock level."
        ),
        category=RequestCategory.OFFICE_SUPPLIES,
        supplier="OfficeHub Distribution",
        requested_amount=Decimal("780.00"),
        expected_purchase_date=date(2026, 9, 15),
    )

    get_or_create_demo_request(
        requester=requester,
        title="Data analytics workstations",
        description=(
            "Purchase high-performance workstations for the business intelligence team."
        ),
        business_justification=(
            "Existing hardware cannot efficiently process the "
            "team's current analytics workloads."
        ),
        category=RequestCategory.HARDWARE,
        supplier="Vertex Business Systems",
        requested_amount=Decimal("18500.00"),
        expected_purchase_date=date(2026, 11, 1),
    )

    db.session.commit()


def register_commands(app: Flask) -> None:
    """Register FlowYield CLI commands."""

    @app.cli.command("seed-demo")
    def seed_demo_command() -> None:
        """Create or update local demonstration data."""
        try:
            seed_demo_data()
        except Exception:
            db.session.rollback()
            raise

        click.echo("FlowYield demo data created successfully.")
        click.echo("")
        click.echo("Demo password:")
        click.echo(f"  {DEMO_PASSWORD}")
        click.echo("")
        click.echo("Demo accounts:")
        click.echo("  requester@aurevia.example")
        click.echo("  manager@aurevia.example")
        click.echo("  it@aurevia.example")
        click.echo("  finance@aurevia.example")
        click.echo("  director@aurevia.example")
        click.echo("  admin@aurevia.example")
