int  SPEED_CURVE;
int  TURN_OUTER_PWM;
int  TURN_INNER_PWM;
unsigned long  TURN_TIMEOUT_MS;
unsigned long  TURN_MIN_MS;
unsigned long  TURN_MEMORY_MS;
unsigned long  TURN_CENTER_CLEAR_MS;
unsigned long  TURN_DIRECTION_CONFIRM_MS;
int  TURN_CONFIRM_COUNT;
int  turnDirection;
int  turnActive;
int  turnFault;
int  turnConfirm;
unsigned long  turnNow;
unsigned long  turnAt;
unsigned long  turnSeenAt;
unsigned long  turnElapsed;
unsigned long  turnAge;
int  centerPending;
unsigned long  centerAt;
unsigned long  centerElapsed;
int  turnCandidate;
unsigned long  turnCandidateAt;
unsigned long  turnCandidateElapsed;
int  GAP_PWM;
unsigned long  GAP_TIMEOUT_MS;
int  gapActive;
unsigned long  gapAt;
unsigned long  gapElapsed;
int  gapConfirm;
unsigned long  MIN_LAP_MS;
unsigned long  MAX_LAP_MS;
unsigned long  DEPART_CONFIRM_MS;
unsigned long  FINISH_CONFIRM_MS;
unsigned long  WIDE_TIMEOUT_MS;
int  WIDE_PWM;
int  lapStarted;
int  lapReady;
int  lapDone;
unsigned long  lapAt;
unsigned long  lapElapsed;
int  departPending;
unsigned long  departAt;
unsigned long  departElapsed;
int  wideActive;
unsigned long  wideAt;
unsigned long  wideElapsed;
int  LIFT_ENABLED;
int  LIFT_CROSSING_INDEX;
unsigned long  LIFT_MARKER_CONFIRM_MS;
unsigned long  LIFT_CLEAR_CONFIRM_MS;
unsigned long  LIFT_WAIT_MS;
int  LIFT_AUTO_EXIT;
int  LIFT_EXIT_PWM;
unsigned long  LIFT_EXIT_TIMEOUT_MS;
int  liftState;
int  liftCrossings;
int  liftMarkerLatched;
int  liftMarkerPending;
unsigned long  liftMarkerAt;
unsigned long  liftMarkerElapsed;
int  liftClearPending;
unsigned long  liftClearAt;
unsigned long  liftClearElapsed;
unsigned long  liftWaitAt;
unsigned long  liftWaitElapsed;
unsigned long  liftExitAt;
unsigned long  liftExitElapsed;
int  liftExitPending;
unsigned long  liftLineAt;
unsigned long  liftLineElapsed;
int  LINE_THRESHOLD;
int  SPEED_STRAIGHT;
int  sensorA1;
int  sensorA2;
int  sensorA3;
int  sensorA4;
int  sensorA5;
int  SPEED_TURN_INNER_MEDIUM;
int  sensorF;
int  WHITE_STOP_COUNT;
int  whiteCount;
int  sumW;
int  countOn;
int  absW;
int  innerSpeed;
int  TURN_KP;
int  rawA1;
int  rawA2;
int  rawA3;
int  rawA4;
int  rawA5;
#include <moto_NeoPixel.h>
moto_NeoPixel strip13= moto_NeoPixel(2,13, NEO_GRB + NEO_KHZ800);
void colorled13(int number,String c)
{
	long rgb_number = strtol(&c[1], NULL, 16);
   int r = rgb_number >> 16;
   int g = rgb_number >> 8 & 0xFF;
   int b = rgb_number & 0xFF;
   if(number <= 0) number = 0;
      else  number--;
   strip13.setPixelColor(number,strip13.Color(r,g,b));
   strip13.show();
}

/**
 * 描述此函式...
 */
void stop2() {
  digitalWrite(7,LOW);
  analogWrite(5,0);
  digitalWrite(4,HIGH);
  analogWrite(6,0);
}

/**
 * Bounded sharp-corner pivot. Outer forward125, inner reverse95.
 * After minimum30ms, F4/F6/F12 starts forward differential capture.
 * Three consecutive captures finish at curve base125, not straight230.
 * Timeout latches stop; no measured angle or automatic restart.
 */
