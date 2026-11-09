"""Committed functional test cases (BM04 §6) mapped to the automated test that already runs in CI.

Source: tag review-2 of LockR-Tech/backend (8c60a0d). Backend CI = .github/workflows/backend-ci.yml (`mvn -B test`
on every pull request); every class below is a JUnit test of that build. Mobile CI (`flutter test`) and the
frontend / iot repos add nothing here: the frontend has no tests and iot has no CI workflow (BM02 SR-20).

Each entry is 'TestClass#method' – the test whose assertions check that acceptance criterion or transition –
or None when no automated test checks it yet (manual in Report 5 until automated; see RF items in BM04 §9).
One automated test may back several committed test cases; each committed case is still counted once.
Reviewed by reading the test bodies on 09/11/2026.
"""

# Feature tests: TC-Fxx-01 main flow, -02 data / business rule, -03 exception or permission (guide §9.3).
FEATURE_CI = {
    'F-01': ['AuthServiceAdminAccessTest#adminStillGetsTokenAfterTwoFactor',
             'EmailOtpServiceTest#defaultOtpHasSixDigitsAndExpiresInFiveMinutes',
             'AuthServiceAdminAccessTest#adminCannotGetTokenFromPasswordOnlyLogin'],
    'F-02': ['OrderServiceBenefitsTest#sendOrderWithVoucherAndPointsChargesOnlyTheRest',
             'LockerServiceTicketRoutingTest#reserveBoxLocksRowAndRejectsInactiveCell',
             None],  # unpaid locker order cancelled after 15 min and box freed: only the setting is tested
    'F-03': ['PaymentServiceMoneyRulesTest#simulatedTransferCompletesThePendingPaymentLikeARealOne',
             'OrderPaymentEventListenerTest#underpaidLockerOrderStaysUnpaidUntilTheRestArrives',
             'PaymentServiceMoneyRulesTest#sameBankTransactionDeliveredTwiceIsRecordedOnce'],
    'F-04': ['OrderServiceSendFlowTest#confirmSendAfterOpeningSwapsDropPinForPickupPin',
             'OrderAccessPolicyTest#unpaidOrderAwaitingDropCannotOpen',
             'OrderServiceSendFlowTest#confirmSendRejectedWhenBoxWasNeverOpened'],
    'F-05': ['IotServiceTest#unlockWithCodeCompletesOrderWhenPickingUpFromStoring',
             'IotServiceTest#unlockWithCodeRejectsCodeAtWrongLocker',
             'IotServiceTest#lockoutAttemptsAndDurationFollowAdminSettings'],
    'F-06': ['OrderServiceRentalPaymentTest#confirmPaidRentalStartsDeadlineFromConfirmTime',
             'IotServiceTest#unlockWithCodeDoesNotCompleteRentalOnReopen',
             'OrderServiceRentalPaymentTest#confirmRejectsUnpaidRental'],
    'F-07': ['BleOrderServiceTest#ownerGetsASignedDropTokenForTheBoxOfTheOrder',
             'BleOrderServiceTest#openedDropMovesTheOrderOnceEvenWhenThePiResendsTheEvent',
             'BleOrderAccessServiceTest#strangerIsForbiddenAndMissingOrderIsNotFound'],
    'F-08': ['OrderServiceRentalPaymentTest#overdueRentalIsChargedAtLeastTheExtensionRate',
             'OrderServiceRentalPaymentTest#sendOvertimeCapDoesNotGrowWithEachAssessment',
             'OrderAccessPolicyTest#sendPickupWithUnpaidOvertimeFeeIsBlocked'],
    'F-09': ['LockerMqttServiceTest#cabinetResultCompletesPendingCommand',
             'IotServiceForceUnlockTest#timeoutIsNotReportedAsOpened',
             'IotServiceForceUnlockTest#jammedDoorIsReportedWithHardwareMessage'],
    'F-10': ['DroneHomePickupFlowPostgresTest#quoteAndBookingPickTheLockerNearestToTheSender',
             'DroneHomePickupFlowPostgresTest#bookingEnforcesRequiredFieldsRangeAndWeightLimit',
             'DroneOrderBookingBenefitsTest#unsafeWeatherBlocksBookingBeforeDestinationCellIsReserved'],
    'F-11': ['DroneOrderMaintenanceServiceTest#launchMarksMissionLaunchingAndRequestsDroneStateChange',
             'DroneSourceLockerSelectorTest#onlyIdleActiveDronesWithKnownSufficientBatteryCanServeANewPickup',
             'DroneOrderMaintenanceServiceTest#launchRejectsReadyMissionWithoutLoadingAudit'],
    'F-12': ['DroneLockerCommunicationServiceTest#fullHandshakeEndsReadyForPickupOnlyAfterTheMatchingCloseResult',
             'DroneTelemetryServiceTest#stagesFollowThePositionAlongTheRoute',
             'DroneLockerCommunicationServiceTest#servoFailureClosesTheLidWithoutDeliveringTheOrder'],
    'F-13': ['LockerServiceReportPhotoTest#reportUsesJwtUserAndAttachesReporterPhotos',
             'OrderServiceBoxIncidentTest#reportingAFaultOnAStoredOrderPausesFeesButKeepsAccess',
             'ReportAttachmentServiceTest#enforcesReporterStageAndRequestLimits'],
    'F-14': ['LockerServiceSlaAndQueueTest#assignedTechnicianExtendsWithinLimitAndCountIsRecorded',
             'LockerServiceSlaAndQueueTest#extensionCountIsCappedByAdminSetting',
             'LockerServiceReportPhotoTest#claimBlockThresholdFollowsAdminSetting'],
    'F-15': ['DroneParcelIncidentServiceTest#paidCompensationResolvesTheIncidentAndMarksTheParcelCompensated',
             'DroneParcelIncidentServiceTest#recoverySubmissionRequiresRealPhotoEvidence',
             'DroneParcelIncidentServiceTest#receiverCannotAnswerTheProposalForTheSender'],
    'F-16': ['ClaudeAnswerGeneratorTest#sendsChunksAsCitableDocumentsAndMapsCitationsBack',
             'OrderContextServiceTest#loadsOnlyTheCallersOrdersAndLooksUpLockers',
             'OrderContextServiceTest#mentionedOrderCodeThatIsNotTheCallersIsReportedAsNotFound'],
    'F-17': ['DroneHomePickupFlowPostgresTest#paymentOffersThePickupToTheNearestIdleTechnicianOnDuty',
             'DroneHomePickupFlowPostgresTest#decliningOrIgnoringAnOfferPassesItToTheNextNearestTechnician',
             'DroneHomePickupFlowPostgresTest#staleLocationIsOnlyAFallbackAndOffDutyIsNeverOffered'],
    'F-18': [None,  # creating a schedule (locker or drone; drone set to MAINTENANCE) has no test yet
             'LockerServiceInspectionTest#droneTechnicianCannotReadOrCompleteLockerSchedule',
             'JwtGatewayFilterTest#scheduleEditsNeedAdminButTechniciansCompleteInspections'],
    'F-19': ['LockerServiceInspectionTest#allItemsPassingAdvancesTheDueDate',
             'LockerServiceInspectionTest#itemsMustMatchTheSchedulesChecklist',
             'LockerServiceInspectionTest#onlyTheAssignedTechnicianOrAnAdminCompletes'],
    'F-20': ['RevenueReportServiceTest#summaryUsesCollectedMoneyAndLoadsPaymentsOnceWhenWindowsOverlap',
             'RevenueReportServiceTest#entriesAddUpToSummaryCards',
             'JwtGatewayFilterTest#revenueReportsRequireAdminRole'],
}

