from mcp.server.fastmcp import FastMCP
from datetime import date
from typing import Optional
from uuid import uuid4

# Create an MCP server
mcp = FastMCP("LeaveManagement")

# In-memory storage for demonstration purposes
employees = {
    "E001": {
        "name": "Alice",
        "annual_leave": 20,
        "sick_leave": 10,
    },
    "E002": {
        "name": "Bob",
        "annual_leave": 15,
        "sick_leave": 8,
    },
}

leave_requests = {}


# Tool 1: Apply for leave
@mcp.tool()
def apply_for_leave(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str = "",
) -> dict:
    """
    Submit a leave request for an employee.

    Args:
        employee_id: Unique employee identifier.
        leave_type: Type of leave (annual or sick).
        start_date: First day of leave in YYYY-MM-DD format.
        end_date: Last day of leave in YYYY-MM-DD format.
        reason: Optional reason for the leave request.
    """
    if employee_id not in employees:
        return {"success": False, "message": "Employee not found."}

    leave_type = leave_type.lower()

    if leave_type not in ["annual", "sick"]:
        return {
            "success": False,
            "message": "Invalid leave type. Choose 'annual' or 'sick'.",
        }

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return {
            "success": False,
            "message": "Invalid date. Use YYYY-MM-DD format.",
        }

    if end < start:
        return {
            "success": False,
            "message": "End date cannot be before start date.",
        }

    # Count calendar days, including both the start and end dates.
    days_requested = (end - start).days + 1

    balance_key = f"{leave_type}_leave"
    balance = employees[employee_id][balance_key]

    if days_requested > balance:
        return {
            "success": False,
            "message": (
                f"Insufficient {leave_type} leave balance. "
                f"Available: {balance} days."
            ),
        }

    request_id = str(uuid4())[:8].upper()

    leave_requests[request_id] = {
        "request_id": request_id,
        "employee_id": employee_id,
        "employee_name": employees[employee_id]["name"],
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days_requested": days_requested,
        "reason": reason,
        "status": "pending",
    }

    return {
        "success": True,
        "message": "Leave request submitted successfully.",
        "request": leave_requests[request_id],
    }


# Tool 2: Check leave balance
@mcp.tool()
def check_leave_balance(employee_id: str) -> dict:
    """
    Check an employee's remaining annual and sick leave balance.

    Args:
        employee_id: Unique employee identifier.
    """
    if employee_id not in employees:
        return {"success": False, "message": "Employee not found."}

    employee = employees[employee_id]

    return {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "annual_leave_balance": employee["annual_leave"],
        "sick_leave_balance": employee["sick_leave"],
    }


# Tool 3: View leave requests
@mcp.tool()
def get_leave_requests(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    """
    Retrieve leave requests, optionally filtering by employee or status.

    Args:
        employee_id: Optional employee ID to filter by.
        status: Optional status filter (pending, approved, rejected, cancelled).
    """
    valid_statuses = {"pending", "approved", "rejected", "cancelled"}

    if status and status.lower() not in valid_statuses:
        return {
            "success": False,
            "message": f"Invalid status. Choose from {sorted(valid_statuses)}.",
        }

    results = list(leave_requests.values())

    if employee_id:
        results = [
            request for request in results
            if request["employee_id"] == employee_id
        ]

    if status:
        results = [
            request for request in results
            if request["status"] == status.lower()
        ]

    return {
        "count": len(results),
        "requests": results,
    }


# Tool 4: Approve a leave request
@mcp.tool()
def approve_leave(request_id: str) -> dict:
    """
    Approve a pending leave request.

    Args:
        request_id: ID of the leave request.
    """
    request = leave_requests.get(request_id)

    if not request:
        return {"success": False, "message": "Leave request not found."}

    if request["status"] != "pending":
        return {
            "success": False,
            "message": f"Cannot approve a request with status '{request['status']}'.",
        }

    request["status"] = "approved"

    return {
        "success": True,
        "message": "Leave request approved.",
        "request": request,
    }


# Tool 5: Reject a leave request
@mcp.tool()
def reject_leave(request_id: str) -> dict:
    """
    Reject a pending leave request.

    Args:
        request_id: ID of the leave request.
    """
    request = leave_requests.get(request_id)

    if not request:
        return {"success": False, "message": "Leave request not found."}

    if request["status"] != "pending":
        return {
            "success": False,
            "message": f"Cannot reject a request with status '{request['status']}'.",
        }

    request["status"] = "rejected"

    return {
        "success": True,
        "message": "Leave request rejected.",
        "request": request,
    }


# Tool 6: Cancel a leave request
@mcp.tool()
def cancel_leave(request_id: str, employee_id: str) -> dict:
    """
    Cancel an employee's pending leave request.

    Args:
        request_id: ID of the leave request.
        employee_id: Employee requesting cancellation.
    """
    request = leave_requests.get(request_id)

    if not request:
        return {"success": False, "message": "Leave request not found."}

    if request["employee_id"] != employee_id:
        return {
            "success": False,
            "message": "You cannot cancel another employee's leave request.",
        }

    if request["status"] != "pending":
        return {
            "success": False,
            "message": "Only pending requests can be cancelled.",
        }

    request["status"] = "cancelled"

    return {
        "success": True,
        "message": "Leave request cancelled.",
        "request": request,
    }


# Resource: Retrieve employee information
@mcp.resource("employee://{employee_id}")
def get_employee(employee_id: str) -> str:
    """
    Retrieve employee information using an employee ID.
    """
    employee = employees.get(employee_id)

    if not employee:
        return f"Employee {employee_id} not found."

    return (
        f"Employee ID: {employee_id}\n"
        f"Name: {employee['name']}\n"
        f"Annual Leave: {employee['annual_leave']} days\n"
        f"Sick Leave: {employee['sick_leave']} days"
    )


# Start the MCP server
if __name__ == "__main__":
    mcp.run()