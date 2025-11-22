from enum import Enum


class PortalAccessEnum(str, Enum):
    # General
    PORTAL_LAUNDRY_FOUNDATION_MANAGEMENT = "portal_laundry_foundation_management"
    PORTAL_SYSTEM_MANAGEMENT = "portal_system_management"

    # Overview
    PORTAL_DASHBOARD_OVERVIEW = "portal_dashboard_overview"
    PORTAL_DASHBOARD_ORDER_MANAGEMENT = "portal_dashboard_order_management"
    PORTAL_DASHBOARD_MACHINE_MANAGEMENT = "portal_dashboard_machine_management"
    PORTAL_DASHBOARD_MACHINE_SETTING = "portal_dashboard_machine_setting"

