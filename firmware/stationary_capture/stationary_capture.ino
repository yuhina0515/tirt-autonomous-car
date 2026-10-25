// Generated from CAGEBOT XML; physical acceptance remains pending.
#include <Arduino.h>
long driveMode;
long configReady;
unsigned long periodMs;
unsigned long logPeriodMs;
unsigned long maxTickGapMs;
long onLevel;
long offLevel;
long weightFloor;
long minContrast;
unsigned long validConfirmMs;
long candidateBand;
long maxJump;
unsigned long uncertainStopMs;
unsigned long acquireTimeoutMs;
unsigned long maxRunMs;
long basePwm;
long curvePwm;
long uncertainPwm;
long minPwm;
long maxPwm;
long kp;
long kd;
long slewPwm;
long lapEnabled;
unsigned long searchTimeoutMs;
unsigned long gapTimeoutMs;
unsigned long wideTimeoutMs;
long searchEdge;
long searchPwm;
long departurePwm;
unsigned long departureConfirmMs;
unsigned long minLapMs;
unsigned long finishConfirmMs;
long widePwm;
unsigned long wideHintMs;
unsigned long nowMs;
unsigned long lastTickMs;
unsigned long dtMs;
unsigned long logAtMs;
unsigned long runAtMs;
unsigned long buttonAtMs;
unsigned long candidateAtMs;
unsigned long uncertainAtMs;
unsigned long elapsedMs;
unsigned long tick;
unsigned long rejected;
unsigned long timingFaults;
unsigned long recoveryBudgetMs;
unsigned long lineAtMs;
unsigned long wideAtMs;
unsigned long hintAtMs;
long controlState;
long reason;
long maskF;
long activeCount;
long contrast;
long maxStrength;
long minStrength;
long weighted;
long totalW;
long candidatePos;
long lastPosition;
long pendingPos;
long candidatePending;
long difference;
long absDifference;
long validCandidate;
long candidateAccepted;
long hasPosition;
long derivative;
long slope;
long tickDt;
long correction;
long lastCorrection;
long magnitude;
long targetBase;
long limitPwm;
long leftTarget;
long rightTarget;
long leftPwm;
long rightPwm;
long buttonLow;
long buttonPrevious;
long buttonReleased;
long buttonEvent;
long historyReady;
long wasTracking;
long recoveryKind;
long departed;
long linePending;
long widePending;
long hintValid;
long hintPosition;
long wideTurn;
long line0;
long background0;
long raw0;
long norm0;
long smooth0;
long on0;
long weight0;
long line1;
long background1;
long raw1;
long norm1;
long smooth1;
long on1;
long weight1;
long line2;
long background2;
long raw2;
long norm2;
long smooth2;
long on2;
long weight2;
long line3;
long background3;
long raw3;
long norm3;
long smooth3;
long on3;
long weight3;
long line4;
long background4;
long raw4;
long norm4;
long smooth4;
long on4;
long weight4;
void read_sensors();
void button_update();
void start_run();
void classify();
void check_candidate();
void steer();
void hold_course();
void begin_recovery();
void recover();
void lap_update();
void run_control();
void write_motors();
void telemetry();
void read_sensors() {
maskF = 0L;
activeCount = 0L;
maxStrength = 0L;
minStrength = 1000L;
weighted = 0L;
totalW = 0L;
raw0 = analogRead(A5);
norm0 = (((raw0 - background0) * 1000L) / (line0 - background0));
if ((norm0 < 0L)) {
norm0 = 0L;
}
if ((norm0 > 1000L)) {
norm0 = 1000L;
}
if ((historyReady == 0L)) {
smooth0 = norm0;
}
else {
smooth0 = ((smooth0 + (norm0 * 3L)) / 4L);
}
on0 = 0L;
weight0 = 0L;
raw1 = analogRead(A4);
norm1 = (((raw1 - background1) * 1000L) / (line1 - background1));
if ((norm1 < 0L)) {
norm1 = 0L;
}
if ((norm1 > 1000L)) {
norm1 = 1000L;
}
if ((historyReady == 0L)) {
smooth1 = norm1;
}
else {
smooth1 = ((smooth1 + (norm1 * 3L)) / 4L);
}
if ((smooth1 >= onLevel)) {
on1 = 1L;
}
else if ((smooth1 <= offLevel)) {
on1 = 0L;
}
maskF = (maskF + (on1 * 8L));
activeCount = (activeCount + on1);
if ((smooth1 > maxStrength)) {
maxStrength = smooth1;
}
if ((smooth1 < minStrength)) {
minStrength = smooth1;
}
weight1 = 0L;
if ((on1 == 1L)) {
weight1 = (smooth1 - weightFloor);
}
if ((weight1 < 0L)) {
weight1 = 0L;
}
totalW = (totalW + weight1);
weighted = (weighted + (weight1 * -1000L));
raw2 = analogRead(A3);
norm2 = (((raw2 - background2) * 1000L) / (line2 - background2));
if ((norm2 < 0L)) {
norm2 = 0L;
}
if ((norm2 > 1000L)) {
norm2 = 1000L;
}
if ((historyReady == 0L)) {
smooth2 = norm2;
}
else {
smooth2 = ((smooth2 + (norm2 * 3L)) / 4L);
}
if ((smooth2 >= onLevel)) {
on2 = 1L;
}
else if ((smooth2 <= offLevel)) {
on2 = 0L;
}
maskF = (maskF + (on2 * 4L));
activeCount = (activeCount + on2);
if ((smooth2 > maxStrength)) {
maxStrength = smooth2;
}
if ((smooth2 < minStrength)) {
minStrength = smooth2;
}
weight2 = 0L;
if ((on2 == 1L)) {
weight2 = (smooth2 - weightFloor);
}
if ((weight2 < 0L)) {
weight2 = 0L;
}
totalW = (totalW + weight2);
weighted = (weighted + (weight2 * 0L));
raw3 = analogRead(A2);
norm3 = (((raw3 - background3) * 1000L) / (line3 - background3));
if ((norm3 < 0L)) {
norm3 = 0L;
}
if ((norm3 > 1000L)) {
norm3 = 1000L;
}
if ((historyReady == 0L)) {
smooth3 = norm3;
}
else {
smooth3 = ((smooth3 + (norm3 * 3L)) / 4L);
}
if ((smooth3 >= onLevel)) {
on3 = 1L;
}
else if ((smooth3 <= offLevel)) {
on3 = 0L;
}
maskF = (maskF + (on3 * 2L));
activeCount = (activeCount + on3);
if ((smooth3 > maxStrength)) {
maxStrength = smooth3;
}
if ((smooth3 < minStrength)) {
minStrength = smooth3;
}
weight3 = 0L;
if ((on3 == 1L)) {
weight3 = (smooth3 - weightFloor);
}
if ((weight3 < 0L)) {
weight3 = 0L;
}
totalW = (totalW + weight3);
weighted = (weighted + (weight3 * 1000L));
raw4 = analogRead(A1);
norm4 = (((raw4 - background4) * 1000L) / (line4 - background4));
if ((norm4 < 0L)) {
norm4 = 0L;
}
if ((norm4 > 1000L)) {
norm4 = 1000L;
}
if ((historyReady == 0L)) {
smooth4 = norm4;
}
else {
smooth4 = ((smooth4 + (norm4 * 3L)) / 4L);
}
on4 = 0L;
weight4 = 0L;
historyReady = 1L;
contrast = (maxStrength - minStrength);
}

