# Unit test cases of Lock.R backend (Report 5 - Unit Test).  One entry per function sheet.
# Each test line: "testMethod | type | preconditions ; ... | inputs ; ... | return ; ... | exception ; ... | log"
# type: N (normal), A (abnormal), B (boundary).  Results (P / F / untested) come from the real surefire run.

FUNCS = [
dict(cls="AuthServicePasswordTest", req="Change Password", target="AuthService", method="changePassword()",
     desc="Set or change the password of an account; revoke other sessions.", pre="Auth account exists",
     tests="""
accountWithPasswordNeedsCurrentPassword|A|Account has own password|Current password empty||AUTH_CURRENT_PASSWORD_REQUIRED
wrongCurrentPasswordKeepsOldPassword|A|Account has own password|Wrong current password|Old password kept|AUTH_INVALID_PASSWORD
newPasswordIsRequired|A|Account has own password|New password empty||AUTH_NEW_PASSWORD_REQUIRED
changeRevokesOtherSessionsAndReturnsFreshTokensForThisDevice|N|Account has own password|Correct current + new password|Other sessions revoked;New tokens for this device
accountWithoutOwnPasswordSetsFirstPasswordWithoutCurrent|N|Account created by OTP (no password)|New password only|First password saved
accountLookupReportsHasPassword|N|Account has own password|Lookup account|hasPassword = true
otpRegistrationWithoutPasswordIsMarkedAsNoPassword|N|Registered by email OTP|Lookup account|hasPassword = false
registrationWithPasswordIsMarkedAsHasPassword|N|Registered with password|Lookup account|hasPassword = true
adminCreatedAccountWithoutPasswordIsMarkedAsNoPassword|B|Created by admin without password|Lookup account|hasPassword = false
"""),
dict(cls="EmailOtpServiceTest", req="Email OTP", target="EmailOtpService", method="sendOtp()",
     desc="Generate and email a one-time code for login, password reset and admin 2FA.", pre="SMTP channel mocked",
     tests="""
defaultOtpHasSixDigitsAndExpiresInFiveMinutes|N|Default settings|Purpose EMAIL_LOGIN|OTP has 6 digits;Expires after 300 s
otpLengthAndExpiryFollowAdminSettings|B|Admin changed OTP length / expiry|Purpose PASSWORD_RESET|Length and expiry follow settings
maskEmailKeepsEnoughToTraceButNotEnoughToIdentify|N||Email address|Masked email||||Email masked in log
expiryTextFallsBackToSecondsWhenNotWholeMinutes|B|Expiry not whole minutes|Expiry 90 s|Expiry text in seconds
otpEmailIsLightInlineStyledSoDarkModeClientsKeepItReadable|N||Purpose ADMIN_2FA|Inline light-styled HTML email
"""),
dict(cls="AuthServiceAdminAccessTest", req="Admin Login with 2FA", target="AuthService", method="adminLogin() / verifyAdmin2fa() / updateAccountStatus()",
     desc="Two-step admin login, account status changes and identifier sync.", pre="Auth account exists",
     tests="""
adminCannotGetTokenFromPasswordOnlyLogin|A|Role ADMIN|Password login only||ADMIN_AUTH_2FA_REQUIRED
adminStillGetsTokenAfterTwoFactor|N|Role ADMIN|Correct password;Correct OTP|Access + refresh token
wrongOtpKeepsTempTokenSoAdminCanRetry|A|Role ADMIN|Correct password;Wrong OTP|Temp token kept|ADMIN_AUTH_OTP_INVALID
tooManyWrongOtpsInvalidateTempToken|B|Role ADMIN|Wrong OTP 5 times|Temp token invalidated|AUTH_TEMP_TOKEN_INVALID
tempTokenIsConsumedOnlyAfterSuccessfulOtp|B|Role ADMIN|Reuse temp token after success||AUTH_TEMP_TOKEN_INVALID
inactiveAdminCannotStartTwoFactorLogin|A|Admin status INACTIVE|Correct password||AUTH_INVALID
suspendedAccountCannotLoginOrRefresh|A|Status INACTIVE|Login / refresh token||AUTH_ACCOUNT_INACTIVE
suspendingAccountRevokesRefreshTokens|N|Status ACTIVE|Set status INACTIVE|Refresh tokens revoked
reactivatingAccountDoesNotTouchTokens|N|Status INACTIVE|Set status ACTIVE|Tokens unchanged
accountCreatedInactiveGetsNoTokens|B|Created with INACTIVE|Create account|No token issued
unknownAccountStatusIsRejected|A||Status BANNED||AUTH_STATUS_INVALID
statusUpdateForProfileWithoutLoginIsNoOp|B|Profile without login account|Set status INACTIVE|Nothing changed
identifiersSyncRejectsEmailOwnedByAnotherAccount|A|Email used by another account|Sync email||AUTH_EMAIL_TAKEN
identifiersSyncUpdatesChangedValuesAndResetsVerification|N||New email and phone|Values updated;Verification reset
identifiersSyncKeepsValuesWhenFieldsAreBlank|B||Blank email and phone|Values kept
"""),
dict(cls="KioskQrLoginServiceTest", req="Kiosk Login by QR", target="KioskQrLoginService", method="create() / confirm() / poll()",
     desc="Kiosk shows a QR session; the customer confirms it in the app and the kiosk collects the tokens.", pre="Kiosk of a locker",
     tests="""
qrCarriesSessionAndCodeButNotPollToken|N|Valid locker id|Create session|QR has session + code;Poll token not in QR
lockerIdIsRequired|A||Locker id missing||KIOSK_QR_LOCKER_REQUIRED
wrongPollTokenLooksLikeUnknownSession|A|Session PENDING|Wrong poll token||KIOSK_QR_INVALID
confirmedSessionDeliversTokensExactlyOnce|B|Session CONFIRMED|Poll twice|Tokens once;Status CONSUMED
confirmNeedsSignedInCustomer|A|Session PENDING|No signed-in user||AUTH_REQUIRED
lockedAccountCannotConfirm|A|Session PENDING;Account INACTIVE|Confirm||AUTH_ACCOUNT_INACTIVE
expiredSessionCannotBeConfirmed|B|Session EXPIRED|Confirm||KIOSK_QR_EXPIRED
confirmedButNotCollectedBeforeExpiryNeverIssuesTokens|B|Session CONFIRMED|Poll after expiry|No token;Status EXPIRED
secondConfirmIsRejected|A|Session CONFIRMED|Confirm again||KIOSK_QR_ALREADY_USED
fiveWrongCodesCancelTheSession|B|Session PENDING|Wrong code 5 times|Status CANCELLED|KIOSK_QR_INVALID
accountLockedBeforeCollectionCancelsSession|A|Session CONFIRMED;Account locked|Poll|Status CANCELLED
kioskCanCancelPendingSession|N|Session PENDING|Kiosk cancels|Status CANCELLED
sessionCreationIsLimitedPerLocker|B|Many sessions of one locker|Create session||KIOSK_QR_RATE_LIMITED
sessionCreationIsLimitedPerAddress|B|Many sessions from one IP|Create session||KIOSK_QR_RATE_LIMITED
cleanupDropsFinishedSessionsAfterRetention|N|Finished sessions older than retention|Run cleanup|Old sessions deleted
"""),
dict(cls="AuthServiceDeleteAccountTest", req="Delete Account", target="AuthService", method="deleteAccount()",
     desc="Delete an account, release its email / phone and revoke tokens.", pre="Auth account exists",
     tests="""
deletingAccountReleasesIdentifiersAndRevokesTokens|N|Status ACTIVE|Delete account|Status DELETED;Email / phone released;Tokens revoked
deletedAccountCannotSignInAgain|A|Status DELETED|Login / refresh||AUTH_INVALID
releasedEmailAndPhoneCanBeUsedForNewAccount|N|Status DELETED|Register same email / phone|New CUSTOMER account
otpAndPhoneSignInTreatReleasedIdentifiersAsNewUser|N|Status DELETED|OTP / phone sign-in|Treated as new user
deletedAccountCannotBeReactivatedOrGivenIdentifiersAgain|A|Status DELETED|Set status ACTIVE||AUTH_ACCOUNT_ALREADY_DELETED
deletingAgainIsSafe|B|Status DELETED|Delete again|No change
deletingUserWithoutLoginAccountIsNoOp|B|Profile without login account|Delete account|Nothing changed
"""),
dict(cls="UserControllerSelfServiceTest", req="Manage Profile", target="UserController", method="updateProfile() / changePassword()",
     desc="Customer updates own profile, phone, email and password.", pre="Customer signed in",
     tests="""
phoneChangeIsCheckedThenSyncedToLoginBeforeProfileIsSaved|N||New phone|Login account synced;Profile saved
duplicatePhoneStopsBeforeTouchingLoginAccount|A|Phone used by another user|New phone||USER_PHONE_TAKEN
loginAccountConflictKeepsProfileUnchanged|A|Email used in auth-service|New email|Profile unchanged|AUTH_EMAIL_TAKEN
unchangedOrBlankIdentifiersDoNotTouchLoginAccount|B||Same / blank email and phone|Login account not called
legacyFullNameIsSplitAtLastSpace|N|Profile with legacy full name|Get profile|First / last name split
nameResolutionRules|N||First, last and full name|Name resolved by rules
jsonBodyAcceptsBothNameShapes|N||fullName or first/last name|Both accepted
profileReportsWhetherAccountHasOwnPassword|N||Get profile|hasPassword reported
profileStillLoadsWhenLoginLookupFails|A|auth-service down|Get profile|Profile returned
passwordChangeReturnsFreshTokensForThisDevice|N||Correct current + new password|New tokens returned
passwordChangeSurfacesAuthErrorCode|A||Current password missing||AUTH_CURRENT_PASSWORD_REQUIRED
"""),
dict(cls="UserProfileServiceAdminTest", req="Manage Accounts", target="UserProfileService", method="updateStatus() / growth()",
     desc="Admin updates user status, uniqueness checks and user growth statistics.", pre="Admin signed in",
     tests="""
updateStatusNormalizesCase|N|User ACTIVE|Status 'inactive'|Status INACTIVE
updateStatusRejectsMissingOrUnknownValue|A||Status empty / unknown||USER_STATUS_INVALID
updateWithoutStatusKeepsSuspension|B|User INACTIVE|Update without status|Still INACTIVE
newProfileWithoutStatusDefaultsToActive|N||New profile, no status|Status ACTIVE
uniquenessCheckForUpdateIgnoresSameUser|A|Phone used by another user|Update phone|Same user allowed|USER_PHONE_TAKEN
findsActiveAccountByTrimmedCaseInsensitiveEmail|N|User ACTIVE|' User@Mail.com '|User found
doesNotResolveInactiveUserByEmail|A|User INACTIVE|Email of user||USER_NOT_FOUND
adminViewCarriesTimestamps|N||Get user (admin)|createdAt / updatedAt returned
growthZeroFillsMonthsAndBucketsByVietnamTime|N|Users created over months|Get growth|Empty months = 0;Vietnam time buckets
growthDefaultsToTwelveMonthsAndCapsAtThirtySix|B||Months empty / 100|12 months default;Max 36 months
"""),
dict(cls="StoreServiceWriteTest", req="Manage Stores", target="StoreService", method="create() / update() / delete()",
     desc="Admin creates, updates and deletes stores.", pre="Admin signed in",
     tests="""
createWithoutActiveOrStatusDefaultsToActive|N||Store without status|Status ACTIVE
updateKeepsFieldsTheRequestOmits|N|Store exists|Partial update|Omitted fields kept
updateOverwritesPresentFieldsAndEmptyTextClearsIt|B|Store exists|Empty text field|Field cleared
responseCarriesTimestamps|N|Store exists|Get store|createdAt / updatedAt
adminEditAnnouncesCatalogChangeForCustomerApps|N|Store exists|Update store|Catalog change event published
deleteSucceedsWhenTheStoreHasNoLockers|N|Store has no locker|Delete store|Store deleted
deleteIsRejectedWhileLockersStillBelongToTheStore|A|Store has lockers|Delete store||STORE_HAS_LOCKERS
deleteIgnoresLockersOfOtherStores|B|Only other stores have lockers|Delete store|Store deleted
deleteIsRefusedWhenLockersCannotBeChecked|A|locker-service down|Delete store||LOCKER_SERVICE_UNAVAILABLE
deleteOfMissingStoreIsNotFoundWithoutCallingLockerService|A|Store not found|Delete store||NotFoundException
"""),
dict(cls="OrderServiceSendFlowTest", req="Send Parcel", target="OrderService", method="confirm() / markDropOpened()",
     desc="Sender opens the box, drops the parcel and confirms; PIN swapped to pickup PIN.", pre="SEND order exists",
     tests="""
confirmSendRejectsUnpaidOrder|A|Order UNPAID|Confirm drop||ORDER_UNPAID
confirmSendRejectedWhenBoxWasNeverOpened|A|Order PAID, box never opened|Confirm drop||ORDER_DROP_NOT_OPENED
confirmSendAfterOpeningSwapsDropPinForPickupPin|N|Order PAID, box opened|Confirm drop|Status STORING;Box OCCUPIED;Pickup PIN issued
markDropOpenedRecordsFirstOpenOnly|B|Order PAID|Open box twice|Only first opening recorded
markDropOpenedIgnoresOrdersPastDropOff|B|Order STORING|Mark drop opened|Nothing changed
statusReportsPaidFromPaymentStatusNotOrderCompletion|N|Payment PAID, order not completed|Get status|paid = true
myOrdersCarryMilestonesParcelAndDelegationFromOneHistoryQuery|N|Orders with history|List my orders|Milestones, parcel, delegation
singleOrderWithoutParcelDeclarationHasNoParcelBlock|B|No parcel declaration|Get order|No parcel block
"""),
dict(cls="OrderServiceRentalPaymentTest", req="Rent Locker", target="OrderService", method="createRental() / extendRental() / reorder()",
     desc="Create, confirm, extend and reorder hourly rentals with correct pricing.", pre="Customer signed in",
     tests="""
createRentalPricesByTheRealCellTypeNotTheOneTheAppSends|N|Box STANDARD available|App sends type XL|Priced as STANDARD;Box RESERVED
createRentalKeepsDeadlineEmptyUntilCustomerActuallyStartsRental|N|Box available|Create rental|Deadline empty
confirmRejectsUnpaidRental|A|Rental UNPAID|Confirm rental||ORDER_UNPAID
confirmPaidRentalStartsDeadlineFromConfirmTime|N|Rental PAID|Confirm rental|Status STORING;Deadline from confirm time
extendRentalMarksPreviouslyPaidRentalAsUnpaidUntilExtraChargeIsSettled|N|Rental STORING, PAID|Extend 2 h|Payment UNPAID until extra paid
pickupStorageRejectsRentalWhenExtensionBalanceIsStillUnpaid|A|Extension unpaid|Pick up||ORDER_UNPAID
overdueRentalIsChargedAtLeastTheExtensionRate|B|Rental overdue|Assess overtime|Fee >= extension rate
extendingAnOverdueRentalChargesTheOverdueHoursFirst|B|Rental overdue|Extend|Overdue hours charged first
sendOvertimeCapDoesNotGrowWithEachAssessment|B|SEND order overdue|Assess overtime twice|Cap unchanged
reorderUsesStoredRentalDurationHoursInsteadOfCreatedAtToDeadlineGap|N|Rental COMPLETED|Reorder|Stored duration used
reorderClampsLegacyRentalDurationToPolicyMaximum|B|Legacy rental > max hours|Reorder|Duration = policy max
reorderRefusesTypesWithoutABookingPath|A|Order STORAGE|Reorder||ORDER_REORDER_UNSUPPORTED
reorderOfSendWithoutReceiverEmailAsksForNewOrder|A|SEND without receiver email|Reorder||RECEIVER_EMAIL_REQUIRED
"""),
dict(cls="OrderServiceSendStorageTest", req="Send Parcel", target="OrderService", method="extendSend() / applyPaidSendExtension()",
     desc="Storage time of a SEND order: included 48 h, paid extension up to the maximum.", pre="SEND order exists",
     tests="""
appWithoutHoursKeepsTheIncluded48AndFlatFee|N||No storage hours|48 h included;Flat fee
storageHoursAbove48AreChargedLikeRentingTheCell|N||72 storage hours|Extra hours at rental price
hoursOutsideIncludedToMaxAreRejected|B||Hours < 48 or > max||SEND_STORAGE_HOURS_INVALID
unpaidOrderIsExtendedRightAwayInThePrice|N|Order UNPAID|Extend|Price increased at once
paidExtensionWaitsForPaymentAndDoesNotBlockTheReceiver|N|Order PAID|Extend|Extension pending;Receiver can pick up
paymentAppliesTheExtensionToTheDeadline|N|Extension pending|Extension paid|Deadline extended
secondExtensionWaitsForThePreviousPayment|A|Extension pending|Extend again||SEND_EXTENSION_PENDING
pendingExtensionOnPaidInitializedOrderStillAllowsDropOff|B|Order PAID, INITIALIZED;Extension pending|Drop parcel|Status STORING
"""),
dict(cls="OrderServiceHandoverAndCompletionTest", req="Pick Up Parcel", target="OrderService", method="directHandover() / delegate()",
     desc="Hand over a parcel with the pickup code and publish completion once.", pre="Order STORING",
     tests="""
handoverWithPickupPinCompletesAndPublishesCompletionOnce|N||Correct pickup PIN|Status COMPLETED;Completion event once
handoverAcceptsTheOrderQrCode|N||Order QR code|Status COMPLETED
handoverWithoutCodeIsRefused|A||Code empty||HANDOVER_OTP_REQUIRED
handoverWithWrongCodeIsRefused|A||Wrong code||INVALID_OTP
handoverOfOrderWithoutActiveCodeCannotBeVerified|A|No active code|Any code||HANDOVER_OTP_UNAVAILABLE
nonCompletingTransitionsDoNotPublishCompletion|B|Order INITIALIZED|Change status|No completion event
delegationRecordsTheDelegateSeparately|N||Delegate phone|Delegate recorded separately
"""),
dict(cls="OrderBenefitServiceTest", req="Apply Voucher and Points", target="OrderBenefitService", method="applyVouchers() / redeemPoints() / releaseBenefits()",
     desc="Apply vouchers then loyalty points to an order; release them on cancel.", pre="Order being created",
     tests="""
pricingAppliesVoucherFirstThenPointsOnTheRemainder|N|Voucher GIAM5K saved;Points available|Voucher + points|Voucher first, points on remainder
pointsDiscountNeverExceedsWhatIsLeftAndTotalNeverGoesNegative|B|Points > remainder|Points request|Total >= 0
noPointsRequestedOrNothingLeftToPayDoesNotCallLoyalty|B||No points / total 0|loyalty-service not called
loyaltyOutageCreatesTheOrderWithoutPointsAndCompensates|A|loyalty-service down|Points request|Order without points
lockerScopedVoucherIsRejectedWithoutTheMatchingLocker|A|Voucher of another locker|Apply voucher||PROMOTION_INVALID
droneVoucherIsCheckedAgainstTheSourceLockerNotTheDestination|N|Drone order|Locker-scoped voucher|Checked on source locker
numberOfVouchersPerOrderFollowsTheAdminSetting|B|Max 1 voucher|2 vouchers||BusinessException
usageLimitsAreCheckedOnTheLockedPromotionRow|B|Promotion usage limit reached|Apply voucher||BusinessException
minimumOrderAmountIsCheckedAgainstTheOriginalPrice|B|Voucher min order amount|Order price|Checked on original price
exchangeOnlyVoucherNeedsAHeldClaim|A|Exchange-only voucher not held|Apply voucher||BusinessException
ordersCoveredByDiscountsCollectedNoMoney|B|Discount = order price|Create order|Collected 0
releaseReturnsVoucherUsageAndRefundsPointsAfterCommit|N|Order cancelled|Release benefits|Voucher usage returned;Points refunded
releasingTwiceDoesNothingTheSecondTime|B|Benefits released|Release again|No change
failedPointRefundIsRetriedLater|A|loyalty-service down|Release benefits|Refund retried later
"""),
dict(cls="OrderAccessGuardTest", req="View Order", target="OrderAccessGuard", method="requireParticipant() / requireOwner()",
     desc="Only owner, receiver / delegate and admin can read an order and its PIN.", pre="Order with PIN exists",
     tests="""
ownerReadsOrderWithPin|N|Caller is owner (CUSTOMER)|Read order|Order with PIN
otherCustomerGetsNotFoundForOrderWithPin|A|Caller is another CUSTOMER|Read order||NotFoundException
technicianIsNotAnOwner|A|Caller LOCKER_TECHNICIAN|Read order||NotFoundException
adminReadsAnyOrderWithoutLookup|N|Caller ADMIN|Read order|Order returned
missingOrderIsNotFound|A|Order does not exist|Read order||NotFoundException
receiverOrDelegateReadsHistory|N|Caller is receiver / delegate|Read history|History returned
ownerReadsHistoryWithoutReceiverLookup|N|Caller is owner|Read history|History, no receiver lookup
strangerGetsNotFoundForHistory|A|Caller is stranger|Read history||NotFoundException
"""),
dict(cls="OrderPaymentEventListenerTest", req="Make Payment", target="OrderPaymentEventListener", method="onPaymentEvent()",
     desc="Apply payment events to orders: paid when covered, refund late money.", pre="Payment completed event",
     tests="""
paidSendOrderTellsTheReceiverOnce|N|SEND order UNPAID|Full payment|Order PAID;Receiver notified once
partialPaymentDoesNotTellTheReceiverYet|B|Order UNPAID|Partial payment|Receiver not notified
underpaidLockerOrderStaysUnpaidUntilTheRestArrives|B|Locker order UNPAID|Amount < total|Still UNPAID
dronePaymentAddsItsOwnAmountAndOnlyMarksPaidOnceTheTotalIsCovered|B|Drone order UNPAID|Two payments|PAID when total covered
paymentCompletedMarksDroneOrderPaidWithoutChangingDispatchStage|N|Drone order AWAITING_DISPATCH|Full payment|PAID;Stage unchanged
moneyArrivingAfterALockerOrderWasCanceledIsSentBack|A|Locker order CANCELED|Late payment|Refund requested
moneyArrivingAfterADroneOrderWasCanceledIsSentBackNotKept|A|Drone order CANCELED|Late payment|Refund requested
aLatePaymentOnADroneOrderAwaitingRefundDoesNotFlipItBackToPaid|A|Drone order REFUND_PENDING|Late payment|Still REFUND_PENDING
aSecondLatePaymentOnAnAlreadyRefundedDroneOrderIsAlsoRefunded|A|Drone order REFUNDED|Second late payment|Refund requested
"""),
dict(cls="BleOrderAccessServiceTest", req="Open Box via Bluetooth", target="BleOrderAccessService", method="check()",
     desc="Decide who may open the box of an order over Bluetooth and for what purpose.", pre="Order in a box",
     tests="""
ownerDropsIntoTheSendBoxOfAPaidNewOrder|N|Order INITIALIZED, PAID;Caller owner|Open (drop)|Allowed DROP
onlyTheOwnerMayDrop|A|Order INITIALIZED;Caller not owner|Open (drop)|BLE_ORDER_FORBIDDEN
unpaidOrderIsRefusedWithTheSameCodeAsThePin|A|Order UNPAID|Open|ORDER_UNPAID
renterOpensARentalWhileStoring|N|Rental STORING;Caller renter|Open|RENTAL_ACCESS
expiredRentalKeepsItsBlockReason|A|Rental expired|Open|RENTAL_EXPIRED
receiverHoldingTheCodePicksUpFromTheReceiveBox|N|Order STORING;Caller receiver|Open (pickup)|PICKUP allowed
onDelegatedOrderOnlyTheDelegatePicksUp|A|Order delegated;Caller receiver|Open (pickup)|BLE_ORDER_FORBIDDEN
senderPicksUpOnlyWhenSendingToThemselves|B|Sender = receiver|Open (pickup)|PICKUP allowed
returnedParcelGoesBackToTheSender|N|Order RETURNED;Caller sender|Open|PICKUP allowed
droneParcelOpensOnlyOnceInTheCell|B|Drone order READY_FOR_PICKUP|Open twice|Second: BLE_ORDER_NOT_OPENABLE
finishedOrderIsNotOpenableForParticipantsAndForbiddenForOthers|A|Order COMPLETED|Open|BLE_ORDER_NOT_OPENABLE / FORBIDDEN
strangerIsForbiddenAndMissingOrderIsNotFound|A|Caller stranger / order missing|Open|BLE_ORDER_FORBIDDEN / ORDER_NOT_FOUND
userServiceOutageIsPassedOnInsteadOfForbidden|A|user-service down|Open|USER_LOOKUP_UNAVAILABLE
"""),
dict(cls="StorageHandoverServiceTest", req="Hand Over Stored Item", target="StorageHandoverService", method="handOver()",
     desc="Admin hands an EXPIRED order kept in storage to the sender, receiver or another person with verification.", pre="Order kept in storage",
     tests="""
senderWithMatchingLast4IsHandedOverAndRecorded|N|Recipient SENDER|Correct last 4 digits|Handed over;Record saved
receiverPhoneOnOrderIsAccepted|N|Recipient RECEIVER|Receiver last 4 digits|Handed over
wrongLast4IsRejectedBeforePhotoOrCheckout|A|Recipient RECEIVER|Wrong last 4 digits||HANDOVER_PHONE_MISMATCH
delegateWithoutPhoneOnOrderAsksForOther|A|Recipient DELEGATE, no phone|Last 4 digits||HANDOVER_PHONE_UNKNOWN
otherRecipientNeedsNamePhoneAndReason|A|Recipient OTHER|Missing name / phone / reason||HANDOVER_OTHER_RECIPIENT_INCOMPLETE
orderNoLongerInStorageIsRejected|A|Order COMPLETED|Hand over||HANDOVER_ORDER_NOT_IN_STORAGE
outstandingMustBeDeclaredCollected|A|Fee outstanding|Not declared collected||HANDOVER_OUTSTANDING_NOT_COLLECTED
collectedOutstandingIsWrittenToHistoryAndRecord|N|Fee outstanding|Declared collected (cash)|Written to history and record
unpaidOrderWithoutPaymentServiceStillCountsAsOwed|A|Order UNPAID;payment-service down|Not declared collected||HANDOVER_OUTSTANDING_NOT_COLLECTED
"""),
dict(cls="RevenueReportServiceTest", req="View Dashboard and Reports", target="RevenueReportService", method="summary() / byService() / byCustomer()",
     desc="Revenue report from money actually collected, by day, service, method, locker and customer.", pre="Payments exist",
     tests="""
summaryUsesCollectedMoneyAndLoadsPaymentsOnceWhenWindowsOverlap|N|Overlapping periods|Get summary|Collected money;Payments loaded once
entriesAddUpToSummaryCards|N||Get entries|Entries = summary cards
entriesRejectUnknownKind|A||Kind 'XYZ'||REVENUE_ENTRY_KIND_INVALID
dailySeriesBucketsByVietnamDateAndFillsEmptyDays|B|Days without payment|Daily series|Vietnam dates;Empty days = 0
byServiceSeparatesOvertimeFeeFromOrderType|N|Rental with overtime|By service|Overtime separated
byMethodAttributesRefundToOriginalMethod|N|Refunded payment|By method|Refund on original method
byLockerAndByStoreIncludeIdleLockersBoxCountsAndUnassigned|B|Idle lockers|By locker / store|Idle lockers included
byCustomerSortsPagesAndFiltersByName|A||Sort 'abc'|Sorted / filtered list|INVALID_SORT
customerDetailListsOrdersWithAmountsMethodsAndAllTimePaid|N|Customer orders|Customer detail|Orders, amounts, all-time paid
paymentServiceOutageFailsReportInsteadOfShowingZeroRevenue|A|payment-service down|Get summary||PAYMENT_DATA_UNAVAILABLE
overtimePortionOnlyCountsMoneyBeyondBasePrice|B|Rental paid more than base|By service|Only extra counted as overtime
"""),
dict(cls="PaymentServiceCheckoutTest", req="Make Payment", target="PaymentService", method="checkout() / refund()",
     desc="Create payments for orders with the enabled methods and refund paid orders.", pre="Customer signed in",
     tests="""
checkoutRejectsRetiredMethodsBeforeLookingUpOrder|A||Method VNPAY||PAYMENT_METHOD_UNSUPPORTED
checkoutRejectsMethodDisabledByAdminBeforeLookingUpOrder|A|Method disabled by admin|Disabled method||PAYMENT_METHOD_DISABLED
directPaymentCreationRejectsRetiredMethods|A||Create payment VNPAY||PAYMENT_METHOD_UNSUPPORTED
checkoutIsRefusedWhileTheOrderBoxIsBeingFixed|A|Box incident open|Checkout SEPAY||ORDER_BOX_INCIDENT_OPEN
checkoutStillRejectsOrderWhenCompletedPaymentsAlreadyCoverTotal|B|Paid amount = total|Checkout||ORDER_ALREADY_PAID
checkoutChargesOnlyOutstandingBalanceAfterRentalExtension|N|Rental extended|Checkout|Amount = outstanding only
topUpAfterExtensionIsLabelledAsAnAdditionalPayment|N|Rental extended|Checkout|Labelled additional payment
firstPaymentKeepsThePlainOrderLabel|N|No previous payment|Checkout|Plain order label
clientReasonWinsOverTheDerivedOne|N||Client reason|Client reason kept
clientReasonIsCappedBecauseItIsShownToTheCustomer|B||Very long reason|Reason truncated
paymentResponseExposesContentAndTimestamps|N||Checkout|Transfer content + timestamps
checkoutSelectsDroneReceiverOnlyForDroneDeliveryOrders|N|Drone order|Checkout SEPAY|Drone receiver account
checkoutKeepsDefaultReceiverForLockerOrders|N|Rental order|Checkout SEPAY|Default receiver account
cashStaysPendingWhenAutoCompleteIsTurnedOff|B|Auto-complete off|Checkout CASH|Payment PENDING
refundOrderCreatesPendingRefundWithoutWalletCredit|N|Order paid|Refund order|Refund PENDING;Paid back by bank transfer
refundOrderSkipsPaymentsAlreadyRefunded|B|Some payments refunded|Refund order|Only others refunded
"""),
dict(cls="PaymentServiceMoneyRulesTest", req="Make Payment", target="PaymentService", method="handleSepayWebhook() / adminApproveRefund() / simulateTransfer()",
     desc="Money rules: SePay webhook, refunds, compensation and payment simulation.", pre="Pending payment exists",
     tests="""
underpaidTransferIsRecordedAtTheAmountActuallyReceived|B||Transfer < amount|Recorded at received amount
sameBankTransactionDeliveredTwiceIsRecordedOnce|B||Same transaction id twice|Recorded once
outgoingTransferIsIgnored|A||Outgoing transfer|Ignored
webhookWithoutAmountDoesNotMarkAnythingPaid|A||Webhook without amount|Payment PENDING
customerCannotAskForMoreThanTheOrderPaid|B|Order paid 15,000|Refund 20,000||REFUND_AMOUNT_EXCEEDS_PAID
refundStatusOfTheOrderFollowsHowMuchWasRefunded|N|Refunds approved / rejected|Approve refund|Order REFUNDED / REFUND_PENDING
approvingAPartialRefundKeepsTheOrderPaidAndReportsTheRefundedAmount|B|Partial refund|Approve|Order still PAID
compensationPayoutsDoNotCountAsRefundsOfTheOrder|N|Compensation payout|Approve|Not counted as refund
compensationWithShippingFeeAlsoQueuesARefundOfThePaidFee|N|Compensation with fee|Create compensation|Fee refund queued
compensationWithoutShippingFeeLeavesTheOrderPaymentStatusAlone|N|Compensation without fee|Create compensation|Order status unchanged
approvingACompensationPayoutReportsItPaidToTheIncident|N|Compensation PENDING|Approve|Incident notified paid
simulationIsRejectedWhileAdminHasItTurnedOff|A|Simulation disabled|Simulate transfer||PAYMENT_SIMULATION_DISABLED
simulatedTransferCompletesThePendingPaymentLikeARealOne|N|Simulation enabled|Simulate transfer|Payment COMPLETED
simulationOnlyForAllowedAccountsAndTheirOwnPayments|A|Account not allowed / other's payment|Simulate||PAYMENT_SIMULATION_NOT_ALLOWED
"""),
dict(cls="SepayServiceTest", req="Make Payment", target="SepayService", method="transferContent() / verifyWebhook() / extractReferenceId()",
     desc="Build VietQR bank transfer data and verify SePay webhooks.", pre="SePay keys configured",
     tests="""
bankTransferCarriesReceiverAccountAndTransferContentForSepay|N|Method SEPAY|Build transfer|Receiver account;Transfer content LOCKR...
bankTransferIsAbsentForOtherMethodsOrWithoutReceiverAccount|B|Other method / no receiver account|Build transfer|No bank transfer
dronePaymentUsesItsOwnReceiverAndKeepsItInTheStoredQr|N|Drone order|Build transfer|Drone receiver in QR
lockerPaymentContinuesUsingTheDefaultReceiver|N|Locker order|Build transfer|Default receiver
testExtractReferenceIdFromContent|N||Transfer content|Reference id extracted
testBuildCheckoutFieldsAndSignature|N||Checkout fields|Fields + signature
testVerifyWebhookWithApiKey|N||Webhook with API key|Webhook accepted
signedCallbackIsAcceptedOnlyWithMatchingSignature|A||Wrong signature|Callback rejected
webhookIsRejectedWhenKeysAreNotConfigured|A|Keys not configured|Webhook||BusinessException
"""),
dict(cls="LoyaltyRedemptionTest", req="Loyalty Points", target="LoyaltyService", method="redeemPreview() / redeemForOrder() / refundOrderRedemption()",
     desc="Redeem loyalty points on orders (min 1,000, max 50 %), refund them and compute tiers.", pre="Loyalty account exists",
     tests="""
previewCapsByPercentOfOrderAndBalance|B|Balance 100,000|Order 20,000|Max 10,000 (50 %)
previewIsZeroBelowMinimumOrWhenDisabled|B|Balance < 1,000 / disabled|Preview|0 points
previewFollowsAdminRedeemSettings|N|Admin changed redeem rules|Preview|Follows settings
redeemClampsRequestAndWritesNegativeOrderRedeem|B||Request > cap|Clamped;ORDER_REDEEM negative entry
redeemNothingForZeroRequestBelowMinimumOrMissingAccount|B|No account|0 / 500 points|Nothing redeemed
redeemIsIdempotentPerOrder|B|Order already redeemed|Redeem again|Same result
redeemForAnotherUsersOrderIsRejected|A|Order of another user|Redeem||LOYALTY_REDEMPTION_CONFLICT
refundReturnsExactlyTheRedeemedPointsOnce|B|Points redeemed|Refund twice|Returned once
refundOfOrderWithoutRedemptionIsZero|B|No redemption|Refund|0
tierFollowsLifetimePointsNotBalance|N|Lifetime 60,000, balance 1,000|Get tier|SILVER
manualAdjustmentMovesLifetimeButNeverBelowZero|B|Lifetime 100|Adjust -500|Lifetime 0;Tier BRONZE
adminCannotWriteSystemRedemptionTypes|A||Type ORDER_REDEEM_REFUND||LOYALTY_TYPE_RESERVED
"""),
dict(cls="LoyaltyOrderPointsTest", req="Loyalty Points", target="LoyaltyService", method="awardOrderPoints() / adjustPoints()",
     desc="Earn points on completed orders and admin manual adjustments.", pre="Loyalty account exists",
     tests="""
completedOrderEarnsTenPercentAsPoints|N|Order COMPLETED, paid 50,000|Earn|5,000 points
earnRateFollowsAdminSetting|N|Earn rate changed|Earn|Follows setting
freeOrTinyOrdersEarnNothing|B|Paid 0 / very small|Earn|0 points
orderAlreadyRewardedIsNotRewardedAgain|B|Order rewarded|Earn again|No new points
redeemingMoreThanBalanceIsRejected|A|Balance 1,000|Redeem 5,000||LOYALTY_POINTS_INSUFFICIENT
redeemingMoreStampsThanOwnedIsRejected|A|Stamps 2|Redeem 5 stamps||LOYALTY_STAMPS_INSUFFICIENT
manualAdjustmentCannotUseOrderEarnType|A||Type ORDER_EARN||LOYALTY_TYPE_RESERVED
adminAdjustmentNotifiesAccountOwner|N||Admin adjusts points|Owner notified
"""),
dict(cls="VoucherExchangeServiceTest", req="Manage Vouchers", target="VoucherExchangeService", method="exchange() / exchangeable()",
     desc="Exchange loyalty points for vouchers that have a point price.", pre="Customer signed in",
     tests="""
exchangeSpendsPointsAndSavesVoucher|N|Enough points|Exchange DOI10K|Points spent;Voucher SAVED
notEnoughPointsSavesNothing|A|Points < price|Exchange||LOYALTY_POINTS_INSUFFICIENT
ordinaryPromotionIsNotExchangeable|A|Promotion without point price|Exchange||BusinessException
heldVoucherCannotBeExchangedAgainUntilUsed|A|Voucher held|Exchange again||VOUCHER_ALREADY_HELD
usedVoucherCanBeExchangedAgain|N|Voucher used|Exchange again|Voucher SAVED
loyaltyFailureRefundsAndSavesNothing|A|loyalty-service fails|Exchange||LOYALTY_UNAVAILABLE
listShowsOnlyExchangeableVouchersCheapestFirstWithHeldFlag|N|Several promotions|List exchangeable|Cheapest first;Held flag
"""),
dict(cls="NotificationServiceTest", req="View Notifications", target="NotificationService", method="consumeDomainEvent() / markRead() / broadcast()",
     desc="Create, push and relay notifications; owner-only read / delete.", pre="Notification service running",
     tests="""
eventWithMessageKeepsItsMessage|N||LOCKER_REPORT event with message|Message kept
orderEventWithoutMessageOnlyPushesRealtimeUpdate|B||Order event, no message|Realtime update only
orderPaymentFailedIsNotifiedInVietnamese|N||Payment failed event|Vietnamese notification
realtimeNotificationFollowsUserLanguage|N|User language English|PAYMENT_COMPLETED|English text
upsertTokenStoresLanguage|N||FCM token (ANDROID) + language|Language stored
ownerCanMarkOwnNotificationRead|N|Caller owner|Mark read|Read
markReadOnlyActsOnCallersOwnNotification|A|Caller not owner|Mark read||NotFoundException
batchReadOnlyActsOnCallersOwnNotifications|A|Mixed owners|Batch read||NotFoundException
deleteOnlyActsOnCallersOwnNotification|A|Caller not owner|Delete||NotFoundException
adminActionsIgnoreOwnerAndReturn404WhenMissing|A|Caller ADMIN;Notification missing|Admin action||NotFoundException
resendPushesToNotificationOwner|N|Caller ADMIN|Resend|Push to owner
broadcastWithUserIdsTargetsOnlyThoseUsers|N||Broadcast to 2 users|Only those users
broadcastWithEmptyUserIdsSendsNothing|B||Empty user list|Nothing sent
broadcastWithoutUserIdsSendsExactlyOnePushPerRegisteredUser|B||No user list|One push per user
lockerAvailabilityChangeIsRelayedWithoutNotification|N||Locker availability change|Relayed, no notification
catalogChangeIsRelayedToPublicTopic|N||Promotion change|Public topic
maintenanceAndDeviceChangesAreRelayedToStaffTopic|N||Device OFFLINE / report|Staff topic
adminDataAndAccountChangesAreRelayedToAdminTopic|N||Refund change|Admin topic
"""),
dict(cls="GuestEmailSenderTest", req="Send Pickup Code", target="GuestEmailSender", method="send()",
     desc="Send branded emails to receivers without an account.", pre="SMTP channel",
     tests="""
fullyConfiguredIsReal|N|Host + from address|Check channel|Channel real
beanWithoutHostIsNotReal|A|No host|Check channel|Not real
hostWithoutFromAddressIsNotReal|A|Host, no from address|Check channel|Not real
missingBeanIsNotReal|A|No mail bean|Check channel|Not real
fallsBackToSmtpUsernameAsSender|B|No from address|Send|From = SMTP username
doesNotSendWhenChannelIsNotConfigured|A|Not configured|Send|Nothing sent
sendsBrandedHtmlWithInlineLogo|N|Configured|Pickup code email|HTML with inline logo
usesProvidedHtmlForDroneEmail|N|Configured|DRONE_TEMPLATE html|Provided HTML used
skipsBlankRecipient|B|Configured|Blank recipient|Nothing sent
masksEmailForLogs|N||Email|Masked email||||Email masked in log
"""),
dict(cls="LockerServiceSlaAndQueueTest", req="Handle Incident Ticket", target="LockerService", method="extendSlaAsTechnician() / releaseReport()",
     desc="Ticket SLA extension (max 2 x 24 h with reason) and returning a ticket to the queue.", pre="Ticket IN_PROGRESS",
     tests="""
assignedTechnicianExtendsWithinLimitAndCountIsRecorded|N|Caller is assignee|Extend 24 h + reason|Deadline extended;Count +1
onlyTheAssigneeMayExtend|A|Caller not assignee|Extend||SLA_EXTENSION_NOT_ASSIGNEE
reasonIsRequired|A|Caller is assignee|Reason empty||SLA_EXTENSION_REASON_REQUIRED
hoursPerExtensionFollowAdminSetting|B|Max 24 h|Extend 25 h||SLA_EXTENSION_HOURS_EXCEEDED
extensionCountIsCappedByAdminSetting|B|Extended 2 times|Extend again||SLA_EXTENSION_LIMIT_REACHED
adminExtensionDoesNotUseTechnicianQuota|N|Caller ADMIN|Extend|Count unchanged
settingsCatalogExposesExtensionLimitsWithDefaults|N||Settings catalog|Limits with defaults
extendRequestAcceptsHoursAndLegacyExtensionHours|N||hours / extensionHours|Both accepted
assigneeReleasesTicketBackToQueueWithReason|N|Caller is assignee|Release + reason|Ticket OPEN in queue
releaseRequiresAssigneeAndReason|A|Not assignee / no reason|Release||REPORT_NOT_ASSIGNED
releasingTechnicianIsNotRoutedTheTicketAgain|N|Ticket released|Route ticket|Other technician chosen
droneTicketReleaseNotifiesDroneTeamWithDroneType|N|Drone ticket|Release|Drone team notified
reportCarriesAssignedTechnicianName|N||Get ticket|Technician name
repairLogsCarryAuthorNamesResolvedOncePerUser|N|Repair logs|Get logs|Author names, one lookup per user
"""),
dict(cls="LockerServiceInspectionTest", req="Perform Periodic Inspection", target="LockerService", method="completeSchedule()",
     desc="Periodic inspection checklist: pass advances the due date, fail opens a ticket.", pre="Inspection schedule exists",
     tests="""
allItemsPassingAdvancesTheDueDate|N|Caller assigned technician|All items PASSED|Due date advanced
aFailingItemKeepsTheDueDateAndOpensATicketForTheInspector|N|Caller assigned technician|One item FAILED|Due date kept;Ticket IN_PROGRESS
failingWithAFaultyBoxMarksThatBoxThroughTheFaultFlow|A|Box of another locker|Failed item with box||FAULT_BOX_NOT_IN_LOCKER
itemsMustMatchTheSchedulesChecklist|A||Unknown / missing items||CHECKLIST_ITEM_UNKNOWN
onlyTheAssignedTechnicianOrAnAdminCompletes|A|Caller other technician|Complete||SCHEDULE_NOT_ASSIGNED
adminRecordedFailureGoesToTheSchedulesTechnicianNotTheAdmin|N|Caller ADMIN|One item FAILED|Ticket to schedule's technician
aScheduleWaitingOnItsTicketCannotBeReinspected|A|Ticket of schedule open|Complete again||SCHEDULE_PENDING_REPORT
resolvingThePendingTicketAdvancesTheDueDate|N|Ticket IN_PROGRESS|Resolve ticket|Due date advanced
droneTechnicianCannotReadOrCompleteLockerSchedule|A|Caller DRONE_TECHNICIAN|Complete locker schedule||SCHEDULE_TARGET_FORBIDDEN
droneScheduleFailureDoesNotOpenALockerTicket|N|Drone schedule|One item FAILED|No locker ticket
legacyClientsStillSendAStatus|B||Status PASSED / MAYBE|PASSED accepted|INSPECTION_STATUS_INVALID
checklistIsSplitByLinesOrSemicolons|N||Checklist text|Items split by line / ';'
dueSchedulesAreRemindedOncePerPeriod|B|Schedule due|Run reminder twice|One reminder
"""),
dict(cls="LockerServiceBoxBatchTest", req="Manage Lockers and Boxes", target="LockerService", method="createBox() / createBoxesBatch() / deleteBox()",
     desc="Admin creates and deletes boxes one by one or in batch.", pre="Locker exists",
     tests="""
createBox_Success_BroadcastsLayoutUpdate|N||Box 1 STANDARD|Box AVAILABLE;Layout update sent
createBox_DuplicateNumber_ThrowsBusinessException|A|Box 1 exists|Box 1||BOX_ALREADY_EXISTS
createBoxesBatch_ExplicitList_Success|N||List of boxes|Boxes created
createBoxesBatch_RangeGenerator_Success|N||Range 1-10|10 boxes created
createBoxesBatch_DuplicateInRequest_ThrowsBusinessException|A||Duplicate number in list||DUPLICATE_BOX_NUMBER
deleteBox_Occupied_ThrowsBusinessException|A|Box OCCUPIED|Delete box||BOX_IN_USE
deleteBoxByNumber_Success|N|Box AVAILABLE|Delete by number|Box deleted
deleteBoxesBatch_Success|N|Boxes AVAILABLE / FAULT|Delete batch|Boxes deleted
deleteBoxesBatch_HasOccupied_ThrowsAndDoesNotDelete|A|One box RESERVED|Delete batch|Nothing deleted|BOX_IN_USE
"""),
dict(cls="ReportAttachmentServiceTest", req="Report Locker Incident", target="ReportAttachmentService", method="addByReporter() / addByStaff() / delete()",
     desc="Photos of incident reports: limits per role, stage rules and ownership.", pre="Incident report exists",
     tests="""
reporterAddsPhotosOnlyToOwnUnresolvedReport|A|Report RESOLVED / of another user|Add photos||REPORT_ALREADY_RESOLVED
enforcesReporterStageAndRequestLimits|B|Customer reporter|6 photos||ATTACHMENT_LIMIT_EXCEEDED
reportTotalsAndReporterRequestLimitFollowAdminSettings|B|Limits changed by admin|Photos over limit||ATTACHMENT_LIMIT_EXCEEDED
assignedTechnicianAddsInspectionPhotosWithLogNote|N|Ticket IN_PROGRESS;Caller assignee|INSPECTION photos|Photos + log note
otherTechnicianCannotAddPhotos|A|Caller other technician|Add photos||REPORT_NOT_ASSIGNED
technicianCannotAddPhotosToOpenReportOrUseReportStage|A|Report OPEN|Stage REPORT||REPORT_NOT_IN_PROGRESS
adminCanAddAnyStageRegardlessOfStatus|N|Caller ADMIN;Report RESOLVED|Any stage|Photos added
rejectsSamePhotoTwiceInOneRequest|A||Same photo twice||ATTACHMENT_DUPLICATE
photoUploadedByAnotherUserIsRejected|A||Photo uploaded by other user||MEDIA_OWNER_MISMATCH
uploaderDeletesBeforeResolutionAdminAnytime|A|Report RESOLVED;Caller uploader|Delete photo||ATTACHMENT_DELETE_FORBIDDEN
deleteRejectsAttachmentFromAnotherReport|A||Attachment of another report|Rejected
capturedAtAcceptsLocalAndOffsetIsoFormats|B||capturedAt local / +07:00|Both accepted
"""),
dict(cls="IotServiceTest", req="Pick Up Parcel", target="IotService", method="unlockWithCode() / confirmDropWithCode() / endRentalWithCode()",
     desc="Kiosk PIN / QR code: open the box, confirm drop, end rental and lock after wrong codes.", pre="Locker online",
     tests="""
unlockWithCodeCompletesOrderWhenPickingUpFromStoring|N|Order STORING|Correct PIN|Box opened;Order completed
unlockWithCodeStillCompletesSendPickup|N|SEND order STORING|Correct PIN|Order completed
unlockCompletesOrderWhenPickingUpFromReturned|N|Order RETURNED|Correct code|Order completed
unlockWithCodeRejectsCodeAtWrongLocker|A|Order at another locker|PIN|Rejected
wrongCodeAtKioskStillReadsAsInvalid|A||Wrong PIN|WRONG (invalid)
lockoutAttemptsAndDurationFollowAdminSettings|B|Lockout settings|Wrong PIN max times|Box locked for duration
orderServiceOutageIsNotCountedAsWrongCode|A|order-service down|PIN|Not counted as wrong
verifyAccessRejectsCanceledCredential|A|Order CANCELED|Code|Rejected
unlockWithCodeDeniesUnpaidDropOffWithoutLockingTheBox|A|Order INITIALIZED, UNPAID|Send code|ORDER_UNPAID;Box not locked
unlockWithCodeAtDropOffRecordsOpeningAndAsksForConfirmation|N|Order INITIALIZED, PAID|Send code|Opening recorded;CONFIRM_DROP
unlockWithCodeDoesNotCompleteOrderWhenDroppingOffAtInitialized|B|Order INITIALIZED|Send code|Not completed
confirmDropWithCodeConfirmsOnBehalfOfOwnerAfterRecentOpen|N|Box opened recently|Confirm drop|Order STORING
confirmDropWithCodeRequiresARecentOpening|A|Box not opened recently|Confirm drop|NOT_OPENED_RECENTLY
confirmDropWithCodeRejectsCodeFromAnotherLocker|A|Code of another locker|Confirm drop|Rejected
confirmDropWithCodeRejectsOrderPastDropOff|A|Order STORING|Confirm drop|ORDER_STATUS_INVALID
unlockWithCodeOnActiveRentalReportsRentalAccess|N|Rental STORING|Rental PIN|RENTAL_ACCESS
unlockWithCodeDoesNotCompleteRentalOnReopen|B|Rental STORING|Reopen with PIN|Rental not completed
unlockDoesNotCompleteRentalOnReopen|B|Rental STORING|Reopen from app|Rental not completed
unlockWithCodeDeniesExpiredRental|A|Rental expired|Rental PIN|RENTAL_EXPIRED
endRentalWithCodeReleasesRentalAfterRecentOpen|N|Rental opened recently|End rental|Order COMPLETED
endRentalWithCodeRejectsNonRentalOrder|A|SEND order|End rental|ORDER_TYPE_INVALID
stuckBoxCannotBeOpenedOrReleasedWithTheCode|A|Box incident open|Code|BOX_INCIDENT_OPEN
unlockKeepsDoorOpenResultEvenWhenAutoCompleteFails|A|Auto-complete fails|Correct PIN|Door-open result kept
unlockWithCodeLogsClearTimeoutWhenCabinetNeverAnswers|A|Cabinet does not answer|Correct PIN|TIMEOUT||||Timeout logged
unlockWithCodeLogsSendFailureSeparatelyFromTimeout|A|MQTT send fails|Correct PIN|FAILED||||Send failure logged
"""),
dict(cls="CabinetControlServiceTest", req="Manage IoT Devices", target="CabinetControlService", method="openBox() / lid() / lidJog() / testOpenBox()",
     desc="Web control of a cabinet (open box, lid, jog) with scope and test-open rules.", pre="Locker exists",
     tests="""
adminControlsAnyLocker|N|Caller ADMIN|Open box|ACCEPTED
assignedTechnicianControlsOwnLocker|N|Caller assigned technician|Open box|Accepted
otherTechnicianIsForbidden|A|Caller other technician|Open box||CABINET_FORBIDDEN
logsRespectLockerScope|A|Caller other technician|Read logs||CABINET_FORBIDDEN
unknownLockerIsNotFound|A|Locker missing|Open box||LOCKER_NOT_FOUND
webCommandIsLoggedWithItsResult|N|Caller ADMIN|LID_OPEN|ACCEPTED||||Command + result logged
timeoutIsStillLoggedWhenCabinetIsOffline|A|Cabinet offline|BOX_OPEN|TIMEOUT||||Timeout logged
jogLogsRevolutionsAndDirection|N|Caller ADMIN|LID_JOG 2 revs|ACCEPTED||||Revs + direction logged
jogRejectsBadDirectionAndRevs|A||Bad direction / revs||JOG_DIRECTION_INVALID
invalidLidActionRejected|A||Lid action 'X'||LID_ACTION_INVALID
failedResultMapsToNotAccepted|A|Cabinet result FAILED|Open box||BusinessException
panelPollingIsNotLogged|B||Panel polling|No log entry
testOpenIsOffByDefault|B|Test open not configured|Test open|TEST_OPEN_DISABLED
testOpenNeedsBothTheAccountAndTheLockerOnTheList|A|Account / locker not listed|Test open|TEST_OPEN_..._NOT_ALLOWED
allowedTesterOpensAnyFreeBoxOfTheLockerAndItIsLogged|N|Tester allowed|Free box|ACCEPTED||||BOX_OPEN_TEST logged
testOpenNeverOpensABoxHoldingAnOrderOrABoxOfAnotherLocker|A|Box in use / other locker|Test open|BOX_IN_USE / BOX_NOT_IN_LOCKER
"""),
dict(cls="LockerMqttServiceTest", req="Execute Cabinet Command", target="LockerMqttService", method="sendUnlockCommandAsync() / messageArrived()",
     desc="MQTT contract with the Pi: commands, results, door status and heartbeats.", pre="MQTT client mocked",
     tests="""
openCommandMatchesContract|N||Open box 3|cabinet/{id}/command/open;boxId + slotIndex
openCommandWithoutLayoutStillCarriesBoxId|B|No layout|Open box|boxId in payload
restartCommandMatchesContract|N||Restart|RESTART command
boxStateSyncMatchesContract|N||Box OCCUPIED|State sync payload
cabinetResultCompletesPendingCommand|N|Command pending|Result SUCCESS|Command completed
restartResultCompletesPendingCommand|N|Restart pending|Result ACCEPTED|Command completed
doorStatusWithBoxIdUpdatesThatBox|N||Door status with boxId|Box updated
doorStatusWithoutBoxIdIsResolvedBySlot|B||Door CLOSED, slot only|Box found by slot
doorStatusForUnknownSlotIsDropped|A||Unknown slot|Dropped
heartbeatIdentifiesDeviceByMac|N||Heartbeat with MAC|Device by MAC
heartbeatWithoutMacFallsBackToTopic|B||Heartbeat without MAC|Device by topic;ONLINE
provisioningMessagesAreRouted|N||iot/{mac}/provision|Routed
controlEventsGoToCabinetLog|N||Control event|Cabinet log
bluetoothOpenEventsAlsoReachTheOrderFlow|N||BOX_OPEN_BLE event|Order flow notified
"""),
dict(cls="DronePickupServiceTest", req="Process Drone Order", target="DronePickupService", method="offerPending() / busy()",
     desc="Offer home pickups to the nearest free drone technician on duty.", pre="Drone order AWAITING_DISPATCH",
     tests="""
offerPendingNeverInvitesATechnicianBeyondThePickupRadius|B|Technician outside radius|Offer pickup|Not invited
offerPendingFallsBackToOnDutyTechnicianWhenLocationIsStale|B|Location stale, on duty|Offer pickup|Technician invited
activeAcceptedPickupKeepsTechnicianBusy|N|Pickup PICKUP_ASSIGNED|Check busy|Busy
droppedParcelMissionDoesNotKeepTechnicianBusy|N|Mission DROP_REPORTED|Check busy|Not busy
stalePickupOfCanceledOrderDoesNotKeepTechnicianBusy|A|Order CANCELED|Check busy|Not busy
staleActiveMissionOfCompletedOrderDoesNotKeepTechnicianBusy|A|Order COMPLETED|Check busy|Not busy
"""),
dict(cls="DroneRefundServiceTest", req="Book Drone Delivery", target="DroneRefundService", method="refundCanceledOrder() / refundLatePayment()",
     desc="Refund paid drone (and locker) orders that were cancelled or failed.", pre="Order closed",
     tests="""
refundsPaidDroneOrderThatWasCanceled|N|Drone order CANCELED, paid|Run refund|REFUND_PENDING
refundsPaidLockerOrdersThatWereCanceledToo|N|Rental CANCELED, paid|Run refund|REFUND_PENDING
refundsWhatWasPaidWhenCanceledWhileWeightSurchargeIsStillOwed|B|Surcharge UNPAID|Run refund|Paid part refunded
refundsMoneyThatArrivedAfterTheOrderWasAlreadyRefunded|A|Order REFUNDED;Late money|Run refund|Late money refunded
latePaymentRefundLeavesActiveOrdersAlone|A|Order AWAITING_DISPATCH|Run refund|No refund
ignoresUnpaidOrStillActiveOrders|A|Order UNPAID / active|Run refund|No refund
doesNotRefundTwice|B|Order REFUNDED|Run refund|No second refund
doesNotRequestARefundAgainWhileOneIsPending|B|Refund pending|Run refund|No new request
doesNotCallAnOrderRefundedWhenNothingCameBack|B|Paid 0|Run refund|Not REFUNDED
refundReasonSaysWhyTheDroneOrderClosed|N|Closed by WEATHER|Run refund|Reason mentions weather
keepsOrderPaidWhenPaymentServiceFails|A|payment-service fails|Run refund|Order stays paid
"""),
dict(cls="DroneWeatherServiceTest", req="Book Drone Delivery", target="DroneWeatherService", method="assessJourney() / assessRoute()",
     desc="Check the forecast along the drone route (Open-Meteo, fallback MET Norway).", pre="Drone route known",
     tests="""
reportsUnsafeWhenRainIsForecastAtAnIntermediateRoutePoint|N|Rain at middle point|Check route|UNSAFE
journeyStartsAtTheSendersPickupPointAndRainThereBlocksTheOrder|N|Rain at pickup point|Check route|UNSAFE
metNorwayRainShowersMakeTheRouteUnsafe|N|Open-Meteo down;MET rain showers|Check route|UNSAFE
fallsBackToMetNorwayWhenOpenMeteoFailsAndReportsTheProvider|A|Open-Meteo down|Check route|MET Norway used
bothProvidersDownMeansUnavailableAndIsNotCached|A|Both providers down|Check route|UNAVAILABLE, not cached
missingForecastOnlyBlocksWhenAdminRequiresIt|B|Forecast missing|Check route|Blocks only if required
adminWeatherRulesApplyWithoutRestart|N|Admin changed rules|Check route|New rules applied
acceptsOpenMeteoUtcTimestampsWithoutOffset|B||UTC time without offset|Parsed correctly
"""),
dict(cls="AssistantServiceTest", req="Ask AI Assistant", target="AssistantService", method="ask()",
     desc="Answer questions from documents and the asker's own orders with citations.", pre="Customer signed in",
     tests="""
generalQuestionNeverLoadsOrders|N||General question|Orders not loaded
orderQuestionWithoutMatchingDocumentsStillAsksTheModelWithTheOrderData|N||Order question|Model called with orders
followUpToAnOrderQuestionKeepsTheOrderData|N|Previous order question|Follow-up|Order data kept
orderContextSettingOffNeverLoadsOrders|B|Order context off|Order question|Orders not loaded
orderServiceFailureWithDocumentsAnswersFromDocumentsOnly|A|order-service down;Documents match|Order question|Answer from documents
orderServiceFailureWithoutDocumentsRefusesWithoutCallingTheModel|A|order-service down;No documents|Order question|Refusal, model not called
unaccentedQuestionIsRestoredForRetrievalAndTheModelButStoredAsTyped|N||Question without diacritics|Restored for search;Stored as typed
unaccentedOrderQuestionIsDetectedAfterRestoration|N||'don hang cua toi'|Detected as order question
restorationFailureUsesTheTypedQuestion|A|Restoration fails|Question|Typed question used
citationIndexPastTheChunksMapsToTheOrderSourceOnlyWhenOrdersWereSent|B|Orders sent|Citation index > chunks|Mapped to order source
"""),
dict(cls="DroneHomePickupFlowPostgresTest", req="Book Drone Delivery", target="DroneOrderBookingService", method="quote() / create()",
     desc="Home pickup drone flow on a real PostgreSQL database (Testcontainers).", pre="PostgreSQL container (Docker)",
     tests="""
quoteAndBookingPickTheLockerNearestToTheSender|N||Pickup location|Nearest locker;Box RESERVED
bookingFallsBackToTheNextLockerWhenTheNearestCannotServe|A|Nearest locker FAULT / MAINTENANCE|Book|Next locker used
bookingEnforcesRequiredFieldsRangeAndWeightLimit|B||Missing address / too heavy / out of range||DRONE_PAYLOAD_TOO_HEAVY
sameIdempotencyKeyReturnsTheSameOrderWithoutReservingAgain|B|Order booked|Same idempotency key|Same order
bookingRejectsAReceiveBoxThatBelongsToAnotherLocker|A||Box of another locker||DRONE_DESTINATION_CELL_LOCKER_MISMATCH
paymentOffersThePickupToTheNearestIdleTechnicianOnDuty|N|Order paid|Payment event|PICKUP_ASSIGNED offer
decliningOrIgnoringAnOfferPassesItToTheNextNearestTechnician|N|Offer pending|Decline / timeout|Next technician
aBusyTechnicianIsSkippedAndAnOrderWaitsWhenNobodyIsFree|A|All technicians busy|Offer|Order waits
staleLocationIsOnlyAFallbackAndOffDutyIsNeverOffered|B|Stale / off duty|Offer|Off duty never offered
acceptedTechnicianCannotGoOffDutyAndIsReplacedWhenTheyNeverShowUp|A|Pickup accepted|End shift / no show||DRONE_TECHNICIAN_HAS_ACTIVE_PICKUP
missedPaymentHookIsRepairedByTheDispatchSweep|A|Payment hook missed|Dispatch sweep|Offer created
adminAssignsATechnicianByHand|N|Caller ADMIN|Assign technician|PICKUP_ASSIGNED
fullJourneyFromHomePickupToTheReceiverLocker|N|Order paid|Pickup, load, fly, land|Ready for pickup
senderMayCancelUntilTheParcelIsPickedUpAndTheTechnicianIsFreed|B|Before / after pickup|Cancel|CANCELED / DRONE_ORDER_STATUS_INVALID
"""),
]
