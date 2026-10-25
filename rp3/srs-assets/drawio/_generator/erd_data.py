"""Conceptual + logical ERD of Lock.R from the JPA entities (entities.json) + assistant-service SQL."""
import json
import os
from dio import Diagram

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the drawio/ folder
HERE = os.path.dirname(os.path.abspath(__file__))
ENT = json.load(open(os.path.join(HERE, "entities.json"), encoding="utf-8"))


def f(name, typ, pk=False):
    return {"name": name, "type": typ, "pk": pk, "rel": None}


# assistant-service uses JDBC + Flyway (no JPA entities)
ENT.update({
    "KbDocument": {"service": "assistant-service", "table": "kb_documents", "fields": [
        f("id", "bigserial", True), f("title", "varchar(255)"), f("file_name", "varchar(255)"), f("mime_type", "varchar(100)"),
        f("status", "varchar(20)"), f("allowed_roles", "text[]"), f("checksum", "varchar(64)"), f("size_bytes", "bigint"),
        f("chunk_count", "int"), f("created_by", "bigint"), f("created_at", "timestamp")]},
    "KbChunk": {"service": "assistant-service", "table": "kb_chunks", "fields": [
        f("id", "bigserial", True), f("document_id", "bigint"), f("ordinal", "int"), f("heading", "varchar(500)"),
        f("content", "text"), f("embedding", "vector(1024)"), f("created_at", "timestamp")]},
    "AssistantConversation": {"service": "assistant-service", "table": "assistant_conversations", "fields": [
        f("id", "bigserial", True), f("user_id", "bigint"), f("title", "varchar(255)"), f("created_at", "timestamp"), f("updated_at", "timestamp")]},
    "AssistantMessage": {"service": "assistant-service", "table": "assistant_messages", "fields": [
        f("id", "bigserial", True), f("conversation_id", "bigint"), f("role", "varchar(20)"), f("content", "text"),
        f("citations", "jsonb"), f("refused", "boolean"), f("top_score", "double"), f("model", "varchar(100)"),
        f("input_tokens", "int"), f("output_tokens", "int"), f("created_at", "timestamp")]},
    "EvalCase": {"service": "assistant-service", "table": "eval_cases", "fields": [
        f("id", "bigserial", True), f("question", "text"), f("roles", "varchar(255)"), f("expected_document_title", "varchar(255)"),
        f("must_refuse", "boolean"), f("created_at", "timestamp")]},
})

# (col, row) on the layout grid, grouped by business area
POS = {
    "AssistantMessage": (0, 0), "AssistantConversation": (1, 0), "KbChunk": (2, 0), "KbDocument": (3, 0), "EvalCase": (4, 0),
    "NotificationMessage": (5, 0), "FcmToken": (6, 0), "GatewayDevice": (7, 0), "DeviceStatus": (8, 0),
    "CabinetControlLog": (9, 0), "BleSigningKey": (10, 0),
    "RefreshToken": (0, 1), "SocialIdentity": (1, 1), "TechnicianPresence": (2, 1), "DroneTechnicianPresence": (4, 1),
    "StoreLocation": (6, 1), "BleTestGrant": (7, 1), "AccessAttempt": (9, 1), "BoxHardwareStatus": (10, 1),
    "EmailOtp": (0, 2), "AuthAccount": (1, 2), "UserProfile": (3, 2), "Promotion": (5, 2), "PromotionClaim": (4, 2),
    "LockerUnit": (8, 2), "LockerBox": (10, 2), "BoxAccessLog": (11, 2),
    "LoyaltyAccount": (1, 3), "UserBankAccount": (2, 3), "PromotionUsage": (5, 3), "RepairLog": (6, 3), "LockerReport": (7, 3),
    "MaintenanceInspectionLog": (10, 3), "MaintenanceSchedule": (9, 3),
    "Wallet": (1, 4), "PointTransaction": (2, 4), "OrderStatusHistory": (3, 4), "LockerOrder": (4, 4), "OrderDetail": (5, 4),
    "ReportAttachment": (6, 4), "LockerReportRating": (7, 4), "DroneDeliveryRequest": (10, 4),
    "WalletTransaction": (0, 5), "WithdrawalRecord": (1, 5), "PaymentRecord": (2, 5), "OrderRating": (3, 5), "OrderComplaint": (4, 5),
    "DronePickup": (5, 5), "DroneMission": (6, 5), "DroneUnit": (9, 5), "DroneDevice": (10, 5),
    "RefundRecord": (2, 6), "DronePickupOffer": (5, 6), "DroneDeliverySession": (6, 6), "DroneIncidentResolutionProposal": (8, 6),
    "DroneParcelIncident": (7, 6), "DroneMaintenanceLog": (9, 6), "DroneIotLog": (10, 6),
    "DroneLockerCommLog": (6, 7), "DroneIncidentEvidence": (7, 7), "DroneIncidentTimeline": (8, 7),
}
missing = set(ENT) - set(POS)
assert not missing, missing

