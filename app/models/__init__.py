"""
Models package for the LMS backend.

This package contains all SQLAlchemy models for the application.
"""

from .controller import Controller, ControllerStatus
from .datapoint import Datapoint, DatapointValueType
from .firmware import Firmware, FirmwareStatus, FirmwareVersionType
from .firmware_deployment import FirmwareDeployment, FirmwareDeploymentStatus
from .machine import Machine, MachineType, MachineStatus
from .tenant import Tenant, TenantStatus
from .tenant_member import TenantMember
from .store import Store, StoreStatus
from .store_member import StoreMember
from .permission_group import PermissionGroup
from .permission import Permission
from .user import User, UserRole, UserStatus
from .notification import Notification, NotificationType, NotificationStatus, NotificationChannel
from .order import Order, OrderStatus, OrderDetail, OrderDetailStatus, PromotionOrder
from .payment import (
    Payment, 
    PaymentStatus, 
    PaymentProvider
)
from .promotion_campaign import (
    PromotionCampaign,
    PromotionCampaignStatus,
)
from .subscription_plan import SubscriptionPlan
from .system_task import SystemTask, SystemTaskStatus

__all__ = [
    # Controller
    "Controller",
    "ControllerStatus",

    # Datapoint
    "Datapoint",
    "DatapointValueType",

    # Firmware
    "Firmware",
    "FirmwareStatus",
    "FirmwareVersionType",

    # Firmware Deployment
    "FirmwareDeployment",
    "FirmwareDeploymentStatus",

    # Machine
    "Machine",
    "MachineType",
    "MachineStatus",

    # Tenant
    "Tenant",
    "TenantStatus",
    "TenantMember",

    # Store
    "Store",
    "StoreStatus",
    "StoreMember",

    # Permission
    "PermissionGroup",
    "Permission",

    # User
    "User",
    "UserRole", 
    "UserStatus",

    # Notification
    "Notification",
    "NotificationType",
    "NotificationStatus",
    "NotificationChannel",

    # Order
    "Order",
    "OrderStatus",
    "OrderDetail",
    "OrderDetailStatus",
    "PromotionOrder",

    # Payment
    "Payment",
    "PaymentStatus",
    "PaymentProvider",
    
    # Promotion Campaign
    "PromotionCampaign",
    "PromotionCampaignStatus",

    # SystemTask
    "SystemTask",
    "SystemTaskStatus",

    # Subscription Plan
    "SubscriptionPlan",
]
