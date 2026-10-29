"""Hand-written explanations used by build_docx.py (architecture, packages)."""

ARCH_INTRO = (
    "Lock.R is built as a set of Spring Boot microservices behind one API gateway. Every client (mobile app, admin "
    "web and the kiosk on each locker) talks to the backend over HTTPS REST and receives realtime updates "
    "over STOMP / WebSocket. Each service owns its PostgreSQL database; services call each other synchronously with "
    "OpenFeign (internal endpoints) and asynchronously through the RabbitMQ topic exchange laundry.events. Physical "
    "lockers are driven by a Raspberry Pi that exchanges commands and events with iot-service over MQTT. The whole "
    "backend runs with Docker Compose on one Azure VM behind Nginx; the web front-ends are deployed on Cloudflare Workers.")

ARCH_COMPONENTS = [
    ("Mobile App", "Flutter application for customers, receivers, locker technicians and drone technicians (Android and iOS). Uses dio for REST, STOMP for realtime events, Firebase Auth for phone / Google sign-in and FCM for push."),
    ("Admin Web", "React 19 + Vite + RTK Query single-page app for administrators: dashboard, users, stores, lockers, cabinet control, maintenance, drones, orders, payments, refunds, promotions, loyalty, settings and knowledge base."),
    ("Kiosk UI", "React web app shown on the touch screen of each locker. Customers pick up with PIN / QR, sign in by QR, send and rent; it calls /api/iot/* and the local API of the Pi."),
    ("Nginx", "TLS termination (Let's Encrypt) for api.locker-drone.tech; forwards HTTP and WebSocket traffic to the API gateway and MQTT over WSS to the broker."),
    ("API Gateway", "Spring Cloud Gateway. Verifies the JWT, applies role-based access by path prefix, blocks /internal/**, adds X-User-Id / X-Account-Id / X-User-Roles headers and routes to services through Eureka (lb://)."),
    ("Discovery Server", "Eureka registry where every service registers and the gateway / Feign clients resolve service instances."),
    ("auth-service", "Credentials, password / OTP / Firebase / kiosk-QR sign-in, admin 2FA, JWT and refresh tokens."),
    ("user-service", "User profiles, roles and status; admin user management; signed Cloudinary upload parameters."),
    ("order-service", "SEND / RENTAL / DRONE_DELIVERY orders, pricing, vouchers and points, ratings and complaints, drone missions, pickups, telemetry, incidents, revenue reports and scheduled jobs."),
    ("locker-service", "Lockers, boxes and layouts, tickets and repair logs, periodic inspections, technician presence, drones and drone devices."),
    ("payment-service", "Payments (SePay VietQR, wallet), SePay webhook, refunds, wallet ledger and withdrawals."),
    ("notification-service", "In-app notifications, FCM push, STOMP /ws broker, SMS / email to receivers without an account."),
    ("iot-service", "MQTT bridge to lockers: open / lid / setup commands, heartbeats and door states, PIN / QR verification, controller provisioning, BLE open tokens."),
    ("store-service", "Stores (locations hosting lockers) and nearby search."),
    ("loyalty-service", "Loyalty accounts, points, tiers, redemption and voucher exchange."),
    ("assistant-service", "RAG assistant: knowledge base indexing, vector search on pgvector, answers from Claude with citations."),
    ("common-lib", "Shared library: ApiResponse / PageResponse DTOs, domain events, exceptions, business settings framework, Cloudinary media, security and utilities."),
    ("PostgreSQL / pgvector", "One PostgreSQL 16 database per service (Flyway migrations, ddl validate); a separate pgvector database for the assistant."),
    ("RabbitMQ", "Topic exchange laundry.events with queues order.payment.events, loyalty.order.events and notification.events."),
    ("MQTT Broker", "Mosquitto broker for cabinet/{lockerId}/command/*, heartbeat, status and iot/{mac}/* topics, and drone telemetry."),
    ("Raspberry Pi Controller", "Python controller in each locker: drives relays, door sensors and the sliding lid through GPIO / Arduino RS485, sends heartbeats and results, verifies BLE tokens offline."),
    ("External services", "Firebase (Auth, FCM), SePay (VietQR + webhook), Cloudinary (images), SMTP and Twilio (OTP, pickup codes), Anthropic Claude and Voyage AI (assistant), OpenStreetMap / OSRM (maps), Open-Meteo (flight weather)."),
]