void button_update() {
buttonEvent = 0L;
buttonLow = (digitalRead(12) == 0L);
if ((buttonLow != buttonPrevious)) {
buttonAtMs = nowMs;
buttonPrevious = buttonLow;
}
elapsedMs = (nowMs - buttonAtMs);
if (((buttonLow == 0L) && (elapsedMs >= 25L))) {
buttonReleased = 1L;
}
if ((((buttonLow == 1L) && (buttonReleased == 1L)) && (elapsedMs >= 25L))) {
buttonReleased = 0L;
buttonEvent = 1L;
}
}

void start_run() {
controlState = 1L;
reason = 8L;
runAtMs = nowMs;
departed = 0L;
linePending = 0L;
widePending = 0L;
recoveryKind = 0L;
hintValid = 0L;
hintPosition = 0L;
wideTurn = 0L;
candidatePending = 0L;
hasPosition = 0L;
historyReady = 0L;
lastPosition = 0L;
lastCorrection = 0L;
derivative = 0L;
leftPwm = 0L;
rightPwm = 0L;
}

void classify() {
validCandidate = 0L;
candidateAccepted = 0L;
if ((activeCount == 0L)) {
reason = 1L;
}
else if ((activeCount == 3L)) {
reason = 2L;
}
else if (((on1 == 1L) && ((on2 == 0L) && (on3 == 1L)))) {
reason = 3L;
}
else if ((contrast < minContrast)) {
reason = 11L;
}
else {
validCandidate = 1L;
reason = 0L;
candidatePos = (weighted / totalW);
}
}

