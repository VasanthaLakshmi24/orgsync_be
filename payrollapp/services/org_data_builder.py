from collections import defaultdict
from django.db.models import Count
from payrollapp.models import (
    Employee,
    Department,
    CLevelSeat,
    CLevelAssignment,
    Designation,
)



# =====================================================
# TREE VIEW (Single reporting line)
# =====================================================
def build_org_tree(org):
    employees = Employee.objects.filter(parent=org, status="onroll")

    nodes = []

    for emp in employees:
        nodes.append({
            "id": f"emp-{emp.id}",  # ✅ frontend expects `id`
            "parentId": (
                f"emp-{emp.reporting_manager.id}"
                if emp.reporting_manager else None
            ),
            "name": (
                emp.designation.name
                if emp.designation else emp.userName
            ),
            "meta": {
                "employee": {
                    "id": str(emp.id),       # ✅ UUID → str
                    "name": emp.userName,
                    "email": emp.email,
                }
            }
        })

    return nodes


# =====================================================
# MATRIX VIEW (Solid + Dotted reporting)
# =====================================================
def build_org_matrix(org):
    employees = Employee.objects.filter(parent=org, status="onroll")

    nodes = []
    links = []

    # ---------- Nodes ----------
    for emp in employees:
        nodes.append({
            "id": f"emp-{emp.id}",
            "name": emp.userName,
            "meta": {
                "employee": {
                    "id": str(emp.id),
                    "name": emp.userName,
                    "email": emp.email,
                }
            }
        })

    # ---------- Solid (Primary Manager) ----------
    for emp in employees:
        if emp.reporting_manager:
            links.append({
                "source": f"emp-{emp.reporting_manager.id}",
                "target": f"emp-{emp.id}",
                "style": "solid",   # ✅ frontend expects `style`
            })

        # ---------- Dotted (Matrix Managers) ----------
        for mgr in emp.matrix_managers.all():
            links.append({
                "source": f"emp-{mgr.id}",
                "target": f"emp-{emp.id}",
                "style": "dashed",  # ✅ frontend expects `style`
            })

    return {
        "nodes": nodes,
        "links": links
    }


# =====================================================
# ANALYTICS (Headcount + Depth)
# =====================================================
def build_org_analytics(org):
    employees = Employee.objects.filter(parent=org, status="onroll")

    headcount = {
        "total": employees.count(),
        "by_department": list(
            employees
            .values("department__name")
            .annotate(count=Count("id"))
        ),
        "by_level": list(
            employees
            .values("designation__level")
            .annotate(count=Count("id"))
        ),
        "by_location": list(
            employees
            .values("location__name")
            .annotate(count=Count("id"))
        ),
    }

    # ---------- Org Depth ----------
    tree = defaultdict(list)

    for emp in employees:
        if emp.reporting_manager_id:
            tree[str(emp.reporting_manager_id)].append(str(emp.id))

    def dfs(emp_id, depth):
        if emp_id not in tree:
            return depth
        return max(dfs(child_id, depth + 1) for child_id in tree[emp_id])

    depth = 1
    roots = employees.filter(reporting_manager__isnull=True)

    for root in roots:
        depth = max(depth, dfs(str(root.id), 1))

    return {
        "headcount": headcount,
        "org_depth": depth,
    }
