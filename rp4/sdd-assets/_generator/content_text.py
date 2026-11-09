"""Hand-written explanations used by build_docx.py (architecture, packages)."""

ARCH_INTRO = (
    "Lock.R is built as a set of Spring Boot microservices behind one API gateway. Every client (mobile app, admin "
    "web and the kiosk on each locker) talks to the backend over HTTPS REST and receives realtime updates "
    "over STOMP / WebSocket. Each service owns its PostgreSQL database; services call each other synchronously with "
    "OpenFeign (internal endpoints) and asynchronously through the RabbitMQ topic exchange laundry.events. Physical "
    "lockers are driven by a Raspberry Pi that exchanges commands and events with iot-service over MQTT. The whole "
    "backend runs with Docker Compose on one Azure VM behind Nginx; the web front-ends are deployed on Cloudflare Workers.")

ARCH_LEGEND = (
    "The table below explains each component of the architecture diagram, grouped by sub-system. In the diagram a "
    "solid arrow is a call, a dashed arrow is its return and a dotted arrow is an asynchronous message (RabbitMQ "
    "event or MQTT).")

# (component, type, description); a list description is rendered as several paragraphs.
ARCH_COMPONENTS = [
    # ---- Client Applications
    ("Client Applications", "Sub-system",
     "Front-end layer through which every actor uses Lock.R. The three clients call the backend over HTTPS "
     "(REST / JSON) through Nginx and receive realtime updates over STOMP / WebSocket."),
    ("Mobile App", "Client module",
     "Flutter application for Android and iOS used by customers, receivers, locker technicians and drone "
     "technicians: send, rental and drone delivery orders, payment, loyalty, order tracking and maintenance "
     "tasks. Uses Firebase Auth for phone / Google sign-in, FCM for push and OpenStreetMap / OSRM for maps."),
    ("Admin Web", "Client module",
     "React single-page application for administrators: dashboard, users, stores, lockers and cabinet control, "
     "maintenance, drones, orders, payments, refunds, promotions, loyalty, business settings and knowledge base."),
    ("Kiosk Screen", "Client module",
     "React web application shown on the touch screen of each cabinet. Customers pick up with PIN / QR, sign in by "
     "QR, send and rent at the locker; it calls the backend (/api/iot/*) and the local API of the Raspberry Pi 4."),
    ("OpenStreetMap / OSRM", "External system (Maps & Routing)",
     "Map tiles and OSRM routing used directly by the client applications to show stores and lockers on the map and "
     "to draw directions and drone routes."),
    # ---- Backend
    ("Backend - Azure VM (Docker Compose)", "Sub-system",
     "Server side of Lock.R. Every backend component runs as a Docker container started by Docker Compose on one "
     "Azure virtual machine; only Nginx is exposed to the Internet."),
    ("Nginx", "Module",
     "Reverse proxy with TLS termination (Let's Encrypt) for api.locker-drone.tech. Forwards HTTPS and WebSocket "
     "traffic from the clients to the API Gateway and returns the responses."),
    ("API Gateway", "Module",
     "Spring Cloud Gateway, the single entry point of the backend. Verifies the JWT, applies role-based access by "
     "path prefix, blocks /internal/**, adds the X-User-Id / X-User-Roles headers and routes each request to the "
     "right microservice."),
    ("Discovery (Eureka)", "Module",
     "Service registry. Every microservice registers itself here; the API Gateway and the OpenFeign clients look up "
     "service instances by name (lb://) instead of fixed addresses."),
    ("Microservices", "Module group",
     ["10 Spring Boot services, each owning its own database and sharing common-lib. They call each other "
      "synchronously with OpenFeign and exchange events asynchronously through RabbitMQ:",
      "- auth-service: password / OTP / Firebase / kiosk-QR sign-in, admin 2FA, JWT and refresh tokens.",
      "- user-service: user profiles, roles and status; signed Cloudinary upload parameters.",
      "- order-service: send, rental and drone delivery orders, pricing, promotions, drone missions, incidents, "
      "revenue reports and scheduled jobs.",
      "- locker-service: lockers, boxes, tickets, inspections, technicians, drones and drone devices.",
      "- payment-service: SePay payments and refunds.",
      "- notification-service: in-app notifications, FCM push, email and the STOMP realtime channel.",
      "- iot-service: MQTT bridge to the cabinets (commands, heartbeats, door states, PIN / QR verification).",
      "- store-service: stores hosting the lockers and nearby search.",
      "- loyalty-service: points, tiers, redemption and voucher exchange.",
      "- assistant-service: RAG assistant answering from the knowledge base."]),
    ("MQTT Broker", "Module (message broker)",
     "Mosquitto broker that connects the backend with the IoT devices: commands, heartbeats and results between "
     "iot-service and the cabinets, signed telemetry and delivery commands between order-service and the drones."),
    ("PostgreSQL", "Data store",
     "PostgreSQL 16 server holding one database per service (database-per-service); schemas are managed by Flyway "
     "migrations."),
    ("pgvector", "Data store",
     "assistant-db, a PostgreSQL database with the pgvector extension that stores knowledge-base chunks and their "
     "1024-dimension embeddings for semantic search."),
    ("RabbitMQ", "Module (message broker)",
     "Topic exchange laundry.events. Services publish domain events (e.g. order paid, order completed) and consume "
     "them asynchronously in payment, loyalty and notification queues."),
    # ---- IoT Devices
    ("IoT Devices", "Sub-system",
     "Physical devices in the field: the smart locker cabinets and the delivery drones. They reach the backend only "
     "through the MQTT broker."),
    ("Smart Locker Cabinet", "Sub-system",
     "A locker with 7 compartments and a motorised sliding lid on top for drone drop-off, controlled by a "
     "Raspberry Pi 4."),
    ("Raspberry Pi 4", "Hardware module (cabinet controller)",
     "Python controller of the cabinet. Receives open / lid / setup commands over MQTT and sends heartbeats and "
     "results; drives the relays through GPIO and reads lock feedback; drives the lid motors with PUL / DIR pulses; "
     "serves the local API used by the Kiosk Screen."),
    ("Relay & 7 Locks", "Hardware",
     "Relay board that switches the 7 electronic locks of the compartments; the lock feedback signal reports whether "
     "each door is open or closed."),
    ("Lid Motors (TB6600)", "Hardware",
     "Stepper motors driven by TB6600 drivers that open and close the sliding lid, with limit switches at both ends."),
    ("Drone", "Sub-system",
     "Delivery drone that carries a parcel to a destination cabinet and releases it through the open lid."),
    ("Raspberry Pi 5", "Hardware module (drone controller)",
     "Companion computer of the drone. Reads MAVLink from the Pixhawk (read-only), publishes HMAC-signed telemetry "
     "and delivery events over MQTT, follows delivery commands from the backend, detects ArUco markers in the camera "
     "frames and triggers the drop servo with PWM."),
    ("Pixhawk 6C (ArduPilot)", "Hardware (flight controller)",
     "Autopilot that flies the drone and reports position, altitude, speed, battery and flight mode over MAVLink."),
    ("Pi Camera", "Hardware",
     "CSI camera that streams frames to the Raspberry Pi 5 for ArUco marker detection above the target cabinet and "
     "for the live view."),
    ("Drop Servo (MG996R)", "Hardware",
     "Servo latch holding the parcel; the Raspberry Pi 5 releases it with a PWM signal once the drone is above the "
     "open lid."),
    # ---- External systems
    ("Claude", "External system (AI Services)",
     "Anthropic large language model called by assistant-service to generate answers with citations from the "
     "retrieved knowledge-base chunks."),
    ("Voyage AI", "External system (AI Services)",
     "Embedding API that turns knowledge-base chunks and user questions into 1024-dimension vectors stored and "
     "searched in pgvector."),
    ("Firebase", "External system (Authentication & Notification)",
     "Firebase Auth for phone OTP and Google sign-in (tokens verified by auth-service) and Firebase Cloud Messaging "
     "for push notifications sent by notification-service."),
    ("SMTP", "External system (Authentication & Notification)",
     "Mail server used to send email OTP and notification emails, including pickup information for receivers "
     "without an account."),
    ("Cloudinary", "External system (File Storage)",
     "Image storage. Clients upload avatars, store, locker, parcel and incident photos directly with signed upload "
     "parameters issued by the backend."),
    ("SePay", "External system (Payment Gateway)",
     "VietQR bank transfer gateway. payment-service creates the QR payment and SePay confirms it through a webhook."),
    ("Open-Meteo", "External system (Weather API)",
     "Weather API that order-service queries (wind, rain) to check whether a drone flight is safe before booking and "
     "dispatch."),
]