void check_candidate() {
classify();
if ((validCandidate == 1L)) {
difference = (candidatePos - lastPosition);
absDifference = difference;
if ((absDifference < 0L)) {
absDifference = (0L - absDifference);
}
if (((controlState == 2L) && (absDifference <= maxJump))) {
candidateAccepted = 1L;
candidatePending = 0L;
}
else {
difference = (candidatePos - pendingPos);
absDifference = difference;
if ((absDifference < 0L)) {
absDifference = (0L - absDifference);
}
if (((candidatePending == 0L) || (absDifference > candidateBand))) {
candidatePending = 1L;
candidateAtMs = nowMs;
pendingPos = candidatePos;
}
elapsedMs = (nowMs - candidateAtMs);
if ((elapsedMs >= validConfirmMs)) {
candidateAccepted = 1L;
}
else {
reason = 8L;
if ((controlState == 2L)) {
reason = 4L;
}
}
}
}
else {
candidatePending = 0L;
}
}

void steer() {
slope = 0L;
tickDt = dtMs;
if (((hasPosition == 1L) && (wasTracking == 1L))) {
slope = (((candidatePos - lastPosition) * 1000L) / tickDt);
}
else {
derivative = 0L;
}
if ((slope > 200000L)) {
slope = 200000L;
}
if ((slope < -200000L)) {
slope = -200000L;
}
derivative = (((derivative * 3L) + slope) / 4L);
correction = (((kp * candidatePos) + (kd * derivative)) / 1000L);
magnitude = candidatePos;
if ((magnitude < 0L)) {
magnitude = (0L - magnitude);
}
targetBase = (basePwm - (((basePwm - curvePwm) * magnitude) / 1000L));
limitPwm = (targetBase - minPwm);
if ((correction > limitPwm)) {
correction = limitPwm;
}
if ((correction < (0L - limitPwm))) {
correction = (0L - limitPwm);
}
leftTarget = (targetBase + correction);
rightTarget = (targetBase - correction);
lastCorrection = correction;
lastPosition = candidatePos;
hasPosition = 1L;
if ((magnitude >= searchEdge)) {
hintValid = 1L;
hintPosition = candidatePos;
hintAtMs = nowMs;
}
controlState = 2L;
reason = 0L;
candidatePending = 0L;
}

void hold_course() {
limitPwm = (uncertainPwm - minPwm);
correction = lastCorrection;
if ((correction > limitPwm)) {
correction = limitPwm;
}
if ((correction < (0L - limitPwm))) {
correction = (0L - limitPwm);
}
leftTarget = (uncertainPwm + correction);
rightTarget = (uncertainPwm - correction);
}

void begin_recovery() {
controlState = 3L;
uncertainAtMs = nowMs;
derivative = 0L;
recoveryKind = 0L;
recoveryBudgetMs = uncertainStopMs;
wideTurn = 0L;
if ((activeCount == 0L)) {
recoveryKind = 1L;
recoveryBudgetMs = gapTimeoutMs;
if ((lastPosition <= (0L - searchEdge))) {
recoveryKind = 2L;
recoveryBudgetMs = searchTimeoutMs;
}
else if ((lastPosition >= searchEdge)) {
recoveryKind = 3L;
recoveryBudgetMs = searchTimeoutMs;
}
}
else if ((activeCount == 3L)) {
recoveryKind = 4L;
recoveryBudgetMs = wideTimeoutMs;
elapsedMs = (nowMs - hintAtMs);
if ((((hintValid == 1L) && (wideHintMs > 0L)) && (elapsedMs <= wideHintMs))) {
if ((hintPosition < 0L)) {
wideTurn = -1L;
}
else {
wideTurn = 1L;
}
}
}
}

void recover() {
hold_course();
if ((activeCount == 0L)) {
if ((recoveryKind == 2L)) {
leftTarget = 0L;
rightTarget = searchPwm;
reason = 14L;
}
else if ((recoveryKind == 3L)) {
rightTarget = 0L;
leftTarget = searchPwm;
reason = 14L;
}
else if ((recoveryKind == 1L)) {
leftTarget = uncertainPwm;
rightTarget = uncertainPwm;
reason = 15L;
}
else if ((recoveryKind == 4L)) {
if ((wideHintMs > 0L)) {
leftTarget = uncertainPwm;
rightTarget = uncertainPwm;
reason = 15L;
if ((wideTurn == -1L)) {
leftTarget = 0L;
rightTarget = searchPwm;
reason = 14L;
}
else if ((wideTurn == 1L)) {
rightTarget = 0L;
leftTarget = searchPwm;
reason = 14L;
}
}
}
}
else if (((activeCount == 3L) && (recoveryKind == 4L))) {
leftTarget = widePwm;
rightTarget = widePwm;
reason = 16L;
}
}