void sharp_turn() {
  turnElapsed = turnNow - turnAt;
  if (turnElapsed >= TURN_TIMEOUT_MS) {
    turnFault = 1;
    turnActive = 0;
    stop2();
  } else {
    if (turnElapsed >= TURN_MIN_MS && (sensorF == 4 || sensorF == 6 || sensorF == 12)) {
      turnConfirm = turnConfirm + 1;
    } else {
      turnConfirm = 0;
    }
    if (turnConfirm >= TURN_CONFIRM_COUNT) {
      turnActive = 0;
      turnDirection = 0;
      turnConfirm = 0;
      whiteCount = 0;
      if (sensorF == 12) {
        digitalWrite(7,LOW);
        analogWrite(5,innerSpeed);
        digitalWrite(4,HIGH);
        analogWrite(6,SPEED_CURVE);
      } else if (sensorF == 6) {
        digitalWrite(7,LOW);
        analogWrite(5,SPEED_CURVE);
        digitalWrite(4,HIGH);
        analogWrite(6,innerSpeed);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,SPEED_CURVE);
        digitalWrite(4,HIGH);
        analogWrite(6,SPEED_CURVE);
      }
    } else {
      if (turnConfirm >= 1) {
        if (sensorF == 12) {
          digitalWrite(7,LOW);
          analogWrite(5,innerSpeed);
          digitalWrite(4,HIGH);
          analogWrite(6,SPEED_CURVE);
        } else if (sensorF == 6) {
          digitalWrite(7,LOW);
          analogWrite(5,SPEED_CURVE);
          digitalWrite(4,HIGH);
          analogWrite(6,innerSpeed);
        } else {
          digitalWrite(7,LOW);
          analogWrite(5,SPEED_CURVE);
          digitalWrite(4,HIGH);
          analogWrite(6,SPEED_CURVE);
        }
      } else {
        if (turnDirection == -1) {
          digitalWrite(7,HIGH);
          analogWrite(5,TURN_INNER_PWM);
          digitalWrite(4,HIGH);
          analogWrite(6,TURN_OUTER_PWM);
        } else {
          digitalWrite(7,LOW);
          analogWrite(5,TURN_OUTER_PWM);
          digitalWrite(4,LOW);
          analogWrite(6,TURN_INNER_PWM);
        }
      }
    }
  }
}

/**
 * Short gap PWM70 with fixed250ms deadline. On side-line return,
 * forward differential capture starts immediately (25/70
 * or45/70 mirrored). No reverse in gap state. Three narrow
 * samples finish; wide line returns to marker handling.
 */
void cross_gap() {
  gapElapsed = turnNow - gapAt;
  if (gapElapsed >= GAP_TIMEOUT_MS) {
    turnFault = 1;
    gapActive = 0;
    stop2();
  } else {
    if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
      gapConfirm = gapConfirm + 1;
    } else {
      gapConfirm = 0;
    }
    if (gapConfirm >= 3 || sensorF == 14) {
      gapActive = 0;
      turnDirection = 0;
      whiteCount = 0;
      if (sensorF == 8) {
        digitalWrite(7,LOW);
        analogWrite(5,25);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 12) {
        digitalWrite(7,LOW);
        analogWrite(5,45);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 2) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,25);
      } else if (sensorF == 6) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,45);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      }
    } else {
      if (sensorF == 8) {
        digitalWrite(7,LOW);
        analogWrite(5,25);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 12) {
        digitalWrite(7,LOW);
        analogWrite(5,45);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 2) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,25);
      } else if (sensorF == 6) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,45);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      }
    }
  }
}

/**
 * Lift: first confirmed wide marker after narrow-line departure,
 * based on user route assumption. Stop without alignment drive;
 * user-requested wait23350ms from stop command, not measured
 * settled feedback. This is below the published27s +/-5% timing.
 * Auto exit PWM45 with1500ms limit. Consume marker once.
 * PWM zero is not active braking. Disable LIFT_ENABLED
 * for the earlier practice mat without a lift.
 */
void lift_control() {
  if (liftState == 1) {
    stop2();
    liftWaitElapsed = turnNow - liftWaitAt;
    if (LIFT_AUTO_EXIT == 1 && liftWaitElapsed >= LIFT_WAIT_MS) {
      liftState = 2;
      liftExitAt = turnNow;
      liftExitPending = 0;
    }
  } else if (liftState == 2) {
    liftExitElapsed = turnNow - liftExitAt;
    if (liftExitElapsed >= LIFT_EXIT_TIMEOUT_MS) {
      turnFault = 1;
      stop2();
    } else {
      if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
        if (liftExitPending == 0) {
          liftExitPending = 1;
          liftLineAt = turnNow;
        }
        liftLineElapsed = turnNow - liftLineAt;
        if (liftLineElapsed >= LIFT_CLEAR_CONFIRM_MS) {
          liftState = 3;
          turnDirection = 0;
          turnCandidate = 0;
          centerPending = 0;
          wideActive = 0;
          whiteCount = 0;
        }
      } else {
        liftExitPending = 0;
      }
      digitalWrite(7,LOW);
      analogWrite(5,LIFT_EXIT_PWM);
      digitalWrite(4,HIGH);
      analogWrite(6,LIFT_EXIT_PWM);
    }
  }
}