JOURNEY = 'DroneHomePickupFlowPostgresTest#fullJourneyFromHomePickupToTheReceiverLocker'

# State transitions (state machines in docs/rp3/srs-assets/drawio): workflow, entity, owner, transition, test.
# Groups and owners follow STATE_TESTS in build_bm04.py.
STATE_CI = [
    # WF-01 – drone delivery stage (06c), main flight and home pickup
    ('WF-01', 'Stage', 'Vi', 'create → AWAITING_DISPATCH',
     'DroneHomePickupFlowPostgresTest#quoteAndBookingPickTheLockerNearestToTheSender'),
    ('WF-01', 'Stage', 'Vi', 'AWAITING_DISPATCH → PICKUP_ASSIGNED',
     'DroneHomePickupFlowPostgresTest#paymentOffersThePickupToTheNearestIdleTechnicianOnDuty'),
    ('WF-01', 'Stage', 'Vi', 'PICKUP_ASSIGNED → PICKED_UP', JOURNEY),
    ('WF-01', 'Stage', 'Vi', 'PICKED_UP → ACCEPTED', JOURNEY),
    ('WF-01', 'Stage', 'Vi', 'ACCEPTED → LAUNCHING', JOURNEY),
    ('WF-01', 'Stage', 'Vi', 'LAUNCHING → DEPARTED',
     'DroneTelemetryServiceTest#takeoffMovesAStandardMissionFromLaunchingToDeparted'),
    ('WF-01', 'Stage', 'Vi', 'DEPARTED → EN_ROUTE', 'DroneTelemetryServiceTest#stagesFollowThePositionAlongTheRoute'),
    ('WF-01', 'Stage', 'Vi', 'EN_ROUTE → APPROACHING', 'DroneTelemetryServiceTest#stagesFollowThePositionAlongTheRoute'),
    ('WF-01', 'Stage', 'Vi', 'APPROACHING → ARRIVED', 'DroneTelemetryServiceTest#stagesFollowThePositionAlongTheRoute'),
    ('WF-01', 'Stage', 'Vi', 'ARRIVED → READY_FOR_PICKUP',
     'DroneLockerCommunicationServiceTest#fullHandshakeEndsReadyForPickupOnlyAfterTheMatchingCloseResult'),
    ('WF-01', 'Stage', 'Vi', 'READY_FOR_PICKUP → COMPLETED',
     'OrderServiceDroneDeliveryTest#completingPickupEndsTheDeliveryStageToo'),
    ('WF-01', 'Stage', 'Vi', 'READY_FOR_PICKUP → EXPIRED', None),
    ('WF-01', 'Stage', 'Vi', 'EXPIRED → COMPLETED', None),
    ('WF-01', 'Stage', 'Vi', 'AWAITING_DISPATCH → CANCELED',
     'DroneOrderTimeoutSweeperTest#cancelsUnpaidOrderPastTheLimitAndReleasesBothCellsWithoutARefund'),
    ('WF-01', 'Stage', 'Vi', 'PICKUP_ASSIGNED → CANCELED',
     'DroneHomePickupFlowPostgresTest#senderMayCancelUntilTheParcelIsPickedUpAndTheTechnicianIsFreed'),
    # WF-01 – drone delivery stage, parcel drop and recovery
    ('WF-01', 'Stage', 'Nhã', 'ACCEPTED → CANCELED (before launch)',
     'DroneOrderMaintenanceServiceTest#cancelStoresReasonAndNoteThenReleasesReservedBox'),
    ('WF-01', 'Stage', 'Nhã', 'in delivery → FAILED',
     'DroneDeliveryFailureFlowPostgresTest#blockedOrderIsClosedAsNotCompletedAfterTheDeadlineAndRefunded'),
    ('WF-01', 'Stage', 'Nhã', 'in flight → DROP_REPORTED',
     'DroneParcelIncidentServiceTest#dropIsRecordedEvenWhenLockerTicketsCannotBeCreated'),
    # WF-01 – drone (06i)
    ('WF-01', 'Drone', 'Huy', 'IDLE → RESERVED (order accepted)', JOURNEY),
    ('WF-01', 'Drone', 'Huy', 'RESERVED → IN_FLIGHT (launch)', JOURNEY),
    ('WF-01', 'Drone', 'Huy', 'IN_FLIGHT → IDLE (mission done)',
     'DroneMissionReconcilerTest#closesLaunchedMissionOfCompletedOrderAndReturnsDroneToIdle'),
    ('WF-01', 'Drone', 'Huy', 'on mission → FAULT',
     'DroneOrderMaintenanceServiceTest#cancelBecauseTheDroneIsFaultyMarksItFaultInsteadOfIdle'),
    # WF-01 – order (06-1), drone delivery path
    ('WF-01', 'Order', 'Nhã', 'create drone order → AWAITING_DISPATCH',
     'DroneHomePickupFlowPostgresTest#sameIdempotencyKeyReturnsTheSameOrderWithoutReservingAgain'),
    ('WF-01', 'Order', 'Nhã', 'AWAITING_DISPATCH → STORING (parcel in cell)', JOURNEY),
    ('WF-01', 'Order', 'Nhã', 'AWAITING_DISPATCH → CANCELED (failed / no technician)',
     'DroneOrderTimeoutSweeperTest#paidOrderNoTechnicianAcceptedEndsAsDeliveryNotCompletedAndIsRefunded'),
    # WF-02 – order (06-1), locker path
    ('WF-02', 'Order', 'Bình', 'create rental → INITIALIZED',
     'OrderServiceRentalPaymentTest#createRentalKeepsDeadlineEmptyUntilCustomerActuallyStartsRental'),
    ('WF-02', 'Order', 'Bình', 'INITIALIZED → STORING (pay & drop)',
     'OrderServiceSendFlowTest#confirmSendAfterOpeningSwapsDropPinForPickupPin'),
    ('WF-02', 'Order', 'Bình', 'INITIALIZED → CANCELED', 'OrderServiceBenefitsTest#cancelingReturnsVoucherAndPoints'),
    ('WF-02', 'Order', 'Bình', 'STORING → COMPLETED',
     'OrderServiceHandoverAndCompletionTest#handoverWithPickupPinCompletesAndPublishesCompletionOnce'),
    ('WF-02', 'Order', 'Bình', 'STORING → EXPIRED', 'OrderServiceBenefitsTest#adminExpireMovesOrderToStorageAndReleasesCell'),
    ('WF-02', 'Order', 'Bình', 'EXPIRED → COMPLETED (pay fee & collect)',
     'StorageHandoverServiceTest#collectedOutstandingIsWrittenToHistoryAndRecord'),
    # WF-02 – locker box (06g), order path
    ('WF-02', 'Box', 'Huy', 'add cell → AVAILABLE', 'LockerServiceBoxBatchTest#createBox_Success_BroadcastsLayoutUpdate'),
    ('WF-02', 'Box', 'Huy', 'AVAILABLE → RESERVED', 'LockerServiceTicketRoutingTest#reserveBoxLocksRowAndRejectsInactiveCell'),
    ('WF-02', 'Box', 'Huy', 'RESERVED → OCCUPIED', JOURNEY),
    ('WF-02', 'Box', 'Huy', 'RESERVED → AVAILABLE (order canceled)',
     'OrderServiceDroneDeliveryTest#cancelDroneDeliveryReleasesReservedBox'),
    ('WF-02', 'Box', 'Huy', 'OCCUPIED → AVAILABLE (order closed)',
     'OrderServiceBenefitsTest#adminExpireMovesOrderToStorageAndReleasesCell'),
    # WF-03 – locker box, incident path
    ('WF-03', 'Box', 'Bình', 'AVAILABLE → PENDING_CHECK',
     'LockerServiceTicketRoutingTest#reportingAnEmptyBoxFromTheLockerScreenTakesItOutOfService'),
    ('WF-03', 'Box', 'Bình', 'OCCUPIED → PENDING_CHECK',
     'LockerServiceTicketRoutingTest#customerFaultIsRoutedToTheLockersTechnicianAndRemembersTheOrderHoldingTheBox'),
    ('WF-03', 'Box', 'Bình', 'PENDING_CHECK → FAULT (confirmed)', None),
    ('WF-03', 'Box', 'Bình', 'PENDING_CHECK → previous (rejected)',
     'LockerServiceTicketRoutingTest#rejectingATicketReturnsTheBoxAndResumesTheOrder'),
    ('WF-03', 'Box', 'Bình', 'FAULT → previous (resolved)',
     'LockerServiceTicketRoutingTest#resolvingReturnsTheBoxToWhatItWasBeforeTheFault'),
    # WF-03 – incident ticket (06j)
    ('WF-03', 'Ticket', 'Bình', 'report → OPEN',
     'LockerServiceTicketRoutingTest#customerFaultIsRoutedToTheLockersTechnicianAndRemembersTheOrderHoldingTheBox'),
    ('WF-03', 'Ticket', 'Bình', 'OPEN → IN_PROGRESS (claim)', 'LockerServiceReportPhotoTest#claimBlockThresholdFollowsAdminSetting'),
    ('WF-03', 'Ticket', 'Bình', 'IN_PROGRESS → RESOLVED',
     'LockerServiceTicketRoutingTest#onlyTheAssigneeResolvesAndATicketCannotBeResolvedTwice'),
    ('WF-03', 'Ticket', 'Bình', 'IN_PROGRESS → REJECTED',
     'LockerServiceTicketRoutingTest#onlyTheAssigneeRejectsAndFeedbackIsRequired'),
    # WF-04 – locker box, maintenance path
    ('WF-04', 'Box', 'Huy', 'AVAILABLE → FAULT (inspection / technician)',
     'LockerServiceInspectionTest#failingWithAFaultyBoxMarksThatBoxThroughTheFaultFlow'),
    ('WF-04', 'Box', 'Huy', 'AVAILABLE → CLEANING', None),
    ('WF-04', 'Box', 'Huy', 'CLEANING → AVAILABLE', None),
    ('WF-04', 'Box', 'Huy', 'AVAILABLE → OUT_OF_SERVICE', None),
    ('WF-04', 'Box', 'Huy', 'OUT_OF_SERVICE → AVAILABLE', 'LockerServiceAdminGuardsTest#idleBoxCanChangeStatus'),
    # WF-04 – drone (06i), fleet and maintenance
    ('WF-04', 'Drone', 'Nhã', 'add drone → IDLE', 'LockerServiceAdminGuardsTest#droneIsCreatedAtLockerWithLandingPad'),
    ('WF-04', 'Drone', 'Nhã', 'IDLE → CHARGING',
     'LockerServiceDroneFleetTest#adminCanUpdateStatusWithoutTakingTechnicianOwnership'),
    ('WF-04', 'Drone', 'Nhã', 'in service → FAULT',
     'LockerServiceDroneFleetTest#faultReportNotifiesRoutedDroneTechnicianWithDroneType'),
    ('WF-04', 'Drone', 'Nhã', 'in service → MAINTENANCE', None),
    ('WF-04', 'Drone', 'Nhã', 'FAULT → MAINTENANCE', None),
    ('WF-04', 'Drone', 'Nhã', 'FAULT → IDLE (ticket resolved)',
     'LockerServiceDroneFleetTest#leavingFaultWithoutOpenReportDoesNotTouchReports'),
    ('WF-04', 'Drone', 'Nhã', 'MAINTENANCE → IDLE (done)', None),
]

# End-to-end test of each workflow's main demo scenario across services and clients: none runs in CI yet
# (BM02 SR-20). The closest, JOURNEY, drives WF-01 inside order-service only and is counted above.
E2E_CI = {'WF-01': None, 'WF-02': None, 'WF-03': None, 'WF-04': None}

# NFR tests: only N4 is a CI test; N1 (k6 on staging), N2 (timed run on CAB-TU01), N3 (event timing),
# N6 (health check) are measured outside CI, and N5's Bluetooth token reuse is checked on the Pi (iot, no CI).
NFR_CI = {
    'N1': None, 'N2': None, 'N3': None,
    'N4': 'PaymentServiceMoneyRulesTest#sameBankTransactionDeliveredTwiceIsRecordedOnce',
    'N5': None, 'N6': None,
}