void lap_update() {
if (((controlState == 2L) && (candidateAccepted == 1L))) {
if ((linePending == 0L)) {
linePending = 1L;
lineAtMs = nowMs;
}
elapsedMs = (nowMs - lineAtMs);
if ((elapsedMs >= departureConfirmMs)) {
departed = 1L;
}
}
else {
linePending = 0L;
}
if ((((lapEnabled == 1L) && (departed == 1L)) && (((controlState == 3L) && (recoveryKind == 4L)) && (activeCount == 3L)))) {
elapsedMs = (nowMs - runAtMs);
if ((elapsedMs >= minLapMs)) {
if ((widePending == 0L)) {
widePending = 1L;
wideAtMs = nowMs;
}
elapsedMs = (nowMs - wideAtMs);
if ((elapsedMs >= finishConfirmMs)) {
controlState = 4L;
reason = 13L;
leftTarget = 0L;
rightTarget = 0L;
}
}
else {
widePending = 0L;
}
}
else {
widePending = 0L;
}
}

void run_control() {
elapsedMs = (nowMs - runAtMs);
if ((elapsedMs >= maxRunMs)) {
controlState = 4L;
reason = 10L;
}
else if (((controlState == 1L) && (elapsedMs >= acquireTimeoutMs))) {
controlState = 5L;
reason = 9L;
leftTarget = 0L;
rightTarget = 0L;
}
else {
elapsedMs = (nowMs - uncertainAtMs);
if (((controlState == 3L) && (elapsedMs >= recoveryBudgetMs))) {
controlState = 5L;
reason = 1L;
leftTarget = 0L;
rightTarget = 0L;
}
else {
wasTracking = (controlState == 2L);
check_candidate();
if ((candidateAccepted == 1L)) {
steer();
}
else {
rejected = (rejected + 1L);
if ((controlState == 2L)) {
begin_recovery();
}
if ((controlState == 3L)) {
recover();
}
if ((((controlState == 1L) && (lapEnabled == 1L)) && (activeCount == 3L))) {
leftTarget = departurePwm;
rightTarget = departurePwm;
reason = 12L;
}
}
lap_update();
}
}
}

void write_motors() {
if ((leftTarget > maxPwm)) {
leftTarget = maxPwm;
}
if ((leftTarget < 0L)) {
leftTarget = 0L;
}
if ((leftTarget <= 0L)) {
leftPwm = 0L;
}
else if ((leftTarget > leftPwm)) {
leftPwm = (leftPwm + slewPwm);
if ((leftPwm < minPwm)) {
leftPwm = minPwm;
}
if ((leftPwm > leftTarget)) {
leftPwm = leftTarget;
}
}
else {
leftPwm = leftTarget;
}
if ((rightTarget > maxPwm)) {
rightTarget = maxPwm;
}
if ((rightTarget < 0L)) {
rightTarget = 0L;
}
if ((rightTarget <= 0L)) {
rightPwm = 0L;
}
else if ((rightTarget > rightPwm)) {
rightPwm = (rightPwm + slewPwm);
if ((rightPwm < minPwm)) {
rightPwm = minPwm;
}
if ((rightPwm > rightTarget)) {
rightPwm = rightTarget;
}
}
else {
rightPwm = rightTarget;
}
digitalWrite(7,LOW);
digitalWrite(4,HIGH);
analogWrite(5,leftPwm);
analogWrite(6,rightPwm);
}