void setup()
{
  Serial.begin(115200);
  strip13.begin();
  strip13.show();
  pinMode(12, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
  pinMode(A4, INPUT);
  pinMode(A5, INPUT);
  pinMode(7, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(6, OUTPUT);
    SPEED_CURVE = 125;
  TURN_OUTER_PWM = 125;
  TURN_INNER_PWM = 95;
  TURN_TIMEOUT_MS = 800;
  TURN_MIN_MS = 30;
  TURN_MEMORY_MS = 250;
  TURN_CENTER_CLEAR_MS = 80;
  TURN_DIRECTION_CONFIRM_MS = 15;
  TURN_CONFIRM_COUNT = 3;
  turnDirection = 0;
  turnActive = 0;
  turnFault = 0;
  turnConfirm = 0;
  turnNow = 0;
  turnAt = 0;
  turnSeenAt = 0;
  turnElapsed = 0;
  turnAge = 0;
  centerPending = 0;
  centerAt = 0;
  centerElapsed = 0;
  turnCandidate = 0;
  turnCandidateAt = 0;
  turnCandidateElapsed = 0;
  GAP_PWM = 70;
  GAP_TIMEOUT_MS = 250;
  gapActive = 0;
  gapAt = 0;
  gapElapsed = 0;
  gapConfirm = 0;
  MIN_LAP_MS = 15000;
  MAX_LAP_MS = 180000;
  DEPART_CONFIRM_MS = 100;
  FINISH_CONFIRM_MS = 250;
  WIDE_TIMEOUT_MS = 900;
  WIDE_PWM = 45;
  lapStarted = 0;
  lapReady = 0;
  lapDone = 0;
  lapAt = 0;
  lapElapsed = 0;
  departPending = 0;
  departAt = 0;
  departElapsed = 0;
  wideActive = 0;
  wideAt = 0;
  wideElapsed = 0;
  LIFT_ENABLED = 1;
  LIFT_CROSSING_INDEX = 1;
  LIFT_MARKER_CONFIRM_MS = 30;
  LIFT_CLEAR_CONFIRM_MS = 100;
  LIFT_WAIT_MS = 23350;
  LIFT_AUTO_EXIT = 1;
  LIFT_EXIT_PWM = 45;
  LIFT_EXIT_TIMEOUT_MS = 1500;
  liftState = 0;
  liftCrossings = 0;
  liftMarkerLatched = 0;
  liftMarkerPending = 0;
  liftMarkerAt = 0;
  liftMarkerElapsed = 0;
  liftClearPending = 0;
  liftClearAt = 0;
  liftClearElapsed = 0;
  liftWaitAt = 0;
  liftWaitElapsed = 0;
  liftExitAt = 0;
  liftExitElapsed = 0;
  liftExitPending = 0;
  liftLineAt = 0;
  liftLineElapsed = 0;
  LINE_THRESHOLD = 70;
  SPEED_STRAIGHT = 230;
  sensorA1 = 0;
  sensorA2 = 0;
  sensorA3 = 0;
  sensorA4 = 0;
  sensorA5 = 0;
  SPEED_TURN_INNER_MEDIUM = 8;
  sensorF = 0;
  WHITE_STOP_COUNT = 40;
  whiteCount = 0;
  sumW = 0;
  countOn = 0;
  absW = 0;
  innerSpeed = 0;
  TURN_KP = 100;
  rawA1 = 0;
  rawA2 = 0;
  rawA3 = 0;
  rawA4 = 0;
  rawA5 = 0;
  colorled13(1,"#0000ff");
  while ((digitalRead(12) == 1)) {
    delay(20);
  }
  colorled13(1,"#33ff33");

}


void loop()
{
  // Start on the narrow line LEFT of the large finish patch,
  // facing away from finish. Three-center-sensor control,
  // sharp corners and short gaps. After departure/minimum
  // run, sustained wide line latches finish stop. This is not
  // measured lap localization. Button waits at boot only.
    colorled13(1,"#33ff33");
    // Read all five ADCs; preserve original raw telemetry.
    sensorA1 = analogRead(A1);
    sensorA2 = analogRead(A2);
    sensorA3 = analogRead(A3);
    sensorA4 = analogRead(A4);
    sensorA5 = analogRead(A5);
    rawA1 = sensorA1;
    rawA2 = sensorA2;
    rawA3 = sensorA3;
    rawA4 = sensorA4;
    rawA5 = sensorA5;
    // Exclude A1 and A5 from decisions; control uses A4/A3/A2 only.
    sensorA1 = 1023;
    sensorA5 = 1023;
    // Build F = 8*A4_on + 4*A3_on + 2*A2_on.
    sensorF = 0;
    if (sensorA2 < LINE_THRESHOLD) {
      sensorF = sensorF + 2;
    }
    if (sensorA3 < LINE_THRESHOLD) {
      sensorF = sensorF + 4;
    }
    if (sensorA4 < LINE_THRESHOLD) {
      sensorF = sensorF + 8;
    }
    // Position weights: A4=-1, A3=0, A2=+1. Curve base125,
    // gain100; minimum inner8. Straight command230 is separate.
    sumW = 0;
    countOn = 0;
    if (sensorA2 < LINE_THRESHOLD) {
      sumW = sumW + 1;
      countOn = countOn + 1;
    }
    if (sensorA3 < LINE_THRESHOLD) {
      countOn = countOn + 1;
    }
    if (sensorA4 < LINE_THRESHOLD) {
      sumW = sumW + -1;
      countOn = countOn + 1;
    }
    absW = sumW;
    if (sumW < 0) {
      absW = 0 - sumW;
    }
    if (countOn > 0) {
      innerSpeed = SPEED_CURVE - (absW * TURN_KP) / countOn;
    }
    if (innerSpeed < SPEED_TURN_INNER_MEDIUM) {
      innerSpeed = SPEED_TURN_INNER_MEDIUM;
    }
    turnNow = millis();
    if (LIFT_ENABLED == 1) {
      if (LIFT_CROSSING_INDEX <= 0) {
        turnFault = 1;
      }
      if (lapReady == 1 && (liftState == 0 || liftState == 3) && turnActive == 0 && gapActive == 0) {
        if (sensorF == 14) {
          liftClearPending = 0;
          if (liftMarkerLatched == 0) {
            if (liftMarkerPending == 0) {
              liftMarkerPending = 1;
              liftMarkerAt = turnNow;
            }
            liftMarkerElapsed = turnNow - liftMarkerAt;
            if (liftMarkerElapsed >= LIFT_MARKER_CONFIRM_MS) {
              liftMarkerLatched = 1;
              liftMarkerPending = 0;
              liftCrossings = liftCrossings + 1;
              if (liftState == 0 && liftCrossings == LIFT_CROSSING_INDEX) {
                liftState = 1;
                liftWaitAt = turnNow;
                liftExitPending = 0;
                turnDirection = 0;
                turnCandidate = 0;
                wideActive = 0;
              }
            }
          }
        } else {
          liftMarkerPending = 0;
        }
      } else {
        liftMarkerPending = 0;
      }
      if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
        if (liftClearPending == 0) {
          liftClearPending = 1;
          liftClearAt = turnNow;
        }
        liftClearElapsed = turnNow - liftClearAt;
        if (liftClearElapsed >= LIFT_CLEAR_CONFIRM_MS) {
          liftMarkerLatched = 0;
        }
      } else {
        liftClearPending = 0;
      }
    }
    if (lapStarted == 0) {
      lapStarted = 1;
      lapAt = turnNow;
    }
    lapElapsed = turnNow - lapAt;
    if (lapElapsed >= MAX_LAP_MS) {
      turnFault = 1;
    }
    if (lapReady == 0) {
      if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
        if (departPending == 0) {
          departPending = 1;
          departAt = turnNow;
        }
        departElapsed = turnNow - departAt;
        if (departElapsed >= DEPART_CONFIRM_MS) {
          lapReady = 1;
        }
      } else {
        departPending = 0;
      }
    }
    if ((liftState == 0 || liftState == 3) && sensorF == 14 && turnActive == 0 && gapActive == 0) {
      if (wideActive == 0) {
        wideActive = 1;
        wideAt = turnNow;
      }
      wideElapsed = turnNow - wideAt;
      if (wideElapsed >= WIDE_TIMEOUT_MS) {
        turnFault = 1;
      } else if ((LIFT_ENABLED == 0 || liftState == 3) && lapReady == 1 && lapElapsed >= MIN_LAP_MS && wideElapsed >= FINISH_CONFIRM_MS) {
        lapDone = 1;
      }
    } else {
      wideActive = 0;
    }
    if ((liftState == 0 || liftState == 3) && turnActive == 0 && gapActive == 0 && turnFault == 0 && lapDone == 0) {
      if (sensorF == 8 || sensorF == 12) {
        if (turnCandidate == -1) {
        } else {
          turnCandidate = -1;
          turnCandidateAt = turnNow;
        }
        turnCandidateElapsed = turnNow - turnCandidateAt;
        if (turnCandidateElapsed >= TURN_DIRECTION_CONFIRM_MS) {
          turnDirection = -1;
          turnSeenAt = turnNow;
        }
      } else if (sensorF == 2 || sensorF == 6) {
        if (turnCandidate == 1) {
        } else {
          turnCandidate = 1;
          turnCandidateAt = turnNow;
        }
        turnCandidateElapsed = turnNow - turnCandidateAt;
        if (turnCandidateElapsed >= TURN_DIRECTION_CONFIRM_MS) {
          turnDirection = 1;
          turnSeenAt = turnNow;
        }
      } else if (sensorF == 0) {
        if (turnCandidate == -1 && turnDirection == 1 || turnCandidate == 1 && turnDirection == -1) {
          turnDirection = 0;
        }
        turnCandidate = 0;
      } else {
        turnCandidate = 0;
        if (sensorF == 14) {
          turnDirection = 0;
        }
      }
      if (sensorF == 4) {
        if (centerPending == 0) {
          centerPending = 1;
          centerAt = turnNow;
        }
        centerElapsed = turnNow - centerAt;
        if (centerElapsed >= TURN_CENTER_CLEAR_MS) {
          turnDirection = 0;
        }
      } else {
        centerPending = 0;
      }
      turnAge = turnNow - turnSeenAt;
      if (sensorF == 0) {
        if ((turnDirection == -1 || turnDirection == 1) && turnAge <= TURN_MEMORY_MS) {
          turnActive = 1;
          turnAt = turnNow;
          turnConfirm = 0;
        } else {
          gapActive = 1;
          gapAt = turnNow;
          gapConfirm = 0;
        }
      }
    }
    if (turnFault == 1 || lapDone == 1) {
      stop2();
      colorled13(1,"#0000ff");
    } else if (LIFT_ENABLED == 1 && (liftState == 1 || liftState == 2)) {
      lift_control();
    } else if (turnActive == 1) {
      sharp_turn();
    } else if (gapActive == 1) {
      cross_gap();
    } else if (wideActive == 1) {
      digitalWrite(7,LOW);
      analogWrite(5,WIDE_PWM);
      digitalWrite(4,HIGH);
      analogWrite(6,WIDE_PWM);
    } else {
      // Normal follow fallback: F=10 holds; left/right proportional
      // steering. Lap finish, wide marker, short gap and
      // sharp-turn states have priority. The preserved legacy
      // F=0 loop counter is bypassed by the gap/turn states.
      if (sensorF == 10) {
      } else if (sensorA4 < LINE_THRESHOLD && sensorA2 > LINE_THRESHOLD) {
        digitalWrite(7,LOW);
        analogWrite(5,innerSpeed);
        digitalWrite(4,HIGH);
        analogWrite(6,SPEED_CURVE);
      } else if (sensorA2 < LINE_THRESHOLD && sensorA4 > LINE_THRESHOLD) {
        digitalWrite(7,LOW);
        analogWrite(5,SPEED_CURVE);
        digitalWrite(4,HIGH);
        analogWrite(6,innerSpeed);
      } else if (sensorF == 0) {
        if (whiteCount < WHITE_STOP_COUNT) {
          whiteCount = whiteCount + 1;
        } else {
          stop2();
          colorled13(1,"#0000ff");
        }
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,SPEED_STRAIGHT);
        digitalWrite(4,HIGH);
        analogWrite(6,SPEED_STRAIGHT);
      }
    }
    // Original 115200-baud raw ADC/F telemetry; no new capture protocol.
    Serial.print((String("A1=") + String(rawA1)));
    Serial.print((String("A2=") + String(rawA2)));
    Serial.print((String("A3=") + String(rawA3)));
    Serial.print((String("A4=") + String(rawA4)));
    Serial.print((String("A5=") + String(rawA5)));
    Serial.println((String("F=") + String(sensorF)));
    if (sensorF > 0) {
      whiteCount = 0;
    }

}