M, O = "many", "one"   # child side cardinality
# child, fk column on child, parent, child-side cardinality
REL = [
    ("AuthAccount", "user_id", "UserProfile", O), ("RefreshToken", "account_id", "AuthAccount", M),
    ("SocialIdentity", "account_id", "AuthAccount", M),
    ("TechnicianPresence", "user_id", "UserProfile", O), ("DroneTechnicianPresence", "user_id", "UserProfile", O),
    ("NotificationMessage", "user_id", "UserProfile", M), ("FcmToken", "user_id", "UserProfile", M),
    ("AssistantConversation", "user_id", "UserProfile", M), ("AssistantMessage", "conversation_id", "AssistantConversation", M),
    ("KbChunk", "document_id", "KbDocument", M),
    ("UserBankAccount", "user_id", "UserProfile", M), ("Wallet", "user_id", "UserProfile", O),
    ("WalletTransaction", "wallet_id", "Wallet", M), ("WithdrawalRecord", "user_id", "UserProfile", M),
    ("LoyaltyAccount", "user_id", "UserProfile", O), ("PointTransaction", "user_id", "LoyaltyAccount", M),
    ("PointTransaction", "order_id", "LockerOrder", M),
    ("LockerUnit", "store_id", "StoreLocation", M), ("LockerUnit", "assigned_technician_id", "UserProfile", M),
    ("LockerBox", "locker_id", "LockerUnit", M),
    ("GatewayDevice", "locker_id", "LockerUnit", O), ("DeviceStatus", "locker_id", "LockerUnit", M),
    ("CabinetControlLog", "locker_id", "LockerUnit", M), ("BleTestGrant", "locker_id", "LockerUnit", M),
    ("BleTestGrant", "user_id", "UserProfile", M),
    ("BoxHardwareStatus", "box_id", "LockerBox", O), ("AccessAttempt", "box_id", "LockerBox", M),
    ("BoxAccessLog", "box_id", "LockerBox", M), ("BoxAccessLog", "order_id", "LockerOrder", M),
    ("LockerReport", "locker_id", "LockerUnit", M), ("LockerReport", "box_id", "LockerBox", M),
    ("LockerReport", "user_id", "UserProfile", M), ("LockerReport", "order_id", "LockerOrder", M),
    ("LockerReport", "schedule_id", "MaintenanceSchedule", M),
    ("RepairLog", "report_id", "LockerReport", M), ("ReportAttachment", "report_id", "LockerReport", M),
    ("LockerReportRating", "report_id", "LockerReport", O),
    ("MaintenanceSchedule", "locker_id", "LockerUnit", M), ("MaintenanceSchedule", "drone_unit_id", "DroneUnit", M),
    ("MaintenanceInspectionLog", "schedule_id", "MaintenanceSchedule", M),
    ("LockerOrder", "user_id", "UserProfile", M), ("LockerOrder", "locker_id", "LockerUnit", M),
    ("LockerOrder", "send_box_id", "LockerBox", M), ("LockerOrder", "store_id", "StoreLocation", M),
    ("OrderDetail", "order_id", "LockerOrder", M), ("OrderStatusHistory", "order_id", "LockerOrder", M),
    ("OrderRating", "order_id", "LockerOrder", O), ("OrderComplaint", "order_id", "LockerOrder", M),
    ("Promotion", "locker_id", "LockerUnit", M), ("PromotionClaim", "promotion_id", "Promotion", M),
    ("PromotionClaim", "user_id", "UserProfile", M), ("PromotionUsage", "promotion_id", "Promotion", M),
    ("PromotionUsage", "order_id", "LockerOrder", M),
    ("PaymentRecord", "order_id", "LockerOrder", M), ("PaymentRecord", "user_id", "UserProfile", M),
    ("RefundRecord", "payment_id", "PaymentRecord", M),
    ("DroneUnit", "locker_id", "LockerUnit", M), ("DroneDevice", "drone_id", "DroneUnit", O),
    ("DroneIotLog", "drone_id", "DroneUnit", M), ("DroneMaintenanceLog", "drone_unit_id", "DroneUnit", M),
    ("DroneDeliveryRequest", "box_id", "LockerBox", M), ("DroneDeliveryRequest", "drone_unit_id", "DroneUnit", M),
    ("DroneMission", "order_id", "LockerOrder", M), ("DroneMission", "drone_unit_id", "DroneUnit", M),
    ("DronePickup", "order_id", "LockerOrder", O), ("DronePickupOffer", "pickup_id", "DronePickup", M),
    ("DroneParcelIncident", "mission_id", "DroneMission", M),
    ("DroneIncidentEvidence", "incident_id", "DroneParcelIncident", M),
    ("DroneIncidentTimeline", "incident_id", "DroneParcelIncident", M),
    ("DroneIncidentResolutionProposal", "incident_id", "DroneParcelIncident", M),
    ("DroneDeliverySession", "order_id", "LockerOrder", M), ("DroneDeliverySession", "mission_id", "DroneMission", M),
    ("DroneLockerCommLog", "session_id", "DroneDeliverySession", M),
]
for child, col, parent, _ in REL:
    assert any(fl["name"] == col for fl in ENT[child]["fields"]), (child, col)