void telemetry() {
elapsedMs = (nowMs - logAtMs);
if ((elapsedMs >= logPeriodMs)) {
logAtMs = nowMs;
Serial.print(nowMs);
Serial.print(",");
Serial.print(tick);
Serial.print(",");
Serial.print(dtMs);
Serial.print(",");
Serial.print(raw0);
Serial.print(",");
Serial.print(raw1);
Serial.print(",");
Serial.print(raw2);
Serial.print(",");
Serial.print(raw3);
Serial.print(",");
Serial.print(raw4);
Serial.print(",");
Serial.print(maskF);
Serial.print(",");
Serial.print(controlState);
Serial.print(",");
Serial.print(reason);
Serial.print(",");
Serial.print(candidatePos);
Serial.print(",");
Serial.print(lastPosition);
Serial.print(",");
Serial.print(contrast);
Serial.print(",");
Serial.print(leftPwm);
Serial.print(",");
Serial.print(rightPwm);
Serial.print(",");
Serial.print(rejected);
Serial.print(",");
Serial.println(timingFaults);
}
}
void setup() {
pinMode(5,OUTPUT);
pinMode(6,OUTPUT);
pinMode(7,OUTPUT);
pinMode(4,OUTPUT);
pinMode(A5,INPUT);
pinMode(A4,INPUT);
pinMode(A3,INPUT);
pinMode(A2,INPUT);
pinMode(A1,INPUT);
pinMode(12,INPUT);
Serial.begin(115200);
driveMode = 0L;
configReady = 0L;
periodMs = 20L;
logPeriodMs = 20L;
maxTickGapMs = 50L;
onLevel = 650L;
offLevel = 350L;
weightFloor = 300L;
minContrast = 200L;
validConfirmMs = 30L;
candidateBand = 250L;
maxJump = 450L;
uncertainStopMs = 120L;
acquireTimeoutMs = 2000L;
maxRunMs = 180000L;
basePwm = 100L;
curvePwm = 65L;
uncertainPwm = 45L;
minPwm = 25L;
maxPwm = 100L;
kp = 45L;
kd = 1L;
slewPwm = 6L;
lapEnabled = 1L;
searchTimeoutMs = 650L;
gapTimeoutMs = 200L;
wideTimeoutMs = 350L;
searchEdge = 600L;
searchPwm = 65L;
departurePwm = 45L;
departureConfirmMs = 300L;
minLapMs = 15000L;
finishConfirmMs = 250L;
widePwm = 45L;
wideHintMs = 0L;
nowMs = 0L;
lastTickMs = 0L;
dtMs = 0L;
logAtMs = 0L;
runAtMs = 0L;
buttonAtMs = 0L;
candidateAtMs = 0L;
uncertainAtMs = 0L;
elapsedMs = 0L;
tick = 0L;
rejected = 0L;
timingFaults = 0L;
recoveryBudgetMs = 0L;
lineAtMs = 0L;
wideAtMs = 0L;
hintAtMs = 0L;
controlState = 6L;
reason = 0L;
maskF = 0L;
activeCount = 0L;
contrast = 0L;
maxStrength = 0L;
minStrength = 0L;
weighted = 0L;
totalW = 0L;
candidatePos = 0L;
lastPosition = 0L;
pendingPos = 0L;
candidatePending = 0L;
difference = 0L;
absDifference = 0L;
validCandidate = 0L;
candidateAccepted = 0L;
hasPosition = 0L;
derivative = 0L;
slope = 0L;
tickDt = 0L;
correction = 0L;
lastCorrection = 0L;
magnitude = 0L;
targetBase = 0L;
limitPwm = 0L;
leftTarget = 0L;
rightTarget = 0L;
leftPwm = 0L;
rightPwm = 0L;
buttonLow = 0L;
buttonPrevious = 0L;
buttonReleased = 0L;
buttonEvent = 0L;
historyReady = 0L;
wasTracking = 0L;
recoveryKind = 0L;
departed = 0L;
linePending = 0L;
widePending = 0L;
hintValid = 0L;
hintPosition = 0L;
wideTurn = 0L;
line0 = 35L;
background0 = 500L;
raw0 = 0L;
norm0 = 0L;
smooth0 = 0L;
on0 = 0L;
weight0 = 0L;
line1 = 35L;
background1 = 500L;
raw1 = 0L;
norm1 = 0L;
smooth1 = 0L;
on1 = 0L;
weight1 = 0L;
line2 = 35L;
background2 = 500L;
raw2 = 0L;
norm2 = 0L;
smooth2 = 0L;
on2 = 0L;
weight2 = 0L;
line3 = 35L;
background3 = 500L;
raw3 = 0L;
norm3 = 0L;
smooth3 = 0L;
on3 = 0L;
weight3 = 0L;
line4 = 35L;
background4 = 500L;
raw4 = 0L;
norm4 = 0L;
smooth4 = 0L;
on4 = 0L;
weight4 = 0L;
analogWrite(5,0L);
analogWrite(6,0L);
digitalWrite(7,LOW);
digitalWrite(4,HIGH);
nowMs = millis();
lastTickMs = nowMs;
buttonAtMs = nowMs;
}
void loop() {
nowMs = millis();
dtMs = (nowMs - lastTickMs);
if ((dtMs >= periodMs)) {
lastTickMs = nowMs;
tick = (tick + 1L);
leftTarget = 0L;
rightTarget = 0L;
read_sensors();
controlState = 6L;
write_motors();
telemetry();
}
}