SERVICE_DESC = {
    "auth-service": "Authentication and token issuing.",
    "user-service": "User profiles, roles and media signatures.",
    "order-service": "Orders, promotions, drone delivery and reports.",
    "locker-service": "Lockers, boxes, tickets, inspections and drones.",
    "payment-service": "Payments and refunds.",
    "notification-service": "Notifications, push and realtime messaging.",
    "iot-service": "MQTT bridge and access control of the lockers.",
    "store-service": "Stores and nearby search.",
    "loyalty-service": "Points, tiers and voucher exchange.",
    "assistant-service": "AI assistant with retrieval-augmented generation.",
}

PKG_DESC = {
    "controller": "REST controllers (@RestController). Receive requests routed by the gateway, read the X-User-Id / X-User-Roles headers, validate the input and wrap results in ApiResponse.",
    "dto": "Request and response records exchanged with clients and other services.",
    "dto.admin": "Response DTOs used by the admin web lists and reports.",
    "dto.internal": "DTOs of the /internal/** API that only other services call.",
    "service": "Business logic (@Service / @Component): use cases, business-rule checks, transactions, scheduled jobs and publishing of domain events.",
    "client": "OpenFeign clients that call other services through Eureka on their /internal/** endpoints.",
    "settings": "Rules and SettingsCatalog of the service: business settings editable on the admin web (common-lib BusinessSettings).",
    "model": "JPA entities mapped to the tables of the service database, and entity listeners that publish change events.",
    "repository": "Spring Data JPA repositories: derived queries, custom JPQL, pessimistic locks.",
    "config": "Spring configuration: RabbitMQ exchange / queues / bindings, security, Firebase, WebSocket.",
    "email": "SMTP e-mail sender used for OTP codes.",
    "channel": "SMS and e-mail channels (Twilio, eSMS, logging fallback) used for pickup codes of guests.",
    "chat": "Question answering: AssistantService and the conversation repository (JDBC).",
    "knowledge": "Knowledge base: documents, chunks, document parser, text chunker and background indexer.",
    "query": "Question preparation: Vietnamese normalisation and order intent detection.",
    "eval": "Evaluation cases used to measure retrieval quality.",
    "orders": "Feign clients and formatter that load the asker's own orders as answer context.",
    "provider": "Adapters for external AI providers: Claude answer generator, Voyage embeddings, diacritics restorer.",
}

