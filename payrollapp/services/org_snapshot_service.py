"""
Org Snapshot Service
--------------------
Responsible for creating immutable historical snapshots
of the organization structure (tree, matrix, analytics).

Used by:
- Manual snapshot API
- Auto snapshot signals (hire / transfer / re-org)
"""

from datetime import timedelta
from django.utils import timezone
from payrollapp.models import OrgSnapshot
from payrollapp.services.org_data_builder import (
    build_org_tree,
    build_org_matrix,
    build_org_analytics,
)

# -------------------------------
# Configuration (SAFE DEFAULTS)
# -------------------------------

AUTO_SNAPSHOT_RETENTION = 20          # keep last 20 AUTO snapshots
AUTO_SNAPSHOT_COOLDOWN_SECONDS = 30   # prevent rapid duplicate snapshots


# -------------------------------
# Public API
# -------------------------------

def create_org_snapshot(org, snapshot_type="MANUAL", triggered_by=None):
    """
    Create a historical snapshot of the org.

    Args:
        org (Organization): Organization instance
        snapshot_type (str): AUTO or MANUAL
        triggered_by (Employee | None): Who triggered the snapshot

    Returns:
        OrgSnapshot instance
    """

    if not org:
        raise ValueError("Organization is required to create snapshot")

    # Prevent snapshot spam for AUTO triggers
    if snapshot_type == "AUTO" and _is_recent_auto_snapshot(org):
        return _get_latest_snapshot(org)

    tree_data = build_org_tree(org)
    matrix_data = build_org_matrix(org)
    analytics_data = build_org_analytics(org)

    snapshot = OrgSnapshot.objects.create(
        organization=org,
        tree_data=tree_data,
        matrix_data=matrix_data,
        analytics_data=analytics_data,
        snapshot_type=snapshot_type,
        triggered_by=triggered_by,
    )

    # Cleanup old AUTO snapshots
    if snapshot_type == "AUTO":
        _cleanup_old_auto_snapshots(org)

    return snapshot


# -------------------------------
# Internal Helpers
# -------------------------------

def _is_recent_auto_snapshot(org):
    """
    Check if an AUTO snapshot was created very recently.
    Prevents multiple snapshots for the same logical action.
    """
    since = timezone.now() - timedelta(seconds=AUTO_SNAPSHOT_COOLDOWN_SECONDS)

    return OrgSnapshot.objects.filter(
        organization=org,
        snapshot_type="AUTO",
        created_at__gte=since,
    ).exists()


def _get_latest_snapshot(org):
    """
    Return the most recent snapshot for an org.
    """
    return (
        OrgSnapshot.objects
        .filter(organization=org)
        .order_by("-created_at")
        .first()
    )


def _cleanup_old_auto_snapshots(org):
    """
    Retain only the most recent AUTO snapshots to control DB size.
    MANUAL snapshots are never deleted.
    """
    auto_snapshots = (
        OrgSnapshot.objects
        .filter(organization=org, snapshot_type="AUTO")
        .order_by("-created_at")
    )

    excess = auto_snapshots[AUTO_SNAPSHOT_RETENTION:]
    if excess.exists():
        excess.delete()