SERVICE_DESC = {
    "auth-service": "Authentication and token issuing.",
    "user-service": "User profiles, roles and media signatures.",
    "order-service": "Orders, promotions, drone delivery and reports.",
    "locker-service": "Lockers, boxes, tickets, inspections and drones.",
    "payment-service": "Payments, refunds, wallet and withdrawals.",
    "notification-service": "Notifications, push and realtime messaging.",
    "iot-service": "MQTT bridge and access control of the lockers.",
    "store-service": "Stores and nearby search.",
    "loyalty-service": "Points, tiers and voucher exchange.",
    "assistant-service": "AI assistant with retrieval-augmented generation.",
}

PKG_DESC = {
    "controller": "REST controllers (@RestController). Receive requests routed by the gateway, read the X-User-Id / X-User-Roles headers, validate the input and wrap results in ApiResponse.",
    "dto": "Request and response records exchanged with clients and other services.",
    "admin": "Response DTOs used by the admin web lists and reports.",
    "internal": "DTOs of the /internal/** API that only other services call.",
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
    ("stores", "Redux store and RTK Query: baseApi (auth header, refresh, error handling) and apis (adminApi, authApi, loyaltyApi, notificationApi, media)."),
    ("hooks", "useAdminRealtimeSync (STOMP -> cache invalidation), useWebSocket, useImageUpload, use-toast."),
    ("context", "AuthContext (session and role), sidebar and theme contexts."),
    ("lib", "Helpers: admin realtime tag map, Cloudinary upload, date/time, locker layout helper, report formatting, validation."),
    ("schemas", "Zod schemas for admin forms."),
    ("types", "TypeScript types of API resources."),
    ("constants", "API paths, roles, sidebar menu, order setting keys."),
    ("utils", "API helpers, auth session storage, i18n."),
]

MOBILE_PKGS = [
    ("main.dart / injection_container", "Application entry, Firebase initialisation and provider factories that wire data sources, repositories and use cases (per-feature *_injection providers)."),
    ("features", "One folder per business feature: auth, home, stores, locker, orders, payment, wallet, transactions, promotions, vouchers, delegations, qr_login, notifications, profile, subscription, drone_delivery, drone_mission, drone_telemetry, maintenance (locker technician), locker_ops, assistant."),
    ("core/network", "dio ApiClient, AuthInterceptor (token refresh), gateway client."),
    ("core/routing", "go_router configuration, role-based routes, main navigation wrapper, notification deep links."),
    ("core/services", "Session and token storage, Firebase auth / messaging, BLE open service, biometric, app event bus."),
    ("core/config, constants, theme", "Environment config, business config loaded from /api/settings/*/public, colours, strings, themes."),
    ("core/domain, enums, errors, utils, media, presentation", "Shared entities, enums, failures, formatters, media upload and common pages."),
    ("shared", "Reusable widgets, icons and utilities."),
]

MOBILE_FEATURE_PKGS = [
    ("presentation", "pages (screens), widgets and providers (Riverpod / provider / bloc state)."),
    ("application", "use_cases: one class per user action (e.g. LoginUseCase, GetMyOrdersUseCase)."),
    ("domain", "entities and repository interfaces of the feature, independent of the API."),
    ("infrastructure", "data_sources (remote calls through ApiClient), models (JSON serializable, *.g.dart) and repository implementations."),
]

IOT_PKGS = [
    ("main.py", "Starts the controller: loads config, connects MQTT, starts heartbeat, discovery / setup handlers, BLE service and local API."),
    ("services", "locker_service (open / lid / sync commands), heartbeat_service, discovery_service and setup_handler (provisioning), ble_service / ble_gatt_service / ble_open_token (offline open), control_log."),
    ("infracstructure", "mqtt_client (paho-mqtt, topics cabinet/* and iot/*), serial_manager (RS485 to Arduino), database (local PostgreSQL log store, psycopg2), cabinet_state, config_api and service_panel (local FastAPI HTTP API), wifi."),
    ("hardware", "factory selecting the driver, gpio_locker / rpi_locker (relays and reed sensors through gpiod), lid_controller (sliding lid), gpio_pins."),
    ("domain", "Models and enums of boxes, commands and results."),
    ("config", "settings (environment), wiring_default.json and hardware_config."),
    ("ui (Kiosk React)", "KioskScreen and AdminScreen, components (virtual keyboard, animations) and api.js calling the backend and the Pi."),
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