COMMON_LIB = [
    ("config", "Flyway repair configuration shared by all services."),
    ("dto", "ApiResponse, ApiError, PageResponse, IdResponse and summaries (UserSummary, OrderSummary, LockerBoxSummary)."),
    ("event", "DomainEvent, DomainEventNames (exchange laundry.events and routing keys) and change-event helpers."),
    ("exception", "BusinessException, NotFoundException and GlobalExceptionHandler (uniform error body)."),
    ("i18n", "MessageService for Vietnamese / English messages."),
    ("media", "CloudinaryMediaStorage: signed upload parameters and verification of uploaded images."),
    ("security", "UserRoles constants and SecuritySecrets checks."),
    ("settings", "BusinessSettings framework: catalog, JDBC store with audit, admin / public controller."),
    ("util", "AfterCommit, BusinessTime (Asia/Ho_Chi_Minh) and CodeGenerator."),
    ("web", "CorrelationIdFilter for request tracing."),
]

ADMIN_WEB_PKGS = [
    ("routes", "app-router, protected-route (role check) and routes-config of every admin page (lazy loaded)."),
    ("pages", "Screens: auth (2FA login) and Admin/* feature folders - dashboard, revenue, users, technicians, stores, lockers, cabinet-control, maintenance, drones, drone-orders, drone-incidents, drone-logs, orders, payments, refunds, promotions, loyalty, feedback, notifications, scheduler, services, settings, knowledge."),
    ("components", "ui (shadcn-style primitives: button, dialog, table, form...) and shared (data-table, layout, page-header, media, status tabs, charts)."),
    ("stores", "Redux store and RTK Query: baseAPi.ts (auth header, refresh, error handling), apis (adminApi, authApi, loyaltyApi, notificationApi, media) and store.ts."),
    ("hooks", "useAdminRealtimeSync (STOMP -> cache invalidation), useWebSocket, useImageUpload, use-toast."),
    ("context", "AuthContext (session and role), sidebar and theme contexts."),
    ("lib", "Helpers: admin realtime tag map, Cloudinary upload, date/time, locker layout helper, report formatting, validation."),
    ("schemas", "Zod schemas for admin forms."),
    ("types", "TypeScript types of API resources."),
    ("constants", "API paths, roles, sidebar menu, order setting keys."),
    ("utils", "API helpers, auth session storage, i18n."),
]

MOBILE_PKGS = [
    ("main.dart", "Application entry: Firebase initialisation and the root providers, wired through the per-feature *_injection factories that create data sources, repositories and use cases."),
    ("features", "One folder per business feature: assistant, auth, delegations, drone_delivery, drone_mission, drone_telemetry, home, locker, locker_ops, maintenance (locker technician), notifications, orders, payment, profile, promotions, qr_login, stores, transactions, vouchers."),
    ("core/network", "dio ApiClient, AuthInterceptor (token refresh), gateway client."),
    ("core/routing", "go_router configuration, role-based routes, main navigation wrapper, notification deep links."),
    ("core/services", "Session and token storage, Firebase auth / messaging, BLE open service, biometric, app event bus."),
    ("core/config, constants, theme, l10n", "Environment config, business config loaded from /api/settings/*/public, colours, strings, themes, locale provider and language switch."),
    ("core/domain, enums, errors, utils, media, presentation", "Shared entities, enums, failures, formatters, media upload and common pages."),
    ("shared", "icons, utils and widgets reused by the features."),
    ("l10n", "Localisation resources: ARB files and the generated AppLocalizations."),
]

MOBILE_FEATURE_PKGS = [
    ("presentation", "pages (screens), widgets and providers (Riverpod / provider / bloc state)."),
    ("application", "use_cases: one class per user action (e.g. LoginUseCase, GetMyOrdersUseCase)."),
    ("domain", "entities and repository interfaces of the feature, independent of the API."),
    ("infrastructure", "data_sources (remote calls through ApiClient), models (JSON serializable, *.g.dart) and repository implementations."),
]

BACKEND_EDGE = [
    ("api-gateway", "Spring Cloud Gateway: JWT validation, RBAC by path, routing, correlation id."),
    ("discovery-server", "Eureka service registry."),
]

IOT_PKGS = [
    ("main.py", "Starts the controller: loads config, connects MQTT, starts heartbeat, discovery / setup handlers, BLE service and local API."),
    ("services", "locker_service (open / lid / sync commands), heartbeat_service, discovery_service and setup_handler (provisioning), ble_service / ble_gatt_service / ble_open_token (offline open), control_log."),
    ("infracstructure", "mqtt_client (paho-mqtt, topics cabinet/* and iot/*), serial_manager (RS485 to Arduino), database (local PostgreSQL log store, psycopg2), cabinet_state, config_api and service_panel (local FastAPI HTTP API), wifi."),
    ("hardware", "factory selecting the driver, gpio_locker / rpi_locker (relays and reed sensors through gpiod), lid_controller (sliding lid), gpio_pins."),
    ("domain", "Models and enums of boxes, commands and results."),
    ("config", "settings (environment), wiring_default.json and hardware_config."),
    ("ui", "Kiosk React app: screens (KioskScreen, AdminScreen), components (virtual keyboard, animations) and api.js calling the backend and the Pi."),
    ("arduino/locker_controller", "Arduino sketch driving relays and reading sensors over RS485."),
    ("drone-iot/lockr_drone", "Companion computer on the drone: reads MAVLink and publishes signed telemetry to MQTT."),
]

DB_INTRO = (
    "Lock.R follows the database-per-service pattern: each microservice owns one PostgreSQL 16 database whose schema "
    "is created by Flyway migrations and validated by Hibernate at start-up; the assistant uses a separate pgvector "
    "database. Foreign keys exist only between tables of the same database. A column that refers to a row of another "
    "service (for example orders.user_id -> user_profiles) is a logical reference: it is checked by the owning service "
    "through Feign calls and is shown as (FK) in the diagrams. The figures list the primary key, the foreign keys and the "
    "first columns of each table; very wide tables (orders, drone_parcel_incidents, drone_missions) show the number of "
    "remaining columns. Crow's-foot notation: | exactly one, o| zero or one, o< zero or many.")
